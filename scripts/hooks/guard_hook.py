#!/usr/bin/env python3
"""REQ-011：安全边界 hook（PreToolUse，matcher: Bash|Write|Edit|MultiEdit|NotebookEdit）。纯本地，不调用模型。

- 部署、发布、git push、发推送、删除文件 / 数据库类命令 → permissionDecision=ask：停下让用户确认后才执行
- 写本套件安装的 agent / 技能文件（.claude/agents、.claude/skills 下本套件的文件，以及 worker-agent 的 agents/、data/skills/）
  → deny，提示走更新提案（proposals/ + apply_proposal.py）
- 只读代码 + 写文档的角色（hook 输入带 agent_type 时）写代码文件 → deny
- 知识库无人值守会话（环境变量 KB_SESSION 非空，REQ-018）：没人能点确认，ask 会挂住或被拒，改成 deny，
  提示改用 kb_ask 请用户确认、由用户执行。知识库自己用 Python 调 git 推送（不经过 Claude 工具）不受影响。
  deny 是硬拒，所以这时改用 kb_guard.kb_danger 逐段分析（拆 sh -c / eval / ssh / $( ) / 前缀，剥引号和 here-doc 数据）：
  引号、here-doc、只读命令参数里的字样不算；git rm、删除会话目录或临时目录里的文件放行；
  推送、部署、发布、发推送、删库、丢弃未提交改动、删工作目录以外或算不出目标的文件拒绝；
  其余认不出的命令段只要原有 DANGER 规则命中（原来会 ask）仍然拒绝。
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
            return None   # 危险字样只在引号 / here-doc / 只读命令参数里，或是会话目录内的日常删除：放行
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
