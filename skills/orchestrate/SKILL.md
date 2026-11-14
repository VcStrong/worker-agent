---
name: orchestrate
description: 用角色 agent 团队完成一个互联网产品需求（做功能、改页面、修线上 Bug、出方案、从 PRD / 技术方案开始开发）。主会话按总控（orchestrator）的规则选角、出执行计划、按 9 阶段调度 14 个专家子 agent、在 3 个节点请用户拍板。用户提出成型的产品 / 研发需求时使用，如 /orchestrate 做一个带积分的签到功能。
---

# /orchestrate <需求>

子 agent 不能再调子 agent，所以完整调度要在**主会话**里进行：

1. 读 `.claude/agents/orchestrator.md`（或 `~/.claude/agents/orchestrator.md`）里 frontmatter 之后的全部规则，**你在本次会话里就是总控**，严格照做。
2. 需求 = `$ARGUMENTS`；为空时问用户要做什么。
3. 先输出执行计划（阶段、主导 / 参与角色、交付物、拍板节点），然后用 Agent 工具按计划调用专家子 agent（subagent_type = 专家 slug）。
4. 遵守 `config/run.yaml`（max_parallel、max_calls、approval_mode）和 `config/team.yaml`（档位、AI 参与规则），日志写 `workspace/<需求名>/log.md`。

也可以直接用 `claude --agent orchestrator` 把总控作为主线程 agent 启动。
