#!/usr/bin/env python3
"""REQ-026：使用度采集 hook（纯本地 Python，不调用模型、不消耗 AI 用量、永不阻断原调用）。

挂在目标项目 .claude/settings.json：
  PreToolUse（matcher: Task|Agent|Skill|Read）、SubagentStop
从 stdin 读 hook JSON，追加一行到 <worker-agent>/usage/usage.jsonl：
  {"ts","event","kind":"role|skill","name","project","need","session"}
usage.jsonl 超过 10 MB 时按月滚动到 usage/archive/usage-YYYYMM.jsonl。
"""
import datetime
import json
import os
import re
import sys

ROOT = os.environ.get("WORKER_AGENT_HOME") or os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
USAGE_DIR = os.path.join(ROOT, "usage")
USAGE = os.path.join(USAGE_DIR, "usage.jsonl")
MAX_BYTES = int(os.environ.get("WORKER_AGENT_USAGE_MAX_BYTES", 10 * 1024 * 1024))


def known():
    try:
        mm = json.load(open(os.path.join(ROOT, "data", "merge_map.json"), encoding="utf-8"))
        roles = set(mm["experts"]) | {"orchestrator", "tech-scout"}
        ovp = os.path.join(ROOT, "data", "roles_overlay.json")
        if os.path.exists(ovp):
            roles |= set((json.load(open(ovp, encoding="utf-8")).get("new_experts") or {}).keys())
    except Exception:
        roles = set()
    skills = {"who", "skills-refresh", "orchestrate"}
    sd = os.path.join(ROOT, "skills")
    if os.path.isdir(sd):
        skills |= set(os.listdir(sd))
    return roles, skills


def rotate():
    if os.path.exists(USAGE) and os.path.getsize(USAGE) > MAX_BYTES:
        arch = os.path.join(USAGE_DIR, "archive")
        os.makedirs(arch, exist_ok=True)
        dest = os.path.join(arch, "usage-%s.jsonl" % datetime.date.today().strftime("%Y%m"))
        with open(USAGE, encoding="utf-8") as src, open(dest, "a", encoding="utf-8") as out:
            out.write(src.read())
        os.remove(USAGE)


def need_from(text):
    m = re.search(r"workspace/([A-Za-z0-9._\-]+)/", text or "")
    return m.group(1) if m else ""


def records(evt):
    roles, skills = known()
    name = evt.get("hook_event_name")
    tool = evt.get("tool_name", "")
    ti = evt.get("tool_input") or {}
    out = []
    if name == "PreToolUse":
        if tool in ("Task", "Agent"):
            r = ti.get("subagent_type", "")
            if r in roles:
                out.append(("call", "role", r, need_from(ti.get("prompt", ""))))
        elif tool == "Skill":
            s = (ti.get("skill") or ti.get("command") or ti.get("name") or "").lstrip("/").split(":")[-1].split()[0:1]
            s = s[0] if s else ""
            if s in skills:
                out.append(("skill", "skill", s, ""))
        elif tool == "Read":
            m = re.search(r"skills/([a-z0-9][a-z0-9-]*)/SKILL\.md$", ti.get("file_path", ""))
            if m and m.group(1) in skills:
                out.append(("read", "skill", m.group(1), ""))
    elif name == "SubagentStop":
        r = evt.get("agent_type") or evt.get("subagent_type") or ""
        if r in roles:
            out.append(("stop", "role", r, ""))
    return out


def main():
    try:
        evt = json.loads(sys.stdin.read() or "{}")
        recs = records(evt)
        if not recs:
            return 0
        os.makedirs(USAGE_DIR, exist_ok=True)
        rotate()
        ts = datetime.datetime.now().astimezone().isoformat(timespec="seconds")
        with open(USAGE, "a", encoding="utf-8") as f:
            for event, kind, nm, need in recs:
                f.write(json.dumps({"ts": ts, "event": event, "kind": kind, "name": nm,
                                    "project": evt.get("cwd") or os.getcwd(), "need": need,
                                    "session": evt.get("session_id", "")}, ensure_ascii=False) + "\n")
    except Exception as e:  # 永不影响原调用
        sys.stderr.write("usage_hook: %s\n" % e)
    return 0


if __name__ == "__main__":
    sys.exit(main())
