---
id: gitops-argocd
name: GitOps（Argo CD）
aliases: [GitOps, Argo CD, ArgoCD, ApplicationSet, 发布系统]
roles: [sre-security, architect, backend-engineer]
maturity: 采用
as_of: 2026-11-14
version: 1.0.0
sources:
  - https://argo-cd.readthedocs.io/en/stable/
  - https://github.com/argoproj/argo-cd/releases/tag/v3.6.0
  - https://argo-cd.readthedocs.io/en/stable/operator-manual/upgrading/overview/
region: both
replaces: []
replaced_by: []
from_graph: false
---

# GitOps（Argo CD）

当前版本：Argo CD v3.6.1（2026-11-04；3.6.0 于 2026-11-03 发布，3.5.x 仍在打补丁）。3.6 新增大量内置健康检查、ApplicationSet OCI 生成器、OpenTelemetry Span、回滚独立 RBAC 权限，默认改用服务端应用（server-side apply）。CNCF 毕业项目。图谱 SRE 工具原有「发布系统」「GitLab CI」，本技能补充 K8s 部署侧的 GitOps 做法。
判断理由：K8s 声明式部署的主流方案，发布节奏稳定、升级文档完善，判「采用」。

## 什么时候用
- 应用部署在 K8s，需要「Git 即期望状态」、可审计、可一键回滚。
- 多集群 / 多环境（开发、测试、预发、生产、海外区）统一发布。
- 平台团队想让业务方自助发布但守住权限边界。

## 关键做法
- 分仓：应用代码仓（CI 构建镜像）与部署配置仓（Helm / Kustomize 清单）分开，CI 只改配置仓镜像标签。
- 用 ApplicationSet 按集群 / 环境批量生成 Application；AppProject 限定可部署的命名空间和仓库。
- 生产开启自动同步需谨慎：建议自动同步 + 手动审批 PR 合并；开启 self-heal 防止手工改动漂移。
- 敏感配置不进 Git 明文：用 External Secrets Operator / Sealed Secrets 对接云 KMS 或 Vault。
- 渐进式发布配合 Argo Rollouts（金丝雀 / 蓝绿 + 指标分析）。

## 常见坑
- 跨小版本升级不看升级指南：3.6 有字段改名（`SyncWindow` → `InlineSyncWindow`）、签名校验参数废弃（`--signature-keys` → source integrity）。
- 默认改服务端应用后，与其它控制器争抢字段所有权，出现持续 OutOfSync；用 ignoreDifferences 或调整 managedFields。
- 单个 Argo CD 管理过多集群 / 应用，控制器内存吃紧；按分片（sharding）部署。
- Argo CD 管理员账号长期启用、未接 SSO，权限过大。

## 迁移
- 从 CI 脚本里 `kubectl apply` / `helm upgrade` → GitOps：先把现有清单导入配置仓，Argo CD 以手动同步模式接管，对比无差异后开自动同步。
- 版本升级逐个小版本进行（3.4 → 3.5 → 3.6），每步读官方 upgrading 文档。

## 最佳做法
- 发布记录即 Git 历史：回滚优先 `git revert` 配置仓，而不是在 UI 里点回滚，保持 Git 与集群一致。

## CHANGELOG
- 2026-11-14 v1.0.0 首版；情报员自动核实（来源见 sources）
