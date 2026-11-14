---
name: playwright
description: "Playwright（Web 端到端测试）（成熟度 采用，as_of 2026-11-14）：Web / H5 / 管理后台的端到端回归、冒烟测试、跨浏览器测试。 适用角色：测试专家、前端工程师。"
---
<!-- generated-by: scripts/build.py；源文件 data/skills/qa/playwright.md，请勿手改 -->

> 成熟度：**采用**（region=cn）｜版本 1.0.0｜as_of 2026-11-14｜来源：https://playwright.dev/ https://github.com/microsoft/playwright/releases

# Playwright（Web 端到端测试）

当前版本：v1.65.1（2026-11-13，GitHub Releases）；1.65 新增在 Bun 下运行测试（`bunx --bun playwright test`）。
判断理由：微软官方维护、约每月一个小版本，Chromium / Firefox / WebKit 三引擎、自动等待、Trace 调试成熟，定「采用」，新 Web E2E 项目默认首选。

## 什么时候用
- Web / H5 / 管理后台的端到端回归、冒烟测试、跨浏览器测试。
- 接口测试（APIRequestContext）与 UI 测试放一个框架里。
- 组件级测试、视觉回归（截图对比）。
- 不适合原生 App（用 Appium / Espresso / XCUITest，见 cloud-device-testing-cn / cloud-device-testing-global）。

## 关键做法
- 定位器优先语义：`getByRole`、`getByLabel`、`getByTestId`，不用易变的 CSS / XPath。
- 依赖自动等待和 web-first 断言（`expect(locator).toBeVisible()`），禁止 `waitForTimeout` 硬等待。
- 登录态用 storageState 复用（setup project），测试之间数据隔离、可并行。
- CI 里开 `retries: 2`、`trace: 'on-first-retry'`，失败时看 Trace Viewer 定位。
- 按优先级打标签（@smoke / @regression），PR 只跑冒烟，夜间跑全量。

## 常见坑
- 共享测试账号 / 数据导致并行时相互干扰，用造数接口每条用例独立造数。
- 截图对比在不同 OS / 字体下有像素差，基线图在 CI 同一 Docker 镜像中生成。
- 浏览器版本随 Playwright 版本绑定，升级 Playwright 后要 `npx playwright install`。

## 迁移
- 从 Selenium 迁移：见 selenium 的「替代」节；先迁冒烟用例，Page Object 结构可沿用，等待逻辑全部改为自动等待。
- 从 Cypress 迁移：多标签页、跨域、Safari（WebKit）场景收益最大，优先迁这些用例。

## 最佳做法
- AI 辅助生成 / 修复用例见 playwright-test-agents，生成结果仍按本节规范评审。
- flaky 用例当天隔离（`test.fixme`）并建缺陷，不允许长期重试掩盖。

## CHANGELOG
- 2026-11-14 v1.0.0 首版；情报员自动核实（来源见 sources）
