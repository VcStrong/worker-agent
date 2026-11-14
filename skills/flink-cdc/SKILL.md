---
name: flink-cdc
description: "Flink CDC（实时数据同步与入湖）（成熟度 采用，as_of 2026-11-14）：业务库 → OLAP（StarRocks / Doris）或湖仓（Paimon / Iceberg）的实时同步。 适用角色：后端工程师。"
---
<!-- generated-by: scripts/build.py；源文件 data/skills/backend/flink-cdc.md，请勿手改 -->

> 成熟度：**采用**（region=cn）｜版本 1.0.0｜as_of 2026-11-14｜来源：https://nightlies.apache.org/flink/flink-cdc-docs-stable/ https://github.com/apache/flink-cdc/releases https://flink.apache.org/

# Flink CDC（实时数据同步与入湖）

当前版本：Apache Flink CDC 3.7.0（2026-10-10），提供 Flink 1.20.x 与 Flink 2.2.x 两套构建，要求 JDK 11+。Pipeline 连接器覆盖 MySQL、PostgreSQL、Oracle、SQL Server、OceanBase、Kafka、Paimon、Iceberg、Hudi、Doris、StarRocks、Elasticsearch、MaxCompute、Fluss 等。
判断理由：Apache 官方子项目，版本节奏稳定，YAML Pipeline 支持整库同步和 Schema 演进，国内大规模生产使用，判「采用」。图谱数据开发原有 Flink，本技能补充 CDC 这一具体用法。

## 什么时候用
- 业务库 → OLAP（StarRocks / Doris）或湖仓（Paimon / Iceberg）的实时同步。
- 替代「定时全量抽取 + Sqoop / DataX」的 T+1 链路。
- 需要分库分表合并、整库同步、DDL 自动同步到下游。

## 关键做法
- 优先用 YAML Pipeline 作业（source / sink / route / transform）描述整库同步，减少手写 DataStream 代码。
- MySQL 源开启 binlog（ROW 格式、full row image），PG 源配置逻辑复制槽与 publication。
- 全量 + 增量无锁读取（增量快照），合理设 chunk 大小与并行度。
- 开启 checkpoint，sink 端用幂等 / 主键写入保证 exactly-once 语义。
- 新集群评估 Flink 2.2 构建；存量 1.20 集群用对应构建，不混用 jar。

## 常见坑
- PG 复制槽不消费会持续堆积 WAL，导致源库磁盘写满；作业停掉要清理槽。
- 上游 DDL 不受控（改列类型）导致下游写失败，需设置 Schema 演进策略（容忍 / 报错 / 忽略）。
- binlog 保留时间短于作业故障恢复时间，恢复时找不到位点。
- 连接器 jar 的 Flink 版本后缀与集群不一致直接报错。

## 迁移
- DataX / Canal + 自研消费 → Flink CDC：先对单库做全量 + 增量比对，确认行数与校验和一致再切。
- Flink 1.x → 2.x：先升 CDC 到同时提供双版本的 3.7，再单独评估 Flink 大版本升级。

## 最佳做法
- 同步作业统一监控：延迟（currentFetchEventTimeLag）、checkpoint 时长、源库复制槽 / binlog 积压。

## CHANGELOG
- 2026-11-14 v1.0.0 首版；情报员自动核实（来源见 sources）
