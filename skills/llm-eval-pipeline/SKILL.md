---
name: llm-eval-pipeline
description: "LLM 评测（离线评测集 + 线上回放）（成熟度 采用，as_of 2026-11-14）：改 Prompt、换模型 / 供应商、改检索、升级推理引擎或量化之前（回归门禁）。 适用角色：AI 评测与安全合规专家、AI 应用 / Agent 工程师、AI 产品经理。"
---
<!-- generated-by: scripts/build.py；源文件 data/skills/ai-eval/llm-eval-pipeline.md，请勿手改 -->

> 成熟度：**采用**（region=cn）｜版本 1.0.0｜as_of 2026-11-14｜来源：https://platform.claude.com/docs/en/test-and-evaluate/develop-tests https://developers.openai.com/api/docs/guides/evaluation-best-practices https://github.com/vibrantlabsai/ragas/releases https://mlflow.org/docs/latest/

# LLM 评测（离线评测集 + 线上回放）

## 成熟度判断
- 采用：Anthropic、OpenAI 官方都把「评测驱动开发」作为标准流程：任务专属评测集、尽量自动打分、LLM 评审需与人工标注校准、每次变更都跑。
- 工具提醒：OpenAI 托管 Evals 平台 2026-10-31 只读、2026-11-30 关停；开源可选 Ragas（RAG 评测，最新 v0.4.4）、MLflow 评测、自建脚本。

## 什么时候用
- 改 Prompt、换模型 / 供应商、改检索、升级推理引擎或量化之前（回归门禁）。
- 上线后发现新问题，要防止复发时。

## 关键做法
- 离线评测集：来源混合（真实日志抽样、专家编写、合成数据），覆盖典型 / 边界 / 对抗样本；按功能分层，持续增量。
- 打分方式按可自动化程度选：精确匹配 / 规则 / Schema 校验 → 相似度类 → LLM 评审（Likert 或二分类，先推理后打分）→ 人工抽检。
- LLM 评审：评审模型与被测模型不同；控制位置偏差和长度偏差；先用 50~100 条人工标注验证一致性再规模化。
- 线上回放：脱敏抽样真实请求，在新版本上重放并与线上版本对比（A/B 胜率、退化样本清单），不影响真实用户。
- 线上监控：点踩、人工接管、拒答率、安全拦截率；失败样本回流进评测集。
- 门禁：CI 中跑评测，关键指标低于阈值或较基线下降超过阈值则阻断上线。

## 常见坑
- 评测集只有几十条「看着行」，统计上无意义。
- 评测集泄漏进 Prompt 示例或微调数据，分数虚高。
- 线上回放用未脱敏的原始用户数据，违反个人信息保护要求。
- 只测质量不测安全，越狱 / 注入样本缺失（见 owasp-llm-top10）。

## 迁移
- OpenAI 托管 Evals 用户：导出数据集与评分配置，迁到自建脚本 + MLflow / Ragas，11-30 前完成。

## 最佳做法
- 每个评测集写清：版本、样本来源、标注规则、通过阈值、负责人。

## CHANGELOG
- 2026-11-14 v1.0.0 首版；情报员自动核实（来源见 sources）
