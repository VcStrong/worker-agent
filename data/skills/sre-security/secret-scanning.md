---
id: secret-scanning
name: 密钥泄露扫描（Gitleaks / TruffleHog / 平台内置扫描）
aliases: [密钥扫描, Secret Scanning, gitleaks, betterleaks, trufflehog, push protection]
roles: [sre-security, backend-engineer]
maturity: 采用
as_of: 2026-11-14
version: 1.0.0
sources:
  - https://github.com/gitleaks/gitleaks
  - https://github.com/betterleaks/betterleaks
  - https://github.com/trufflesecurity/trufflehog
  - https://docs.github.com/en/code-security/secret-scanning/introduction/about-secret-scanning
region: both
replaces: []
replaced_by: []
from_graph: false
---

# 密钥泄露扫描（Gitleaks / TruffleHog / 平台内置扫描）

当前版本：Gitleaks v8.30.1（2026-03），README 声明已「功能完整」进入维护模式，只修安全问题，作者转向新项目 Betterleaks（2026-02 创建，MIT）；TruffleHog v3.99.x（2026-11，可在线验证密钥是否有效）；GitHub Secret Scanning 与推送保护。图谱安全工具原有「密钥管理」，本技能补充泄露检测环节。
判断理由：密钥泄露是最常见的高危事件，扫描工具成熟、接入成本低，判「采用」。工具选择：Gitleaks 仍可稳定使用；Betterleaks 尚新，按「评估」对待，可在非阻断流水线试跑对比。

## 什么时候用
- 所有代码仓库：提交前（pre-commit）、CI（合并请求）、定期全历史扫描。
- 开源 / 外包交付代码前、仓库从私有转公开前做全量历史扫描。
- 应急响应：怀疑泄露时快速确认范围。

## 关键做法
- 三层防线：开发机 pre-commit hook（`gitleaks git --pre-commit --staged`，或官方 pre-commit 钩子配置）→ CI 阻断合并 → 代码平台推送保护（GitHub / GitLab 内置 Secret Detection）。
- Gitleaks v8.19 起 `detect` / `protect` 已废弃，改用 `git`、`dir`、`stdin` 子命令；CI 脚本按新命令写。
- 自定义规则覆盖公司内部密钥格式（内部网关 Token、国内云 AccessKey 前缀等），并维护 allowlist 消除测试数据误报。
- 定期用 TruffleHog 带验证模式扫描历史，优先处理「仍然有效」的密钥。
- 从根上减少明文密钥：接入 KMS / Vault / 云密钥管理服务，应用运行时注入。

## 常见坑
- 只删提交里的密钥而不轮换：Git 历史、Fork、CI 日志里仍可拿到，泄露后第一步永远是吊销并轮换。
- allowlist 过宽（整目录忽略），真实密钥被漏报。
- 扫描结果只发邮件无人处理；需进工单系统，按有效性和权限分级限时处理。
- 镜像层、前端打包产物、移动端安装包里的密钥未被扫描。

## 迁移
- 从人工抽查 → 三层自动化；先在 CI 以告警模式运行两周清理存量，再改为阻断。
- 若后续 Gitleaks 停止安全修复，按同类规则迁到 Betterleaks 或 TruffleHog，规则文件单独维护便于迁移。

## 最佳做法
- 每次泄露事件复盘时补一条自定义检测规则，避免同类密钥再次漏检。

## CHANGELOG
- 2026-11-14 v1.0.0 首版；情报员自动核实（来源见 sources）
