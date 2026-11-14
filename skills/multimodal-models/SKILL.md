---
name: multimodal-models
description: "多模态大模型（视觉理解 / 全模态）（成熟度 采用，as_of 2026-11-14）：票据 / 截图 / 表单 / 商品图理解与抽取、内容审核辅助、UI 截图分析。 适用角色：模型与算法工程师、AI 应用 / Agent 工程师。"
---
<!-- generated-by: scripts/build.py；源文件 data/skills/ai-model/multimodal-models.md，请勿手改 -->

> 成熟度：**采用**（region=cn）｜版本 1.0.0｜as_of 2026-11-14｜来源：https://help.aliyun.com/zh/model-studio/models https://github.com/QwenLM/Qwen3-Omni https://platform.claude.com/docs/en/about-claude/models/overview https://api-docs.deepseek.com/quick_start/pricing

# 多模态大模型（视觉理解 / 全模态）

## 成熟度判断
- 图文理解 采用：Claude 当前全系支持图像输入；阿里云百炼的 qwen4-max-preview、qwen3.7-plus 支持视觉理解；DeepSeek Flash 支持视觉。
- 全模态实时（音视频对话）按试用对待：百炼提供 qwen3.8-omni-flash / -realtime，开源有 Qwen3-Omni，效果与成本仍在快速变化，需写回退方案（降级为 ASR + 文本模型 + TTS 级联）。

## 什么时候用
- 票据 / 截图 / 表单 / 商品图理解与抽取、内容审核辅助、UI 截图分析。
- 视频摘要、实时语音视频助手（试用）。

## 关键做法
- 先用通用多模态 API 验证效果，达不到再考虑专用 OCR 或微调开源 VLM。
- 图片预处理：控制分辨率（按官方建议的长边上限），裁掉无关区域，降低 Token 成本。
- 结构化抽取配合结构化输出（见 structured-outputs），并对关键字段做规则校验。
- 视频按关键帧抽样 + 字幕 / ASR 文本，比整段送入更省。
- 评测集按图片类型分层（清晰 / 模糊 / 手写 / 多语言）。

## 常见坑
- 图片 Token 计费远高于文本，未估算导致成本失控（见 llm-cost-estimation）。
- 小字、表格、手写体识别不稳，关键数字必须校验。
- 图片中嵌入文字形式的提示词注入（OWASP LLM01）。
- 人脸、证件等敏感个人信息处理需单独授权与合规评估（见 pipl-compliance-audit）。

## 迁移
- 传统 OCR + 规则 → 多模态模型：先并行对比字段准确率，再按字段逐步切换，保留 OCR 作兜底。

## 最佳做法
- 生成的图片 / 音视频按要求加显式与隐式标识（见 ai-content-labeling）。

## CHANGELOG
- 2026-11-14 v1.0.0 首版；情报员自动核实（来源见 sources）
