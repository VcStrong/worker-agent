---
id: ai-image-generation
name: AI 辅助出图（Figma AI / 即梦 / Midjourney）
aliases: [AI 出图, 文生图, Figma AI, 即梦, Midjourney, AIGC 素材]
roles: [ux-designer, data-growth]
maturity: 试用
maturity_by_region: {cn: 试用, global: 试用}
as_of: 2026-11-14
version: 1.0.0
sources:
  - https://help.figma.com/hc/en-us/sections/31803050978967-About-Figma-AI
  - https://jimeng.jianying.com/
  - https://docs.midjourney.com/
  - https://www.cac.gov.cn/2025-03/14/c_1743654685899683.htm
region: both
replaces: []
replaced_by: []
from_graph: true
---

# AI 辅助出图（Figma AI / 即梦 / Midjourney）

当前版本：均为 SaaS 持续发布。Figma AI 于 2025-07-24 结束 beta（含生成 / 编辑图片），按 AI credits 计费；即梦为字节跳动官方 AI 图片 / 视频创作平台；Midjourney 当前默认模型以官方文档为准（官方文档页本次抓取被拒，版本号未能一手确认）。
判断理由：出图质量已可用于概念稿、运营素材，但版权、标识合规和风格一致性需要人工把关，定「试用」。图谱 G-05 原有 Midjourney / Stable Diffusion / 即梦。

## 什么时候用
- 概念探索、情绪板、插画草稿、运营活动 banner、商品场景图、占位图。
- 设计稿里快速补图、去背景、扩图（Figma 内直接操作）。
- 不用于：品牌 Logo / IP 形象定稿、需要明确版权归属的核心资产。

## 关键做法
- 选型：region=cn 默认即梦（国内可用、中文提示词友好）；海外或设计稿内操作用 Figma AI；风格化插画可选 Midjourney。
- 提示词模板化：主体 + 场景 + 风格 + 构图 + 色调 + 比例；固定风格参考图，保证系列素材一致。
- 生成后必须人工修整：文字、手部、品牌元素、敏感内容。
- 素材登记：工具、模型版本、提示词、生成日期、商用授权条款，存入素材库。

## 常见坑
- 生成图中的文字、Logo、人物肖像可能侵权或失真。
- 各平台商用条款不同（付费档位、是否允许商用），上线前查当期服务条款。
- 同一提示词多次生成结果不同，系列素材要锁定种子 / 参考图。

## 迁移
- 从「图库购买 + 手工修图」迁移：先在运营素材、占位图上试点，核心品牌资产仍走设计师原创。

## 最佳做法
- 合规（国内）：按《人工智能生成合成内容标识办法》（2025-09-01 施行），对外发布的 AI 生成图片需按要求加显式标识，保留平台写入的隐式标识（元数据），不要擦除。
- 风险与回退：素材被投诉或存疑时立即下线，替换为图库或原创素材。

## CHANGELOG
- 2026-11-14 v1.0.0 首版；情报员自动核实（来源见 sources）
