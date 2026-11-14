---
name: serverless-cn-fc
description: "国内 Serverless 函数计算（阿里云 FC / 腾讯云 SCF / 华为云 FunctionGraph）（成熟度 采用，as_of 2026-11-14）：事件驱动：OSS / COS / OBS 文件处理、消息队列消费、定时任务、Webhook。 适用角色：后端工程师、架构师 / 技术负责人。"
---
<!-- generated-by: scripts/build.py；源文件 data/skills/backend/serverless-cn-fc.md，请勿手改 -->

> 成熟度：**采用**（region=cn）｜版本 1.0.0｜as_of 2026-11-14｜来源：https://help.aliyun.com/zh/functioncompute/ https://help.aliyun.com/document_detail/2539903.html https://cloud.tencent.com/document/product/583/9199 https://support.huaweicloud.com/functiongraph/ https://help.aliyun.com/zh/icp-filing/

# 国内 Serverless 函数计算（阿里云 FC / 腾讯云 SCF / 华为云 FunctionGraph）

当前版本：阿里云函数计算 FC 3.0（2023-10 推出，取消「服务」层级，函数为一级资源，支持 GPU 函数）；腾讯云云函数 SCF（事件函数 / Web 函数，支持镜像部署）；华为云 FunctionGraph（产品文档 2025-08 更新）。
判断理由：三家官方文档完整、按量计费、与本云事件源深度集成，面向国内用户的业务默认用国内函数计算，region=cn 判「采用」；海外业务默认走 AWS Lambda（见 `serverless-aws-lambda`），国内函数计算在 global 下只作「评估」。

## 什么时候用
- 事件驱动：OSS / COS / OBS 文件处理、消息队列消费、定时任务、Webhook。
- 流量波峰明显、长期低负载的 API（活动页后端、运营工具）。
- AI 推理小流量场景：FC GPU 函数按需拉起，避免长期占卡。
- 不适合：长连接、强状态、稳定高 QPS 核心链路（成本反而高于容器）。

## 关键做法
- 选本业务主云的函数服务，事件源、VPC、日志都在同一云内，减少跨云延迟与流量费。
- 用 Serverless Devs（阿里云）/ Serverless Framework 或 Terraform 管理函数配置，代码与配置进 Git。
- 冷启动敏感接口：配置预留实例 / 最小实例数；Java 优先用 GraalVM 原生镜像或换 Go / Node。
- 函数内访问数据库走连接代理或 Serverless 版数据库，防止并发扩容打爆连接数。

## 常见坑
- 对外提供 HTTP 访问必须绑定已 ICP 备案的自定义域名，默认域名可能被强制下载或限制访问。
- 各家超时上限、并发配额、包大小不同，上线前对照官方「约束与限制」提工单调额度。
- 只看单次调用价格，忽略公网流量、日志服务、预留实例的费用。
- 同一函数混用多种触发器，权限过宽（RAM / CAM 角色给了 `*`）。

## 迁移
- FC 2.0 → 3.0：按官方《3.0 和 2.0 版本差异及兼容性说明》迁移，注意「服务」层级取消后的权限与日志配置变化。
- 跨云迁移：业务逻辑与触发适配层分离，用 CloudEvents 格式抽象事件。

## 最佳做法
- 合规：面向公众的服务做 ICP 备案；涉及个人信息按《个人信息保护法》做告知同意与数据最小化，日志脱敏。
- 每个函数设置成本告警与并发上限，防止被刷导致账单失控。

## CHANGELOG
- 2026-11-14 v1.0.0 首版；情报员自动核实（来源见 sources）
