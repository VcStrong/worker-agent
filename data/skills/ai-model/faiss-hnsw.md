---
id: faiss-hnsw
name: 向量检索（Faiss / HNSW）
aliases: [Faiss, HNSW, IVF, PQ, ANN, 近似最近邻, 向量索引, RaBitQ]
roles: [model-algorithm-engineer, ai-app-engineer]
maturity: 采用
as_of: 2026-11-14
version: 1.0.0
sources:
  - https://github.com/facebookresearch/faiss/wiki/Guidelines-to-choose-an-index
  - https://github.com/facebookresearch/faiss/releases
region: both
replaces: []
replaced_by: []
from_graph: true
---

# 向量检索（Faiss / HNSW）

## 成熟度判断
- 采用：图谱原有工具。Faiss 持续维护（最新 v1.16.0，2026-11-10），官方索引选型指南新增 RaBitQ、SVS Vamana 等选项；HNSW 仍是内存充足时的默认图索引，Milvus 等向量库底层也提供同类索引。

## 什么时候用
- 推荐召回、以图搜图、去重、RAG 向量召回等近似最近邻检索。
- 需要嵌入到自研服务、离线批量检索，或对索引参数做精细控制时用 Faiss；需要增删改、过滤、分布式和运维能力时用向量数据库（Milvus / pgvector 等）。

## 关键做法
- 按官方指南选索引：搜索次数少或要精确结果 → Flat；内存充足 → HNSW（M 取 4~64，efSearch 调速度与精度）；内存紧 → IVF + PQ / OPQ；极致压缩 → RaBitQ。
- 数据规模定 IVF 聚类数：百万以下 K 取 4√N~16√N；千万到十亿级用 IVF65536_HNSW32 起步逐级放大。
- GPU 支持 Flat、IVF-Flat、PQ；HNSW、RaBitQ 不支持 GPU，GPU 上改用 IVF。
- 归一化后用内积等价余弦；建库与查询使用同一 Embedding 模型版本。
- 用召回率@K 对比精确检索结果，确定参数，再压测 QPS 与 P99。

## 常见坑
- HNSW 不擅长删除和频繁更新，需定期重建或改用向量库。
- 训练 IVF 的样本太少或分布与线上不同，召回率掉。
- Embedding 模型升级后未重建索引，新旧向量混用。
- 只看速度不量召回率。

## 迁移
- 自建 Faiss 服务 → 向量数据库：当出现过滤、实时更新、多副本需求时迁移，索引参数可平移。
- RAG 场景纯向量 → 混合检索（见 hybrid-retrieval-rerank）。

## 最佳做法
- 索引配置、Embedding 模型版本、召回率基线一起记录，变更必须回归。

## CHANGELOG
- 2026-11-14 v1.0.0 首版；情报员自动核实（来源见 sources）
