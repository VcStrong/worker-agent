#!/usr/bin/env python3
"""REQ-011：安全边界 hook（PreToolUse，matcher: Bash|Write|Edit|MultiEdit|NotebookEdit）。纯本地，不调用模型。

默认不拦截：角色套件只协助、不比 Claude Code 本身管得更严。不开严格模式时本 hook 什么都不输出，
放行与否完全交给 Claude Code 自己的权限设置（permission mode、allow / deny 规则、auto 模式分类器）。
安装默认也不注册本 hook；想要下面的严格规则时显式打开：`./install.sh --guard`（注册为 `guard_hook.py --strict`），
或环境变量 WORKER_AGENT_GUARD=strict。以下规则只在严格模式下生效：

- 部署、发布、强推、发推送、删库类命令 → permissionDecision=ask：停下让用户确认后才执行。
  常用命令（普通 git push、rm / find -delete、git reset --hard / clean -f / branch -D）用户已授权，直接放行（COMMON_ALLOW），
  其中强推、+ 推送、删远端分支、sudo 删除、删 / 或 ~ 仍 ask（common_risky）。
- 写本套件安装的 agent / 技能文件（.claude/agents、.claude/skills 下本套件的文件，以及 worker-agent 的 agents/、data/skills/）
  → deny，提示走更新提案（proposals/ + apply_proposal.py）
- 只读代码 + 写文档的角色（hook 输入带 agent_type 时）写代码文件 → deny
- 知识库无人值守会话（环境变量 KB_SESSION 非空，REQ-018）：交互会话放行的常用命令同样放行（免打扰不被卡住）；
  交互会话会 ask 的命令没人能点确认，ask 会挂住或被拒，改成 deny，
  提示改用 kb_ask 请用户确认、由用户执行。知识库自己用 Python 调 git 推送（不经过 Claude 工具）不受影响。
  deny 是硬拒，所以这时改用 kb_guard.kb_danger 逐段分析（拆 sh -c / eval / ssh / $( ) / 前缀，剥引号和 here-doc 数据）：
  引号、here-doc、只读命令参数里的字样不算；git rm、删除会话目录或临时目录里的文件放行；
  推送、部署、发布、发推送、删库、丢弃未提交改动、删工作目录以外或算不出目标的文件拒绝；
  其余认不出的命令段只要原有 DANGER 规则命中（原来会 ask）仍然拒绝。
  例外（变更 CR-002）：KB_SESSION=dev 或 px:* 时，整条命令里每个 git push 段都只推 refs/for/<分支> 送审
  （无 + 前缀、无强推 / --all / --tags / --mirror / --delete / --prune、%选项和 -o 里无 submit / l= / label=）时放行。
"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kb_guard  # noqa: E402

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


# ---------- 知识库会话（KB_SESSION）：判断逻辑在 kb_guard.py ----------
def kb_danger(cmd, cwd):
    """知识库会话里要硬拒的操作，返回标签；放行返回 None。认不出的命令按上面 DANGER（原有 ask 规则）兜底。"""
    return kb_guard.kb_danger(cmd, cwd, DANGER)


def gerrit_session():
    """只有 SDD 开发会话（KB_SESSION=dev）和跟进会话（px:*）适用 Gerrit 送审例外（REQ-018，变更 CR-002）。"""
    s = (os.environ.get("KB_SESSION") or "").strip()
    return s == "dev" or s.startswith("px:")


def kb_gerrit_review_push(cmd, cwd):
    """整条命令按 kb_danger 同样的方式拆段（sh -c / eval / $( ) / 前缀 / 引号 / git -C、-c 全局选项），
    其中每个 git push 段都只推 refs/for/<分支> 送审（REQ-018 的 4 个条件）、其余段也没有要拒的操作时返回 True。
    只在 gerrit_session() 为真时调用；ssh 远程命令里的 push 不放行。"""
    return kb_guard.kb_danger(cmd, cwd, DANGER, review=True) is None

# 日常开发常用、用户已授权直接放行的类别（交互会话不再弹确认；知识库无人值守会话仍走 kb_danger，不受影响）。
# 其中的危险写法由 common_risky 单独拦下，照旧弹确认。
COMMON_ALLOW = {"git push", "删除文件", "丢弃代码 / 删除分支"}
FORCE_PUSH = re.compile(r"\bgit\b[^;&|\n]*\bpush\b[^;&|\n]*(\s--force(-with-lease)?\b|\s-[a-z]*f[a-z]*\b|\s\+\S|\s--mirror\b|\s--delete\b|\s-d\b|\s:\S)")
SUDO_RM = re.compile(r"\bsudo\s+(rm|rmdir|find|shred)\b")
GIT_PUSH = re.compile(r"\bgit\b[^;&|\n]*?\bpush\b")
RM_ROOT = re.compile(r"\brm\s+(-[a-z]+\s+)*(/|~|~/|\$home|\$\{home\}|/\*|~/\*)(\s|$|[;&|'\"])")


def common_risky(low):
    """常用类别里仍要确认的写法：强推 / 删远端分支、sudo 删除、删根目录或家目录。"""
    if FORCE_PUSH.search(low):
        return "强推 / 删除远端分支"
    if SUDO_RM.search(low):
        return "sudo 删除文件"
    if RM_ROOT.search(low):
        return "删除根目录或家目录"
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


STRICT_VALUES = {"strict", "1", "on", "true", "yes"}


def strict_mode(argv=None):
    """严格模式：命令行带 --strict（install.sh --guard 注册的写法），或 WORKER_AGENT_GUARD=strict。"""
    if "--strict" in (sys.argv[1:] if argv is None else argv):
        return True
    return (os.environ.get("WORKER_AGENT_GUARD") or "").strip().lower() in STRICT_VALUES


def decide(evt, strict=None):
    """返回 (permissionDecision, reason) 或 None（不出决定）。默认模式一律 None。"""
    if not (strict_mode() if strict is None else strict):
        return None
    d = _decide(evt)
    # 知识库会话：交互会话放行的常用命令（COMMON_ALLOW）同样放行，免打扰时不被拒、不卡住；
    # 交互会话会 ask 的（强推、sudo 删除、部署发布、删库…）才交给 kb_danger 细判，认定危险就拒绝。
    if kb_session() and evt.get("tool_name") == "Bash" and d is not None and d[0] == "ask":
        cmd = (evt.get("tool_input") or {}).get("command", "")
        label = kb_danger(cmd, evt.get("cwd") or os.getcwd())
        if not label:
            return None   # 危险字样只在引号 / here-doc / 只读命令参数里，或是会话目录内的日常删除：放行
        if label == "git push" and gerrit_session() and kb_gerrit_review_push(cmd, evt.get("cwd") or os.getcwd()):
            return None   # SDD 开发 / 跟进会话推 Gerrit 送审（refs/for，需人工 +2 才合入）：放行（变更 CR-002）
        return ("deny", KB_DENY_HINT + "知识库后台会话（KB_SESSION=%s）里没人能当场确认，这一步不执行。"
                "把要执行的命令和理由写进 kb_ask，由用户本人执行。原因：【角色 agent 安全边界】检测到「%s」类操作，"
                "需用户确认后才执行。命令：%s" % (os.environ.get("KB_SESSION", "").strip(), label, cmd[:200]))
    return d


def _decide(evt, allow_common=True):
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
        risky = common_risky(low) if allow_common else None
        if risky:
            return ("ask", "【角色 agent 安全边界】检测到「%s」：需用户确认后才执行。命令：%s" % (risky, cmd[:200]))
        no_git_push = GIT_PUSH.sub("git-p", low)   # 「发推送」规则别把 git push 的 push 字样当成发推送
        for pat, label in DANGER:
            if allow_common and label in COMMON_ALLOW:
                continue
            if re.search(pat, no_git_push if allow_common and label == "发推送" else low):
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
