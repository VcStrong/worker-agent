---
id: jetpack-compose
name: Jetpack Compose
aliases: [Compose, Android Compose, Compose BOM]
roles: [client-engineer]
maturity: 采用
as_of: 2026-11-14
version: 1.0.0
sources:
  - https://developer.android.com/develop/ui/compose/migrate/strategy
  - https://android-developers.googleblog.com/2026/08/jetpack-compose-august-2026-release.html
  - https://developer.android.com/jetpack/androidx/releases/compose-runtime
region: both
replaces: [android-xml-layout]
replaced_by: []
from_graph: false
---

# Jetpack Compose

当前版本：Compose 1.12（2026-08 发布，BOM 2026.08.00；稳定补丁 1.12.1，1.13 处于 RC）。1.12 提高了最低 AGP 要求并对齐 compileSdk 37；1.11 起 v2 测试 API 成为默认、v1 废弃。
判断理由：Google 官方推荐的 Android UI 工具包，新页面一律 Compose，判「采用」。

## 什么时候用
- Android 所有新页面、新组件。
- 存量 View 项目：新页面 Compose，老页面按需逐页迁移（见 android-xml-layout）。
- 与 iOS 共享 UI 时可评估 Compose Multiplatform（见 kotlin-multiplatform）。

## 关键做法
- 版本统一用 Compose BOM 管理，不单独钉各模块版本；Kotlin 2.x 下用 `org.jetbrains.kotlin.plugin.compose` 编译器插件。
- 状态提升：ViewModel 暴露 `StateFlow<UiState>`，界面用 `collectAsStateWithLifecycle()` 收集；可组合函数保持无副作用、参数稳定。
- 列表用 `LazyColumn` 并提供稳定 `key`；副作用用 `LaunchedEffect` / `rememberUpdatedState`。
- 纯 Compose 应用用单 Activity + Navigation 3；混合项目才保留 Fragment。
- 测试用 v2 测试 API；配合 Baseline Profiles 解决首帧与滚动卡顿（见 baseline-profiles）。

## 常见坑
- 不稳定参数（`List`、可变类）导致无谓重组：用不可变集合或 `@Immutable` / `@Stable`，用 Layout Inspector 看重组次数。
- 在组合中直接发请求或写状态导致循环重组。
- 升级 BOM 前确认 AGP / compileSdk 满足最低要求，否则构建失败。
- Debug 包性能明显差于 Release，性能结论只看 Release + R8。

## 迁移
- 增量迁移：Fragment 里返回 `ComposeView`，设置 `ViewCompositionStrategy.DisposeOnViewTreeLifecycleDestroyed`；Compose 里嵌旧 View 用 `AndroidView` / `AndroidViewBinding`。
- 主题：先用 Material Theme Builder 生成 Compose 主题，迁移期两套主题并存，注意保持一致。

## 最佳做法
- 设计系统组件先在 Compose 落地，业务页面复用，迁移进度按组件覆盖率追踪。

## CHANGELOG
- 2026-11-14 v1.0.0 首版；情报员自动核实（来源见 sources）
