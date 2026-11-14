---
name: tailwind-css-v4
description: "Tailwind CSS v4（成熟度 采用，as_of 2026-11-14）：新项目的原子化样式方案，尤其是有设计 Token 的产品。 适用角色：前端工程师。"
---
<!-- generated-by: scripts/build.py；源文件 data/skills/frontend/tailwind-css-v4.md，请勿手改 -->

> 成熟度：**采用**（region=cn）｜版本 1.0.0｜as_of 2026-11-14｜来源：https://tailwindcss.com/blog/tailwindcss-v4 https://tailwindcss.com/blog/tailwindcss-v4-3 https://tailwindcss.com/docs/upgrade-guide

# Tailwind CSS v4

当前版本：v4.3（2026-05-08 公告，含 v4.2；新增滚动条、zoom、tab-size 等工具类）。v4.0 于 2025-01-22 发布，引擎重写，配置从 JS 移到 CSS。
判断理由：v4 已稳定迭代近两年，与设计 Token 结合顺畅，判「采用」。

## 什么时候用
- 新项目的原子化样式方案，尤其是有设计 Token 的产品。
- 组件库样式（配合 headless 组件库）。
- 已有 CSS Modules / Sass 的大型存量项目不强求迁移。

## 关键做法
- 入口 CSS 写 `@import "tailwindcss";`，主题用 `@theme { --color-brand: ...; }` 定义，直接映射设计 Token（CSS 变量）。
- Vite 项目用官方 `@tailwindcss/vite` 插件；其他构建用 `@tailwindcss/postcss`。
- 容器查询内置（`@container`、`@sm:`），不再需要插件。
- 自定义工具类用 `@utility`，变体用 `@custom-variant`。

## 常见坑
- v4 依赖现代 CSS（cascade layers、`@property`、`color-mix()`）：目标浏览器需较新（官方要求 Safari 16.4+、Chrome 111+、Firefox 128+），国内老 WebView / 低版本内核要先评估；v4.1 起对旧浏览器有部分降级。
- 动态拼接类名（`bg-${color}-500`）不会被扫描到，要写完整类名或 safelist。
- 小程序环境不支持部分现代 CSS，需用社区适配方案并单独评估。

## 迁移
- v3 → v4：先跑官方 `npx @tailwindcss/upgrade`，再人工处理 `tailwind.config.js` 中的自定义主题与插件。
- 默认边框色、阴影 / 圆角刻度命名有变化，迁移后做视觉回归截图对比。

## 最佳做法
- 设计 Token 单一事实源：Token → `@theme` 变量，禁止在业务代码里写任意值 `[#xxxxxx]`。

## CHANGELOG
- 2026-11-14 v1.0.0 首版；情报员自动核实（来源见 sources）
