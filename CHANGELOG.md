# CHANGELOG

## 未发布：技能定期自动学习、自动更新（2026-11-19）

- 新增 `scripts/auto_refresh.py`：`config/run.yaml` 的 `skills_refresh_mode: auto`（默认）下每 7 天无人值守地用 `claude -p` 跑技术情报员（全部角色），核实后自动应用，写摘要 `proposals/summaries/<日期>.md` 并追加到 CHANGELOG，附一键回滚命令；`--install-schedule` 可装 launchd / crontab；`auto_sync_projects` 自动 install --update 本套件装过的项目。
- refresh_check `--hook`：auto 模式下不再提醒、不等回复，到期就在后台启动自动更新，上次结果只提示一行；`ask` 恢复提醒 + 拍板，`off` 关闭；知识库会话和自动更新自身不触发。
- apply_proposal 新增 `--auto` / `--summary`：核实过的条目（含废弃、新增 / 下线角色等大改动）全部应用，待核实 / 可疑来源 / 格式错误 / 重复驳回跳过；整批回归退化时逐条重试、只留不退化的。
- 快照提交只包含技能层、proposals、CHANGELOG，不再 `git add -A` 把用户别的未提交改动一起提交。
- skills-refresh / tech-scout / orchestrator 说明同步改为默认自动；新增 tests/test_auto_refresh.py。

## 未发布：guard_hook 默认不拦截，只协助（2026-11-19）

- 角色套件只协助、不比 Claude Code 本身管得更严：guard_hook 默认不输出 ask / deny，放行与否完全交给 Claude Code 自己的权限设置（permission mode、allow / deny 规则、auto 模式分类器）。强推、`sudo rm`、kubectl / helm / terraform、发布、删库、写 agent / 技能包、文档角色写代码文件，默认都不再弹确认或拒绝；知识库后台会话（`KB_SESSION`）同样不再 deny。
- 严格模式改为显式开关：`./install.sh --guard`（注册为 `guard_hook.py --strict`）或环境变量 `WORKER_AGENT_GUARD=strict`，打开后规则与之前完全一致（含 KB_SESSION 下 ask → deny、Gerrit 送审例外）。
- install.sh / settings_merge.py：默认不再往 settings.json 写 guard_hook；重装（`./install.sh --user --update`）会把旧版装进去的 guard_hook 条目清掉，加 `--guard` 则写成严格模式。旧条目在重装前也已不生效（hook 本身默认不出决定）。
- replay_guard.py 按严格模式重放；新增测试 `GuardDefaultOff`（默认 / KB_SESSION 下不出决定、strict 开关、settings_merge 默认与 --guard）。

## 未发布：常用命令不再弹确认（2026-11-17）

- guard_hook：交互会话里普通 `git push`、`rm` / `rmdir` / `find -delete`、`git reset --hard` / `clean -f` / `branch -D` 直接放行（`COMMON_ALLOW`）；强推、`+` 推送、删远端分支、`sudo` 删除、删 `/` 或 `~` 仍弹确认；部署、发布、K8s、删库、发推送、添加远端不变。知识库无人值守会话（`KB_SESSION`）同样放行这些常用命令（免打扰时不被拒），只对交互会话也会 ask 的命令按 kb_guard 细判后拒绝。
- 「发推送」规则不再把 `git push` 里的 push 字样当成发推送（连推两个分支、`--push-option` 不再误拦）。

## 未发布：角色团接入知识库（2026-11-16）

- 新增 `config/kb_scenes.json`：知识库后台会话的场景 → 角色表（REQ-005），随安装拷到 `role-agents/config/`。
- build：每个专家渲染「知识库宿主模式」段落：不写 workspace/、不用 Write，正文作为最终回复交回（REQ-013 / 019）。
- guard_hook：`KB_SESSION` 存在时 ask → deny，提示改用 kb_ask（REQ-018）；硬拒只看命令名位置（拆段、剥引号和 here-doc），
  grep / echo / commit 说明里的字样、git rm、删工作目录或临时目录里的文件不再误伤（审查第 1 轮）。
- guard_hook（审查第 2 轮）：知识库会话判断移到 scripts/hooks/kb_guard.py，改为「能证明是数据才放行，其余照原有规则拒绝」：
  递归检查 sh / bash -c、eval、su -c、ssh 远程命令、$( ) / 反引号、喂给 shell 的 here-doc，去掉带参数的前缀（sudo -u、env -i、timeout、nice -n、xargs -I），
  python / node 代码只查 os.system / subprocess / execSync 等调用和 execute(...) 里的删库 SQL；删除目标含 $( ) / 反引号 / 未知变量时拒绝；
  补 git branch --delete --force、checkout -f、switch --discard-changes、带数据的推送请求。
- validate：kb_scenes.json 多出 12 个以外的场景报错；顶层 / 场景 / 档位 / 用途 / 名单类型不对时报出位置，不再崩溃。
- tests/e2e/kb_sessions.sh 第 3 步先改文件再提交；汇总脚本按预期核对、不符合时退出码 1；单测加十类会话命令组的自动化版本。
- 新增 scripts/hooks/replay_guard.py（历史会话命令重放）、tests/e2e/kb_sessions.sh（十类知识库会话实测），记录见 docs/evidence/kb-hooks-e2e.md。
- refresh_check：知识库会话里 --hook 不注入提醒、不记 last_remind。
- validate：校验 kb_scenes.json（版本=1、12 个场景、字段完整、每确认点上限、档位映射、每期上限默认、自动场景模型、产物目录、角色名、精简 ⊆ tiers.lite.roles 且 roles 必须是列表、只读安全角色不含工程师）和宿主模式段落（REQ-019，变更 CR-001）。
- build：宿主模式里的产物目录从 kb_scenes.json 的「产物目录」读。
- 选角评测加 12 条知识库场景题；产品经理补术语「确认点、开发流程、需求变更说明、需求扩展」，体验设计师补「设计稿、缺状态」。
- install：检查 config 带上 kb_scenes.json，结束时打印知识库角色团可用状态（REQ-019）。

## v1.0.0（2026-11-14）

- 首版：图谱 48 个岗位合并为 14 个专家 + 总控（兼项目经理）+ 技术情报员，共 16 个 Claude Code subagent。
- 首版技能层：98 个技能包（data/skills/），覆盖 14 个专家截至 2026-11 的新平台、新技术、新框架；**情报员自动核实**：每条都联网核实了官方 / 一手来源（见各技能包 sources 与 CHANGELOG），核实不到的记在 proposals/unverified.md，没有写入技能层。
- 图谱原有过时写法标为「暂缓」并给替代：Webpack（新项目）、Android XML 布局（新页面）、RxJava（新代码）、Sketch、Selenium、社区 Ingress NGINX 控制器（已退役）、AutoGen（仓库已归档）。
- 脚本：extract / build / validate / who / usage_report / refresh_check / apply_proposal / rollback / install.sh，hooks：usage_hook / guard_hook。
