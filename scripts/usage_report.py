#!/usr/bin/env python3
"""REQ-026：角色与技能使用度排行（who.py --usage 同源）。

数据来源：
1. usage/usage.jsonl + usage/archive/*.jsonl（hook 采集，统计全部历史）
2. hook 没装或失效（没有任何 hook 记录）时，退回从各项目 workspace/*/log.md 的 <!--usage {...} --> 行统计，并提示「hook 未生效」
   项目列表来自 state/projects.json（install.sh 登记）和 --workspace 参数

用法：python3 scripts/usage_report.py [--json] [--workspace <目录>...]
"""
import argparse
import glob
import json
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "lib"))
import common  # noqa: E402


def hook_records():
    files = sorted(glob.glob(common.p("usage", "archive", "*.jsonl"))) + [common.p("usage", "usage.jsonl")]
    out = []
    for f in files:
        if not os.path.exists(f):
            continue
        for line in open(f, encoding="utf-8"):
            line = line.strip()
            if line:
                try:
                    out.append(json.loads(line))
                except ValueError:
                    pass
    return out


def log_records(extra_dirs=()):
    projects = list((common.read_json(common.p("state", "projects.json"), {}) or {}).get("projects", []))
    projects += list(extra_dirs)
    out = []
    pats = []
    for d in projects:
        pats += glob.glob(os.path.join(d, "workspace", "*", "log.md")) + glob.glob(os.path.join(d, "*", "log.md")) \
            + glob.glob(os.path.join(d, "log.md"))
    for f in sorted(set(pats)):
        for m in re.finditer(r"<!--usage\s+(\{.*?\})\s*-->", open(f, encoding="utf-8").read()):
            try:
                r = json.loads(m.group(1))
            except ValueError:
                continue
            if r.get("event") in ("call", None) and r.get("role"):
                out.append({"ts": r.get("ts", ""), "event": "call", "kind": "role",
                            "name": r["role"].split("#")[0], "project": r.get("project", os.path.dirname(f)), "need": r.get("need", "")})
            if r.get("skill"):
                out.append({"ts": r.get("ts", ""), "event": "read", "kind": "skill", "name": r["skill"],
                            "project": r.get("project", ""), "need": r.get("need", "")})
    return out


def build_report(extra_dirs=()):
    mm = common.load_merge_map()
    run = common.run_config()
    skills = common.load_skills()
    recs = [r for r in hook_records() if r.get("event") in ("call", "skill", "read")]
    source, notice = "hook", ""
    if not any(r.get("kind") == "role" for r in recs):
        fallback = log_records(extra_dirs)
        if fallback:
            recs = fallback + [r for r in recs if r.get("kind") == "skill"]
            source = "log.md"
            notice = "hook 未生效（usage/usage.jsonl 没有角色调用记录），已退回从 workspace 的 log.md 统计"
        else:
            source = "none"
            notice = "hook 没有任何角色调用记录（hook 未生效，或安装后还没调用过角色），workspace 的 log.md 里也没有记录"
    roles = {}
    for slug, info in common.active_experts(mm).items():
        mounted = [s for s in skills.values() if slug in (s["meta"].get("roles") or [])]
        dates = sorted(str(s["meta"].get("as_of")) for s in mounted if s["meta"].get("as_of"))
        stale = [s["id"] for s in mounted if (common.skill_age_days(s) or 0) > common.stale_limit(s, mm, run)]
        roles[slug] = {"slug": slug, "name": info["name"], "count": 0, "last": "", "needs": set(), "projects": set(),
                       "oldest_as_of": dates[0] if dates else "", "stale": stale}
    skl = {}
    for r in recs:
        if r.get("kind") == "role" and r.get("name") in roles:
            x = roles[r["name"]]
        elif r.get("kind") == "skill" and r.get("name") in skills:
            s = skills[r["name"]]
            x = skl.setdefault(r["name"], {"id": r["name"], "name": s["meta"].get("name", r["name"]), "count": 0, "last": "",
                                           "needs": set(), "projects": set(), "as_of": str(s["meta"].get("as_of")),
                                           "stale": (common.skill_age_days(s) or 0) > common.stale_limit(s, mm, run)})
        else:
            continue
        x["count"] += 1
        x["last"] = max(x["last"], r.get("ts", ""))
        if r.get("need"):
            x["needs"].add(r["need"])
        if r.get("project"):
            x["projects"].add(r["project"])
    has_data = any(x["count"] for x in roles.values())
    if has_data:
        ranked = sorted(roles.values(), key=lambda x: (-x["count"], x["oldest_as_of"], x["slug"]))
    else:  # 没有使用数据：按角色名排序
        ranked = sorted(roles.values(), key=lambda x: (x["name"], x["slug"]))
    sk = sorted(skl.values(), key=lambda x: (-x["count"], x["id"]))
    for x in ranked + sk:
        x["needs"], x["projects"] = sorted(x["needs"]), sorted(x["projects"])
    return {"source": source, "notice": notice, "has_data": has_data, "roles": ranked, "skills": sk}


def render(rep):
    if rep["notice"]:
        print("⚠️  " + rep["notice"])
    if not rep["has_data"]:
        print("ℹ️  暂无使用数据，按角色名排序")
    print("角色使用度（按调用次数倒序）")
    print("%-4s %-26s %6s  %-25s %-12s %s" % ("排名", "角色", "次数", "最近使用", "最旧 as_of", "过期"))
    for i, x in enumerate(rep["roles"], 1):
        print("%-4d %-26s %6d  %-25s %-12s %s" % (i, "%s（%s）" % (x["name"], x["slug"]), x["count"], x["last"] or "—",
                                                  x["oldest_as_of"] or "—", ("是：" + "、".join(x["stale"])) if x["stale"] else "否"))
    print("\n技能使用度（被按需读取 / Skill 调用）")
    if not rep["skills"]:
        print("  （暂无）")
    for x in rep["skills"]:
        print("  %-36s %4d 次  最近 %-25s as_of %s  过期 %s" % ("%s（%s）" % (x["name"], x["id"]), x["count"], x["last"] or "—",
                                                             x["as_of"], "是" if x["stale"] else "否"))


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--workspace", nargs="*", default=[], help="额外的项目目录（找 workspace/*/log.md）")
    a = ap.parse_args(argv)
    rep = build_report(a.workspace)
    if a.json:
        print(json.dumps(rep, ensure_ascii=False, indent=2))
    else:
        render(rep)
    return 0


if __name__ == "__main__":
    sys.exit(main())
