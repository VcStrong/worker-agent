---
id: peft-lora
name: 参数高效微调（LoRA / QLoRA）
aliases: [PEFT, LoRA, QLoRA, DoRA, 参数高效微调, 低秩适配, LLaMA-Factory]
roles: [model-algorithm-engineer, ai-infra-mlops]
maturity: 采用
as_of: 2026-11-14
version: 1.0.0
sources:
  - https://github.com/huggingface/peft
  - https://github.com/huggingface/peft/releases
  - https://huggingface.co/docs/peft/index
region: both
replaces: []
replaced_by: []
from_graph: false
---

# 参数高效微调（LoRA / QLoRA）

## 成熟度判断
- 采用：Hugging Face PEFT 是事实标准库（最新 v0.21.3，2026-11-13），与 Transformers、TRL、Accelerate、Diffusers 深度集成；图谱原有的 LLaMA-Factory 也基于它。官方示例中 LoRA 可训练参数约 0.1%，检查点只有几十 MB。

## 什么时候用
- 领域风格 / 格式 / 术语适配、分类抽取等固定任务，且 Prompt + RAG 已到瓶颈。
- 需要一个底座挂多个业务适配器（多租户、多任务）。
- 显存有限：QLoRA（4bit 量化底座 + LoRA）单卡即可微调中等规模模型。

## 关键做法
- 先判断要不要微调：知识更新用 RAG，行为 / 格式 / 风格用微调。
- 数据优先：几百到几千条高质量指令样本胜过大量噪声数据；留出验证集和业务评测集。
- 起步参数：rank 8~64，覆盖注意力和 MLP 投影层，学习率高于全参微调；对比 1~2 组即可。
- 用 TRL 做 SFT / DPO，PEFT 负责适配器；训练记录进 MLflow（见 mlflow）。
- 部署：vLLM / SGLang 支持多 LoRA 动态加载，或合并权重后再量化（见 model-quantization）。

## 常见坑
- 用微调灌知识，模型仍会编造，且知识更新要重训。
- 只看训练 loss，不跑业务评测集，上线后通用能力退化（灾难性遗忘）。
- 训练与推理的对话模板（chat template）不一致，效果骤降。
- 用于对公众服务的微调模型属于新模型，国内需评估是否走备案（见 genai-service-filing）。

## 迁移
- 全参微调 → LoRA：同数据同评测集对比，效果接近即切换，节省训练与存储成本。

## 最佳做法
- 每个适配器记录：底座版本、数据版本、超参、评测分数，可追溯可回滚。

## CHANGELOG
- 2026-11-14 v1.0.0 首版；情报员自动核实（来源见 sources）
