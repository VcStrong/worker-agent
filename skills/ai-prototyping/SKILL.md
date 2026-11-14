---
name: ai-prototyping
description: "AI 原型工具（Figma Make / v0）（成熟度 评估，as_of 2026-11-14）：需求立项 / 方案评审前，把一句话需求或线框快速变成可点击、可交互的原型，用来对齐「做成什么样」。 适用角色：产品经理、体验设计师。"
---
<!-- generated-by: scripts/build.py；源文件 data/skills/product/ai-prototyping.md，请勿手改 -->

> 成熟度：**评估**（region=cn）｜版本 1.0.0｜as_of 2026-11-14｜来源：https://www.figma.com/blog/figma-make-general-availability/ https://help.figma.com/hc/en-us/sections/31831621091223-Work-with-Figma-Make https://v0.app/docs

# AI 原型工具（Figma Make / v0）

## 什么时候用
- 需求立项 / 方案评审前，把一句话需求或线框快速变成可点击、可交互的原型，用来对齐「做成什么样」。
- 用户访谈、可用性测试需要能真实操作的 Demo，而设计稿还没出。
- 比较 2~3 个交互方案，让干系人直接点着体验后拍板。
- 不用于：交付给研发的正式设计稿、生产代码。

## 关键做法
- Figma Make：2025-07-24 随 Figma AI 一起 GA（发布到线上仍为 beta）；可挂载已有 Figma 设计和组件库作为上下文，复杂应用先用 plan 模式出计划再生成；每轮生成都留版本检查点，可回退。
- v0（v0.app）：Vercel 的 AI agent，生成 React / Next.js 代码，可连 GitHub、一键部署到 Vercel；适合要「能跑起来的 Web 原型」。
- 提示词按页面 / 模块分段写，写清角色、主流程、异常态、空状态；先让工具帮你改写提示词再生成。
- 原型链接写进 PRD「交互说明」节，注明「原型仅示意，以设计稿为准」。
- 计费按 AI credits（Figma 各席位额度不同，Starter 只有草稿），批量生成前先看额度。

## 常见坑
- 原型代码不是生产代码：结构、性能、无障碍、安全都没保证，研发不要直接复用。
- 从图片无法准确取色和间距，品牌色要靠挂载组件库或写明 token。
- 生成结果每次不同，评审时以截图 + 版本号留档。
- 境外 SaaS：需求里如有未公开业务数据、用户数据，不要粘进提示词。

## 迁移
- 从「Axure 手画高保真原型」迁移：主流程用 AI 原型做快速验证，复杂逻辑分支仍可保留 Axure / 流程图说明。
- 已有 Figma 设计系统的团队优先用 Figma Make（能直接复用库）；纯 Web 产品想要可部署 Demo 用 v0。

## 最佳做法
- 判断理由：两款均为官方正式产品、持续迭代（Figma Make 已 GA，v0 文档完整），但产物定位是原型，海外定为「试用」。
- 国内（region=cn）定「评估」：境外服务需跨境访问，涉及未公开需求与数据出境风险；国内团队可先用 MasterGo 的 AI 原型能力（见 mastergo-jsdesign）。
- 风险与回退：原型失真或额度用完时，回退到 Figma / MasterGo 手工原型。

## CHANGELOG
- 2026-11-14 v1.0.0 首版；情报员自动核实（来源见 sources）
