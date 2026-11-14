---
name: posthog
description: "PostHog（产品分析 + 实验 + 会话回放）（成熟度 评估，as_of 2026-11-14）：海外产品要用一套工具搞定埋点分析、漏斗、Feature Flag、A/B 实验和会话回放（替代图谱 P-03「行为回放工具」+ G-04「实验平台」的组合）。 适用角色：产品经理、数据与增长运营。"
---
<!-- generated-by: scripts/build.py；源文件 data/skills/product/posthog.md，请勿手改 -->

> 成熟度：**评估**（region=cn）｜版本 1.0.0｜as_of 2026-11-14｜来源：https://posthog.com/docs/experiments https://posthog.com/docs https://github.com/PostHog/posthog-js/releases

# PostHog（产品分析 + 实验 + 会话回放）

## 什么时候用
- 海外产品要用一套工具搞定埋点分析、漏斗、Feature Flag、A/B 实验和会话回放（替代图谱 P-03「行为回放工具」+ G-04「实验平台」的组合）。
- 小团队不想自己搭数据栈，但又希望数据可导出到数仓。
- 国内项目默认用 datatester-ab-testing + sensors-growingio。

## 关键做法
- 实验建立在 Feature Flag 之上：每个实验背后都有一个 flag 负责分组并记录曝光，不需要额外埋点。
- 统计方法可选贝叶斯或频率学派；指标支持漏斗、均值、比率，也可用数仓表（收入、订阅）做指标。
- 每个实验组可直接跳到对应用户的会话回放，定量 + 定性一起看。
- 可通过 Web 界面、API 或 MCP 客户端管理实验，适合接入 AI 助手做实验复盘。
- 事件命名统一「对象_动作」（如 checkout_completed），在 PRD 埋点表里先定义再开发。

## 常见坑
- 会话回放默认可能录到输入内容，上线前配置输入框脱敏和页面屏蔽。
- 客户端 SDK 被广告拦截器拦截，核心转化事件要从服务端补报。
- 按事件量计费，高频无用事件（滚动、心跳）要在客户端采样或关闭自动采集。

## 迁移
- 从 GA4 + Optimizely / 自研开关迁移：先双写 2~4 周对齐口径，再切换看板和实验。
- 若后续数据量大到需要自建数仓，用 PostHog 的数据导出把事件同步到数仓，用 dbt 建模（见 dbt）。

## 最佳做法
- 判断理由：官方文档完整、SDK 频繁发布（posthog-js 仓库 2026-11-14 仍有新版本），海外定「采用」；国内访问与个人信息出境合规成本高，定「评估」。
- 风险与回退：如需撤出，保留原始事件导出，Feature Flag 先迁到配置中心再下线 SDK。

## CHANGELOG
- 2026-11-14 v1.0.0 首版；情报员自动核实（来源见 sources）
