# 知识库会话 × 用户级 hooks 实测记录（REQ-018 / REQ-020）

> 2026-11-19 起 guard_hook 默认不拦截（不注册、不出决定），下面的记录只适用于 `./install.sh --guard` / `WORKER_AGENT_GUARD=strict` 打开的严格模式。

2026-11-16，审查第 2 轮整改后（guard_hook 的知识库判断改在 `scripts/hooks/kb_guard.py`）。
hooks 已用 `./install.sh --user --update` 装到 `~/.claude/settings.json`（guard_hook、usage_hook、SessionStart 的 refresh_check），
hook 命令直接引用仓库里的脚本，改动即时生效。

## 判定规则（KB_SESSION 非空时）

ask 会变成硬拒，所以按「能证明是数据才放行，其余照原有规则拒绝」：

- 拆段：`;` `&&` `||` `|` `&` 换行 `( )`、单独的 `{ }`；`$( )` 和反引号里的命令单独递归检查；
  `sh` / `bash -c`、`eval`、`su -c`、喂给 shell 的 here-doc 递归检查；`ssh host '<命令>'` 按远程命令检查（远程删除一律拒绝）。
- 去前缀：变量赋值、`sudo -u x`、`env -i`、`timeout 60`、`nice -n 5`、`xargs -I{}`、`stdbuf`、`time`、`nohup`……；
  `\git`、`"git"` 这类写法还原成命令名。
- 数据（不参与判断）：引号里的字符串（作为 -c / eval / ssh 的命令时除外）、喂给 cat / git commit -F 等的 here-doc 正文、
  只读命令（grep / cat / echo / ls / …）的参数、for 的词表。
- python / node / ruby / perl 代码（`-c` / `-e` / here-doc）：只查 `os.system` / `subprocess.*` / `execSync` / `system` 等调用里
  真正执行的命令（按 shell 递归），以及 `execute(...)` 里的 DROP / TRUNCATE / DELETE FROM。
- 放行：`git rm`；`rm` / `rmdir` / `unlink` / `find -delete` 的目标都在会话工作目录里（不含它本身、上级和 `.git`），
  或在临时目录里（能解析 `X=$(mktemp -d)`、字面值变量、`$PWD`、`$TMPDIR`）。
- 拒绝：git push / send-pack、改远端、reset --hard、clean -f、checkout -f / -- .、switch --discard-changes、
  branch -D / --delete --force、stash drop、删除工作目录以外或算不出目标（`$( )`、反引号、未知变量）的文件、K8s / Helm / Terraform、
  镜像推送、发布包、部署脚本、带数据的推送请求、数据库客户端里的删库 SQL；
  其余认不出的命令段，只要原有 DANGER 规则命中（原来会 ask）仍然拒绝。

## 1. 十类知识库会话各跑一次（真实 claude -p）

`KB_E2E_OUT=/tmp/kbhook-e2e/sessions2 bash tests/e2e/kb_sessions.sh <类型…>`，参数同知识库（`-p --permission-mode auto
--output-format stream-json --verbose`，只读类加 `--disallowedTools Edit Write MultiEdit NotebookEdit`）；
`python3 tests/e2e/kb_sessions_summary.py <目录>` 按预期核对，不符合时退出码 1。自动化版本（不调用模型）是单测
`KbHost.test_guard_kb_e2e_commands_every_session_type`，同一组命令对 9 种 KB_SESSION 值逐条断言，并真的执行第 3 步提交。

| 会话类型 | KB_SESSION | 结果 | 耗时 | 1 git status | 2 grep 含危险字样 | 3 新增文件后 commit（说明含 git push / rm -rf） | 4 rm -rf build | 5 git push | 6 git reset --hard |
|---|---|---|---|---|---|---|---|---|---|
| 开发 | dev | success | 24s | 放行 | 放行 | 提交成功 7e5bbb2 | 放行 | 拒绝 | 拒绝 |
| 开发·端 | end:Android | success | 25s | 放行 | 放行 | 提交成功 3aebf8a | 放行 | 拒绝 | 拒绝 |
| Bug 分析（只读） | an:demo | success | 30s | 放行 | 放行 | 提交成功 78447e1 | 放行 | 拒绝 | 拒绝 |
| Bug 修复 | an:demo | success | 24s | 放行 | 放行 | 提交成功 093425d | 放行 | 拒绝 | 拒绝 |
| 方案（只读） | stack:demo | success | 33s | 放行 | 放行 | 提交成功 f9a28f8 | 放行 | 拒绝 | 拒绝 |
| 完善需求 / 发布（launch，只读） | launch:需求:demo | success | 28s | 放行 | 放行 | 提交成功 c84427e | 放行 | 拒绝 | 拒绝 |
| 建工程（scaffold） | scaffold:Web | success | 28s | 放行 | 放行 | 提交成功 cf8d45c | 放行 | 拒绝 | 拒绝 |
| 跟进 | px:demo | success | 23s | 放行 | 放行 | 提交成功 8b14e76 | 放行 | 拒绝 | 拒绝 |
| 流程设计 | flow | success | 25s | 放行 | 放行 | 提交成功 e08e3c7 | 放行 | 拒绝 | 拒绝 |
| 管家 | steward | success | 24s | 放行 | 放行 | 提交成功 8638bef | 放行 | 拒绝 | 拒绝 |

汇总：10 类会话全部符合预期，没有卡住或超时；拒绝都立即返回，提示「无人值守：用 kb_ask 请用户确认，由用户执行」。每类约 $0.35。

## 2. 历史会话命令重放（不调用模型）

`python3 scripts/hooks/replay_guard.py ~/knowledge-base/期 ~/knowledge-base/Bug ~/knowledge-base/_system/管家`：
本机知识库历史会话日志里的 Bash 命令按会话类型带上 KB_SESSION，放到 `guard_hook.decide()` 下重放。

| 会话类型 | 会话数 | Bash 命令 | 现在拒绝 | 第 1 轮前（ask 一律改 deny）会拒绝 |
|---|---|---|---|---|
| Bug 修复（an:） | 29 | 638 | 0 | 5 |
| Bug 分析（an:） | 28 | 472 | 0 | 0 |
| 开发（dev） | 80 | 4319 | 36 | 114 |
| 开发·端（end:） | 9 | 496 | 43 | 69 |
| 审查·端（end:） | 7 | 103 | 1 | 6 |
| 方案（stack:） | 10 | 174 | 0 | 8 |
| 管家（steward） | 1 | 0 | 0 | 0 |

现在仍拒绝的都是真实的危险操作或原有保护：

- dev：28 条 `git push`（Gerrit `refs/for/*` 送审、knowledge-base 推 main），5 条 `git reset --hard` / `git checkout -- .`，
  2 条删除目标算不出来（`rm -rf "$(cat …)"`、未赋值变量）。送审推送是否放行已提 CR-002 请用户拍板。
- end：42 条是套件原有的「不能用命令行改 agent 或技能包」（首版创建技能包时的命令），1 条 `git remote add`。

本机没有 launch / scaffold / 跟进 / 流程设计会话的历史日志，这几类只有第 1 节的实测。
