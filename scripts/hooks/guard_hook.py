#!/usr/bin/env python3
"""REQ-011：安全边界 hook（PreToolUse，matcher: Bash|Write|Edit|MultiEdit|NotebookEdit）。纯本地，不调用模型。

- 部署、发布、git push、发推送、删除文件 / 数据库类命令 → permissionDecision=ask：停下让用户确认后才执行
- 写本套件安装的 agent / 技能文件（.claude/agents、.claude/skills 下本套件的文件，以及 worker-agent 的 agents/、data/skills/）
  → deny，提示走更新提案（proposals/ + apply_proposal.py）
- 只读代码 + 写文档的角色（hook 输入带 agent_type 时）写代码文件 → deny
- 知识库无人值守会话（环境变量 KB_SESSION 非空，REQ-018）：没人能点确认，ask 会挂住或被拒，改成 deny，
  提示改用 kb_ask 请用户确认、由用户执行。知识库自己用 Python 调 git 推送（不经过 Claude 工具）不受影响。
  deny 是硬拒，所以这时不再对整条命令文本做关键词匹配，而是按 ; && || | 换行 $( 拆段、剥掉引号里的内容，
  只看每段命令名位置（kb_danger）：grep / echo / git commit -m 里出现的字样不算；git rm、删除会话目录或临时目录里的
  文件属于日常开发，放行；推送、部署、发布、发推送、删库、丢弃未提交改动、删工作目录以外的文件仍拒绝。
"""
import json
import os
import re
import sys

ROOT = os.environ.get("WORKER_AGENT_HOME") or os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DOC_ROLES = {"product-manager", "ux-designer", "data-growth", "ai-product-manager", "ai-eval-compliance", "tech-scout"}
CODE_EXT = {".py", ".js", ".jsx", ".ts", ".tsx", ".vue", ".java", ".kt", ".kts", ".swift", ".m", ".mm", ".go", ".rs",
            ".c", ".cc", ".cpp", ".h", ".hpp", ".cs", ".php", ".rb", ".dart", ".ets", ".sql", ".sh", ".gradle",
            ".scala", ".lua", ".wxml", ".wxss", ".css", ".scss", ".less", ".html"}
DANGER = [
    (r"\bgit\s+push\b", "git push"),
    (r"\bgit\s+(remote\s+add|push\s+--force)", "添加远端 / 强推"),
    (r"(^|[;&|]\s*|\s)(sudo\s+)?rm\s+", "删除文件"),
    (r"\b(find\b.*-delete|shred|rmdir)\b", "删除文件"),
    (r"\bgit\s+(clean\s+-[a-z]*f|reset\s+--hard|branch\s+-D)", "丢弃代码 / 删除分支"),
    (r"\b(kubectl|oc)\s+(apply|delete|rollout|scale|set|patch|replace|create)\b", "K8s 部署 / 变更"),
    (r"\bhelm\s+(install|upgrade|uninstall|rollback|delete)\b", "Helm 发布"),
    (r"\bterraform\s+(apply|destroy)\b|\bpulumi\s+(up|destroy)\b", "基础设施变更"),
    (r"\bdocker\s+(push|stack\s+deploy)\b|\bdocker\s+compose\b.*\bup\b.*(-d|--detach)", "镜像推送 / 部署"),
    (r"\b(npm|pnpm|yarn)\s+publish\b|\btwine\s+upload\b|\bcargo\s+publish\b|\bpod\s+trunk\s+push\b|\bohpm\s+publish\b", "发布包"),
    (r"\b(vercel|netlify)\b.*\b(--prod|deploy)\b|\bfirebase\s+deploy\b|\bfastlane\b|\bgh\s+release\b|\bserverless\s+deploy\b|\bs\s+deploy\b", "部署 / 发布"),
    (r"\b(drop\s+(table|database|schema)|truncate\s+table|delete\s+from)\b", "删除数据库数据"),
    (r"\b(redis-cli\b.*\b(flushall|flushdb)|dropdb)\b", "清空数据库"),
    (r"\b(deploy|release|publish)\.(sh|py)\b", "部署 / 发布脚本"),
    (r"(push|notification|jpush|getui|fcm|apns).*(send|push)|curl\b.*(/push|/message/send)", "发推送"),
]


# ---------- 知识库会话（KB_SESSION）：只看命令名位置 ----------
QUOTED = re.compile(r"\"(?:\\.|[^\"\\])*\"|'[^']*'")
KB_SPLIT = re.compile(r"\|\||&&|[;|&\n]|\$\(|`|\(|\)")
WRAPPERS = {"sudo", "env", "time", "nohup", "command", "exec", "nice", "xargs", "builtin", "then", "do", "else", "!", "{"}
TMP_ROOTS = ["/tmp", "/private/tmp", "/var/folders", "/private/var/folders"]
DB_CLIENTS = {"mysql", "psql", "sqlite3", "mongo", "mongosh", "clickhouse-client", "sqlcmd"}
GIT_OPTS_WITH_ARG = {"-C", "-c", "--git-dir", "--work-tree", "--namespace"}
KB_CMD_DANGER = [  # 匹配「命令名 + 子命令」开头（已去掉 git 全局选项、引号内容）
    (r"git push\b", "git push"),
    (r"git remote (add|set-url)\b", "添加 / 修改远端"),
    (r"git reset\b.*--hard\b", "丢弃未提交改动"),
    (r"git clean\b.*\s-[a-zA-Z]*f", "丢弃未跟踪文件"),
    (r"git branch\b.*\s-D\b", "删除分支"),
    (r"git (checkout|restore)\b.*\s\.(\s|$)", "丢弃未提交改动"),
    (r"git stash (drop|clear)\b", "删除 stash"),
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
PUSH_URL = re.compile(r"(/push\b|/message/send|/messages:send|jpush|getui|fcm\.googleapis|api\.push\.apple)", re.I)


HEREDOC = re.compile(r"<<-?\s*(['\"]?)([A-Za-z_][A-Za-z0-9_]*)\1")
QMARK = re.compile(r"^\x00(\d+)\x00$")


def strip_heredocs(cmd):
    """去掉 here-doc 正文（commit 说明、python - <<EOF 脚本、cat > f <<EOF 文档），只留起始行。"""
    lines, out, i = cmd.split("\n"), [], 0
    while i < len(lines):
        line = lines[i]
        out.append(line)
        i += 1
        for m in HEREDOC.finditer(line):
            end = m.group(2)
            while i < len(lines) and lines[i].strip() != end:
                i += 1
            i += 1
    return "\n".join(out)


def _mask(cmd):
    """引号里的内容换成占位符 \\x00<序号>\\x00（不参与命令名匹配、不影响拆段），返回 (masked, 原文列表)。"""
    lits = []

    def rep(m):
        lits.append(m.group(0))
        return " \x00%d\x00 " % (len(lits) - 1)
    return QUOTED.sub(rep, cmd), lits


def _segments(cmd):
    """拆成命令段，每段返回去掉前缀（环境变量赋值、sudo / env / xargs 等）后的词；引号内容是占位符。"""
    masked, lits = _mask(strip_heredocs(cmd))
    out = []
    for seg in KB_SPLIT.split(masked):
        toks = seg.split()
        while toks and (toks[0] in WRAPPERS or re.match(r"^[A-Za-z_][A-Za-z0-9_]*=", toks[0])):
            toks = toks[1:]
        if toks:
            out.append((toks, lits))
    return out


VAR_REF = re.compile(r"\$\{?([A-Za-z_][A-Za-z0-9_]*)\}?")
VAR_MKTEMP = re.compile(r"(?:^|[\s;&|(])([A-Za-z_][A-Za-z0-9_]*)=[\"']?\$\(\s*mktemp\b")
VAR_LIT = re.compile(r"(?:^|[\s;&|(])([A-Za-z_][A-Za-z0-9_]*)=(\"[^\"$`]*\"|'[^']*'|[^\s;&|$`'\"()]+)")


def _vars(cmd, cwd):
    """命令里简单赋值的变量：X=$(mktemp …) → 临时目录；X=字面值 → 该值。$PWD → 工作目录。"""
    v = {"PWD": cwd, "TMPDIR": os.environ.get("TMPDIR") or "/tmp"}
    for m in VAR_LIT.finditer(cmd):
        val = m.group(2)
        v[m.group(1)] = val[1:-1] if val[:1] in "\"'" else val
    for m in VAR_MKTEMP.finditer(cmd):
        v[m.group(1)] = "/tmp/mktemp"
    return v


def _literal(tok, lits, env=None):
    """占位符还原成去掉引号的字面值，展开已知的简单变量；还有算不出来的 $ / 反引号时返回 None。"""
    m = QMARK.match(tok)
    if m:
        raw = lits[int(m.group(1))]
        if raw.startswith("'"):
            return raw[1:-1]
        tok = raw[1:-1]
    if "`" in tok or "$(" in tok:
        return None
    env = env or {}
    tok = VAR_REF.sub(lambda x: env.get(x.group(1), "\x01"), tok)
    return None if ("\x01" in tok or "$" in tok) else tok


def _git_norm(toks):
    """git -C x -c k=v --no-pager push → git push。"""
    if os.path.basename(toks[0]) != "git":
        return toks
    i = 1
    while i < len(toks) and toks[i].startswith("-"):
        i += 2 if toks[i] in GIT_OPTS_WITH_ARG else 1
    return ["git"] + toks[i:]


def _inside(path, roots):
    return any(path == r or path.startswith(r.rstrip(os.sep) + os.sep) for r in roots)


def _rm_outside(toks, d, lits, env=None):
    """rm / find -delete 的目标：都在会话工作目录（不含目录本身和 .git）或临时目录里就放行，返回越界的目标。"""
    tmp = TMP_ROOTS + [os.path.normpath(os.environ.get("TMPDIR") or "/tmp")]
    is_find = os.path.basename(toks[0]) == "find"
    targets = [t for t in toks[1:] if not t.startswith("-")]
    if is_find:
        targets = targets[:1] or ["."]   # 搜索起点：删的是它下面匹配到的文件，起点等于工作目录也算目录内
    bad = []
    for raw in targets:
        t = _literal(raw, lits, env)
        if t is None or not t or t.startswith("~"):
            bad.append(raw if t is None else (t or "''"))   # 变量 / 命令替换 / 家目录：算不出目标，按越界处理
            continue
        ap = os.path.normpath(t if os.path.isabs(t) else os.path.join(d, t))
        if ".git" in ap.split(os.sep):
            bad.append(t)
        elif _inside(ap, tmp) and ap not in tmp:
            continue        # 临时目录里的东西（不含临时目录根）
        elif (ap == d and not is_find) or (ap != d and _inside(d, [ap])):
            bad.append(t)   # 工作目录本身或它的上级
        elif (ap != d or is_find) and _inside(ap, [d]):
            continue
        else:
            bad.append(t)
    return bad


def kb_danger(cmd, cwd):
    """知识库会话里要硬拒的操作，返回标签或 None。只看每段命令名位置；跟踪 cd 改变的工作目录。"""
    d = os.path.abspath(cwd)
    env = _vars(strip_heredocs(cmd), d)
    for toks, lits in _segments(cmd):
        name = os.path.basename(toks[0])
        if name in ("cd", "pushd") and len(toks) > 1:
            t = _literal(toks[1], lits, env)
            if t and not t.startswith("-"):
                d = os.path.normpath(os.path.join(d, os.path.expanduser(t)))
            continue
        toks = _git_norm(toks)
        head = " ".join([os.path.basename(toks[0])] + toks[1:])
        for pat, label in KB_CMD_DANGER:
            if re.match(pat, head):
                return label
        if name == "rm" or (name == "find" and "-delete" in toks):
            bad = _rm_outside(toks, d, lits, env)
            if bad:
                shown = [(lits[int(QMARK.match(b).group(1))] if QMARK.match(b) else b) for b in bad[:3]]
                return "删除工作目录以外的文件（%s）" % " ".join(shown)
        # SQL / 推送地址一般写在引号里：只在数据库客户端、curl 类命令那一段里看引号原文
        full = " ".join(lits[int(QMARK.match(t).group(1))] if QMARK.match(t) else t for t in toks)
        if name in DB_CLIENTS and SQL_DANGER.search(full):
            return "删除数据库数据"
        if name in ("curl", "wget", "http", "https") and PUSH_URL.search(full):
            return "发推送"
    return None


SUITE_ROOTS = [os.path.join(ROOT, "agents"), os.path.join(ROOT, "data", "skills"), os.path.join(ROOT, "skills"),
               os.path.join(ROOT, "local", "skills")]


def protected_paths(cwd):
    """Write/Edit 与 Bash 共用的保护范围：worker-agent 的 agents/、data/skills/、skills/、local/skills/，
    以及本套件装进项目 / 用户目录的 .claude 文件（manifest 登记的）。"""
    out = list(SUITE_ROOTS)
    for base in (cwd, os.path.expanduser("~")):
        mf = os.path.join(base, ".claude", "role-agents", "manifest.json")
        try:
            m = json.load(open(mf, encoding="utf-8"))
            for f in m.get("files", {}):
                if f.startswith(("agents/", "skills/")):
                    out.append(os.path.join(base, ".claude", f))
        except Exception:
            pass
    return out


def under(path, roots):
    path = os.path.normpath(path)
    for r in roots:
        r = os.path.normpath(r)
        if path == r or path.startswith(r + os.sep):
            return r
    return None


WRITE_OPS = re.compile(
    r"\bsed\b[^|;&]*\s-[a-z]*i|\btee\b|\bcp\b|\bmv\b|\brm\b|\brmdir\b|\btouch\b|\bln\b|\brsync\b|\bdd\b|\btruncate\b"
    r"|\binstall\b|\bchmod\b|\bperl\b|\bpython3?\b|\bnode\b|\bruby\b|\bawk\b|\bed\b|\bex\b|\bvim?\b|\bnano\b"
    r"|\bunzip\b|\btar\b|\bpatch\b|\bgit\s+(checkout|restore|apply|mv|rm|reset|stash|clean)\b|\bfind\b[^|;&]*-(delete|exec)")
# 本套件自带、会写技能层的脚本（只认 worker-agent ROOT 下的，用户仓库里同名脚本不受影响）
WRITER_SCRIPTS = [os.path.join(ROOT, "scripts", n) for n in
                  ("apply_proposal.py", "build.py", "rollback.py", "install_helper.py", "extract.py", "settings_merge.py")] + \
                 [os.path.join(ROOT, "install.sh")]
READ_ONLY_SCRIPTS = [os.path.join(ROOT, "scripts", n) for n in ("who.py", "validate.py", "usage_report.py", "refresh_check.py")] + \
                    [os.path.join(ROOT, "scripts", "eval_routing", "run_eval.py"), os.path.join(ROOT, "scripts", "eval_skills", "run_skill_eval.py")]
SEGMENT = re.compile(r"[;&|]+|\n")
TOKEN = re.compile(r"\"[^\"]*\"|'[^']*'|[^\s;&|<>()]+")
PATHISH = re.compile(r"[~\w./\-]*(?:agents|skills|SKILL\.md)[\w./\-]*")


def _unquote(t):
    return t[1:-1] if len(t) >= 2 and t[0] == t[-1] and t[0] in "\"'" else t


def _resolve(tok, d):
    tok = os.path.expanduser(_unquote(tok))
    return os.path.normpath(tok if os.path.isabs(tok) else os.path.join(d, tok))


def _paths_in(token, d):
    """token 本身以及 token 里出现的路径片段（如 python -c "open('…SKILL.md','w')"）解析成绝对路径。"""
    out = [_resolve(token, d)]
    raw = _unquote(token)
    if raw != token or " " in raw or "(" in raw:
        out += [_resolve(m, d) for m in PATHISH.findall(raw) if m]
    return out


def bash_touches_protected(cmd, cwd, in_subagent):
    """逐段分析命令（跟踪 cd / pushd），把出现的路径按当时的工作目录解析成绝对路径再判断。
    返回 None（放行）、"subagent"（子 agent 运行写技能层的脚本）或命中的保护目录。"""
    roots = protected_paths(cwd)
    d = os.path.abspath(cwd)
    for seg in SEGMENT.split(cmd):
        seg = seg.strip()
        if not seg:
            continue
        toks = TOKEN.findall(seg)
        if not toks:
            continue
        if toks[0] in ("cd", "pushd") and len(toks) > 1:
            d = _resolve(toks[1], d)
            continue
        if in_subagent:
            for t in toks:
                for p in _paths_in(t, d):
                    if p == ".claude" or "/.claude/agents" in p or "/.claude/skills" in p:
                        roots = roots + [p]
        # 内置脚本
        resolved = [p for t in toks for p in _paths_in(t, d)]
        writer = next((p for p in resolved if p in WRITER_SCRIPTS), None)
        if writer:
            if os.path.basename(writer) == "apply_proposal.py" and "--check" in toks:
                continue
            if in_subagent:
                return "subagent"
            continue
        if any(p in READ_ONLY_SCRIPTS for p in resolved):
            continue
        # 重定向目标
        for m in re.finditer(r"(?:^|[^0-9&>])>{1,2}\s*([^\s;&|]+)|\b[0-9]?>{1,2}\s*([^\s;&|&]+)", seg):
            target = m.group(1) or m.group(2)
            if not target or target.startswith("&") or target == "/dev/null":
                continue
            hit = under(_resolve(target, d), roots)
            if hit:
                return hit
        # 写操作 + 受保护路径（含工作目录本身在保护目录里时的相对路径）
        if WRITE_OPS.search(seg):
            for p in resolved[1:] + ([d] if toks[0] in ("rm", "touch", "tee", "cp", "mv", "sed", "perl", "python", "python3") else []):
                hit = under(p, roots)
                if hit:
                    return hit
    return None


KB_DENY_HINT = "【无人值守：用 kb_ask 请用户确认，由用户执行】"


def kb_session():
    return bool((os.environ.get("KB_SESSION") or "").strip())


def decide(evt):
    d = _decide(evt)
    if kb_session() and evt.get("tool_name") == "Bash" and (d is None or d[0] == "ask"):
        cmd = (evt.get("tool_input") or {}).get("command", "")
        label = kb_danger(cmd, evt.get("cwd") or os.getcwd())
        if not label:
            return None   # 危险字样只在参数 / 引号里，或是会话目录内的日常删除：放行
        return ("deny", KB_DENY_HINT + "知识库后台会话（KB_SESSION=%s）里没人能当场确认，这一步不执行。"
                "把要执行的命令和理由写进 kb_ask，由用户本人执行。原因：【角色 agent 安全边界】检测到「%s」类操作，"
                "需用户确认后才执行。命令：%s" % (os.environ.get("KB_SESSION", "").strip(), label, cmd[:200]))
    return d


def _decide(evt):
    tool = evt.get("tool_name", "")
    ti = evt.get("tool_input") or {}
    cwd = evt.get("cwd") or os.getcwd()
    agent = evt.get("agent_type") or ""
    if tool == "Bash":
        cmd = ti.get("command", "")
        low = cmd.lower()
        hit = bash_touches_protected(cmd, cwd, bool(agent))
        if hit == "subagent":
            return ("deny", "【角色 agent 安全边界】子 agent 不能运行写技能层的脚本（apply_proposal / build / rollback / install）。技能更新写成提案，由用户在主会话拍板后执行。")
        if hit:
            return ("deny", "【角色 agent 安全边界】不能用命令行改 agent 或技能包（命中 %s）。请把改动写成更新提案放进 %s/proposals/，用户拍板后由 apply_proposal.py 应用。" % (hit, ROOT))
        for pat, label in DANGER:
            if re.search(pat, low):
                return ("ask", "【角色 agent 安全边界】检测到「%s」类操作：任何角色都只出方案，需用户确认后才执行。命令：%s" % (label, cmd[:200]))
        return None
    path = ti.get("file_path") or ti.get("notebook_path") or ""
    if not path:
        return None
    ap = os.path.abspath(os.path.join(cwd, path))
    if under(ap, protected_paths(cwd)):
        return ("deny", "【角色 agent 安全边界】不能在执行任务时直接改 agent 或技能包（%s）。请把改动写成更新提案放进 %s/proposals/，用户拍板后由 apply_proposal.py 应用。" % (path, ROOT))
    if agent in DOC_ROLES and os.path.splitext(ap)[1].lower() in CODE_EXT:
        return ("deny", "【角色 agent 安全边界】角色「%s」只读代码 + 写文档，没有改代码文件的授权（%s）。请把改动要求交给对应的工程角色。" % (agent, path))
    return None


def main():
    try:
        evt = json.loads(sys.stdin.read() or "{}")
        d = decide(evt)
    except Exception as e:
        sys.stderr.write("guard_hook: %s\n" % e)
        return 0
    if d:
        print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": d[0],
                                                 "permissionDecisionReason": d[1]}}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
