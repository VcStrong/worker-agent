---
id: k6-load-testing
name: 性能压测（Grafana k6 / JMeter）
aliases: [k6, Grafana k6, JMeter, 压测, 性能测试, load testing, Locust]
roles: [qa-expert, sre-security, backend-engineer]
maturity: 采用
as_of: 2026-11-14
version: 1.0.0
sources:
  - https://github.com/grafana/k6/releases
  - https://grafana.com/docs/k6/latest/
  - https://jmeter.apache.org/download_jmeter.cgi
region: both
replaces: []
replaced_by: []
from_graph: false
---

# 性能压测（Grafana k6 / JMeter）

当前版本：k6 v2.4.0（2026-11-12）；k6 v2.0.0 于 2026-05-11 发布（移除大量废弃命令与选项、Go 模块路径改为 go.k6.io/k6/v2）。Apache JMeter 5.6.3（2024-01，Java 8+，推荐 Java 17+）。
判断理由：k6 用 JavaScript 写脚本、易纳入代码评审与 CI，支持阈值判定、浏览器与 gRPC 模块，遵循语义化版本，新压测项目定「采用」；JMeter 仍稳定可用，适合存量脚本与 GUI 录制场景。图谱 Q-02 原有「JMeter / Locust」。

## 什么时候用
- 上线前容量评估、大促 / 活动前压测、接口性能回归。
- 需要把性能门禁放进 CI（P95 延迟、错误率不达标即失败）。
- 存量 JMeter 脚本、需要 GUI 录制或特定协议插件时继续用 JMeter。

## 关键做法
- 场景建模：用 scenarios + executor（如 ramping-arrival-rate）按到达率施压，模拟真实流量曲线而不是固定并发。
- 用 thresholds 写验收标准（如 `http_req_duration: ['p(95)<300']`、`http_req_failed: ['rate<0.01']`），与 SLO 对齐。
- 脚本进 Git，参数化数据与环境变量分离；压测结果输出到 Grafana / Prometheus 与链路追踪对照分析。
- 压测分级：基准 → 负载 → 压力 → 稳定性（长时间） → 尖峰。
- 分布式大规模压测用 k6 Operator（Kubernetes）或云服务。

## 常见坑
- k6 升到 v2：`k6 login`、`k6 cloud script.js` 位置参数、`externally-controlled` 执行器、`options.ext.loadimpact` 等已移除，升级前全文搜索替换；扩展需改为 v2 模块路径。
- 压测机自身成为瓶颈（CPU / 带宽），先监控施压端。
- 直接压生产会影响用户；用影子流量 / 隔离环境，或在低峰期按预案小流量验证。

## 迁移
- 从 JMeter 迁移：新场景直接用 k6 编写；存量 .jmx 在稳定使用期内继续维护，改造时再按场景重写，不做一次性全量转换。
- k6 v1 → v2：按 v2.0.0 发布说明逐项替换废弃 API，先在 CI 中并行跑两版对比结果。

## 最佳做法
- 每次压测产出报告：目标、场景、结果、瓶颈、优化建议、复测结论，归档到测试报告。

## CHANGELOG
- 2026-11-14 v1.0.0 首版；情报员自动核实（来源见 sources）
