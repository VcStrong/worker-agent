---
name: flutter
description: "Flutter（成熟度 采用，as_of 2026-11-14）：双端 UI 高度一致、团队愿意用 Dart 的新产品。 适用角色：客户端工程师。"
---
<!-- generated-by: scripts/build.py；源文件 data/skills/client/flutter.md，请勿手改 -->

> 成熟度：**采用**（region=cn）｜版本 1.0.0｜as_of 2026-11-14｜来源：https://docs.flutter.dev/release/whats-new https://docs.flutter.dev/release/release-notes/release-notes-3.47.0 https://blog.flutter.dev/whats-new-in-flutter-3-44-b0cc1ad3c527

# Flutter

当前版本：Flutter 3.50（2026-11-11）正式废弃框架内置的 Material / Cupertino 库，迁到独立包 `material_ui` / `cupertino_ui`；3.47（2026-08）Widget Previews 转稳定；3.44（2026-05）Android 引入 Hybrid Composition++、iOS/macOS 默认改用 Swift Package Manager、Impeller Vulkan 改进。
判断理由：Google 官方维护、多端（Android / iOS / Web / 桌面）稳定，适合一套 UI 多端一致的产品，判「采用」。选型需与原生 / KMP 对比后定。

## 什么时候用
- 双端 UI 高度一致、团队愿意用 Dart 的新产品。
- 已有原生 App 中的独立业务模块：add-to-app 方式嵌入。
- 需要鸿蒙原生版本：Flutter 官方不支持鸿蒙，鸿蒙按 harmonyos-next 原生实现（社区适配版本需单独评估，不默认推荐）。

## 关键做法
- 新项目直接依赖 `material_ui` / `cupertino_ui` 独立包（3.50 起），老项目按官方迁移指南替换 import。
- 状态管理选一种并全项目统一（如 Riverpod / Bloc），业务逻辑与 Widget 分离，便于测试。
- 渲染引擎用 Impeller（iOS / Android 默认）；性能问题用 DevTools 的帧图与 Raster 线程分析。
- 平台能力通过 Pigeon 生成类型安全的平台通道，或用 FFI / JNI 原生互操作。
- 用 Widget Previews 开发组件，配合 golden 测试做视觉回归。

## 常见坑
- 3.38 起 iOS 需迁移到 UIScene 生命周期，未迁移的插件可能出问题。
- 平台视图（地图、WebView）性能与手势冲突：3.44 的 Hybrid Composition++ 改善了 Android 侧，升级后回归。
- 包体积比原生大：开启 `--split-debug-info`、`--obfuscate`、按 ABI 拆包。
- 国内三方 SDK（推送、支付、地图）多无官方 Flutter 插件，要自己封装平台通道。

## 迁移
- 升级到 3.50：先迁 Material / Cupertino 独立包，再升级依赖插件。
- 原生 → Flutter：从 add-to-app 的独立模块开始，验证构建、热更新限制与发版流程。

## 最佳做法
- 锁定 Flutter 版本（FVM 或 CI 固定），全组同一版本，升级单独排期。

## CHANGELOG
- 2026-11-14 v1.0.0 首版；情报员自动核实（来源见 sources）
