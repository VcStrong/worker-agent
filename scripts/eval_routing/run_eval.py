#!/usr/bin/env python3
"""REQ-003：选角评测。

离线模式（默认）：用 agents 的路由线索（专家名、合并来源岗位名、典型活儿、术语、技能）做确定性打分，
近似宿主 AI 读 description 选角；不调用模型、可重复。
--llm 模式：把 16 个 agent 的 description 交给 `claude -p --model haiku` 选角（会消耗 AI 用量，手动跑）。

输出首选命中率；--save 写 scripts/eval_routing/last_result.json 供回归比较（REQ-024）。
退出码：命中率 < --min（默认 0.85）时为 1。
"""
import argparse
import glob
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "lib"))
import common  # noqa: E402
import index  # noqa: E402


def llm_route(task, descs):
    menu = "\n".join("- %s: %s" % (k, v) for k, v in descs.items())
    prompt = ("下面是可用的子 agent 及其 description。对任务只回答最合适的一个 agent name，不要解释。\n%s\n\n任务：%s" % (menu, task))
    out = subprocess.run(["claude", "-p", "--model", "haiku", prompt], capture_output=True, text=True, timeout=120)
    m = re.search(r"[a-z]+(?:-[a-z]+)+|orchestrator", out.stdout)
    return m.group(0) if m else out.stdout.strip()


def evaluate(llm=False, verbose=True):
    cases = common.read_json(os.path.join(HERE, "cases.json"))["cases"]
    idx = index.Index()
    descs = {}
    if llm:
        for f in sorted(glob.glob(common.p("agents", "*.md"))):
            t = open(f, encoding="utf-8").read()
            descs[os.path.basename(f)[:-3]] = re.search(r"^description: (.*)$", t, re.M).group(1)
    results = []
    for c in cases:
        if llm:
            got = llm_route(c["task"], descs)
            ranked = [got]
        else:
            ranked = [s for s, _ in idx.route(c["task"], top=3)]
            got = ranked[0] if ranked else None
        ok = got == c["expect"] or got in (c.get("also_ok") or [])
        results.append({"task": c["task"], "expect": c["expect"], "got": got, "top3": ranked, "ok": ok})
    hit = sum(r["ok"] for r in results) / len(results)
    if verbose:
        for r in results:
            print("%s %-34s 期望 %-24s 得到 %s" % ("✅" if r["ok"] else "❌", r["task"][:34], r["expect"], r["got"]))
        print("首选命中率：%.1f%%（%d/%d），原始岗位名问法：%d/%d" % (
            hit * 100, sum(r["ok"] for r in results), len(results),
            sum(r["ok"] for r, c in zip(results, cases) if c.get("kind") == "raw_role"),
            sum(1 for c in cases if c.get("kind") == "raw_role")))
    return hit, results


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--llm", action="store_true")
    ap.add_argument("--min", type=float, default=0.85)
    ap.add_argument("--save", action="store_true", help="离线结果写 last_result.json（install --update / apply_proposal 的回归基线）；--llm 时写 last_result_llm.json")
    ap.add_argument("--quiet", action="store_true")
    a = ap.parse_args()
    hit, results = evaluate(a.llm, not a.quiet)
    if a.save:
        common.write_json(os.path.join(HERE, "last_result_llm.json" if a.llm else "last_result.json"), {"hit_rate": hit, "mode": "llm(claude -p --model haiku)" if a.llm else "offline", "ts": common.now_iso(), "results": results})
    return 0 if hit >= a.min else 1


if __name__ == "__main__":
    sys.exit(main())
