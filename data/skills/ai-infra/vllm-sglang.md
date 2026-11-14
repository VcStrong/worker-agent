---
id: vllm-sglang
name: 推理引擎（vLLM / SGLang）
aliases: [vLLM, SGLang, PagedAttention, RadixAttention, 推理服务, PD 分离, 大模型推理引擎]
roles: [ai-infra-mlops, model-algorithm-engineer]
maturity: 采用
as_of: 2026-11-14
version: 1.0.0
sources:
  - https://docs.vllm.ai/en/stable/
  - https://github.com/vllm-project/vllm/releases
  - https://docs.sglang.io/
  - https://github.com/sgl-project/sglang/releases
region: both
replaces: []
replaced_by: []
from_graph: true
---

# 推理引擎（vLLM / SGLang）

## 成熟度判断
- 采用：图谱原有工具。vLLM 稳定版 v0.32.0（2026-10-18，v0.33 为 RC），支持 PagedAttention、连续批处理、分块预填充、前缀缓存、多种量化、张量 / 流水线 / 专家 / 上下文并行、预填充-解码分离，提供 OpenAI 兼容、Anthropic Messages 与 gRPC 接口，硬件含 NVIDIA、AMD，并经插件支持昇腾等。SGLang 最新 v0.5.23（2026-11-02），RadixAttention 前缀缓存，官方称全球 40 万+ GPU 在用，支持 NVIDIA、AMD、TPU、昇腾、摩尔线程。
- 两者都还在 1.0 之前、发版频繁，生产要锁版本。

## 什么时候用
- 自部署开源 / 微调模型（数据不出域、成本、定制化需求）。
- 高并发在线推理、离线批量推理、RL 训练中的 Rollout。

## 关键做法
- 选型：通用默认 vLLM（生态最广）；前缀复用多（多轮、Agent、结构化输出）或 DeepSeek 类 MoE 大模型可重点对比 SGLang；两者用同一压测脚本比吞吐与 P99。
- 对外统一 OpenAI 兼容接口，挂在模型网关后（见 llm-gateway-routing）。
- 开启前缀缓存；长输入场景开分块预填充；大规模部署评估 PD 分离。
- 量化优先 FP8（显存与精度平衡），更省用 W4A16（见 model-quantization）。
- 部署在 Kubernetes，用就绪探针 + 预热；采集 Prometheus 指标（队列长度、KV Cache 使用率、TTFT、TPOT）。

## 常见坑
- 不锁版本自动升级，行为或性能回退。
- max_model_len 与显存利用率设置不当导致 OOM 或 KV Cache 太小、并发上不去。
- 国产卡走插件 / 分支版本，算子覆盖和性能需单独验证。
- 低流量时独占 GPU，成本远高于调 API（见 llm-cost-estimation）。

## 迁移
- 从 HF Transformers 直接推理或 TGI：换成 vLLM / SGLang 的 OpenAI 兼容服务，调用方只改 base_url。
- TensorRT-LLM 适合极致 NVIDIA 优化场景，可作为对比项保留。

## 最佳做法
- 每次升级引擎或模型，跑固定压测 + 评测集两套回归。

## CHANGELOG
- 2026-11-14 v1.0.0 首版；情报员自动核实（来源见 sources）
