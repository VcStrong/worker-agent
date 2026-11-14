---
name: hybrid-retrieval-rerank
description: "混合检索与重排（RAG）（成熟度 采用，as_of 2026-11-14）：企业知识库、客服、文档问答等 RAG 场景，尤其含产品型号、条款编号、人名等精确词。 适用角色：AI 应用 / Agent 工程师、模型与算法工程师。"
---
<!-- generated-by: scripts/build.py；源文件 data/skills/ai-app/hybrid-retrieval-rerank.md，请勿手改 -->

> 成熟度：**采用**（region=cn）｜版本 1.0.0｜as_of 2026-11-14｜来源：https://milvus.io/docs/multi-vector-search.md https://www.elastic.co/docs/solutions/search/hybrid-semantic-text

# 混合检索与重排（RAG）

## 成熟度判断
- 采用：Milvus（官方文档基于 v3.0.x）原生支持稠密 + 稀疏（内置 BM25 全文检索）多向量混合检索与 RRF / 加权融合；Elasticsearch 用 semantic_text + RRF retriever 一条请求完成混合检索。纯向量检索对专有名词、编号、代码召回差，混合检索已是 RAG 默认做法。

## 什么时候用
- 企业知识库、客服、文档问答等 RAG 场景，尤其含产品型号、条款编号、人名等精确词。
- 纯向量召回效果不达标、出现「找得到相似但找不到准确」时。

## 关键做法
- 两路召回：稠密向量（语义）+ BM25 / 稀疏向量（关键词），各取 Top 50~100。
- 融合：先用 RRF（无需调参，k 常用 60~100），有标注数据后再试加权融合。
- 重排：融合后 Top N 交给交叉编码器重排模型（如开源 bge-reranker 系列或云厂商 rerank API），取 Top 5~10 进 Prompt。
- 切块：按语义结构（标题、段落）切，保留标题路径和元数据，支持按权限 / 时间过滤。
- 评测：召回率@K、MRR、最终答案准确率分开测，定位问题在检索还是生成。

## 常见坑
- 中文 BM25 未配置合适分词器，关键词通道形同虚设。
- 重排候选太多拖慢时延，太少则重排无意义。
- 只调 Prompt 不看检索命中，问题根源在召回。
- 向量库没做权限过滤，越权检索到别人的文档（OWASP LLM08，见 owasp-llm-top10）。

## 迁移
- 纯向量 → 混合：在现有集合加稀疏字段或全文索引，离线对比召回率后上线。

## 最佳做法
- 维护 100~300 条「问题 → 应命中文档」标注集，每次改切块、模型、参数都回归。

## CHANGELOG
- 2026-11-14 v1.0.0 首版；情报员自动核实（来源见 sources）
