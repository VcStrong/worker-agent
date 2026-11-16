#!/usr/bin/env python3
"""把知识库历史会话日志（claude -p --output-format stream-json 的 .jsonl）里的 Bash 命令，
按会话类型带上 KB_SESSION 放到 guard_hook.decide() 下重放，看装了用户级 hooks 后哪些命令会被硬拒（REQ-018 / 020）。
纯本地，只读日志，不执行任何命令、不调用模型。

用法：
  python3 scripts/hooks/replay_guard.py <知识库根目录或 .jsonl ...> [--show 20] [--json]

会话类型按日志路径推断（与 kblib 设置 KB_SESSION 的地方对应）：
  期/<期>/开发会话/<时间>.jsonl → dev；期/<期>/开发会话/<端>开发|审查-*.jsonl → end:<端>；新会话-*.jsonl → px:
  期/<期>/开发会话/<场景>会话-*.jsonl（需求 / 发布…）→ launch:；建工程-*.jsonl → scaffold:
  期/<期>/全栈/方案会话-*.jsonl → stack:；Bug/分析会话/修复-*.jsonl → an:（修复）；Bug/分析会话/*.jsonl → an:（分析）
  _system/管家/*.jsonl → steward
输出每类会话的命令数、被拒数，以及「改前」（第 1 轮：ask 一律改 deny）的被拒数做对照。
"""
import argparse
import glob
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import guard_hook  # noqa: E402


def session_type(path):
    name = os.path.basename(path)
    parts = path.replace("\\", "/").split("/")
    if "管家" in parts:
        return "steward", "steward"
    if "分析会话" in parts:
        return ("an:修复", "an:x") if name.startswith("修复-") else ("an:分析", "an:x")
    if "全栈" in parts and name.startswith("方案会话"):
        return "stack", "stack:x"
    if name.startswith("新会话-"):
        return "px(跟进)", "px:x"
    if name.startswith("建工程-"):
        return "scaffold", "scaffold:x"
    m = re.match(r"^(.+?)(开发|审查)-\d{8}-\d{6}", name)
    if m:
        return "end:%s" % m.group(2), "end:" + m.group(1)
    m = re.match(r"^(.+?)会话-\d{8}-\d{6}", name)
    if m:
        return "launch:%s" % m.group(1), "launch:" + m.group(1)
    if "开发会话" in parts:
        return "dev", "dev"
    return None, None


def commands(path):
    cwd, out = None, []
    with open(path, encoding="utf-8", errors="replace") as f:
        for line in f:
            try:
                e = json.loads(line)
            except ValueError:
                continue
            if not isinstance(e, dict):
                continue
            if e.get("type") == "system" and e.get("cwd"):
                cwd = e["cwd"]
            msg = e.get("message") if e.get("type") == "assistant" else None
            for c in (msg or {}).get("content") or []:
                if isinstance(c, dict) and c.get("type") == "tool_use" and c.get("name") == "Bash":
                    cmd = (c.get("input") or {}).get("command")
                    if cmd:
                        out.append((cmd, cwd or os.path.dirname(path)))
    return out


def old_decide(evt):
    """第 1 轮的行为：原有判断里的 ask 一律改 deny（对照用）。"""
    d = guard_hook._decide(evt)
    return ("deny", d[1]) if d and d[0] == "ask" else d


def collect(paths):
    files = []
    for p in paths:
        if os.path.isdir(p):
            files += glob.glob(os.path.join(p, "**", "*.jsonl"), recursive=True)
        else:
            files.append(p)
    return sorted(f for f in files if "/.git/" not in f)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("paths", nargs="+")
    ap.add_argument("--show", type=int, default=20, help="每类最多列出多少条被拒命令")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    stats = {}
    saved = os.environ.get("KB_SESSION")
    try:
        for f in collect(a.paths):
            kind, env = session_type(f)
            if not kind:
                continue
            os.environ["KB_SESSION"] = env
            st = stats.setdefault(kind, {"sessions": 0, "commands": 0, "deny": 0, "deny_old": 0, "denied": []})
            cmds = commands(f)
            st["sessions"] += 1
            for cmd, cwd in cmds:
                evt = {"tool_name": "Bash", "tool_input": {"command": cmd}, "cwd": cwd}
                st["commands"] += 1
                d = guard_hook.decide(evt)
                if d and d[0] == "deny":
                    st["deny"] += 1
                    label = guard_hook.kb_danger(cmd, cwd) or "原有 deny：" + re.sub(r"^【[^】]*】", "", d[1])[:40]
                    st["denied"].append({"file": f, "cwd": cwd, "command": cmd[:300], "label": label})
                o = old_decide(evt)
                if o and o[0] == "deny":
                    st["deny_old"] += 1
    finally:
        if saved is None:
            os.environ.pop("KB_SESSION", None)
        else:
            os.environ["KB_SESSION"] = saved
    if a.json:
        print(json.dumps(stats, ensure_ascii=False, indent=2))
        return 0
    print("%-16s %6s %8s %8s %12s" % ("会话类型", "会话数", "Bash命令", "现在拒绝", "第1轮会拒绝"))
    for k in sorted(stats):
        s = stats[k]
        print("%-16s %6d %8d %8d %12d" % (k, s["sessions"], s["commands"], s["deny"], s["deny_old"]))
    for k in sorted(stats):
        for x in stats[k]["denied"][:a.show]:
            print("\n[%s 拒绝：%s] %s\n  命令：%s" % (k, x["label"], os.path.basename(x["file"]), x["command"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
