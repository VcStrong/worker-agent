---
name: llm-cost-monitoring
description: "推理成本与用量监控（成熟度 采用，as_of 2026-11-14）：任何上线的大模型功能（API 或自部署）。 适用角色：AI Infra / MLOps 工程师、AI 产品经理。"
---
<!-- generated-by: scripts/build.py；源文件 data/skills/ai-infra/llm-cost-monitoring.md，请勿手改 -->

> 成熟度：**采用**（region=cn）｜版本 1.0.0｜as_of 2026-11-14｜来源：https://github.com/open-telemetry/semantic-conventions-genai https://docs.litellm.ai/docs/ https://platform.claude.com/docs/en/build-with-claude/prompt-caching https://developers.openai.com/api/docs/guides/prompt-caching

# 推理成本与用量监控

## 成熟度判断
- 采用：各家 API 响应都返回分项用量（输入、缓存读、缓存写、输出），网关（LiteLLM / Higress）原生按 Key / 团队 / 模型统计花费，做法成熟。
- 注意：OpenTelemetry 的 GenAI 语义约定已迁到独立仓库 open-telemetry/semantic-conventions-genai，仍在演进，属性名可能变化；采用其命名时要锁版本并做映射层。

## 什么时候用
- 任何上线的大模型功能（API 或自部署）。
- 账单异常、需要按业务线分摊成本、评估降本措施效果时。

## 关键做法
- 每次调用记录：业务线、功能、模型、供应商、输入 / 缓存读 / 缓存写 / 输出 / 思考 Token、时延（TTFT、总时长）、是否回退、请求 ID。
- 统一在网关采集，按价目表实时折算金额；价目表配置化并按官方定价页更新。
- 看板：日花费趋势、单用户 / 单次成本、缓存命中率、各模型占比、Top 消耗功能。
- 告警：日花费超预算 X%、单用户异常调用（滥用 / 刷量，对应 OWASP LLM10 无界消耗）、缓存命中率骤降。
- 自部署：GPU 利用率、KV Cache 使用率、每千 Token 成本（GPU 小时价 / 吞吐）。

## 常见坑
- 只统计总账单，不知道钱花在哪个功能。
- 漏算思考 Token、工具调用费（搜索、代码执行）。
- 日志里存全量 Prompt 和回答，存储成本与隐私风险双高；用量指标和内容日志分开存，内容抽样且脱敏。

## 迁移
- 月底看供应商账单 → 实时计量：先在网关打通用量采集，再接告警，最后做分摊报表。

## 最佳做法
- 每月把实际单次成本回填 AI 成本测算表（见 llm-cost-estimation），偏差 > 20% 要复盘。

## CHANGELOG
- 2026-11-14 v1.0.0 首版；情报员自动核实（来源见 sources）
