---
id: figma-variables-dev-mode
name: Figma Variables 与 Dev Mode
aliases: [Figma Variables, Figma 变量, Dev Mode, 研发模式, Figma Modes]
roles: [ux-designer, frontend-engineer]
maturity: 试用
maturity_by_region: {cn: 试用, global: 采用}
as_of: 2026-11-14
version: 1.0.0
sources:
  - https://help.figma.com/hc/articles/15145852043927
  - https://help.figma.com/hc/en-us/sections/15023066873239-Dev-Mode
  - https://help.figma.com/hc/en-us/articles/27882809912471
region: global
replaces: []
replaced_by: []
from_graph: false
---

# Figma Variables 与 Dev Mode

当前版本：Figma 为 SaaS 持续发布；Variables（变量 / 集合 / 模式）与 Dev Mode 均为正式功能。
判断理由：官方文档完整、海外设计协作事实标准，海外定「采用」；国内团队受访问稳定性与数据出境影响，定「试用」，默认用 mastergo-jsdesign。

## 什么时候用
- 搭设计系统：颜色、间距、圆角、字号用变量统一管理，替代图谱里的「Variants / Token 插件」手工方案。
- 一套稿子要支持多主题（亮 / 暗、品牌 A / B）、多端密度：用变量的 Modes 切换。
- 设计交付给研发：用 Dev Mode 替代 Zeplin / 蓝湖式的标注切图。

## 关键做法
- 变量分两层：原始值（color/blue/500）和语义别名（color/bg/primary → 引用原始值），组件只引用语义层。
- 集合按用途拆（Primitives、Semantic、Spacing），Modes 只放在语义层集合上。
- Dev Mode 里研发可看到变量名而非裸值；有匹配的裸值时 Dev Mode 会提示建议变量，交付前清理掉裸值。
- 设计稿用「Ready for dev」状态标记可开发的页面，变更后用对比功能告知研发改了什么。
- 变量导出给研发：按 W3C DTCG 格式输出 token 文件（见 design-tokens-dtcg），由 Style Dictionary 等工具生成各端代码。

## 常见坑
- 变量命名一旦被代码引用就很难改，命名规范要在第一批变量前定稿。
- 只建变量不绑定组件，等于没用；用检查插件或 Dev Mode 抽查裸值。
- Dev Mode 需要对应席位（Dev seat / Full seat），研发人数多时先算成本。

## 迁移
- 从 Styles + 插件 token 迁移：先把颜色 / 文字样式映射为变量，再逐个组件替换引用；旧 Styles 保留一个版本周期。
- 从 Zeplin / 蓝湖标注迁移：新需求起改用 Dev Mode 链接，旧项目文档不回迁。

## 最佳做法
- 设计评审加一条检查：新页面裸色值数为 0。
- 风险与回退：Figma 访问异常时，切到已同步的 MasterGo 文件或导出的 token 文件，研发按 token 文件开发不受影响。

## CHANGELOG
- 2026-11-14 v1.0.0 首版；情报员自动核实（来源见 sources）
