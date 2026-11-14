"""REQ-024：技能层快照（skills.lock + git 标签，或非 git 时 snapshots/<标签>/ 目录拷贝）。"""
import datetime
import os
import shutil
import subprocess

import common

SNAP_DIRS = ["data/skills", "agents", "skills", "local", "data/merge_map.json", "data/roles_overlay.json",
             "data/experts.json", "config/radar.yaml", "skills.lock"]


def is_git():
    try:
        out = subprocess.run(["git", "-C", common.ROOT, "rev-parse", "--is-inside-work-tree"],
                             capture_output=True, text=True, timeout=10)
        return out.returncode == 0 and out.stdout.strip() == "true"
    except (OSError, subprocess.SubprocessError):
        return False


def git(*args, check=True):
    r = subprocess.run(["git", "-C", common.ROOT] + list(args), capture_output=True, text=True)
    if check and r.returncode != 0:
        raise RuntimeError("git %s 失败：%s" % (" ".join(args), r.stderr.strip()))
    return r.stdout.strip()


def list_tags():
    if is_git():
        tags = git("tag", "--list", "skills-*", "--sort=creatordate", check=False)
        return [t for t in tags.splitlines() if t]
    d = common.p("snapshots")
    if not os.path.isdir(d):
        return []
    return sorted(x for x in os.listdir(d) if x.startswith("skills-"))


def next_tag():
    day = common.today().strftime("%Y%m%d")
    existing = [t for t in list_tags() if t.startswith("skills-%s-" % day)]
    return "skills-%s-%02d" % (day, len(existing) + 1)


def write_lock(tag, reason):
    skills = common.load_skills(include_local=False)
    lock = {
        "tag": tag,
        "created": common.today().isoformat(),
        "reason": reason,
        "suite_version": open(common.p("VERSION")).read().strip() if os.path.exists(common.p("VERSION")) else "",
        "skills": {sid: {"version": str(s["meta"].get("version")), "maturity": s["meta"].get("maturity"),
                         "as_of": str(s["meta"].get("as_of")), "sha": common.sha8(s["text"])}
                   for sid, s in skills.items()},
    }
    common.write_json(common.p("skills.lock"), lock)
    return lock


def take(reason):
    """生成快照：写 skills.lock，git 时提交 + 打标签（只本地，不 push），否则拷贝到 snapshots/<标签>/。"""
    tag = next_tag()
    write_lock(tag, reason)
    if is_git():
        git("add", "-A")
        st = git("status", "--porcelain", check=False)
        if st:
            git("commit", "-q", "-m", "skills: %s（%s）\n\nCo-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>" % (reason, tag))
        git("tag", tag)
        return tag, "git"
    dest = common.p("snapshots", tag)
    os.makedirs(dest, exist_ok=True)
    for rel in SNAP_DIRS:
        src = common.p(rel)
        if os.path.isdir(src):
            shutil.copytree(src, os.path.join(dest, rel), dirs_exist_ok=True)
        elif os.path.exists(src):
            os.makedirs(os.path.dirname(os.path.join(dest, rel)), exist_ok=True)
            shutil.copy2(src, os.path.join(dest, rel))
    return tag, "dir"


def restore(tag):
    """回到某个快照：git 时只还原技能层相关路径（不动其他代码、不 push），否则从 snapshots/ 拷回。"""
    if is_git():
        paths = [p for p in SNAP_DIRS if p != "local"]
        existing = [p for p in paths if git("ls-tree", "-r", "--name-only", tag, "--", p, check=False)]
        # 先删掉当前技能层里快照中不存在的文件，再从标签检出
        for p in ("data/skills", "agents", "skills"):
            full = common.p(p)
            if os.path.isdir(full):
                shutil.rmtree(full)
        git("checkout", tag, "--", *existing)
        return "git"
    src = common.p("snapshots", tag)
    if not os.path.isdir(src):
        raise RuntimeError("快照不存在：%s" % src)
    for rel in SNAP_DIRS:
        s, d = os.path.join(src, rel), common.p(rel)
        if os.path.isdir(s):
            if os.path.isdir(d):
                shutil.rmtree(d)
            shutil.copytree(s, d)
        elif os.path.exists(s):
            shutil.copy2(s, d)
    return "dir"


def now_tag_time():
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
