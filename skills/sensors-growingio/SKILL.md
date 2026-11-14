---
name: sensors-growingio
description: "埋点与用户行为分析（国内：神策 / GrowingIO）（成熟度 采用，as_of 2026-11-14）：国内 App / Web / 小程序的埋点、漏斗、留存、分群、路径分析。 适用角色：数据与增长运营、产品经理。"
---
<!-- generated-by: scripts/build.py；源文件 data/skills/data-growth/sensors-growingio.md，请勿手改 -->

> 成熟度：**采用**（region=cn）｜版本 1.0.0｜as_of 2026-11-14｜来源：https://manual.sensorsdata.cn/sa/latest/ https://github.com/sensorsdata/sa-sdk-android/releases https://github.com/growingio/growingio-sdk-android-autotracker/releases

# 埋点与用户行为分析（国内：神策 / GrowingIO）

当前版本：神策 Android SDK v6.9.9（2026-11-04）、iOS SDK v5.0.12（2026-09-02）；GrowingIO Android 无埋点 SDK v4.7.0（2026-10-29）。均可私有化部署。
判断理由：国内主流行为分析平台，SDK 持续更新、支持私有化与国内合规要求，国内定「采用」；海外项目默认 ga4，本方案定「评估」。图谱 P-01 / A-01 原有「神策 / GrowingIO」。

## 什么时候用
- 国内 App / Web / 小程序的埋点、漏斗、留存、分群、路径分析。
- 对数据驻留有要求，需要私有化部署。
- 需要把行为数据与实验平台、CDP、营销自动化打通。

## 关键做法
- 先写埋点方案再开发：事件名、触发时机、属性（名、类型、取值示例）、所属指标、负责人，放进 PRD 附录。
- 全埋点（自动采集点击 / 浏览）负责「广度」，代码埋点负责关键业务事件（下单、支付成功以服务端为准）。
- 用户标识：匿名 ID → 登录后 login 关联，统一 ID-Mapping 规则，避免一人多 ID。
- 上线前用 Debug 模式 / 埋点校验工具逐条验收，验收记录归档。
- 事件与属性在平台元数据里写中文名和口径，过期事件及时隐藏。

## 常见坑
- 隐私合规：SDK 必须在用户同意隐私政策后初始化，同意前不得采集设备标识；隐私政策中列明 SDK 名称、采集字段和目的（工信部 App 个人信息保护专项检查重点）。
- 全埋点事件量巨大，计费与存储成本高；按页面白名单或采样控制。
- 客户端时间不准、断网补发，导致数据延迟和时序错乱，分析时用服务端接收时间校验。

## 迁移
- 神策与 GrowingIO 互迁：先统一事件字典，双 SDK 并行 2~4 周对比核心指标，偏差 < 2% 再切换。
- 从自研日志迁移：保留服务端关键事件日志作为对账源。

## 最佳做法
- 每个版本发版清单加「埋点验收」项，未验收不得上线。
- 埋点变更走评审，记录版本号，看板注明口径生效版本。

## CHANGELOG
- 2026-11-14 v1.0.0 首版；情报员自动核实（来源见 sources）
