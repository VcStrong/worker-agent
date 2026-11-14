---
id: mastergo-jsdesign
name: 国内设计协作（MasterGo / 即时设计）
aliases: [MasterGo, 莫高设计, 即时设计, js.design, 国产 Figma]
roles: [ux-designer, product-manager]
maturity: 采用
maturity_by_region: {cn: 采用, global: 评估}
as_of: 2026-11-14
version: 1.0.0
sources:
  - https://mastergo.com/
  - https://mastergo.com/help
  - https://developers.mastergo.com/
  - https://js.design/
region: cn
replaces: []
replaced_by: []
from_graph: false
---

# 国内设计协作（MasterGo / 即时设计）

当前版本：均为 SaaS 持续发布（MasterGo 官网有更新日志与开发者中心；即时设计官网定位「专业 UI 设计工具，在线协作」）。
判断理由：国内访问稳定、中文支持、可私有化 / 企业内网部署，适合国内团队与对数据驻留有要求的企业，国内定「采用」；海外团队生态与插件不如 Figma，定「评估」。

## 什么时候用
- region=cn 的团队做 UI 设计、交互原型、设计系统和研发交付。
- 企业要求设计稿不出境、需要内网部署或 SSO / 权限审计。
- 需要和 Figma 互通的过渡期（两者均支持导入 Figma 文件）。

## 关键做法
- MasterGo（莫高设计）：设计系统统一组件与样式（一处修改全局同步，组件支持插槽）；研发模式可查看组件参数并复制 CSS / React 代码片段；支持文 / 图生成原型并用自然语言调整；有 D2C（设计工程化）与开放平台。
- 即时设计：在线协作 UI 设计，适合中小团队和个人；资源社区丰富。
- 团队统一一款主工具，另一款只用于接收外部文件，避免组件库分裂。
- 设计 token 按 W3C DTCG 格式维护在仓库里（见 design-tokens-dtcg），工具只是编辑入口，便于将来切换。

## 常见坑
- 从 Figma 导入后，自动布局、变量、插件效果可能丢失，导入后逐页核对。
- D2C 生成的代码只能当参考，组件化、状态管理仍由前端按工程规范写。
- 公有云版本也要确认企业数据协议、账号权限与离职回收流程。

## 迁移
- 从 Sketch 迁移：直接导入 .sketch 文件，重建组件库与样式（见 sketch 的「替代」节）。
- 从 Figma 迁移：先迁组件库与 token，再迁进行中的项目；历史稿件只读归档。

## 最佳做法
- 合规：私有化部署时由 SRE 负责备份与升级；公有云版本确认服务商 ICP 备案（MasterGo 官网备案号 京ICP备2023020756号-2）及数据存储在境内。
- 风险与回退：保留 token 文件和组件文档，工具切换时研发侧不受影响。

## CHANGELOG
- 2026-11-14 v1.0.0 首版；情报员自动核实（来源见 sources）
