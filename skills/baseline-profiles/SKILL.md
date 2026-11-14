---
name: baseline-profiles
description: "Baseline Profiles（成熟度 采用，as_of 2026-11-14）：所有线上 Android App，尤其冷启动、首帧耗时、列表滚动卡顿是关键指标的产品。 适用角色：客户端工程师。"
---
<!-- generated-by: scripts/build.py；源文件 data/skills/client/baseline-profiles.md，请勿手改 -->

> 成熟度：**采用**（region=cn）｜版本 1.0.0｜as_of 2026-11-14｜来源：https://developer.android.com/topic/performance/baselineprofiles/overview https://developer.android.com/topic/performance/baselineprofiles/create-baselineprofile https://developer.android.com/topic/performance/baselineprofiles/measure-baselineprofile

# Baseline Profiles

当前状态：Android 官方的配置引导优化（PGO）方案，告诉 ART 安装时预编译哪些关键路径代码，改善冷启动与卡顿。最低要求：AGP 8.0.0、Macrobenchmark 1.5.0、ProfileInstaller 1.4.1。
判断理由：官方稳定方案、接入成本低、收益可量化（官方 codelab 示例全显时间降约 28%），判「采用」。

## 什么时候用
- 所有线上 Android App，尤其冷启动、首帧耗时、列表滚动卡顿是关键指标的产品。
- Compose 页面（首次运行需 JIT，收益更明显）。
- 国内渠道包（非 Google Play 分发）同样生效：ProfileInstaller 会在安装后写入配置。

## 关键做法
- 用 Android Studio 的 Baseline Profile Generator 模板新建 `:baselineprofile` 模块，接入 `androidx.baselineprofile` Gradle 插件。
- 用 `BaselineProfileRule`（需 API 28+ 设备或 root）覆盖关键用户路径：启动 → 首页 → 核心列表滚动 → 核心详情。
- 同时生成 Startup Profile 优化 dex 布局，提升启动。
- 用 Macrobenchmark 对比 `CompilationMode.None()` 与 `Partial()` 的启动、帧耗时，结果写进性能报告。
- 在 CI 定期重新生成配置，随代码变更更新。

## 常见坑
- 在模拟器上测性能：数值与真机不符，必须用真机（中低端机优先）。
- 只覆盖启动，不覆盖核心交互路径，滚动卡顿收益有限。
- 混淆规则变化或大重构后未重新生成，配置失效。

## 迁移
- 未接入项目：先只覆盖启动路径上线一版，确认收益后扩展到核心路径。
- 手写 `baseline-prof.txt` 的老项目：改为 Gradle 插件 + 自动生成。

## 最佳做法
- 发版报告固定附「冷启动 P50/P90 有无 Profile 对比」，作为性能回归门禁。

## CHANGELOG
- 2026-11-14 v1.0.0 首版；情报员自动核实（来源见 sources）
