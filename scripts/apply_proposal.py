#!/usr/bin/env python3
"""REQ-021 / 023 / 024 / 025：应用技能更新提案（情报员提案、复盘经验）。

skills_refresh_mode=auto（默认）时情报员的提案由 auto_refresh.py 用 --auto 自动应用；ask 模式或复盘经验照旧拍板。

用法：
  python3 scripts/apply_proposal.py <提案.md> --check                 # 只校验格式 / 来源 / 重复驳回
  python3 scripts/apply_proposal.py <提案.md> --approve 1,3 --reject 2 # 拍板：只应用通过的条目
  python3 scripts/apply_proposal.py <提案.md> --approve all
  python3 scripts/apply_proposal.py <提案.md> --auto [--summary x.json] # 自动：核实过的条目全部应用，退化的逐条剔除
  python3 scripts/apply_proposal.py <提案.md>                         # 不拍板：只自动应用小改动（需 run.yaml auto_apply_trivial=true）

流程：拍板结果写回提案 → 驳回条目记 proposals/rejected.jsonl（以后不重复提出，除非有新证据）
→ 应用通过的条目（技能包 CHANGELOG 记提案编号）→ build → validate → 选角评测 + 技能回归题
→ 任何一项比应用前下降：全部还原、拒绝更新并打印退化用例
→ 通过：快照（git：本地提交 + 标签 skills-<日期>-<序号>，不 push；非 git：snapshots/<标签>/）
→ 提示 install.sh --update 同步到项目。

条目格式见 proposals/README.md。
"""
import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "lib"))
import common  # noqa: E402
import miniyaml  # noqa: E402
import snapshot  # noqa: E402

TRIVIAL_ACTIONS = {"update_as_of", "add_source", "fix_typo"}
SKILL_ACTIONS = {"add_skill", "update_maturity", "update_version", "deprecate", "update_as_of", "add_source", "fix_typo",
                 "append_lesson", "update_fields"}
ROLE_ACTIONS = {"merge_role", "new_role", "retire_role"}
REJECTED = common.p("proposals", "rejected.jsonl")
ITEM_RE = re.compile(r"^###\s+(\S+)\s*(.*)$", re.M)


# ---------------- 解析 ----------------
def parse(path):
    text = open(path, encoding="utf-8").read()
    items = []
    heads = list(ITEM_RE.finditer(text))
    for i, h in enumerate(heads):
        end = heads[i + 1].start() if i + 1 < len(heads) else len(text)
        chunk = text[h.end():end]
        m = re.search(r"```ya?ml\n(.*?)\n```", chunk, re.S)
        if not m:
            continue
        data = miniyaml.loads(m.group(1)) or {}
        md = re.search(r"```markdown\n(.*?)\n```\s*$", chunk[m.end():], re.S) or re.search(r"```markdown\n(.*?)\n```", chunk[m.end():], re.S)
        js = re.search(r"```json\n(.*?)\n```", chunk[m.end():], re.S)
        if js:
            try:
                data.update(json.loads(js.group(1)))
            except ValueError as e:
                data["_json_error"] = str(e)
        items.append({"id": h.group(1), "title": h.group(2).strip(), "data": data,
                      "content": md.group(1) + "\n" if md else None,
                      "yaml_span": (h.end() + m.start(1), h.end() + m.end(1))})
    return text, items


def set_status(text, item, status):
    s, e = item["yaml_span"]
    block = text[s:e]
    if re.search(r"^status:.*$", block, re.M):
        block = re.sub(r"^status:.*$", "status: %s" % status, block, count=1, flags=re.M)
    else:
        block = block + "\nstatus: %s" % status
    return text[:s] + block + text[e:]


def dedupe_key(d):
    return "%s|%s|%s" % (d.get("action"), d.get("skill") or d.get("role") or "", d.get("suggested_maturity") or d.get("fields") or "")


def load_rejected():
    out = []
    if os.path.exists(REJECTED):
        for line in open(REJECTED, encoding="utf-8"):
            if line.strip():
                out.append(json.loads(line))
    return out


# ---------------- 校验 ----------------
def check_items(items):
    errs, warns = [], []
    rejected = load_rejected()
    for it in items:
        d, w = it["data"], it["id"]
        act = d.get("action")
        if act not in SKILL_ACTIONS | ROLE_ACTIONS:
            errs.append("%s：action 不合法：%r" % (w, act))
            continue
        status = d.get("status", "待拍板")
        ev = d.get("evidence") or []
        if act != "append_lesson":
            if not any(str(x).startswith("http") for x in ev):
                errs.append("%s：缺少证据链接 evidence" % w)
            if not d.get("published") and act not in ("fix_typo", "add_source"):
                warns.append("%s：缺少发布日期 published" % w)
        if status == "待核实" and d.get("suggested_maturity") == "采用":
            errs.append("%s：待核实的条目不能建议成「采用」" % w)
        if d.get("suspicious_sources"):
            warns.append("%s：含可疑来源：%s" % (w, d["suspicious_sources"]))
        if act in TRIVIAL_ACTIONS and d.get("suggested_maturity"):
            errs.append("%s：小改动类条目不能改成熟度" % w)
        if d.get("trivial") and act not in TRIVIAL_ACTIONS:
            errs.append("%s：只有 update_as_of / add_source / fix_typo 能标 trivial" % w)
        if act in SKILL_ACTIONS and act != "add_skill" and not d.get("skill"):
            errs.append("%s：缺少 skill" % w)
        if act == "add_skill" and not it["content"]:
            errs.append("%s：add_skill 需要紧跟一个 ```markdown 代码块（完整技能包）" % w)
        if act == "append_lesson":
            for k in ("source_need", "role", "text"):
                if not d.get(k):
                    errs.append("%s：经验条目缺少 %s" % (w, k))
        if d.get("_json_error"):
            errs.append("%s：json 代码块解析失败：%s" % (w, d["_json_error"]))
        if act == "new_role":
            errs += check_new_role(w, d, items)
        if act == "retire_role":
            for k in ("slug", "replacement"):
                if not d.get(k):
                    errs.append("%s：retire_role 缺少 %s" % (w, k))
        key = dedupe_key(d)
        for r in rejected:
            if r["key"] == key and not (set(ev) - set(r.get("evidence") or [])):
                warns.append("%s：和以前驳回的 %s 重复且没有新证据，不应重复提出" % (w, r["id"]))
    return errs, warns


PROFILE_KEYS = ["tools_profile", "lead_stages", "stages", "summary", "duties", "outputs", "upstream", "downstream",
                "standards", "boundaries", "tasks", "terms"]


def check_new_role(w, d, items):
    """新增专家必须一次带齐：档案、合并来源、≥2 条选角用例、≥3 条技能回归题、≥5 个挂载技能，超编时给合并 / 下线方案。"""
    errs = []
    slug = d.get("slug", "")
    if not re.match(r"^[a-z0-9]+(-[a-z0-9]+)*$", slug):
        errs.append("%s：slug 不合法：%r" % (w, slug))
    if slug in common.load_merge_map()["experts"]:
        errs.append("%s：专家 %s 已存在" % (w, slug))
    if not d.get("name"):
        errs.append("%s：缺少 name" % w)
    prof = d.get("profile") or {}
    miss = [k for k in PROFILE_KEYS if not prof.get(k)]
    if miss:
        errs.append("%s：profile 缺少 %s（格式同 data/experts.json）" % (w, "、".join(miss)))
    tp = prof.get("tools_profile")
    if tp and tp not in common.load_experts()[0]:
        errs.append("%s：tools_profile 不存在：%s" % (w, tp))
    rc = [c for c in d.get("routing_cases") or [] if c.get("expect") == slug and c.get("task")]
    if len(rc) < 2:
        errs.append("%s：routing_cases 至少 2 条（task → expect: %s）" % (w, slug))
    sc = [c for c in d.get("skill_cases") or [] if c.get("id") and c.get("scenario")]
    if len(sc) < 3:
        errs.append("%s：skill_cases 至少 3 条（id、scenario、expect_adopt / agent_contains…，role 会自动填为 %s）" % (w, slug))
    mounted = set(d.get("mount_skills") or [])
    for x in items:
        xd = x["data"]
        if xd.get("action") == "add_skill" and x["content"]:
            meta, _ = common.split_frontmatter(x["content"])
            if slug in ((meta or {}).get("roles") or []):
                mounted.add(meta.get("id"))
    known = set(common.load_skills())
    for sid in d.get("mount_skills") or []:
        if sid not in known:
            errs.append("%s：mount_skills 里的技能不存在：%s" % (w, sid))
    if len(mounted) < 5:
        errs.append("%s：新专家至少挂 5 个技能（mount_skills + 同一提案里 roles 含 %s 的 add_skill），现在 %d 个" % (w, slug, len(mounted)))
    team = common.team_config()
    mm = common.load_merge_map()
    active = [r for r in team.get("enabled") or [] if r in mm["experts"] and not mm["experts"][r].get("retired")]
    if len(active) + 2 > int(team.get("role_cap", 15)):
        rom = d.get("retire_or_merge") or {}
        if not rom.get("slug"):
            errs.append("%s：新增后编制 %d 超过 role_cap=%s，必须给出 retire_or_merge: {slug, replacement, reason}" % (
                w, len(active) + 2, team.get("role_cap", 15)))
    rom = d.get("retire_or_merge") or {}
    if rom.get("slug"):
        if rom["slug"] not in mm["experts"]:
            errs.append("%s：retire_or_merge.slug 不存在：%s" % (w, rom["slug"]))
        rep = rom.get("replacement") or slug
        if rep != slug and rep not in mm["experts"]:
            errs.append("%s：retire_or_merge.replacement 不存在：%s（可以写新专家自己 %s）" % (w, rep, slug))
    return errs


# ---------------- 应用 ----------------
def skill_path(sid):
    s = common.load_skills(include_local=False).get(sid)
    return s["path"] if s else None


def bump(ver, major_minor):
    parts = [int(x) for x in str(ver or "1.0.0").split(".")[:3]] + [0, 0, 0]
    a, b, c = parts[:3]
    if major_minor:
        return "%d.%d.0" % (a, b + 1)
    return "%d.%d.%d" % (a, b, c + 1)


def rewrite_skill(path, meta_updates, changelog, append=None, section=None, minor=True, typo=None):
    text = open(path, encoding="utf-8").read()
    m = re.match(r"^---\n(.*?)\n---\n?(.*)$", text, re.S)
    meta, body = miniyaml.loads(m.group(1)), m.group(2)
    new_ver = bump(meta.get("version"), minor)
    meta.update(meta_updates)
    meta["version"] = new_ver
    if typo:
        body = body.replace(typo[0], typo[1])
    if append and section:
        body = add_to_section(body, section, append)
    body = add_to_section(body, "CHANGELOG", "- %s v%s %s" % (common.today().isoformat(), new_ver, changelog))
    out = "---\n%s\n---\n%s" % (miniyaml.dumps(meta), body if body.startswith("\n") else "\n" + body)
    common.write_text(path, out)
    return new_ver


def add_to_section(body, section, line):
    pat = re.compile(r"(^##\s+%s\s*\n)(.*?)(?=^##\s|\Z)" % re.escape(section), re.S | re.M)
    m = pat.search(body)
    if not m:
        return body.rstrip() + "\n\n## %s\n\n%s\n" % (section, line)
    content = m.group(2).rstrip("\n")
    new = m.group(1) + (content + "\n" if content else "") + line + "\n\n"
    return body[:m.start()] + new + body[m.end():]


def norm_text(s):
    return re.sub(r"[\s，。,.;；：:、！!？?（）()「」\"'`-]", "", s).lower()


def apply_item(it, log):
    d, pid = it["data"], it["id"]
    act = d["action"]
    reason = d.get("reason", it["title"])
    if act == "add_skill":
        meta, _ = common.split_frontmatter(it["content"])
        dom = d.get("domain") or meta.get("domain") or "misc"
        path = common.p("data", "skills", dom, meta["id"] + ".md")
        if os.path.exists(path):
            raise RuntimeError("%s：技能 %s 已存在" % (pid, meta["id"]))
        content = it["content"]
        if "提案 %s" % pid not in content:
            content = add_to_section(content, "CHANGELOG", "- %s v%s 提案 %s：%s" % (common.today().isoformat(), meta.get("version", "1.0.0"), pid, reason))
        common.write_text(path, content)
        log.append("新增技能 %s（%s）" % (meta["id"], pid))
        return
    if act in ROLE_ACTIONS:
        apply_role(it, log)
        return
    sid = d["skill"]
    if act == "append_lesson":
        apply_lesson(it, log)
        return
    path = skill_path(sid)
    if not path:
        raise RuntimeError("%s：技能 %s 不存在" % (pid, sid))
    cl = "提案 %s：%s" % (pid, reason)
    if act == "update_maturity" or act == "deprecate":
        upd = {"maturity": d.get("suggested_maturity") or ("暂缓" if act == "deprecate" else None)}
        if d.get("replaced_by"):
            upd["replaced_by"] = d["replaced_by"]
        if d.get("evidence"):
            upd["sources"] = sorted(set((common.split_frontmatter(open(path).read())[0].get("sources") or []) + d["evidence"]))
        upd["as_of"] = common.today().isoformat()
        append = None
        if act == "deprecate" or upd["maturity"] == "暂缓":
            append = d.get("replacement_note") or "原因：%s；替代：%s" % (reason, "、".join(d.get("replaced_by") or []))
        ver = rewrite_skill(path, upd, cl, append=append, section="替代" if append else None)
    elif act in ("update_version", "update_fields"):
        upd = dict(d.get("fields") or {})
        upd["as_of"] = common.today().isoformat()
        ver = rewrite_skill(path, upd, cl, append=d.get("note"), section=d.get("section") if d.get("note") else None)
    elif act == "update_as_of":
        ver = rewrite_skill(path, {"as_of": d.get("as_of") or common.today().isoformat()}, cl, minor=False)
    elif act == "add_source":
        meta = common.split_frontmatter(open(path).read())[0]
        ver = rewrite_skill(path, {"sources": list(dict.fromkeys((meta.get("sources") or []) + (d.get("evidence") or [])))}, cl, minor=False)
    elif act == "fix_typo":
        ver = rewrite_skill(path, {}, cl, minor=False, typo=(d.get("from", ""), d.get("to", "")))
    log.append("%s %s → v%s（%s）" % (act, sid, ver, pid))


def apply_lesson(it, log):
    d, pid = it["data"], it["id"]
    sid = d["skill"]
    section = d.get("section", "常见坑")
    line = "- %s（来源需求 %s，角色 %s，%s）" % (d["text"], d["source_need"], d["role"], pid)
    base = skill_path(sid)
    if not base:
        raise RuntimeError("%s：技能 %s 不存在" % (pid, sid))
    if d.get("scope") == "local":
        dom = os.path.basename(os.path.dirname(base))
        path = os.path.join(common.LOCAL_DIR, "skills", dom, sid + ".md")
        if not os.path.exists(path):
            os.makedirs(os.path.dirname(path), exist_ok=True)
            shutil.copy2(base, path)
    else:
        path = base
    body = open(path, encoding="utf-8").read()
    if norm_text(d["text"]) in norm_text(body):
        log.append("经验 %s 与 %s 已有内容重复，已合并（跳过写入）" % (pid, sid))
        return
    ver = rewrite_skill(path, {}, "提案 %s：经验回流（%s）" % (pid, d["source_need"]), append=line, section=section, minor=False)
    log.append("经验 %s → %s「%s」v%s%s" % (pid, sid, section, ver, "（local 覆盖层）" if d.get("scope") == "local" else ""))


def apply_role(it, log):
    d, pid = it["data"], it["id"]
    act = d["action"]
    if act == "merge_role":
        ov = load_overlay()
        role = dict(d.get("role_def") or {})
        role.setdefault("id", d.get("role"))
        role["target"] = d["target"]
        role["proposal"] = pid
        ov["add_roles"] = [r for r in ov["add_roles"] if r["id"] != role["id"]] + [role]
        save_overlay(ov)
        log.append("新岗位 %s 并入 %s（%s）" % (role["id"], d["target"], pid))
    elif act == "new_role":
        apply_new_role(d, pid, log)
    elif act == "retire_role":
        retire(d["slug"], d["replacement"], d.get("reason", ""), pid, log)


def load_overlay():
    ov = common.read_json(common.p("data", "roles_overlay.json"), {}) or {}
    for k, v in (("add_roles", []), ("merge", {}), ("new_experts", {}), ("retire", {})):
        ov.setdefault(k, v)
    return ov


def save_overlay(ov):
    common.write_json(common.p("data", "roles_overlay.json"), ov)


def apply_new_role(d, pid, log):
    """REQ-025：新增专家一次落地——覆盖层档案、合并来源、编制、阶段矩阵、选角评测集、技能回归题、挂载技能。"""
    slug = d["slug"]
    rom = d.get("retire_or_merge") or {}
    ov = load_overlay()
    ov["new_experts"][slug] = {"name": d["name"], "kind": d.get("kind", "traditional"), "model": d.get("model", "sonnet"),
                               "overlay": True, "proposal": pid, "profile": d["profile"]}
    roles = d.get("role_defs") or ([d["role_def"]] if d.get("role_def") else [])
    for r in roles:
        r = dict(r, target=slug, proposal=pid)
        ov["add_roles"] = [x for x in ov["add_roles"] if x["id"] != r["id"]] + [r]
    for rid in d.get("merge_from") or []:  # 原始岗位改挂到新专家
        ov["merge"][rid] = {"target": slug, "proposal": pid}
    save_overlay(ov)
    # 新专家写进覆盖层之后再下线旧角色：replacement 可以是新专家自己（默认就是）
    if rom.get("slug"):
        retire(rom["slug"], rom.get("replacement") or slug, rom.get("reason", "为新增专家 %s 腾编制" % slug), pid, log)
    add_enabled(slug)
    # 挂载已有技能
    for sid in d.get("mount_skills") or []:
        path = skill_path(sid)
        meta = common.split_frontmatter(open(path, encoding="utf-8").read())[0]
        if slug not in (meta.get("roles") or []):
            rewrite_skill(path, {"roles": list(meta.get("roles") or []) + [slug]}, "提案 %s：挂载到新专家 %s" % (pid, slug), minor=False)
    # 评测集与回归题
    rp = common.p("scripts", "eval_routing", "cases.json")
    rdata = common.read_json(rp)
    for c in d.get("routing_cases") or []:
        rdata["cases"].append(dict(c, proposal=pid))
    common.write_json(rp, rdata)
    sp = common.p("scripts", "eval_skills", "cases.json")
    sdata = common.read_json(sp)
    for c in d.get("skill_cases") or []:
        sdata["cases"].append(dict(c, role=slug, proposal=pid))
    common.write_json(sp, sdata)
    # 阶段 × 角色矩阵
    prof = d["profile"]
    stage_note("- 新增专家 %s（`%s`）：主导 %s；参与 %s（提案 %s）" % (
        d["name"], slug, "、".join("%02d" % n for n in prof.get("lead_stages", [])),
        "、".join("%02d" % n for n in prof.get("stages", [])), pid))
    log.append("新增专家 %s（%s）：挂载技能 %d 个、选角用例 %d 条、回归题 %d 条" % (
        slug, pid, len(d.get("mount_skills") or []), len(d.get("routing_cases") or []), len(d.get("skill_cases") or [])))


def retire(slug, replacement, reason, pid, log):
    mm = common.load_merge_map()
    if slug not in mm["experts"] or replacement not in mm["experts"]:
        raise RuntimeError("%s：下线 / 替代角色不存在：%s → %s" % (pid, slug, replacement))
    ov = load_overlay()
    ov["retire"][slug] = {"replacement": replacement, "reason": reason, "proposal": pid}
    # 原始岗位改由替代角色承担（agent 文件保留到下一个大版本，description 写明替代）
    for rid, m in sorted(mm["map"].items()):
        also = list(m.get("also") or [])
        if m.get("target") != slug and slug not in also:
            continue
        new = dict(m)
        new.pop("overlay", None)
        if m.get("target") == slug:
            new["target"], new["from"] = replacement, slug
        also = [replacement if a == slug else a for a in also]
        also = [a for i, a in enumerate(also) if a != new["target"] and a not in also[:i]]
        if also:
            new["also"] = also
        else:
            new.pop("also", None)
        new["proposal"] = pid
        ov["merge"][rid] = new
    save_overlay(ov)
    # 被下线角色挂的技能转挂到替代角色
    moved = 0
    for sid, sk in common.load_skills(include_local=False).items():
        roles = sk["meta"].get("roles") or []
        if slug in roles and replacement not in roles:
            rewrite_skill(sk["path"], {"roles": roles + [replacement]}, "提案 %s：%s 下线，转挂 %s" % (pid, slug, replacement), minor=False)
            moved += 1
    # 期望该角色的选角用例改为替代角色；它的回归题标记下线（评测跳过）
    rp = common.p("scripts", "eval_routing", "cases.json")
    rdata = common.read_json(rp)
    for c in rdata["cases"]:
        if c.get("expect") == slug:
            c["expect"], c["retired_from"] = replacement, slug
        if slug in (c.get("also_ok") or []):
            c["also_ok"] = [x for x in c["also_ok"] if x != slug] + [replacement]
    common.write_json(rp, rdata)
    sp = common.p("scripts", "eval_skills", "cases.json")
    sdata = common.read_json(sp)
    for c in sdata["cases"]:
        if c.get("role") == slug:
            c["retired"] = True
    common.write_json(sp, sdata)
    stage_note("- 下线专家 `%s`，改由 `%s` 承担（提案 %s）：%s" % (slug, replacement, pid, reason))
    log.append("下线专家 %s，替代 %s（%s），转挂技能 %d 个" % (slug, replacement, pid, moved))


def stage_note(line):
    path = common.p("workflow", "stages.md")
    text = open(path, encoding="utf-8").read()
    head = "## 覆盖层调整（roles_overlay.json，总控选角时一并考虑）"
    if head not in text:
        text = text.rstrip() + "\n\n" + head + "\n\n"
    common.write_text(path, text.rstrip() + "\n" + line + "\n")


def add_enabled(slug):
    path = common.p("config", "team.yaml")
    lines = open(path, encoding="utf-8").read().splitlines()
    if any(re.match(r"^\s*-\s*%s\s*$" % re.escape(slug), l) for l in lines):
        return
    i = next(i for i, l in enumerate(lines) if l.startswith("enabled:"))
    j = i + 1
    while j < len(lines) and re.match(r"^\s+-\s", lines[j]):
        j += 1
    lines.insert(j, "  - %s" % slug)
    common.write_text(path, "\n".join(lines) + "\n")


# ---------------- 回归 ----------------
def run_evals():
    sys.path.insert(0, os.path.join(HERE, "eval_routing"))
    sys.path.insert(0, os.path.join(HERE, "eval_skills"))
    import importlib
    r = importlib.import_module("run_eval")
    importlib.reload(r)
    hit, rres = r.evaluate(verbose=False)
    s = importlib.import_module("run_skill_eval")
    importlib.reload(s)
    rate, sres = s.evaluate(verbose=False)
    return {"routing": hit, "routing_results": rres, "skills": rate, "skills_results": sres}


def regressions(before, after):
    import regress
    return regress.compare(before["routing_results"], after["routing_results"], before["routing"], after["routing"], "routing") + \
        regress.compare(before["skills_results"], after["skills_results"], before["skills"], after["skills"], "skills")


def backup_tree():
    tmp = tempfile.mkdtemp(prefix="role-agents-apply-")
    for rel in snapshot.SNAP_DIRS:
        src = common.p(rel)
        if os.path.isdir(src):
            shutil.copytree(src, os.path.join(tmp, rel))
        elif os.path.exists(src):
            os.makedirs(os.path.dirname(os.path.join(tmp, rel)), exist_ok=True)
            shutil.copy2(src, os.path.join(tmp, rel))
    return tmp


def restore_tree(tmp):
    for rel in snapshot.SNAP_DIRS:
        src, dst = os.path.join(tmp, rel), common.p(rel)
        if os.path.isdir(dst):
            shutil.rmtree(dst)
        elif os.path.exists(dst):
            os.remove(dst)
        if os.path.isdir(src):
            shutil.copytree(src, dst)
        elif os.path.exists(src):
            shutil.copy2(src, dst)


def sh(*args):
    r = subprocess.run([sys.executable] + list(args), capture_output=True, text=True, cwd=common.ROOT)
    return r.returncode, r.stdout + r.stderr


def apply_batch(to_apply):
    """应用一批条目 → build → validate → 回归评测；任何一步失败整批还原。返回 (ok, 错误, 评测结果, 日志)。"""
    tmp = backup_tree()
    before = run_evals()
    log = []
    try:
        order = {"retire_role": 0, "merge_role": 1, "new_role": 1, "add_skill": 2}
        for it in sorted(to_apply, key=lambda x: order.get(x["data"].get("action"), 3)):
            apply_item(it, log)
        rc, out = sh(os.path.join(HERE, "build.py"), "--quiet")
        if rc != 0:
            raise RuntimeError("build 失败：\n" + out)
        rc, out = sh(os.path.join(HERE, "validate.py"))
        if rc != 0:
            raise RuntimeError("validate 失败：\n" + "\n".join(l for l in out.splitlines() if l.startswith("❌")))
        after = run_evals()
        reg = regressions(before, after)
        if reg:
            raise RuntimeError("回归退化，拒绝更新（不允许 install --update）：\n  " + "\n  ".join(reg))
    except Exception as e:
        restore_tree(tmp)
        shutil.rmtree(tmp, ignore_errors=True)
        return False, str(e), None, []
    shutil.rmtree(tmp, ignore_errors=True)
    return True, "", after, log


BIG_ACTIONS = {"deprecate", "new_role", "retire_role", "merge_role"}


def auto_candidates(items, errs):
    """自动模式（skills_refresh_mode=auto）：核实过的条目全部应用；待核实、含可疑来源、格式错误、重复驳回的跳过。"""
    bad = {e.split("：")[0] for e in errs}
    rejected = load_rejected()
    take, skip = [], []
    for it in items:
        d = it["data"]
        st = d.get("status", "待拍板")
        if st in ("已应用", "驳回"):
            continue
        ev = d.get("evidence") or []
        dup = any(r["key"] == dedupe_key(d) and not (set(ev) - set(r.get("evidence") or [])) for r in rejected)
        why = ("格式错误" if it["id"] in bad else "待核实" if st == "待核实" else
               "含可疑来源" if d.get("suspicious_sources") else "以前驳回过且没有新证据" if dup else "")
        (skip if why else take).append((it, why))
    return [t[0] for t in take], [(t[0], t[1]) for t in skip]


def write_summary(path, proposal, applied, skipped, failed, tag, prev_tag):
    """自动更新摘要（JSON），由 auto_refresh.py 汇总成 markdown 和 CHANGELOG。"""
    def row(it, why=""):
        d = it["data"]
        return {"id": it["id"], "title": it["title"], "action": d.get("action"),
                "target": d.get("skill") or d.get("slug") or d.get("role") or (it["content"] and common.split_frontmatter(it["content"])[0].get("id")) or "",
                "maturity": d.get("suggested_maturity") or "", "evidence": d.get("evidence") or [],
                "big": d.get("action") in BIG_ACTIONS, "why": why}
    common.write_json(path, {"proposal": os.path.basename(proposal), "tag": tag, "prev_tag": prev_tag,
                             "applied": [row(i) for i in applied], "skipped": [row(i, w) for i, w in skipped],
                             "failed": [row(i, w) for i, w in failed]})


def main_auto(a, text, items, errs):
    take, skipped = auto_candidates(items, errs)
    prev_tag = (common.read_json(common.p("skills.lock"), {}) or {}).get("tag")
    applied, failed, log = [], [], []
    if take:
        ok, err, after, log = apply_batch(take)
        if ok:
            applied = take
        else:
            # 整批不过：逐条重试，只留下不退化的条目
            print("⚠️  整批应用未通过（%s），改为逐条应用" % err.splitlines()[0])
            for it in take:
                ok1, err1, _, log1 = apply_batch([it])
                if ok1:
                    applied.append(it)
                    log += log1
                else:
                    failed.append((it, err1.splitlines()[0]))
    for it in applied:
        text = set_status(text, it, "已应用")
    for it, why in failed:
        text = set_status(text, it, "自动应用失败")
    open(a.proposal, "w", encoding="utf-8").write(text)
    with open(common.p("proposals", "apply.log"), "a", encoding="utf-8") as f:
        for l in log:
            f.write("%s %s %s（自动更新）\n" % (common.now_iso(), os.path.basename(a.proposal), l))
    for l in log:
        print("✅ " + l)
    for it, why in skipped:
        print("⏭  %s 跳过：%s" % (it["id"], why))
    for it, why in failed:
        print("❌ %s 未应用：%s" % (it["id"], why))
    tag = None
    if applied and not a.no_snapshot:
        tag, mode = snapshot.take("自动更新 %s" % os.path.basename(a.proposal))
        print("📸 快照 %s（%s）" % (tag, "git 本地提交 + 标签，未 push" if mode == "git" else "snapshots/%s/" % tag))
    if a.summary:
        write_summary(a.summary, a.proposal, applied, skipped, failed, tag, prev_tag)
    print("—— 自动应用 %d 条，跳过 %d 条，失败 %d 条" % (len(applied), len(skipped), len(failed)))
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("proposal")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--approve", default="")
    ap.add_argument("--reject", default="")
    ap.add_argument("--no-snapshot", action="store_true", help="调试用：不打快照")
    ap.add_argument("--auto", action="store_true", help="自动模式：核实过的条目全部应用（skills_refresh_mode=auto 时由 auto_refresh.py 调用）")
    ap.add_argument("--summary", help="自动模式：把应用结果写成 JSON 摘要")
    a = ap.parse_args(argv)

    text, items = parse(a.proposal)
    if not items:
        print("❌ 没有解析到提案条目（每条：### 编号 标题 + ```yaml 代码块）")
        return 1
    errs, warns = check_items(items)
    for w in warns:
        print("⚠️  " + w)
    for e in errs:
        print("❌ " + e)
    if a.check:
        print("—— 提案 %d 条：%d 个错误，%d 条告警" % (len(items), len(errs), len(warns)))
        return 1 if errs else 0
    if a.auto:
        return main_auto(a, text, items, errs)

    ids = [it["id"] for it in items]
    approve = set(ids) if a.approve.strip() == "all" else {x.strip() for x in a.approve.split(",") if x.strip()}
    reject = {x.strip() for x in a.reject.split(",") if x.strip()}
    for x in (approve | reject) - set(ids):
        # 允许只写序号
        if x.isdigit() and int(x) <= len(ids):
            (approve if x in approve else reject).add(ids[int(x) - 1])
        else:
            print("❌ 提案里没有条目 %s" % x)
            return 1
    auto = bool(common.run_config().get("auto_apply_trivial", False))
    to_apply, auto_applied = [], []
    for it in items:
        d = it["data"]
        st = d.get("status", "待拍板")
        if st in ("已应用", "驳回"):
            continue
        if it["id"] in reject:
            text = set_status(text, it, "驳回")
            with open(REJECTED, "a", encoding="utf-8") as f:
                f.write(json.dumps({"id": it["id"], "key": dedupe_key(d), "evidence": d.get("evidence") or [],
                                    "date": common.today().isoformat(), "file": os.path.basename(a.proposal)}, ensure_ascii=False) + "\n")
            continue
        if it["id"] in approve:
            if st == "待核实":
                print("⚠️  %s 标为待核实，按用户拍板仍然应用" % it["id"])
            to_apply.append(it)
        elif auto and d.get("trivial") and d.get("action") in TRIVIAL_ACTIONS and st != "待核实":
            to_apply.append(it)
            auto_applied.append(it["id"])
    if errs and any(it["id"] in {e.split("：")[0] for e in errs} for it in to_apply):
        print("❌ 通过的条目有格式错误，先修正提案")
        return 1
    if not to_apply:
        open(a.proposal, "w", encoding="utf-8").write(text)
        print("ℹ️  没有要应用的条目（auto_apply_trivial=%s；未拍板的条目等用户拍板）。驳回 %d 条已记录。" % (str(auto).lower(), len(reject)))
        return 0

    ok, err, after, log = apply_batch(to_apply)
    if not ok:
        print("❌ %s\n已还原到应用前的状态，技能层没有改动。" % err)
        return 1
    for it in to_apply:
        text = set_status(text, it, "已应用")
    open(a.proposal, "w", encoding="utf-8").write(text)
    with open(common.p("proposals", "apply.log"), "a", encoding="utf-8") as f:
        for l in log:
            f.write("%s %s %s%s\n" % (common.now_iso(), os.path.basename(a.proposal), l,
                                      "（auto_apply_trivial 自动应用）" if any(x in l for x in auto_applied) else ""))
    for l in log:
        print("✅ " + l)
    if auto_applied:
        print("ℹ️  自动应用的小改动：%s（auto_apply_trivial=true，已记日志 proposals/apply.log）" % ", ".join(auto_applied))
    print("回归：选角命中率 %.1f%%，技能题通过率 %.1f%%（均未下降）" % (after["routing"] * 100, after["skills"] * 100))
    if not a.no_snapshot:
        tag, mode = snapshot.take("应用提案 %s" % os.path.basename(a.proposal))
        print("📸 快照 %s（%s）" % (tag, "git 本地提交 + 标签，未 push" if mode == "git" else "snapshots/%s/" % tag))
    print("下一步：在目标项目运行 `%s --update --project <目录>` 同步。" % common.p("install.sh"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
