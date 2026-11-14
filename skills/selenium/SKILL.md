---
name: selenium
description: "Selenium WebDriver（新 Web E2E 暂缓）（成熟度 暂缓，as_of 2026-11-14）：维护存量 Selenium 用例与 Grid 基础设施。 适用角色：测试专家。"
---
<!-- generated-by: scripts/build.py；源文件 data/skills/qa/selenium.md，请勿手改 -->

> 成熟度：**暂缓**（region=cn）｜版本 1.0.0｜as_of 2026-11-14｜来源：https://www.selenium.dev/ https://github.com/SeleniumHQ/selenium/releases

# Selenium WebDriver（新 Web E2E 暂缓）

当前版本：Selenium 4.52.0（2026-10-29，GitHub Releases），项目仍活跃维护。图谱 Q-02 原有「Selenium / Appium」。
判断理由：Selenium 本身没有过时，但新 Web 端到端项目用 Playwright 在自动等待、调试（Trace）、并行与环境安装上明显更省力，新 Web E2E 项目判「暂缓」。Appium（移动端，基于 WebDriver 协议）不在此列，继续使用。存量项目照旧维护。

## 什么时候用
- 维护存量 Selenium 用例与 Grid 基础设施。
- 必须使用 W3C WebDriver 标准协议对接第三方平台、或需要 Java / C# 等语言且团队已有成熟 Selenium 框架时。

## 关键做法
- 存量项目升级到 Selenium 4 最新版，使用 Selenium Manager 自动管理浏览器驱动。
- 统一显式等待封装，清理散落的 `Thread.sleep`。
- 新增用例不再扩充 Selenium 专属的自研工具层，降低迁移成本。

## 常见坑
- 隐式等待与显式等待混用导致超时不可预测。
- 浏览器与驱动版本不匹配导致批量失败（Selenium Manager 可缓解）。

## 迁移
- 见下方「替代」节。

## 替代
- 原因：同等用例在 Playwright 中代码更少、更稳定（自动等待、web-first 断言），自带 Trace、并行、截图对比，环境安装更简单。
- 替代项：新 Web E2E 项目默认 `playwright`。
- 迁移建议：按模块分批迁移，先迁冒烟与高 flaky 用例；Page Object 结构可保留，定位器改为语义定位、等待逻辑全部删除改用自动等待；迁移期两套用例并行跑 2 周，对比通过率后下线旧用例；单独立项，不和业务测试混做。
- 存量项目照旧维护，不擅自迁移，只在测试方案里提迁移建议。

## 最佳做法
- 每季度统计 Selenium 用例的 flaky 率与维护工时，作为迁移优先级依据。

## CHANGELOG
- 2026-11-14 v1.0.0 首版；情报员自动核实（来源见 sources）
