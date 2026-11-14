---
id: platform-engineering-backstage
name: 平台工程与内部开发者门户（IDP / Backstage）
aliases: [平台工程, Platform Engineering, IDP, Internal Developer Portal, Backstage, 黄金路径]
roles: [architect, sre-security]
maturity: 试用
as_of: 2026-11-14
version: 1.0.0
sources:
  - https://backstage.io/
  - https://github.com/backstage/backstage/releases
  - https://www.cncf.io/projects/backstage/
region: both
replaces: []
replaced_by: []
from_graph: false
---

# 平台工程与内部开发者门户（IDP / Backstage）

当前版本：Backstage v1.56.x（2026-11，月度发布，v1.57 预发布中），CNCF 孵化项目（2022-03 起）。新后端系统已是默认（旧后端系统支持已移除），新前端系统正在推广。
判断理由：平台工程方向明确、Backstage 是开源 IDP 的主流选择；但它是框架而非开箱即用产品，需要专职团队写插件、维护目录数据，中小团队投入产出比不确定，判「试用」。风险：建成「没人用的门户」；回退方案：保留 Wiki 服务目录 + 脚手架仓库模板，门户下线不影响研发流程。

## 什么时候用
- 服务数 > 50、团队 > 5 个，服务归属、文档、依赖关系散落难找时。
- 想把新建服务、申请资源、上线流程做成「黄金路径」自助化时。
- 研发经理 / 技术总监要统一看服务健康度、合规评分（Scorecard）时。

## 关键做法
- 先定平台产品目标与用户（业务研发），用 DORA / 开发者满意度度量，不以「上线门户」为目标。
- Software Catalog：每个仓库放 `catalog-info.yaml`（owner、system、lifecycle），CI 校验必填。
- Software Templates：新服务脚手架默认带 CI、OpenTelemetry、Dockerfile、Argo CD 应用定义。
- TechDocs：文档与代码同仓，docs-as-code。
- 按新后端系统开发插件，升级跟官方月度节奏，避免一次跨多个版本。

## 常见坑
- 目录数据靠手填，很快过期：必须从 Git、K8s、云资源自动同步。
- 一次铺太多插件，维护成本超过团队能力。
- 国内网络环境下 npm 依赖拉取慢、部分插件依赖海外 SaaS，需提前准备镜像与替代。

## 迁移
- 从 Wiki / 表格服务目录迁入：先批量生成 `catalog-info.yaml` 提 PR 给各团队确认 owner。
- 已有自研门户：评估复用其 API 作为 Backstage 插件数据源，不必推倒重来。

## 最佳做法
- 先做一条最痛的黄金路径（如「新建一个后端服务到上线」）跑通，再扩展。

## CHANGELOG
- 2026-11-14 v1.0.0 首版；情报员自动核实（来源见 sources）
