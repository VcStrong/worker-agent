---
id: llm-gateway-routing
name: 模型网关与路由
aliases: [模型 API 网关, AI 网关, LLM Gateway, LiteLLM, Higress, 模型路由, Fallback]
roles: [ai-infra-mlops, ai-app-engineer]
maturity: 采用
as_of: 2026-11-14
version: 1.0.0
sources:
  - https://docs.litellm.ai/docs/
  - https://github.com/BerriAI/litellm/releases
  - https://higress.cn/en/docs/ai/quick-start
  - https://github.com/higress-group/higress/releases
region: both
replaces: []
replaced_by: []
from_graph: true
---

# 模型网关与路由

## 成熟度判断
- 采用：图谱原有「模型 API 网关」。开源 LiteLLM（最新 v1.109.1，2026-11-12）提供统一 OpenAI 格式、路由与回退、负载均衡、虚拟 Key、按 Key / 团队 / 用户的预算与花费统计；Higress AI 网关（最新 v2.2.6，2026-11-10）支持通义、DeepSeek、豆包、OpenAI 等多供应商代理、Token 故障转移、Token 限流、语义缓存、AI 看板，并可托管远程 MCP Server。
- 国内默认 Higress（或阿里云 AI 网关企业版），海外 / Python 团队常用 LiteLLM，两者都可。

## 什么时候用
- 接入两家以上模型供应商、自部署模型与 API 混用。
- 需要统一鉴权、配额、成本归集、审计、内容安全过滤。

## 关键做法
- 应用只调网关的 OpenAI 兼容接口，模型名用逻辑别名（如 chat-default、chat-cheap），映射在网关配置。
- 路由策略：按任务难度分档（轻量模型优先、复杂再升级）、按地域（cn / global）、按成本或时延。
- 回退：主模型超时 / 限流 / 5xx 时切备用，带重试上限；记录切换事件。
- 每个业务方独立 Key + 预算 + 限流（按 Token 计），超预算降级或拒绝。
- 网关统一做输入输出安全检查（敏感词、提示词注入检测）和日志脱敏。

## 常见坑
- 回退到能力差异大的模型却不告诉调用方，结构化输出等功能静默失效。
- 网关成单点，未做多副本和健康检查。
- 日志全量记录用户原文，违反个人信息最小化（见 pipl-compliance-audit）。
- 语义缓存命中错误答案，对时效性和个性化问题要关闭。

## 迁移
- 应用直连各家 SDK → 网关：先把 base_url 指向网关并透传，再逐步启用路由与配额。

## 最佳做法
- 网关指标（各模型调用量、错误率、Token、花费）直接作为成本监控的数据源（见 llm-cost-monitoring）。

## CHANGELOG
- 2026-11-14 v1.0.0 首版；情报员自动核实（来源见 sources）
