---
name: postgresql
description: "PostgreSQL 生态（18 / 19、pgvector、扩展）（成熟度 采用，as_of 2026-11-14）：新业务 OLTP、需要复杂查询 / JSONB / 地理信息 / 全文检索时，优先 PG。 适用角色：后端工程师、架构师 / 技术负责人。"
---
<!-- generated-by: scripts/build.py；源文件 data/skills/backend/postgresql.md，请勿手改 -->

> 成熟度：**采用**（region=cn）｜版本 1.0.0｜as_of 2026-11-14｜来源：https://www.postgresql.org/support/versioning/ https://www.postgresql.org/about/news/postgresql-19-rc-1-released-3409/ https://github.com/postgres/postgres/tags https://github.com/pgvector/pgvector

# PostgreSQL 生态（18 / 19、pgvector、扩展）

当前版本：PostgreSQL 18（最新补丁 18.7）为生产稳定线；PostgreSQL 19 已到 RC2，官方公告计划 2026-11-19 GA。每个大版本官方支持 5 年。图谱 DBA 工具原有「MySQL / PostgreSQL」。
判断理由：官方版本策略和发布节奏清晰，扩展生态（pgvector、PostGIS、逻辑复制）成熟，国内外云均有托管版，判「采用」。新项目用 18，19 等 .1/.2 补丁后再上生产。

## 什么时候用
- 新业务 OLTP、需要复杂查询 / JSONB / 地理信息 / 全文检索时，优先 PG。
- 中小规模向量检索（百万到千万级）：PG + pgvector，省掉一套向量库。
- 已大量使用 MySQL 且团队经验集中在 MySQL 的，不为换而换。

## 关键做法
- 托管优先：阿里云 RDS PostgreSQL / PolarDB、腾讯云 TencentDB、华为云 RDS、AWS RDS / Aurora；确认目标云已支持的大版本。
- 连接管理：应用侧连接池 + PgBouncer（事务模式），避免每请求建连。
- 18 起有异步 I/O（AIO），升级后复核 `io_method` 等参数与 I/O 指标。
- 向量：pgvector 用 HNSW 索引，按召回率 / 延迟调 `ef_search`；数据量过亿再评估专用向量库。
- 备份：基础备份 + WAL 归档（pgBackRest 或云托管 PITR），定期演练恢复。

## 常见坑
- 长事务阻止 VACUUM，表膨胀、事务 ID 回卷风险；监控 `xact_age` 与死元组。
- 大版本升级直接 `pg_dump` 停机太久：用 `pg_upgrade --link` 或逻辑复制蓝绿切换。
- 给每个查询加索引导致写放大；先看 `pg_stat_statements` 再定索引。
- 刚 GA 的大版本扩展兼容性（pgvector、PostGIS 等）可能滞后，升级前逐个确认。

## 迁移
- MySQL → PG：用 pgloader 或云厂商 DTS 迁移，重点检查大小写敏感、自增主键、隐式类型转换。
- 16 / 17 → 18：测试环境 `pg_upgrade --check`，再用逻辑复制做灰度切换。

## 最佳做法
- 每个实例默认开 `pg_stat_statements` 与慢查询日志，作为 DBA 与后端共同的性能基线。

## CHANGELOG
- 2026-11-14 v1.0.0 首版；情报员自动核实（来源见 sources）
