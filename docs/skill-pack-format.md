# 技能包格式（data/skills/<领域>/<技能id>.md）

技能包是「用什么技术、怎么做」的独立单元，和角色（来自图谱 + merge_map）分开维护。
一个技能只有一份文件，可以挂多个专家（`roles` 多对多）。
build.py 会把它挂进对应 agent 的「技能清单」，并为每个技能生成 `skills/<id>/SKILL.md`（按需加载）。

## 目录（领域）

`product` `design` `frontend` `client` `backend` `architecture` `sre-security` `qa` `data-growth` `ai-product` `ai-app` `ai-model` `ai-infra` `ai-eval`

AI 领域 = `ai-product` `ai-app` `ai-model` `ai-infra` `ai-eval`（过期阈值用 stale_days_ai=90）。

## frontmatter（YAML 子集：key: value、[a, b] 行内列表、- 列表；不要用多行字符串）

```yaml
---
id: jetpack-compose              # 小写字母、数字、连字符，全局唯一，= 文件名
name: Jetpack Compose            # 显示名
aliases: [Compose, Android Compose]   # 可选：who 反查用的别名
roles: [client-engineer]         # 适用专家 slug，至少 1 个（见下表）
maturity: 采用                    # 采用 / 试用 / 评估 / 暂缓
maturity_by_region: {cn: 采用, global: 试用}   # 可选：国内外两套方案时按 region 取默认
as_of: 2026-11-14                # 核实日期 YYYY-MM-DD
version: 1.0.0
sources:                         # 至少 1 个官方 / 一手来源链接
  - https://developer.android.com/compose
region: both                     # cn / global / both
replaces: [android-xml-layout]   # 可选：本技能取代的技能 id
replaced_by: []                  # 暂缓项必填：替代技能 id（或在正文「替代」节写清）
from_graph: false                # 图谱 tl 里原有的工具 = true（如 RxJava、Webpack）；首版新增 = false
---
```

## 正文（必填节，中文）

```markdown
# Jetpack Compose

## 什么时候用
## 关键做法
## 常见坑
## 迁移
（从旧方案怎么迁；暂缓项写「原因 / 替代 / 迁移建议」，并写一节「## 替代」）
## 最佳做法
（经验回流写在这里，首版可写 1~3 条）
## CHANGELOG
- 2026-11-14 v1.0.0 首版；情报员自动核实（来源见 sources）
```

暂缓项（maturity: 暂缓）必须有 `## 替代` 节，写原因、替代项、迁移建议；存量项目照旧维护。

## 专家 slug

| slug | 专家 |
|---|---|
| product-manager | 产品经理 |
| ux-designer | 体验设计师 |
| architect | 架构师 / 技术负责人 |
| frontend-engineer | 前端工程师 |
| client-engineer | 客户端工程师（Android / iOS / 鸿蒙 / 小程序 / 跨端） |
| backend-engineer | 后端工程师（含 DBA、数据开发） |
| qa-expert | 测试专家 |
| sre-security | SRE 与安全工程师 |
| data-growth | 数据与增长运营（数据分析、产品/用户/内容/活动运营、增长投放、客服） |
| ai-product-manager | AI 产品经理（含 AI 体验设计、AI 解决方案架构） |
| ai-app-engineer | AI 应用 / Agent 工程师（大模型应用、RAG、Agent、AI 研发效能） |
| model-algorithm-engineer | 模型与算法工程师（算法、搜索推荐、训练微调、语音多模态、数据训练师） |
| ai-infra-mlops | AI Infra / MLOps 工程师（推理优化、MLOps） |
| ai-eval-compliance | AI 评测与安全合规专家（评测、AI 安全合规、法务合规） |

## 成熟度含义

- 采用：默认推荐
- 试用：新项目或用户同意时可用，要写明风险和回退方案
- 评估：只在调研、技术方案对比里提，不进生产代码
- 暂缓：不推荐新用，存量项目照旧维护并提示迁移路径
