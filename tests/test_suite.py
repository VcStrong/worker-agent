#!/usr/bin/env python3
"""套件自测：每个用例把仓库拷到临时目录里跑脚本，不改动真实仓库。

运行：python3 -m unittest discover -s tests -v
"""
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PY = sys.executable
GRAPH = os.path.join(REPO, "source", "graph.html")


def copy_repo(git=False):
    d = tempfile.mkdtemp(prefix="ra-test-")
    dst = os.path.join(d, "wa")
    shutil.copytree(REPO, dst, ignore=shutil.ignore_patterns(".git", "state", "snapshots", "build", "__pycache__", ".dev"))
    if os.path.exists(os.path.join(dst, "usage", "usage.jsonl")):
        os.remove(os.path.join(dst, "usage", "usage.jsonl"))
    if git:
        for args in (["init", "-q"], ["add", "-A"], ["-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qm", "init"]):
            subprocess.run(["git", "-C", dst] + args, check=True, capture_output=True)
    return dst


def run(root, *args, env=None, stdin=None):
    e = dict(os.environ)
    e.pop("WORKER_AGENT_HOME", None)
    e.pop("KB_SESSION", None)  # 测试可能跑在知识库后台会话里，hook 行为不能受外层环境影响
    e.update(env or {})
    r = subprocess.run([PY] + [os.path.join(root, a) if a.endswith(".py") and not os.path.isabs(a) else a for a in args],
                       capture_output=True, text=True, cwd=root, env=e, input=stdin)
    return r.returncode, r.stdout + r.stderr


def fm(path):
    t = open(path, encoding="utf-8").read()
    m = re.match(r"^---\n(.*?)\n---\n", t, re.S)
    return dict(l.split(": ", 1) for l in m.group(1).splitlines() if ": " in l)


class Extract(unittest.TestCase):
    def test_extract_48_roles_fields_and_deterministic(self):
        root = copy_repo()
        rc, out = run(root, "scripts/extract.py", GRAPH)
        self.assertEqual(rc, 0, out)
        data = json.load(open(os.path.join(root, "data", "roles.json"), encoding="utf-8"))
        self.assertEqual(len(data["roles"]), 48)
        need = ["id", "family_name", "name", "positioning", "duties", "outputs", "abilities", "upstream", "downstream",
                "stages", "lead_stages", "tools", "metrics", "career", "work", "terms", "unwritten_rules"]
        for r in data["roles"]:
            for k in need:
                self.assertIn(k, r)
            self.assertTrue(any(g["group"] == "AI 协同" for g in r["terms"]))
            for t in r["tools"]:
                self.assertEqual(t["source"], "图谱")
        before = open(os.path.join(root, "data", "roles.json"), "rb").read()
        run(root, "scripts/extract.py", GRAPH)
        self.assertEqual(before, open(os.path.join(root, "data", "roles.json"), "rb").read())

    def test_missing_field_and_unmapped_role_warn_and_skills_untouched(self):
        root = copy_repo()
        html = open(GRAPH, encoding="utf-8").read()
        html = html.replace('m:"需求交付率、版本目标达成度、需求变更率、核心业务指标",', "", 1)
        html = html.replace("const ROLES = [", 'const ROLES = [\n{id:"X-01",f:"I",n:"提示词运营",t:"新岗位",d:["a"],o:["b"],k:["c"],u:"x",dn:"y",s:[9],l:[9],tl:["Z"],m:"m",p:"p"},', 1)
        p = os.path.join(root, "g.html")
        open(p, "w", encoding="utf-8").write(html)
        skills_before = {f: open(f, "rb").read() for f in _skill_files(root)}
        rc, out = run(root, "scripts/extract.py", p)
        self.assertEqual(rc, 0, out)
        self.assertIn("P-01 缺少字段 metrics", out)
        self.assertIn("X-01 提示词运营", out)
        self.assertIn("没有映射", out)
        self.assertEqual(skills_before, {f: open(f, "rb").read() for f in _skill_files(root)})
        rc, out = run(root, "scripts/build.py", "--mcp", "none", "--quiet")
        self.assertEqual(rc, 0, out)
        self.assertEqual(len(os.listdir(os.path.join(root, "agents"))), 16)


def _skill_files(root):
    out = []
    for d, _, fs in os.walk(os.path.join(root, "data", "skills")):
        out += [os.path.join(d, f) for f in fs]
    return sorted(out)


class BuildValidate(unittest.TestCase):
    def test_build_16_agents_models_tools(self):
        root = copy_repo()
        rc, out = run(root, "scripts/build.py", "--mcp", "kb")
        self.assertEqual(rc, 0, out)
        agents = os.path.join(root, "agents")
        self.assertEqual(len([f for f in os.listdir(agents) if f.endswith(".md")]), 16)
        opus = {"orchestrator", "architect", "product-manager", "ai-product-manager", "tech-scout"}
        for f in os.listdir(agents):
            h = fm(os.path.join(agents, f))
            self.assertEqual(h["model"], "opus" if h["name"] in opus else "sonnet", f)
            self.assertNotIn("kb_base_secret", h["tools"])
            if h["name"] != "orchestrator":
                self.assertNotIn("kb_log", h["tools"])
                self.assertNotIn("kb_ask", h["tools"])
            if h["name"] == "product-manager":
                self.assertNotIn("Edit", h["tools"])
                self.assertNotIn("Bash", h["tools"])
                self.assertIn("mcp__kb__kb_search", h["tools"])
        rc, out = run(root, "scripts/validate.py")
        self.assertEqual(rc, 0, out)

    def test_no_kb_no_kb_tools(self):
        root = copy_repo()
        rc, out = run(root, "scripts/build.py", "--mcp", "none")
        for f in os.listdir(os.path.join(root, "agents")):
            self.assertNotIn("mcp__", fm(os.path.join(root, "agents", f))["tools"])

    def test_context7_only_engineering(self):
        root = copy_repo()
        run(root, "scripts/build.py", "--mcp", "context7")
        self.assertIn("mcp__context7__", fm(os.path.join(root, "agents", "backend-engineer.md"))["tools"])
        self.assertNotIn("mcp__context7__", fm(os.path.join(root, "agents", "product-manager.md"))["tools"])
        self.assertIn("先用文档类 MCP", open(os.path.join(root, "agents", "frontend-engineer.md"), encoding="utf-8").read())

    def test_model_overrides(self):
        root = copy_repo()
        p = os.path.join(root, "config", "run.yaml")
        t = open(p, encoding="utf-8").read().replace("  standard: {}", "  standard: {data-growth: haiku, architect: sonnet}")
        open(p, "w", encoding="utf-8").write(t)
        run(root, "scripts/build.py", "--mcp", "none")
        self.assertEqual(fm(os.path.join(root, "agents", "data-growth.md"))["model"], "haiku")
        self.assertEqual(fm(os.path.join(root, "agents", "architect.md"))["model"], "sonnet")
        rc, out = run(root, "scripts/validate.py")
        self.assertEqual(rc, 0, out)

    def test_validate_errors(self):
        root = copy_repo()
        run(root, "scripts/build.py", "--mcp", "none")
        # 长 description、禁用工具、非总控写工具
        p = os.path.join(root, "agents", "qa-expert.md")
        t = open(p, encoding="utf-8").read()
        t = re.sub(r"^description: .*$", "description: " + "长" * 1100, t, count=1, flags=re.M)
        t = re.sub(r"^tools: (.*)$", r"tools: \1, mcp__kb__kb_base_secret, mcp__kb__kb_log", t, count=1, flags=re.M)
        open(p, "w", encoding="utf-8").write(t)
        # team.yaml 不存在的角色 + 超编
        tp = os.path.join(root, "config", "team.yaml")
        tt = open(tp, encoding="utf-8").read().replace("role_cap: 15", "role_cap: 10").replace("  - ai-eval-compliance\n", "  - ai-eval-compliance\n  - no-such-role\n", 1)
        open(tp, "w", encoding="utf-8").write(tt)
        # 技能包缺来源和 as_of；暂缓缺替代
        sp = os.path.join(root, "data", "skills", "frontend", "vite.md")
        st = open(sp, encoding="utf-8").read()
        st = re.sub(r"^as_of:.*\n", "", st, count=1, flags=re.M)
        st = re.sub(r"^sources:\n(  - .*\n)+", "sources: []\n", st, count=1, flags=re.M)
        open(sp, "w", encoding="utf-8").write(st)
        wp = os.path.join(root, "data", "skills", "frontend", "webpack.md")
        wt = re.sub(r"## 替代\n.*?(?=\n## )", "", open(wp, encoding="utf-8").read(), count=1, flags=re.S)
        wt = re.sub(r"^replaced_by:.*\n(  - .*\n)*", "", wt, count=1, flags=re.M)
        open(wp, "w", encoding="utf-8").write(wt)
        rc, out = run(root, "scripts/validate.py")
        self.assertNotEqual(rc, 0)
        for s in ("description 超过 1024", "禁用工具：mcp__kb__kb_base_secret", "只有总控能用知识库写工具",
                  "不存在的角色 id：no-such-role", "超过 role_cap=10", "缺少来源链接", "缺少必填元数据 as_of", "暂缓项必须"):
            self.assertIn(s, out)

    def test_stale_warning_exit_zero(self):
        root = copy_repo()
        rc, out = run(root, "scripts/validate.py", env={"WORKER_AGENT_TODAY": "2027-03-01"})
        self.assertEqual(rc, 0, out)
        self.assertIn("过期技能包", out)
        self.assertIn("mcp", out)          # AI 技能 90 天就过期
        self.assertNotIn("  - vite ", out)  # 普通技能 180 天未过期

    def test_local_override_wins(self):
        root = copy_repo()
        src = os.path.join(root, "data", "skills", "frontend", "vite.md")
        dst = os.path.join(root, "local", "skills", "frontend", "vite.md")
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        open(dst, "w", encoding="utf-8").write(open(src, encoding="utf-8").read().replace("maturity: 采用", "maturity: 试用"))
        run(root, "scripts/build.py", "--mcp", "none")
        t = open(os.path.join(root, "agents", "frontend-engineer.md"), encoding="utf-8").read()
        trial = t.split("### 试用")[1].split("###")[0]
        self.assertIn("`vite`", trial)
        self.assertIn("local/ 覆盖", trial)

    def test_merge_map_change_syncs_agents(self):
        root = copy_repo()
        mp = os.path.join(root, "data", "merge_map.json")
        mm = json.load(open(mp, encoding="utf-8"))
        del mm["experts"]["ai-infra-mlops"]
        mm["map"]["I-05"] = {"target": "ai-app-engineer"}
        mm["map"]["I-08"] = {"target": "ai-app-engineer"}
        json.dump(mm, open(mp, "w", encoding="utf-8"), ensure_ascii=False)
        rc, out = run(root, "scripts/build.py", "--mcp", "none")
        self.assertIn("删除 agents/ai-infra-mlops.md", out)
        self.assertFalse(os.path.exists(os.path.join(root, "agents", "ai-infra-mlops.md")))
        self.assertEqual(len(os.listdir(os.path.join(root, "agents"))), 15)

    def test_region_global_switches_default(self):
        root = copy_repo()
        rp = os.path.join(root, "config", "radar.yaml")
        t = open(rp, encoding="utf-8").read()
        open(rp, "w", encoding="utf-8").write(t.replace("region: cn", "region: global"))
        run(root, "scripts/build.py", "--mcp", "none")
        t = open(os.path.join(root, "agents", "client-engineer.md"), encoding="utf-8").read()
        adopt = t.split("### 采用")[1].split("###")[0]
        self.assertIn("`fcm`", adopt)
        self.assertNotIn("`push-cn-vendor-channels`", adopt)

    def test_radar_override_paused(self):
        root = copy_repo()
        rp = os.path.join(root, "config", "radar.yaml")
        t = open(rp, encoding="utf-8").read()
        open(rp, "w", encoding="utf-8").write(t.replace("overrides: {}", "overrides:\n  tailwind-css-v4: {maturity: 暂缓}"))
        rc, out = run(root, "scripts/build.py", "--mcp", "none")
        t = open(os.path.join(root, "agents", "frontend-engineer.md"), encoding="utf-8").read()
        self.assertIn("`tailwind-css-v4`", t.split("### 暂缓")[1])


class Who(unittest.TestCase):
    def q(self, *a):
        return run(REPO, "scripts/who.py", *a)

    def test_queries(self):
        rc, out = self.q("灰度")
        self.assertIn("SRE 与安全工程师", out)
        self.assertIn("客户端工程师", out)
        rc, out = self.q("DBA")
        self.assertIn("后端工程师", out)
        rc, out = self.q("HRBP")
        self.assertIn("不做 agent", out)
        rc, out = self.q("后端工程师")
        self.assertIn("合并了原始岗位", out)
        rc, out = self.q("ArkTS")
        self.assertIn("成熟度 采用", out)
        self.assertIn("as_of", out)
        rc, out = self.q("Webpack")
        self.assertIn("暂缓", out)
        self.assertIn("替代", out)
        rc, out = self.q("不存在的词qq")
        self.assertEqual(rc, 1)
        self.assertIn("未找到", out)
        self.assertEqual(len(out.split("最接近的词：")[1].strip().split("、")), 3)


class Evals(unittest.TestCase):
    def test_routing_and_skills(self):
        rc, out = run(REPO, "scripts/eval_routing/run_eval.py")
        self.assertEqual(rc, 0, out)
        rc, out = run(REPO, "scripts/eval_skills/run_skill_eval.py")
        self.assertEqual(rc, 0, out)


class Hooks(unittest.TestCase):
    def test_usage_hook_and_report(self):
        root = copy_repo()
        evts = [
            {"hook_event_name": "PreToolUse", "tool_name": "Task", "cwd": "/p", "tool_input": {"subagent_type": "backend-engineer", "prompt": "写 workspace/checkin-points/06-x.md"}},
            {"hook_event_name": "PreToolUse", "tool_name": "Agent", "cwd": "/p", "tool_input": {"subagent_type": "backend-engineer"}},
            {"hook_event_name": "PreToolUse", "tool_name": "Agent", "cwd": "/p", "tool_input": {"subagent_type": "general-purpose"}},
            {"hook_event_name": "PreToolUse", "tool_name": "Read", "cwd": "/p", "tool_input": {"file_path": "/p/.claude/skills/vite/SKILL.md"}},
            {"hook_event_name": "PreToolUse", "tool_name": "Skill", "cwd": "/p", "tool_input": {"skill": "who"}},
        ]
        for e in evts:
            rc, out = run(root, "scripts/hooks/usage_hook.py", stdin=json.dumps(e))
            self.assertEqual((rc, out), (0, ""))
        lines = open(os.path.join(root, "usage", "usage.jsonl"), encoding="utf-8").read().splitlines()
        self.assertEqual(len(lines), 4)
        self.assertEqual(json.loads(lines[0])["need"], "checkin-points")
        rc, out = run(root, "scripts/usage_report.py", "--json")
        rep = json.loads(out)
        self.assertEqual(rep["roles"][0]["slug"], "backend-engineer")
        self.assertEqual(rep["roles"][0]["count"], 2)
        self.assertEqual(len(rep["roles"]), 14)
        self.assertEqual(rep["skills"][0]["id"], "vite")

    def test_usage_rotation(self):
        root = copy_repo()
        e = json.dumps({"hook_event_name": "PreToolUse", "tool_name": "Agent", "cwd": "/p", "tool_input": {"subagent_type": "qa-expert"}})
        env = {"WORKER_AGENT_USAGE_MAX_BYTES": "300"}
        for _ in range(6):
            run(root, "scripts/hooks/usage_hook.py", stdin=e, env=env)
        self.assertTrue(os.listdir(os.path.join(root, "usage", "archive")))
        rep = json.loads(run(root, "scripts/usage_report.py", "--json")[1])
        self.assertEqual(rep["roles"][0]["count"], 6)

    def test_fallback_to_log(self):
        root = copy_repo()
        proj = tempfile.mkdtemp()
        os.makedirs(os.path.join(proj, "workspace", "x"))
        open(os.path.join(proj, "workspace", "x", "log.md"), "w").write(
            '<!--usage {"ts":"2026-11-14T10:00:00+08:00","event":"call","role":"qa-expert#1","stage":"07","need":"x"} -->\n')
        rc, out = run(root, "scripts/usage_report.py", "--workspace", proj)
        self.assertIn("hook 未生效", out)
        self.assertIn("测试专家（qa-expert）", out.splitlines()[3])

    def test_guard_hook(self):
        def g(evt):
            rc, out = run(REPO, "scripts/hooks/guard_hook.py", stdin=json.dumps(evt))
            return json.loads(out)["hookSpecificOutput"]["permissionDecision"] if out.strip() else None
        for cmd in ("git push origin main", "rm -rf build", "kubectl apply -f x.yaml", "npm publish", "mysql -e 'DROP TABLE t'"):
            self.assertEqual(g({"tool_name": "Bash", "tool_input": {"command": cmd}}), "ask", cmd)
        self.assertIsNone(g({"tool_name": "Bash", "tool_input": {"command": "npm test"}}))
        self.assertEqual(g({"tool_name": "Write", "tool_input": {"file_path": os.path.join(REPO, "data/skills/frontend/vite.md")}}), "deny")
        self.assertEqual(g({"tool_name": "Edit", "agent_type": "product-manager", "tool_input": {"file_path": "/p/src/a.ts"}}), "deny")
        self.assertIsNone(g({"tool_name": "Write", "agent_type": "product-manager", "tool_input": {"file_path": "/p/workspace/x/02-PRD.md"}}))

    def test_refresh_check(self):
        root = copy_repo()
        env = {"WORKER_AGENT_TODAY": "2026-11-20"}
        run(root, "scripts/rollback.py", "--snapshot", "init", env=env)
        rc, out = run(root, "scripts/refresh_check.py", "--hook", env=env)
        self.assertEqual(out.strip(), "")                      # 无过期、不足 30 天：不提醒
        env = {"WORKER_AGENT_TODAY": "2027-03-01"}
        rc, out = run(root, "scripts/refresh_check.py", "--hook", env=env)
        ctx = json.loads(out)["hookSpecificOutput"]["additionalContext"]
        self.assertIn("不回复不会消耗 AI 用量", ctx)
        self.assertIn("暂无使用数据", ctx)
        rc, out = run(root, "scripts/refresh_check.py", "--hook", env=env)
        self.assertEqual(out.strip(), "")                      # 当天去重
        run(root, "scripts/refresh_check.py", "--snooze", "7", env={"WORKER_AGENT_TODAY": "2027-03-02"})
        rc, out = run(root, "scripts/refresh_check.py", env={"WORKER_AGENT_TODAY": "2027-03-08"})
        self.assertEqual(out.strip(), "")                      # 暂缓期内
        rc, out = run(root, "scripts/refresh_check.py", env={"WORKER_AGENT_TODAY": "2027-03-09"})
        self.assertIn("技能更新提醒", out)


PROPOSAL = """# 测试提案
### T-01 vite 补来源
```yaml
action: add_source
skill: vite
evidence: [https://vite.dev/test-source]
trivial: true
status: 待拍板
```
### T-02 tailwind 改为试用
```yaml
action: update_maturity
skill: tailwind-css-v4
suggested_maturity: 试用
evidence: [https://tailwindcss.com/blog]
published: 2026-11-01
reason: 测试
status: 待拍板
```
### T-03 jetpack-compose 暂缓（会让技能回归题退化）
```yaml
action: deprecate
skill: jetpack-compose
suggested_maturity: 暂缓
replaced_by: [android-xml-layout]
evidence: [https://developer.android.com/compose]
published: 2026-11-01
reason: 测试退化
status: 待拍板
```
### T-04 经验：签到跨天
```yaml
action: append_lesson
skill: postgresql
section: 常见坑
text: 签到按用户时区算自然日，唯一约束用 (user_id, sign_date) 防重复签到
source_need: checkin-points
role: backend-engineer
scope: public
status: 待拍板
```
"""


class Proposals(unittest.TestCase):
    def setup(self, git):
        root = copy_repo(git=git)
        p = os.path.join(root, "proposals", "2026-11-20-test.md")
        open(p, "w", encoding="utf-8").write(PROPOSAL)
        return root, p

    def test_check_and_trivial_off(self):
        root, p = self.setup(False)
        rc, out = run(root, "scripts/apply_proposal.py", p, "--check")
        self.assertEqual(rc, 0, out)
        rc, out = run(root, "scripts/apply_proposal.py", p)   # auto_apply_trivial=false：什么都不应用
        self.assertIn("没有要应用的条目", out)
        self.assertNotIn("https://vite.dev/test-source", open(os.path.join(root, "data/skills/frontend/vite.md"), encoding="utf-8").read())

    def test_trivial_on_only_trivial(self):
        root, p = self.setup(False)
        rp = os.path.join(root, "config", "run.yaml")
        t = open(rp, encoding="utf-8").read()
        open(rp, "w", encoding="utf-8").write(t.replace("auto_apply_trivial: false", "auto_apply_trivial: true"))
        rc, out = run(root, "scripts/apply_proposal.py", p)
        self.assertEqual(rc, 0, out)
        self.assertIn("https://vite.dev/test-source", open(os.path.join(root, "data/skills/frontend/vite.md"), encoding="utf-8").read())
        self.assertIn("maturity: 采用", open(os.path.join(root, "data/skills/frontend/tailwind-css-v4.md"), encoding="utf-8").read())

    def test_approve_reject_git_tag_and_rollback(self):
        root, p = self.setup(True)
        rc, out = run(root, "scripts/apply_proposal.py", p, "--approve", "T-02,T-04", "--reject", "T-01")
        self.assertEqual(rc, 0, out)
        tw = open(os.path.join(root, "data/skills/frontend/tailwind-css-v4.md"), encoding="utf-8").read()
        self.assertIn("maturity: 试用", tw)
        self.assertIn("提案 T-02", tw)
        pg = open(os.path.join(root, "data/skills/backend/postgresql.md"), encoding="utf-8").read()
        self.assertIn("唯一约束用 (user_id, sign_date)", pg)
        self.assertNotIn("https://vite.dev/test-source", open(os.path.join(root, "data/skills/frontend/vite.md"), encoding="utf-8").read())
        self.assertIn("T-01", open(os.path.join(root, "proposals", "rejected.jsonl"), encoding="utf-8").read())
        tags = subprocess.run(["git", "-C", root, "tag"], capture_output=True, text=True).stdout.split()
        self.assertEqual(len([t for t in tags if t.startswith("skills-")]), 1)
        self.assertEqual(subprocess.run(["git", "-C", root, "remote"], capture_output=True, text=True).stdout.strip(), "")
        # 再提一次重复经验：合并、不重复写入
        open(p, "a", encoding="utf-8").write(PROPOSAL.split("### T-04")[1].replace(" 经验：签到跨天", "### T-05 重复经验", 1))
        p2 = os.path.join(root, "proposals", "dup.md")
        open(p2, "w", encoding="utf-8").write("### T-05 重复\n" + "```yaml" + PROPOSAL.split("```yaml")[4])
        rc, out = run(root, "scripts/apply_proposal.py", p2, "--approve", "all", "--no-snapshot")
        self.assertIn("已合并", out)
        self.assertEqual(open(os.path.join(root, "data/skills/backend/postgresql.md"), encoding="utf-8").read().count("sign_date"), 1)
        # 回滚：先打一个初始快照再应用，回到上一个标签
        rc, out = run(root, "scripts/rollback.py", "--list")
        self.assertIn("skills-", out)

    def test_regression_refused(self):
        root, p = self.setup(False)
        before = open(os.path.join(root, "data/skills/client/jetpack-compose.md"), encoding="utf-8").read()
        rc, out = run(root, "scripts/apply_proposal.py", p, "--approve", "T-03")
        self.assertNotEqual(rc, 0)
        self.assertIn("回归退化，拒绝更新", out)
        self.assertIn("CL-1", out)
        self.assertEqual(before, open(os.path.join(root, "data/skills/client/jetpack-compose.md"), encoding="utf-8").read())

    def test_rollback_non_git(self):
        root, p = self.setup(False)
        rc, out = run(root, "scripts/rollback.py", "--snapshot", "初始")
        self.assertIn("skills-", out)
        rc, out = run(root, "scripts/apply_proposal.py", p, "--approve", "T-02")
        self.assertEqual(rc, 0, out)
        self.assertTrue(os.path.isdir(os.path.join(root, "snapshots")))
        rc, out = run(root, "scripts/rollback.py")
        self.assertEqual(rc, 0, out)
        self.assertIn("validate 通过", out)
        self.assertIn("maturity: 采用", open(os.path.join(root, "data/skills/frontend/tailwind-css-v4.md"), encoding="utf-8").read())

    def test_rollback_git(self):
        root, p = self.setup(True)
        run(root, "scripts/rollback.py", "--snapshot", "初始")
        rc, out = run(root, "scripts/apply_proposal.py", p, "--approve", "T-02")
        self.assertEqual(rc, 0, out)
        rc, out = run(root, "scripts/rollback.py")
        self.assertEqual(rc, 0, out)
        self.assertIn("maturity: 采用", open(os.path.join(root, "data/skills/frontend/tailwind-css-v4.md"), encoding="utf-8").read())

    def test_new_role_overlay(self):
        root, _ = self.setup(False)
        p = os.path.join(root, "proposals", "role.md")
        open(p, "w", encoding="utf-8").write("""### R-01 提示词运营并入 AI 应用
```yaml
action: merge_role
role: X-01
role_def: {id: X-01, family: I, name: 提示词运营, positioning: 维护提示词库, terms: [{group: AI 协同, terms: [提示词库]}], tools: []}
target: ai-app-engineer
evidence: [https://example.com/a]
published: 2026-11-01
reason: 和 AI 应用工程师职责重叠高
status: 待拍板
```
""")
        rc, out = run(root, "scripts/apply_proposal.py", p, "--approve", "all", "--no-snapshot")
        self.assertEqual(rc, 0, out)
        rc, out = run(root, "scripts/who.py", "提示词运营")
        self.assertIn("AI 应用 / Agent 工程师", out)
        self.assertIn("X-01 提示词运营", open(os.path.join(root, "agents", "ai-app-engineer.md"), encoding="utf-8").read())


class Install(unittest.TestCase):
    def test_install_update_uninstall(self):
        root = copy_repo()
        proj = tempfile.mkdtemp()
        os.makedirs(os.path.join(proj, ".claude", "agents"))
        settings = {"permissions": {"allow": ["Bash(ls:*)"]}, "hooks": {"PreToolUse": [{"matcher": "Bash", "hooks": [{"type": "command", "command": "echo mine"}]}]}}
        json.dump(settings, open(os.path.join(proj, ".claude", "settings.json"), "w"))
        open(os.path.join(proj, ".claude", "agents", "architect.md"), "w").write("my own architect\n")
        open(os.path.join(proj, ".claude", "agents", "mine.md"), "w").write("---\nname: mine\n---\n")
        sh = os.path.join(root, "install.sh")
        r = subprocess.run(["bash", sh, "--project", proj, "--mcp", "none"], capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        agents = [f for f in os.listdir(os.path.join(proj, ".claude", "agents")) if f.endswith(".md")]
        self.assertEqual(len(agents), 17)  # 16 + 用户自己的 mine.md
        self.assertTrue(any(f.startswith("architect.md.bak-") for f in os.listdir(os.path.join(proj, ".claude", "agents"))))
        s = json.load(open(os.path.join(proj, ".claude", "settings.json")))
        self.assertEqual(s["permissions"], settings["permissions"])
        self.assertIn("echo mine", json.dumps(s))
        self.assertTrue(os.path.exists(os.path.join(proj, ".claude", "settings.json.bak")))
        self.assertEqual(json.load(open(os.path.join(proj, ".claude", "settings.json.bak"))), settings)
        # --update：改一个技能包，只替换变化的文件并打印 旧 → 新
        sp = os.path.join(root, "data", "skills", "frontend", "vite.md")
        t = open(sp, encoding="utf-8").read()
        open(sp, "w", encoding="utf-8").write(t.replace("version: 1.0.0", "version: 1.0.1"))
        r = subprocess.run(["bash", sh, "--update", "--project", proj, "--mcp", "none"], capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("更新 skills/vite/SKILL.md：v1.0.0", r.stdout)
        self.assertIn("→ v1.0.1", r.stdout)
        self.assertNotIn("更新 agents/qa-expert.md", r.stdout)
        # --uninstall：只删本套件
        r = subprocess.run(["bash", sh, "--uninstall", "--project", proj], capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        left = os.listdir(os.path.join(proj, ".claude", "agents"))
        self.assertIn("mine.md", left)
        self.assertNotIn("qa-expert.md", left)
        s = json.load(open(os.path.join(proj, ".claude", "settings.json")))
        self.assertEqual(s, settings)


class KbHost(unittest.TestCase):
    """角色团接入知识库：REQ-005 / 013 / 018 / 019。"""

    def test_guard_kb_session_ask_becomes_deny(self):
        def g(evt, env=None):
            rc, out = run(REPO, "scripts/hooks/guard_hook.py", stdin=json.dumps(evt), env=env)
            return json.loads(out)["hookSpecificOutput"] if out.strip() else None
        push = {"tool_name": "Bash", "tool_input": {"command": "git push origin main"}}
        for cmd in ("git push origin main", "rm -rf /opt/build", "npm publish", "kubectl apply -f x.yaml"):
            d = g({"tool_name": "Bash", "tool_input": {"command": cmd}}, {"KB_SESSION": "steward"})
            self.assertEqual(d["permissionDecision"], "deny", cmd)
            self.assertIn("无人值守：用 kb_ask 请用户确认，由用户执行", d["permissionDecisionReason"])
        self.assertEqual(g(push)["permissionDecision"], "ask")                       # 不在知识库会话：照旧 ask
        self.assertEqual(g(push, {"KB_SESSION": "  "})["permissionDecision"], "ask")  # 空值不算
        self.assertIsNone(g({"tool_name": "Bash", "tool_input": {"command": "npm test"}}, {"KB_SESSION": "flow"}))
        d = g({"tool_name": "Write", "tool_input": {"file_path": os.path.join(REPO, "data/skills/frontend/vite.md")}}, {"KB_SESSION": "flow"})
        self.assertEqual(d["permissionDecision"], "deny")                           # 原有 deny 不变
        self.assertNotIn("无人值守", d["permissionDecisionReason"])

    def test_guard_kb_session_command_position_only(self):
        """审查第 1 轮：KB_SESSION 下硬拒只看命令名位置，参数 / 引号 / here-doc 里的字样不误伤。"""
        cwd = "/opt/kb-test-proj"   # 会话工作目录（不在临时目录里；hook 不要求它真实存在）

        def g(cmd):
            evt = {"tool_name": "Bash", "tool_input": {"command": cmd}, "cwd": cwd}
            rc, out = run(REPO, "scripts/hooks/guard_hook.py", stdin=json.dumps(evt), env={"KB_SESSION": "dev"})
            return json.loads(out)["hookSpecificOutput"]["permissionDecision"] if out.strip() else None
        allowed = [
            'grep -rnE "git (push|reset --hard|clean)|rm -rf" kblib',
            "grep -rn 'rm -rf' scripts",
            'git commit -m "fix: rm stale git push note; deploy.sh docs"',
            "git commit -q -F - <<'EOF'\nfix: drop rm -rf and git push from docs\nEOF\ngit log -1",
            "python3 - <<'EOF'\nimport os\nos.system('npm publish')\nEOF",
            'echo "git push origin main"',
            "git rm old.txt", "rm -rf build", "rm -f /tmp/x.log", "cd sub && rm a.txt",
            "find . -name '*.pyc' -delete", "T=$(mktemp -d); cd $T && rm -rf $T",
            'rm -rf "out dir/cache"', "cat deploy.sh", "grep -n push_notification src/a.kt",
        ]
        for cmd in allowed:
            self.assertIsNone(g(cmd), cmd)
        denied = [
            "git push origin main", "git -C /x -c a=b push", "git status; git push", "FOO=1 git push",
            "git reset --hard HEAD~1", "git clean -fd", "git branch -D feat", "git checkout -- .",
            "rm -rf /Users/someone/else", "rm -rf ..", "rm -rf .", "rm -rf ~/x", "rm -rf .git", "rm -rf $UNKNOWN/x",
            'rm -rf "$(cat /tmp/list)"', "echo x | xargs rm -rf /etc", "kubectl apply -f k.yaml", "npm publish",
            "./deploy.sh prod", "mysql -e 'DROP TABLE t'", "curl -X POST https://api.jpush.cn/v3/push -d '{}'",
            "cat > /tmp/m.txt <<EOF\nhello\nEOF\ngit push",
        ]
        for cmd in denied:
            self.assertEqual(g(cmd), "deny", cmd)

    def test_guard_replay_tool(self):
        d = tempfile.mkdtemp()
        dev = os.path.join(d, "期", "x", "开发会话")
        os.makedirs(dev)
        lines = [{"type": "system", "subtype": "init", "cwd": d}]
        for c in ('grep -rn "git push" .', "rm -rf build", "git push origin main"):
            lines.append({"type": "assistant", "message": {"content": [{"type": "tool_use", "name": "Bash", "input": {"command": c}}]}})
        open(os.path.join(dev, "20261116-100000.jsonl"), "w", encoding="utf-8").write("\n".join(json.dumps(x) for x in lines))
        rc, out = run(REPO, "scripts/hooks/replay_guard.py", d, "--json")
        st = json.loads(out)["dev"]
        self.assertEqual((st["sessions"], st["commands"], st["deny"], st["deny_old"]), (1, 3, 1, 3))
        self.assertEqual(st["denied"][0]["label"], "git push")

    def test_refresh_check_silent_in_kb_session(self):
        root = copy_repo()
        env = {"WORKER_AGENT_TODAY": "2027-03-01", "KB_SESSION": "dev"}
        run(root, "scripts/rollback.py", "--snapshot", "init", env={"WORKER_AGENT_TODAY": "2026-11-20"})
        rc, out = run(root, "scripts/refresh_check.py", "--hook", env=env)
        self.assertEqual((rc, out.strip()), (0, ""))
        rc, out = run(root, "scripts/refresh_check.py", "--hook", env={"WORKER_AGENT_TODAY": "2027-03-01"})
        self.assertIn("additionalContext", out)                 # 当天的提醒没被知识库会话占掉

    def test_kb_scenes_top_level_fields_and_lite_list(self):
        root = copy_repo()
        p = os.path.join(root, "config", "kb_scenes.json")
        d = json.load(open(p, encoding="utf-8"))
        d["档位"] = {"精简": "tiny"}
        d["每期上限默认"] = "30"
        d["自动场景模型"] = "gpt"
        d["产物目录"] = "../outside"
        del d["场景"]["开发"]["每确认点上限"]
        d["场景"]["开发·端"]["每确认点上限"] = 9
        open(p, "w", encoding="utf-8").write(json.dumps(d, ensure_ascii=False))
        tp = os.path.join(root, "config", "team.yaml")
        open(tp, "w", encoding="utf-8").write(open(tp, encoding="utf-8").read().replace(
            "    roles: [product-manager, architect, frontend-engineer, client-engineer, backend-engineer, qa-expert]", "    roles: all", 1))
        rc, out = run(root, "scripts/validate.py")
        self.assertNotEqual(rc, 0)
        for msg in ("档位 必须是", "每期上限默认 必须是 0～200 的整数", "自动场景模型 不合法", "产物目录 必须是",
                    "场景「开发」 缺少字段 每确认点上限", "场景「开发·端」 每确认点上限 9 大于整轮上限 6",
                    "tiers.lite.roles 必须是角色列表"):
            self.assertIn(msg, out)

    def test_build_reads_artifact_dir_from_scenes(self):
        root = copy_repo()
        p = os.path.join(root, "config", "kb_scenes.json")
        d = json.load(open(p, encoding="utf-8"))
        d["产物目录"] = "其他资料/专家产物"
        open(p, "w", encoding="utf-8").write(json.dumps(d, ensure_ascii=False))
        run(root, "scripts/build.py", "--mcp", "none")
        t = open(os.path.join(root, "agents", "qa-expert.md"), encoding="utf-8").read()
        self.assertIn("其他产物写 其他资料/专家产物/<阶段序号>-<产物名>.md", t)
        self.assertNotIn("其他资料/角色产物", t)

    def test_kb_scenes_valid_and_bad_role_fails(self):
        scenes = json.load(open(os.path.join(REPO, "config", "kb_scenes.json"), encoding="utf-8"))
        limits = {k: v["上限"] for k, v in scenes["场景"].items()}
        self.assertEqual(limits["方案"], 4)
        self.assertEqual(limits["管家"], 1)
        self.assertEqual(limits["发布"], 1)
        self.assertEqual(scenes["场景"]["发布"]["精简"]["主导"], "architect")
        self.assertEqual(scenes["场景"]["发布"]["标准"]["主导"], "sre-security")
        root = copy_repo()
        run(root, "scripts/build.py", "--mcp", "none")
        rc, out = run(root, "scripts/validate.py")
        self.assertEqual(rc, 0, out)
        p = os.path.join(root, "config", "kb_scenes.json")
        t = open(p, encoding="utf-8").read()
        open(p, "w", encoding="utf-8").write(t.replace('"主导": "sre-security"', '"主导": "devops-guru"')
                                             .replace('"精简": {"主导": "architect", "参与": []}', '"精简": {"主导": "ux-designer", "参与": []}'))
        rc, out = run(root, "scripts/validate.py")
        self.assertNotEqual(rc, 0)
        self.assertIn("引用了不存在的角色：devops-guru", out)
        self.assertIn("精简 用了 team.yaml tiers.lite 之外的角色：ux-designer", out)
        # 版本、缺场景、缺档位名单、只读安全角色含工程师（变更 CR-001）
        d = json.loads(t)
        d["版本"] = 2
        del d["场景"]["需求体检"]
        del d["场景"]["管家"]["精简"]
        d["只读安全角色"].append("backend-engineer")
        open(p, "w", encoding="utf-8").write(json.dumps(d, ensure_ascii=False))
        rc, out = run(root, "scripts/validate.py")
        self.assertNotEqual(rc, 0)
        for msg in ("版本 必须是 1", "缺少场景：需求体检", "场景「管家」 缺少字段 精简", "场景「管家」.精简 缺少主导角色",
                    "只读安全角色 不能含工程师", "backend-engineer"):
            self.assertIn(msg, out)
        open(p, "w", encoding="utf-8").write("{bad json")
        rc, out = run(root, "scripts/validate.py")
        self.assertIn("JSON 解析失败", out)

    def test_build_renders_kb_host_mode(self):
        root = copy_repo()
        for mcp in ("none", "kb"):
            run(root, "scripts/build.py", "--mcp", mcp)
            for slug in ("product-manager", "client-engineer"):
                t = open(os.path.join(root, "agents", slug + ".md"), encoding="utf-8").read()
                self.assertIn("知识库宿主模式", t)
                self.assertIn("不写 workspace/、不用 Write", t)
                self.assertIn("不要 run_in_background", t)
        t = open(os.path.join(root, "agents", "product-manager.md"), encoding="utf-8").read()
        self.assertIn("建议来自：产品经理", t)
        # 删掉宿主模式段落 → validate 报错
        p = os.path.join(root, "agents", "qa-expert.md")
        t = open(p, encoding="utf-8").read()
        open(p, "w", encoding="utf-8").write(t.replace("知识库宿主模式", "x"))
        rc, out = run(root, "scripts/validate.py")
        self.assertNotEqual(rc, 0)
        self.assertIn("缺少「知识库宿主模式」段落", out)

    def test_install_copies_scenes_and_prints_status(self):
        root = copy_repo()
        proj = tempfile.mkdtemp()
        sh = os.path.join(root, "install.sh")
        r = subprocess.run(["bash", sh, "--project", proj, "--mcp", "kb", "--no-hooks"], capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        inst = os.path.join(proj, ".claude", "role-agents", "config", "kb_scenes.json")
        self.assertEqual(open(inst, "rb").read(), open(os.path.join(root, "config", "kb_scenes.json"), "rb").read())
        self.assertIn("知识库角色团：可用（kb MCP ✅，agent 16/16", r.stdout)
        r = subprocess.run(["bash", sh, "--uninstall", "--project", proj], capture_output=True, text=True)
        proj2 = tempfile.mkdtemp()
        r = subprocess.run(["bash", sh, "--project", proj2, "--mcp", "none", "--no-hooks"], capture_output=True, text=True)
        self.assertIn("知识库角色团：不可用（kb MCP ❌ 未检测到", r.stdout)


class Deliverables(unittest.TestCase):
    def test_template_validation(self):
        d = tempfile.mkdtemp()
        p = os.path.join(d, "02-PRD.md")
        open(p, "w", encoding="utf-8").write(open(os.path.join(REPO, "templates", "deliverables", "03-prd.md"), encoding="utf-8").read())
        rc, out = run(REPO, "scripts/validate.py", "--deliverable", p)
        self.assertNotEqual(rc, 0)
        self.assertIn("必填节「AI 机会评估」为空", out)

    def test_example_passes(self):
        ws = os.path.join(REPO, "examples", "checkin-points", "workspace", "checkin-points")
        files = [os.path.join(ws, f) for f in sorted(os.listdir(ws))
                 if re.match(r"^\d\d-", f) and "<!-- template:" in open(os.path.join(ws, f), encoding="utf-8").read(300)]
        self.assertGreaterEqual(len(files), 5)
        rc, out = run(REPO, "scripts/validate.py", "--deliverable", *files)
        self.assertEqual(rc, 0, out)


if __name__ == "__main__":
    unittest.main()


NEW_ROLE = """# 新角色提案
### R-10 新增专家：提示词运营
```yaml
action: new_role
slug: prompt-ops
name: 提示词运营专家
kind: traditional
model: sonnet
evidence: [https://example.com/prompt-ops-jd]
published: 2026-11-01
reason: 提示词库运营在用户场景里常用，和现有专家职责重叠低于一半
mount_skills: [structured-outputs, prompt-caching, llm-eval-pipeline, ai-feature-metrics, agent-skills]
status: 待拍板
```
```json
{
  "retire_or_merge": {"slug": "ai-infra-mlops", "replacement": "ai-app-engineer", "reason": "自部署推理需求少，并入 AI 应用 / Agent 工程师"},
  "role_defs": [{"id": "X-10", "family": "I", "name": "提示词运营", "positioning": "维护提示词库和提示词评审",
                 "terms": [{"group": "AI 协同", "terms": ["提示词库", "提示词评审"]}], "tools": []}],
  "profile": {
    "tools_profile": "doc", "lead_stages": [9], "stages": [6, 9],
    "summary": "维护业务提示词库，组织提示词评审和版本管理。",
    "duties": ["维护提示词库", "组织提示词评审"], "outputs": [{"name": "提示词库变更说明", "template": "11-dashboard-retro"}],
    "upstream": ["ai-app-engineer"], "downstream": ["ai-eval-compliance"],
    "standards": ["每条提示词有版本和负责人"], "boundaries": [{"task": "写代码", "go_to": "ai-app-engineer"}],
    "tasks": ["提示词库运营", "提示词评审", "提示词版本管理"], "terms": ["提示词库", "提示词评审", "提示词版本"]
  },
  "routing_cases": [
    {"task": "整理客服机器人的提示词库，做一轮提示词评审", "expect": "prompt-ops"},
    {"task": "给提示词库做提示词版本管理", "expect": "prompt-ops"}
  ],
  "skill_cases": [
    {"id": "PO-1", "scenario": "提示词输出给程序用", "expect_adopt": ["structured-outputs"]},
    {"id": "PO-2", "scenario": "提示词改动先跑评测", "expect_adopt": ["llm-eval-pipeline"]},
    {"id": "PO-3", "scenario": "边界", "agent_contains": ["这不归我管"]}
  ]
}
```
"""


class NewRole(unittest.TestCase):
    def test_new_role_with_retire_applies_and_validates(self):
        root = copy_repo(git=True)
        p = os.path.join(root, "proposals", "2026-11-20-roles.md")
        open(p, "w", encoding="utf-8").write(NEW_ROLE)
        rc, out = run(root, "scripts/apply_proposal.py", p, "--check")
        self.assertEqual(rc, 0, out)
        rc, out = run(root, "scripts/apply_proposal.py", p, "--approve", "all")
        self.assertEqual(rc, 0, out)
        agents = os.path.join(root, "agents")
        self.assertTrue(os.path.exists(os.path.join(agents, "prompt-ops.md")))
        self.assertEqual(len(os.listdir(agents)), 17)              # 15 个专家（含已下线）+ 总控 + 情报员
        self.assertIn("已下线", fm(os.path.join(agents, "ai-infra-mlops.md"))["description"])
        rc, out = run(root, "scripts/validate.py")
        self.assertEqual(rc, 0, out)
        rc, out = run(root, "scripts/who.py", "提示词运营")
        self.assertIn("提示词运营专家", out)
        rc, out = run(root, "scripts/who.py", "模型运维工程师")
        self.assertIn("AI 应用 / Agent 工程师", out)               # 下线专家的原始岗位转给替代角色
        self.assertIn("prompt-ops", open(os.path.join(root, "workflow", "stages.md"), encoding="utf-8").read())
        self.assertIn("prompt-ops", open(os.path.join(root, "agents", "orchestrator.md"), encoding="utf-8").read())
        tags = subprocess.run(["git", "-C", root, "tag"], capture_output=True, text=True).stdout.split()
        self.assertTrue(any(t.startswith("skills-") for t in tags))
        # 新专家的调用会被 hook 记录
        e = json.dumps({"hook_event_name": "PreToolUse", "tool_name": "Agent", "cwd": "/p", "tool_input": {"subagent_type": "prompt-ops"}})
        run(root, "scripts/hooks/usage_hook.py", stdin=e)
        self.assertIn("prompt-ops", open(os.path.join(root, "usage", "usage.jsonl"), encoding="utf-8").read())

    def test_new_role_incomplete_rejected_by_check(self):
        root = copy_repo()
        p = os.path.join(root, "proposals", "bad.md")
        bad = NEW_ROLE.replace('"retire_or_merge": {"slug": "ai-infra-mlops", "replacement": "ai-app-engineer", "reason": "x"},', "")
        bad = re.sub(r'"retire_or_merge": \{[^}]*\},', "", bad).replace("mount_skills: [structured-outputs, prompt-caching, llm-eval-pipeline, ai-feature-metrics, agent-skills]", "mount_skills: [structured-outputs]")
        open(p, "w", encoding="utf-8").write(bad)
        rc, out = run(root, "scripts/apply_proposal.py", p, "--check")
        self.assertNotEqual(rc, 0)
        self.assertIn("至少挂 5 个技能", out)
        self.assertIn("retire_or_merge", out)


class Round1Fixes(unittest.TestCase):
    def test_guard_bash_protected(self):
        def g(evt):
            rc, out = run(REPO, "scripts/hooks/guard_hook.py", stdin=json.dumps(evt))
            return json.loads(out)["hookSpecificOutput"]["permissionDecision"] if out.strip() else None
        R = REPO
        self.assertEqual(g({"tool_name": "Bash", "cwd": R, "tool_input": {"command": "sed -i '' 's/a/b/' data/skills/frontend/vite.md"}}), "deny")
        self.assertEqual(g({"tool_name": "Bash", "cwd": "/p", "tool_input": {"command": "echo x > %s/agents/qa-expert.md" % R}}), "deny")
        self.assertEqual(g({"tool_name": "Bash", "cwd": "/p", "agent_type": "backend-engineer", "tool_input": {"command": "cp a.md .claude/agents/architect.md"}}), "deny")
        self.assertEqual(g({"tool_name": "Bash", "cwd": "/p", "agent_type": "backend-engineer", "tool_input": {"command": "python3 -c \"open('.claude/skills/vite/SKILL.md','w')\""}}), "deny")
        self.assertEqual(g({"tool_name": "Bash", "cwd": "/p", "agent_type": "architect", "tool_input": {"command": "python3 %s/scripts/apply_proposal.py x.md --approve all" % R}}), "deny")
        self.assertIsNone(g({"tool_name": "Bash", "cwd": R, "tool_input": {"command": "grep -r Vite data/skills"}}))
        self.assertIsNone(g({"tool_name": "Bash", "cwd": R, "tool_input": {"command": "cat data/skills/frontend/vite.md 2>/dev/null"}}))
        self.assertIsNone(g({"tool_name": "Bash", "cwd": "/p", "tool_input": {"command": "python3 %s/scripts/apply_proposal.py x.md --approve 1" % R}}))

    def test_rounded_baseline_not_regression(self):
        root = copy_repo()
        for rel, key in (("scripts/eval_routing/last_result.json", "hit_rate"), ("scripts/eval_skills/last_result.json", "pass_rate")):
            p = os.path.join(root, rel)
            d = json.load(open(p, encoding="utf-8"))
            d["results"][0]["ok"] = False      # 基线里第 1 条失败
            d[key] = round((len(d["results"]) - 1) / len(d["results"]), 4)
            json.dump(d, open(p, "w", encoding="utf-8"), ensure_ascii=False)
        # 让第 1 条真的失败：把对应用例改成不可能命中
        rp = os.path.join(root, "scripts", "eval_routing", "cases.json")
        rc_ = json.load(open(rp, encoding="utf-8"))
        first_r = json.load(open(os.path.join(root, "scripts/eval_routing/last_result.json"), encoding="utf-8"))["results"][0]["task"]
        for c in rc_["cases"]:
            if c["task"] == first_r:
                c["expect"], c["also_ok"] = "model-algorithm-engineer", []
        json.dump(rc_, open(rp, "w", encoding="utf-8"), ensure_ascii=False)
        sp = os.path.join(root, "scripts", "eval_skills", "cases.json")
        sc = json.load(open(sp, encoding="utf-8"))
        sc["cases"][0]["expect_adopt"] = ["posthog"]
        json.dump(sc, open(sp, "w", encoding="utf-8"), ensure_ascii=False)
        proj = tempfile.mkdtemp()
        sh = os.path.join(root, "install.sh")
        r = subprocess.run(["bash", sh, "--update", "--project", proj, "--mcp", "none"], capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertNotIn("拒绝", r.stdout)

    def test_settings_bak_keeps_original(self):
        root = copy_repo()
        proj = tempfile.mkdtemp()
        os.makedirs(os.path.join(proj, ".claude"))
        orig = {"permissions": {"allow": ["Bash(ls:*)"]}}
        json.dump(orig, open(os.path.join(proj, ".claude", "settings.json"), "w"))
        sh = os.path.join(root, "install.sh")
        for _ in range(2):
            subprocess.run(["bash", sh, "--project", proj, "--mcp", "none"], capture_output=True, text=True, check=True)
        self.assertEqual(json.load(open(os.path.join(proj, ".claude", "settings.json.bak"))), orig)
        subprocess.run(["bash", sh, "--uninstall", "--project", proj], capture_output=True, text=True, check=True)
        self.assertEqual(json.load(open(os.path.join(proj, ".claude", "settings.json.bak"))), orig)
        self.assertEqual(json.load(open(os.path.join(proj, ".claude", "settings.json"))), orig)

    def test_usage_report_no_data(self):
        root = copy_repo()
        os.makedirs(os.path.join(root, "state"), exist_ok=True)
        json.dump({"projects": []}, open(os.path.join(root, "state", "projects.json"), "w"))
        rep = json.loads(run(root, "scripts/usage_report.py", "--json")[1])
        names = [r["name"] for r in rep["roles"]]
        self.assertEqual(names, sorted(names))
        self.assertIn("hook 没有任何角色调用记录", rep["notice"])

    def test_refresh_uses_proposal_date_and_mark(self):
        root = copy_repo()
        env = {"WORKER_AGENT_TODAY": "2026-12-30"}
        open(os.path.join(root, "proposals", "2026-12-20-frontend.md"), "w").write("<!-- source: tech-scout 2026-12-20 -->\n# x\n")
        rc, out = run(root, "scripts/refresh_check.py", env=env)
        self.assertEqual(out.strip(), "")       # 10 天前侦察过（情报员提案文件日期），不提醒
        rc, out = run(root, "scripts/refresh_check.py", "--mark-refreshed", env=env)
        self.assertIn("2026-12-30", out)


class Round2Fixes(unittest.TestCase):
    def test_new_role_replaces_retired_with_itself(self):
        for rep in ('"replacement": "prompt-ops", ', ""):      # 显式写新专家自己 / 不写（默认新专家自己）
            root = copy_repo()
            prop = NEW_ROLE.replace('"replacement": "ai-app-engineer", ', rep)
            p = os.path.join(root, "proposals", "r.md")
            open(p, "w", encoding="utf-8").write(prop)
            self.assertEqual(run(root, "scripts/apply_proposal.py", p, "--check")[0], 0)
            rc, out = run(root, "scripts/apply_proposal.py", p, "--approve", "all", "--no-snapshot")
            self.assertNotIn("不存在", out)
            # 用 prompt-ops 顶替推理部署会让 vLLM 等用例选错角色：回归门禁按逐条用例拒绝，这是预期行为
            self.assertIn("期望 prompt-ops", out)
            # 绕过门禁直接调用 apply_new_role，检查落地结果
            code = ("import sys,json;sys.path.insert(0,'scripts');import apply_proposal as a;"
                    "t,items=a.parse('proposals/r.md');a.apply_new_role(items[0]['data'],'R-10',[]);"
                    "print(json.dumps(json.load(open('data/roles_overlay.json'))['retire']))")
            rc, out = run(root, "-c", code)
            self.assertEqual(rc, 0, out)
            self.assertEqual(json.loads(out.strip().splitlines()[-1])["ai-infra-mlops"]["replacement"], "prompt-ops")
            rc, out = run(root, "scripts/build.py", "--mcp", "none", "--quiet")
            d = fm(os.path.join(root, "agents", "ai-infra-mlops.md"))["description"]
            self.assertIn("改找 提示词运营专家", d)
            self.assertIn("原来合并的原始岗位已转给", d)
            self.assertNotIn("合并了原始岗位：——", d)

    def test_retire_keeps_also(self):
        root = copy_repo()
        p = os.path.join(root, "proposals", "ret.md")
        open(p, "w", encoding="utf-8").write("""### R-20 下线前端工程师
```yaml
action: retire_role
slug: frontend-engineer
replacement: backend-engineer
evidence: [https://example.com/x]
published: 2026-11-01
reason: 测试 also 保留
status: 待拍板
```
""")
        rc, out = run(root, "scripts/apply_proposal.py", p, "--approve", "all", "--no-snapshot")
        # 下线前端会让前端用例改由后端承担；不管回归结果如何，映射逻辑单独校验
        sys.path.insert(0, os.path.join(root, "scripts"))
        code = ("import sys,json;sys.path.insert(0,'scripts');import apply_proposal as a;"
                "a.retire('frontend-engineer','backend-engineer','t','R-20',[]);"
                "import json;print(json.dumps(json.load(open('data/roles_overlay.json'))['merge']))")
        rc, out = run(root, "-c", code)
        merge = json.loads(out.strip().splitlines()[-1])
        self.assertEqual(merge["E-01"]["target"], "backend-engineer")
        self.assertEqual(merge["E-05"]["target"], "backend-engineer")
        self.assertNotIn("frontend-engineer", merge["E-05"].get("also", []))
        self.assertNotIn("also", merge["E-05"])       # also 指向被下线角色→替代角色，与 target 相同则去掉

    def test_guard_cd_and_writer_scope(self):
        def g(cmd, cwd="/p", agent="backend-engineer"):
            evt = {"tool_name": "Bash", "cwd": cwd, "agent_type": agent, "tool_input": {"command": cmd}}
            rc, out = run(REPO, "scripts/hooks/guard_hook.py", stdin=json.dumps(evt))
            return json.loads(out)["hookSpecificOutput"]["permissionDecision"] if out.strip() else None
        R = REPO
        self.assertEqual(g("cd %s && echo x >> data/skills/frontend/vite.md" % R), "deny")
        self.assertEqual(g("cd %s/data/skills/frontend && printf x > vite.md" % R), "deny")
        self.assertEqual(g("cd %s && python3 scripts/build.py" % R), "deny")
        self.assertIsNone(g("python3 build.py --release"))
        self.assertIsNone(g("./install.sh"))
        self.assertIsNone(g("python tools/extract.py data.json"))
        self.assertIsNone(g("cd %s && python3 scripts/validate.py" % R))
        for path in ("skills/vite/SKILL.md", "local/skills/x/y.md"):
            evt = {"tool_name": "Write", "cwd": "/p", "tool_input": {"file_path": os.path.join(R, path)}}
            out = run(REPO, "scripts/hooks/guard_hook.py", stdin=json.dumps(evt))[1]
            self.assertEqual(json.loads(out)["hookSpecificOutput"]["permissionDecision"], "deny")

    def test_refresh_ignores_unmarked_and_future(self):
        root = copy_repo()
        env = {"WORKER_AGENT_TODAY": "2027-01-30"}
        run(root, "scripts/rollback.py", "--snapshot", "init", env={"WORKER_AGENT_TODAY": "2026-11-20"})
        open(os.path.join(root, "proposals", "2027-01-25-roles.md"), "w").write("# 手写提案\n")
        open(os.path.join(root, "proposals", "2099-01-01-frontend.md"), "w").write("<!-- source: tech-scout 2099-01-01 -->\n")
        rc, out = run(root, "scripts/refresh_check.py", env=env)
        self.assertIn("距上次 /skills-refresh 已", out)
