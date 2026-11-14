---
name: rxjava
description: "RxJava（新代码暂缓）（成熟度 暂缓，as_of 2026-11-14）：维护存量 RxJava 代码。 适用角色：客户端工程师。"
---
<!-- generated-by: scripts/build.py；源文件 data/skills/client/rxjava.md，请勿手改 -->

> 成熟度：**暂缓**（region=cn）｜版本 1.0.0｜as_of 2026-11-14｜来源：https://github.com/ReactiveX/RxJava https://github.com/ReactiveX/RxJava/releases https://developer.android.com/kotlin/coroutines/coroutines-best-practices

# RxJava（新代码暂缓）

当前版本：RxJava 3.x 仍在维护（GitHub 最新 3.1.12）；RxJava 2.x 已于 2021-02-28 EOL。图谱客户端「架构与框架」里列有 RxJava。
判断理由：库本身未停更，但 Android 官方架构与 Jetpack 已统一到 Kotlin 协程 + Flow，新代码继续用 RxJava 会增加学习与维护成本，判「暂缓」。存量代码照旧维护。

## 什么时候用
- 维护存量 RxJava 代码。
- 纯 Java 模块且短期不引入 Kotlin 时可继续使用 RxJava 3。
- 不在新的 Kotlin 代码中引入。

## 关键做法
- 仍在 RxJava 2 的项目先升 RxJava 3（2.x 已无修复）。
- 存量订阅统一用 `CompositeDisposable` 并在生命周期结束时清理，防泄漏。
- 新老代码边界用 `kotlinx-coroutines-rx3` 桥接，不在新代码里继续扩散 Observable。

## 常见坑
- 订阅未释放导致内存泄漏、回调到已销毁页面崩溃。
- 线程切换 `subscribeOn` / `observeOn` 写错导致主线程网络请求或 UI 线程异常。
- 混用 Rx 与协程时取消语义不一致，桥接处要写测试。

## 迁移
- 见下方「替代」节。

## 替代
- 原因：官方架构建议、Room / DataStore / Paging / Compose 均以协程与 Flow 为一等 API；协程结构化并发更易保证取消与生命周期安全。
- 替代项：`kotlin-coroutines-flow`。
- 迁移建议：从数据层自底向上迁——`Single` / `Completable` → `suspend`，`Observable` / `Flowable` → `Flow`，`BehaviorSubject` → `StateFlow`，`PublishSubject` → `SharedFlow`；边界处用 rx3 互转函数过渡；按模块迁并补单元测试，不一次性大改。
- 存量项目照旧维护，不擅自迁移，只在技术方案里提迁移建议。

## 最佳做法
- 迁移时先迁读多写少的数据流（列表、配置），事件总线类最后迁。

## CHANGELOG
- 2026-11-14 v1.0.0 首版；情报员自动核实（来源见 sources）
