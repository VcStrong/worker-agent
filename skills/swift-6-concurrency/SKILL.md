---
name: swift-6-concurrency
description: "Swift 6 并发（严格并发检查）（成熟度 采用，as_of 2026-11-14）：新 iOS 项目直接用 Swift 6 语言模式。 适用角色：客户端工程师。"
---
<!-- generated-by: scripts/build.py；源文件 data/skills/client/swift-6-concurrency.md，请勿手改 -->

> 成熟度：**采用**（region=cn）｜版本 1.0.0｜as_of 2026-11-14｜来源：https://www.swift.org/blog/swift-6.2-released/ https://www.swift.org/blog/swift-6.4-released/ https://www.swift.org/blog/swift-6.3-released/

# Swift 6 并发（严格并发检查）

当前版本：Swift 6.4（2026-09-15，补丁 6.4.1 于 2026-10-12）。Swift 6.2 引入 Approachable Concurrency：可选默认主 Actor 隔离、`@concurrent` 显式标注并行代码、nonisolated async 默认在调用方上下文执行。6.3 起提供官方 Android SDK。
判断理由：Swift 6 语言模式在编译期消除数据竞争，6.2 后迁移门槛大幅降低，判「采用」。

## 什么时候用
- 新 iOS 项目直接用 Swift 6 语言模式。
- 存量项目分模块从 Swift 5 模式 + 严格检查警告逐步切到 Swift 6 模式。

## 关键做法
- 新 App 目标：开启 Approachable Concurrency，并把 Default Actor Isolation 设为 MainActor（两者是独立设置），UI 代码天然在主线程。
- 真正需要并行的计算用 `@concurrent` 标注，或放进独立 actor。
- 跨隔离域传递的类型遵循 `Sendable`；值类型优先，引用类型用 actor 或不可变设计。
- 回调式 API 用 `withCheckedContinuation` 包装为 async；任务取消用 `Task.checkCancellation()`。
- 网络、数据库层设计为 actor 或 nonisolated async 接口，UI 层只 await 结果。

## 常见坑
- 用 `@unchecked Sendable`、`nonisolated(unsafe)` 压错误会掩盖真实数据竞争，必须写注释说明理由并评审。
- 一次性把整个工程切 Swift 6 模式，错误量爆炸：按模块（SPM target）逐个切。
- 第三方库未适配 Sendable：用 `@preconcurrency import` 暂时降级，并跟踪上游升级。
- 在 Swift 6.2 前后 nonisolated async 函数的执行位置语义不同，升级后复查性能热点。

## 迁移
- Swift 5 → 6：先在 Swift 5 模式开启 `-strict-concurrency=complete` 清警告，再逐 target 切 Swift 6 语言模式。
- GCD / 回调 → async/await：从数据层开始，`DispatchQueue` 保护的状态改为 actor。

## 最佳做法
- 模块切换 Swift 6 模式作为独立任务排期，每个模块切换后跑 Thread Sanitizer 回归。

## CHANGELOG
- 2026-11-14 v1.0.0 首版；情报员自动核实（来源见 sources）
