#!/usr/bin/env python3
"""REQ-028：技能更新提醒（只提醒，用户批准后才执行 /skills-refresh）。纯本地脚本，不调用模型。

由 SessionStart hook 运行（--hook）。满足任一条件才提醒：
  - 距上次 /skills-refresh 超过 refresh_remind_days（默认 30 天）
  - 有技能包 as_of 超过 stale_days（普通 180 天、AI 领域 90 天）
同一天最多提醒一次；用户回「暂缓 N 天」时运行 --snooze N。

用法：
  python3 scripts/refresh_check.py            # 打印提醒（不满足条件时不输出）
  python3 scripts/refresh_check.py --hook     # SessionStart hook：输出 JSON（systemMessage + additionalContext）
  python3 scripts/refresh_check.py --snooze 7 # 暂缓 7 天
  python3 scripts/refresh_check.py --mark-refreshed   # /skills-refresh 完成后记录时间
  python3 scripts/refresh_check.py --force    # 忽略当天去重和暂缓（调试用）
"""
import argparse
import datetime
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "lib"))
import common  # noqa: E402

STATE = common.p("state", "refresh_state.json")


def load_state():
    return common.read_json(STATE, {}) or {}


def save_state(st):
    common.write_json(STATE, st)


def last_refresh(st):
    """取最近一次：--mark-refreshed 记录、skills.lock 快照日期、情报员提案文件日期。
    提案文件只认第一行带 `<!-- source: tech-scout -->` 标记的（手写提案、测试文件不算），日期晚于今天的忽略。"""
    import glob
    import re
    cands = [common.parse_date(st.get("last_refresh") or "")]
    lock = common.read_json(common.p("skills.lock"), {}) or {}
    cands.append(common.parse_date(lock.get("created") or ""))
    for f in glob.glob(common.p("proposals", "*.md")):
        m = re.match(r"(\d{4}-\d{2}-\d{2})-", os.path.basename(f))
        if not m:
            continue
        with open(f, encoding="utf-8") as fh:
            if "<!-- source: tech-scout" not in fh.readline():
                continue
        cands.append(common.parse_date(m.group(1)))
    today = common.today()
    cands = [c for c in cands if c and c <= today]
    return max(cands) if cands else None


def check(st):
    import usage_report
    run = common.run_config()
    today = common.today()
    reasons = []
    lr = last_refresh(st)
    days = (today - lr).days if lr else None
    if days is not None and days > int(run.get("refresh_remind_days", 30)):
        reasons.append("距上次 /skills-refresh 已 %d 天（阈值 %s 天）" % (days, run.get("refresh_remind_days", 30)))
    rep = usage_report.build_report()
    stale_roles = [r for r in rep["roles"] if r["stale"]]
    stale_ids = sorted({s for r in stale_roles for s in r["stale"]})
    if stale_ids:
        reasons.append("%d 个技能包已过期" % len(stale_ids))
    return reasons, rep, stale_ids, days


def source_count(roles):
    src = (common.read_yaml(common.p("config", "sources.yaml"), {}) or {}).get("sources", [])
    return len([s for s in src if set(s.get("roles") or []) & set(roles)])


def message(reasons, rep, stale_ids, days):
    roles = [r for r in rep["roles"]]
    suggest = [r for r in roles if r["stale"]] or roles[:5]
    lines = ["🔔 角色技能更新提醒：%s。" % "；".join(reasons)]
    if not rep["has_data"]:
        lines.append("（暂无使用数据，按角色名排序）")
    lines.append("按使用度倒序（次数｜最旧 as_of｜是否过期）：")
    for r in roles:
        lines.append("  - %s（%s）：%d 次｜%s｜%s" % (r["name"], r["slug"], r["count"], r["oldest_as_of"] or "—",
                                                 ("过期：" + "、".join(r["stale"])) if r["stale"] else "未过期"))
    if stale_ids:
        lines.append("过期技能：%s" % "、".join(stale_ids))
    sel = [r["slug"] for r in suggest]
    lines.append("建议更新：%s（预计侦察 %d 个信息源）。" % ("、".join(r["name"] for r in suggest), source_count(sel)))
    lines.append("回复要更新的角色后才会开始（执行 /skills-refresh <角色…>），不回复不会消耗 AI 用量；"
                 "回复「暂缓 N 天」则运行 `python3 %s --snooze N`。" % common.p("scripts", "refresh_check.py"))
    return "\n".join(lines)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--hook", action="store_true")
    ap.add_argument("--snooze", type=int)
    ap.add_argument("--mark-refreshed", action="store_true")
    ap.add_argument("--force", action="store_true")
    a = ap.parse_args(argv)
    st = load_state()
    today = common.today()
    if a.snooze is not None:
        st["snooze_until"] = (today + datetime.timedelta(days=a.snooze)).isoformat()
        save_state(st)
        print("✅ 已暂缓更新提醒 %d 天（到 %s 前不再提醒）" % (a.snooze, st["snooze_until"]))
        return 0
    if a.mark_refreshed:
        st["last_refresh"] = today.isoformat()
        save_state(st)
        print("✅ 已记录本次技能侦察时间 %s" % st["last_refresh"])
        return 0
    try:
        if not a.force:
            if st.get("last_remind") == today.isoformat():
                return 0
            su = common.parse_date(st.get("snooze_until") or "")
            if su and today < su:
                return 0
        reasons, rep, stale_ids, days = check(st)
        if not reasons:
            return 0
        msg = message(reasons, rep, stale_ids, days)
        st["last_remind"] = today.isoformat()
        save_state(st)
        if a.hook:
            ctx = msg + ("\n（给 AI 的说明：请把这段提醒原样简短转告用户；如果 kb MCP 可用且在知识库某一期里，用 kb_log 记一条「技能更新提醒」；"
                         "在用户明确回复要更新哪些角色之前，不要运行 /skills-refresh 或调用技术情报员。）")
            print(json.dumps({"systemMessage": msg.splitlines()[0] + " 详情见会话开头。",
                              "hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": ctx}}, ensure_ascii=False))
        else:
            print(msg)
    except Exception as e:  # hook 永不阻断会话
        sys.stderr.write("refresh_check: %s\n" % e)
    return 0


if __name__ == "__main__":
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    sys.exit(main())
