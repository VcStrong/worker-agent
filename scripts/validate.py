#!/usr/bin/env python3
"""REQ-015 / 027 / 003 / 009 / 018 / 019：校验整套 agent 和数据。

用法：
  python3 scripts/validate.py                     # 全量校验（agents/、merge_map、team.yaml、kb_scenes.json、技能包、模板、评测集）
  python3 scripts/validate.py --agents-dir <目录>  # 校验另一处生成 / 安装的 agents（如 <项目>/.claude/agents）
  python3 scripts/validate.py --deliverable <产物.md> [...]   # 只校验交付物是否满足模板必填节

退出码：0 = 没有错误（告警不影响）；1 = 有错误，逐条打印文件和原因。
"""
import argparse
import glob
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "lib"))
import common  # noqa: E402

NAME_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
MODELS = {"opus", "sonnet", "haiku", "inherit"}
BASE_TOOLS = {"Read", "Grep", "Glob", "Write", "Edit", "Bash", "WebFetch", "WebSearch", "Agent", "Task", "Skill"}
DOC_FORBIDDEN = {"Edit", "Bash", "MultiEdit", "NotebookEdit"}
KB_READ = {"kb_search", "kb_read", "kb_iteration", "kb_repo_read", "kb_base"}
KB_ORCH_WRITE = {"kb_log", "kb_ask", "kb_wait_answer", "kb_write_doc"}
# 需要用户本人操作 / 机密 / 批准开发相关：任何角色都不能有
KB_FORBIDDEN = {"kb_base_secret", "kb_set_status", "kb_approve", "kb_dev_package", "kb_dev_prepare",
                "kb_base_save", "kb_stack_release", "kb_propose_push", "kb_create_iteration", "kb_bug_fixed"}
DOCS_MCP_TOOLS = {"resolve-library-id", "get-library-docs", "query-docs"}
ENGINEERING = {"frontend-engineer", "client-engineer", "backend-engineer", "qa-expert", "sre-security",
               "architect", "ai-app-engineer", "model-algorithm-engineer", "ai-infra-mlops"}
RAW_LEAD_NAMES = ["项目经理", "研发经理", "交互设计师", "UI 设计师", "用户研究员", "产品负责人", "数据分析师",
                  "产品运营", "测试工程师", "安全工程师", "AI 评测", "AI 基础设施", "研发负责人", "DBA", "运维"]


class Report:
    def __init__(self):
        self.errors, self.warnings = [], []

    def err(self, where, msg):
        self.errors.append((where, msg))

    def warn(self, where, msg):
        self.warnings.append((where, msg))

    def print(self):
        for w, m in self.warnings:
            print("⚠️  %s：%s" % (w, m))
        for w, m in self.errors:
            print("❌ %s：%s" % (w, m))
        print("—— 校验完成：%d 个错误，%d 条告警" % (len(self.errors), len(self.warnings)))
        return 1 if self.errors else 0


def rel(path):
    try:
        return os.path.relpath(path, common.ROOT)
    except ValueError:
        return path


# ---------------- agents ----------------
def parse_agent(path):
    text = open(path, encoding="utf-8").read()
    m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    if not m:
        return None, text
    fm = {}
    for line in m.group(1).splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            fm[k.strip()] = v.strip()
    return fm, text


def check_agents(rep, agents_dir, mm, team, run):
    files = sorted(glob.glob(os.path.join(agents_dir, "*.md")))
    expected = set(mm["experts"]) | {"orchestrator", "tech-scout"}
    if os.path.abspath(agents_dir) != os.path.abspath(common.p("agents")):
        # 安装位置：只校验本套件的 agent，用户自己的 agent 跳过
        others = [f for f in files if os.path.basename(f)[:-3] not in expected]
        for f in others:
            rep.warn(rel(f), "不是本套件的 agent，跳过")
        files = [f for f in files if f not in others]
    names = {}
    for f in files:
        fm, text = parse_agent(f)
        where = rel(f)
        if fm is None:
            rep.err(where, "缺少 frontmatter")
            continue
        for key in ("name", "description", "tools", "model"):
            if not fm.get(key):
                rep.err(where, "frontmatter 缺少 %s" % key)
        name = fm.get("name", "")
        if name in names:
            rep.err(where, "name 重复：%s（另见 %s）" % (name, names[name]))
        names[name] = where
        if not NAME_RE.match(name):
            rep.err(where, "name 只能含小写字母、数字、连字符：%r" % name)
        if name + ".md" != os.path.basename(f):
            rep.err(where, "文件名应为 %s.md" % name)
        desc = fm.get("description", "")
        if len(desc) > 1024:
            rep.err(where, "description 超过 1024 字符（%d）" % len(desc))
        model = fm.get("model", "")
        if model not in MODELS:
            rep.err(where, "model 不合法：%r（允许 %s）" % (model, "/".join(sorted(MODELS))))
        tier = team.get("tier", "standard")
        default = (mm["experts"].get(name) or mm["special"].get(name) or {}).get("model")
        want = ((run.get("model_overrides") or {}).get(tier) or {}).get(name, default)
        if want and model != want:
            rep.err(where, "model 应为 %s（merge_map 默认 + run.yaml model_overrides[%s]），实际 %s" % (want, tier, model))
        check_tools(rep, where, name, [t.strip() for t in fm.get("tools", "").split(",") if t.strip()])
        if name in mm["experts"]:
            for sec in ("身份", "职责", "产出", "上下游", "判断标准", "边界", "技能清单", "知识时效"):
                if not re.search(r"^## %s\s*$" % re.escape(sec), text, re.M):
                    rep.err(where, "缺少「%s」节" % sec)
            if not mm["experts"][name].get("retired") and common.KB_HOST_MARK not in text:
                rep.err(where, "缺少「%s」段落（build.py 工作方式里渲染，REQ-019），请重新 build / install" % common.KB_HOST_MARK)
            if mm["experts"][name].get("retired") and "已下线" not in desc:
                rep.err(where, "已下线角色的 description 必须写明「已下线」和替代角色")
    got = set(names)
    for miss in sorted(expected - got):
        rep.err(rel(agents_dir), "缺少 agent：%s.md" % miss)
    for extra in sorted(got - expected):
        rep.err(rel(agents_dir), "多余的 agent（merge_map / roles_overlay 里没有）：%s" % extra)
    base = len(common.load_merge_map()["experts"]) + 2
    if len(files) != base:
        rep.err(rel(agents_dir), "agent 数量应为 %d（专家 %d + 总控 + 技术情报员），实际 %d" % (base, base - 2, len(files)))


def check_tools(rep, where, name, tools):
    profile = None
    experts = common.load_experts()[1]
    if name in experts:
        profile = experts[name].get("tools_profile", "doc")
    for t in tools:
        if t.startswith("mcp__"):
            parts = t.split("__")
            tool = parts[-1] if len(parts) >= 3 else t
            if tool in KB_FORBIDDEN or "approve" in tool:
                rep.err(where, "禁用工具：%s（机密 / 需要用户本人操作 / 批准开发相关）" % t)
            elif tool.startswith("kb_"):
                if tool in KB_ORCH_WRITE and name != "orchestrator":
                    rep.err(where, "只有总控能用知识库写工具：%s" % t)
                elif tool not in KB_READ | KB_ORCH_WRITE:
                    rep.err(where, "不在白名单的 kb 工具：%s" % t)
            elif tool in DOCS_MCP_TOOLS:
                if name not in ENGINEERING:
                    rep.err(where, "文档类 MCP 只给工程角色：%s" % t)
            else:
                rep.err(where, "不在白名单的 MCP 工具：%s" % t)
            continue
        if t not in BASE_TOOLS:
            rep.err(where, "不在白名单的工具：%s" % t)
        if t == "WebSearch" and name != "tech-scout":
            rep.err(where, "WebSearch 只给技术情报员")
        if t == "WebFetch" and name not in ENGINEERING | {"tech-scout"}:
            rep.err(where, "WebFetch 只给技术情报员和需要查官方文档的工程角色")
        if t in ("Agent", "Task") and name != "orchestrator":
            rep.err(where, "只有总控能调度子 agent：%s" % t)
        if profile == "doc" and t in DOC_FORBIDDEN:
            rep.err(where, "只读代码 + 写文档的角色不能有 %s" % t)
    if name == "tech-scout" and ("Edit" in tools or "Bash" in tools):
        rep.err(where, "技术情报员不能有 Edit / Bash（只写提案）")


# ---------------- merge_map / roles ----------------
def check_merge_map(rep, mm):
    roles = common.load_roles()
    ids = [r["id"] for r in roles]
    where = "data/merge_map.json"
    if len(set(ids)) != len(ids):
        rep.err("data/roles.json", "岗位 id 重复")
    targets = set(mm["experts"]) | {"orchestrator", "none"}
    for rid in ids:
        if rid not in mm["map"]:
            rep.err(where, "原始岗位 %s 没有映射" % rid)
    for rid, m in mm["map"].items():
        if rid not in ids:
            rep.err(where, "映射了不存在的岗位：%s" % rid)
        if not isinstance(m.get("target"), str):
            rep.err(where, "%s 必须恰好映射到一个 target" % rid)
            continue
        if m["target"] not in targets:
            rep.err(where, "%s 映射到不存在的角色：%s" % (rid, m["target"]))
        for a in m.get("also") or []:
            if a not in mm["experts"]:
                rep.err(where, "%s 的 also 引用了不存在的专家：%s" % (rid, a))
        if m["target"] == "none" and not m.get("reason"):
            rep.err(where, "%s 标为不做 agent，必须写 reason" % rid)
    none = sorted(r for r, m in mm["map"].items() if m.get("target") == "none")
    if none != ["S-01"]:
        rep.warn(where, "不做 agent 的岗位应只有 S-01，实际：%s" % ", ".join(none))
    for slug in mm["experts"]:
        if not NAME_RE.match(slug):
            rep.err(where, "专家 slug 不合法：%s" % slug)
        if not common.expert_roles(mm, slug) and not mm["experts"][slug].get("overlay") and not mm["experts"][slug].get("retired"):
            rep.warn(where, "专家 %s 没有合并任何原始岗位" % slug)
    experts = common.load_experts()[1]
    for slug in mm["experts"]:
        if slug not in experts:
            rep.err("data/experts.json", "缺少专家档案：%s" % slug)


# ---------------- team.yaml ----------------
def check_team(rep, team, mm):
    where = "config/team.yaml"
    known = set(mm["experts"])
    enabled = team.get("enabled") or []
    for r in enabled:
        if r not in known:
            rep.err(where, "enabled 里有不存在的角色 id：%s" % r)
    for tier, spec in (team.get("tiers") or {}).items():
        roles = spec.get("roles")
        if isinstance(roles, list):
            for r in roles:
                if r not in known:
                    rep.err(where, "tiers.%s.roles 里有不存在的角色 id：%s" % (tier, r))
        for k, v in (spec.get("stand_in") or {}).items():
            for r in (k, v):
                if r not in known:
                    rep.err(where, "tiers.%s.stand_in 里有不存在的角色 id：%s" % (tier, r))
    for r in (team.get("ai_participation") or {}):
        if r not in known:
            rep.err(where, "ai_participation 里有不存在的角色 id：%s" % r)
    if team.get("tier") not in (team.get("tiers") or {}):
        rep.err(where, "tier=%s 不在 tiers 里" % team.get("tier"))
    cap = int(team.get("role_cap", 15))
    active = [r for r in enabled if r in known and not mm["experts"][r].get("retired")]
    total = len(active) + 1  # 含总控
    if total > cap:
        rep.warn(where, "启用角色数 %d（含总控）超过 role_cap=%d，超出的角色：%s" % (total, cap, ", ".join(active[cap - 1:])))


# ---------------- kb_scenes.json（REQ-005 / 019） ----------------
KB_SCENE_REQUIRED = ["触发", "上限", "只读", "标准", "精简"]
KB_SCENES_EXPECTED = ["管家", "流程设计", "需求", "需求体检", "方案", "开发", "开发·端", "审查·端", "Bug分析", "Bug修复", "跟进", "发布"]


def check_kb_scenes(rep, mm, team, path=None):
    """知识库场景表（v1 格式，变更 CR-001）：版本=1、12 个场景齐全、字段完整、角色名都存在（含 @端）、
    精简名单 ⊆ team.yaml tiers.lite.roles、只读安全角色不含工程师。"""
    path = path or common.KB_SCENES
    where = rel(path)
    if not os.path.exists(path):
        rep.err(where, "缺少知识库场景表（知识库会退回内置兜底）")
        return
    try:
        import json
        data = json.load(open(path, encoding="utf-8"))
    except Exception as e:
        rep.err(where, "JSON 解析失败：%s" % e)
        return
    if data.get("版本") != 1:
        rep.err(where, "版本 必须是 1（知识库按 v1 格式读，版本不对会整表退回内置兜底）：%r" % data.get("版本"))
    known = {k for k, v in mm["experts"].items() if not v.get("retired")}
    retired = {k for k, v in mm["experts"].items() if v.get("retired")}

    def check_role(r, ctx):
        if r == "@端":
            return
        if r in retired:
            rep.err(where, "%s 引用了已下线的角色：%s" % (ctx, r))
        elif r not in known:
            rep.err(where, "%s 引用了不存在的角色：%s" % (ctx, r))

    for k, r in (data.get("端角色") or {}).items():
        check_role(r, "端角色.%s" % k)
    if "默认" not in (data.get("端角色") or {}):
        rep.err(where, "端角色 缺少「默认」（@端 找不到对应端时用）")
    for key in ("只读安全角色", "自动场景不派"):
        for r in data.get(key) or []:
            check_role(r, key)
    for r in data.get("只读安全角色") or []:
        if r.endswith("-engineer") or r == "@端":
            rep.err(where, "只读安全角色 不能含工程师（子 agent 可能不继承只读会话的禁用工具）：%s" % r)
    lite = (team.get("tiers") or {}).get("lite") or {}
    lite_roles = lite.get("roles") if isinstance(lite.get("roles"), list) else list(known)
    lite_ok = set(lite_roles) | {"@端"}
    scenes = data.get("场景")
    if not isinstance(scenes, dict) or not scenes:
        rep.err(where, "缺少「场景」")
        return
    for name in KB_SCENES_EXPECTED:
        if name not in scenes:
            rep.err(where, "缺少场景：%s" % name)
    for name, sc in scenes.items():
        ctx = "场景「%s」" % name
        for f in KB_SCENE_REQUIRED:
            if f not in sc:
                rep.err(where, "%s 缺少字段 %s" % (ctx, f))
        lim = sc.get("上限")
        if not isinstance(lim, int) or isinstance(lim, bool) or lim < 0:
            rep.err(where, "%s 上限必须是非负整数：%r" % (ctx, lim))
        if not isinstance(sc.get("只读"), bool):
            rep.err(where, "%s 只读 必须是 true / false" % ctx)
        for tier in ("标准", "精简"):
            spec = sc.get(tier) or {}
            if not isinstance(spec.get("参与", None), list):
                rep.err(where, "%s.%s 缺少参与名单（没有参与角色写 []）" % (ctx, tier))
            roles = ([spec["主导"]] if spec.get("主导") else []) + list(spec.get("参与") or [])
            if not spec.get("主导"):
                rep.err(where, "%s.%s 缺少主导角色" % (ctx, tier))
            for r in roles:
                check_role(r, "%s.%s" % (ctx, tier))
                if tier == "精简" and r in known and r not in lite_ok:
                    rep.err(where, "%s.精简 用了 team.yaml tiers.lite 之外的角色：%s" % (ctx, r))
        for r in (sc.get("用途") or {}):
            check_role(r, "%s.用途" % ctx)


# ---------------- 技能包 ----------------
def check_skills(rep, mm, run):
    skills = common.load_skills()
    radar = common.radar_config()
    known = set(mm["experts"])
    stale = []
    per_role = {k: [] for k in known}
    for sid, s in skills.items():
        where = rel(s["path"])
        meta = s["meta"]
        if not meta:
            rep.err(where, "缺少 frontmatter")
            continue
        for k in common.SKILL_REQUIRED_FIELDS:
            if meta.get(k) in (None, "", []):
                rep.err(where, "缺少必填元数据 %s" % k)
        if not NAME_RE.match(str(meta.get("id", ""))):
            rep.err(where, "id 不合法：%r" % meta.get("id"))
        if s["layer"] == "skills" and os.path.basename(s["path"])[:-3] != meta.get("id"):
            rep.err(where, "文件名应与 id 一致")
        srcs = meta.get("sources") or []
        if not any(str(x).startswith(("http://", "https://")) for x in srcs):
            rep.err(where, "缺少来源链接（sources 至少 1 个 http(s) 链接）")
        if meta.get("maturity") not in common.MATURITIES:
            rep.err(where, "maturity 不合法：%r" % meta.get("maturity"))
        for reg, m in (meta.get("maturity_by_region") or {}).items():
            if m not in common.MATURITIES:
                rep.err(where, "maturity_by_region.%s 不合法：%r" % (reg, m))
        if meta.get("region", "both") not in ("cn", "global", "both"):
            rep.err(where, "region 只能是 cn / global / both")
        for r in meta.get("roles") or []:
            if r not in known:
                rep.err(where, "适用角色不存在：%s" % r)
            else:
                per_role[r].append(s)
        if meta.get("as_of") and not common.parse_date(meta.get("as_of")):
            rep.err(where, "as_of 不是日期：%r" % meta.get("as_of"))
        secs = common.sections(s["body"])
        for sec in common.SKILL_REQUIRED_SECTIONS:
            if sec not in secs:
                rep.err(where, "缺少「%s」节" % sec)
        if common.effective_maturity(s, radar) == "暂缓" or meta.get("maturity") == "暂缓":
            if not secs.get("替代") and not meta.get("replaced_by"):
                rep.err(where, "暂缓项必须写替代项（## 替代 节或 replaced_by）")
            elif not secs.get("替代"):
                rep.err(where, "暂缓项必须有「## 替代」节（原因、替代项、迁移建议）")
        for a in (meta.get("replaced_by") or []) + (meta.get("replaces") or []):
            if a not in skills:
                rep.warn(where, "replaces / replaced_by 引用的技能不存在：%s" % a)
        age = common.skill_age_days(s)
        limit = common.stale_limit(s, mm, run)
        if age is not None and age > limit:
            stale.append((sid, meta.get("as_of"), age, limit))
        if age is not None and age < 0:
            rep.warn(where, "as_of 在未来：%s" % meta.get("as_of"))
    if stale:
        rep.warn("data/skills", "过期技能包 %d 个（as_of 超过阈值，建议 /skills-refresh）：\n%s" % (
            len(stale), "\n".join("      - %s  as_of %s，%d 天（阈值 %d）" % x for x in stale)))
    # 首版覆盖要求（REQ-019）
    for slug, lst in sorted(per_role.items()):
        if mm["experts"][slug].get("retired"):
            continue
        if len(lst) < 5:
            rep.err("data/skills", "专家 %s 只挂了 %d 个技能包（至少 5 个）" % (slug, len(lst)))
        kind = mm["experts"][slug].get("kind")
        if slug in ENGINEERING or kind == "ai":
            new = [s for s in lst if not s["meta"].get("from_graph")]
            if len(new) < 3:
                rep.err("data/skills", "专家 %s 的新技能（from_graph: false）只有 %d 个（至少 3 个）" % (slug, len(new)))
    # 生成物同步
    for sid in skills:
        if not os.path.exists(common.p("skills", sid, "SKILL.md")):
            rep.err("skills/%s/SKILL.md" % sid, "缺少生成的 SKILL.md（运行 scripts/build.py）")
    return skills


# ---------------- 模板与交付物 ----------------
REQ_MARK = "<!-- 必填 -->"


def template_required(path):
    out = []
    for line in open(path, encoding="utf-8"):
        m = re.match(r"^##\s+(.+?)\s*<!--\s*必填\s*-->", line)
        if m:
            out.append(m.group(1).strip())
    return out


def check_templates(rep):
    d = common.p("templates", "deliverables")
    files = sorted(f for f in glob.glob(os.path.join(d, "*.md")) if not f.endswith("README.md"))
    if len(files) != 11:
        rep.err(rel(d), "交付物模板应为 11 个，实际 %d" % len(files))
    for f in files:
        first = open(f, encoding="utf-8").readline()
        tid = os.path.basename(f)[:-3]
        if "template: %s" % tid not in first:
            rep.err(rel(f), "第一行应为 <!-- template: %s ... -->" % tid)
        if not template_required(f):
            rep.err(rel(f), "没有标记任何必填节")
    prd, tech = os.path.join(d, "03-prd.md"), os.path.join(d, "06-tech-design.md")
    if os.path.exists(prd) and "AI 机会评估" not in template_required(prd):
        rep.err(rel(prd), "PRD 模板缺少必填节「AI 机会评估」")
    if os.path.exists(tech) and "选型及成熟度" not in template_required(tech):
        rep.err(rel(tech), "技术方案模板缺少必填节「选型及成熟度」")


def _meaningful(content):
    lines = []
    for line in content.splitlines():
        s = re.sub(r"<!--.*?-->", "", line).strip()
        if not s or re.fullmatch(r"[（(].*[)）]", s) or re.fullmatch(r"\|?[\s\-|:]*\|?", s):
            continue
        if re.fullmatch(r"-\s*[^：:]{1,30}[：:]\s*", s):  # 只有「- 结论：」这种空填空
            continue
        lines.append(s)
    # 只有表头一行不算内容
    table = [x for x in lines if x.startswith("|")]
    if lines and len(table) == len(lines) and len(table) <= 1:
        return []
    return lines


def check_deliverable(rep, path):
    where = path
    text = open(path, encoding="utf-8").read()
    m = re.search(r"<!--\s*template:\s*([a-z0-9-]+)", text)
    if not m:
        rep.err(where, "开头缺少 <!-- template: xx --> 标记，无法确定模板")
        return
    tid = m.group(1)
    tpath = common.p("templates", "deliverables", tid + ".md")
    if not os.path.exists(tpath):
        rep.err(where, "模板不存在：%s" % tid)
        return
    required = template_required(tpath)
    secs = {re.sub(r"\s*<!--.*?-->\s*", "", k).strip(): v for k, v in common.sections(text).items()}
    lang_en = bool(re.search(r"lang:\s*en", text[:300]))
    if lang_en:
        # 英文产物：按顺序对齐必填节
        heads = [k for k in secs]
        if len(heads) < len(required):
            rep.err(where, "英文产物的节数少于模板必填节（%d < %d）" % (len(heads), len(required)))
        return
    for sec in required:
        if sec not in secs:
            rep.err(where, "缺少必填节「%s」" % sec)
        elif not _meaningful(secs[sec]):
            rep.err(where, "必填节「%s」为空" % sec)
    if tid == "03-prd" and "AI 机会评估" in secs:
        if not re.search(r"结论[:：]\s*(\*\*)?\s*(用|不用)", secs["AI 机会评估"]):
            rep.err(where, "「AI 机会评估」没有结论（需写「结论：用 AI / 不用 AI」及理由）")
    if tid == "06-tech-design" and "选型及成熟度" in secs:
        body = secs["选型及成熟度"]
        rows = [r for r in body.splitlines() if r.startswith("|") and not re.fullmatch(r"\|[\s\-|:]*\|", r)][1:]
        for r in rows:
            if not re.search(r"采用|试用|评估|暂缓", r):
                rep.err(where, "选型行没有标成熟度：%s" % r[:60])
            if "试用" in r and len([c for c in r.split("|") if c.strip()]) < 5:
                rep.err(where, "「试用」选型必须写风险与回退：%s" % r[:60])
    if "引用" in required and "引用" in secs and not _meaningful(secs["引用"]):
        pass  # 已在上面报过


# ---------------- 评测集 / stages ----------------
def check_eval(rep, mm):
    cases = common.read_json(common.p("scripts", "eval_routing", "cases.json"), {"cases": []})["cases"]
    where = "scripts/eval_routing/cases.json"
    if len(cases) < 30:
        rep.err(where, "选角评测集至少 30 条，实际 %d" % len(cases))
    cnt = {k: 0 for k in mm["experts"]}
    for c in cases:
        for e in [c.get("expect")] + (c.get("also_ok") or []):
            if e and e not in cnt and e != "orchestrator":
                rep.err(where, "期望角色不存在：%s" % e)
        if c.get("expect") in cnt:
            cnt[c["expect"]] += 1
    for k, v in cnt.items():
        if v < 2 and not mm["experts"][k].get("retired"):
            rep.err(where, "专家 %s 的评测用例少于 2 条（%d）" % (k, v))
    sk = common.read_json(common.p("scripts", "eval_skills", "cases.json"), {"cases": []})["cases"]
    c2 = {k: 0 for k in mm["experts"]}
    for c in sk:
        if c.get("role") in c2:
            c2[c["role"]] += 1
    for k, v in c2.items():
        if v < 3 and not mm["experts"][k].get("retired"):
            rep.err("scripts/eval_skills/cases.json", "专家 %s 的技能回归题少于 3 条（%d）" % (k, v))


def check_stages(rep, mm):
    path = common.p("workflow", "stages.md")
    if not os.path.exists(path):
        rep.err("workflow/stages.md", "缺少")
        return
    allowed = [v["name"] for v in mm["experts"].values()] + ["总控", "架构师"]
    for line in open(path, encoding="utf-8"):
        m = re.match(r"^\|\s*0\d\s*\|[^|]+\|([^|]+)\|", line)
        if m:
            lead = m.group(1)
            stripped = lead
            for a in sorted(allowed, key=len, reverse=True):
                stripped = stripped.replace(a, "")
            for raw in RAW_LEAD_NAMES:
                if raw in stripped:
                    rep.err("workflow/stages.md", "主导角色出现已合并的原始岗位名「%s」：%s" % (raw, lead.strip()))
            if not any(a in lead for a in allowed):
                rep.err("workflow/stages.md", "主导角色不是 14 个专家或总控：%s" % lead.strip())


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--agents-dir", default=common.p("agents"))
    ap.add_argument("--deliverable", nargs="+", help="只校验交付物")
    args = ap.parse_args(argv)
    rep = Report()
    if args.deliverable:
        for d in args.deliverable:
            check_deliverable(rep, d)
        return rep.print()
    mm = common.load_merge_map()
    team, run = common.team_config(), common.run_config()
    check_merge_map(rep, mm)
    check_agents(rep, args.agents_dir, mm, team, run)
    check_team(rep, team, mm)
    check_kb_scenes(rep, mm, team)
    check_skills(rep, mm, run)
    check_templates(rep)
    check_eval(rep, mm)
    check_stages(rep, mm)
    return rep.print()


if __name__ == "__main__":
    sys.exit(main())
