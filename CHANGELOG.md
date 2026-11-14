# CHANGELOG

## v1.0.0（2026-11-14）

- 首版：图谱 48 个岗位合并为 14 个专家 + 总控（兼项目经理）+ 技术情报员，共 16 个 Claude Code subagent。
- 首版技能层：98 个技能包（data/skills/），覆盖 14 个专家截至 2026-11 的新平台、新技术、新框架；**情报员自动核实**：每条都联网核实了官方 / 一手来源（见各技能包 sources 与 CHANGELOG），核实不到的记在 proposals/unverified.md，没有写入技能层。
- 图谱原有过时写法标为「暂缓」并给替代：Webpack（新项目）、Android XML 布局（新页面）、RxJava（新代码）、Sketch、Selenium、社区 Ingress NGINX 控制器（已退役）、AutoGen（仓库已归档）。
- 脚本：extract / build / validate / who / usage_report / refresh_check / apply_proposal / rollback / install.sh，hooks：usage_hook / guard_hook。
