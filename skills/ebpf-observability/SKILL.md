---
name: ebpf-observability
description: "eBPF 可观测与运行时安全（OBI / Cilium Hubble / Tetragon）（成熟度 试用，as_of 2026-11-14）：存量服务多、语言杂、短期无法逐个接 OTel SDK，需要先拿到 RED 指标与基础链路。 适用角色：SRE 与安全工程师、架构师 / 技术负责人。"
---
<!-- generated-by: scripts/build.py；源文件 data/skills/sre-security/ebpf-observability.md，请勿手改 -->

> 成熟度：**试用**（region=cn）｜版本 1.0.0｜as_of 2026-11-14｜来源：https://opentelemetry.io/docs/zero-code/obi/ https://opentelemetry.io/blog/2026/obi-v1-release/ https://cilium.io/ https://tetragon.io/ https://github.com/cilium/tetragon/releases

# eBPF 可观测与运行时安全（OBI / Cilium Hubble / Tetragon）

当前版本：OpenTelemetry eBPF Instrumentation（OBI）v1.0.0（2026-10-30，前身为 Grafana Beyla 捐赠）；Cilium 1.20.x（1.21 预发布中，网络可观测组件 Hubble）；Tetragon v1.8.0（2026-10-30，运行时安全）。
判断理由：Cilium / Tetragon 已广泛生产使用，但 OBI 刚到 1.0，且 eBPF 方案依赖内核版本与特权部署，各家云 / 自建节点情况不一，整体判「试用」。风险：内核不兼容、特权容器带来的安全面；回退方案：卸载 DaemonSet 即可，业务无改动，继续用 SDK 插桩与 Prometheus 指标。

## 什么时候用
- 存量服务多、语言杂、短期无法逐个接 OTel SDK，需要先拿到 RED 指标与基础链路。
- 排查网络问题：服务间连通、DNS、丢包、L7 请求可视化（Hubble）。
- 运行时安全：检测容器内异常进程执行、敏感文件访问、提权（Tetragon），并可在内核侧阻断。

## 关键做法
- 先确认节点内核版本和 BTF 支持（主流发行版较新内核默认具备），在一个节点池灰度。
- OBI 以 DaemonSet 部署，输出 OTLP 到现有 Collector，与 SDK 插桩的数据用同一套 service.name 规范。
- 有 SDK 插桩的服务以 SDK 数据为准，OBI 只做兜底，避免重复 Span。
- Tetragon 策略（TracingPolicy）从「只告警」开始，观察误报后再开阻断。
- 部署组件所需的特权、hostPID 等权限单独审批，镜像固定版本并做签名校验。

## 常见坑
- 托管 K8s 的节点 OS 内核较旧或禁止特权容器，eBPF 组件起不来。
- 采集全部 L7 流量导致数据量与费用暴涨；按命名空间 / 端口过滤。
- TLS 加密流量的 L7 解析依赖对 SSL 库的 uprobe，静态编译或非常规 TLS 库无法解析。
- 把 eBPF 当作 APM 全部替代：业务语义（订单号、用户操作）仍需代码埋点。

## 迁移
- 从各语言私有 Agent → OBI 兜底 + 重点服务 OTel SDK；先并行一周对比指标一致性。
- 已用 Beyla 的：按官方说明切换到 OBI，配置项基本兼容，逐节点池替换。

## 最佳做法
- 先用 Hubble / OBI 画出真实服务依赖拓扑，再对照架构图修正，常能发现「影子调用」。

## CHANGELOG
- 2026-11-14 v1.0.0 首版；情报员自动核实（来源见 sources）
