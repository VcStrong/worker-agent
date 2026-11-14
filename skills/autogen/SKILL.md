---
name: autogen
description: "AutoGen（微软多 Agent 框架）（成熟度 暂缓，as_of 2026-11-14）：不再用于新项目。 适用角色：AI 应用 / Agent 工程师。"
---
<!-- generated-by: scripts/build.py；源文件 data/skills/ai-app/autogen.md，请勿手改 -->

> 成熟度：**暂缓**（region=cn）｜版本 1.0.0｜as_of 2026-11-14｜来源：https://github.com/microsoft/autogen https://learn.microsoft.com/en-us/agent-framework/migration-guide/from-autogen/ https://github.com/microsoft/agent-framework/releases

# AutoGen（微软多 Agent 框架）

## 成熟度判断
- 暂缓：图谱原有工具。官方 GitHub 仓库已标记归档（archived），声明不再提供缺陷修复、安全修复和新功能，不建议生产使用；最后版本 python-v0.7.5（2025-09-30）。
- 官方继任者为 Microsoft Agent Framework（AutoGen 与 Semantic Kernel 合并，最新 python-1.26.0，2026-11-13）。

## 什么时候用
- 不再用于新项目。
- 存量项目照旧维护，但须评估安全风险并排期迁移。

## 关键做法
- 存量系统冻结依赖版本，隔离运行环境，限制其可访问的数据和网络。
- 盘点 AutoGen 中的 Agent、工具、对话模式，形成迁移清单。

## 常见坑
- 继续在 AutoGen 上加功能，迁移成本越积越大。
- 误用社区分叉 AG2 当作微软官方延续，二者治理不同。

## 替代
- 原因：上游已归档，无安全修复，依赖漏洞无法得到处理。
- 替代项：langgraph（国内默认，模型无关、生产可用）；agent-sdk（海外项目，厂商官方 SDK）；.NET / Azure 体系可选微软官方的 Microsoft Agent Framework。
- 迁移建议：按微软官方「AutoGen → Microsoft Agent Framework」迁移指南，或把 GroupChat 等对话模式改写为 LangGraph 子图 / Agent SDK 的 Handoffs；工具层先抽成 MCP Server，可复用到新框架。
- 存量项目照旧维护，只在产物里提迁移建议，不擅自迁移。

## 迁移
- 第一步工具抽离（MCP），第二步编排改写，第三步用同一评测集对比新旧效果后切流。

## 最佳做法
- 迁移期间新旧并行，评测集分数不低于旧系统再下线。

## CHANGELOG
- 2026-11-14 v1.0.0 首版；情报员自动核实（来源见 sources）
