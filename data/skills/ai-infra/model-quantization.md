---
id: model-quantization
name: 模型量化部署
aliases: [量化, FP8, INT8, INT4, AWQ, GPTQ, NVFP4, W4A16, llm-compressor, compressed-tensors]
roles: [ai-infra-mlops, model-algorithm-engineer]
maturity: 采用
as_of: 2026-11-14
version: 1.0.0
sources:
  - https://github.com/vllm-project/llm-compressor
  - https://github.com/vllm-project/llm-compressor/releases
  - https://docs.vllm.ai/en/stable/
region: both
replaces: []
replaced_by: []
from_graph: false
---

# 模型量化部署

## 成熟度判断
- 采用：vLLM 官方支持 FP8、MXFP8/MXFP4、NVFP4、INT8、INT4、GPTQ/AWQ、GGUF、compressed-tensors 等；vLLM 项目的 llm-compressor（最新 0.15.0，2026-10-29）支持 GPTQ、AWQ、SmoothQuant、AutoRound、SpinQuant 等算法，输出 compressed-tensors 格式可被 vLLM 直接加载。

## 什么时候用
- 自部署模型显存不够、想用更少 GPU 承载同样流量、或降低时延。
- 端侧 / 边缘部署（GGUF 等格式）。

## 关键做法
- 选方案：Hopper 及以上卡优先 FP8（W8A8，精度损失最小）；显存紧张用 W4A16（GPTQ / AWQ）；Blackwell 卡可评估 NVFP4；KV Cache 可单独 FP8 量化以提升并发。
- 流程：加载模型 → 选 recipe（如 FP8 / W4A16）→ 用业务相关校准集 oneshot → save_pretrained → vLLM 加载。
- 校准数据用真实业务样本几百条，不用纯通用语料。
- 量化前后跑同一业务评测集 + 压测，对比准确率、吞吐、P99，写进上线评审。
- 优先使用官方或模型厂商发布的量化权重，省去自己校准。

## 常见坑
- 只看通用基准不看业务评测，数学、代码、长上下文等能力在低比特下掉得更多。
- 硬件不支持对应格式（如旧卡无 FP8 算子），速度反而变慢。
- LoRA 适配器与量化底座组合未验证（见 peft-lora）。

## 迁移
- FP16 全精度部署 → FP8：通常可直接替换，验证后切流；再按需评估 INT4。
- 旧版 AutoGPTQ / AutoAWQ 工具链：改用 llm-compressor 产出 compressed-tensors。

## 最佳做法
- 量化产物记录：原模型版本、算法、校准集版本、评测分数，登记到模型仓库（见 mlflow）。

## CHANGELOG
- 2026-11-14 v1.0.0 首版；情报员自动核实（来源见 sources）
