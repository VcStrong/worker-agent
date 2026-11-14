---
name: llm-cost-estimation
description: "AI 成本估算（成熟度 采用，as_of 2026-11-14）：PRD「AI 机会评估」、立项 ROI、定价与套餐设计时。 适用角色：AI 产品经理、AI Infra / MLOps 工程师。"
---
<!-- generated-by: scripts/build.py；源文件 data/skills/ai-product/llm-cost-estimation.md，请勿手改 -->

> 成熟度：**采用**（region=cn）｜版本 1.0.0｜as_of 2026-11-14｜来源：https://platform.claude.com/docs/en/about-claude/models/overview https://platform.claude.com/docs/en/build-with-claude/prompt-caching https://developers.openai.com/api/docs/guides/prompt-caching https://api-docs.deepseek.com/quick_start/pricing

# AI 成本估算

## 成熟度判断
- 采用：各家官方定价都按「每百万 Token 输入 / 输出」计价，并单列缓存读写价、Batch 折扣、峰谷价，估算方法稳定。
- 2026-11 官方要点：Claude 缓存读为基础输入价 0.1 倍（Opus 5.5 / Sonnet 5.5 为 0.05 倍），Batch 五折；OpenAI 新模型缓存读 0.1 倍；DeepSeek 区分缓存命中 / 未命中并有峰谷价（谷时半价）。具体数字以官方定价页为准，不要抄进文档长期使用。

## 什么时候用
- PRD「AI 机会评估」、立项 ROI、定价与套餐设计时。
- 选型对比、上线前容量规划、账单异常复盘。

## 关键做法
- 单次成本 = 未缓存输入 × 输入价 + 缓存读 × 缓存读价 + 缓存写 × 缓存写价 + 输出 × 输出价（含思考 Token）+ 工具调用费（如联网搜索按次计费）。
- 月成本 = 单次成本 × 每用户日均次数 × DAU × 30 × 重试系数（一般 1.1~1.3）。
- Agent 按「平均轮数 × 每轮上下文增长」估，长任务成本常是单轮的 10 倍以上。
- 输入用真实样本按目标模型分词器计数，不用「1 字 ≈ 1 Token」拍脑袋。
- 降本杠杆：Prompt 缓存、模型分档路由、Batch（非实时任务）、限制输出长度、谷时跑批（DeepSeek）、自部署（见 vllm-sglang）。
- 给出三档情景（保守 / 预期 / 爆发）和单用户成本上限，超限触发降级。

## 常见坑
- 忽略思考 Token 和多轮上下文累积，低估 3~10 倍。
- 只算模型费，漏掉向量库、网关、日志存储、人工审核。
- 自部署只算 GPU 价，忽略利用率（低流量时远贵于 API）。

## 迁移
- 从「拍一个单价」改为成本测算表：输入分布、输出分布、缓存命中率、模型分档比例四个参数可调。

## 最佳做法
- 上线后用实际计量数据（见 llm-cost-monitoring）每月校准测算表。

## CHANGELOG
- 2026-11-14 v1.0.0 首版；情报员自动核实（来源见 sources）
