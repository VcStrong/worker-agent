---
id: opentelemetry
name: OpenTelemetry（统一可观测：Trace / Metrics / Logs）
aliases: [OTel, OpenTelemetry, 链路追踪, OTLP, Collector]
roles: [architect, backend-engineer, sre-security]
maturity: 采用
as_of: 2026-11-14
version: 1.0.0
sources:
  - https://opentelemetry.io/docs/
  - https://opentelemetry.io/status/
  - https://github.com/open-telemetry/opentelemetry-collector-releases/releases
  - https://opentelemetry.io/blog/2026/obi-v1-release/
region: both
replaces: []
replaced_by: []
from_graph: false
---

# OpenTelemetry（统一可观测：Trace / Metrics / Logs）

当前版本：Collector v0.165.0（2026-11-07）；SDK 状态（官方状态页）：Java 的 Traces / Metrics / Logs 均 Stable、Profiles 开发中；Go 的 Traces / Metrics Stable、Logs RC；Python 的 Traces / Metrics Stable、Logs 开发中。eBPF 零代码插桩 OBI 已发布 v1.0.0（2026-10-30）。图谱后端 / 架构原有「日志与链路追踪」「链路追踪」，本技能给出统一标准。
判断理由：CNCF 项目，厂商中立的事实标准，国内外主流可观测平台普遍提供 OTLP 接入（接入前以各厂商文档为准），判「采用」。

## 什么时候用
- 新服务默认接入 OTel，取代各厂商私有 Agent / SDK。
- 多语言微服务需要端到端 Trace、Trace 与日志关联排障时。
- 想保留切换后端存储（自建 Grafana 栈 ↔ 云 APM）的自由时。

## 关键做法
- Java 用 OTel Java Agent 零代码插桩；Spring Boot 4.1 起可直接读取 OTel 标准环境变量；Go 用 SDK + 官方 instrumentation 库，或用 OBI 先零代码兜底。
- 统一资源属性：`service.name`、`service.version`、`deployment.environment.name`，按语义约定命名。
- 部署 Collector（Agent 模式 DaemonSet + Gateway 模式集中处理），在 Collector 里做采样、脱敏、路由，应用只管 OTLP 上报。
- 采样：入口头部采样 + Collector 尾部采样（错误、慢请求全留）。
- 日志里注入 trace_id / span_id，实现 Trace ↔ 日志跳转。

## 常见坑
- 高基数属性（用户 ID、URL 带参数）作为指标标签，导致时序爆炸、费用飙升。
- 只在部分服务接入，链路断点；上下文传播格式不统一（W3C TraceContext vs 旧 B3）。
- Logs 在部分语言 SDK 未稳定，生产先用「现有日志框架 + Collector 采集」方式。
- Span 里带出手机号、Token 等敏感信息，需在 Collector 统一脱敏（个人信息保护合规）。

## 迁移
- SkyWalking / Zipkin / Jaeger 客户端 → OTel：先在 Collector 开对应接收器兼容旧数据，再逐服务替换 SDK。
- 厂商 Agent → OTel：后端不变，先改为 OTLP 上报到厂商的 OTel 接入点。

## 最佳做法
- 平台提供统一的 OTel 配置模板与 Collector，业务方只填服务名，避免各自为政。

## CHANGELOG
- 2026-11-14 v1.0.0 首版；情报员自动核实（来源见 sources）
