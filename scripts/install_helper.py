#!/usr/bin/env python3
"""install.sh 的实现（REQ-014 / 024 / 026 / 027 / 028）。见 install.sh --help。"""
import argparse
import datetime
import glob
import hashlib
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

HOME = common.ROOT
HAND_SKILLS = ["who", "skills-refresh", "orchestrate"]
SUITE_DOCS = ["rules", "workflow", "templates/deliverables", "config"]


def sha(path):
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()[:12]


def version_of(path):
    text = open(path, encoding="utf-8").read()
    m = re.search(r"版本 ([0-9][^\s]*) -->", text)
    if m:
        return m.group(1)
    m = re.search(r"｜版本 ([^｜]+)｜", text)
    if m:
        return "v" + m.group(1).strip() + "+" + sha(path)[:6]
    return sha(path)[:8]


def ts():
    return datetime.datetime.now().strftime("%Y%m%d%H%M%S")


def stage_build(base, project, mcp):
    out = tempfile.mkdtemp(prefix="role-agents-build-")
    cmd = [sys.executable, os.path.join(HERE, "build.py"), "--out", out, "--mcp", mcp,
           "--suite-dir", os.path.join(base, "role-agents"), "--skills-path", os.path.join(base, "skills"), "--home", HOME]
    if project:
        cmd += ["--project", project]
    r = subprocess.run(cmd, text=True)
    if r.returncode:
        raise SystemExit("❌ build 失败")
    for s in HAND_SKILLS:
        src = common.p("skills", s, "SKILL.md")
        dst = os.path.join(out, "skills", s, "SKILL.md")
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        common.write_text(dst, open(src, encoding="utf-8").read().replace("__HOME__", HOME))
    files = {}
    for f in sorted(glob.glob(os.path.join(out, "agents", "*.md"))):
        files["agents/" + os.path.basename(f)] = f
    for f in sorted(glob.glob(os.path.join(out, "skills", "*", "SKILL.md"))):
        files["skills/%s/SKILL.md" % os.path.basename(os.path.dirname(f))] = f
    for d in SUITE_DOCS:
        for f in sorted(glob.glob(common.p(d, "**", "*"), recursive=True)):
            if os.path.isfile(f):
                files["role-agents/" + os.path.relpath(f, HOME)] = f
    return out, files


def regression_gate():
    """REQ-024：选角评测或技能回归题比上次（last_result.json）下降就不允许 --update。"""
    sys.path.insert(0, os.path.join(HERE, "eval_routing"))
    sys.path.insert(0, os.path.join(HERE, "eval_skills"))
    import run_eval
    import run_skill_eval
    hit, rres = run_eval.evaluate(verbose=False)
    rate, sres = run_skill_eval.evaluate(verbose=False)
    import regress
    prev_r = common.read_json(os.path.join(HERE, "eval_routing", "last_result.json"), {}) or {}
    prev_s = common.read_json(os.path.join(HERE, "eval_skills", "last_result.json"), {}) or {}
    bad = []
    if prev_r:
        bad += regress.compare(prev_r.get("results"), rres, prev_r.get("hit_rate"), hit, "routing")
    if prev_s:
        bad += regress.compare(prev_s.get("results"), sres, prev_s.get("pass_rate"), rate, "skills")
    return bad, hit, rate


def register_project(project, remove=False):
    path = common.p("state", "projects.json")
    st = common.read_json(path, {"projects": []}) or {"projects": []}
    ps = [p for p in st["projects"] if p != project]
    if not remove:
        ps.append(project)
    st["projects"] = ps
    common.write_json(path, st)


def install(a, base, project):
    manifest_path = os.path.join(base, "role-agents", "manifest.json")
    manifest = common.read_json(manifest_path, {}) or {}
    old_files = manifest.get("files", {})
    if a.update and not old_files:
        print("ℹ️  目标位置还没有安装过，按全新安装处理")
    if a.update:
        bad, hit, rate = regression_gate()
        if bad:
            print("❌ 回归评测比上次下降，拒绝 --update：\n  " + "\n  ".join(bad))
            return 1
    out, files = stage_build(base, project, a.mcp)
    stamp = ts()
    new_manifest = {"home": HOME, "installed_at": common.now_iso(), "target": base,
                    "suite_version": open(common.p("VERSION")).read().strip(), "files": {}}
    changed = backed = 0
    for rel, src in files.items():
        dst = os.path.join(base, rel)
        new_ver = version_of(src)
        new_manifest["files"][rel] = {"sha": sha(src), "version": new_ver}
        if os.path.exists(dst):
            cur_sha = sha(dst)
            if cur_sha == sha(src):
                continue
            rec = old_files.get(rel)
            if rec is None or rec.get("sha") != cur_sha:
                # 不是本套件装的、或用户改过：先备份
                shutil.copy2(dst, dst + ".bak-" + stamp)
                backed += 1
                print("   备份 %s → %s" % (rel, os.path.basename(dst) + ".bak-" + stamp) +
                      ("（本地改动冲突，已保留备份）" if rec else "（同名文件）"))
            old_ver = (rec or {}).get("version") or version_of(dst)
            if a.dry_run:
                print("   [dry-run] 更新 %s：%s → %s" % (rel, old_ver, new_ver))
                continue
            print("   更新 %s：%s → %s" % (rel, old_ver, new_ver))
        else:
            if a.dry_run:
                print("   [dry-run] 新增 %s（%s）" % (rel, new_ver))
                continue
            if a.update:
                print("   新增 %s：— → %s" % (rel, new_ver))
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copy2(src, dst)
        changed += 1
    # 删除上一版装过、这一版没有的文件
    removed = 0
    for rel in sorted(set(old_files) - set(files)):
        dst = os.path.join(base, rel)
        if os.path.exists(dst) and not a.dry_run:
            if sha(dst) != old_files[rel].get("sha"):
                shutil.copy2(dst, dst + ".bak-" + stamp)
            os.remove(dst)
            removed += 1
            print("   删除旧文件 %s" % rel)
    shutil.rmtree(out, ignore_errors=True)
    if a.dry_run:
        print("（dry-run，没有写入）")
        return 0
    common.write_json(manifest_path, new_manifest)
    if not a.no_hooks:
        settings = os.path.join(base, "settings.json")
        args = [sys.executable, os.path.join(HERE, "settings_merge.py"), "install", settings, "--home", HOME]
        subprocess.run(args, check=True)
    else:
        print("ℹ️  --no-hooks：不改 settings.json；使用度改为从 workspace/*/log.md 统计，更新提醒改为总控开工时检查")
        print("⚠️  没有 guard hook：危险命令不会自动弹确认；产品 / 设计等文档角色有 Write 工具，无法再在工具层拦截它们写代码文件，只能靠提示词约束")
    if project:
        register_project(project)
    n_agents = len([r for r in files if r.startswith("agents/")])
    print("✅ %s完成：%s（%d 个 agent，%d 个 skill）；写入 %d 个文件，备份 %d 个，删除 %d 个" % (
        "更新" if a.update else "安装", base, n_agents, len([r for r in files if r.startswith("skills/")]), changed, backed, removed))
    r = subprocess.run([sys.executable, os.path.join(HERE, "validate.py"), "--agents-dir", os.path.join(base, "agents")],
                       capture_output=True, text=True)
    errs = [l for l in r.stdout.splitlines() if l.startswith("❌") and "agents" in l]
    print("   安装位置 agent 校验：%s" % ("通过" if not errs else "有问题：\n" + "\n".join(errs)))
    if a.update:
        # 记录本次基线，供下次 --update 比较
        subprocess.run([sys.executable, os.path.join(HERE, "eval_routing", "run_eval.py"), "--save", "--quiet"])
        subprocess.run([sys.executable, os.path.join(HERE, "eval_skills", "run_skill_eval.py"), "--save", "--quiet"])
    return 0


def uninstall(a, base, project):
    manifest_path = os.path.join(base, "role-agents", "manifest.json")
    manifest = common.read_json(manifest_path)
    if not manifest:
        print("ℹ️  %s 没有本套件的安装记录（manifest.json），什么都没删" % base)
        return 0
    n = 0
    for rel in manifest.get("files", {}):
        dst = os.path.join(base, rel)
        if os.path.exists(dst):
            os.remove(dst)
            n += 1
            d = os.path.dirname(dst)
            while d.startswith(base) and d != base and os.path.isdir(d) and not os.listdir(d):
                os.rmdir(d)
                d = os.path.dirname(d)
    os.remove(manifest_path)
    rd = os.path.join(base, "role-agents")
    if os.path.isdir(rd) and not any(os.scandir(rd)):
        os.rmdir(rd)
    settings = os.path.join(base, "settings.json")
    subprocess.run([sys.executable, os.path.join(HERE, "settings_merge.py"), "uninstall", settings], check=True)
    if project:
        register_project(project, remove=True)
    print("✅ 已卸载：删除本套件装的 %d 个文件和 hooks；其他文件、你自己的 agent / skill 不受影响" % n)
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(prog="install.sh", description="安装角色 agent 套件到 Claude Code")
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--project", help="安装到项目级 <目录>/.claude/")
    g.add_argument("--user", action="store_true", help="安装到用户级 ~/.claude/")
    ap.add_argument("--update", action="store_true", help="只替换有变化的文件，打印旧版本 → 新版本；回归退化时拒绝")
    ap.add_argument("--uninstall", action="store_true", help="只删除本套件装进去的文件和 hooks")
    ap.add_argument("--no-hooks", action="store_true", help="不改 settings.json")
    ap.add_argument("--mcp", default="auto", help="auto（检测） / none / kb,context7")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args(argv)
    if not a.project and not a.user:
        ap.error("需要 --project <目录> 或 --user")
    project = os.path.abspath(os.path.expanduser(a.project)) if a.project else None
    if project and not os.path.isdir(project):
        ap.error("目录不存在：%s" % project)
    base = os.path.join(project, ".claude") if project else os.path.expanduser("~/.claude")
    if a.uninstall:
        return uninstall(a, base, project)
    return install(a, base, project)


if __name__ == "__main__":
    sys.exit(main())
