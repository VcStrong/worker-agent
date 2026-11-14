---
name: kotlin-2-k2
description: "Kotlin 2 / K2 编译器（成熟度 采用，as_of 2026-11-14）：所有 Android / KMP 项目，新项目直接用最新 2.4.x。 适用角色：客户端工程师。"
---
<!-- generated-by: scripts/build.py；源文件 data/skills/client/kotlin-2-k2.md，请勿手改 -->

> 成熟度：**采用**（region=cn）｜版本 1.0.0｜as_of 2026-11-14｜来源：https://kotlinlang.org/docs/whatsnew24.html https://kotlinlang.org/docs/whatsnew2420.html https://kotlinlang.org/docs/releases.html https://kotlinlang.org/docs/compatibility-guide-24.html

# Kotlin 2 / K2 编译器

当前版本：Kotlin 2.4.0（2026-06-03，语言版本）、2.4.20（2026-09-07，工具版本）、2.4.21（2026-10-08，修复版）。K2 自 2.0 起为默认编译器。
判断理由：Kotlin 2.x 是唯一主线，K2 默认开启且稳定，判「采用」。

## 什么时候用
- 所有 Android / KMP 项目，新项目直接用最新 2.4.x。
- 仍在 1.9.x 的存量项目尽快升级（AGP、Compose 新版本会抬高 Kotlin 最低版本）。

## 关键做法
- Kotlin、AGP、Compose 编译器插件、KSP 版本成套升级，用 Gradle version catalog 统一管理。
- Compose 编译器随 Kotlin 发布：使用 `org.jetbrains.kotlin.plugin.compose` 插件，不再单独配 `kotlinCompilerExtensionVersion`。
- 注解处理从 kapt 迁到 KSP2（Room、Hilt、Moshi 等均支持）。
- 2.4 新稳定特性可用：context parameters、显式 backing fields、common 代码中的 `Uuid`；集合字面量仍是实验特性，不进生产代码。
- JVM 21+ 下 `when` 的 invokedynamic 编译在 2.4.20 默认开启。

## 常见坑
- 2.4.0 把若干警告升级为错误（如对不兼容类型的 `is` 检查）：升级前先清理当前版本的警告。
- 依赖 K1 内部 API 的编译器插件 / 老版本 kapt 在 K2 下失效。
- 增量编译缓存异常时先 `./gradlew clean` 再定位，别误判为代码问题。

## 迁移
- 1.9 → 2.x：先升到 1.9.2x 清警告，再切 2.x；按官方 compatibility guide 逐条核对。
- kapt → KSP：按库逐个替换，构建耗时通常明显下降。

## 最佳做法
- 语言版本升级与业务改动分开提交，附构建耗时对比。

## CHANGELOG
- 2026-11-14 v1.0.0 首版；情报员自动核实（来源见 sources）
