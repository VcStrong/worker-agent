"""词表索引：who.py 反查和离线选角评测共用。

每个专家的词表来源（权重不同）：
- 专家名、合并来源的原始岗位名（拆开 " / "）
- experts.json 的 tasks / terms
- 合并来源岗位在 roles.json 的术语词库（含 AI 协同组）、工具 tl
- 挂载技能包的 name / aliases / id
"""
import math
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common  # noqa: E402

W_NAME, W_ROLE, W_TASK, W_TERM, W_GRAPH, W_SKILL = 6.0, 5.0, 3.0, 2.5, 1.0, 2.0


def norm(s):
    return re.sub(r"\s+", "", str(s)).lower()


def split_name(n):
    out = []
    for piece in re.split(r"\s*/\s*|（|）|\(|\)|、", n):
        piece = piece.strip()
        if len(norm(piece)) >= 2:
            out.append(piece)
    return out


class Index:
    def __init__(self):
        self.mm = common.load_merge_map()
        self.experts = common.load_experts()[1]
        self.roles = {r["id"]: r for r in common.load_roles()}
        self.skills = common.load_skills()
        self.radar = common.radar_config()
        # vocab[term_norm] = {"display": term, "hits": {slug: (weight, kind, detail)}}
        self.vocab = {}
        for slug, info in common.active_experts(self.mm).items():
            ex = self.experts.get(slug, {})
            self._add(info["name"], slug, W_NAME, "专家名", info["name"])
            for p in split_name(info["name"]):
                self._add(p, slug, W_NAME, "专家名", info["name"])
            for t in ex.get("tasks", []):
                self._add(t, slug, W_TASK, "典型活儿", t)
                for p in split_name(t):
                    self._add(p, slug, W_TASK * 0.8, "典型活儿", t)
            for t in ex.get("terms", []):
                self._add(t, slug, W_TERM, "高频术语", t)
            for rid, primary in common.expert_roles(self.mm, slug):
                r = self.roles.get(rid)
                if not r:
                    continue
                w = 1.0 if primary else 0.6
                self._add(r["name"], slug, W_ROLE * w, "原始岗位", "%s %s" % (rid, r["name"]))
                for p in split_name(r["name"]):
                    self._add(p, slug, W_ROLE * w, "原始岗位", "%s %s" % (rid, r["name"]))
                for g in r.get("terms", []):
                    for t in g["terms"]:
                        self._add(t, slug, W_GRAPH * w, "术语词库", "%s %s · %s" % (rid, r["name"], g["group"]))
                for t in r.get("tools", []):
                    for p in split_name(t["name"]) or [t["name"]]:
                        self._add(p, slug, W_GRAPH * w, "图谱工具", "%s %s" % (rid, r["name"]))
            for s in self.skills.values():
                if slug in (s["meta"].get("roles") or []):
                    names = [s["meta"].get("name", s["id"]), s["id"]] + list(s["meta"].get("aliases") or [])
                    for n in names:
                        for p in [n] + split_name(n):
                            self._add(p, slug, W_SKILL, "技能", s["id"])
        n = max(1, len(common.active_experts(self.mm)))
        for v in self.vocab.values():
            v["idf"] = math.log(1 + n / len(v["hits"]))

    def _add(self, term, slug, weight, kind, detail):
        key = norm(term)
        if len(key) < 2:
            return
        v = self.vocab.setdefault(key, {"display": term, "hits": {}})
        old = v["hits"].get(slug)
        if not old or old[0] < weight:
            v["hits"][slug] = (weight, kind, detail)

    def matches(self, text):
        t = norm(text)
        found = [k for k in self.vocab if k in t]
        # 去掉被更长命中词包含的短词
        found.sort(key=len, reverse=True)
        kept = []
        for k in found:
            if not any(k in longer for longer in kept):
                kept.append(k)
        return kept

    def route(self, text, top=3):
        scores = {}
        for k in self.matches(text):
            v = self.vocab[k]
            length_bonus = min(len(k), 8) / 4.0
            for slug, (w, _, _) in v["hits"].items():
                scores[slug] = scores.get(slug, 0) + w * v["idf"] * length_bonus
        ranked = sorted(scores.items(), key=lambda kv: (-kv[1], kv[0]))
        return ranked[:top]
