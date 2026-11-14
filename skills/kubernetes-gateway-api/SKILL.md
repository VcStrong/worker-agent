---
name: kubernetes-gateway-api
description: "Kubernetes Gateway API（成熟度 采用，as_of 2026-11-14）：新建 K8s 集群的南北向入口（替代 Ingress）。 适用角色：架构师 / 技术负责人、SRE 与安全工程师、后端工程师。"
---
<!-- generated-by: scripts/build.py；源文件 data/skills/architecture/kubernetes-gateway-api.md，请勿手改 -->

> 成熟度：**采用**（region=cn）｜版本 1.0.0｜as_of 2026-11-14｜来源：https://gateway-api.sigs.k8s.io/ https://github.com/kubernetes-sigs/gateway-api/releases/tag/v1.7.0 https://kubernetes.io/blog/2026/04/21/gateway-api-v1-5/ https://github.com/kubernetes-sigs/ingress2gateway

# Kubernetes Gateway API

当前版本：Gateway API v1.7.0（2026-10-29）。v1.5（2026-02）把 ListenerSet、TLSRoute、ReferenceGrant 等升入 Standard 通道；v1.7 把 HTTPRoute 重试、BackendTLSPolicy 的 SAN / TLS 选项升入 Standard，新增 TelemetryPolicy、前置路由过滤器等实验特性。项目已改为发布列车模式。
判断理由：Kubernetes 官方的下一代流量入口 API，Gateway / HTTPRoute / GRPCRoute 已 GA，主流实现（Envoy Gateway、Istio、Cilium、NGINX Gateway Fabric、Kong、云厂商网关）均支持；社区 Ingress NGINX 控制器已于 2026-03 退役并官方推荐迁到 Gateway API，判「采用」。

## 什么时候用
- 新建 K8s 集群的南北向入口（替代 Ingress）。
- 需要按 Header / 权重灰度、跨命名空间路由委托、gRPC 路由、后端 TLS 时。
- 平台团队管 Gateway、业务团队自管 Route 的多租户分工场景。

## 关键做法
- 角色分离：平台团队维护 GatewayClass / Gateway（监听、证书），业务团队在自己的命名空间写 HTTPRoute。
- 只装 Standard 通道 CRD 上生产；Experimental 字段只在测试集群验证。
- 选实现：所在云的托管网关若已支持 Gateway API（以云厂商文档为准）优先用托管，自建用 Envoy Gateway 或 Istio；用官方 conformance 报告核对支持的特性。
- 证书交给 cert-manager，跨命名空间引用用 ReferenceGrant 显式授权。
- 灰度：HTTPRoute `backendRefs` 权重 + Argo Rollouts / Flagger。

## 常见坑
- Standard 与 Experimental CRD 混装：升级 v1.5+ 后旧的实验版 TLSRoute 不可用，v1.7 实验通道还有字段改名。
- 不同实现对可选特性（重试、超时、会话保持）支持不一，迁移前跑 conformance 对比。
- 照搬 ingress-nginx 注解（rewrite、snippet）：Gateway API 没有任意配置片段，需改用标准过滤器或实现方扩展策略。

## 迁移
- 用 ingress2gateway 把现有 Ingress 资源转换为 Gateway / HTTPRoute，人工复核注解对应关系。
- 新旧入口并行：新网关拿独立 LB，DNS 按权重切流，观察错误率与延迟后下线旧 Ingress。

## 最佳做法
- 每个环境只留一个 GatewayClass 默认实现，避免业务方随意选择导致行为不一致。

## CHANGELOG
- 2026-11-14 v1.0.0 首版；情报员自动核实（来源见 sources）
