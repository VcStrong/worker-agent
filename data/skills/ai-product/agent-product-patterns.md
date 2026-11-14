---
id: agent-product-patterns
name: Agent 产品形态
aliases: [智能体产品, Agent 形态, 工作流 vs 智能体, Copilot 形态]
roles: [ai-product-manager, ai-app-engineer]
maturity: 采用
as_of: 2026-11-14
version: 1.0.0
sources:
  - https://www.anthropic.com/engineering/building-effective-agents
  - https://code.claude.com/docs/en/agent-sdk/overview
region: both
replaces: []
replaced_by: []
from_graph: false
---

# Agent 产品形态

## 成熟度判断
- 采用：Anthropic 官方工程文章给出的「工作流 vs 智能体」划分和 5 种工作流模式已成为行业通用语言；各厂商 Agent SDK、托管 Agent 服务（如 Claude Managed Agents）均按此落地。
- 当前状态（2026-11）：Agent 形态从「聊天框」扩展到后台长任务、嵌入式 Copilot、多 Agent 协作。

## 什么时候用
- 设计 AI 功能时决定「单次调用 / 固定工作流 / 自主 Agent」哪种形态。
- 评估一个需求是否真需要 Agent，避免为了 Agent 而 Agent。

## 关键做法
- 先选最简单形态：单次调用 + 检索 + 示例 → 工作流 → 自主 Agent，只在能证明效果提升时加复杂度。
- 工作流 5 种模式：链式（Prompt chaining）、路由（Routing）、并行（分段 / 投票）、编排-执行（Orchestrator-workers）、生成-评审（Evaluator-optimizer）。
- 自主 Agent 适合步骤数无法预知的开放任务，必须设计：迭代上限、检查点、人工确认点、可回滚。
- 产品形态四选一并写进 PRD：对话助手 / 嵌入式 Copilot（在现有页面里给建议）/ 后台任务型（异步执行、完成通知）/ 多 Agent 协作。
- 把「Agent 可以做什么、不能做什么」写成权限清单（读、写、付款、外发消息分级授权）。

## 常见坑
- 用自主 Agent 做本可固定流程的事，成本高、错误会累积。
- 没有停止条件，Agent 死循环烧 Token。
- 高风险动作（下单、删数据、对外发消息）没有人工确认。
- 只展示最终结果不展示过程，用户无法信任也无法纠错。

## 迁移
- 从「一个大 Prompt 聊天框」迁到工作流：先把稳定步骤拆成链式或路由，只把真正不确定的环节交给 Agent。
- 从 Dify / Coze 原型迁到代码实现时，保留工作流图作为需求文档（见 dify-coze）。

## 最佳做法
- PRD 中写清 Agent 的「目标、可用工具、权限、停止条件、人工接管入口」五项。
- 过程透明：展示计划和关键步骤，用户可中途打断。

## CHANGELOG
- 2026-11-14 v1.0.0 首版；情报员自动核实（来源见 sources）
