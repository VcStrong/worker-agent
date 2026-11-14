---
name: lakehouse-iceberg-paimon
description: "湖仓表格式（Apache Iceberg / Apache Paimon）（成熟度 试用，as_of 2026-11-14）：图谱原有 Hive / Spark / Flink 离线数仓，想要 ACID、Schema 演进、时间旅行、多引擎共享同一份数据。 适用角色：后端工程师、架构师 / 技术负责人。"
---
<!-- generated-by: scripts/build.py；源文件 data/skills/backend/lakehouse-iceberg-paimon.md，请勿手改 -->

> 成熟度：**试用**（region=cn）｜版本 1.0.0｜as_of 2026-11-14｜来源：https://iceberg.apache.org/spec/ https://github.com/apache/iceberg/releases https://paimon.apache.org/ https://github.com/apache/paimon/releases

# 湖仓表格式（Apache Iceberg / Apache Paimon）

当前版本：Apache Iceberg 1.12.0（2026-09-30），表格式规范已有 v1 / v2 / v3（扩展类型与能力），v4 在规范中定义中；Apache Paimon 2.1.0（2026-10-12，2.0.0 于 2026-08 发布）。
判断理由：两者都是 Apache 顶级项目、发布活跃；但湖仓需要配套 Catalog、计算引擎、小文件治理，团队投入大，且 Iceberg v3 新特性在各引擎的支持程度不一，判「试用」。风险：引擎版本兼容与运维复杂度；回退方案：保留原 Hive 表 / 数仓链路双写，验证后再下线。

## 什么时候用
- 图谱原有 Hive / Spark / Flink 离线数仓，想要 ACID、Schema 演进、时间旅行、多引擎共享同一份数据。
- Iceberg：以批 / 交互查询为主、多引擎（Spark、Flink、Trino、StarRocks、Doris）共享，生态最广。
- Paimon：以 Flink 实时入湖、主键表高频 upsert、流读流写为主（源自 Flink Table Store）。

## 关键做法
- 先定 Catalog：Iceberg REST Catalog / Hive Metastore / 云厂商托管（阿里云 DLF、AWS Glue / S3 Tables）。
- 新表 Iceberg 用 format-version 2，确认所有读写引擎都支持后再升 v3。
- Paimon 主键表按数据量设 bucket，合理配置 compaction；Iceberg 定期 `rewrite_data_files`、`expire_snapshots`。
- 实时入湖链路：Flink CDC → Paimon / Iceberg（见 `flink-cdc`），分析层用 StarRocks / Doris 直查（见 `starrocks-doris`）。

## 常见坑
- 不做小文件合并与快照过期，元数据膨胀，查询越来越慢。
- 多个引擎版本对表格式版本支持不一致，升了 v3 后旧引擎读不了。
- 把湖仓当 OLTP 用：高并发点查仍应走数据库或 OLAP 引擎。

## 迁移
- Hive 表 → Iceberg：用 Spark 的 `migrate` / `snapshot` 过程原地迁或影子表验证。
- 双写 / 双跑一个周期，核对行数和关键指标一致后切读，再下线旧表。

## 最佳做法
- 先选一个业务域试点（如埋点明细），跑通治理（合并、过期、权限）后再推广。

## CHANGELOG
- 2026-11-14 v1.0.0 首版；情报员自动核实（来源见 sources）
