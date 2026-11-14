---
name: starrocks-doris
description: "实时 OLAP（StarRocks / Apache Doris）（成熟度 采用，as_of 2026-11-14）：实时报表、用户画像、运营看板、Ad-hoc 分析，需要多表 Join 和高并发查询。 适用角色：后端工程师、架构师 / 技术负责人。"
---
<!-- generated-by: scripts/build.py；源文件 data/skills/backend/starrocks-doris.md，请勿手改 -->

> 成熟度：**采用**（region=cn）｜版本 1.0.0｜as_of 2026-11-14｜来源：https://docs.starrocks.io/ https://github.com/StarRocks/starrocks/releases https://doris.apache.org/releases/all-release/ https://doris.apache.org/releases/v4.0/release-4.0.0/

# 实时 OLAP（StarRocks / Apache Doris）

当前版本：StarRocks 4.1.7（2026-10，4.0.x 仍维护）；Apache Doris 4.1.5（2026-10），4.0 起内置向量检索（HNSW / IVF）、AI 函数和 BM25 全文检索。
判断理由：两者均为 MySQL 协议兼容的 MPP 引擎，国内互联网大规模生产使用，发布与文档活跃，支持存算分离和直查 Iceberg / Paimon / Hive，判「采用」。图谱原有 ClickHouse，本技能是补充，不替代 ClickHouse。

## 什么时候用
- 实时报表、用户画像、运营看板、Ad-hoc 分析，需要多表 Join 和高并发查询。
- 湖仓查询加速：Catalog 直查 Iceberg / Paimon，热数据再落内表。
- 选型：已有 ClickHouse 且以单大宽表日志分析为主可继续用；多表关联、更新频繁、MySQL 协议接入优先 StarRocks / Doris。两者能力接近，按团队经验和云托管情况选一个，不要同时引入。

## 关键做法
- 表模型：明细（Duplicate）、聚合、主键 / Unique（支持实时 upsert），按查询模式选。
- 分区 + 分桶：按时间分区、高基数列分桶，避免数据倾斜。
- 导入：Flink CDC / Routine Load / Stream Load 实时入库；离线用 Broker Load 或 INSERT FROM Catalog。
- 存算分离模式（对象存储 + 本地缓存）降成本，冷热分层。
- 物化视图做查询改写加速，替代人工维护汇总表。

## 常见坑
- 分桶过多或过少：小文件 / 单 tablet 过大，查询与 compaction 都变慢。
- 高频小批量写入未攒批，导致版本过多报错（too many versions）。
- 主键表全部常驻内存的旧配置，内存吃紧；新版用持久化主键索引。
- 混用两个引擎的方言与函数，迁移时 SQL 不兼容。

## 迁移
- ClickHouse / Hive 报表迁移：先建 Catalog 直查验证结果一致，再逐步把高频报表落内表。
- 3.x → 4.x 滚动升级前看官方升级说明与行为变更（如 4.1.7 的 compaction 开关默认值调整）。

## 最佳做法
- 给每个业务方建资源组 / Workload Group，限制大查询拖垮集群。

## CHANGELOG
- 2026-11-14 v1.0.0 首版；情报员自动核实（来源见 sources）
