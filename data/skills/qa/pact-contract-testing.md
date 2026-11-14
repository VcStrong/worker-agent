---
id: pact-contract-testing
name: 契约测试（Pact）
aliases: [Pact, 契约测试, consumer-driven contract, CDC, Pact Broker, PactFlow]
roles: [qa-expert, backend-engineer]
maturity: 采用
as_of: 2026-11-14
version: 1.0.0
sources:
  - https://docs.pact.io/
  - https://github.com/pact-foundation/pact-js/releases
  - https://github.com/pact-foundation/pact_broker/releases
  - https://docs.pactflow.io/docs/bi-directional-contract-testing
region: both
replaces: []
replaced_by: []
from_graph: false
---

# 契约测试（Pact）

当前版本：pact-js v17.1.4（2026-09-07）；Pact Broker v2.124.0（2026-11-11）。PactFlow（SmartBear 商业版）提供双向契约测试。
判断理由：开源、多语言实现齐全、社区和文档成熟，是微服务 / 前后端分离接口兼容性测试的主流方案，定「采用」。

## 什么时候用
- 前后端分离、微服务之间、App 与服务端之间，接口经常变、联调成本高。
- 服务提供方有多个消费方，想知道「改这个字段会不会搞坏谁」。
- 想减少依赖完整联调环境的端到端测试数量。

## 关键做法
- 消费方驱动：消费方单测里用 Pact mock 声明请求和期望响应，生成 pact 文件。
- 契约发布到 Pact Broker，提供方 CI 拉取契约做验证（provider verification）。
- 部署前用 `can-i-deploy` 判断版本组合是否兼容，部署后 `record-deployment` 记录环境。
- 只写消费方真正用到的字段，用匹配器（类型 / 正则）而不是写死值。
- 提供方用 provider states 准备数据，不依赖共享测试库。

## 常见坑
- 把契约测试写成功能测试（断言业务逻辑），契约会变得脆弱，业务逻辑留给提供方单测。
- 不接 Broker、只在本地传文件，失去版本兼容判断的价值。
- 双向契约（OpenAPI 对比消费方契约）是 PactFlow 商业功能，开源 Broker 不支持；且只校验同步 HTTP 交互。

## 迁移
- 从「全靠联调环境 E2E」迁移：先选变更最频繁的 1~2 对服务试点，把对应 E2E 下沉为契约测试。
- 已有 OpenAPI 规范的团队：可先用 OpenAPI 做 schema 校验，再逐步引入消费方契约。

## 最佳做法
- 把 `can-i-deploy` 设为发布流水线的门禁，失败即阻断。
- 契约变更在 PR 描述中注明影响的消费方，评审时 @ 对应负责人。

## CHANGELOG
- 2026-11-14 v1.0.0 首版；情报员自动核实（来源见 sources）
