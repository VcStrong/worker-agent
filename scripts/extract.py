#!/usr/bin/env python3
"""REQ-001：从图谱 HTML 内嵌脚本抽取 STAGES / FAMS / ROLES / CHAIN / EXTRA，
生成 data/roles.json（48 个原始岗位，知识底座）、data/stages.json、data/chain.json。

用法：python3 scripts/extract.py <图谱.html> [--import-date YYYY-MM-DD] [--out data/]

- 字段顺序固定、重复运行输出一致（导入日期默认沿用已有 roles.json 里的 import_date）
- 某岗位缺字段：输出里标空，终端告警，不中断
- 图谱只做基线层：不读、不写 data/skills/
- 出现 merge_map.json 没映射的岗位：告警并列出（build 不会为它单独生成 agent）
"""
import argparse
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "lib"))
import common  # noqa: E402
import jslit  # noqa: E402

# 图谱字段 → 输出字段（顺序即输出顺序）
ROLE_FIELDS = [
    ("id", "id", "str"),
    ("f", "family", "str"),
    (None, "family_name", "str"),
    ("n", "name", "str"),
    ("t", "positioning", "str"),
    ("d", "duties", "list"),
    ("o", "outputs", "list"),
    ("k", "abilities", "list"),
    ("u", "upstream", "str"),
    ("dn", "downstream", "str"),
    ("s", "stages", "list"),
    ("l", "lead_stages", "list"),
    ("tl", "tools", "list"),
    ("m", "metrics", "str"),
    ("p", "career", "str"),
]
EXTRA_FIELDS = [("wk", "work", "list"), ("tx", "terms", "list"), ("rp", "unwritten_rules", "list")]
FIELD_LEGEND = {
    "id": "id", "family": "族代码", "family_name": "族", "name": "名称", "positioning": "一句话定位",
    "duties": "职责", "outputs": "产出", "abilities": "能力", "upstream": "上游", "downstream": "下游",
    "stages": "参与阶段", "lead_stages": "主导阶段", "tools": "工具（来源=图谱、日期=导入日）",
    "metrics": "指标", "career": "晋升", "work": "工作内容", "terms": "术语词库（含 AI 协同组）",
    "unwritten_rules": "潜规则",
}
AI_GROUP = "AI 协同"


def find_const(src, name):
    m = re.search(r"\bconst\s+%s\s*=\s*" % re.escape(name), src)
    if not m:
        return None
    val, _ = jslit.parse_at(src, m.end())
    return val


def find_extra(src):
    out = {}
    for m in re.finditer(r'EXTRA\[\s*"([^"]+)"\s*\]\s*=\s*', src):
        try:
            val, _ = jslit.parse_at(src, m.end())
            out[m.group(1)] = val
        except jslit.JSParseError as e:
            common.warn("EXTRA[%s] 解析失败：%s" % (m.group(1), e))
    return out


def script_text(html):
    blocks = re.findall(r"<script[^>]*>(.*?)</script>", html, re.S)
    return "\n".join(blocks) if blocks else html


def empty(kind):
    return [] if kind == "list" else ""


def build_roles(roles_src, extra, fam_names, import_date, warnings):
    out = []
    for r in roles_src:
        rid = r.get("id", "?")
        item = {}
        for src_key, key, kind in ROLE_FIELDS:
            if src_key is None:
                item[key] = fam_names.get(r.get("f"), "")
                continue
            v = r.get(src_key)
            if v in (None, "", []):
                warnings.append("%s 缺少字段 %s（%s），已标空" % (rid, key, FIELD_LEGEND[key]))
                v = empty(kind)
            if key == "tools":
                v = [{"name": t, "source": "图谱", "date": import_date} for t in v]
            item[key] = v
        ex = extra.get(rid)
        if ex is None:
            warnings.append("%s 缺少扩展档案 EXTRA（工作内容 / 术语词库 / 潜规则），已标空" % rid)
            ex = {}
        for src_key, key, kind in EXTRA_FIELDS:
            v = ex.get(src_key)
            if v in (None, "", []):
                warnings.append("%s 缺少字段 %s（%s），已标空" % (rid, key, FIELD_LEGEND[key]))
                v = empty(kind)
            if key == "terms":
                v = [{"group": g.get("g", ""), "terms": list(g.get("t", []))} for g in v]
                if not any(g["group"] == AI_GROUP for g in v):
                    warnings.append("%s 术语词库缺少「%s」组，已补空组" % (rid, AI_GROUP))
                    v.append({"group": AI_GROUP, "terms": []})
            item[key] = v
        out.append(item)
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("html")
    ap.add_argument("--import-date", help="图谱导入日（工具来源日期），默认沿用已有 roles.json，否则今天")
    ap.add_argument("--out", default=common.DATA)
    args = ap.parse_args(argv)

    with open(args.html, encoding="utf-8") as f:
        src = script_text(f.read())

    stages_src = find_const(src, "STAGES") or []
    fams_src = find_const(src, "FAMS") or []
    roles_src = find_const(src, "ROLES") or []
    chain_src = find_const(src, "CHAIN") or []
    extra = find_extra(src)
    if not roles_src:
        print("❌ 没有在 HTML 里找到 const ROLES", file=sys.stderr)
        return 2

    roles_path = os.path.join(args.out, "roles.json")
    prev = common.read_json(roles_path, {}) or {}
    import_date = args.import_date or prev.get("import_date") or common.today().isoformat()
    fam_names = {f["code"]: f["name"] for f in fams_src}

    warnings = []
    roles = build_roles(roles_src, extra, fam_names, import_date, warnings)
    for rid in extra:
        if rid not in {r["id"] for r in roles}:
            warnings.append("EXTRA[%s] 没有对应的岗位，已忽略" % rid)

    common.write_json(roles_path, {
        "source": os.path.basename(args.html),
        "import_date": import_date,
        "layer": "图谱基线（技能补充与更新在 data/skills/，抽取不会改动）",
        "count": len(roles),
        "fields": FIELD_LEGEND,
        "families": [{"code": f["code"], "name": f["name"]} for f in fams_src],
        "roles": roles,
    })
    stages = [{"no": int(s["no"]), "code": s["no"], "name": s["name"], "short": s["sn"],
               "desc": s["desc"], "lead_in_graph": s.get("lead", "")} for s in stages_src]
    common.write_json(os.path.join(args.out, "stages.json"), {"source": os.path.basename(args.html), "stages": stages})
    chain = [{"seq": i + 1, "name": c["n"], "owners_in_graph": c.get("o", ""), "handoff": c.get("t", "")}
             for i, c in enumerate(chain_src)]
    common.write_json(os.path.join(args.out, "chain.json"), {"source": os.path.basename(args.html), "chain": chain})

    # 未映射岗位告警
    mm = common.read_json(os.path.join(args.out, "merge_map.json"), {"map": {}}) or {"map": {}}
    ov = common.read_json(os.path.join(args.out, "roles_overlay.json"), {}) or {}
    mapped = set(mm.get("map", {})) | set((ov.get("merge") or {}))
    unmapped = [r for r in roles if r["id"] not in mapped]

    for w in warnings:
        common.warn(w)
    if unmapped:
        common.warn("有 %d 个岗位在 merge_map.json 里没有映射（build 不会为它们单独生成 agent）：" % len(unmapped))
        for r in unmapped:
            print("    - %s %s" % (r["id"], r["name"]), file=sys.stderr)
    print("✅ roles.json：%d 个岗位；stages.json：%d 个阶段；chain.json：%d 个交付物；告警 %d 条；未映射 %d 个"
          % (len(roles), len(stages), len(chain), len(warnings), len(unmapped)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
