---
name: ingress-nginx-controller
description: "Ingress NGINX 控制器（已退役，暂缓）（成熟度 暂缓，as_of 2026-11-14）：不用于新集群、新入口。 适用角色：SRE 与安全工程师、架构师 / 技术负责人。"
---
<!-- generated-by: scripts/build.py；源文件 data/skills/sre-security/ingress-nginx-controller.md，请勿手改 -->

> 成熟度：**暂缓**（region=cn）｜版本 1.0.0｜as_of 2026-11-14｜来源：https://kubernetes.io/blog/2025/11/11/ingress-nginx-retirement/ https://github.com/kubernetes/ingress-nginx https://github.com/kubernetes-sigs/ingress2gateway

# Ingress NGINX 控制器（已退役，暂缓）

当前状态：Kubernetes SIG Network 与安全响应委员会于 2025-11 宣布退役社区 Ingress NGINX 控制器，尽力维护到 2026-03；最后一批版本为 2026-03-19 发布的 helm-chart 4.15.1 / 4.14.5 / 4.13.9，仓库已于 2026-03-24 归档只读。此后不再有任何版本、修复和安全补丁。图谱基础架构工具原有「Nginx / Istio」。
判断理由：官方已退役且不再修安全漏洞，新部署判「暂缓」。注意：退役的只是 Kubernetes 社区的 ingress-nginx 控制器，NGINX 本身（作为反向代理 / Web 服务器）和 Istio 不在此列。

## 什么时候用
- 不用于新集群、新入口。
- 只在存量集群里继续运行，直到迁移完成。

## 关键做法
- 存量集群：固定在最后版本，收紧暴露面（不启用 snippet 注解、限制 admission webhook 访问），在其前面加 WAF。
- 盘点所有 Ingress 资源和使用的注解，作为迁移清单。
- 关注安全通告，一旦出现无补丁的高危漏洞，按应急优先级迁移。

## 常见坑
- 以为「现有部署不坏」就可以无限期使用：新漏洞没有补丁，合规扫描会持续报告。
- 混淆 ingress-nginx（社区）与 NGINX 公司的 NGINX Ingress Controller / NGINX Gateway Fabric，二者是不同项目。
- 大量依赖 `configuration-snippet` 等自定义片段，迁移时没有一一对应的标准能力。

## 迁移
- 见下方「替代」节。

## 替代
- 原因：上游官方退役，2026-03 后无安全补丁；仓库已归档。
- 替代项：`kubernetes-gateway-api`（Gateway API + 任一合规实现，如 Envoy Gateway、Istio、Cilium、NGINX Gateway Fabric、云厂商托管网关）。
- 迁移建议：用 ingress2gateway 转换 Ingress 资源 → 人工核对注解对应的过滤器 / 策略 → 新网关独立 LB 并行运行 → DNS 按权重切流 → 观察错误率、延迟后下线旧控制器。迁移单独立项，不与业务需求混做。
- 存量项目照旧维护，不擅自迁移，只在技术方案里提迁移建议并标出安全风险。

## 最佳做法
- 迁移前先读 Kubernetes 官方博客对 ingress-nginx 隐含行为（如路径匹配、重写）的说明，避免切换后路由行为变化。

## CHANGELOG
- 2026-11-14 v1.0.0 首版；情报员自动核实（来源见 sources）
