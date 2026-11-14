---
id: dbt
name: dbt（数据建模与转换）
aliases: [dbt, dbt Core, dbt Fusion, data build tool, 数仓建模, ELT]
roles: [data-growth, backend-engineer]
maturity: 采用
as_of: 2026-11-14
version: 1.0.0
sources:
  - https://docs.getdbt.com/
  - https://github.com/dbt-labs/dbt/releases
  - https://docs.getdbt.com/docs/fusion/fusion-availability
region: both
replaces: []
replaced_by: []
from_graph: false
---

# dbt（数据建模与转换）

当前版本：dbt Core v1.12.7（2026-11-12，GitHub 仓库已更名为 dbt-labs/dbt）；新引擎 dbt Fusion 目前仅在 dbt 平台 + Snowflake 上 GA，其他适配器为预览。
判断理由：数仓 SQL 建模的事实标准，开源 Core 稳定、适配器覆盖主流数仓，定「采用」；Fusion 引擎按适配器分别评估，暂不作为默认。

## 什么时候用
- 指标、看板背后的数仓表（DWD / DWS / ADS）用 SQL 建模，需要版本管理、测试、文档、血缘。
- 数据分析师要自助维护口径，而不是每次找数据开发写调度脚本（图谱 A-01 的 SQL / Hive 工作流的工程化升级）。
- 需要统一指标口径时，配合指标层（见 metrics-semantic-layer）。

## 关键做法
- 分层：staging（清洗、改名）→ intermediate（业务逻辑）→ marts（面向主题的宽表 / 指标表），每层命名前缀统一。
- 每个模型写 `schema.yml`：描述、字段说明、数据测试（unique、not_null、accepted_values、relationships）。
- 大表用增量模型（incremental），分区字段与数仓分区一致。
- CI 里只构建变更模型及其下游（state:modified+），合并前跑测试。
- 国内数仓：确认适配器支持（如 StarRocks / Doris / MaxCompute / Hive / Spark 等社区或厂商适配器），先小范围验证 SQL 方言与增量策略。

## 常见坑
- 把 dbt 当调度器：调度仍交给 Airflow / DolphinScheduler / 云调度，dbt 只负责转换。
- 社区适配器成熟度参差，宏和增量策略可能不支持，选型时先跑完整用例。
- 模型间循环引用、过度拆分导致 DAG 难以维护。

## 迁移
- 从「调度平台里散落的 SQL 脚本」迁移：先把 ADS 层报表 SQL 收进 dbt，补测试和文档，再向下迁 DWS / DWD。
- 从 dbt Core 迁移到 Fusion：先在非生产环境按官方就绪清单检查废弃写法，再按适配器 GA 情况切换。

## 最佳做法
- 每个对外指标表必须有负责人（meta.owner）和数据测试，测试失败阻断下游看板刷新。
- 风险与回退：适配器问题时保留原调度 SQL 作为回退路径，直到 dbt 版本稳定运行两个周期。

## CHANGELOG
- 2026-11-14 v1.0.0 首版；情报员自动核实（来源见 sources）
