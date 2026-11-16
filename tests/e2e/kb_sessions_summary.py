"""汇总 tests/e2e/kb_sessions.sh 的会话日志：每类会话每条 Bash 命令是放行、被 hook 拒绝还是命令自身出错。"""
import glob, json, os, sys

for f in sorted(glob.glob(os.path.join(sys.argv[1] if len(sys.argv) > 1 else "/tmp/kbhook-e2e/sessions", "*.jsonl"))):
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
    kind = os.path.basename(f)[:-6]
    print("== %s  result=%s cost=%s bash=%d" % (kind, final, cost, len(uses)))
    for i, (tid, cmd) in enumerate(uses.items(), 1):
        err, txt = results.get(tid, (None, "(no result)"))
        tag = "HOOK-DENY" if "无人值守" in txt else ("ERROR" if err else "ok")
        print("   %d. %-9s %s%s" % (i, tag, cmd.replace("\n", "⏎")[:80], ("  | " + txt.replace("\n", " ")[:70]) if tag == "ERROR" else ""))
