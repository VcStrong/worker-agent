---
id: cloud-device-testing-global
name: 移动端云真机自动化（海外：Firebase Test Lab / BrowserStack）
aliases: [Firebase Test Lab, Robo test, BrowserStack, App Automate, 云真机]
roles: [qa-expert, client-engineer]
maturity: 评估
maturity_by_region: {cn: 评估, global: 采用}
as_of: 2026-11-14
version: 1.0.0
sources:
  - https://firebase.google.com/docs/test-lab
  - https://firebase.google.com/docs/test-lab/android/robo-ux-test
  - https://www.browserstack.com/docs/app-automate
region: global
replaces: []
replaced_by: []
from_graph: true
---

# 移动端云真机自动化（海外：Firebase Test Lab / BrowserStack）

当前版本：均为 SaaS 持续发布。Firebase Test Lab 支持 Android 仪器测试、Robo 自动探索测试和 iOS 测试（iOS Robo 为 beta），Google Play 预发布报告即基于 Robo test；BrowserStack App Automate 支持 Appium、Espresso、XCUITest 等框架在真机上运行。
判断理由：海外机型覆盖广、与 Google Play / CI 集成好，海外定「采用」；国内访问受限、缺少国内厂商定制 ROM 覆盖，国内定「评估」，默认用 cloud-device-testing-cn。

## 什么时候用
- 面向海外市场的 App 发版兼容性测试与自动化回归。
- 无脚本时用 Robo test 做自动探索，快速发现崩溃。
- 需要真机跑 Web 跨浏览器测试（BrowserStack Automate 可配合 Playwright / Selenium）。

## 关键做法
- Firebase Test Lab：用 gcloud CLI 在 CI 里触发 `gcloud firebase test android run`，指定设备矩阵；Robo 可用 Robo script 引导登录等关键路径，超时按应用复杂度设（简单 ≥120 秒，中等 ≥300 秒）。
- BrowserStack：上传 App 后用远程 WebDriver 跑 Appium / 原生框架用例，结果和视频回写 CI。
- 设备矩阵按海外市场机型分布选取，包含最低支持系统版本和最新系统 beta。
- 失败用例保留视频、日志、性能数据并附到缺陷单。

## 常见坑
- 测 alpha / beta 渠道包时，先去掉授权校验（licensing check），否则 Robo 卡在校验页。
- 深链接找不到匹配 Activity 时 Test Lab 会忽略该链接，不报错。
- 按设备分钟计费，矩阵过大成本失控；PR 跑虚拟设备，发版跑真机。

## 迁移
- 国内外同一 App：国内包跑 cloud-device-testing-cn，海外包（含 GMS）跑本方案，用例脚本保持同一套 Appium / Espresso 代码。

## 最佳做法
- 合规：测试包使用测试环境与假数据，避免把个人信息上传到境外平台。
- 风险与回退：平台不可用时降级为本地模拟器 + 自建设备跑冒烟。

## CHANGELOG
- 2026-11-14 v1.0.0 首版；情报员自动核实（来源见 sources）
