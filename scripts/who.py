#!/usr/bin/env python3
"""REQ-008：按岗位名、专家名、术语、技术名反查负责的专家角色。

用法：
  python3 scripts/who.py 灰度            # 术语 → 相关角色 + 命中的术语组
  python3 scripts/who.py 后端工程师      # 专家名 → 完整档案摘要（含合并了哪些原始岗位）
  python3 scripts/who.py DBA             # 原始岗位名 → 合并到的专家；HRBP → 不做 agent 及原因
  python3 scripts/who.py ArkTS           # 技能层技术名 → 挂载角色、成熟度、as_of；暂缓时显示替代
  python3 scripts/who.py --usage         # 使用度排行（同 scripts/usage_report.py）
  python3 scripts/who.py --json <词>     # JSON 输出
"""
import argparse
import difflib
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "lib"))
import common  # noqa: E402
import index  # noqa: E402


def stage_names():
    return {s["no"]: s["short"] for s in (common.read_json(common.p("data", "stages.json"), {}) or {}).get("stages", [])}


def fmt_stages(nums, names):
    return "、".join("%02d %s" % (n, names.get(n, "")) for n in nums) or "—"


class Who:
    def __init__(self):
        self.idx = index.Index()
        self.mm = self.idx.mm
        self.names = stage_names()

    def expert_name(self, slug):
        if slug in self.mm["experts"]:
            return self.mm["experts"][slug]["name"]
        return {"orchestrator": "总控（兼项目经理）", "none": "不做 agent", "tech-scout": "技术情报员"}.get(slug, slug)

    # ---- 各类命中 ----
    def find_expert(self, q):
        nq = index.norm(q)
        for slug, info in self.mm["experts"].items():
            if nq in (index.norm(slug), index.norm(info["name"])) or nq in [index.norm(x) for x in index.split_name(info["name"])]:
                return slug
        if nq in ("总控", "orchestrator"):
            return "orchestrator"
        if nq in ("技术情报员", "tech-scout", "情报员"):
            return "tech-scout"
        return None

    def find_roles(self, q):
        nq = index.norm(q)
        out = []
        for rid, r in self.idx.roles.items():
            if nq == index.norm(rid) or nq == index.norm(r["name"]) or nq in [index.norm(x) for x in index.split_name(r["name"])]:
                out.append(r)
        return out

    def find_skills(self, q):
        nq = index.norm(q)
        out = []
        for s in self.idx.skills.values():
            names = [s["id"], s["meta"].get("name", "")] + list(s["meta"].get("aliases") or [])
            if any(nq == index.norm(n) or (len(nq) >= 3 and nq in index.norm(n)) for n in names):
                out.append(s)
        return out

    def find_terms(self, q):
        """术语 → [(slug, 原始岗位, 术语组, 术语)]"""
        nq = index.norm(q)
        hits = []
        for rid, r in self.idx.roles.items():
            target = self.mm["map"].get(rid, {}).get("target")
            for g in r.get("terms", []):
                for t in g["terms"]:
                    if nq == index.norm(t) or (len(nq) >= 2 and nq in index.norm(t)):
                        hits.append((target, rid, r["name"], g["group"], t))
            for t in r.get("tools", []):
                if nq in index.norm(t["name"]):
                    hits.append((target, rid, r["name"], "图谱工具（%s，%s）" % (t["source"], t["date"]), t["name"]))
        for slug, ex in self.idx.experts.items():
            for t in ex.get("terms", []) + ex.get("tasks", []):
                if nq == index.norm(t) or (len(nq) >= 2 and nq in index.norm(t)):
                    hits.append((slug, "-", self.expert_name(slug), "专家高频术语 / 典型活儿", t))
        return hits

    # ---- 输出 ----
    def profile(self, slug):
        if slug in ("orchestrator", "tech-scout"):
            merged = [rid for rid, m in self.mm["map"].items() if m["target"] == slug]
            return {"type": "expert", "slug": slug, "name": self.expert_name(slug),
                    "merged": [{"id": r, "name": self.idx.roles[r]["name"]} for r in merged if r in self.idx.roles],
                    "summary": "总控：判断规模和起始阶段、选角、调度、拍板、日志、仲裁、经验收集" if slug == "orchestrator"
                    else "技术情报员：只在 /skills-refresh 时侦察技术变化、出更新提案"}
        ex = self.idx.experts.get(slug, {})
        info = self.mm["experts"][slug]
        skills = []
        for s in self.idx.skills.values():
            if slug in (s["meta"].get("roles") or []):
                skills.append({"id": s["id"], "name": s["meta"].get("name"), "maturity": common.effective_maturity(s, self.idx.radar),
                               "as_of": str(s["meta"].get("as_of"))})
        return {
            "type": "expert", "slug": slug, "name": info["name"], "model": info.get("model"),
            "retired": info.get("retired"),
            "summary": ex.get("summary"), "lead_stages": fmt_stages(ex.get("lead_stages", []), self.names),
            "stages": fmt_stages(ex.get("stages", []), self.names),
            "merged": [{"id": rid, "name": self.idx.roles[rid]["name"], "primary": p}
                       for rid, p in common.expert_roles(self.mm, slug) if rid in self.idx.roles],
            "outputs": [o["name"] for o in ex.get("outputs", [])], "tasks": ex.get("tasks", []),
            "skills": skills,
        }

    def role_result(self, r):
        m = self.mm["map"].get(r["id"], {})
        target = m.get("target")
        res = {"type": "raw_role", "id": r["id"], "name": r["name"], "target": target,
               "target_name": self.expert_name(target), "positioning": r.get("positioning")}
        if target == "none":
            res["reason"] = m.get("reason", "")
        if m.get("also"):
            res["also"] = [self.expert_name(a) for a in m["also"]]
        if m.get("note"):
            res["note"] = m["note"]
        return res

    def skill_result(self, s):
        meta = s["meta"]
        mat = common.effective_maturity(s, self.idx.radar)
        res = {"type": "skill", "id": s["id"], "name": meta.get("name"), "maturity": mat, "as_of": str(meta.get("as_of")),
               "version": meta.get("version"), "region": meta.get("region", "both"),
               "roles": [{"slug": r, "name": self.expert_name(r)} for r in meta.get("roles") or []],
               "sources": meta.get("sources") or [], "layer": s["layer"], "from_graph": bool(meta.get("from_graph"))}
        if mat == "暂缓":
            alts = meta.get("replaced_by") or []
            res["alternatives"] = [{"id": a, "name": self.idx.skills[a]["meta"].get("name", a) if a in self.idx.skills else a} for a in alts]
            res["reason"] = index_first(common.sections(s["body"]).get("替代", ""))
        return res

    def query(self, q):
        results = []
        slug = self.find_expert(q)
        if slug:
            results.append(self.profile(slug))
        for r in self.find_roles(q):
            results.append(self.role_result(r))
        for s in self.find_skills(q):
            results.append(self.skill_result(s))
        terms = self.find_terms(q)
        if terms and not slug:
            agg = {}
            for target, rid, rname, group, t in terms:
                a = agg.setdefault(target, {"slug": target, "name": self.expert_name(target), "groups": set(), "from": set(), "count": 0})
                a["groups"].add("%s：%s" % (group, t))
                a["from"].add("%s %s" % (rid, rname) if rid != "-" else rname)
                a["count"] += 3 if rid == "-" else 1
            ranked = sorted(agg.values(), key=lambda a: (-a["count"], a["slug"] or ""))
            for a in ranked:
                ex = self.idx.experts.get(a["slug"], {})
                results.append({"type": "term", "query": q, "slug": a["slug"], "name": a["name"],
                                "lead_stages": fmt_stages(ex.get("lead_stages", []), self.names),
                                "hits": sorted(a["groups"]), "from": sorted(a["from"]), "count": a["count"]})
        if not results:
            vocab = [v["display"] for v in self.idx.vocab.values()] + [s["meta"].get("name", s["id"]) for s in self.idx.skills.values()]
            close = difflib.get_close_matches(q, vocab, n=3, cutoff=0.0)
            return {"found": False, "query": q, "suggest": close}
        return {"found": True, "query": q, "results": results}


def self_name(slug):
    mm = common.load_merge_map()
    return mm["experts"].get(slug, {}).get("name", slug)


def index_first(text):
    for line in text.splitlines():
        line = line.strip().lstrip("-* ").strip()
        if line:
            return line
    return ""


def render(res):
    if not res["found"]:
        print("未找到「%s」。最接近的词：%s" % (res["query"], "、".join(res["suggest"])))
        return
    for r in res["results"]:
        t = r["type"]
        if t == "expert":
            print("🧑‍💼 专家：%s（%s%s）" % (r["name"], r["slug"], "，model " + r["model"] if r.get("model") else ""))
            if r.get("retired"):
                rep_slug = r["retired"].get("replacement", "")
                print("   ⛔ 已下线，替代：%s（%s）" % (self_name(rep_slug), rep_slug))
            print("   定位：%s" % r.get("summary"))
            if r.get("lead_stages"):
                print("   主导阶段：%s；参与：%s" % (r["lead_stages"], r.get("stages")))
            print("   合并了原始岗位：%s" % "、".join("%s %s%s" % (m["id"], m["name"], "" if m.get("primary", True) else "（部分）") for m in r["merged"]))
            if r.get("outputs"):
                print("   产出：%s" % "、".join(r["outputs"]))
            if r.get("tasks"):
                print("   典型活儿：%s" % "、".join(r["tasks"]))
            if r.get("skills"):
                groups = {}
                for s in r["skills"]:
                    groups.setdefault(s["maturity"], []).append(s["name"])
                print("   技能：" + "；".join("%s：%s" % (m, "、".join(groups[m])) for m in common.MATURITIES if m in groups))
        elif t == "raw_role":
            if r["target"] == "none":
                print("📇 原始岗位 %s %s → 不做 agent。原因：%s" % (r["id"], r["name"], r.get("reason")))
            else:
                extra = ("；%s" % r["note"]) if r.get("note") else ""
                print("📇 原始岗位 %s %s → 已合并到「%s」（%s）%s" % (r["id"], r["name"], r["target_name"], r["target"], extra))
        elif t == "skill":
            print("🧰 技能：%s（%s）成熟度 %s｜as_of %s｜v%s｜region %s%s" % (
                r["name"], r["id"], r["maturity"], r["as_of"], r["version"], r["region"], "｜local 覆盖" if r["layer"] == "local" else ""))
            print("   挂载角色：%s" % "、".join(x["name"] for x in r["roles"]))
            if r["maturity"] == "暂缓":
                print("   ⛔ 暂缓：%s" % r.get("reason", ""))
                print("   替代：%s" % ("、".join(a["name"] for a in r.get("alternatives", [])) or "见技能包"))
            if r["sources"]:
                print("   来源：%s" % r["sources"][0])
        elif t == "term":
            print("🔎 「%s」→ %s（主导阶段 %s），命中 %d 处" % (r["query"], r["name"], r["lead_stages"], r["count"]))
            for h in r["hits"][:4]:
                print("     · %s" % h)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("query", nargs="*")
    ap.add_argument("--usage", action="store_true", help="使用度排行")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    if a.usage:
        import usage_report  # noqa
        return usage_report.main(["--json"] if a.json else [])
    if not a.query:
        ap.print_help()
        return 2
    res = Who().query(" ".join(a.query))
    if a.json:
        print(json.dumps(res, ensure_ascii=False, indent=2, default=list))
    else:
        render(res)
    return 0 if res["found"] else 1


if __name__ == "__main__":
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    sys.exit(main())
