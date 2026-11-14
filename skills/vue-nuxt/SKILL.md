---
name: vue-nuxt
description: "Vue 3.5+ / Nuxt（成熟度 采用，as_of 2026-11-14）：国内中后台、营销页、团队熟悉 Vue 的项目：Vue 3.5 + Vite + Pinia。 适用角色：前端工程师。"
---
<!-- generated-by: scripts/build.py；源文件 data/skills/frontend/vue-nuxt.md，请勿手改 -->

> 成熟度：**采用**（region=cn）｜版本 1.0.0｜as_of 2026-11-14｜来源：https://nuxt.com/blog/v4 https://nuxt.com/blog/v4-4 https://nuxt.com/docs/4.x/community/roadmap https://github.com/vuejs/core/releases https://v2.vuejs.org/eol/

# Vue 3.5+ / Nuxt

当前版本：Vue 3.5.x 为稳定线；Vue 3.6 处于 RC（Vapor Mode 功能已完整，可选开启）。Nuxt 4（2025-07 发布），4.4 于 2026-01-22 发布（支持 vue-router v5）；官方路线图预计 Nuxt 5 在 2026 Q4（升级 Nitro v3）。
判断理由：Vue 3.5 与 Nuxt 4 均为稳定版且国内生态广，判「采用」；Vapor Mode 仍在 RC，只做「评估」。

## 什么时候用
- 国内中后台、营销页、团队熟悉 Vue 的项目：Vue 3.5 + Vite + Pinia。
- 需要 SSR / SSG / SEO：Nuxt 4。
- 多端（小程序 / App）复用：配合 uni-app，见 miniprogram 技能。

## 关键做法
- 统一 `<script setup lang="ts">` + Composition API；3.5 起响应式 props 解构可直接用，`useTemplateRef` 取模板引用。
- 状态管理用 Pinia，不再新引入 Vuex。
- Nuxt 4 用 `app/` 目录结构，数据获取用 `useFetch` / `useAsyncData`，4.4 起可自定义工厂统一错误处理与鉴权头。
- 类型检查用 `vue-tsc`；注意 TypeScript 7.0 暂无 API，Vue 模板类型检查仍需 TS 6.0（见 typescript-strict）。

## 常见坑
- Vapor Mode 不支持 Options API、`getCurrentInstance()` 返回 null、不支持 `v-memo`，不要在生产代码开启。
- Nuxt 5 计划随 Nitro v3 带来破坏性变更：新项目可在 Nuxt 4 打开 `compatibilityVersion` 相关预览提前适配，但别在发版前追 RC。
- SSR 下访问 `window` / `localStorage` 要放 `onMounted` 或 `<ClientOnly>`。

## 迁移
- Vue 2 已于 2023-12-31 EOL（最终版 2.7.16），不再有安全修复：存量项目先升 2.7，用官方迁移构建（@vue/compat）分模块迁 3.x；新项目禁止选 Vue 2。
- Nuxt 3 → 4：按官方升级指南先开 v4 兼容模式，再调整目录结构。
- Vuex → Pinia：按 store 逐个迁，两者可短期共存。

## 最佳做法
- 跟随 Vue / Nuxt 小版本升级，大版本等首个补丁版再上。

## CHANGELOG
- 2026-11-14 v1.0.0 首版；情报员自动核实（来源见 sources）
