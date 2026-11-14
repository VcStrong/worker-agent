---
id: ga4
name: 埋点与用户行为分析（海外：Google Analytics 4 / Firebase Analytics）
aliases: [GA4, Google Analytics 4, Firebase Analytics, gtag, Measurement Protocol]
roles: [data-growth, product-manager]
maturity: 评估
maturity_by_region: {cn: 评估, global: 采用}
as_of: 2026-11-14
version: 1.0.0
sources:
  - https://developers.google.com/analytics/devguides/collection/ga4
  - https://developers.google.com/analytics/devguides/collection/protocol/ga4
region: global
replaces: []
replaced_by: []
from_graph: false
---

# 埋点与用户行为分析（海外：Google Analytics 4 / Firebase Analytics）

当前版本：GA4 为 Google 持续发布的 SaaS；Web 用 gtag.js / Google Tag Manager，App 用 Firebase SDK（Google Analytics for Firebase），服务端用 Measurement Protocol 补充。
判断理由：海外 Web / App 分析的事实标准、免费版功能充足、可导出 BigQuery，海外定「采用」；中国大陆无法稳定访问 Google 服务且涉及数据出境，国内定「评估」，默认用 sensors-growingio。

## 什么时候用
- 面向海外用户的网站、App 做流量、转化、留存分析。
- 投放归因需要和 Google Ads 打通。
- 需要原始事件数据进数仓（BigQuery 导出），配合 dbt 建模。

## 关键做法
- 事件模型：优先使用推荐事件（如 purchase、sign_up、add_to_cart）及其标准参数，自定义事件命名统一「对象_动作」。
- 关键转化标记为关键事件，自定义维度 / 指标在后台注册后才能在报表里使用。
- Measurement Protocol 只用于补充服务端事件（如退款、离线成交），不能替代客户端采集，也不能发送地理位置；部分保留事件名与参数不能使用。
- 开启 BigQuery 导出，复杂分析在数仓里做，GA4 界面看趋势。
- 欧盟等地区用户按当地要求接入同意管理（Consent Mode）。

## 常见坑
- 报表存在阈值与采样，小样本数据会被隐藏，精确分析用 BigQuery 导出。
- 数据保留期默认较短，上线第一天就调整保留设置并开导出。
- 前后端事件重复上报导致转化翻倍，用 transaction_id 去重。

## 迁移
- 国内外同一产品：国内包接 sensors-growingio，海外包接 GA4，事件字典保持同一份，用 dbt 统一口径。
- 从 Universal Analytics 遗留实现迁移：按事件模型重新设计，不要逐条照搬 pageview 思路。

## 最佳做法
- 每个版本发版前用 DebugView 验收关键事件。
- 风险与回退：若需撤出 Google 生态，依赖 BigQuery 历史导出保留数据，切到 posthog 等方案。

## CHANGELOG
- 2026-11-14 v1.0.0 首版；情报员自动核实（来源见 sources）
