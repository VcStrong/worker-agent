#!/usr/bin/env python3
"""REQ-024：技能回归题（每个专家 ≥ 3 条「场景 → 期望做法」）。离线、确定性，检查生成的 agent 和技能层：

case 字段：
  id, role, scenario
  expect_adopt: [技能id]       这些技能挂在该角色上，且（按 region）成熟度为「采用」，agent 技能清单的「采用」组里有它
  expect_not_adopt: [技能id]   这些技能不是「采用」
  expect_paused: 技能id         成熟度为「暂缓」，并且 agent 里写了替代项 expect_alt
  expect_alt: [技能id]
  agent_contains: [文本]        agents/<role>.md 必须包含
  region: cn|global             按指定 region 计算（模拟 radar.yaml 切换）

用法：python3 scripts/eval_skills/run_skill_eval.py [--save] [--quiet]
"""
import argparse
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "lib"))
import common  # noqa: E402


def adopt_block(agent_text):
    m = re.search(r"^### 采用\n(.*?)(?=^### |^## |\Z)", agent_text, re.S | re.M)
    return m.group(1) if m else ""


def evaluate(verbose=True):
    cases = common.read_json(os.path.join(HERE, "cases.json"))["cases"]
    skills = common.load_skills()
    radar = common.radar_config()
    results = []
    for c in cases:
        why = []
        role = c["role"]
        path = common.p("agents", role + ".md")
        text = open(path, encoding="utf-8").read() if os.path.exists(path) else ""
        if not text:
            why.append("agent 文件不存在")
        rd = dict(radar, region=c["region"]) if c.get("region") else radar
        for sid in c.get("expect_adopt", []):
            s = skills.get(sid)
            if not s:
                why.append("技能 %s 不存在" % sid)
                continue
            if role not in (s["meta"].get("roles") or []):
                why.append("%s 没挂在 %s 上" % (sid, role))
            if common.effective_maturity(s, rd) != "采用":
                why.append("%s 不是采用（%s）" % (sid, common.effective_maturity(s, rd)))
            elif not c.get("region") and "`%s`" % sid not in adopt_block(text):
                why.append("agent 的「采用」组里没有 %s" % sid)
        for sid in c.get("expect_not_adopt", []):
            s = skills.get(sid)
            if s and common.effective_maturity(s, rd) == "采用":
                why.append("%s 不应是采用" % sid)
        if c.get("expect_paused"):
            sid = c["expect_paused"]
            s = skills.get(sid)
            if not s or common.effective_maturity(s, rd) != "暂缓":
                why.append("%s 应为暂缓" % sid)
            for alt in c.get("expect_alt", []):
                name = skills[alt]["meta"].get("name", alt) if alt in skills else alt
                if name not in text and alt not in text:
                    why.append("agent 里没写替代项 %s" % alt)
        for t in c.get("agent_contains", []):
            if t not in text:
                why.append("agent 缺少「%s」" % t)
        results.append({"id": c["id"], "role": role, "scenario": c["scenario"], "ok": not why, "why": "；".join(why)})
    rate = sum(r["ok"] for r in results) / max(1, len(results))
    if verbose:
        for r in results:
            print("%s %-8s %-22s %s %s" % ("✅" if r["ok"] else "❌", r["id"], r["role"], r["scenario"][:40], r["why"]))
        print("技能回归题通过率：%.1f%%（%d/%d）" % (rate * 100, sum(r["ok"] for r in results), len(results)))
    return rate, results


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--save", action="store_true")
    ap.add_argument("--quiet", action="store_true")
    a = ap.parse_args()
    rate, results = evaluate(not a.quiet)
    if a.save:
        common.write_json(os.path.join(HERE, "last_result.json"), {"pass_rate": round(rate, 4), "results": results})
    return 0 if rate == 1 else 1


if __name__ == "__main__":
    sys.exit(main())
