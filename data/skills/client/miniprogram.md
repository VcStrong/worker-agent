---
id: miniprogram
name: 小程序（微信小程序 / uni-app / Taro）
aliases: [微信小程序, 小程序, uni-app, uni-app x, Taro, Skyline, glass-easel]
roles: [client-engineer, frontend-engineer]
maturity: 采用
as_of: 2026-11-14
version: 1.0.0
sources:
  - https://developers.weixin.qq.com/miniprogram/dev/framework/release/v3.html
  - https://developers.weixin.qq.com/miniprogram/dev/framework/runtime/skyline/changelog.html
  - https://developers.weixin.qq.com/miniprogram/product/record/guidelines.html
  - https://doc.dcloud.net.cn/uni-app-x/app-harmony/
  - https://github.com/NervJS/taro/releases
region: cn
replaces: []
replaced_by: []
from_graph: false
---

# 小程序（微信小程序 / uni-app / Taro）

当前版本：微信基础库 3.17.x（3.17.3 于 2026-08-20），Skyline 渲染引擎下默认组件框架为 glass-easel；uni-app x 自 4.61 起支持编译为鸿蒙原生应用（要求 API 14+，蒸汽模式 API 20+）；Taro 4.x（GitHub Releases 已到 v4.3.0），4.1.0 起支持鸿蒙 C-API 方案。
判断理由：国内流量入口刚需，三者均有官方文档与持续发版，判「采用」（国内）。

## 什么时候用
- 只做微信：原生小程序（WXML + TS），性能和新能力最先可用。
- 一套代码多端（微信 / 支付宝 / 抖音 / H5 / App / 鸿蒙）：Vue 技术栈选 uni-app（含 uni-app x），React 技术栈选 Taro。
- 重交互、长列表、动画多的页面：评估开启 Skyline 渲染。

## 关键做法
- 原生小程序用 TypeScript 模板，组件化 + 分包加载（主包 ≤2MB 硬限制），首屏只放主流程。
- Skyline：在 `app.json` / 页面配置 `renderer: "skyline"`，按页面灰度，保留 WebView 回退。
- 跨端框架用条件编译（`#ifdef MP-WEIXIN` / `process.env.TARO_ENV`）隔离平台差异，平台专属能力封装到适配层。
- uni-app x 出鸿蒙包需本地安装 DevEco Studio 编译（不支持云打包），发行必须配置发布证书。

## 常见坑
- 合规：在中国境内提供服务的小程序必须完成工信部备案（平台初审 → 12381 短信 24 小时内核验 → 通管局审核），未备案不能上线；涉及用户信息须配置隐私保护指引并按需弹授权。
- 基础库版本碎片：用 `wx.canIUse` 与后台「最低基础库版本」配合，不要假设用户已更新。
- 跨端框架升级小版本也可能破坏编译（如 Taro 4.1.3/4.1.4 鸿蒙编译报错），锁版本、升级前全端回归。
- 样式：小程序不支持部分现代 CSS（如 Tailwind v4 依赖的特性），需单独适配。

## 迁移
- 原生 WebView 渲染 → Skyline：按页面迁，先迁新页面，注意 Skyline 下部分 WXSS 与组件行为差异。
- uni-app（Vue 2）→ uni-app Vue 3 / uni-app x；Taro 3 → Taro 4：按官方升级说明处理，鸿蒙端改走 Taro 4 的 ArkUI / C-API 方案（3.x JS UI 适配已停止更新）。

## 最佳做法
- 包体积、首屏时间、白屏率纳入发版检查，分包预下载只给高转化路径。

## CHANGELOG
- 2026-11-14 v1.0.0 首版；情报员自动核实（来源见 sources）
