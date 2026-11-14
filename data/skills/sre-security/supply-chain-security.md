---
id: supply-chain-security
name: 软件供应链安全（SBOM / SLSA / Sigstore 签名）
aliases: [供应链安全, SBOM, SLSA, Sigstore, cosign, Syft, CycloneDX, SPDX, 依赖签名, 构建溯源]
roles: [sre-security, architect, backend-engineer]
maturity: 采用
as_of: 2026-11-14
version: 1.0.0
sources:
  - https://slsa.dev/spec/v1.2/
  - https://docs.sigstore.dev/
  - https://github.com/sigstore/cosign/releases
  - https://github.com/anchore/syft
  - https://cyclonedx.org/
  - https://spdx.dev/
  - https://www.cisa.gov/resources-tools/resources/2025-minimum-elements-software-bill-materials-sbom
region: both
replaces: []
replaced_by: []
from_graph: false
---

# 软件供应链安全（SBOM / SLSA / Sigstore 签名）

当前版本：SLSA 规范 v1.2（已批准，含 Build Track 与 Source Track）；Sigstore cosign v3.1.4（2026-10，v2.6.x 仍有补丁）；Syft v1.57.x（2026-11）；SBOM 格式 CycloneDX / SPDX；美国 CISA 2025 年发布 SBOM 最小要素更新稿（新增组件哈希、许可证、工具名、生成上下文）。图谱安全工具原有「SAST / DAST」「漏洞扫描器」，本技能补充供应链环节。
判断理由：标准与工具均由开源基金会 / 政府机构维护、持续发布；SBOM 生成 + 镜像签名验签成本低、收益明确，判「采用」；SLSA Build L3（隔离构建平台）对自建 CI 改造较大，按「试用」推进。

## 什么时候用
- 所有对外发布的容器镜像、二进制、SDK、App 安装包。
- 客户 / 监管要求提供 SBOM，或需要快速回答「某个漏洞组件（如 log4j 类）影响了哪些服务」。
- 防止被篡改镜像、投毒依赖进入生产。

## 关键做法
- 构建时生成 SBOM（Syft，输出 CycloneDX 或 SPDX），随制品一起存入镜像仓库（作为 OCI 附件）。
- 用 cosign 无密钥签名（OIDC + Fulcio 证书 + Rekor 透明日志）或企业 KMS 密钥签名；同时签 SBOM 与构建溯源（provenance）。
- 部署前验签：K8s 准入控制（Kyverno / Sigstore policy-controller）只允许已签名、来自可信构建流水线的镜像。
- 依赖治理：锁定版本 + 哈希校验（lockfile）、私有镜像源代理公网仓库、自动化依赖升级与漏洞扫描（Trivy / Grype 等基于 SBOM 扫描）。
- 按 SLSA Build 级别逐步提升：L1 有溯源 → L2 托管构建平台签名溯源 → L3 构建隔离、防篡改。

## 常见坑
- 只生成 SBOM 不入库不检索，出漏洞时依旧找不到影响面。
- 签名了但部署侧没验签，等于没做。
- 国内网络访问公共 Sigstore 服务（Fulcio / Rekor）不稳定：内网可自建 Sigstore 或用 KMS 密钥签名模式。
- cosign 跨大版本（v2 → v3）命令与默认行为有变化，CI 脚本固定版本并按发布说明升级。

## 迁移
- 先在 CI 加 SBOM 生成 + 签名（不阻断），观察一个迭代；再在预发环境开启准入验签，最后生产强制。

## 最佳做法
- 维护「SBOM 检索」能力：输入组件名 + 版本，秒级列出受影响的服务与镜像版本。

## CHANGELOG
- 2026-11-14 v1.0.0 首版；情报员自动核实（来源见 sources）
