#!/usr/bin/env bash
# 角色 agent 套件安装（REQ-014）。只依赖 python3（3.8+），不需要 pip 包。
#
#   ./install.sh --project <目录>        安装到项目级 <目录>/.claude/（agents、skills、role-agents、hooks）
#   ./install.sh --user                  安装到用户级 ~/.claude/
#   ./install.sh --update --project <目录>   技能层更新后同步：只替换有变化的文件，打印 旧版本 → 新版本
#   ./install.sh --uninstall --project <目录> 只删除本套件装进去的文件和 hooks
#   选项：--no-hooks（不改 settings.json）  --guard（注册 guard_hook 严格模式；默认不注册、不拦截）  --mcp auto|none|kb,context7  --dry-run
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if ! command -v python3 >/dev/null 2>&1; then
  echo "❌ 需要 python3" >&2; exit 1
fi
exec python3 "$HERE/scripts/install_helper.py" "$@"
