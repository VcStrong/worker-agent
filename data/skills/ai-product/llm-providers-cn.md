---
id: llm-providers-cn
name: 国内大模型供应商选型（通义千问 / DeepSeek / 豆包 / 文心）
aliases: [国内大模型, 通义千问, Qwen, 阿里云百炼, DeepSeek, 豆包, 火山方舟, 文心, 千帆, ERNIE]
roles: [ai-product-manager, ai-app-engineer, ai-infra-mlops]
maturity: 采用
maturity_by_region: {cn: 采用, global: 评估}
as_of: 2026-11-14
version: 1.0.0
sources:
  - https://help.aliyun.com/zh/model-studio/models
  - https://api-docs.deepseek.com/quick_start/pricing
  - https://docs.volcengine.com/docs/82379/1330310
  - https://cloud.baidu.com/doc/qianfan/index.html
  - https://www.cac.gov.cn/2023-07/13/c_1690898327029107.htm
region: cn
replaces: []
replaced_by: []
from_graph: false
---

# 国内大模型供应商选型

## 成熟度判断
- region=cn 采用：面向境内公众的服务须使用已备案的模型（《生成式人工智能服务管理暂行办法》2023-08-15 施行），国内四家均有官方 API 平台和备案模型。
- region=global 评估：海外业务一般优先海外供应商，国内模型只作对比或成本备选。
- 当前版本（官方页 2026-11-14 核实）：阿里云百炼列出 qwen4-max-preview、qwen3.7-plus、qwen3.8-flash、qwen3.8-omni-flash 等；DeepSeek 为 deepseek-flash（V4.1-Flash）与 deepseek-v4-pro，1M 上下文，分峰谷计价；豆包（火山方舟）、文心（百度千帆）以官方模型列表页为准。

## 什么时候用
- 国内 App / 小程序 / Web 的面向公众 AI 功能（默认）。
- 需要数据境内存储、对接国内云（阿里云 / 火山引擎 / 百度智能云）的项目。

## 关键做法
- 选型维度：效果（用自家评测集跑，不看榜单）→ 价格（含缓存命中价、峰谷价、Batch）→ 时延与并发上限 → 能力（工具调用、结构化输出、上下文缓存、多模态）→ 合规（备案、数据不出境、SLA）。
- 至少接两家，经模型网关切换（见 llm-gateway-routing），避免单点。
- 优先 OpenAI 兼容接口接入；DeepSeek 还提供 Anthropic 兼容接口，便于复用代码。
- 简单任务用 flash / 轻量档，复杂推理再用旗舰档，按路由分流。

## 合规要点（国内必看）
- 调用他人已备案模型做应用：上线前在属地网信办办理「登记」，在显著位置公示所用模型名称与备案号。
- 自研或微调后对公众提供：走生成式人工智能服务备案（安全评估 + 算法备案），见 genai-service-filing。
- 生成内容按《人工智能生成合成内容标识办法》加标识，见 ai-content-labeling。

## 常见坑
- 用海外模型直接对境内公众提供服务，属未备案模型，不可上线。
- 模型名硬编码；供应商频繁更名（如 DeepSeek 旧名 deepseek-v4-flash 已退役并被重定向），要配置化。
- 只比标价不比缓存命中率和输出长度，实际账单差距可达数倍。

## 迁移
- 从单一供应商迁到多供应商：先接网关、统一评测集，再灰度切流。

## 最佳做法
- 每季度用同一评测集重跑一次各家主力模型，更新默认选择。

## CHANGELOG
- 2026-11-14 v1.0.0 首版；情报员自动核实（来源见 sources）
