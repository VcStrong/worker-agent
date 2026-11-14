---
name: mcp
description: "MCP（Model Context Protocol）（成熟度 采用，as_of 2026-11-14）：把内部系统（工单、知识库、数据库、业务 API）以工具 / 资源形式开放给多个 AI 客户端复用。 适用角色：AI 应用 / Agent 工程师、AI Infra / MLOps 工程师。"
---
<!-- generated-by: scripts/build.py；源文件 data/skills/ai-app/mcp.md，请勿手改 -->

> 成熟度：**采用**（region=cn）｜版本 1.0.0｜as_of 2026-11-14｜来源：https://modelcontextprotocol.io/specification/2026-07-28 https://github.com/modelcontextprotocol/modelcontextprotocol/releases

# MCP（Model Context Protocol）

## 成熟度判断
- 采用：图谱原有工具。当前规范版本 2026-07-28（GitHub Release 2026-07-28 发布），由 Linux 基金会下的 Agentic AI Foundation 治理；主流模型厂商、IDE、Agent SDK 均原生支持。
- 本版要点：核心协议改为无状态（每个请求自带版本与能力协商，不再有会话握手）；Tasks（长任务）、MCP Apps（对话内交互 UI）、Skills over MCP 以可选扩展形式提供；2024-11-05 版本已列为旧版。

## 什么时候用
- 把内部系统（工单、知识库、数据库、业务 API）以工具 / 资源形式开放给多个 AI 客户端复用。
- 需要一套接口同时服务 Claude、ChatGPT、IDE、自研 Agent 时。

## 关键做法
- Server 暴露三类能力：Tools（模型可调用的函数）、Resources（上下文数据）、Prompts（模板）；客户端可提供 Elicitation（向用户追问）。
- 远程 Server 用 Streamable HTTP + OAuth 授权；本地工具用 stdio。
- 新 Server 直接按 2026-07-28 无状态模型实现，便于水平扩展和网关负载均衡。
- 工具描述写清用途、参数、副作用；高风险工具在 Host 侧要求用户确认。
- 长耗时操作用 Tasks 扩展（轮询、中途补充输入），不要阻塞请求。

## 常见坑
- 把第三方 Server 的工具描述当可信内容，遭工具投毒 / 提示词注入；规范明确工具注解默认不可信。
- 一个 Server 暴露几十个工具，挤占上下文、降低选工具准确率。
- Token 透传：把用户令牌原样转给下游 API，违反授权规范。
- 仍按旧版有状态会话实现，部署到多副本后会话丢失。

## 迁移
- 旧版（2025 年及之前的会话式）Server：按官方迁移说明去掉会话依赖，把状态放到外部存储或请求参数中；SDK 升到支持 2026-07-28 的版本。
- 自研插件 / Function Calling 适配层：逐步改为 MCP Server，一次实现多客户端复用。

## 最佳做法
- 内部 MCP Server 统一挂在网关后面做鉴权、限流和审计（见 llm-gateway-routing）。

## CHANGELOG
- 2026-11-14 v1.0.0 首版；情报员自动核实（来源见 sources）
