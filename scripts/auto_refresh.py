#!/usr/bin/env python3
"""技能定期自动学习、自动更新（skills_refresh_mode=auto，默认）。

worker-agent 的本质是持续学习、完善自身技能，不设卡：到期后无人值守地
  1. 用 `claude -p` 跑技术情报员，侦察全部角色（或 run.yaml 的 skills_refresh_roles），只写 proposals/；
  2. 对新提案做格式自检，`apply_proposal.py --auto` 应用核实过的条目（版本、成熟度、新增技能、废弃、新增 / 下线角色），
     待核实、含可疑来源、格式错误、重复驳回的跳过；回归退化的条目逐条剔除；
  3. 打一个快照（git 本地提交 + 标签，不 push），写摘要 proposals/summaries/<日期>.md 并追加到 CHANGELOG.md，
     附一键回滚命令；
  4. auto_sync_projects=true 时，对已安装的项目执行 install --update。
用户事后看摘要即可，不弹确认。run.yaml 里 skills_refresh_mode 改成 ask 就恢复「提醒 + 拍板」，改成 off 完全关闭。

触发：SessionStart hook（refresh_check.py --hook）发现到期时在后台分离启动 `--run`；
也可以用 --install-schedule 装 launchd（macOS）/ crontab（其他），每天检查一次，到期才跑。

用法：
  python3 scripts/auto_refresh.py --status              # 模式、上次运行、是否到期
  python3 scripts/auto_refresh.py --run [--force]       # 到期（或 --force）就跑一次，前台等待完成
  python3 scripts/auto_refresh.py --spawn               # 到期就在后台分离启动 --run（hook 用）
  python3 scripts/auto_refresh.py --install-schedule    # 装每日检查（launchd / crontab）
  python3 scripts/auto_refresh.py --uninstall-schedule
"""
import argparse
import glob
import json
import os
import shlex
import subprocess
import sys
import tempfile
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "lib"))
import common  # noqa: E402
import snapshot  # noqa: E402

STATE = common.p("state", "auto_refresh.json")
LOCK = common.p("state", "auto_refresh.lock")
LOG = common.p("state", "auto_refresh.log")
SUMMARY_DIR = common.p("proposals", "summaries")
LABEL = "com.worker-agent.skills-refresh"
CRON_MARK = "# worker-agent skills-refresh"
SCOUT_TOOLS = "WebSearch,WebFetch,Read,Write,Grep,Glob"
LOCK_STALE_SECONDS = 6 * 3600


def cfg():
    run = common.run_config()
    mode = str(run.get("skills_refresh_mode", "auto")).strip().lower()
    return {
        "mode": mode if mode in ("auto", "ask", "off") else "auto",
        "interval": int(run.get("skills_refresh_interval_days", 7) or 7),
        "roles": run.get("skills_refresh_roles", "all") or "all",
        "command": os.environ.get("WORKER_AGENT_CLAUDE_CMD") or run.get("skills_refresh_command") or "claude",
        "timeout": int(run.get("skills_refresh_timeout", 3600) or 3600),
        "sync": bool(run.get("auto_sync_projects", True)),
    }


def load_state():
    return common.read_json(STATE, {}) or {}


def save_state(st):
    common.write_json(STATE, st)


def is_due(st=None, c=None):
    c = c or cfg()
    if c["mode"] != "auto":
        return False
    st = st if st is not None else load_state()
    last = common.parse_date(st.get("last_run") or "")
    return last is None or (common.today() - last).days >= c["interval"]


# ---------------- 锁 ----------------
def _pid_alive(pid):
    try:
        os.kill(pid, 0)
        return True
    except (OSError, ValueError, TypeError):
        return False


def locked():
    info = common.read_json(LOCK, None)
    if not info:
        return False
    if time.time() - float(info.get("time", 0)) > LOCK_STALE_SECONDS or not _pid_alive(info.get("pid")):
        return False
    return True


def acquire():
    if locked():
        return False
    common.write_json(LOCK, {"pid": os.getpid(), "time": time.time()})
    return True


def release():
    try:
        os.remove(LOCK)
    except OSError:
        pass


# ---------------- 侦察 ----------------
def scope_roles(c):
    mm = common.load_merge_map()
    active = sorted(common.active_experts(mm))
    r = c["roles"]
    if isinstance(r, str):
        r = active if r.strip() in ("all", "全部", "") else [x.strip() for x in r.replace("，", ",").split(",") if x.strip()]
    return [x for x in r if x in active] or active


def scout_instructions():
    """技术情报员的系统提示：取已渲染的 agents/tech-scout.md 正文（去掉 frontmatter）。"""
    path = common.p("agents", "tech-scout.md")
    if not os.path.exists(path):
        return ""
    return common.split_frontmatter(open(path, encoding="utf-8").read())[1]


def scout_prompt(roles):
    today = common.today().isoformat()
    return (
        "定期自动技能更新（无人值守，没有人能回答问题，不要提问）。你是技术情报员 tech-scout。\n"
        "今天 %s。侦察范围（角色 slug）：%s。信息源登记在 %s。\n"
        "按你的规则侦察 → 核实一手来源 → 写提案到 %s/%s-<领域或角色>.md（可按领域拆成多份），"
        "第一行写 `<!-- source: tech-scout %s -->`，格式严格按 %s。只写 proposals/ 目录，不改其他文件。\n"
        "这一次的提案会被自动应用（status 写「待拍板」即可；找不到一手来源的写「待核实」，不会被应用）。"
        "没有值得更新的变化时不写提案，直接说明。完成后简短列出：几条、哪些待核实、可疑来源、失败的信息源。"
        % (today, ", ".join(roles), common.p("config", "sources.yaml"), common.p("proposals"), today, today,
           common.p("proposals", "README.md"))
    )


def run_scout(c, roles, log):
    cmd = shlex.split(c["command"]) + ["-p", scout_prompt(roles), "--allowedTools", SCOUT_TOOLS,
                                       "--permission-mode", "acceptEdits"]
    sysprompt = scout_instructions()
    if sysprompt:
        cmd += ["--append-system-prompt", sysprompt]
    env = dict(os.environ, WORKER_AGENT_AUTO_REFRESH="1")
    try:
        r = subprocess.run(cmd, cwd=common.ROOT, env=env, capture_output=True, text=True, timeout=c["timeout"])
    except FileNotFoundError:
        return False, "找不到命令 %s（run.yaml 的 skills_refresh_command）" % cmd[0]
    except subprocess.TimeoutExpired:
        return False, "侦察超时（%d 秒）" % c["timeout"]
    log.write("$ %s -p …\n%s\n%s\n" % (cmd[0], r.stdout[-8000:], r.stderr[-4000:]))
    if r.returncode != 0:
        return False, "情报员退出码 %d：%s" % (r.returncode, (r.stderr or r.stdout).strip().splitlines()[-1:] or "")
    return True, (r.stdout or "").strip()


def new_proposals(since):
    out = []
    for f in sorted(glob.glob(common.p("proposals", "*.md"))):
        if os.path.getmtime(f) < since:
            continue
        with open(f, encoding="utf-8") as fh:
            if "<!-- source: tech-scout" in fh.readline():
                out.append(f)
    return out


def py(*args):
    r = subprocess.run([sys.executable] + list(args), capture_output=True, text=True, cwd=common.ROOT,
                       env=dict(os.environ, WORKER_AGENT_AUTO_REFRESH="1"))
    return r.returncode, r.stdout + r.stderr


# ---------------- 摘要 ----------------
ACTION_NAMES = {"add_skill": "新增技能", "update_maturity": "成熟度调整", "update_version": "版本更新",
                "update_fields": "元数据更新", "deprecate": "废弃（改为暂缓）", "update_as_of": "更新核实日期",
                "add_source": "补来源", "fix_typo": "修错别字", "append_lesson": "经验回流",
                "merge_role": "岗位并入专家", "new_role": "新增专家", "retire_role": "下线专家"}


def render_summary(results, tag, prev_tag, roles, scout_note, synced):
    today = common.today().isoformat()
    applied = [x for r in results for x in r["applied"]]
    skipped = [x for r in results for x in r["skipped"]]
    failed = [x for r in results for x in r["failed"]]
    big = [x for x in applied if x["big"]]
    L = ["# 技能自动更新摘要 %s" % today, "",
         "- 侦察范围：%d 个角色（%s）" % (len(roles), "、".join(roles)),
         "- 提案：%s" % ("、".join("`proposals/%s`" % r["proposal"] for r in results) or "无"),
         "- 结果：应用 %d 条（大改动 %d 条），跳过 %d 条，失败 %d 条" % (len(applied), len(big), len(skipped), len(failed))]
    if tag:
        L.append("- 快照：`%s`（本地提交 + 标签，未 push）" % tag)
    if applied:
        L.append("- 一键回滚：`python3 %s%s`" % (common.p("scripts", "rollback.py"), (" --to %s" % prev_tag) if prev_tag else ""))
    if synced:
        L.append("- 已同步到项目：%s" % "、".join(synced))
    if big:
        L += ["", "## ⚠️ 大改动（已自动应用，不满意就一键回滚）", ""]
        L += ["- **%s** %s：%s（%s）" % (ACTION_NAMES.get(x["action"], x["action"]), x["target"], x["title"], x["id"]) for x in big]
    if applied:
        L += ["", "## 改了哪些技能", "", "| 条目 | 动作 | 技能 / 角色 | 成熟度 | 来源 |", "|---|---|---|---|---|"]
        for x in applied:
            L.append("| %s %s | %s | %s | %s | %s |" % (x["id"], x["title"], ACTION_NAMES.get(x["action"], x["action"]), x["target"],
                                                  x["maturity"] or "—", " ".join(x["evidence"]) or "—"))
    if skipped or failed:
        L += ["", "## 没有应用的条目", ""]
        L += ["- %s %s：跳过（%s）" % (x["id"], x["title"], x["why"]) for x in skipped]
        L += ["- %s %s：失败（%s）" % (x["id"], x["title"], x["why"]) for x in failed]
    if scout_note:
        L += ["", "## 情报员说明", "", scout_note.strip()[:3000]]
    L += ["", "关闭自动更新或改回「需拍板」：把 `config/run.yaml` 的 `skills_refresh_mode` 改成 `off` 或 `ask`。", ""]
    return "\n".join(L)


def append_changelog(results, tag, prev_tag, summary_rel):
    applied = [x for r in results for x in r["applied"]]
    if not applied:
        return
    path = common.p("CHANGELOG.md")
    text = open(path, encoding="utf-8").read() if os.path.exists(path) else "# CHANGELOG\n"
    lines = ["## 技能自动更新 %s（%s）" % (common.today().isoformat(), tag or "未打快照"), ""]
    for x in applied:
        lines.append("- %s%s %s：%s（%s）来源：%s" % ("⚠️ 大改动 " if x["big"] else "", ACTION_NAMES.get(x["action"], x["action"]),
                                             x["target"], x["title"], x["id"], " ".join(x["evidence"]) or "—"))
    lines.append("- 摘要：`%s`；回滚：`python3 scripts/rollback.py%s`" % (summary_rel, (" --to %s" % prev_tag) if prev_tag else ""))
    block = "\n".join(lines) + "\n\n"
    head, sep, rest = text.partition("\n\n")
    text = head + sep + block + rest if sep else text + "\n\n" + block
    common.write_text(path, text)


def _ours(base):
    """只同步从本套件目录装出去的安装（manifest 的 home 是本目录），别的副本 / 别的套件不碰。"""
    m = common.read_json(os.path.join(base, "role-agents", "manifest.json"), None) or {}
    return bool(m.get("home")) and os.path.realpath(m["home"]) == os.path.realpath(common.ROOT)


def sync_projects():
    done = []
    st = common.read_json(common.p("state", "projects.json"), {}) or {}
    for proj in st.get("projects") or []:
        if not _ours(os.path.join(proj, ".claude")):
            continue
        rc, out = py(os.path.join(HERE, "install_helper.py"), "--update", "--project", proj)
        done.append(proj if rc == 0 else "%s（失败）" % proj)
    if _ours(os.path.expanduser("~/.claude")):
        rc, out = py(os.path.join(HERE, "install_helper.py"), "--update", "--user")
        done.append("~/.claude" if rc == 0 else "~/.claude（失败）")
    return done


# ---------------- 一次运行 ----------------
def run_once(force=False):
    c = cfg()
    st = load_state()
    if c["mode"] != "auto" and not force:
        print("ℹ️  skills_refresh_mode=%s：不自动更新" % c["mode"])
        return 0
    if not force and not is_due(st, c):
        print("ℹ️  还没到期（每 %d 天一次，上次 %s）" % (c["interval"], st.get("last_run")))
        return 0
    if not acquire():
        print("ℹ️  已有一次自动更新在运行")
        return 0
    os.makedirs(os.path.dirname(LOG), exist_ok=True)
    started = time.time()
    try:
        with open(LOG, "a", encoding="utf-8") as log:
            log.write("\n===== %s 自动更新开始 =====\n" % common.now_iso())
            st["last_run"] = common.today().isoformat()  # 先记，失败也不在同一周反复重跑
            save_state(st)
            roles = scope_roles(c)
            ok, note = run_scout(c, roles, log)
            if not ok:
                st.update(last_status="失败：%s" % note, notified=False, last_summary=None)
                save_state(st)
                print("❌ " + note)
                return 1
            py(os.path.join(HERE, "refresh_check.py"), "--mark-refreshed")
            props = new_proposals(started - 1)
            # 应用前确保有一个基线快照，回滚才有目标
            if not snapshot.list_tags():
                snapshot.take("自动更新前基线")
            prev_tag = (common.read_json(common.p("skills.lock"), {}) or {}).get("tag")
            results = []
            for prop in props:
                tmp = tempfile.NamedTemporaryFile(suffix=".json", delete=False).name
                rc, out = py(os.path.join(HERE, "apply_proposal.py"), prop, "--auto", "--no-snapshot", "--summary", tmp)
                log.write(out + "\n")
                r = common.read_json(tmp, None)
                os.remove(tmp)
                if r:
                    results.append(r)
            applied = sum(len(r["applied"]) for r in results)
            synced = sync_projects() if applied and c["sync"] else []
            tag = snapshot.next_tag() if applied else None
            day = common.today().isoformat()
            summary_rel, n = os.path.join("proposals", "summaries", "%s.md" % day), 2
            while os.path.exists(common.p(summary_rel)):
                summary_rel, n = os.path.join("proposals", "summaries", "%s-%d.md" % (day, n)), n + 1
            common.write_text(common.p(summary_rel), render_summary(results, tag, prev_tag, roles, note, synced))
            append_changelog(results, tag, prev_tag, summary_rel)
            if applied:
                snapshot.take("自动更新 %s" % day)
            st.update(last_status="完成：应用 %d 条" % applied, last_summary=summary_rel, notified=False,
                      last_tag=tag, prev_tag=prev_tag)
            save_state(st)
            print("✅ 自动更新完成：应用 %d 条，摘要 %s" % (applied, common.p(summary_rel)))
            return 0
    finally:
        release()


def spawn():
    """到期且没有在跑时，在后台分离启动 --run，立即返回。返回是否启动了。"""
    if not is_due() or locked() or os.environ.get("WORKER_AGENT_AUTO_REFRESH"):
        return False
    os.makedirs(os.path.dirname(LOG), exist_ok=True)
    with open(LOG, "a", encoding="utf-8") as out:
        subprocess.Popen([sys.executable, os.path.abspath(__file__), "--run"], cwd=common.ROOT, stdout=out, stderr=out,
                         stdin=subprocess.DEVNULL, start_new_session=True,
                         env=dict(os.environ, WORKER_AGENT_AUTO_REFRESH="1"))
    return True


def pending_notice():
    """上次自动更新还没告诉过用户：返回一行提示并标记已提示。"""
    st = load_state()
    if st.get("notified", True) or not st.get("last_status"):
        return None
    st["notified"] = True
    save_state(st)
    if st.get("last_summary"):
        return "🧠 技能已自动更新（%s），摘要：%s；不满意可一键回滚：python3 %s%s" % (
            st["last_status"], common.p(st["last_summary"]), common.p("scripts", "rollback.py"),
            (" --to %s" % st["prev_tag"]) if st.get("prev_tag") else "")
    return "🧠 技能自动更新没有完成（%s），下个周期会再试；日志：%s" % (st["last_status"], LOG)


# ---------------- 定时 ----------------
def plist_path():
    return os.path.expanduser("~/Library/LaunchAgents/%s.plist" % LABEL)


def install_schedule():
    cmd = [sys.executable, os.path.abspath(__file__), "--run"]
    if sys.platform == "darwin":
        p = plist_path()
        os.makedirs(os.path.dirname(p), exist_ok=True)
        args = "".join("<string>%s</string>" % x for x in cmd)
        open(p, "w", encoding="utf-8").write(
            '<?xml version="1.0" encoding="UTF-8"?>\n<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" '
            '"http://www.apple.com/DTDs/PropertyList-1.0.dtd">\n<plist version="1.0"><dict>'
            "<key>Label</key><string>%s</string><key>ProgramArguments</key><array>%s</array>"
            "<key>StartCalendarInterval</key><dict><key>Hour</key><integer>10</integer><key>Minute</key><integer>0</integer></dict>"
            "<key>StandardOutPath</key><string>%s</string><key>StandardErrorPath</key><string>%s</string>"
            "</dict></plist>\n" % (LABEL, args, LOG, LOG))
        subprocess.run(["launchctl", "unload", p], capture_output=True)
        subprocess.run(["launchctl", "load", p], capture_output=True)
        print("✅ 已安装 launchd 任务 %s：每天 10:00 检查，到期（每 %d 天）才更新" % (p, cfg()["interval"]))
        return 0
    cur = subprocess.run(["crontab", "-l"], capture_output=True, text=True).stdout
    lines = [l for l in cur.splitlines() if CRON_MARK not in l]
    lines.append("0 10 * * * %s %s" % (" ".join(shlex.quote(x) for x in cmd), CRON_MARK))
    subprocess.run(["crontab", "-"], input="\n".join(lines) + "\n", text=True)
    print("✅ 已加入 crontab：每天 10:00 检查，到期才更新")
    return 0


def uninstall_schedule():
    if sys.platform == "darwin":
        p = plist_path()
        if os.path.exists(p):
            subprocess.run(["launchctl", "unload", p], capture_output=True)
            os.remove(p)
        print("✅ 已移除 launchd 任务")
        return 0
    cur = subprocess.run(["crontab", "-l"], capture_output=True, text=True).stdout
    subprocess.run(["crontab", "-"], input="\n".join(l for l in cur.splitlines() if CRON_MARK not in l) + "\n", text=True)
    print("✅ 已从 crontab 移除")
    return 0


def status():
    c, st = cfg(), load_state()
    print("模式：%s（auto 自动学习并应用 / ask 提醒 + 拍板 / off 关闭）" % c["mode"])
    print("周期：每 %d 天；范围：%s" % (c["interval"], c["roles"]))
    print("上次运行：%s（%s）" % (st.get("last_run") or "—", st.get("last_status") or "—"))
    print("上次摘要：%s" % (st.get("last_summary") or "—"))
    print("到期：%s；运行中：%s" % ("是" if is_due(st, c) else "否", "是" if locked() else "否"))
    sched = os.path.exists(plist_path()) if sys.platform == "darwin" else False
    print("系统定时：%s（没装也会在会话开始时按周期触发）" % ("已安装" if sched else "未安装"))
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--spawn", action="store_true")
    ap.add_argument("--status", action="store_true")
    ap.add_argument("--install-schedule", action="store_true")
    ap.add_argument("--uninstall-schedule", action="store_true")
    a = ap.parse_args(argv)
    if a.run:
        return run_once(force=a.force)
    if a.spawn:
        print("🧠 已在后台启动技能自动更新" if spawn() else "ℹ️  未到期或已在运行")
        return 0
    if a.install_schedule:
        return install_schedule()
    if a.uninstall_schedule:
        return uninstall_schedule()
    return status()


if __name__ == "__main__":
    sys.exit(main())
