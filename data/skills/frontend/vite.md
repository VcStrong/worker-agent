---
id: vite
name: Vite（Rolldown 内核）
aliases: [Vite 8, Rolldown, Vite / Rolldown]
roles: [frontend-engineer]
maturity: 采用
as_of: 2026-11-14
version: 1.0.0
sources:
  - https://vite.dev/blog/announcing-vite8
  - https://vite.dev/blog/announcing-vite8-1
  - https://voidzero.dev/posts/announcing-rolldown-1-0
region: both
replaces: [webpack]
replaced_by: []
from_graph: true
---

# Vite（Rolldown 内核）

当前版本：Vite 8（2026-03-12 发布），已用 Rust 实现的 Rolldown 作为唯一打包器，取代此前 esbuild + Rollup 双引擎；Vite 8.1 已发布（实验性 chunk import map）。Rolldown 1.0 稳定版已发布（API 进入 semver 锁定）。
判断理由：图谱原有工具 Vite 在新版本下统一了开发与生产构建，生态最广，判「采用」，作为新项目默认构建工具。

## 什么时候用
- 新建 SPA、组件库、Vue / React 项目：默认 Vite。
- 需要 SSR 框架时由框架托管（Nuxt、React Router、SvelteKit 等底层都是 Vite）。
- 重度依赖 webpack 插件 / Module Federation 的存量项目：优先迁 Rspack（见 rspack），不硬迁 Vite。

## 关键做法
- Node 版本对齐 Vite 8 要求（20.19+ / 22.12+），CI 镜像同步升级。
- 原有 `esbuild`、`build.rollupOptions` 配置有兼容层自动转换为 Rolldown 等价项；新配置直接写 `build.rolldownOptions`。
- 库模式产物用 `build.lib`，并单独验证 ESM / CJS 双格式。
- 环境变量统一 `VITE_` 前缀，敏感值不进前端。

## 常见坑
- 个别 Rollup 插件依赖内部钩子，在 Rolldown 下行为不同：升级后逐个跑构建产物 diff。
- 开发态（未打包）与生产态（打包）差异：上线前必须 `vite build && vite preview` 回归。
- CommonJS 依赖在 dev 预构建中偶发问题，用 `optimizeDeps.include` 显式声明。

## 迁移
- Vite 5/6/7 → 8：先升 7 的最新补丁消除警告，再升 8；关注插件兼容表。
- webpack → Vite：入口改为 `index.html`，`require` 改 `import`，`process.env` 改 `import.meta.env`，loader 换 Vite 插件。

## 最佳做法
- 构建工具大版本升级单独 PR，附构建耗时与产物体积对比。

## CHANGELOG
- 2026-11-14 v1.0.0 首版；情报员自动核实（来源见 sources）
