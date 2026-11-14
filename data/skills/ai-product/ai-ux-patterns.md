---
id: ai-ux-patterns
name: AI 体验设计模式（流式、可解释、人工兜底）
aliases: [AI 体验设计, AI UX, 流式输出, 可解释性, 人工兜底, Human-in-the-loop, People + AI Guidebook]
roles: [ai-product-manager, ai-app-engineer]
maturity: 采用
as_of: 2026-11-14
version: 1.0.0
sources:
  - https://pair.withgoogle.com/guidebook-v2/
  - https://www.anthropic.com/engineering/building-effective-agents
  - https://docs.langchain.com/oss/python/langgraph/overview
region: both
replaces: []
replaced_by: []
from_graph: false
---

# AI 体验设计模式

## 成熟度判断
- 采用：Google PAIR《People + AI Guidebook》按 8 个问题整理设计模式（可解释、信任校准、反馈与控制、错误与优雅失败等），各大模型厂商和框架（流式输出、人工中断）都已原生支持。

## 什么时候用
- 任何面向用户的 AI 功能（对话、生成、推荐、Agent）出交互方案时。
- 用户对 AI 结果不信任、投诉「乱说」「不知道它在干嘛」时。

## 关键做法
- 流式：长回答一律流式输出，先给结构或要点；首字时延写进验收标准；Agent 任务展示步骤进度。
- 可解释：给出依据（引用来源、检索片段、使用了哪些数据），标注「AI 生成」；不确定时直说不确定。
- 信任校准：开场说明 AI 能做什么不能做什么；高风险领域（医疗、金融、法律）加提示并引导人工。
- 反馈与控制：点赞点踩 + 原因、重新生成、编辑后采纳；Agent 关键动作前确认，可中途打断。
- 人工兜底：设置转人工入口和自动转人工条件（连续点踩、低置信、敏感话题、用户明确要求），转接时把上下文带给人工。
- 优雅失败：超时、拒答、限流有可理解的文案和下一步建议，不出现原始报错。

## 常见坑
- 等全部生成完才显示，用户以为卡死。
- 只显示结论不给依据，出错时用户无法判断。
- 转人工入口藏太深，或转过去人工看不到对话历史。
- AI 生成内容没有显式标识，国内违反《人工智能生成合成内容标识办法》（见 ai-content-labeling）。

## 迁移
- 从「一次性返回」改流式：后端改 SSE / WebSocket，前端做增量渲染和中断按钮。
- 从「全自动」改「人机协同」：先在高风险动作加确认，再按数据放开自动化比例。

## 最佳做法
- 每个 AI 功能的交互稿必须包含：加载态、流式态、失败态、拒答态、转人工态五种状态。

## CHANGELOG
- 2026-11-14 v1.0.0 首版；情报员自动核实（来源见 sources）
