---
name: swift-testing
description: "Swift Testing（成熟度 采用，as_of 2026-11-14）：iOS / Swift Package 的新单元测试、集成测试。 适用角色：客户端工程师。"
---
<!-- generated-by: scripts/build.py；源文件 data/skills/client/swift-testing.md，请勿手改 -->

> 成熟度：**采用**（region=cn）｜版本 1.0.0｜as_of 2026-11-14｜来源：https://developer.apple.com/videos/play/wwdc2024/10179/ https://developer.apple.com/videos/play/wwdc2026/267/ https://developer.apple.com/xcode/swift-testing/

# Swift Testing

当前状态：Apple 官方新测试框架，2024 年随 Xcode 16 推出，内置于 Xcode 与 Swift 工具链；WWDC26 发布「Migrate to Swift Testing」专场，新增退出测试 `#expect(processExitsWith:)`，并支持在 XCTestCase 中调用 `#expect` 以便渐进迁移。
判断理由：官方主推、与 Swift 并发原生集成、支持参数化与并行，判「采用」；UI 测试与性能测试仍用 XCTest。

## 什么时候用
- iOS / Swift Package 的新单元测试、集成测试。
- 需要参数化（多组输入）或大量并行执行的测试。
- UI 自动化（XCUITest）、性能测试（`measure`）继续用 XCTest。

## 关键做法
- 用 `@Test` 标注函数、`@Suite` 组织类型；断言用 `#expect`（失败继续）和 `#require`（失败即停，可解包可选值）。
- 参数化：`@Test(arguments: [...])`，替代循环断言。
- 错误断言：`#expect(throws: SomeError.self) { try f() }`。
- 用 Traits 控制：`.tags`、`.disabled("原因")`、`.timeLimit`、`.serialized`（需要串行时）。
- 测试默认并行执行，测试间不得共享可变状态；每个测试用新的实例。

## 常见坑
- 把 `try` / `await` 写在 `#expect` 外面可能编译失败，写成 `#expect(try f())`。
- 依赖执行顺序或全局单例的旧测试迁过来后随机失败：去掉共享状态或加 `.serialized`。
- 同一测试目标里两套框架混用时，命名与组织规范要统一，避免重复覆盖。

## 迁移
- 渐进迁移：新测试写 Swift Testing，老 XCTest 保留；改到哪个老测试就迁哪个。
- 对照：`XCTAssertEqual` → `#expect(a == b)`，`XCTUnwrap` → `#require`，`setUp` → `init`，`tearDown` → `deinit`（需类类型）。

## 最佳做法
- 新模块测试覆盖用参数化测试表达业务规则表，评审时直接对照需求。

## CHANGELOG
- 2026-11-14 v1.0.0 首版；情报员自动核实（来源见 sources）
