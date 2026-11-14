---
name: a2a-protocol
description: "A2A（Agent2Agent 协议）（成熟度 试用，as_of 2026-11-14）：不同团队 / 不同厂商 / 不同框架实现的 Agent 需要互相委派任务（如企业助手调用供应商的报价 Agent）。 适用角色：AI 应用 / Agent 工程师。"
---
<!-- generated-by: scripts/build.py；源文件 data/skills/ai-app/a2a-protocol.md，请勿手改 -->

> 成熟度：**试用**（region=cn）｜版本 1.0.0｜as_of 2026-11-14｜来源：https://a2a-protocol.org/latest/ https://github.com/a2aproject/A2A/releases https://www.linuxfoundation.org/press/a2a-protocol-surpasses-150-organizations-lands-in-major-cloud-platforms-and-sees-enterprise-production-use-in-first-year

# A2A（Agent2Agent 协议）

## 成熟度判断
- 试用：Google 发起、2025-06 移交 Linux 基金会；规范已发布首个稳定版 1.0（GitHub Releases 最新 v1.0.1，2026-05-28）；Linux 基金会 2026-04 公告称 150+ 组织支持，已进入 Google、Microsoft、AWS 云平台。
- 风险：国内生态与落地案例较少；大多数业务场景单进程多 Agent 即可满足。回退方案：跨系统调用退回普通 HTTP API 或 MCP 工具调用。

## 什么时候用
- 不同团队 / 不同厂商 / 不同框架实现的 Agent 需要互相委派任务（如企业助手调用供应商的报价 Agent）。
- 远程 Agent 是「黑盒」，只暴露能力不暴露内部工具与提示词。

## 关键做法
- 区分 A2A 与 MCP：MCP 是 Agent 调工具 / 数据，A2A 是 Agent 调 Agent，两者互补。
- 每个远程 Agent 发布 Agent Card（名称、能力、技能、端点、鉴权方式），供调用方发现。
- 以 Task 为单位交互，支持长任务状态更新、流式推送和产物（Artifact）返回。
- 鉴权走标准 HTTP 方案（OAuth / API Key），在网关统一做认证、限流与审计。
- 用官方 SDK 实现，避免手写协议细节。

## 常见坑
- 为内部同进程的子 Agent 也上 A2A，徒增网络与运维复杂度。
- 信任远程 Agent 返回的内容并直接执行，需做输出校验和权限隔离。
- 不做超时与取消，远程长任务挂起拖垮调用方。

## 迁移
- 自定义的 Agent 间 HTTP 接口：对外暴露的部分改为 A2A，内部保留原接口。

## 最佳做法
- 先在一个跨团队场景小范围试点，验证可观测性和失败处理后再推广。

## CHANGELOG
- 2026-11-14 v1.0.0 首版；情报员自动核实（来源见 sources）
