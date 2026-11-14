#!/usr/bin/env python3
"""REQ-011：安全边界 hook（PreToolUse，matcher: Bash|Write|Edit|MultiEdit|NotebookEdit）。纯本地，不调用模型。

- 部署、发布、git push、发推送、删除文件 / 数据库类命令 → permissionDecision=ask：停下让用户确认后才执行
- 写本套件安装的 agent / 技能文件（.claude/agents、.claude/skills 下本套件的文件，以及 worker-agent 的 agents/、data/skills/）
  → deny，提示走更新提案（proposals/ + apply_proposal.py）
- 只读代码 + 写文档的角色（hook 输入带 agent_type 时）写代码文件 → deny
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


def protected_paths(cwd):
    out = [os.path.join(ROOT, "agents") + os.sep, os.path.join(ROOT, "data", "skills") + os.sep]
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


def decide(evt):
    tool = evt.get("tool_name", "")
    ti = evt.get("tool_input") or {}
    cwd = evt.get("cwd") or os.getcwd()
    agent = evt.get("agent_type") or ""
    if tool == "Bash":
        cmd = ti.get("command", "")
        low = cmd.lower()
        for pat, label in DANGER:
            if re.search(pat, low):
                return ("ask", "【角色 agent 安全边界】检测到「%s」类操作：任何角色都只出方案，需用户确认后才执行。命令：%s" % (label, cmd[:200]))
        return None
    path = ti.get("file_path") or ti.get("notebook_path") or ""
    if not path:
        return None
    ap = os.path.abspath(os.path.join(cwd, path))
    for p in protected_paths(cwd):
        if ap == p or ap.startswith(p):
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
