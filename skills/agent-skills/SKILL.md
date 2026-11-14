---
name: agent-skills
description: "Agent Skills（SKILL.md 技能包）（成熟度 采用，as_of 2026-11-14）：把团队流程、领域知识、模板、脚本打包给 Agent 按需加载（如「按公司规范写 PRD」「生成合规报告」）。 适用角色：AI 应用 / Agent 工程师、AI 产品经理。"
---
<!-- generated-by: scripts/build.py；源文件 data/skills/ai-app/agent-skills.md，请勿手改 -->

> 成熟度：**采用**（region=cn）｜版本 1.0.0｜as_of 2026-11-14｜来源：https://agentskills.io/ https://agentskills.io/specification https://code.claude.com/docs/en/agent-sdk/skills

# Agent Skills（SKILL.md 技能包）

## 成熟度判断
- 采用：Anthropic 于 2025-12 把 Agent Skills 作为开放标准发布（agentskills.io），已被大量 Agent 产品和 IDE 采纳；Claude Agent SDK 原生从 .claude/ 目录加载技能。格式简单（文件夹 + SKILL.md），迁移成本低。
- 治理：官方站点称标准对社区开放贡献，规范与讨论在 GitHub agentskills/agentskills。

## 什么时候用
- 把团队流程、领域知识、模板、脚本打包给 Agent 按需加载（如「按公司规范写 PRD」「生成合规报告」）。
- 系统提示词过长、想按任务懒加载知识时。

## 关键做法
- 结构：skill-name/SKILL.md（必填，frontmatter 至少 name、description）+ 可选 scripts/、references/、assets/。
- 渐进式披露三步：启动时只加载 name + description → 任务匹配时读 SKILL.md 全文 → 执行时再按需读引用文件或运行脚本。
- description 写成「什么时候用我」，包含触发词，决定能否被正确选中。
- SKILL.md 正文保持精简，大段资料放 references/，由正文指向。
- 技能纳入 Git 版本管理和评审，像代码一样发版。

## 常见坑
- description 含糊，技能永远不被触发或被误触发。
- 把所有内容塞进 SKILL.md，失去按需加载的意义。
- 技能里的脚本未审查就执行，等同引入不可信代码。
- 从网上下载的第三方技能可能含恶意指令，安装前需审查。

## 迁移
- 冗长的系统提示词 / 自定义指令：按任务拆成多个技能，主提示词只留身份和通用规则。
- 私有插件格式：改为 SKILL.md 标准格式，即可在多个兼容客户端复用。

## 最佳做法
- 每个技能配 3~5 条触发测试用例，验证 description 的路由效果。

## CHANGELOG
- 2026-11-14 v1.0.0 首版；情报员自动核实（来源见 sources）
