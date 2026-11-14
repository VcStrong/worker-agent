---
id: llm-providers-global
name: 海外大模型供应商选型（Claude / OpenAI / Gemini）
aliases: [海外大模型, Claude, Anthropic, OpenAI, GPT, Gemini, Google AI Studio]
roles: [ai-product-manager, ai-app-engineer, ai-infra-mlops]
maturity: 采用
maturity_by_region: {cn: 评估, global: 采用}
as_of: 2026-11-14
version: 1.0.0
sources:
  - https://platform.claude.com/docs/en/about-claude/models/overview
  - https://developers.openai.com/api/docs/models
  - https://aistudio.google.com/docs/models
region: global
replaces: []
replaced_by: []
from_graph: false
---

# 海外大模型供应商选型

## 成熟度判断
- region=global 采用：三家都有稳定 API、官方模型生命周期承诺和退役时间表。
- region=cn 评估：海外模型未在国内备案，不能直接向境内公众提供生成式 AI 服务；境内团队只可用于调研对比、或面向海外用户的业务。
- 当前版本（官方页 2026-11-14 核实）：Anthropic 主推 Claude Opus 5.5，另有 Fable 5.2（高难推理）、Sonnet 5.5、Haiku 5.5，1M 上下文；OpenAI 旗舰为 gpt-6-astra，另有 gpt-6.1-sol / terra、gpt-6-luna；Google 稳定版含 gemini-3.8-flash 等，Gemini 4 系列以官方页标注为准。

## 什么时候用
- 出海产品、海外用户为主的服务（默认）。
- 国内团队做技术调研、能力上限对比、内部研发效能工具（需符合公司数据外发规定）。

## 关键做法
- 选型维度同国内：自家评测集效果 → 价格（缓存读价、Batch 五折）→ 时延 → 能力 → 数据驻留与合规（GDPR、EU AI Act，见 eu-ai-act）。
- 按任务分档：路由 / 分类 / 抽取用轻量档，复杂推理与长链路 Agent 用旗舰档。
- 关注官方模型退役日期，提前用迁移指南验证新模型。
- 通过云厂商托管渠道（如 Bedrock、Google Cloud、Microsoft Foundry）接入时，模型 ID、生命周期和缓存能力可能与官方 API 不同，以对应渠道文档为准。

## 常见坑
- 模型 ID 写死不跟踪退役公告，到期调用失败。
- 把境内用户流量打到海外模型，触发备案与数据出境问题。
- 不同模型分词器不同，同一文本 Token 数不同，成本估算要按目标模型重算。

## 迁移
- 国内项目出海：在网关层新增海外路由，评测集复用，按地域分流。
- 跨代升级：先在评测集上跑新旧模型对比，再灰度切流。

## 最佳做法
- 供应商与模型 ID 配置化，按 region 切默认值。

## CHANGELOG
- 2026-11-14 v1.0.0 首版；情报员自动核实（来源见 sources）
