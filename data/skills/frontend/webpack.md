---
id: webpack
name: Webpack（新项目暂缓）
aliases: [webpack 5, Webpack]
roles: [frontend-engineer]
maturity: 暂缓
as_of: 2026-11-14
version: 1.0.0
sources:
  - https://webpack.js.org/
  - https://rspack.rs/guide/migration/webpack
  - https://vite.dev/blog/announcing-vite8
region: both
replaces: []
replaced_by: [vite, rspack]
from_graph: true
---

# Webpack（新项目暂缓）

当前版本：webpack 5 仍在维护。图谱前端工具栏原有「Vite / Webpack」。
判断理由：Vite 8（Rolldown 内核）与 Rspack 2（兼容 webpack API 的 Rust 实现）在构建速度和默认配置上全面领先，新项目已无首选 webpack 的理由，判「暂缓」。存量项目照旧维护。

## 什么时候用
- 只在维护存量 webpack 项目时使用，不在新项目中选用。
- 依赖某些只支持 webpack 的私有插件、且短期无法替换时，可继续保留。

## 关键做法
- 存量项目保持在 webpack 5 最新补丁版，锁定 loader / plugin 版本。
- 打开持久化缓存（`cache: { type: 'filesystem' }`）缓解构建慢。
- 新增需求不要再引入 webpack 专属的冷门插件，降低未来迁移成本。

## 常见坑
- 仍停留在 webpack 4 的项目：依赖链老化、Node 新版本兼容差，应优先升到 5 或直接迁 Rspack。
- 配置堆叠多年难以维护，迁移前先梳理实际生效的 loader / plugin 清单。

## 迁移
- 见下方「替代」节。

## 替代
- 原因：构建速度、开箱配置、生态活跃度均已被 Vite / Rspack 超越；webpack 配置复杂、冷启动慢。
- 替代项：新项目默认 `vite`；存量 webpack 项目想低成本提速、或依赖 Module Federation，用 `rspack`。
- 迁移建议：存量项目先按 Rspack 官方迁移指南替换依赖与配置文件（改动最小），稳定后再评估是否迁 Vite；迁移单独立项，附构建耗时与产物体积对比，不和业务需求混做。
- 存量项目照旧维护，不擅自迁移，只在技术方案里提迁移建议。

## 最佳做法
- 每年评估一次存量 webpack 项目的迁移收益，构建 > 1 分钟或 HMR > 2 秒的优先迁。

## CHANGELOG
- 2026-11-14 v1.0.0 首版；情报员自动核实（来源见 sources）
