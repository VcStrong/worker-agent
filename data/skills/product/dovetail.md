---
id: dovetail
name: Dovetail（用户研究库与 AI 归纳）
aliases: [用户研究库, research repository, 访谈归纳, 问卷星]
roles: [product-manager, ux-designer]
maturity: 评估
maturity_by_region: {cn: 评估, global: 采用}
as_of: 2026-11-14
version: 1.0.0
sources:
  - https://dovetail.com/
  - https://www.wjx.cn/
region: global
replaces: []
replaced_by: []
from_graph: true
---

# Dovetail（用户研究库与 AI 归纳）

## 什么时候用
- 用户访谈、可用性测试、客服反馈、应用商店评论需要集中存放、打标签、归纳成洞察时（图谱 P-03 用户研究员原有工具）。
- 需求立项前要回答「这个问题有多少用户提过、影响多大」。
- 问卷本身（定量）国内用问卷星，海外用 Qualtrics；Dovetail 负责定性资料的归纳。

## 关键做法
- 访谈录音 / 视频上传后自动转写（时间戳、说话人分离、翻译），按研究项目（Projects）自动分析出结构化洞察。
- Channels 把大量原始反馈自动分类成需求点与新问题，并按客户和业务影响排序，可当「需求证据库」。
- Chat 跨全部资料提问，答案带引用；写 PRD 的「用户问题」节时直接引用原话片段。
- Agents 可把洞察通过 MCP 推到 Jira / Linear 等工具；先人工复核再推送。
- 标签体系先定好（问题域、用户分群、严重度），否则 AI 分类结果难以比较。

## 常见坑
- AI 归纳会「平均化」少数但关键的声音，重要结论要回看原始片段。
- 访谈资料含人脸、声音、姓名，属个人信息；要开自动脱敏（官方支持姓名、人脸、声音打码）和保留期限。
- 境外 SaaS：中国境内用户的访谈资料上传属于个人信息出境，需按《个人信息保护法》做告知同意和出境评估 / 标准合同。

## 迁移
- 从「录音转写 + 在线文档手工贴便签」迁移：先把近 6 个月访谈导入，统一打标签，再停用零散文档。
- 国内团队（region=cn）：定性资料优先用国内部署的工具或内部知识库，Dovetail 只在海外项目或已完成出境合规后使用。

## 最佳做法
- 判断理由：Dovetail 官网显示持续迭代（Agents、Channels 2.0、Digital Twins 等），并声明 SOC 2 Type II、ISO 27001 / 42001、可选美欧澳数据驻留，海外定「采用」；国内因出境合规定「评估」。
- 每份洞察写清：证据条数、来源分群、置信度。

## CHANGELOG
- 2026-11-14 v1.0.0 首版；情报员自动核实（来源见 sources）
