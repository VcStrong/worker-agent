# 待核实清单（REQ-019 / 021）

> 情报员核实不到一手官方来源的候选或细节，**没有写入技能层**（或正文里刻意不写具体值）。有新证据时走提案。

## 首版核实（g1，2026-11-14）


核实日期：2026-11-14。以下候选没有写成独立技能包，或只在已核实技能包里作为备选提及、不作推荐依据。

| 候选 | 适用专家 | 查了哪些地方 | 为什么没核实到 |
|---|---|---|---|
| 个推（Getui）推送 | data-growth、client-engineer | docs.getui.com、www.getui.com（curl / WebFetch 均超时）；WebSearch「个推 官方文档 厂商通道」只返回 DCloud、阿里云、腾讯云等第三方转述 | 官网与文档站本环境无法访问，没有一手来源；push-cn-vendor-channels 只以极光 + 厂商通道 + 鸿蒙 Push Kit 为依据，未写入个推 |
| Midjourney 当前版本号 | ux-designer、data-growth | docs.midjourney.com/docs/models（HTTP 403）；WebSearch 只有第三方报道 V8 / V8.1 / V8.2 且日期互相矛盾 | 官方文档拒绝抓取，版本号无法一手确认；ai-image-generation 只引用官方文档地址，未写具体版本，以即梦 / Figma AI 为主 |
| 即时设计帮助中心与功能细节 | ux-designer | js.design 首页（仅拿到标题「专业 UI 设计工具，在线协作更高效」）；WebSearch 只有第三方目录站 | 官网为前端渲染，取不到功能、价格、私有化说明；mastergo-jsdesign 的具体做法以 MasterGo 官网为准，即时设计只确认产品存在与定位 |
| GrowingIO 官网 / 帮助中心（growingio.com、docs.growingio.com） | data-growth、product-manager | curl 超时；WebSearch 返回 growingio.gitbook.io（无法确认是否官方） | 官网不可达；sensors-growingio 中 GrowingIO 仅以其官方 GitHub 组织的 SDK Release（v4.7.0）为依据 |
| 火山引擎「国内指标平台」（DataLeap / DataWind 指标能力）、网易数帆等 | data-growth | 未找到可访问的一手文档页 | 时间内未完成核实；metrics-semantic-layer 国内侧只采用阿里云 Dataphin（help.aliyun.com 已核实） |
| Intercom Fin（海外大模型客服） | data-growth、ai-app-engineer | www.intercom.com/fin（308 跳转）、帮助中心链接 404 | 未拿到可读官方页面；llm-customer-service 海外侧以 Zendesk AI agents 官方页为依据 |
| v0 最新版本 / 功能细节 | product-manager | v0.app/docs（WebSearch 摘要可见，未逐页抓取） | 仅核实到官方文档入口与核心能力（生成、GitHub、部署到 Vercel），未写具体版本；已在 ai-prototyping 中标为试用 |

## 首版核实（g2，2026-11-14）


核实日期：2026-11-14

## 未写技能包的候选

| 候选 | 适用专家 | 查了哪些地方 | 结论 / 原因 |
|---|---|---|---|
| Vue 2（暂缓项） | frontend-engineer | 图谱 E-01 tl / tx（只有泛称「Vue」，无 Vue 2）；v2.vuejs.org/eol | 官方 EOL 已核实（2023-12-31，最终版 2.7.16），但图谱里没有 Vue 2 这一写法，不满足「图谱原有工具」条件，未单独建暂缓包；EOL 与迁移建议已写进 vue-nuxt 的「迁移」节 |
| Flutter 鸿蒙适配（社区 OpenHarmony 版 Flutter） | client-engineer | docs.flutter.dev、blog.flutter.dev | Flutter 官方未声明支持 HarmonyOS NEXT，未找到一手官方来源；不建包，flutter 包中注明「鸿蒙走原生，社区方案需单独评估」 |

## 已建包但部分细节未能从一手来源确认（正文已避免写死）

- HarmonyOS 26.0.0 / HarmonyOS 7.0：华为升级适配指南已发布，但页面未写正式发布日期与对应 DevEco Studio 版本号；正文以 6.0.0(20) 与 6.1.1(24) 的已发布版本为准。
- Taro 4.x 最新版本日期：GitHub Releases 列到 v4.3.0，未确认发布日期；正文只写版本号。
- 微信小程序基础库：官方日志检索到的最新条目为 3.17.3（2026-08-20），可能有更新版本未被检索到。

## 首版核实（g3，2026-11-14）


本组（backend-engineer / architect / sre-security）候选全部找到一手官方来源，没有因无法核实而不写的技能包。

说明（未建包，但不属于「核实失败」）：
- Zabbix 等过时监控工具：图谱 O-01 / O-02 / E-06 的 tl 里没有 Zabbix（只有 Kubernetes、Prometheus / Grafana、日志平台、发布系统、云控制台、Nginx / Istio、Kafka、GitLab CI 等），不需要建「暂缓」包。
- Betterleaks（Gitleaks 作者的新项目）：只核实到 GitHub 仓库（2026-02 创建，MIT），没有正式发布说明，没有单独建包，只在 secret-scanning 里写成「评估」。
- PostgreSQL 19：官方公告到 RC 阶段（REL_19_RC2，计划 2026-11-19 GA），尚未 GA，postgresql 包写成「新项目用 18、19 等补丁版后再上」。
- 国内云对 FinOps FOCUS 账单格式的原生导出支持：没有查到阿里云 / 腾讯云 / 华为云的官方说明，finops-focus 里写成「需逐家确认」。
- 国内云托管网关对 Kubernetes Gateway API 的支持：没有逐家核实，kubernetes-gateway-api 里写成「以云厂商文档为准」。

## 首版核实（g4，2026-11-14）


核实日期：2026-11-14

## 整条未核实（未写技能包）
- 无。REQ-019 分给 g4 的候选都找到了官方或一手来源，已写入 data/skills/ai-*/。

## 部分细节未核实（技能包已写，但正文刻意没写具体值）
- 豆包（火山方舟）当前主力文本模型名和版本
  - 适用专家：ai-product-manager、ai-app-engineer、ai-infra-mlops（llm-providers-cn）
  - 查过：docs.volcengine.com/docs/82379/1330310（官方文档页，抓取结果只有导航，看不到模型表）、WebSearch（只有媒体报道）
  - 原因：官方页没抓到模型表正文，所以正文只写「以官方模型列表页为准」，没写版本号。
- 文心（百度千帆）当前主力 ERNIE 模型名和版本
  - 适用专家：同上
  - 查过：cloud.baidu.com/doc/qianfan/index.html（官方，没有列模型）、WebSearch（只有第三方 / arXiv 来源）
  - 原因：官方文档首页没列具体模型，所以正文只写平台，没写版本号。
- OpenTelemetry GenAI 语义约定的状态（development / stable）和指标名
  - 适用专家：ai-infra-mlops（llm-cost-monitoring）
  - 查过：opentelemetry.io/docs/specs/semconv/gen-ai/（页面写着已迁到新仓库）、github.com/open-telemetry/semantic-conventions-genai（README 没写状态）
  - 原因：正文只写「仍在演进，要锁版本并加一层映射」，没写具体属性名。
- EU AI Act 修订后第 50 条（透明度 / 机器可读标注）的确切适用日期
  - 适用专家：ai-eval-compliance（eu-ai-act）
  - 查过：eur-lex.europa.eu/eli/reg/2026/1744/oj（自动抓取返回空页）、efta.int EEA-Lex（只有元数据）、digital-strategy.ec.europa.eu（写的是「2026 年 8 月」）
  - 原因：按欧委会官方页写成「2026-08」；律所提到的「机器可读标注推迟到 2026-12-02」没有官方原文佐证，所以没写进去。

