---
id: agent-sdk
name: Agent SDK（Claude Agent SDK / OpenAI Agents SDK）
aliases: [Claude Agent SDK, OpenAI Agents SDK, Agents SDK, Claude Code SDK, Microsoft Agent Framework]
roles: [ai-app-engineer]
maturity: 试用
maturity_by_region: {cn: 评估, global: 试用}
as_of: 2026-11-14
version: 1.0.0
sources:
  - https://code.claude.com/docs/en/agent-sdk/overview
  - https://github.com/anthropics/claude-agent-sdk-python/releases
  - https://openai.github.io/openai-agents-python/
  - https://github.com/openai/openai-agents-python/releases
region: global
replaces: [autogen]
replaced_by: []
from_graph: false
---

# Agent SDK（Claude Agent SDK / OpenAI Agents SDK）

## 成熟度判断
- global 试用：两者均为模型厂商官方维护，迭代很快但仍在 1.0 之前（claude-agent-sdk-python v0.2.182，2026-11-13；openai-agents-python v0.24.0，2026-10-15），API 可能有破坏性变更。
- cn 评估：Claude Agent SDK 依赖 Claude 模型，境内面向公众不可用；OpenAI Agents SDK 可经 LiteLLM 等适配接国内模型，可做内部工具。国内生产首选 LangGraph（见 langgraph）。
- 回退方案：编排逻辑与业务工具解耦（工具走 MCP），SDK 出问题可换 LangGraph 或直接调 API 自写循环。

## 什么时候用
- Claude Agent SDK：要复用 Claude Code 同款能力（文件读写、命令执行、子 Agent、Hooks、权限、会话、Skills、插件）构建研发效能或文档处理类 Agent。
- OpenAI Agents SDK：轻量多 Agent（Handoffs、Agent 作为工具）、内置 Guardrails、Sessions 和 Tracing。

## 关键做法
- 先按官方「最简方案优先」：单次调用够用就不上 SDK。
- 权限最小化：默认只读，写文件 / 执行命令 / 外发网络需要确认或白名单。
- 工具统一走 MCP，SDK 只负责循环与编排，降低绑定。
- 打开 Tracing / Hooks 记录每步工具调用，接入评测（见 llm-eval-pipeline）。
- 锁定 SDK 小版本，升级前跑回归。

## 常见坑
- Claude Agent SDK 官方要求第三方产品使用 API Key 鉴权，不得提供 claude.ai 登录；产品命名不得冒用「Claude Code」。
- 无迭代上限，Agent 在失败任务上反复重试。
- 让 Agent 在生产服务器直接执行命令，缺沙箱隔离。

## 迁移
- 从 Claude Code SDK 旧包：按官方 Migration guide 改包名与导入。
- 从 AutoGen：按微软官方指南迁 Microsoft Agent Framework，或改用本技能 / LangGraph（见 autogen）。

## 最佳做法
- 先跑通官方示例 Agent，再替换工具和提示词，避免从零搭。

## CHANGELOG
- 2026-11-14 v1.0.0 首版；情报员自动核实（来源见 sources）
