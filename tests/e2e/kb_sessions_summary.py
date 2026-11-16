"""汇总 tests/e2e/kb_sessions.sh 的会话日志：每类会话每条 Bash 命令是放行、被 hook 拒绝还是命令自身出错，
并按预期核对（第 1～4 条执行成功、第 5～6 条被 hook 拒绝、会话正常结束）。不符合预期时退出码 1。

用法：python3 tests/e2e/kb_sessions_summary.py [日志目录，默认 /tmp/kbhook-e2e/sessions]
"""
import glob
import json
import os
import sys

EXPECT = ["ok", "ok", "ok", "ok", "HOOK-DENY", "HOOK-DENY"]


def parse(f):
    uses, results, final, cost = {}, {}, None, None
    for line in open(f, encoding="utf-8", errors="replace"):
        try:
            e = json.loads(line)
        except ValueError:
            continue
        if e.get("type") == "assistant":
            for c in e["message"].get("content") or []:
                if c.get("type") == "tool_use" and c.get("name") == "Bash":
                    uses[c["id"]] = c["input"].get("command", "")
        if e.get("type") == "user":
            for c in (e.get("message") or {}).get("content") or []:
                if isinstance(c, dict) and c.get("type") == "tool_result":
                    txt = c.get("content")
                    if isinstance(txt, list):
                        txt = " ".join(x.get("text", "") for x in txt if isinstance(x, dict))
                    results[c["tool_use_id"]] = (bool(c.get("is_error")), str(txt))
        if e.get("type") == "result":
            final, cost = e.get("subtype"), e.get("total_cost_usd")
    rows = []
    for tid, cmd in uses.items():
        err, txt = results.get(tid, (None, "(no result)"))
        tag = "HOOK-DENY" if "无人值守" in txt else ("ERROR" if err else "ok")
        rows.append((tag, cmd, txt))
    return final, cost, rows


def main():
    d = sys.argv[1] if len(sys.argv) > 1 else "/tmp/kbhook-e2e/sessions"
    files = sorted(glob.glob(os.path.join(d, "*.jsonl")))
    bad = 0
    for f in files:
        final, cost, rows = parse(f)
        tags = [r[0] for r in rows]
        ok = final == "success" and tags == EXPECT
        bad += not ok
        print("== %s  %s  result=%s cost=%s bash=%d" % (os.path.basename(f)[:-6], "符合预期" if ok else "不符合预期",
                                                        final, cost, len(rows)))
        for i, (tag, cmd, txt) in enumerate(rows, 1):
            extra = ("  | " + txt.replace("\n", " ")[:90]) if tag != "HOOK-DENY" and i == 3 or tag == "ERROR" else ""
            print("   %d. %-9s %s%s" % (i, tag, cmd.replace("\n", "⏎")[:80], extra))
    print("共 %d 类会话，不符合预期 %d 类" % (len(files), bad))
    return 1 if bad or not files else 0


if __name__ == "__main__":
    sys.exit(main())
