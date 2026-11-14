---
id: metrics-semantic-layer
name: 指标平台 / 语义层（dbt Semantic Layer · MetricFlow / 阿里云 Dataphin）
aliases: [指标平台, 指标中台, 语义层, Semantic Layer, MetricFlow, Dataphin, 原子指标, 派生指标]
roles: [data-growth, backend-engineer]
maturity: 试用
maturity_by_region: {cn: 试用, global: 试用}
as_of: 2026-11-14
version: 1.0.0
sources:
  - https://docs.getdbt.com/docs/use-dbt-semantic-layer/dbt-sl
  - https://github.com/dbt-labs/metricflow/releases
  - https://www.getdbt.com/blog/dbt-labs-affirms-commitment-to-open-semantic-interchange-by-open-sourcing-metricflow
  - https://help.aliyun.com/zh/dataphin/
  - https://help.aliyun.com/zh/document_detail/2781772.html
region: both
replaces: []
replaced_by: []
from_graph: false
---

# 指标平台 / 语义层（dbt Semantic Layer · MetricFlow / 阿里云 Dataphin）

当前版本：MetricFlow v0.213.0（2026-09-10）；自 0.209.0 起改为 Apache 2.0 开源（2025-10 宣布）。dbt Semantic Layer 需 dbt Starter / Enterprise / Enterprise+ 套餐。阿里云 Dataphin 为 SaaS / 半托管持续发布，提供原子指标、派生指标等规范定义。
判断理由：统一口径价值明确，但需要数仓建模基础与组织流程配合，落地成本高，国内外均定「试用」。region=cn 默认 Dataphin（或企业已有的国内指标平台），global 默认 dbt Semantic Layer。

## 什么时候用
- 同一个指标（DAU、GMV、留存）在不同看板数字对不上，需要「一处定义、处处一致」。
- 要让 BI、实验平台、AI 问数（ChatBI / MCP）使用受治理的指标，而不是直接查原始表。
- 指标数量多（上百个），需要指标目录、负责人和变更记录。

## 关键做法
- 指标拆解：原子指标（口径 + 算法）+ 业务限定 + 统计周期 + 维度 = 派生指标（Dataphin 规范建模的公式），先在指标字典里写清再实现。
- dbt 方案：在 dbt 模型上定义 semantic models 与 metrics，由 MetricFlow 生成多方言 SQL；下游通过 Semantic Layer API、BI 集成或 dbt MCP server 查询。
- 指标定义进版本库，变更走评审，记录生效日期并通知看板负责人。
- 北极星指标与核心护栏指标优先纳入，长尾指标逐步迁入。

## 常见坑
- 先建平台、后理口径，结果平台里堆满重复指标；先做指标盘点与去重。
- 维度表质量差（如用户维度缺失）会让派生指标不可用，先补齐数仓公共层。
- 托管语义层的服务层与 API 不随 MetricFlow 一起开源，自建时需自行解决查询服务与权限。

## 迁移
- 从「各看板自写 SQL」迁移：按指标重要度分批收口，旧看板加「口径已迁移」标记，并行核对两周后下线旧 SQL。

## 最佳做法
- 每个指标必须有：业务定义、计算 SQL / 定义文件、负责人、更新频率、关联看板。
- 合规（国内）：指标明细涉及个人信息时按最小必要原则做脱敏与权限分级。

## CHANGELOG
- 2026-11-14 v1.0.0 首版；情报员自动核实（来源见 sources）
