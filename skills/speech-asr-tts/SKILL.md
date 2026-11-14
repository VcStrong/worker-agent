---
name: speech-asr-tts
description: "语音识别与合成（ASR / TTS）（成熟度 采用，as_of 2026-11-14）：语音输入、会议转写、客服质检、字幕生成（ASR）。 适用角色：模型与算法工程师、AI 应用 / Agent 工程师。"
---
<!-- generated-by: scripts/build.py；源文件 data/skills/ai-model/speech-asr-tts.md，请勿手改 -->

> 成熟度：**采用**（region=cn）｜版本 1.0.0｜as_of 2026-11-14｜来源：https://github.com/modelscope/FunASR https://github.com/FunAudioLLM/CosyVoice https://github.com/openai/whisper https://help.aliyun.com/zh/model-studio/models

# 语音识别与合成（ASR / TTS）

## 成熟度判断
- 采用：图谱原有工具（Whisper / FunASR / CosyVoice）均在维护。FunASR 最新 v1.4.26（2026-11），含 Paraformer、SenseVoice、LLM 型 Fun-ASR-Nano，提供 OpenAI 兼容转写服务；CosyVoice 最新为 Fun-CosyVoice 3.0（2025-12，Apache-2.0，流式时延约 150ms，支持 9 种语言与 18+ 方言）；云端阿里云百炼提供 qwen-audio ASR / TTS / 实时语音系列。
- Whisper 仍可用但中文与流式场景国内首选 FunASR / 云 API。

## 什么时候用
- 语音输入、会议转写、客服质检、字幕生成（ASR）。
- 语音播报、有声内容、语音助手、数字人配音（TTS）。

## 关键做法
- 先用云 API 验证，量大或需私有化再自部署 FunASR / CosyVoice。
- ASR 链路：VAD 切分 → 识别 → 标点 → 说话人分离 → 热词 / 领域词表；流式用 Paraformer 流式或云实时接口。
- TTS 用流式合成降低首包时延；长文本按句切分并行合成。
- 实时语音对话：级联（ASR → LLM → TTS）稳定可控，端到端全模态见 multimodal-models（试用）。
- 评测：ASR 看字错率（CER）分场景（噪声、方言、专有名词）；TTS 看 MOS 抽样与发音错误率。

## 常见坑
- 声音复刻未取得本人书面授权，侵犯声音权益与个人信息。
- 合成语音未加标识（《人工智能生成合成内容标识办法》要求音频加语音或节奏提示等显式标识，见 ai-content-labeling）。
- FunASR 服务默认建议只监听本机，直接暴露公网有安全风险。
- 训练录音含个人信息，未做脱敏和存储期限管理。

## 迁移
- 老 Kaldi / 传统 ASR → FunASR：同测试集对比 CER，热词表迁移后切流。

## 最佳做法
- 每个业务场景维护一份带标注的音频测试集，模型升级必回归。

## CHANGELOG
- 2026-11-14 v1.0.0 首版；情报员自动核实（来源见 sources）
