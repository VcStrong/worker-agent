---
name: generative-recommendation
description: "生成式推荐（成熟度 评估，as_of 2026-11-14）：大规模推荐（千万级 DAU、长用户行为序列）且现有级联系统遇到效果瓶颈时做预研。 适用角色：模型与算法工程师。"
---
<!-- generated-by: scripts/build.py；源文件 data/skills/ai-model/generative-recommendation.md，请勿手改 -->

> 成熟度：**评估**（region=cn）｜版本 1.0.0｜as_of 2026-11-14｜来源：https://github.com/meta-recsys/generative-recommenders https://arxiv.org/abs/2402.17152 https://arxiv.org/abs/2506.13695 https://github.com/Kuaishou-OneRec/OpenOneRec

# 生成式推荐

## 成熟度判断
- 评估：Meta 的 HSTU（ICML'24 论文与官方代码 meta-recsys/generative-recommenders）、快手 OneRec 技术报告（用单一生成模型替代召回-粗排-精排级联，报告称已承担约 25% 流量）均来自一线公司一手发布，并有开源 OpenOneRec。但工程门槛高（算力、语义 ID、在线服务），中小团队复现案例少，只进技术方案对比，不直接进生产。

## 什么时候用
- 大规模推荐（千万级 DAU、长用户行为序列）且现有级联系统遇到效果瓶颈时做预研。
- 技术方案中与传统「双塔召回 + 精排」做对比评估。

## 关键做法
- 两条路线：序列生成式排序（HSTU 类，把行为序列当序列建模）与端到端生成（OneRec 类，直接生成物品语义 ID）。
- 语义 ID：用 RQ-VAE 等把物品向量量化成离散 Token，是端到端路线的基础。
- 先离线：在自有日志上对比 NDCG / Recall 与现有模型，再评估训练与推理算力成本。
- 小流量 A/B：保留原级联系统作兜底，按流量分桶对比时长、点击、多样性。

## 常见坑
- 只看论文收益，忽略推理时延与 GPU 成本，在线无法承受。
- 新物品冷启动、语义 ID 冲突处理不当。
- 生成结果多样性下降、出现重复推荐。

## 迁移
- 不建议整体替换；先在召回或精排的某一路引入生成式模型，作为新增通道评估。

## 最佳做法
- 评估报告写清：数据规模、算力预算、离线指标、在线 A/B 计划与回滚方案。

## CHANGELOG
- 2026-11-14 v1.0.0 首版；情报员自动核实（来源见 sources）
