#!/usr/bin/env python3
"""REQ-014 / 026 / 028：把本套件的 hooks 合并进目标 .claude/settings.json（先备份 .bak），或干净移除。

  python3 scripts/settings_merge.py install   <settings.json> [--home <worker-agent>] [--no-reminder]
  python3 scripts/settings_merge.py uninstall <settings.json>

只追加带标记 `role-agents-suite` 的 hook，原有配置保持不变；卸载只删带标记的 hook。
"""
import json
import os
import shutil
import sys

MARK = "role-agents-suite"


def hooks_for(home, reminder=True):
    py = "python3"
    q = lambda p: '"%s"' % os.path.join(home, p)  # noqa: E731
    h = {
        "PreToolUse": [
            {"matcher": "Task|Agent|Skill|Read", "hooks": [{"type": "command", "command": "%s %s # %s" % (py, q("scripts/hooks/usage_hook.py"), MARK)}]},
            {"matcher": "Bash|Write|Edit|MultiEdit|NotebookEdit", "hooks": [{"type": "command", "command": "%s %s # %s" % (py, q("scripts/hooks/guard_hook.py"), MARK)}]},
        ],
        "SubagentStop": [
            {"hooks": [{"type": "command", "command": "%s %s # %s" % (py, q("scripts/hooks/usage_hook.py"), MARK)}]},
        ],
    }
    if reminder:
        h["SessionStart"] = [{"hooks": [{"type": "command", "command": "%s %s --hook # %s" % (py, q("scripts/refresh_check.py"), MARK)}]}]
    return h


def load(path):
    if not os.path.exists(path):
        return {}
    with open(path, encoding="utf-8") as f:
        txt = f.read().strip()
    return json.loads(txt) if txt else {}


def strip_ours(settings):
    hooks = settings.get("hooks") or {}
    removed = 0
    for event in list(hooks):
        new_groups = []
        for g in hooks[event]:
            kept = [x for x in g.get("hooks", []) if MARK not in x.get("command", "")]
            removed += len(g.get("hooks", [])) - len(kept)
            if kept:
                g = dict(g, hooks=kept)
                new_groups.append(g)
        if new_groups:
            hooks[event] = new_groups
        else:
            del hooks[event]
    if "hooks" in settings and not hooks:
        del settings["hooks"]
    return removed


def save(path, data, backup=True):
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    if backup and os.path.exists(path):
        shutil.copy2(path, path + ".bak")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")


def main(argv):
    if len(argv) < 2 or argv[0] not in ("install", "uninstall"):
        print(__doc__)
        return 2
    action, path = argv[0], argv[1]
    home = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if "--home" in argv:
        home = os.path.abspath(argv[argv.index("--home") + 1])
    settings = load(path)
    existed = os.path.exists(path)
    removed = strip_ours(settings)
    if action == "install":
        hooks = settings.setdefault("hooks", {})
        added = 0
        for event, groups in hooks_for(home, "--no-reminder" not in argv).items():
            hooks.setdefault(event, []).extend(groups)
            added += len(groups)
        save(path, settings)
        print("✅ hooks 已合并进 %s（追加 %d 组%s）%s" % (path, added, "，替换旧版 %d 条" % removed if removed else "",
                                                     "；原文件已备份为 settings.json.bak" if existed else ""))
    else:
        if not existed:
            print("ℹ️  %s 不存在，跳过" % path)
            return 0
        save(path, settings)
        print("✅ 已从 %s 移除本套件的 %d 条 hook（备份 settings.json.bak）" % (path, removed))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
