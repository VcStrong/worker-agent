# CHANGELOG

## 未发布：角色团接入知识库（2026-11-16）

- 新增 `config/kb_scenes.json`：知识库后台会话的场景 → 角色表（REQ-005），随安装拷到 `role-agents/config/`。
- build：每个专家渲染「知识库宿主模式」段落：不写 workspace/、不用 Write，正文作为最终回复交回（REQ-013 / 019）。
- guard_hook：`KB_SESSION` 存在时 ask → deny，提示改用 kb_ask（REQ-018）。
- validate：校验 kb_scenes.json 角色名、精简名单、宿主模式段落（REQ-019）。
- 选角评测加 12 条知识库场景题；产品经理补术语「确认点、开发流程、需求变更说明、需求扩展」，体验设计师补「设计稿、缺状态」。
- install：检查 config 带上 kb_scenes.json，结束时打印知识库角色团可用状态（REQ-019）。

## v1.0.0（2026-11-14）

- 首版：图谱 48 个岗位合并为 14 个专家 + 总控（兼项目经理）+ 技术情报员，共 16 个 Claude Code subagent。
- 首版技能层：98 个技能包（data/skills/），覆盖 14 个专家截至 2026-11 的新平台、新技术、新框架；**情报员自动核实**：每条都联网核实了官方 / 一手来源（见各技能包 sources 与 CHANGELOG），核实不到的记在 proposals/unverified.md，没有写入技能层。
- 图谱原有过时写法标为「暂缓」并给替代：Webpack（新项目）、Android XML 布局（新页面）、RxJava（新代码）、Sketch、Selenium、社区 Ingress NGINX 控制器（已退役）、AutoGen（仓库已归档）。
- 脚本：extract / build / validate / who / usage_report / refresh_check / apply_proposal / rollback / install.sh，hooks：usage_hook / guard_hook。
