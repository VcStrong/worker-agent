---
name: dify-coze
description: "Dify / Coze 低代码 AI 应用平台（成熟度 试用，as_of 2026-11-14）：AI 产品经理快速做可演示原型、验证 Prompt 和工作流。 适用角色：AI 产品经理、AI 应用 / Agent 工程师。"
---
<!-- generated-by: scripts/build.py；源文件 data/skills/ai-product/dify-coze.md，请勿手改 -->

> 成熟度：**试用**（region=cn）｜版本 1.0.0｜as_of 2026-11-14｜来源：https://github.com/langgenius/dify/releases https://github.com/coze-dev/coze-studio

# Dify / Coze 低代码 AI 应用平台

## 成熟度判断
- 试用：图谱原有工具。Dify 持续高频发版（GitHub Releases 最新 1.19.0，2026-11-04）；Coze 开源版 Coze Studio 最新 v0.5.1（2026-02），仍在 1.0 之前。适合原型和内部工具，核心生产链路仍建议代码实现。
- 风险：平台升级可能改变工作流行为；复杂逻辑难以测试和版本管理。回退方案：把验证过的工作流按图改写为代码（LangGraph / Agent SDK）。

## 什么时候用
- AI 产品经理快速做可演示原型、验证 Prompt 和工作流。
- 内部知识库问答、运营工具等低风险场景。

## 关键做法
- 私有化部署优先（Dify / Coze Studio 都可自托管），模型接已备案的国内模型。
- 工作流导出为 DSL 文件纳入 Git 管理，变更走评审。
- 平台内也要配评测集，改 Prompt 前后跑一遍。
- 对外发布到公众渠道前，按国内要求完成登记与内容标识。

## 常见坑
- 原型直接当生产，流量上来后性能、权限、审计跟不上。
- 平台里填的 API Key 权限过大，或多人共用一个 Key。
- 自托管版本长期不升级，积累安全漏洞。

## 迁移
- 原型 → 生产：保留工作流图作为需求，节点逐个改写为代码，评测集复用，对比效果一致后切流。

## 最佳做法
- 原型阶段就记录每个节点的输入输出样例，方便后续转代码和写评测。

## CHANGELOG
- 2026-11-14 v1.0.0 首版；情报员自动核实（来源见 sources）
