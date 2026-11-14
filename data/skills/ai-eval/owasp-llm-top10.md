---
id: owasp-llm-top10
name: OWASP Top 10 for LLM Applications
aliases: [OWASP LLM Top 10, 提示词注入, Prompt Injection, LLM 安全, 越狱, 红队测试]
roles: [ai-eval-compliance, ai-app-engineer]
maturity: 采用
as_of: 2026-11-14
version: 1.0.0
sources:
  - https://genai.owasp.org/llm-top-10/
region: both
replaces: []
replaced_by: []
from_graph: false
---

# OWASP Top 10 for LLM Applications

## 成熟度判断
- 采用：OWASP GenAI Security Project 官方当前版本为 2025 版，是业界通用的大模型应用风险清单，适合作为安全评审和红队测试的检查框架。官方另有 Agentic Security 专项，Agent 场景需同时关注。

## 什么时候用
- AI 功能技术方案评审、上线前安全评估、红队测试用例设计。
- RAG、Agent、插件 / MCP 工具接入时的威胁建模。

## 关键做法
- 以下按 2025 版十项逐条给出对策：
- LLM01 提示词注入：外部内容与指令隔离、标注不可信来源，高风险动作需人工确认，输入输出双向检测。
- LLM02 敏感信息泄露：训练与上下文数据脱敏，输出过滤，按用户权限检索。
- LLM03 供应链：模型、数据集、插件、MCP Server 来源审查与签名校验。
- LLM04 数据与模型投毒：训练 / 微调 / 知识库数据来源可追溯，入库审核。
- LLM05 输出处理不当：模型输出当不可信输入，渲染前转义，执行前校验（防 XSS、SQL 注入、命令注入）。
- LLM06 过度授权：工具最小权限、只读优先、关键操作人工审批。
- LLM07 系统提示词泄露：提示词里不放密钥和权限逻辑，权限在服务端校验。
- LLM08 向量与 Embedding 弱点：向量库按租户 / 权限隔离和过滤。
- LLM09 错误信息：引用来源、事实核查、提示不确定性。
- LLM10 无界消耗：Token 限流、单用户配额、超时与最大轮数。

## 常见坑
- 只靠系统提示词「请不要……」防注入，没有服务端权限控制。
- Agent 读取网页 / 邮件 / 文档内容后直接执行其中指令（间接注入）。
- 安全测试只在上线前做一次，模型或提示词变更后不复测。

## 迁移
- 传统 Web 安全评审清单基础上增加本十项，作为 AI 功能必查项。

## 最佳做法
- 红队样本纳入评测集（见 llm-eval-pipeline），每次变更自动回归；国内同时满足内容安全要求（见 genai-service-filing）。

## CHANGELOG
- 2026-11-14 v1.0.0 首版；情报员自动核实（来源见 sources）
