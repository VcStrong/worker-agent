---
id: mlflow
name: MLflow（实验与模型管理）
aliases: [MLflow, 实验追踪, 模型注册表, Model Registry, MLflow Tracing, Prompt 管理]
roles: [ai-infra-mlops, model-algorithm-engineer, ai-eval-compliance]
maturity: 采用
as_of: 2026-11-14
version: 1.0.0
sources:
  - https://mlflow.org/docs/latest/
  - https://github.com/mlflow/mlflow/releases
region: both
replaces: []
replaced_by: []
from_graph: true
---

# MLflow（实验与模型管理）

## 成熟度判断
- 采用：图谱原有工具。MLflow 3 系列持续发版（最新 v3.18.0，2026-11-04），覆盖传统 ML 的实验追踪、模型注册、打包部署，并扩展到大模型 / Agent 的可观测（Tracing）、评测框架与 Prompt 管理。开源可私有化，国内部署无障碍。

## 什么时候用
- 训练 / 微调实验记录与对比、模型版本管理与上线审批。
- 大模型应用的 Trace 采集、评测结果留档、Prompt 版本管理（不想依赖海外 SaaS 时）。

## 关键做法
- 每次训练记录：代码版本、数据版本、超参、指标、产物（含 LoRA 适配器、量化模型）。
- 模型注册表管理版本与别名（如 champion / challenger），上线只认注册表里的版本。
- 大模型应用接入 Tracing，记录每步调用、工具、Token、时延，与评测集关联。
- 评测结果写回同一 Run，便于把「模型版本 ↔ 评测分数 ↔ 上线决策」串起来。
- 后端存储用数据库 + 对象存储，开启鉴权，不要裸露在公网。

## 常见坑
- 只记指标不记数据版本，实验不可复现。
- Tracking Server 未开鉴权，模型和数据被随意下载。
- Trace 中存储用户原文未脱敏。

## 迁移
- MLflow 2.x → 3.x：按官方 Release Notes 检查破坏性变更，先在测试环境升级并验证注册表与存储兼容。
- 从 Excel / 文档记实验：先强制所有训练脚本调用 MLflow 记录，再迁历史结果。

## 最佳做法
- 模型上线审批单直接引用注册表版本号和评测 Run 链接。

## CHANGELOG
- 2026-11-14 v1.0.0 首版；情报员自动核实（来源见 sources）
