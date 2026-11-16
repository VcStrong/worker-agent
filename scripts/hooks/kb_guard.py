"""知识库无人值守会话（KB_SESSION）里 guard_hook 的命令判断（REQ-018）。纯本地，只做文本分析，不执行命令。

在知识库会话里 ask 会变成硬拒（deny），所以这里要同时做到：
- 不误伤：引号里的字符串、here-doc 正文、只读命令（grep / cat / echo …）的参数、git 的非危险子命令都只是数据；
  git rm、删除会话工作目录或临时目录里的文件属于日常开发，放行；
- 不漏：把 sh / bash -c、eval、su -c、ssh 远程命令、$( ) 和反引号里的命令拆出来递归检查，去掉带参数的前缀
  （sudo -u x、env -i、timeout 60、nice -n 5、xargs -I{} …）、反斜杠和引号包住的命令名；
  python / node -c 和喂给解释器的 here-doc 按原有危险规则检查；
  其余认不出的命令段，只要原有规则（guard_hook.DANGER，原来会 ask）命中就仍然拒绝。
kb_danger() 返回拒绝原因标签，放行返回 None。
"""
import os
import re

SHELLS = {"sh", "bash", "zsh", "dash", "ksh", "fish"}
INTERPS = {"python", "python3", "python2", "node", "ruby", "perl", "php", "osascript"}
DB_CLIENTS = {"mysql", "psql", "sqlite3", "mongo", "mongosh", "clickhouse-client", "sqlcmd"}
NET_CLIENTS = {"curl", "wget", "http", "https", "httpie", "xh"}
DELETERS = {"rm", "rmdir", "unlink"}
# 只读 / 打印类命令：参数都是数据，不按原有规则兜底
READ_ONLY = {"cat", "less", "more", "head", "tail", "grep", "egrep", "fgrep", "rg", "ag", "ack", "ls", "echo", "printf",
             "wc", "stat", "file", "diff", "cmp", "which", "type", "tree", "du", "df", "pwd", "basename", "dirname",
             "realpath", "readlink", "sort", "uniq", "cut", "tr", "jq", "yq", "column", "true", "false", "test", "[",
             "[[", "sleep", "date", "nl", "tac", "shasum", "md5", "md5sum", "sha256sum", "hexdump", "xxd", "strings",
             "git-grep", "fd", "mkdir", "touch", "cp", "mv", "ln", "chmod", "tee", "export", "unset", "local",
             "set", "source", ".", "read", "wait", "kill", "pkill", "ps", "lsof", "open", "adb"}
TMP_ROOTS = ["/tmp", "/private/tmp", "/var/folders", "/private/var/folders"]
GIT_OPTS_WITH_ARG = {"-C", "-c", "--git-dir", "--work-tree", "--namespace", "--exec-path"}
PREFIX_SIMPLE = {"then", "do", "else", "elif", "if", "while", "until", "!", "{", "}", "time", "nohup", "command",
                 "builtin", "exec", "caffeinate", "noglob", "unbuffer"}
PREFIX_OPTS = {  # 前缀命令 → 带一个参数的选项
    "sudo": {"-u", "-g", "-C", "-h", "-p", "-r", "-t", "-U", "-D", "-R", "-T"},
    "env": {"-u", "-C", "-S", "--unset", "--chdir", "--split-string"},
    "timeout": {"-s", "-k", "--signal", "--kill-after"},
    "gtimeout": {"-s", "-k", "--signal", "--kill-after"},
    "nice": {"-n", "--adjustment"},
    "ionice": {"-c", "-n", "-p"},
    "xargs": {"-n", "-I", "-P", "-L", "-d", "-s", "-E", "-a", "--max-args", "--max-procs", "--delimiter", "--arg-file"},
    "stdbuf": {"-i", "-o", "-e"},
    "doas": {"-u", "-C"},
}
PREFIX_POSITIONAL = {"timeout": 1, "gtimeout": 1}   # 选项之后还要跳过的位置参数（时长）
SSH_OPTS = {"-p", "-i", "-l", "-o", "-F", "-J", "-L", "-R", "-D", "-b", "-c", "-E", "-m", "-O", "-Q", "-S", "-W", "-w", "-B", "-I"}

KB_CMD_DANGER = [  # 匹配「命令名 + 子命令」开头（git 已去掉全局选项）
    (r"git push\b", "git push"),
    (r"git send-pack\b", "git push"),
    (r"git remote (add|set-url)\b", "添加 / 修改远端"),
    (r"git reset\b.*--hard\b", "丢弃未提交改动"),
    (r"git clean\b.*(\s-[a-zA-Z]*f|--force)", "丢弃未跟踪文件"),
    (r"git branch\b.*(\s-[a-zA-Z]*D\b|(--delete|-d)\b.*(--force|-f)\b|(--force|-f)\b.*(--delete|-d)\b)", "删除分支"),
    (r"git (checkout|switch)\b.*(\s-[a-zA-Z]*f\b|--force|--discard-changes)", "丢弃未提交改动"),
    (r"git (checkout|restore)\b.*\s\.(\s|$)", "丢弃未提交改动"),
    (r"git stash (drop|clear)\b", "删除 stash"),
    (r"git update-ref\b.*\s-d\b", "删除分支"),
    (r"(kubectl|oc) (apply|delete|rollout|scale|set|patch|replace|create)\b", "K8s 部署 / 变更"),
    (r"helm (install|upgrade|uninstall|rollback|delete)\b", "Helm 发布"),
    (r"terraform (apply|destroy)\b|pulumi (up|destroy)\b", "基础设施变更"),
    (r"docker (push|stack deploy)\b|docker compose\b.*\bup\b.*(-d|--detach)", "镜像推送 / 部署"),
    (r"(npm|pnpm|yarn) publish\b|twine upload\b|cargo publish\b|pod trunk push\b|ohpm publish\b", "发布包"),
    (r"(vercel|netlify)\b.*(--prod|deploy)\b|firebase deploy\b|fastlane\b|gh release\b|serverless deploy\b|s deploy\b", "部署 / 发布"),
    (r"dropdb\b|redis-cli\b.*\b(flushall|flushdb)\b", "清空数据库"),
    (r"((bash|sh|zsh|python3?|node) )?\S*\b(deploy|release|publish)\.(sh|py)\b", "部署 / 发布脚本"),
    (r"shred\b", "删除文件"),
]
SQL_DANGER = re.compile(r"\b(drop\s+(table|database|schema)|truncate\s+table|delete\s+from)\b", re.I)
PUSH_URL = re.compile(r"(push|notification|jpush|getui|fcm|apns).*(send|push)|/push\b|/message/send|/messages:send"
                      r"|fcm\.googleapis|api\.push\.apple", re.I)
HEREDOC = re.compile(r"<<-?\s*(['\"]?)([A-Za-z_][A-Za-z0-9_]*)\1")
SPLIT = re.compile(r"\|\||&&|[;|&\n()]|(?:(?<=\s)|^)[{}](?=\s|$)")
PH = re.compile(r"\x00(\d+)\x00")       # 引号占位
SUB = re.compile(r"\x02(\d+)\x02")      # $( ) / 反引号占位
VAR_REF = re.compile(r"\$\{?([A-Za-z_][A-Za-z0-9_]*)\}?")
VAR_MKTEMP = re.compile(r"(?:^|[\s;&|(])([A-Za-z_][A-Za-z0-9_]*)=[\"']?\$\(\s*mktemp\b")
VAR_LIT = re.compile(r"(?:^|[\s;&|(])([A-Za-z_][A-Za-z0-9_]*)=(\"[^\"$`]*\"|'[^']*'|[^\s;&|$`'\"()]+)")
MAX_DEPTH = 6


# ---------------- 词法 ----------------
def _match_paren(s, i):
    """s[i:] 以 "$(" 开头，返回匹配的 ")" 下标（跳过引号），找不到返回 len(s)。"""
    depth, j = 0, i + 1
    while j < len(s):
        c = s[j]
        if c == "\\":
            j += 2
            continue
        if c in "'\"":
            k = s.find(c, j + 1)
            j = (k if k > 0 else len(s)) + 1
            continue
        if c == "(":
            depth += 1
        elif c == ")":
            depth -= 1
            if depth == 0:
                return j
        j += 1
    return len(s)


def scan(cmd):
    """引号 → \\x00n\\x00（lits[n] 为含引号原文），$( ) / 反引号 → \\x02m\\x02（subs[m] 为里面的命令），
    反斜杠转义去掉反斜杠。返回 (masked, lits, subs)。"""
    out, lits, subs, i = [], [], [], 0
    while i < len(cmd):
        c = cmd[i]
        if c == "\\":
            out.append(cmd[i + 1:i + 2])
            i += 2
        elif c == "'":
            j = cmd.find("'", i + 1)
            j = j if j >= 0 else len(cmd) - 1
            lits.append(cmd[i:j + 1])
            out.append("\x00%d\x00" % (len(lits) - 1))
            i = j + 1
        elif c == '"':
            j = i + 1
            while j < len(cmd) and cmd[j] != '"':
                if cmd[j] == "\\":
                    j += 1
                elif cmd.startswith("$(", j):
                    k = _match_paren(cmd, j)
                    subs.append(cmd[j + 2:k])
                    j = k
                elif cmd[j] == "`":
                    k = cmd.find("`", j + 1)
                    k = k if k >= 0 else len(cmd)
                    subs.append(cmd[j + 1:k])
                    j = k
                j += 1
            lits.append(cmd[i:j + 1])
            out.append("\x00%d\x00" % (len(lits) - 1))
            i = j + 1
        elif cmd.startswith("$(", i):
            k = _match_paren(cmd, i)
            subs.append(cmd[i + 2:k])
            out.append("\x02%d\x02" % (len(subs) - 1))
            i = k + 1
        elif c == "`":
            k = cmd.find("`", i + 1)
            k = k if k >= 0 else len(cmd)
            subs.append(cmd[i + 1:k])
            out.append("\x02%d\x02" % (len(subs) - 1))
            i = k + 1
        else:
            out.append(c)
            i += 1
    return "".join(out), lits, subs


def split_heredocs(cmd):
    """去掉 here-doc 正文；正文喂给 shell 的当命令递归检查，喂给解释器的按原有规则查，其余（cat > f、git commit -F -）是数据。
    返回 (去掉正文后的命令, [(\"shell\"|\"interp\", 正文)])。"""
    lines, out, bodies, i = cmd.split("\n"), [], [], 0
    while i < len(lines):
        line = lines[i]
        out.append(line)
        i += 1
        for m in HEREDOC.finditer(line):
            end, body = m.group(2), []
            while i < len(lines) and lines[i].strip() != end:
                body.append(lines[i])
                i += 1
            i += 1
            before = re.split(r"\|\||&&|[;|&]", line[:m.start()])[-1].split()
            before = strip_prefix([t.strip("\"'") for t in before]) if before else []
            name = os.path.basename(before[0]) if before else ""
            if name in SHELLS or name == "eval":
                bodies.append(("shell", "\n".join(body)))
            elif name in INTERPS:
                bodies.append(("interp", "\n".join(body)))
            elif name in DB_CLIENTS:
                bodies.append(("sql", "\n".join(body)))
    return "\n".join(out), bodies


def strip_prefix(toks):
    """去掉变量赋值和 sudo / env / timeout / nice / xargs … 前缀（含它们带参数的选项）。"""
    toks = list(toks)
    while toks:
        t = toks[0]
        if re.match(r"^[A-Za-z_][A-Za-z0-9_]*=", t) or t in PREFIX_SIMPLE:
            toks = toks[1:]
            if t == "time" and toks[:1] == ["-p"]:
                toks = toks[1:]
            continue
        name = os.path.basename(t)
        if name in PREFIX_OPTS:
            toks, opts = toks[1:], PREFIX_OPTS[name]
            while toks and toks[0].startswith("-"):
                o = toks[0]
                toks = toks[1:]
                if o == "--":
                    break
                if o in opts and "=" not in o:
                    toks = toks[1:]
            toks = toks[PREFIX_POSITIONAL.get(name, 0):]
            continue
        break
    return toks


# ---------------- 求值 ----------------
def _vars(text, cwd):
    v = {"PWD": cwd or "", "TMPDIR": os.environ.get("TMPDIR") or "/tmp"}
    for m in VAR_LIT.finditer(text):
        val = m.group(2)
        v[m.group(1)] = val[1:-1] if val[:1] in "\"'" else val
    for m in VAR_MKTEMP.finditer(text):
        v[m.group(1)] = "/tmp/mktemp"
    return v


class Ctx:
    def __init__(self, lits, subs, env):
        self.lits, self.subs, self.env = lits, subs, env

    def raw(self, tok):
        """去掉占位：引号原文去引号，$( ) 还原成原文（用于拼回 -c / eval / ssh 的命令文本）。"""
        tok = PH.sub(lambda m: _unq(self.lits[int(m.group(1))]), tok)
        return SUB.sub(lambda m: "$(" + self.subs[int(m.group(1))] + ")", tok)

    def data(self, tok):
        """兜底匹配用：引号内容和 $( ) 都当数据去掉。"""
        return SUB.sub(" ", PH.sub(" ", tok))

    def literal(self, tok):
        """算出路径类参数的字面值；含 $( ) / 反引号 / 未知变量时返回 None。"""
        if SUB.search(tok):
            return None
        parts = []
        for piece in re.split(r"(\x00\d+\x00)", tok):
            m = PH.fullmatch(piece)
            if m:
                q = self.lits[int(m.group(1))]
                if q.startswith("'"):
                    parts.append(q[1:-1])
                    continue
                piece = q[1:-1]
                if "$(" in piece or "`" in piece:
                    return None
            parts.append(piece)
        s = "".join(parts)
        s = VAR_REF.sub(lambda x: self.env.get(x.group(1), "\x01"), s)
        return None if ("\x01" in s or "$" in s) else s


def _unq(q):
    return q[1:-1] if len(q) >= 2 and q[0] == q[-1] and q[0] in "'\"" else q.strip("'\"")


def _inside(path, roots):
    return any(path == r or path.startswith(r.rstrip(os.sep) + os.sep) for r in roots)


def _git_norm(toks):
    i = 1
    while i < len(toks) and toks[i].startswith("-"):
        i += 2 if toks[i] in GIT_OPTS_WITH_ARG else 1
    return ["git"] + toks[i:]


def _delete_outside(name, toks, d, ctx, remote):
    """rm / rmdir / unlink / find -delete 的目标都在会话工作目录（不含它本身、上级和 .git）或临时目录里时返回 []。"""
    tmp = TMP_ROOTS + [os.path.normpath(os.environ.get("TMPDIR") or "/tmp")]
    is_find = name == "find"
    targets, skip = [], False
    for t in toks[1:]:
        if skip:
            skip = False
            continue
        if re.match(r"^\d*[<>]+&?$", t):       # 单独的重定向符：后面那个是重定向目标，不是删除目标
            skip = True
            continue
        if not t.startswith("-") and not re.match(r"^\d*[<>]", t):
            targets.append(t)
    if is_find:
        targets = targets[:1] or ["."]
    if remote:
        return targets or [name]
    bad = []
    for raw in targets:
        t = ctx.literal(raw)
        if t is None or not t or t.startswith("~"):
            bad.append(ctx.raw(raw))
            continue
        if not os.path.isabs(t) and d is None:
            bad.append(t)
            continue
        ap = os.path.normpath(t if os.path.isabs(t) else os.path.join(d, t))
        if ".git" in ap.split(os.sep):
            bad.append(t)
        elif _inside(ap, tmp) and ap not in tmp:
            continue
        elif d and ((ap == d and not is_find) or (ap != d and _inside(d, [ap]))):
            bad.append(t)
        elif d and _inside(ap, [d]):
            continue
        else:
            bad.append(t)
    return bad


def _payload_after(toks, flags, ctx):
    """sh -c 'x' / su -c 'x' / python -c 'x'：返回 -c 后面那个参数的命令文本。"""
    for i, t in enumerate(toks[1:], 1):
        if t in flags or (re.match(r"^-[a-zA-Z]+$", t) and any(f[1] in t for f in flags if len(f) == 2)):
            if i + 1 < len(toks):
                return ctx.raw(toks[i + 1])
    return None


def _old_rules(text, danger):
    for pat, label in danger:
        if re.search(pat, text.lower()):
            return label
    return None


def analyze(cmd, cwd, danger, remote=False, depth=0):
    if depth > MAX_DEPTH:
        return "命令嵌套过深，无法判断"
    text, bodies = split_heredocs(cmd)
    for kind, body in bodies:
        if kind == "shell":
            lab = analyze(body, cwd, danger, remote, depth + 1)
        elif kind == "sql":
            lab = "删除数据库数据" if SQL_DANGER.search(body) else None
        else:
            lab = interp_danger(body, cwd, danger, remote, depth + 1)
        if lab:
            return lab
    masked, lits, subs = scan(text)
    ctx = Ctx(lits, subs, _vars(text, cwd))
    for s in subs:                                   # $( ) / 反引号里的命令
        lab = analyze(s, cwd, danger, remote, depth + 1)
        if lab:
            return lab
    d = os.path.abspath(cwd) if cwd else None
    for seg in SPLIT.split(masked):
        toks = strip_prefix(seg.split())
        if not toks:
            continue
        if PH.fullmatch(toks[0]):                    # "git" push
            toks[0] = ctx.raw(toks[0])
        name = os.path.basename(toks[0])
        if name in ("cd", "pushd"):
            t = ctx.literal(toks[1]) if len(toks) > 1 else os.path.expanduser("~")
            d = os.path.normpath(os.path.join(d or "/", os.path.expanduser(t))) if t and d is not None else None
            continue
        lab = _segment(name, toks, d, ctx, danger, remote, depth)
        if lab:
            return lab
    return None


def _segment(name, toks, d, ctx, danger, remote, depth):
    nested = lambda c, r=remote: analyze(c, d, danger, r, depth + 1)   # noqa: E731
    if name in SHELLS:
        p = _payload_after(toks, {"-c"}, ctx)
        if p is not None:
            return nested(p)
        return _head(toks, ctx, danger)
    if name == "eval":
        return nested(" ".join(ctx.raw(t) for t in toks[1:]))
    if name == "su":
        p = _payload_after(toks, {"-c", "--command"}, ctx)
        return nested(p) if p is not None else None
    if name == "ssh":
        rest, i = toks[1:], 0
        while i < len(rest) and rest[i].startswith("-"):
            i += 2 if rest[i] in SSH_OPTS else 1
        remote_cmd = " ".join(ctx.raw(t) for t in rest[i + 1:])
        return nested(remote_cmd, True) if remote_cmd.strip() else None
    if name in INTERPS:
        p = _payload_after(toks, {"-c", "-e", "--eval"}, ctx)
        if p is not None:
            return interp_danger(p, d, danger, remote, depth + 1)
        return _head(toks, ctx, danger)
    if name in DELETERS or name == "shred" or (name == "find" and ("-delete" in toks or _find_exec_rm(toks))):
        if name == "shred":
            return "删除文件"
        bad = _delete_outside(name, toks, d, ctx, remote)
        if bad:
            return "删除工作目录以外或算不出目标的文件（%s）" % " ".join(bad[:3])
        return None
    if name == "git":
        return _head(_git_norm(toks), ctx, danger, fallback=False)
    full = " ".join(ctx.raw(t) for t in toks)
    if name in NET_CLIENTS:   # 只有带数据 / POST 的请求才算发推送；GET 文档页不算
        sends = any(t in SEND_FLAGS or t.startswith(("--data", "--json", "--form")) for t in toks[1:]) or \
            re.search(r"-X\s*(POST|PUT)\b|--request\s*(POST|PUT)\b", full, re.I) or name in ("http", "https", "httpie", "xh")
        return "发推送" if sends and PUSH_URL.search(full) else None
    if name in ("for", "select", "case", "function"):
        return None   # for 的词表、case 的模式是数据；循环体在后面的段里单独检查
    if name in DB_CLIENTS:
        return "删除数据库数据" if SQL_DANGER.search(full) else None
    return _head(toks, ctx, danger, fallback=name not in READ_ONLY)


SEND_FLAGS = {"-d", "-F", "-T", "--data", "--json", "--form", "--upload-file"}
CODE_CALL = re.compile(r"\b(os\.system|os\.popen|os\.exec\w*|subprocess\.(?:run|call|check_call|check_output|Popen|getoutput|getstatusoutput)"
                       r"|execSync|execFileSync|spawnSync|exec|execFile|spawn|system|popen|Popen|check_output|check_call)\s*(?=\()")
SQL_CALL = re.compile(r"\b(execute|executescript|executemany|query|raw|exec_driver_sql)\s*\(\s*[rbuf]*(['\"]{1,3})"
                      r"[^'\"]*?\b(drop\s+(table|database|schema)|truncate\s+table|delete\s+from)\b", re.I | re.S)
STR_LIT = re.compile(r"'([^'\\]*(?:\\.[^'\\]*)*)'|\"([^\"\\]*(?:\\.[^\"\\]*)*)\"|`([^`]*)`")


def interp_danger(code, cwd, danger, remote=False, depth=0):
    """python / node / ruby / perl 代码（-c / -e 参数或 here-doc）：代码里的字符串大多是数据（改文件的脚本常含任意文字），
    只检查真正会执行的：os.system / subprocess / execSync / system … 调用里的命令按 shell 递归分析，
    execute(...) 等里的 DROP / TRUNCATE / DELETE FROM 算删库。"""
    if depth > MAX_DEPTH:
        return "命令嵌套过深，无法判断"
    if SQL_CALL.search(code):
        return "删除数据库数据"
    for m in CODE_CALL.finditer(code):
        end = _match_paren(code, m.end() - 1)
        arg = code[m.end() + 1:end]
        parts = [a or b or c for a, b, c in STR_LIT.findall(arg)]
        if not parts:
            continue                 # 参数是变量，算不出来：不按命令文本猜
        lab = analyze(" ".join(parts), cwd, danger, remote, depth + 1)
        if lab:
            return lab
    return None


def _find_exec_rm(toks):
    return "-exec" in toks and any(os.path.basename(t) in ("rm", "shred") for t in toks[toks.index("-exec") + 1:])


def _head(toks, ctx, danger, fallback=True):
    head = " ".join([os.path.basename(toks[0])] + [ctx.data(t) for t in toks[1:]])
    head = re.sub(r"\s+", " ", head).strip()
    for pat, label in KB_CMD_DANGER:
        if re.match(pat, head):
            return label
    if fallback:
        return _old_rules(head, danger)   # 认不出的命令：原有规则命中（原来会 ask）仍然拒绝
    return None


def kb_danger(cmd, cwd, danger):
    """知识库会话里要硬拒的操作，返回标签；放行返回 None。danger 为 guard_hook.DANGER（原有 ask 规则）。"""
    return analyze(cmd, cwd, danger)
