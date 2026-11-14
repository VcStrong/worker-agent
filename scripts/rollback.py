#!/usr/bin/env python3
"""REQ-024：技能层回滚到上一个快照。

- worker-agent 是 git 仓库：从上一个 skills-* 标签检出技能层（data/skills、agents、skills、merge_map 等），不 push
- 不是 git：从 snapshots/<标签>/ 拷回
回滚后重新 build + validate。

用法：
  python3 scripts/rollback.py            # 回到上一个快照
  python3 scripts/rollback.py --to skills-20261114-01
  python3 scripts/rollback.py --list
  python3 scripts/rollback.py --snapshot "原因"   # 手动打一个快照
"""
import argparse
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "lib"))
import common  # noqa: E402
import snapshot  # noqa: E402


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--to")
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--snapshot")
    a = ap.parse_args(argv)
    mode = "git 标签" if snapshot.is_git() else "snapshots/ 目录"
    tags = snapshot.list_tags()
    if a.snapshot:
        tag, m = snapshot.take(a.snapshot)
        print("📸 快照 %s（%s）" % (tag, mode))
        return 0
    if a.list:
        cur = (common.read_json(common.p("skills.lock"), {}) or {}).get("tag")
        print("快照（%s）：" % mode)
        for t in tags:
            print("  %s %s" % ("*" if t == cur else " ", t))
        return 0
    cur = (common.read_json(common.p("skills.lock"), {}) or {}).get("tag")
    if a.to:
        target = a.to
        if target not in tags:
            print("❌ 没有快照 %s" % target)
            return 1
    else:
        if cur in tags:
            i = tags.index(cur)
            if i == 0:
                print("❌ %s 已是最早的快照，无法再回滚" % cur)
                return 1
            target = tags[i - 1]
        elif tags:
            target = tags[-1]
        else:
            print("❌ 还没有任何快照")
            return 1
    snapshot.restore(target)
    print("⏪ 已回滚技能层到 %s（%s，未 push）" % (target, mode))
    rc = subprocess.run([sys.executable, os.path.join(HERE, "build.py"), "--quiet"]).returncode
    rc2 = subprocess.run([sys.executable, os.path.join(HERE, "validate.py")], capture_output=True, text=True)
    print(rc2.stdout.splitlines()[-1] if rc2.stdout else "")
    if rc or rc2.returncode:
        print("❌ 回滚后 build / validate 未通过")
        return 1
    print("✅ validate 通过。需要同步到项目时运行 install.sh --update。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
