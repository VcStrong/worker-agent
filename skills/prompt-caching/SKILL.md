---
name: prompt-caching
description: "Prompt 缓存（上下文缓存）（成熟度 采用，as_of 2026-11-14）：长系统提示词、工具定义、知识文档、多轮对话、Agent 循环等「前缀反复出现」的场景。 适用角色：AI 应用 / Agent 工程师、AI Infra / MLOps 工程师。"
---
<!-- generated-by: scripts/build.py；源文件 data/skills/ai-app/prompt-caching.md，请勿手改 -->

> 成熟度：**采用**（region=cn）｜版本 1.0.0｜as_of 2026-11-14｜来源：https://platform.claude.com/docs/en/build-with-claude/prompt-caching https://developers.openai.com/api/docs/guides/prompt-caching https://api-docs.deepseek.com/quick_start/pricing https://docs.volcengine.com/docs/82379/1330310

# Prompt 缓存（上下文缓存）

## 成熟度判断
- 采用：主流供应商都已提供，且是最直接的降本降时延手段。
- 官方要点（2026-11）：Claude 支持自动缓存（顶层 cache_control）和最多 4 个显式断点，TTL 5 分钟（写 1.25 倍）或 1 小时（写 2 倍），读 0.1 倍（Opus 5.5 / Sonnet 5.5 为 0.05 倍）；OpenAI 默认开启，新模型 TTL 30 分钟或 12 小时，读 0.1 倍；DeepSeek 默认开启，按命中 / 未命中分价；火山方舟、阿里云百炼提供上下文缓存。

## 什么时候用
- 长系统提示词、工具定义、知识文档、多轮对话、Agent 循环等「前缀反复出现」的场景。
- 首字时延敏感、输入远大于输出的应用。

## 关键做法
- Prompt 顺序：不变的放前面（工具 → 系统提示 → 固定文档 → 历史对话），变化的放最后。
- Claude：多轮对话用自动缓存；不同更新频率的段落用显式断点分开。
- 监控命中：Claude 看 cache_read_input_tokens / cache_creation_input_tokens；OpenAI 看 usage.input_tokens_details.cached_tokens。
- 低于最小可缓存长度（Claude 新模型 512 Token、OpenAI 1024 Token）不会缓存，也不报错。
- 自部署模型同理开启前缀缓存（vLLM prefix caching、SGLang RadixAttention）。

## 常见坑
- 在前缀里放时间戳、用户 ID、随机示例，导致每次都不命中。
- 修改工具定义会使 Claude 全部缓存失效；切换思考配置、增删图片也会使部分缓存失效。
- 工具调用 JSON 键顺序不稳定（某些语言随机化），破坏前缀一致。
- 低频请求用 1 小时 TTL，写入溢价反而更贵。

## 迁移
- 旧代码每次拼接动态内容在前：调整顺序，先做一次命中率基线再优化。

## 最佳做法
- 把缓存命中率作为线上指标（目标 > 70%），掉线时告警（见 llm-cost-monitoring）。

## CHANGELOG
- 2026-11-14 v1.0.0 首版；情报员自动核实（来源见 sources）
