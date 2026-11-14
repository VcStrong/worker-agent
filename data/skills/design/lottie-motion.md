---
id: lottie-motion
name: Lottie 动效（Lottie 规范 1.0 / dotLottie）
aliases: [Lottie, dotLottie, .lottie, 动效, Bodymovin]
roles: [ux-designer, client-engineer, frontend-engineer]
maturity: 采用
as_of: 2026-11-14
version: 1.0.0
sources:
  - https://lottie.github.io/
  - https://lottie.github.io/lottie-spec/1.0.1/
  - https://www.linuxfoundation.org/press/lottie-animation-community-announces-lottie-v1.0-specification
  - https://dotlottie.io/spec/2.0
  - https://airbnb.io/lottie/
  - https://github.com/airbnb/lottie-android/releases
region: both
replaces: []
replaced_by: []
from_graph: false
---

# Lottie 动效（Lottie 规范 1.0 / dotLottie）

当前版本：Lottie 格式规范 1.0.1（Linux 基金会下 Lottie Animation Community 维护）；dotLottie 规范 2.0；lottie-android 6.7.1（2025-10-31）。
判断理由：开放规范 + 多端成熟播放器，App 与 Web 广泛使用，定「采用」。

## 什么时候用
- 加载、空状态、成功反馈、引导页、活动页等矢量动效，需要设计做、研发零改动播放。
- 需要同一份动效在 Android / iOS / Web / 鸿蒙多端一致。
- 不适合：长视频、大量位图帧动画、需要实时物理交互的复杂动画。

## 关键做法
- 动效交付物：.json 或 .lottie（dotLottie，ZIP 打包，可含多个动画与主题，体积更小）+ 预览视频 + 时长、循环、触发说明。
- 只用规范内支持的特性；交付前在目标平台播放器里预览（各端渲染器支持的特性子集不同）。
- 体积预算：单个动效建议 < 100 KB，图片资源压缩或改矢量。
- 动效参数（时长、缓动）同步进设计 token，与交互说明一致。
- 尊重系统「减少动态效果」设置，提供静态降级帧。

## 常见坑
- AE 表达式、某些效果、蒙版在部分播放器不支持，表现为空白或错位。
- 大量图层导致低端机掉帧；列表中同时播放多个动画要控制数量。
- 文本图层依赖字体，跨端显示不一致，尽量转成形状。

## 迁移
- 从 GIF / APNG / 帧序列迁移：用 Lottie 重做，通常体积下降、清晰度提升。
- 从 .json 迁移到 .lottie：用官方工具打包，播放器升级到支持 dotLottie 的版本。

## 最佳做法
- 建动效库：统一命名、版本号、适用场景，组件化封装播放器（自动暂停不可见动画）。
- AI 生成动效（如文生 Lottie 工具）只作初稿，交付前按上述清单验收。

## CHANGELOG
- 2026-11-14 v1.0.0 首版；情报员自动核实（来源见 sources）
