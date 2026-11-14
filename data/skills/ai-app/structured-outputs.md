---
id: structured-outputs
name: 结构化输出（JSON Schema 约束）
aliases: [Structured Outputs, JSON Mode, JSON Schema, strict tool use, 函数调用参数校验]
roles: [ai-app-engineer, ai-product-manager]
maturity: 采用
as_of: 2026-11-14
version: 1.0.0
sources:
  - https://platform.claude.com/docs/en/build-with-claude/structured-outputs
  - https://developers.openai.com/api/docs/guides/structured-outputs
  - https://api-docs.deepseek.com/quick_start/pricing
  - https://docs.volcengine.com/docs/82379/1330310
region: both
replaces: []
replaced_by: []
from_graph: false
---

# 结构化输出（JSON Schema 约束）

## 成熟度判断
- 采用：Claude（JSON 输出 + strict 工具调用）、OpenAI（json_schema + strict）均官方支持按 Schema 约束解码；国内 DeepSeek 官方标注支持 JSON 输出，火山方舟文档有「结构化输出（beta）」，阿里云百炼支持 JSON Mode。
- 差异：海外两家是「Schema 级保证」，国内多为「保证是合法 JSON」，字段约束仍需自己校验。

## 什么时候用
- 抽取、分类、表单填充、生成配置、Agent 工具参数等需要程序消费的输出。
- 下游是数据库写入或接口调用，不能容忍解析失败。

## 关键做法
- 用 Pydantic / Zod 定义 Schema，SDK 直接生成 JSON Schema 并解析回对象。
- OpenAI strict 模式：根节点为 object，所有字段列入 required，additionalProperties: false；可选字段用「类型或 null」表达。
- Agent 场景：工具调用开 strict，最终答案用 JSON 输出，两者可组合。
- 国内模型：开 JSON Mode（消息里通常需包含 json 字样）+ 本地 Schema 校验 + 失败重试一次 + 业务规则校验。
- Schema 字段加 description，等同给模型的字段说明。

## 常见坑
- 结构正确不等于内容正确，仍需评测字段准确率。
- Schema 过深过大，增加输入 Token 并降低质量；Claude 会为输出格式额外注入系统提示，输入 Token 略增。
- 使用了 strict 不支持的 JSON Schema 关键字，请求报错。
- 拒答或截断（max_tokens 不足）时输出不完整，要处理 stop_reason。

## 迁移
- 从「Prompt 里要求输出 JSON + 正则提取」迁到官方结构化输出；保留本地校验作为兜底。
- Claude 旧的 beta 头与 output_format 参数官方给了过渡期，新代码按当前文档参数写。

## 最佳做法
- 枚举类字段用 enum 限定，比自由文本准确率高、评测也更容易。

## CHANGELOG
- 2026-11-14 v1.0.0 首版；情报员自动核实（来源见 sources）
