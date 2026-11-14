---
name: finops-focus
description: "FinOps 云成本治理（FinOps Framework / FOCUS）（成熟度 采用，as_of 2026-11-14）：云账单月度上涨、说不清钱花在哪个业务 / 团队时。 适用角色：架构师 / 技术负责人、SRE 与安全工程师、后端工程师。"
---
<!-- generated-by: scripts/build.py；源文件 data/skills/architecture/finops-focus.md，请勿手改 -->

> 成熟度：**采用**（region=cn）｜版本 1.0.0｜as_of 2026-11-14｜来源：https://www.finops.org/framework/ https://focus.finops.org/ https://www.linuxfoundation.org/press/finops-foundation-launches-focus-1.3-to-deepen-cloud-and-saas-billing-transparency-announces-expanded-vendor-support-for-focus-1.2

# FinOps 云成本治理（FinOps Framework / FOCUS）

当前版本：FinOps Framework 2026 版（2026-03 更新，三个阶段 Inform / Optimize / Operate，四个领域，Scope 覆盖公有云、AI、SaaS、数据平台、数据中心等）；FOCUS 账单数据规范 1.3（2025-12 批准，新增分摊拆分、合同承诺数据集和数据新鲜度元数据）。图谱技术总监工具原有「成本看板」，本技能给出标准方法。
判断理由：FinOps 基金会（Linux 基金会旗下）官方框架和规范持续更新，AWS 等已原生导出 FOCUS 格式，方法论成熟，判「采用」。国内云对 FOCUS 导出的支持程度需逐家确认，不支持时按 FOCUS 字段自建映射。

## 什么时候用
- 云账单月度上涨、说不清钱花在哪个业务 / 团队时。
- 多云 / 混合云（阿里云 + AWS、自建 IDC）需要统一成本口径时。
- AI 推理、GPU 成本占比快速上升，需要单位经济（每次调用 / 每用户成本）时。

## 关键做法
- Inform：资源强制打标签（业务线、环境、owner），未打标资源 CI / 策略拦截；账单统一转成 FOCUS 字段入数仓。
- Optimize：闲置资源清理、规格调整（rightsizing）、预留实例 / 节省计划覆盖稳定负载、Spot / 抢占式实例跑可中断任务。
- Operate：按团队出月度成本报告和预算告警，成本进入架构评审与上线检查清单。
- K8s 成本按命名空间 / 工作负载分摊（如 OpenCost），共享成本按 FOCUS 1.3 的拆分方式分摊。
- 定义单位成本指标（如每千次请求成本、每 GPU 小时产出），比总额更能指导优化。

## 常见坑
- 只做一次性降本运动，没有持续机制，半年后反弹。
- 预留 / 承诺购买过量，业务下滑后成为沉没成本。
- 标签规范不统一（大小写、缩写），分摊口径无法对齐。

## 迁移
- 从人工 Excel 汇总账单 → 自动导出账单到数仓 + FOCUS 统一口径 + BI 看板。

## 最佳做法
- 成本数据给到工程师本人：每个服务的月成本显示在服务目录 / 门户里，比集中通报更有效。

## CHANGELOG
- 2026-11-14 v1.0.0 首版；情报员自动核实（来源见 sources）
