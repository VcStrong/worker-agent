---
id: fcm
name: App 推送与触达（海外：Firebase Cloud Messaging）
aliases: [FCM, Firebase Cloud Messaging, Google 推送, APNs, Web Push]
roles: [data-growth, client-engineer]
maturity: 评估
maturity_by_region: {cn: 评估, global: 采用}
as_of: 2026-11-14
version: 1.0.0
sources:
  - https://firebase.google.com/docs/cloud-messaging
region: global
replaces: []
replaced_by: []
from_graph: false
---

# App 推送与触达（海外：Firebase Cloud Messaging）

当前版本：FCM 为 Google 持续发布的服务；服务端通过 FCM HTTP v1 API 或 Firebase Admin SDK 发送；客户端覆盖 Android、Apple、Web，另有 Flutter、Unity、C++ SDK。
判断理由：海外 Android 设备普遍带 GMS，FCM 免费、稳定、跨平台，海外定「采用」；中国大陆设备无 GMS、FCM 无法送达，国内定「评估」，默认用 push-cn-vendor-channels。

## 什么时候用
- 面向海外用户的 App / Web 推送：交易通知、运营召回、静默数据同步。
- iOS 也可以经 FCM 统一发送（底层走 APNs），减少两套服务端逻辑。

## 关键做法
- 消息类型：通知消息（系统展示）与数据消息（由 App 代码决定行为）分开用；需要自定义展示或埋点时用数据消息。
- 发送目标：单设备 token、设备组、主题（topic）订阅；运营群发优先用主题或分群后批量发送。
- 服务端统一用 HTTP v1 API / Admin SDK，凭证用服务账号，密钥存密钥管理系统，不进代码。
- token 会轮换，客户端监听刷新并上报，服务端清理失效 token。
- Android 13+ 需要运行时通知权限；按场景时机申请，不在首启立即弹。

## 常见坑
- 国内外同一个包：国内设备拿不到 FCM token，要按设备是否有 GMS 自动切换通道。
- 数据消息在 App 被强制停止后不会唤醒，关键通知用通知消息。
- 高优先级消息滥用会被系统降级，只给真正紧急的消息用高优先级。

## 迁移
- 从旧版 FCM 服务端接口迁移到 HTTP v1：按官方迁移指南改用 OAuth 服务账号凭证与新消息结构。
- 国内外双发：抽象一层推送网关，按地区 / 设备能力路由到 FCM 或国内聚合通道。

## 最佳做法
- 合规：欧盟等地区按当地法律获得营销推送同意，提供退订入口；推送内容不含敏感个人信息。
- 风险与回退：FCM 异常时关键通知走邮件 / 短信兜底。

## CHANGELOG
- 2026-11-14 v1.0.0 首版；情报员自动核实（来源见 sources）
