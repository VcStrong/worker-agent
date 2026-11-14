---
id: serverless-aws-lambda
name: AWS Lambda（海外 Serverless）
aliases: [Lambda, AWS Lambda, Lambda Managed Instances, Lambda durable functions, Serverless]
roles: [backend-engineer, architect]
maturity: 采用
maturity_by_region: {cn: 试用, global: 采用}
as_of: 2026-11-14
version: 1.0.0
sources:
  - https://docs.aws.amazon.com/lambda/latest/dg/welcome.html
  - https://aws.amazon.com/about-aws/whats-new/2026/07/aws-lambda-durable-custom-sdk/
  - https://aws.amazon.com/about-aws/whats-new/2026/09/aws-lambda-90-minute-function/
  - https://aws.amazon.com/blogs/compute/serverless-icymi-q3-2026/
  - https://www.amazonaws.cn/
region: global
replaces: []
replaced_by: []
from_graph: false
---

# AWS Lambda（海外 Serverless）

当前状态：Lambda 持续迭代。2025 年底推出 durable functions（检查点 + 重放，可长时间暂停等待）和 Lambda Managed Instances（在托管 EC2 上运行函数）；2026-07 durable functions 支持自定义 Durable Execution SDK，2026-09 Managed Instances 的异步 / 事件源调用超时提升到 90 分钟。
判断理由：海外 Serverless 事实标准，文档、生态与工具链最完整，region=global 判「采用」；国内业务需单独开 AWS 中国区账号（由合作方运营，功能与上新节奏和海外区不同），region=cn 判「试用」，默认改用 `serverless-cn-fc`。

## 什么时候用
- 海外业务的事件处理、API 后端、定时任务、数据管道胶水层。
- 多步骤编排、需要等待人工审批或外部回调：durable functions 或 Step Functions。
- 稳定高吞吐、又想保留 Lambda 编程模型：Managed Instances（按实例计费，适合可预测负载）。

## 关键做法
- 用 AWS SAM / CDK / Terraform 管理；每个函数最小权限 IAM 角色。
- 冷启动：Java 用 SnapStart，延迟敏感接口用预置并发；Node / Python / Go 优先。
- 数据库访问走 RDS Proxy；异步调用配置 DLQ / on-failure destination。
- 观测：开启 Lambda 的 OpenTelemetry / X-Ray 集成，日志结构化输出到 CloudWatch。

## 常见坑
- durable functions 依赖确定性重放，函数体内随机数、当前时间、外部调用必须走 SDK 提供的 step 包装。
- Managed Instances 是多并发模型，同一实例并发处理多个请求，全局变量要线程安全。
- 海外区新功能不一定在中国区（北京、宁夏）可用，上线前查中国区文档。
- 国内用户访问海外 Lambda 延迟高且不稳定，不要把面向国内用户的接口放在海外区。

## 迁移
- 国内业务迁海外：函数逻辑与触发适配层分离，事件用 CloudEvents 结构，FC / SCF ↔ Lambda 只换适配层。
- 从 EC2 / 容器迁 Lambda：先迁异步、低频任务，核心同步链路评估成本后再动。

## 最佳做法
- 海外上线前确认数据驻留要求（GDPR 等）；中国区账号需 ICP 备案，跨境传输个人信息需走数据出境合规流程。

## CHANGELOG
- 2026-11-14 v1.0.0 首版；情报员自动核实（来源见 sources）
