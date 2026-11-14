---
name: sketch
description: "Sketch（新项目暂缓）（成熟度 暂缓，as_of 2026-11-14）：只在维护存量 Sketch 设计文件、组件库时使用。 适用角色：体验设计师。"
---
<!-- generated-by: scripts/build.py；源文件 data/skills/design/sketch.md，请勿手改 -->

> 成熟度：**暂缓**（region=cn）｜版本 1.0.0｜as_of 2026-11-14｜来源：https://www.sketch.com/updates/ https://www.sketch.com/changelog/2025-2-3/

# Sketch（新项目暂缓）

当前版本：Sketch 仍在持续更新（2025 年发布 Athens 2025.1、Barcelona 2025.2、2025.3 系列等，支持 Frames、Stacks、Glass 效果）。图谱 D-01 交互设计工具栏原有「Sketch」。
判断理由：产品本身仍在维护，但仅支持 macOS 编辑、多人实时协作与研发交付生态弱于浏览器端协作工具，国内团队有 MasterGo / 即时设计、海外有 Figma，新项目判「暂缓」。存量项目照旧维护。

## 什么时候用
- 只在维护存量 Sketch 设计文件、组件库时使用。
- 团队全员 Mac、已有大量 Sketch 资产且短期无迁移排期时，可继续使用。

## 关键做法
- 存量文件保持在当前版本打开保存，避免多人使用不同大版本导致格式问题。
- 新增需求不要再扩充 Sketch 专属插件依赖，降低迁移成本。
- 交付给研发的标注改用导出 token 文件 + 截图标注，减少对 Zeplin / 蓝湖的强依赖。

## 常见坑
- Windows / Linux 同事无法编辑，评审靠导出图片，信息损失。
- 第三方插件随 Sketch 大版本升级经常失效。

## 迁移
- 见下方「替代」节。

## 替代
- 原因：协作与交付链路（实时多人编辑、Dev Mode / 研发模式、变量与多主题）已落后于浏览器端工具；跨平台受限。
- 替代项：region=cn 默认 `mastergo-jsdesign`；region=global 默认 `figma-variables-dev-mode`。
- 迁移建议：先迁组件库与样式（重建为变量 / 设计系统），再迁进行中的项目；MasterGo / 即时设计 / Figma 均可导入 .sketch 文件，导入后逐页核对自动布局与文字样式；历史稿件只读归档。
- 存量项目照旧维护，不擅自迁移，只在设计方案里提迁移建议。

## 最佳做法
- 迁移前先统一 token（见 design-tokens-dtcg），迁移后视觉回归抽查关键页面。

## CHANGELOG
- 2026-11-14 v1.0.0 首版；情报员自动核实（来源见 sources）
