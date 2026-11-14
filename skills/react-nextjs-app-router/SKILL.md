---
name: react-nextjs-app-router
description: "React 19 / Next.js App Router 与 Server Components（成熟度 采用，as_of 2026-11-14）：需要 SEO、首屏性能、BFF 能力的 Web 站点 / 中后台：Next.js App Router。 适用角色：前端工程师。"
---
<!-- generated-by: scripts/build.py；源文件 data/skills/frontend/react-nextjs-app-router.md，请勿手改 -->

> 成熟度：**采用**（region=cn）｜版本 1.0.0｜as_of 2026-11-14｜来源：https://nextjs.org/blog/next-16-4 https://nextjs.org/blog/november-2026-security-release https://react.dev/blog/2025/10/01/react-19-2 https://react.dev/versions

# React 19 / Next.js App Router 与 Server Components

当前版本：Next.js 16.4（2026-10-06，捆绑 React 19.3；Cache Components 成为推荐默认，新建项目默认开启）；安全补丁 16.4.5（LTS）/ 15.5.29（维护线）于 2026-11-03 发布。
判断理由：App Router + RSC 是 Next.js 官方主线，React 19.x 稳定迭代，判「采用」；但 RSC 相关安全公告频繁，必须跟补丁。

## 什么时候用
- 需要 SEO、首屏性能、BFF 能力的 Web 站点 / 中后台：Next.js App Router。
- 纯 SPA、嵌入式页面、无 Node 运行时的场景：React 19 + Vite 即可，不必上 Next.js。
- 已有 Pages Router 项目：照常维护，新路由逐步放到 `app/`。

## 关键做法
- 默认写 Server Component，只在需要状态 / 事件 / 浏览器 API 的叶子组件加 `'use client'`，把客户端边界压低。
- 数据获取放在服务端组件里直接 `await`；写操作用 Server Actions，并在 action 内做鉴权与输入校验。
- 16.4 起用 Cache Components 明确声明可缓存部分，别依赖隐式缓存。
- React 19.2 起：`<Activity>` 保留离屏状态、`useEffectEvent` 拆分 Effect 中的事件逻辑（不要为压 lint 滥用）。
- 流式渲染：用 `loading.tsx` / `<Suspense>` 切分慢数据块，配合 INP / LCP 观测。

## 常见坑
- 把密钥、数据库客户端 import 进 Client Component 会被打进前端包：服务端模块加 `import 'server-only'`。
- Server Actions 等于公开 HTTP 接口，不做鉴权即越权。
- RSC 链路出现过多次安全漏洞（含 2026-11 的跨租户缓存泄露）：订阅 nextjs.org/blog 安全标签，补丁 48 小时内升级。
- 第三方组件库未标 `'use client'` 时在服务端组件中直接用会报错，需要包一层客户端组件。

## 迁移
- Pages Router → App Router：按路由逐个迁移，两套可共存；`getServerSideProps` 改为服务端组件内取数。
- React 18 → 19：先跑官方 codemod，处理 `ref` 作为 prop、移除的旧 API，再升级 Next.js。
- 自托管时确认运行时 Node 版本与缓存存储（多实例需共享缓存）。

## 最佳做法
- 每个页面在评审时标出「服务端 / 客户端」边界图，防止整页被 `'use client'` 污染。
- 安全补丁走快速通道，不等版本火车。

## CHANGELOG
- 2026-11-14 v1.0.0 首版；情报员自动核实（来源见 sources）
