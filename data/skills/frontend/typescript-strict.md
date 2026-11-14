---
id: typescript-strict
name: TypeScript 严格模式
aliases: [TS strict, strict mode, TypeScript 7, tsgo]
roles: [frontend-engineer]
maturity: 采用
as_of: 2026-11-14
version: 1.0.0
sources:
  - https://devblogs.microsoft.com/typescript/announcing-typescript-7-0/
  - https://devblogs.microsoft.com/typescript/announcing-typescript-6-0/
  - https://www.typescriptlang.org/docs/handbook/release-notes/typescript-6-0.html
region: both
replaces: []
replaced_by: []
from_graph: false
---

# TypeScript 严格模式

当前版本：TypeScript 7.0（2026-07-08 发布，Go 原生编译器，全量构建官方称一般快 8~12 倍）；6.0 是 JS 实现的最后一版，作为过渡桥。
判断理由：6.0 起 `strict` 默认开启，7.0 沿用并把 6.0 废弃项改为硬错误，严格模式已是官方默认，判「采用」。

## 什么时候用
- 所有新建 TS 项目：不写 `strict` 也已默认开启，不要再显式关掉。
- 存量项目升级到 6.0 / 7.0 时：先按严格模式收敛类型错误，再升级。
- 组件库、SDK、BFF 等对外暴露类型的代码，严格模式是底线。

## 关键做法
- tsconfig 显式写 `"strict": true`，再按需加 `noUncheckedIndexedAccess`、`exactOptionalPropertyTypes`。
- 6.0 改了 `types` 默认值为空数组、`rootDir` 等默认值：升级后显式列出 `types`（如 `["node", "vite/client"]`）。
- 7.0 安装方式仍是 `npm i -D typescript`；需要与 6.0 并存时用 npm 别名（如 `@typescript/native` 指向 `typescript@^7`）。
- CI 里单独跑 `tsc --noEmit`，和打包器的类型擦除分开。
- 用 `unknown` 替代 `any`，外部输入（接口返回、表单）用 zod / valibot 一类运行时校验再收窄类型。

## 常见坑
- 7.0 暂无编程 API（官方计划 7.1 提供新 API）：Vue / Svelte / Astro / Angular 模板类型检查、部分 lint 插件仍依赖 6.0，Vue 项目编辑器侧先留 6.0。
- `target: es5` 等 6.0 废弃项在 7.0 直接报错；`ignoreDeprecations: "6.0"` 只能在 6.0 临时压制。
- 7.0 重写了 JS 支持，部分 JSDoc 写法失效，`checkJs` 项目要回归。
- 用 `// @ts-ignore` 压错误会掩盖真实问题，统一改用 `// @ts-expect-error` 并写原因。

## 迁移
- 存量非严格项目：先开 `strict` 看错误量，按目录分批修，或先逐项开启 `strictNullChecks`、`noImplicitAny`。
- 5.x → 6.0 → 7.0 分两步走：先在 6.0 消灭全部废弃警告，再切 7.0。
- 需要编译器 API 的工具链（自研代码生成、自定义 transformer）暂留 6.0，等 7.1 API。

## 最佳做法
- 新项目一开始就严格，后补的成本远高于前期多写几个类型。
- 升级 TS 大版本单独提 PR，不和业务改动混在一起，方便回滚。

## CHANGELOG
- 2026-11-14 v1.0.0 首版；情报员自动核实（来源见 sources）
