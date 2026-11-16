# 知识库会话 × 用户级 hooks 实测记录（REQ-018 / REQ-020）

2026-11-16，审查第 1 轮整改后。hooks 已用 `./install.sh --user --update` 装到 `~/.claude/settings.json`
（guard_hook、usage_hook、SessionStart 的 refresh_check）。

## 1. 十类知识库会话各跑一次（真实 claude -p）

脚本 `tests/e2e/kb_sessions.sh`：参数同知识库（`-p --permission-mode auto --output-format stream-json --verbose`，
只读类加 `--disallowedTools Edit Write MultiEdit NotebookEdit`），每个会话带对应的 `KB_SESSION`，在临时 git 仓库里逐条执行同一组命令；
`tests/e2e/kb_sessions_summary.py` 汇总。

| 会话类型 | KB_SESSION | 结果 | 耗时 | git status | grep 含危险字样 | commit 说明含危险字样 | rm -rf build | git push | git reset --hard |
|---|---|---|---|---|---|---|---|---|---|
| 开发 | dev | success | 26s | 放行 | 放行 | 放行¹ | 放行 | 拒绝 | 拒绝 |
| 开发·端 | end:Android | success | 25s | 放行 | 放行 | 放行¹ | 放行 | 拒绝 | 拒绝 |
| Bug 分析（只读） | an:demo | success | 27s | 放行 | 放行 | 放行¹ | 放行 | 拒绝 | 拒绝 |
| Bug 修复 | an:demo | success | 32s | 放行 | 放行 | 放行¹ | 放行 | 拒绝 | 拒绝 |
| 方案（只读） | stack:demo | success | 30s | 放行 | 放行 | 放行¹ | 放行 | 拒绝 | 拒绝 |
| 完善需求 / 发布（launch） | launch:需求:demo | success | 26s | 放行 | 放行 | 放行¹ | 放行 | 拒绝 | 拒绝 |
| 建工程（scaffold） | scaffold:Web | success | 24s | 放行 | 放行 | 放行¹ | 放行 | 拒绝 | 拒绝 |
| 跟进 | px:demo | success | 28s | 放行 | 放行 | 放行¹ | 放行 | 拒绝 | 拒绝 |
| 流程设计 | flow | success | 35s | 放行 | 放行 | 放行¹ | 放行 | 拒绝 | 拒绝 |
| 管家 | steward | success | 26s | 放行 | 放行 | 放行¹ | 放行 | 拒绝 | 拒绝 |

¹ hook 放行；git 因为「nothing to commit」返回 1，跟 hook 无关。

没有会话卡住或超时；拒绝都立即返回，提示「无人值守：用 kb_ask 请用户确认，由用户执行」。每类约 $0.35。

## 2. 历史会话命令重放（不调用模型）

`python3 scripts/hooks/replay_guard.py ~/knowledge-base/期 ~/knowledge-base/Bug ~/knowledge-base/_system/管家`：
把本机知识库历史会话日志里的 Bash 命令按会话类型带上 KB_SESSION，放到 `guard_hook.decide()` 下重放。

| 会话类型 | 会话数 | Bash 命令 | 现在拒绝 | 第 1 轮（ask 一律改 deny）会拒绝 |
|---|---|---|---|---|
| Bug 修复（an:） | 29 | 638 | 0 | 5 |
| Bug 分析（an:） | 28 | 472 | 0 | 0 |
| 开发（dev） | 80 | 4319 | 36 | 114 |
| 开发·端（end:） | 6 | 405 | 43 | 65 |
| 审查·端（end:） | 5 | 63 | 1 | 4 |
| 方案（stack:） | 9 | 164 | 0 | 6 |
| 管家（steward） | 1 | 0 | 0 | 0 |

现在仍拒绝的都是真实的危险操作或原有保护：

- dev：28 条 `git push`（Gerrit `refs/for/*` 送审、knowledge-base 推 main），5 条 `git reset --hard` / `git checkout -- .`，
  2 条删除目标算不出来（`rm -rf "$(cat …)"`、未赋值变量）。送审推送是否放行已提 CR-002 请用户拍板。
- end：42 条是套件原有的「不能用命令行改 agent 或技能包」（首版创建技能包时的命令），1 条 `git remote add`。

本机没有 launch / scaffold / 跟进 / 流程设计会话的历史日志，这几类只有第 1 节的实测。
