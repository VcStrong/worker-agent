---
id: harmonyos-next
name: 鸿蒙 HarmonyOS NEXT（ArkTS / ArkUI / DevEco Studio）
aliases: [鸿蒙, 纯血鸿蒙, HarmonyOS, HarmonyOS NEXT, ArkTS, ArkUI, DevEco Studio, 鸿蒙原生应用]
roles: [client-engineer]
maturity: 采用
as_of: 2026-11-14
version: 1.0.0
sources:
  - https://developer.huawei.com/consumer/en/doc/harmonyos-guides/introduction-to-arkts
  - https://developer.huawei.com/consumer/en/doc/harmonyos-guides/arkts-state-management-overview
  - https://developer.huawei.com/consumer/en/doc/harmonyos-guides/arkts-v1-v2-migration
  - https://developer.huawei.com/consumer/en/doc/harmonyos-guides/ide-hvigor-commandline
  - https://developer.huawei.com/consumer/en/doc/harmonyos-guides/ide-ohpm-publish
  - https://developer.huawei.com/consumer/en/doc/harmonyos-releases/upgrade-adaptation
  - https://developer.huawei.com/consumer/cn/doc/app/50170
region: cn
replaces: []
replaced_by: []
from_graph: false
---

# 鸿蒙 HarmonyOS NEXT（ArkTS / ArkUI / DevEco Studio）

当前版本：HarmonyOS 6.0.0(API 20) + DevEco Studio 6.0.0 Release（2025-09-25）；6.1.1(API 24) 于 2026-05-26 发布；官方已发布升级到 26.0.0（HarmonyOS 7.0）的适配指南。
判断理由：纯血鸿蒙不再兼容 APK，国内 App 必须单独做原生版本；官方工具链与文档完整，判「采用」（国内）。被要求做鸿蒙版时直接给 ArkTS / ArkUI 方案，不说不支持。

## 什么时候用
- 国内 App 需要覆盖华为 / 鸿蒙设备：做鸿蒙原生应用（或元服务）。
- 已有 Android / iOS 应用：鸿蒙版按原生重写 UI 层，业务逻辑和接口复用。
- 跨端框架（uni-app x、Taro、Flutter 社区版）只在团队已用该框架时评估，主力仍推原生 ArkTS。

## 关键做法

### 工程骨架
- 应用模型用 Stage 模型（API 9 起推荐、长期演进）：`AbilityStage` → `UIAbility`（`onCreate` / `onWindowStageCreate` 里 `windowStage.loadContent('pages/Index')`）→ ArkUI 页面；后台能力用各类 `ExtensionAbility`。
- 工程结构：`AppScope/app.json5`（包名、版本）；`entry/src/main/module.json5`（abilities、权限 `requestPermissions`）；`ets/` 下写 ArkTS。模块分 HAP（入口）/ HSP（应用内共享，同进程同包名）/ HAR（静态库）。
- 依赖：ohpm 管理，`oh-package.json5` 写 `dependencies` / `devDependencies`；运行时依赖不能放 devDependencies；发布 HAR 时必须声明全部直接依赖；私仓用 ohpm-repo。
- 构建：hvigor（`hvigorfile.ts` + `build-profile.json5`），命令行 `hvigorw assembleHap`、`hvigorw assembleApp`，默认 HAP/HSP/HAR 为 debug、App Pack 为 release；CI 用 hvigorw 而不是 IDE 点按钮。
- SDK 版本：`build-profile.json5` 里显式设置 `compatibleSdkVersion`（最低支持）与 `targetSdkVersion`，不要依赖 IDE 自动升级。

### ArkUI 声明式 + 状态管理 V2
- UI 用 `@Entry` + `@ComponentV2` 结构体，`build()` 里声明式组合 `Column` / `Row` / `List` / `Navigation`；长列表用 `LazyForEach` / `Repeat` 做懒加载。
- 新项目一律用状态管理 V2：组件内部状态 `@Local`、父传子 `@Param`（只读）+ `@Once`、子回调 `@Event`、跨层 `@Provider` / `@Consumer`、监听 `@Monitor`、派生 `@Computed`。
- 数据模型类用 `@ObservedV2`，需观测的字段加 `@Trace`（深层嵌套也能观测）；序列化还原类型用 `@Type`。
- 页面路由用 `Navigation` + `NavPathStack`（官方推荐），不再新写 `router` 页面栈。
- 网络用 `@kit.NetworkKit` 的 http，持久化用 Preferences / RelationalStore；ArkTS 是 TS 的严格子集：无 `any`、无运行时改结构、对象字面量需有类型声明。

## 常见坑
- V1（`@Component`、`@State`、`@Prop`、`@Link`、`@Watch`）和 V2 装饰器不能在同一组件混用；`@Trace` 写在组件 struct 成员上会编译报错。
- 照搬 TS / JS 库常因 ArkTS 严格语法编译失败：优先找 ohpm 中心仓的鸿蒙版三方库。
- 升级 DevEco Studio 后若没显式写 targetSdkVersion 会被自动升级，带入行为变更：升级前用 IDE 的 API Change Assistant 扫描。
- 上架：服务器在国内的联网应用必须完成 APP 备案，备案时平台选「鸿蒙」并登记鸿蒙包名（应用与元服务的包名都要备案）；勾选「单机」但实际联网会被驳回。

## 迁移
- 从 Android 迁：Activity/Fragment → UIAbility + Navigation 页面；ViewModel + Flow → `@ObservedV2` 模型 + V2 状态装饰器；Gradle → hvigor；Maven 依赖 → ohpm。
- 存量 V1 状态管理代码：按官方 V1→V2 迁移指南逐组件迁（`@Component` → `@ComponentV2`，`@Watch` → `@Monitor`），新页面直接写 V2。

## 最佳做法
- 鸿蒙版独立排期与测试矩阵（真机 + AGC 云调试），不按「Android 顺手改改」估工时。

## CHANGELOG
- 2026-11-14 v1.0.0 首版；情报员自动核实（来源见 sources）
