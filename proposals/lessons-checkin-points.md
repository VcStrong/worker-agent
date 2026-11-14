# 经验条目：checkin-points（App 每日签到 + 积分）

- 来源需求：checkin-points（/tmp/ra-e2e/app/workspace/checkin-points/）
- 收集：总控，2026-11-15。来源是 02–08 各阶段小结、06-CodeReview.md 和 07 测试报告里的经验条目。
- 已对照 data/skills 的现有内容去重，没有发现重复。同类条目已合并：PG 写入时间和对账口径合并为一条；「内存 / PG 同套测试」和「对账注入异常」合并为一条。
- 所有条目 status 都是「待拍板」。要用户拍板后才由 `scripts/apply_proposal.py` 应用，总控不直接改技能包。

### L20261115-checkin-01 加锁事务里，判定输入要在拿到锁之后再算
```yaml
action: append_lesson
skill: postgresql
section: 常见坑
text: "按用户加行锁（SELECT ... FOR UPDATE）的事务里，「今天 / 业务日期 / 规则版本」这类判定输入必须在拿到锁之后再计算；在加锁前算，跨零点的并发请求如果后发先到，会把连续签到误判为断签、少发奖励（checkin-points CR P-01）"
source_need: checkin-points
role: architect
scope: public
status: 待拍板
```

### L20261115-checkin-02 PG now() 不代表写入顺序；对账不要从 created_at 推业务日期
```yaml
action: append_lesson
skill: postgresql
section: 常见坑
text: "now() / CURRENT_TIMESTAMP 取的是事务开始时间，不是实际写入时间。只追加的流水表要在拿锁后用 clock_timestamp() 写 created_at；对账 SQL 按业务日期字段（如 checkin_date）分组、按自增 id 排序，不要用 created_at 推算业务日期或先后顺序，否则会误报（checkin-points CR P-05/P-06）"
source_need: checkin-points
role: backend-engineer
scope: public
status: 待拍板
```

### L20261115-checkin-03 内存 / PG 两套存储共用一套测试，对账脚本要注入异常验证
```yaml
action: append_lesson
skill: postgresql
section: 最佳做法
text: "存储层有内存实现和 PG 实现时，用同一套测试分别跑两遍（内存锁通过不能证明 PG 行锁正确）；资金类对账脚本上线前要人为注入异常数据（余额≠流水和、同日重复发放）来验证它能检出，另外配一条「对账没跑」告警"
source_need: checkin-points
role: qa-expert
scope: public
status: 待拍板
```

### L20261115-checkin-04 幂等 request_id 不要用拦截器自动注入
```yaml
action: append_lesson
skill: kotlin-coroutines-flow
section: 常见坑
text: "幂等写请求（如签到、支付）的 request_id 必须由业务层生成，只在结果不明（超时、断连、502/504）时用同一个 id 重发确认；OkHttp 拦截器每次请求自动注入新 id 会破坏这种复用。签到这类状态机要放在 @ApplicationScope 的单例里，避免离开页面时请求被取消"
source_need: checkin-points
role: client-engineer
scope: public
status: 待拍板
```

### L20261115-checkin-05 Paging 3 的 initialLoadSize 默认是 pageSize 的 3 倍
```yaml
action: append_lesson
skill: jetpack-compose
section: 常见坑
text: "Paging 3 的 PagingConfig.initialLoadSize 默认是 pageSize × 3。服务端契约限制 limit 上限（如 ≤ 50）时，首屏请求会超限或和游标分页口径不一致，必须显式设 initialLoadSize = pageSize"
source_need: checkin-points
role: client-engineer
scope: public
status: 待拍板
```

### L20261115-checkin-06 信任网关 header 的服务要把 header 剥离写成测试和上线阻断项
```yaml
action: append_lesson
skill: kubernetes-gateway-api
section: 最佳做法
text: "后端只信任网关注入的身份 header（如 X-User-Id）时，网关必须剥掉客户端自带的同名 header，服务用 NetworkPolicy 只放行网关；这两点要写成测试用例和上线单阻断项，并约定网关不改写幂等 header（X-Request-Id）"
source_need: checkin-points
role: sre-security
scope: public
status: 待拍板
```

### L20261115-checkin-07 技术方案要包含一键关闭和冒烟数据规划
```yaml
action: append_lesson
skill: gitops-argocd
section: 最佳做法
text: "发放资产类功能（积分、优惠券）在技术方案阶段就要设计服务端功能开关（如 CHECKIN_ENABLED）和网关层一键关闭；流水只追加时冒烟数据删不掉，上线前要规定测试账号和发放金额。灰度判据同时看累计请求数和时长，并覆盖周期性奖励节点"
source_need: checkin-points
role: sre-security
scope: public
status: 待拍板
```

### L20261115-checkin-08 零依赖 Go 服务的 /metrics 口径
```yaml
action: append_lesson
skill: opentelemetry
section: 常见坑
text: "Go 标准库的 expvar 输出的是 JSON，Prometheus 抓不了；要求零第三方依赖的服务，/metrics 要么自研 Prometheus 文本格式，要么接 OTel SDK 再导出，在技术方案阶段就定下口径"
source_need: checkin-points
role: sre-security
scope: public
status: 待拍板
```

## 流程改进（不对应技能包，供总控 / 模板维护者参考，不经 apply_proposal）

- 子 agent 的 Bash 权限可能被拒（本次后端、QA 都执行不了 `command -v go` 和 git）。05 探测工具链时，就要让用户确认 06 / 07 能执行编译和测试命令，或者提供 CI / Docker 环境；否则 06 / 07 只能静态走查，「通过」会退化成「有条件通过」。（角色：architect / backend-engineer / qa-expert）
- 工具链探测命令要一条一次执行；用 `;`、`&&`、`||` 拼接的复合命令会被权限拦截。（角色：architect）
- 没有 Edit 工具的角色（product-manager、ux-designer、ai-product-manager）修改产物时只能整份重写，容易留下临时文件。建议 03 执行计划里约定「产物一次写成，局部修改由总控代改」。（角色：ux-designer）
- 没有编译器时，Code Review 结论只能写「静态未发现」，不能写「通过」，06 准出相应降级为「有条件」。（角色：architect）
