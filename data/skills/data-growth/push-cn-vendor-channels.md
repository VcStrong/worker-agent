---
id: push-cn-vendor-channels
name: App 推送与触达（国内：极光 + 厂商通道 / 鸿蒙 Push Kit）
aliases: [推送, 消息推送, 极光推送, JPush, 厂商通道, 华为推送, 小米推送, OPPO 推送, vivo 推送, Push Kit, 离线推送]
roles: [data-growth, client-engineer]
maturity: 采用
maturity_by_region: {cn: 采用, global: 评估}
as_of: 2026-11-14
version: 1.0.0
sources:
  - https://docs.jiguang.cn/jpush/client/Android/android_guide
  - https://developer.huawei.com/consumer/cn/doc/harmonyos-guides/push-kit-guide
region: cn
replaces: []
replaced_by: []
from_graph: true
---

# App 推送与触达（国内：极光 + 厂商通道 / 鸿蒙 Push Kit）

当前版本：极光 JPush Android SDK 6.x（集成指南 2026-08-27 更新，v6.0.3 起最低 Android 5.0 / API 21）；HarmonyOS NEXT 应用使用系统 Push Kit。各厂商通道（华为、荣耀、小米、OPPO、vivo 等）由聚合 SDK 统一接入。
判断理由：国内 Android 无 GMS，App 被杀后只能依赖厂商系统通道送达，聚合推送 + 厂商通道是国内唯一可行方案，国内定「采用」；海外默认 fcm。图谱 P-04 / G-01 原有「推送系统 / 推送平台」。

## 什么时候用
- 国内 App 的运营推送（召回、活动）、交易通知（订单、物流）、IM 离线消息。
- 鸿蒙 NEXT 版本 App：直接接 Push Kit（不能复用 Android 厂商 SDK）。

## 关键做法
- 聚合 SDK（如极光）+ 各厂商通道参数（AppID / AppKey / AppSecret）在控制台配好；验证方法：杀进程后发推送仍能收到。
- 按厂商消息分类申报：私信 / 服务通讯类（订单、聊天）与公信 / 运营类分开发送，运营类受每日条数限制。
- 推送带深链接，落地页统一路由；点击、到达、展示回传埋点，算真实触达率。
- 运营推送做频控（每人每天上限）、免打扰时段、分群与 A/B（见 datatester-ab-testing）。
- 鸿蒙 Push Kit：在 AppGallery Connect 开通推送服务，获取 Push Token；场景化消息需按规定申请权益。

## 常见坑
- 运营消息被误标为服务通讯类，会被厂商限流或处罚；按真实类型申报。
- 各厂商对图标、角标、通知渠道（Channel）要求不同，需逐一适配测试。
- 新机型 / 系统版本通知权限默认关闭，首启引导用户开启但不要强弹。

## 迁移
- 聚合平台之间迁移：先双通道灰度、按设备 ID 映射，确认到达率一致后切换；厂商参数可复用。

## 最佳做法
- 合规：推送 SDK 必须在用户同意隐私政策后初始化（极光未授权时不得初始化 / 采集），隐私政策列明 SDK 名称与收集字段；提供关闭推送入口；营销推送遵守工信部关于 App 弹窗与骚扰信息的管理要求。
- 风险与回退：聚合平台故障时，关键交易通知走短信 / 站内信兜底。

## CHANGELOG
- 2026-11-14 v1.0.0 首版；情报员自动核实（来源见 sources）
