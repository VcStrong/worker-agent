# CHANGELOG

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
