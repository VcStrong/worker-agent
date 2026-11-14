---
name: kotlin-multiplatform
description: "Kotlin Multiplatform 与 Compose Multiplatform（成熟度 试用，as_of 2026-11-14）：Android 团队主导、需同步上 iOS 的产品：先用 KMP 共享网络、数据、领域逻辑。 适用角色：客户端工程师。"
---
<!-- generated-by: scripts/build.py；源文件 data/skills/client/kotlin-multiplatform.md，请勿手改 -->

> 成熟度：**试用**（region=cn）｜版本 1.0.0｜as_of 2026-11-14｜来源：https://blog.jetbrains.com/kotlin/2025/05/compose-multiplatform-1-8-0-released-compose-multiplatform-for-ios-is-stable-and-production-ready/ https://blog.jetbrains.com/kotlin/2026/05/compose-multiplatform-1-11-0/ https://kotlinlang.org/docs/multiplatform/supported-platforms.html

# Kotlin Multiplatform 与 Compose Multiplatform

当前版本：KMP 核心与 Compose Multiplatform 的 iOS 目标均为 Stable（CMP 1.8.0 于 2025-05 宣布 iOS 稳定）；CMP 1.11.0（2026-05）默认开启 iOS 并发渲染，新增实验性原生文本输入。
判断理由：技术已稳定，但跨端涉及团队分工、iOS 侧构建链与人员技能，需按项目决策，判「试用」。共享业务逻辑风险低，共享 UI 风险较高。

## 什么时候用
- Android 团队主导、需同步上 iOS 的产品：先用 KMP 共享网络、数据、领域逻辑。
- 设计统一、不追求平台原生观感的工具类 / 内部 App：可试用 Compose Multiplatform 共享 UI。
- 需要鸿蒙版本时：KMP 官方不支持鸿蒙目标，鸿蒙仍按 harmonyos-next 原生实现。

## 关键做法
- 模块划分：`shared`（commonMain / androidMain / iosMain）+ 各平台壳；平台差异用 `expect` / `actual` 或接口注入。
- 公共库选多平台版本：Ktor（网络）、kotlinx.serialization、SQLDelight 或 Room KMP、kotlinx-coroutines。
- iOS 集成通过 XCFramework 或 SPM；Kotlin 2.4 起 Swift export 进入 Alpha，暂以 Objective-C 头文件互操作为主。
- 共享 UI 时 iOS 侧保留原生导航 / 系统组件的接入点（UIKit/SwiftUI 互嵌）。

## 常见坑
- iOS 侧 Kotlin/Native 构建慢、调试体验弱于 Swift：给 iOS 同学安排 KMP 培训与工具支持。
- 挂起函数、Flow 暴露给 Swift 的易用性差：用 SKIE 一类桥接或包一层回调 API。
- CMP 的文本输入、无障碍、滚动手感与原生存在差异，上线前做 iOS 专项体验走查。

## 迁移
- 从纯原生开始：先抽一个低风险模块（如埋点、配置、数据模型）共享，验证构建与发版流程，再扩大范围。
- 风险与回退：共享模块保持接口清晰，必要时 iOS 侧可用 Swift 重写该模块而不影响 Android。

## 最佳做法
- 先共享逻辑、后共享 UI；每扩大一个共享层都要双端负责人共同评审。

## CHANGELOG
- 2026-11-14 v1.0.0 首版；情报员自动核实（来源见 sources）
