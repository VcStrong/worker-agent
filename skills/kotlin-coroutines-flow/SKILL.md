---
name: kotlin-coroutines-flow
description: "Kotlin 协程与 Flow（成熟度 采用，as_of 2026-11-14）：Android / KMP 所有新的异步代码、数据流、事件流。 适用角色：客户端工程师。"
---
<!-- generated-by: scripts/build.py；源文件 data/skills/client/kotlin-coroutines-flow.md，请勿手改 -->

> 成熟度：**采用**（region=cn）｜版本 1.0.0｜as_of 2026-11-14｜来源：https://developer.android.com/kotlin/coroutines/coroutines-best-practices https://developer.android.com/kotlin/flow https://developer.android.com/topic/architecture/recommendations https://kotlinlang.org/docs/whatsnew2420.html

# Kotlin 协程与 Flow

当前状态：Android 官方架构建议以协程 + Flow 作为异步与数据流标准；Kotlin 2.4.20（2026-09）新增协程栈追踪恢复，便于排查。
判断理由：官方架构指南、Jetpack（Room / DataStore / Paging / Compose）均以协程与 Flow 为一等接口，判「采用」，作为 RxJava 的替代。

## 什么时候用
- Android / KMP 所有新的异步代码、数据流、事件流。
- 一次性请求用 `suspend` 函数；持续变化的数据用 `Flow`。

## 关键做法
- 数据层、领域层暴露 `suspend` 和 `Flow`；ViewModel 用 `viewModelScope` 启动业务，不让 View 触发业务逻辑。
- UI 状态：单一 `uiState: StateFlow`，来自下层的流用 `stateIn(viewModelScope, SharingStarted.WhileSubscribed(5000), initial)`。
- 收集：Compose 用 `collectAsStateWithLifecycle()`，View 用 `repeatOnLifecycle`，不要用 `launchWhenX`。
- 线程：suspend 函数要主线程安全，阻塞操作用 `withContext(Dispatchers.IO)`；Flow 上游切换用 `flowOn`；Dispatcher 通过注入，便于测试。
- 并发编排用 `combine`、`mapLatest`、`flatMapLatest`，不手写取消逻辑。

## 常见坑
- 吞掉 `CancellationException`（`catch (e: Exception)`）导致协程无法取消：捕获具体异常类型，或重新抛出。
- 用 `GlobalScope`：需要比页面活得长的任务，注入应用级 `CoroutineScope`。
- 一次性事件（Toast、导航）用 StateFlow 会重复消费：用状态字段 + 消费回执，或 Channel。
- 测试中收集永不完成的流要放 `backgroundScope`，并用 `runTest` + `StandardTestDispatcher`。

## 迁移
- 从 RxJava 迁移见 rxjava 技能「替代」节；边界处可用 `kotlinx-coroutines-rx3` 互转（`asFlow()` / `asObservable()`）。
- LiveData 存量照旧，新代码用 StateFlow。

## 最佳做法
- 每个 Repository 方法签名评审时确认：一次性 = suspend，持续 = Flow，禁止返回回调。

## CHANGELOG
- 2026-11-14 v1.0.0 首版；情报员自动核实（来源见 sources）
