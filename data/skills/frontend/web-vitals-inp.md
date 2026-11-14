---
id: web-vitals-inp
name: Web Vitals（INP）
aliases: [Core Web Vitals, INP, Interaction to Next Paint, LCP, CLS, web-vitals]
roles: [frontend-engineer]
maturity: 采用
as_of: 2026-11-14
version: 1.0.0
sources:
  - https://web.dev/articles/inp
  - https://web.dev/articles/vitals
  - https://web.dev/articles/optimize-inp
  - https://web.dev/blog/inp-cwv-launch
region: both
replaces: []
replaced_by: []
from_graph: false
---

# Web Vitals（INP）

当前状态：Core Web Vitals = LCP、INP、CLS。INP 已取代 FID 成为稳定指标（FID 已废弃）。阈值（75 分位）：INP ≤200ms 良好、>500ms 差；LCP ≤2.5s；CLS ≤0.1。
判断理由：Google 官方稳定指标，是衡量交互性能的行业基准，判「采用」。图谱里的 FCP / TTI 只作辅助指标。

## 什么时候用
- 所有面向用户的 Web 页面上线前后的性能验收。
- 性能优化立项：用 INP / LCP 的前后数据对比证明收益。
- H5 嵌入 App WebView 的页面同样适用（自采数据）。

## 关键做法
- 线上用 `web-vitals` 库采集真实用户数据（RUM）上报自有埋点，看 75 分位，按页面 / 机型 / 网络拆分。
- 用 `onINP(..., { reportAllChanges: true })` 加 attribution 构建定位慢交互的元素与阶段（输入延迟 / 处理 / 呈现）。
- 实验室里 Lighthouse 测不了 INP，用 TBT 作代理；用 Chrome DevTools Performance 面板复现长任务。
- 优化 INP：拆长任务并让出主线程（`scheduler.yield()` 或 `setTimeout` 分片）、减少 JS 体积、避免大范围重渲染，事件处理里先给视觉反馈再做重活。

## 常见坑
- 只看 PageSpeed / CrUX：国内用户多数不在 CrUX 样本里，必须自采。
- INP 统计整个访问期的交互，只优化首屏点击不够。
- React / Vue 大列表一次性更新导致呈现延迟高：用虚拟列表、`startTransition` / 分批渲染。
- 第三方脚本（广告、客服、埋点 SDK）是长任务常见来源，要单独计量。

## 迁移
- 原有以 FID / TTI 为目标的性能看板：替换为 INP，阈值按 200 / 500ms 设置告警。
- 历史数据保留，新旧指标并行一个版本周期后下线 FID。

## 最佳做法
- 性能需求必须给出「优化前 / 优化后」75 分位数据，讲不出提升多少等于没优化。

## CHANGELOG
- 2026-11-14 v1.0.0 首版；情报员自动核实（来源见 sources）
