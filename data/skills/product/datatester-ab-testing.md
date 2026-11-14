---
id: datatester-ab-testing
name: 火山引擎 A/B 测试（DataTester）
aliases: [DataTester, AB 实验, A/B 测试, 实验平台, Feature Flag, 火山 AB]
roles: [product-manager, data-growth]
maturity: 采用
maturity_by_region: {cn: 采用, global: 评估}
as_of: 2026-11-14
version: 1.0.0
sources:
  - https://docs.volcengine.com/docs/6287
  - https://docs.volcengine.com/docs/56651/784000
region: cn
replaces: []
replaced_by: []
from_graph: false
---

# 火山引擎 A/B 测试（DataTester）

## 什么时候用
- 国内 App / Web / 小程序要验证改版、文案、推荐策略、付费页是否真的提升指标（图谱 G-04「实验平台」的具体选型）。
- 需要「灰度发布 + 实验 + 回滚」一体：用 Feature Flag 控制功能开关。
- 海外项目默认用 posthog（见该技能包）。

## 关键做法
- 实验前写实验设计：假设、核心指标（1 个）、护栏指标（崩溃率、时长、退款等）、最小样本量（用平台流量计算器）、实验周期（至少覆盖 1 个完整周）。
- 实验类型按场景选：编程实验（客户端 / 服务端 SDK 分流）、可视化实验（Web 文案 / 样式）、多链接实验（落地页）、推送实验、MAB 智能调优（短期活动）。
- 用流量层与互斥域隔离同时跑的实验，避免互相污染。
- 客户端 SDK 覆盖 iOS、Android、HarmonyOS Next、Web/JS、小程序、Unity；服务端有 Java / Python / Go / Node.js / HTTP API。
- 结论按「显著 + 实际提升 ≥ 预期最小效应 + 护栏不恶化」三条同时满足才全量。

## 常见坑
- 中途改实验配置或加流量会破坏随机性，需要重开实验。
- 只看 p 值不看样本比例失衡（SRM），分流异常时结论无效。
- 指标口径要和埋点 / 指标平台一致，否则实验结论和日报对不上。
- 多次偷看结果提前停实验，假阳性显著增加。

## 迁移
- 从自研「按用户 ID 尾号分组」迁移：先 A/A 实验校验分流均匀，再把存量开关迁到 Feature Flag。
- 已用神策 / GrowingIO 的团队，确认事件能打通或在平台内重新定义指标。

## 最佳做法
- 判断理由：官方文档持续更新（SaaS 发布日志覆盖 2024~2026 年），支持私有化部署，国内定「采用」；海外数据驻留与合规需另评估，定「评估」。
- 合规：SDK 需在用户同意隐私政策后初始化；隐私政策中列明 SDK 名称、收集字段与目的。
- 当前版本：SaaS 持续发布；Go 服务端 SDK 文档标注 v1.0.13。

## CHANGELOG
- 2026-11-14 v1.0.0 首版；情报员自动核实（来源见 sources）
