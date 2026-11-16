"""公共工具：路径、JSON/YAML 读写、技能包加载（技能层 + local 覆盖）、成熟度计算。"""
import datetime as _dt
import hashlib
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import miniyaml  # noqa: E402

ROOT = os.environ.get("WORKER_AGENT_HOME") or os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA = os.path.join(ROOT, "data")
SKILLS_DIR = os.path.join(DATA, "skills")
LOCAL_DIR = os.path.join(ROOT, "local")
CONFIG = os.path.join(ROOT, "config")

MATURITIES = ["采用", "试用", "评估", "暂缓"]
AI_DOMAINS = {"ai-product", "ai-app", "ai-model", "ai-infra", "ai-eval"}
SKILL_REQUIRED_FIELDS = ["id", "name", "roles", "maturity", "as_of", "version", "sources"]
KB_HOST_MARK = "知识库宿主模式"          # build.py 渲染进每个专家、validate.py 检查（REQ-019）
KB_SCENES = os.path.join(CONFIG, "kb_scenes.json")  # 知识库场景表（REQ-005）
SKILL_REQUIRED_SECTIONS = ["什么时候用", "关键做法", "常见坑", "迁移", "最佳做法", "CHANGELOG"]


def p(*parts):
    return os.path.join(ROOT, *parts)


def today():
    override = os.environ.get("WORKER_AGENT_TODAY")
    if override:
        return _dt.date.fromisoformat(override)
    return _dt.date.today()


def now_iso():
    return _dt.datetime.now().astimezone().isoformat(timespec="seconds")


def read_json(path, default=None):
    if not os.path.exists(path):
        return default
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def write_json(path, data):
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    text = json.dumps(data, ensure_ascii=False, indent=2) + "\n"
    write_text(path, text)


def write_text(path, text):
    """只在内容变化时写，保证可重复生成、mtime 不乱跳。返回是否改动。"""
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            if f.read() == text:
                return False
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)
    return True


def read_yaml(path, default=None):
    if not os.path.exists(path):
        return default
    return miniyaml.load(path)


def sha8(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:8]


def split_frontmatter(text):
    m = re.match(r"^---\n(.*?)\n---\n?(.*)$", text, re.S)
    if not m:
        return None, text
    return miniyaml.loads(m.group(1)), m.group(2)


def sections(body):
    """返回 {二级标题: 内容}。"""
    out, cur, buf = {}, None, []
    for line in body.splitlines():
        m = re.match(r"^##\s+(.+?)\s*$", line)
        if m:
            if cur is not None:
                out[cur] = "\n".join(buf).strip()
            cur, buf = m.group(1), []
        elif cur is not None:
            buf.append(line)
    if cur is not None:
        out[cur] = "\n".join(buf).strip()
    return out


def parse_date(v):
    if isinstance(v, _dt.date):
        return v
    try:
        return _dt.date.fromisoformat(str(v)[:10])
    except ValueError:
        return None


def _scan_skill_dir(base, layer):
    found = {}
    if not os.path.isdir(base):
        return found
    for dirpath, _, files in os.walk(base):
        for fn in sorted(files):
            if not fn.endswith(".md") or fn.startswith("_") or fn.upper() == "README.MD":
                continue
            path = os.path.join(dirpath, fn)
            with open(path, encoding="utf-8") as f:
                text = f.read()
            meta, body = split_frontmatter(text)
            domain = os.path.relpath(dirpath, base).split(os.sep)[0]
            if domain == ".":
                domain = (meta or {}).get("domain", "misc")
            sid = (meta or {}).get("id") or fn[:-3]
            found[sid] = {"id": sid, "meta": meta or {}, "body": body, "path": path,
                          "domain": domain, "layer": layer, "text": text}
    return found


def load_skills(include_local=True):
    """技能层 + local/skills 覆盖层（同 id 以 local 为准）。"""
    skills = _scan_skill_dir(SKILLS_DIR, "skills")
    if include_local:
        for sid, s in _scan_skill_dir(os.path.join(LOCAL_DIR, "skills"), "local").items():
            if sid in skills:
                s["overrides"] = skills[sid]["path"]
                if s["domain"] == "misc":
                    s["domain"] = skills[sid]["domain"]
            skills[sid] = s
    return dict(sorted(skills.items()))


def run_config():
    return read_yaml(os.path.join(CONFIG, "run.yaml"), {}) or {}


def radar_config():
    return read_yaml(os.path.join(CONFIG, "radar.yaml"), {}) or {}


def team_config():
    return read_yaml(os.path.join(CONFIG, "team.yaml"), {}) or {}


def effective_maturity(skill, radar=None):
    """radar.yaml 覆盖 > maturity_by_region[region] > maturity。"""
    radar = radar if radar is not None else radar_config()
    meta = skill["meta"]
    overrides = radar.get("overrides") or {}
    if skill["id"] in overrides:
        ov = overrides[skill["id"]]
        return ov.get("maturity") if isinstance(ov, dict) else ov
    region = radar.get("region", "cn")
    by_region = meta.get("maturity_by_region") or {}
    if isinstance(by_region, dict) and region in by_region:
        return by_region[region]
    return meta.get("maturity")


def is_ai_skill(skill, merge_map=None):
    if skill["domain"] in AI_DOMAINS:
        return True
    if merge_map:
        ai_experts = {k for k, v in merge_map["experts"].items() if v.get("kind") == "ai"}
        return bool(set(skill["meta"].get("roles") or []) & ai_experts)
    return False


def stale_limit(skill, merge_map=None, run=None):
    run = run if run is not None else run_config()
    if is_ai_skill(skill, merge_map):
        return int(run.get("stale_days_ai", 90))
    return int(run.get("stale_days", 180))


def skill_age_days(skill):
    d = parse_date(skill["meta"].get("as_of"))
    if not d:
        return None
    return (today() - d).days


def load_merge_map():
    """merge_map.json + roles_overlay.json（新增专家 / 并入 / 下线）。"""
    mm = read_json(os.path.join(DATA, "merge_map.json"))
    ov = read_json(os.path.join(DATA, "roles_overlay.json"), {}) or {}
    mm = json.loads(json.dumps(mm))
    for slug, spec in (ov.get("new_experts") or {}).items():
        mm["experts"][slug] = spec
    for rid, target in (ov.get("merge") or {}).items():
        mm["map"][rid] = target if isinstance(target, dict) else {"target": target}
    for role in ov.get("add_roles") or []:
        if role.get("target"):
            mm["map"][role["id"]] = {"target": role["target"], "overlay": True}
    for slug, spec in (ov.get("retire") or {}).items():
        if slug in mm["experts"]:
            mm["experts"][slug]["retired"] = spec
    return mm


def load_roles():
    """roles.json + roles_overlay.add_roles。"""
    roles = read_json(os.path.join(DATA, "roles.json"), {"roles": []})
    ov = read_json(os.path.join(DATA, "roles_overlay.json"), {}) or {}
    out = list(roles.get("roles", []))
    known = {r["id"] for r in out}
    for r in ov.get("add_roles") or []:
        if r["id"] not in known:
            rr = dict(r)
            rr["source"] = "overlay"
            out.append(rr)
    return out


def active_experts(mm):
    return {k: v for k, v in mm["experts"].items() if not v.get("retired")}


def expert_roles(mm, slug):
    """某专家合并了哪些原始岗位（含 also）。返回 [(id, primary_bool)]。"""
    out = []
    for rid, m in sorted(mm["map"].items(), key=lambda kv: kv[0]):
        if m["target"] == slug:
            out.append((rid, True))
        elif slug in (m.get("also") or []):
            out.append((rid, False))
    return out


def warn(msg):
    print("⚠️  " + msg, file=sys.stderr)


def load_experts():
    """专家档案：data/experts.json + roles_overlay.new_experts[*].profile + local/experts.json（后者优先）。
    返回 (tools_profiles, {slug: profile})。"""
    ex = read_json(os.path.join(DATA, "experts.json"))
    ov = read_json(os.path.join(DATA, "roles_overlay.json"), {}) or {}
    local = read_json(os.path.join(LOCAL_DIR, "experts.json"), {}) or {}
    out = dict(ex["experts"])
    for slug, spec in (ov.get("new_experts") or {}).items():
        if spec.get("profile"):
            out[slug] = spec["profile"]
    for slug, over in (local.get("experts") or {}).items():
        if slug in out:
            out[slug] = _deep_merge(out[slug], over)
    return ex["tools_profiles"], out


def _deep_merge(base, over):
    res = dict(base)
    for k, v in (over or {}).items():
        res[k] = _deep_merge(res[k], v) if isinstance(v, dict) and isinstance(res.get(k), dict) else v
    return res
