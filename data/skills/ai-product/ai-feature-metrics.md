---
id: ai-feature-metrics
name: AI 功能指标与评测思路
aliases: [AI 指标, 成功标准, Success Criteria, AI 北极星指标]
roles: [ai-product-manager, ai-eval-compliance]
maturity: 采用
as_of: 2026-11-14
version: 1.0.0
sources:
  - https://platform.claude.com/docs/en/test-and-evaluate/develop-tests
  - https://developers.openai.com/api/docs/guides/evaluation-best-practices
region: both
replaces: []
replaced_by: []
from_graph: false
---

# AI 功能指标与评测思路

## 成熟度判断
- 采用：Anthropic、OpenAI 官方文档都把「先定可度量的成功标准、再建评测集」列为大模型应用的第一步，方法论稳定。
- 当前状态：OpenAI 官方指南明确反对「凭感觉（vibe-based）评测」；注意 OpenAI 托管 Evals 平台 2026-10-31 起只读、2026-11-30 关停，方法照用，工具要换。

## 什么时候用
- PRD「AI 机会评估」节需要回答「用不用 AI、做到什么程度算成功」时。
- AI 功能立项、模型或 Prompt 换代、供应商切换前，定上线门槛。
- 复盘 AI 功能效果，区分「模型问题」还是「产品问题」。

## 关键做法
- 指标分三层：业务指标（转化、留存、人工替代率）→ 体验指标（采纳率、重试率、点踩率、首字时延）→ 模型指标（准确率、幻觉率、拒答率、单次成本）。
- 成功标准按官方要求写成「具体、可度量、可达成、相关」，如「工单分类准确率 ≥ 92%，P95 首字 < 1.5s，单次成本 < 0.02 元」。
- 每条标准对应评测方法：精确匹配 / 代码校验 / LLM 评审（Likert 或二分类）/ 人工抽检，交给 AI 评测与安全合规专家落地。
- 评测集覆盖真实流量分布 + 边界（超长、歧义、无关、恶意输入），数量优先于精修。
- 上线后加线上指标：点赞点踩、人工接管率、投诉率，按周回看。

## 常见坑
- 只看离线准确率不看成本和时延，上线后账单失控。
- 用同一个模型既生成又当评审，分数虚高；官方建议评审模型与被测模型不同。
- 指标没有基线（人工水平或旧方案），无法判断 AI 是否值得做。
- 「好用」「智能」这类形容词当验收标准，测试无法执行。

## 迁移
- 旧做法：上线前几十条手工样例「看着行」→ 改为固定评测集 + 自动打分 + 门槛。
- 使用 OpenAI 托管 Evals 的团队：导出数据集与评分器，迁到自建脚本或其他评测平台（见 llm-eval-pipeline）。

## 最佳做法
- PRD 里每个 AI 功能必须写「成功标准 / 评测方法 / 兜底策略」三件套。
- 业务指标与模型指标分开报，避免模型分涨了业务没动还以为成功。

## CHANGELOG
- 2026-11-14 v1.0.0 首版；情报员自动核实（来源见 sources）
