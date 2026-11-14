---
id: swiftui
name: SwiftUI
aliases: [SwiftUI, Liquid Glass, Observation]
roles: [client-engineer]
maturity: 采用
as_of: 2026-11-14
version: 1.0.0
sources:
  - https://developer.apple.com/videos/play/wwdc2026/269/
  - https://developer.apple.com/wwdc26/guides/swiftui/
  - https://developer.apple.com/videos/play/wwdc2026/272/
region: both
replaces: []
replaced_by: []
from_graph: false
---

# SwiftUI

当前版本：WWDC26 发布的新一代 SDK（Xcode 27）：任意容器拖拽排序、ScrollView 上的滑动操作、工具栏溢出与优先级、`@State` 改为宏（类对象懒初始化）、ContentBuilder 提升类型检查速度、AsyncImage 默认走 HTTP 缓存；Liquid Glass 设计语言延续。
判断理由：Apple 官方主推的 UI 框架，新 API 只在 SwiftUI 上提供的越来越多，判「采用」。

## 什么时候用
- iOS 新页面、新 App（最低支持版本 iOS 17+ 时体验最好，可用 Observation）。
- 存量 UIKit 项目：新页面用 SwiftUI，通过 `UIHostingController` 嵌入。
- 复杂高性能列表、深度定制转场仍可保留 UIKit 实现。

## 关键做法
- 状态用 Observation：模型类标 `@Observable`，视图持有用 `@State`，下传用 `@Bindable`；不再新写 `ObservableObject` + `@Published`。
- 导航用 `NavigationStack` + 类型安全的 `navigationDestination`，路由状态放模型层。
- 按钮玻璃效果用 `glassButtonStyle` / `glassProminent`，不要自己叠 `glassEffect`。
- 视图拆小、避免在 `body` 里做重计算；列表元素提供稳定 `id`。
- 与 UIKit / AppKit 互操作用 Representable 协议（WWDC26 新增 `NSGestureRecognizerRepresentable`）。

## 常见坑
- 新 API 需要对应系统版本：用 `if #available` 包裹并提供降级 UI，避免抬高最低版本。
- 大型 `body` 导致编译器类型检查超时：拆子视图；Xcode 27 的 ContentBuilder 可缓解。
- `@State` 持有引用类型时注意生命周期（新版宏改为懒初始化，旧系统行为不同）。

## 迁移
- UIKit → SwiftUI：按页面迁，先迁设置页、详情页等简单页面；公用组件做成 SwiftUI 版本再用 `UIHostingConfiguration` 放进 UICollectionView。
- `ObservableObject` → `@Observable`：按模型逐个迁，注意 `@StateObject` / `@ObservedObject` 对应替换。

## 最佳做法
- 每年 WWDC 后评估新 API，按最低支持版本分批引入，不追 beta 上生产。

## CHANGELOG
- 2026-11-14 v1.0.0 首版；情报员自动核实（来源见 sources）
