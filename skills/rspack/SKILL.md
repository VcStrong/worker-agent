---
name: rspack
description: "Rspack / Rsbuild（成熟度 采用，as_of 2026-11-14）：存量 webpack 5 项目要提速、又不想大改配置：首选 Rspack。 适用角色：前端工程师。"
---
<!-- generated-by: scripts/build.py；源文件 data/skills/frontend/rspack.md，请勿手改 -->

> 成熟度：**采用**（region=cn）｜版本 1.0.0｜as_of 2026-11-14｜来源：https://rspack.rs/blog/announcing-2-0 https://rspack.rs/blog/announcing-2-1 https://rspack.rs/guide/migration/webpack

# Rspack / Rsbuild

当前版本：Rspack 2.0（2026-04-22 发布，与 Rsbuild 2.0 同期），2.1 默认开启 pureFunctions 摇树，2.2 已发布。Rust 实现，兼容 webpack 配置与大部分 loader / plugin。
判断理由：官方提供成熟的 webpack 迁移指南，兼容 Module Federation，适合存量 webpack 项目提速，判「采用」。

## 什么时候用
- 存量 webpack 5 项目要提速、又不想大改配置：首选 Rspack。
- 依赖 Module Federation / 微前端（qiankun 等）的项目。
- 新项目想要开箱即用：用 Rsbuild（基于 Rspack 的上层工具）；否则默认 Vite。

## 关键做法
- Node 要求 ^20.19.0 或 >=22.12.0；2.0 起核心包为纯 ESM。
- 依赖替换：`webpack` → `@rspack/core`，`webpack-cli` → `@rspack/cli`，`webpack-dev-server` → `@rspack/dev-server`。
- `webpack.config.js` 改名为 `rspack.config.js`；`html-webpack-plugin` 换 `html-rspack-plugin`，`tsconfig-paths-webpack-plugin` 改用 `resolve.tsConfig`。
- `file-loader` / `url-loader` / `raw-loader` 改为 asset modules。

## 常见坑
- webpack 的 `cache` 配置不能照搬，持久缓存字段结构不同。
- CLI 参数 `--progress`、`--bail` 等不支持，会直接报错。
- 残留插件仍 `import 'webpack/lib/...'` 时需保留 webpack 依赖，迁完再清。
- RSC 支持在 2.0 为实验特性，不要用于生产。

## 迁移
- webpack → Rspack：按官方迁移指南逐项替换，先保证产物一致（对比 chunk 列表与体积），再开启 Rspack 特有优化。
- Rspack 1.x → 2.x：按官方 v1→v2 升级指南处理 Node 版本与 ESM 变化。

## 最佳做法
- 迁移前后记录冷启动、HMR、生产构建三项耗时，作为技术收益证据。

## CHANGELOG
- 2026-11-14 v1.0.0 首版；情报员自动核实（来源见 sources）
