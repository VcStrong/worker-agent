---
name: langgraph
description: "LangGraph（成熟度 采用，as_of 2026-11-14）：有状态、长时运行、需要可恢复的 Agent 或工作流（审批流、多步研究、客服多轮）。 适用角色：AI 应用 / Agent 工程师。"
---
<!-- generated-by: scripts/build.py；源文件 data/skills/ai-app/langgraph.md，请勿手改 -->

> 成熟度：**采用**（region=cn）｜版本 1.0.0｜as_of 2026-11-14｜来源：https://docs.langchain.com/oss/python/langgraph/overview https://blog.langchain.com/langchain-langgraph-1dot0 https://github.com/langchain-ai/langgraph/releases

# LangGraph

## 成熟度判断
- 采用：图谱原有工具。2025-10 发布 1.0（承诺稳定、向后兼容），GitHub Releases 最新 1.2.22（2026-11-14）。模型无关，可接国内外任意模型，适合作为国内 Agent 生产编排默认选型。

## 什么时候用
- 有状态、长时运行、需要可恢复的 Agent 或工作流（审批流、多步研究、客服多轮）。
- 需要人工介入（暂停 → 人审 → 继续）和精细控制流程的场景。

## 关键做法
- 用状态图建模：节点 = 步骤，边 = 条件跳转；状态结构用强类型定义。
- 开启持久化（checkpointer 存 Postgres / Redis），支持断点续跑和时间回溯调试。
- 人工介入用 interrupt 暂停，前端展示待审内容，审批后恢复。
- 流式输出 Token 与状态更新，前端展示过程。
- 简单 ReAct Agent 用 langchain.agents 的预制方案（1.0 起 langgraph.prebuilt 已废弃迁移至此），复杂流程再手写图。

## 常见坑
- 状态里塞大对象（全文档、图片），持久化和序列化变慢。
- 图里无终止条件或循环上限。
- 只依赖 LangSmith 托管服务，私有化 / 国内部署时可观测性缺位；可改接自建 Trace（如 MLflow Tracing、OpenTelemetry）。

## 迁移
- 0.x → 1.0：主要变化是 langgraph.prebuilt 迁到 langchain.agents，按官方迁移指南替换导入。
- 从 AutoGen：多 Agent 对话改为图中的节点与子图（见 autogen）。

## 最佳做法
- 每个节点可单测：输入状态 → 输出状态，配合评测集做回归。

## CHANGELOG
- 2026-11-14 v1.0.0 首版；情报员自动核实（来源见 sources）
