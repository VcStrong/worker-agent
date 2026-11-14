---
id: android-xml-layout
name: Android XML 布局（新页面暂缓）
aliases: [XML 布局, View 体系, ViewBinding, findViewById, Android View]
roles: [client-engineer]
maturity: 暂缓
as_of: 2026-11-14
version: 1.0.0
sources:
  - https://developer.android.com/develop/ui/compose/migrate/strategy
  - https://developer.android.com/develop/ui/compose/migrate/interoperability-apis/compose-in-views
  - https://developer.android.com/develop/ui/compose/migrate/interoperability-apis/views-in-compose
region: both
replaces: []
replaced_by: [jetpack-compose]
from_graph: true
---

# Android XML 布局（新页面暂缓）

当前状态：View 体系仍受支持，但 Android 官方迁移策略明确为「新页面用 Compose、逐页替换旧页面」。
判断理由：新 UI 能力（Material 3 新组件、自适应布局、动画 API）主要在 Compose 上提供，新页面继续写 XML 只会增加迁移债，判「暂缓」。存量页面照旧维护。

## 什么时候用
- 维护、修复存量 XML 页面。
- Compose 暂无等价能力的系统组件（如部分 MapView、WebView 场景）可继续用 View，通过 `AndroidView` 嵌入。
- 不在新页面、新组件中使用。

## 关键做法
- 存量页面统一用 ViewBinding，不再新增 `findViewById` / kotlin-android-extensions。
- 存量页面的状态层先改为 ViewModel + StateFlow，用 `repeatOnLifecycle` 收集，为后续换 Compose 做准备。
- 自定义 View 修改时评估顺手迁为 Composable 的成本。

## 常见坑
- 混合期两套主题（XML theme / Compose theme）不一致导致颜色、字体偏差。
- `ComposeView` 默认组合策略在 Fragment 中可能丢状态，需显式设置 ViewCompositionStrategy。
- 窗口 insets 在 View 与 Compose 混合层级中被重复消费。

## 迁移
- 见下方「替代」节。

## 替代
- 原因：官方 UI 演进集中在 Compose，XML + View 开发效率低、状态与 UI 同步易出错，新页面继续写会扩大迁移面。
- 替代项：`jetpack-compose`。
- 迁移建议：新页面直接 Compose；存量按「先抽通用组件 → 再逐页替换」推进，XML 内嵌 `ComposeView`、Compose 内嵌 `AndroidView` / `AndroidViewBinding` 过渡；每迁一页做截图对比 + Compose UI 测试；迁移单独排期，不夹带在业务需求里。
- 存量项目照旧维护，不擅自迁移，只在技术方案里提迁移建议。

## 最佳做法
- 迁移优先级：改动频繁的页面 > 新设计稿重做的页面 > 稳定老页面。

## CHANGELOG
- 2026-11-14 v1.0.0 首版；情报员自动核实（来源见 sources）
