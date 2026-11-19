#!/usr/bin/env python3
"""技能定期自动学习、自动更新（skills_refresh_mode=auto）。用假的 claude 命令写提案，端到端验证，不联网、不调模型。

运行：python3 -m unittest tests.test_auto_refresh -v
"""
import json
import os
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from test_suite import copy_repo, run, set_refresh_mode  # noqa: E402

TODAY = "2026-11-20"

FAKE_PROPOSAL = """<!-- source: tech-scout {day} -->
# 自动侦察测试提案
### A-01 vite 补来源
```yaml
action: add_source
skill: vite
evidence: [https://vite.dev/auto-source]
trivial: true
status: 待拍板
```
### A-02 tailwind 改为试用
```yaml
action: update_maturity
skill: tailwind-css-v4
suggested_maturity: 试用
evidence: [https://tailwindcss.com/blog/auto]
published: 2026-11-01
reason: 自动测试
status: 待拍板
```
### A-03 jetpack-compose 暂缓（回归退化，应被剔除）
```yaml
action: deprecate
skill: jetpack-compose
suggested_maturity: 暂缓
replaced_by: [android-xml-layout]
evidence: [https://developer.android.com/compose]
published: 2026-11-01
reason: 自动测试退化
status: 待拍板
```
### A-04 rxjava 废弃（大改动）
```yaml
action: deprecate
skill: rxjava
suggested_maturity: 暂缓
replaced_by: [kotlin-coroutines-flow]
evidence: [https://github.com/ReactiveX/RxJava/releases]
published: 2026-11-01
reason: 官方维护模式
status: 待拍板
```
### A-05 只有自媒体来源
```yaml
action: update_maturity
skill: vite
suggested_maturity: 试用
evidence: [https://example.com/blog]
published: 2026-11-01
status: 待核实
```
### A-06 可疑来源
```yaml
action: update_fields
skill: vite
fields: {version: 9.9.9}
evidence: [https://example.org/inject]
published: 2026-11-01
suspicious_sources: [https://example.org/inject]
status: 待拍板
```
"""

FAKE_CLAUDE = r'''
import os, sys
day = os.environ.get("WORKER_AGENT_TODAY")
assert os.environ.get("WORKER_AGENT_AUTO_REFRESH") == "1"
assert "-p" in sys.argv and "--allowedTools" in sys.argv
os.makedirs("proposals", exist_ok=True)
open(os.path.join("proposals", day + "-auto.md"), "w", encoding="utf-8").write(open(sys.argv[1], encoding="utf-8").read().replace("{day}", day))
print("写了 1 份提案，6 条")
'''


def git(root, *args):
    return subprocess.run(["git", "-C", root] + list(args), capture_output=True, text=True).stdout


class AutoRefresh(unittest.TestCase):
    def fake_cmd(self):
        d = tempfile.mkdtemp(prefix="ra-fake-claude-")
        prop = os.path.join(d, "proposal.md")
        open(prop, "w", encoding="utf-8").write(FAKE_PROPOSAL)
        script = os.path.join(d, "fake_claude.py")
        open(script, "w", encoding="utf-8").write(FAKE_CLAUDE)
        return "%s -I %s %s" % (sys.executable, script, prop)

    def read(self, root, rel):
        with open(os.path.join(root, rel), encoding="utf-8") as f:
            return f.read()

    def test_default_mode_is_auto(self):
        self.assertIn("skills_refresh_mode: auto", self.read(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config/run.yaml"))

    def test_end_to_end_auto_apply_summary_rollback(self):
        root = copy_repo(git=True)
        tw_before = self.read(root, "data/skills/frontend/tailwind-css-v4.md")
        # 用户自己在仓库里的未提交改动不能被自动更新一起提交
        open(os.path.join(root, "notes.txt"), "w").write("mine")
        with open(os.path.join(root, "README.md"), "a", encoding="utf-8") as f:
            f.write("\nuser edit\n")
        env = {"WORKER_AGENT_TODAY": TODAY, "WORKER_AGENT_CLAUDE_CMD": self.fake_cmd()}
        rc, out = run(root, "scripts/auto_refresh.py", "--status", env=env)
        self.assertIn("模式：auto", out)
        self.assertIn("到期：是", out)
        rc, out = run(root, "scripts/auto_refresh.py", "--run", env=env)
        self.assertEqual(rc, 0, out)

        # 核实过的条目自动应用；退化、待核实、可疑来源的不应用
        self.assertIn("https://vite.dev/auto-source", self.read(root, "data/skills/frontend/vite.md"))
        self.assertIn("maturity: 试用", self.read(root, "data/skills/frontend/tailwind-css-v4.md"))
        self.assertIn("kotlin-coroutines-flow", self.read(root, "data/skills/client/rxjava.md"))
        self.assertNotIn("9.9.9", self.read(root, "data/skills/frontend/vite.md"))
        self.assertIn("maturity: 采用", self.read(root, "data/skills/client/jetpack-compose.md"))
        prop = self.read(root, "proposals/%s-auto.md" % TODAY)
        self.assertIn("status: 自动应用失败", prop)
        self.assertEqual(prop.count("status: 已应用"), 3)

        # 摘要 + CHANGELOG：改了哪些技能、来源链接、大改动、回滚命令
        summary = self.read(root, "proposals/summaries/%s.md" % TODAY)
        for s in ("vite", "tailwind-css-v4", "https://tailwindcss.com/blog/auto", "大改动", "rxjava", "rollback.py --to skills-",
                  "A-03", "A-05", "待核实", "A-06", "含可疑来源", "skills_refresh_mode"):
            self.assertIn(s, summary)
        cl = self.read(root, "CHANGELOG.md")
        self.assertIn("## 技能自动更新 %s" % TODAY, cl)
        self.assertIn("⚠️ 大改动", cl)

        # 快照：基线 + 本次，各一个标签；只提交技能层，用户的改动仍未提交；不 push
        tags = [t for t in git(root, "tag").split() if t.startswith("skills-")]
        self.assertEqual(len(tags), 2, tags)
        st = git(root, "status", "--porcelain")
        self.assertIn("notes.txt", st)
        self.assertIn("README.md", st)
        self.assertNotIn("data/skills", st)
        self.assertNotIn("CHANGELOG.md", st)
        self.assertEqual(git(root, "remote").strip(), "")

        # 下次会话开头：一行摘要提示，只提示一次；本周期内不再触发
        rc, out = run(root, "scripts/refresh_check.py", "--hook", env=env)
        msg = json.loads(out)["systemMessage"]
        self.assertIn("技能已自动更新", msg)
        self.assertNotIn("hookSpecificOutput", out)          # 不注入「请用户选角色」的上下文
        rc, out = run(root, "scripts/refresh_check.py", "--hook", env=env)
        self.assertEqual(out.strip(), "")
        rc, out = run(root, "scripts/auto_refresh.py", "--run", env=env)
        self.assertIn("还没到期", out)

        # 一键回滚
        rc, out = run(root, "scripts/rollback.py", "--to", tags[0], env=env)
        self.assertEqual(rc, 0, out)
        self.assertEqual(self.read(root, "data/skills/frontend/tailwind-css-v4.md"), tw_before)

    def test_sync_only_own_installs(self):
        root = copy_repo(git=True)
        mine, other = tempfile.mkdtemp(prefix="ra-mine-"), tempfile.mkdtemp(prefix="ra-other-")
        rc, out = run(root, "scripts/install_helper.py", "--project", mine, "--no-hooks", "--mcp", "none")
        self.assertEqual(rc, 0, out)
        os.makedirs(os.path.join(other, ".claude", "role-agents"))
        with open(os.path.join(other, ".claude", "role-agents", "manifest.json"), "w") as f:
            json.dump({"home": "/somewhere/else", "files": {}}, f)
        with open(os.path.join(root, "state", "projects.json"), "w") as f:
            json.dump({"projects": [mine, other]}, f)
        env = {"WORKER_AGENT_TODAY": TODAY, "WORKER_AGENT_CLAUDE_CMD": self.fake_cmd()}
        rc, out = run(root, "scripts/auto_refresh.py", "--run", env=env)
        self.assertEqual(rc, 0, out)
        summary = self.read(root, "proposals/summaries/%s.md" % TODAY)
        self.assertIn(mine, summary)
        self.assertNotIn(other, summary)
        self.assertNotIn("~/.claude", summary)               # 真实用户级安装不是这个副本装的，不碰
        self.assertIn("成熟度：**试用**", self.read(mine, ".claude/skills/tailwind-css-v4/SKILL.md"))
        self.assertEqual(os.listdir(os.path.join(other, ".claude", "role-agents")), ["manifest.json"])

    def test_interval_and_failure_notice(self):
        root = copy_repo(git=True)
        env = {"WORKER_AGENT_TODAY": TODAY, "WORKER_AGENT_CLAUDE_CMD": "false"}
        rc, out = run(root, "scripts/auto_refresh.py", "--run", env=env)
        self.assertEqual(rc, 1)
        rc, out = run(root, "scripts/refresh_check.py", "--hook", env=env)
        self.assertIn("没有完成", json.loads(out)["systemMessage"])
        rc, out = run(root, "scripts/auto_refresh.py", "--status", env={"WORKER_AGENT_TODAY": "2026-11-26"})
        self.assertIn("到期：否", out)
        rc, out = run(root, "scripts/auto_refresh.py", "--status", env={"WORKER_AGENT_TODAY": "2026-11-27"})
        self.assertIn("到期：是", out)                       # 默认 7 天一次

    def test_ask_and_off_modes(self):
        root = copy_repo()
        set_refresh_mode(root, "off")
        rc, out = run(root, "scripts/refresh_check.py", "--hook", env={"WORKER_AGENT_TODAY": "2027-03-01"})
        self.assertEqual(out.strip(), "")
        rc, out = run(root, "scripts/auto_refresh.py", "--run", env={"WORKER_AGENT_TODAY": "2027-03-01"})
        self.assertIn("不自动更新", out)
        set_refresh_mode(root, "ask")
        rc, out = run(root, "scripts/refresh_check.py", "--hook", env={"WORKER_AGENT_TODAY": "2027-03-01"})
        self.assertIn("回复要更新的角色后才会开始", out)
        self.assertFalse(os.path.exists(os.path.join(root, "state", "auto_refresh.lock")))

    def test_kb_session_does_not_trigger(self):
        root = copy_repo()
        rc, out = run(root, "scripts/refresh_check.py", "--hook", env={"WORKER_AGENT_TODAY": TODAY, "KB_SESSION": "dev"})
        self.assertEqual(out.strip(), "")
        self.assertFalse(os.path.exists(os.path.join(root, "state", "auto_refresh.log")))


if __name__ == "__main__":
    unittest.main()
