---
name: playwright-test-agents
description: "AI 生成测试用例（Playwright Test Agents）（成熟度 试用，as_of 2026-11-14）：新功能上线前，从 PRD / 验收标准快速生成测试计划和 E2E 用例初稿。 适用角色：测试专家、前端工程师、AI 应用 / Agent 工程师。"
---
<!-- generated-by: scripts/build.py；源文件 data/skills/qa/playwright-test-agents.md，请勿手改 -->

> 成熟度：**试用**（region=cn）｜版本 1.0.0｜as_of 2026-11-14｜来源：https://github.com/microsoft/playwright/releases/tag/v1.56.0 https://github.com/microsoft/playwright/blob/main/docs/src/test-agents-js.md

# AI 生成测试用例（Playwright Test Agents）

当前版本：Playwright 1.56（2025-10-06）引入 Test Agents，当前随 Playwright v1.65.1 发布。
判断理由：官方内置能力，可大幅缩短从测试计划到用例代码的时间，但生成质量依赖 LLM 与被测应用稳定性，需人工评审，定「试用」。

## 什么时候用
- 新功能上线前，从 PRD / 验收标准快速生成测试计划和 E2E 用例初稿。
- 存量用例因 UI 改版大面积失败，用 healer 批量修复定位器。
- 补齐回归覆盖率（先生成，再人工筛选入库）。

## 关键做法
- 三个 agent：planner 探索应用、产出 Markdown 测试计划；generator 把计划转成 Playwright Test 代码；healer 运行用例并自动修复失败。三者可独立使用。
- 初始化：`npx playwright init-agents --loop=claude`（另有 vscode、opencode 等宿主），生成 agent 定义文件，Playwright 升级后重新执行以获取最新定义。
- 提供 seed 测试（登录、进入起始页）让 agent 在正确上下文中探索。
- 测试计划（specs/ 下的 Markdown）先由测试专家评审，再让 generator 生成代码。
- 生成的用例按 playwright 技能包规范评审：断言是否验证业务结果、是否有硬等待、数据是否隔离。

## 常见坑
- healer 可能把「真实缺陷」当成定位器变化「修好」，导致漏测；healer 的改动必须走代码评审，断言变化要特别标注。
- 在生产或共享测试环境让 agent 自由探索，可能误触下单、删除等操作，只在隔离环境运行。
- 不要把真实用户数据、密钥放进提示词或 seed 测试。

## 迁移
- 从「人工写用例文档 + 手工转脚本」迁移：先在 1 个模块试点，对比生成用例的有效率与人工耗时，再推广。

## 最佳做法
- 统计生成用例的「采纳率」和「误修率」，作为是否升级为采用的依据。
- 风险与回退：生成质量不达标时，只保留 planner 产出的测试计划，代码回到人工编写。

## CHANGELOG
- 2026-11-14 v1.0.0 首版；情报员自动核实（来源见 sources）
