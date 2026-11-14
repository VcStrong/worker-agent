---
id: cloud-aws
name: 海外公有云选型（AWS 为默认）
aliases: [AWS, Amazon Web Services, 海外云, 出海云服务, 云服务选型]
roles: [architect, backend-engineer, sre-security]
maturity: 采用
maturity_by_region: {cn: 试用, global: 采用}
as_of: 2026-11-14
version: 1.0.0
sources:
  - https://aws.amazon.com/what-is-aws/
  - https://aws.amazon.com/about-aws/global-infrastructure/regions_az/
  - https://docs.aws.amazon.com/wellarchitected/latest/framework/welcome.html
  - https://www.amazonaws.cn/en/about-aws/china/
region: global
replaces: []
replaced_by: []
from_graph: false
---

# 海外公有云选型（AWS 为默认）

当前状态：AWS 全球区域与可用区覆盖最广，官方 Well-Architected Framework 提供架构评审基线；AWS 中国区（北京、宁夏）由本地合作方运营，账号体系与全球区独立。
判断理由：出海业务的默认云，产品线与生态最完整，region=global 判「采用」；面向国内用户时需用 AWS 中国区（独立账号、需 ICP 备案、部分服务和新功能晚于全球区），region=cn 判「试用」，默认改用 `cloud-cn-providers`。Azure、GCP 在特定场景（微软生态、数据分析 / AI）可作为备选，按评估对待。

## 什么时候用
- 面向海外用户的出海 App / SaaS / 游戏后端。
- 客户合同或当地法规要求数据驻留在特定国家 / 地区。
- 需要成熟的全球化能力：多区域部署、全球加速、CDN 边缘计算。

## 关键做法
- 多账号治理：AWS Organizations + Control Tower，按环境 / 业务分账号，SCP 限制高危操作。
- 架构评审对照 Well-Architected 六大支柱（卓越运营、安全、可靠性、性能效率、成本优化、可持续性）。
- 就近选区域：东南亚用新加坡 / 雅加达等，欧洲用法兰克福 / 爱尔兰，按用户分布实测延迟。
- 基础设施即代码（CDK / Terraform）；与国内云共用 K8s、OTel、Terraform 模块，降低双栈维护成本。

## 合规要点
- 欧盟用户数据按 GDPR 处理（数据驻留、DPA、删除权）；其他市场按当地数据保护法。
- 国内主体向海外传输个人信息，按国家网信办数据跨境规定办理；国内用户数据不要默认放海外区。
- 使用 AWS 中国区时需 ICP 备案，按中国区文档确认服务可用性。

## 常见坑
- 跨区域、跨可用区、NAT 网关流量费被低估。
- 国内办公网络访问海外控制台和镜像仓库不稳定，CI/CD 要准备镜像加速。
- 把国内云的产品名、配额习惯直接套到 AWS，忽略服务配额（Service Quotas）申请周期。

## 迁移
- 国内业务出海：复用容器镜像与 IaC 模块，数据层按区域独立部署，不做跨境实时同步。

## 最佳做法
- 出海前先做数据分类分级，决定哪些数据可以出境、存在哪个区域，写进架构 ADR。

## CHANGELOG
- 2026-11-14 v1.0.0 首版；情报员自动核实（来源见 sources）
