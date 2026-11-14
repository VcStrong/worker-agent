<!-- 负责：架构师 | 阶段：06 开发联调 | 产物：Code Review + 契约答复（无模板） -->
# Code Review 与契约答复：checkin-points（06 开发联调）

## 引用
- /tmp/ra-e2e/app/workspace/checkin-points/05-技术方案.md：接口契约（已锁定）、签到事务流程 1–10 步、存储接口草案、数据模型、对账 SQL、超时约定、Android 实现要点
- /tmp/ra-e2e/app/workspace/checkin-points/06-自测记录-后端.md：后端自报偏离（`UserTx.LedgerByBiz`、`/metrics` 未做），标注「未编译、未运行」
- /tmp/ra-e2e/app/workspace/checkin-points/06-自测记录-Android.md：实现说明（android/ 未落盘）和文末 8 个契约 / 交互问题
- /tmp/ra-e2e/app/workspace/checkin-points/04-交互说明.md：签到状态机（第 52、186、199 行）、429 按钮恢复（第 149 行）、「明天 +N」（第 138 行）
- /tmp/ra-e2e/app/workspace/checkin-points/02-PRD.md：US-02、US-07，埋点 `checkin_result`（第 158 行）
- 审查对象：/tmp/ra-e2e/app/server/ 下全部源码、测试、SQL（go.mod、.gitignore、configs/rules.json、cmd/server/{main,main_nopg,main_pg}.go、internal/{civil,clock,rules,store,store/memory,store/postgres,service,ratelimit,httpapi}/*.go、migrations/*.sql、scripts/reconcile.sql）
- 没有知识库，本期没有以前的结论可引用。

**审查方式**：本机没有 Go，代码从未编译。本次是人工「编译器式」静态审查，没有运行任何 go 命令，下面关于「能编译」的结论都是**静态判断，不等于编译通过**。逐文件核对了：
1. import：每个文件的每个 import 都有使用点，没有未使用的 import；没有声明后未使用的局部变量（`:=` 重声明和 if / 块作用域遮蔽逐个看过，例如 service.go 的 `res, err :=` 都至少引入了一个新变量）。
2. 类型和签名：`store.Store` / `store.UserTx` 在 memory（有 `var _` 编译期断言）和 postgres（无断言，人工核对 5 + 8 个方法）中签名一致；`service.New`、`httpapi.Config`、`ratelimit.Limiter.Allow` 的调用方和定义一致；`clock.Real`（值接收者）和 `*clock.Fixed`（指针接收者）都满足 `clock.Clock`；main.go 里 `p.Ping` 的方法值类型是 `func(context.Context) error`，和 `Ready` 字段一致。
3. 标识符遮蔽：memory.go 里 `fn func(tx store.UserTx) error` 的形参名 `tx` 只在函数类型里出现，不会遮蔽函数体里的 `&tx{...}` 类型；service.go 的 `rules` 字段和 `rules` 包不冲突（字段只通过 `s.rules` 访问）。
4. build tag：`main_nopg.go`（`//go:build !pg`）和 `main_pg.go`（`//go:build pg`）互斥，`openPG` 两边签名一致，任何 tag 组合都恰好有一个定义；`internal/store/postgres` 只有带 `pg` tag 的文件，默认构建下 `./...` 会跳过这个包，默认构建不需要 pgx。
5. go.mod：`go 1.26` ≥ 1.22，ServeMux 新路由语义默认开启（不受 `httpmuxgo121` 影响）。
6. ServeMux 路由：`"GET /api/v1/checkin/status"`、`"POST /api/v1/checkin"` 等方法加路径的模式，和兜底的 `"/"` 之间是「更具体优先」的关系，注册时不会 panic；方法不对的请求会落到 `"/"` 的 fallback，再按 `knownRoutes` 返回 405 和 `Allow`，`TestNotFoundAndMethodNotAllowedUseEnvelope` 的期望和实现一致。
7. vet：slog 的键值对都是偶数个，键都是字符串字面量；`fmt.Errorf` 的 `%s` 参数是有 `String()` 方法的 `civil.Date`；没有复制锁的写法。
8. 测试期望值：按实现逐个手算了 service_test.go 和 httpapi_test.go 的断言（第 3 / 7 / 8 天、跨零点、并发 100、分页 10 / 9 条、429 的 `Retry-After=6`、坏游标 `MV8` 解出 `"1_"` 后 ParseInt 失败等），没有发现实现和期望值不一致的地方。

## 审查结论：有条件通过

- **没有发现有把握的编译错误**（默认构建和 `-tags pg` 都看了；`-tags pg` 需要先补 pgx 依赖，见 P-04）。
- **没有发现重复发分或余额不一致的资金错误**：同一用户的写操作由账户行锁（memory 里是 `txMu`）串行化；重放 → 已签 → 新签的顺序和方案第 4–9 步一致；`balance_after` 从锁内读到的余额开始累加；余额更新和流水写入在同一个事务里，发生错误时整笔回滚（memory 用缓冲区丢弃来模拟）。`uq_checkin_user_date`、`uq_checkin_user_request`、`uq_ledger_biz` 三道约束都在。
- 通过的条件（满足后才能进入 07 测试）：
  1. 修复 P-01（「今天」要在拿到锁之后再算）。
  2. 在有 Go 1.26+ 的环境（CI 或 `golang:1.27` 镜像）跑 `gofmt -l .`、`go vet ./...`、`go test ./... -race -count=1`，全部通过，并把输出附到自测记录。在这之前，「静态审查通过」不能当成「测试通过」。
  3. 08 上线前必须关闭 P-02（PG 实现编译、加测试、在 PG 18 上跑迁移和对账）。这条不影响 07 用 memory 实现先测。

## 问题清单

| 编号 | 文件:行 | 严重度 | 问题 | 修改建议 | 归属角色 |
|---|---|---|---|---|---|
| P-01 | server/internal/service/service.go:64-65（在锁外算 `today`、`rule`），:74-78（事务） | 主要 | 「今天」在进入 `WithUserTx` 之前就算好了。同一个用户跨零点的两个并发请求（例如两台设备，A 在 23:59:59.990 算出 D，B 在 00:00:00.010 算出 D+1），如果 B 先拿到锁，B 查「D+1 之前最近一条」时 D 的记录还没写入，会判成断签（streak=1）；随后 A 写入 D。结果是 D+1 的连签被错误重置，少发了连签奖励（不会多发分，也不会造成余额不一致，但用户资产算错了）。memory 和 PG 实现都有这个问题 | 把 `today := clock.Today(s.clk)` 和 `s.rules.Effective(today)` 移进 `WithUserTx` 的闭包里，作为闭包的第一步（这时已经拿到账户行锁）。这样后拿到锁的请求看到的一定是已提交的前序记录。语义仍然是「以服务端时间为准」（D5），只是取时间点从「收到请求」后移到「拿到锁」，差值不超过 `lock_timeout` 2 秒，契约不变。补一个单测：用 `clock.Fixed` 在闭包里拨时间，或者直接构造「D+1 的请求先进锁」的顺序，断言 D+1 的 streak 是 n+2 | 后端工程师 |
| P-02 | server/internal/store/postgres/postgres.go（全文件）；该目录下没有 `_test.go` | 主要 | PG 实现从未编译，也没有任何测试；资金正确性的最终保障（行锁、23505 映射、`lock_timeout`）只在这份代码里，memory 的测试覆盖不到它。另外静态看有两处要在真实 PG 上确认：① `(created_at, id) < ($2, $3)` 行比较里参数类型能不能正确推断；② `SMALLINT cycle_day` 扫描到 `int`（pgx v5 支持，但要实测） | 补 `postgres_test.go`（`//go:build pg`）：把 service 测试里的并发 100、同 id 并发重放、跨零点、分页插入抽成以 `store.Store` 为参数的套件，memory 和 PG 两边都跑；再加一个「拿锁超时 → 503」的用例（另开一个事务持有 `FOR UPDATE` 超过 2 秒）。08 上线前必须关闭 | 后端工程师；执行环境由 SRE 提供 |
| P-03 | server/internal/service/service.go:281-300（`Status` 的格子循环） | 次要 | 已签的格子每格都单独调一次 `GetCheckinByDate`，一次状态查询最多 8 次 SQL。方案容量按「2 次索引点查」估算，状态查询峰值 400 QPS 时会变成最多约 3200 QPS 打到 PG | 在 `Store` 上加一个只读方法 `ListCheckinsBetween(ctx, userID, from, to civil.Date)`，一条 `WHERE user_id=$1 AND checkin_date BETWEEN $2 AND $3`（走 `uq_checkin_user_date`）把本周期的记录一次取回来；这是内部接口，不改 HTTP 契约。07 前改不完的话可以先保留，在 08 压测时确认 | 后端工程师 |
| P-04 | server/go.mod:1-3；postgres.go:15-17 | 次要 | go.mod 里没有 pgx 依赖，也没有 go.sum，`go build -tags pg` 会直接报「no required module provides package」。自测记录已经写明，这里只是列为补测的第一步 | 在有网的环境执行 `go get github.com/jackc/pgx/v5@<最新 v5.x>`、`go mod tidy`，把 go.mod 和 go.sum 一起提交；补完后默认构建仍然不需要联网（模块缓存里要有 pgx 才能跑 `go mod verify`，CI 镜像要预热缓存） | 后端工程师 |
| P-05 | server/internal/store/postgres/postgres.go:223-226、:236-239；server/migrations/0001_init.up.sql:20、:35 | 次要 | `created_at DEFAULT now()` 取的是**事务开始**时间。同一用户的两个事务，先 BEGIN 的可能后拿到锁，结果后写入的流水 `created_at` 反而更早：① 流水按 `created_at DESC, id DESC` 排序时顺序和发放顺序相反；② 对账 C4 按 `created_at, id` 排 `LAG` 会误报链路断裂。这是我在 05 数据模型里留下的问题 | 在 `WithUserTx` 拿到行锁之后执行一次 `SELECT clock_timestamp()`，把结果存进 `userTx`，`InsertCheckin` / `AppendLedger` 显式写入 `created_at`。同一事务内的两条流水时间仍然相同（满足契约「奖励那条排在上面」靠 `id DESC`），同一用户的流水时间单调递增。不需要改表结构 | 后端工程师 |
| P-06 | server/scripts/reconcile.sql:10-12（C2）、:25（C4） | 次要 | C2 按流水 `created_at` 换算北京日期来分组：23:59:59.9xx 判为 D 的签到，如果事务在 00:00 之后才开始，它的流水会算到 D+1，用户 D+1 再签一次，C2 就会误报「一天 2 条基础分」。C4 的排序问题同 P-05。护栏指标误报多了，大家就会不再相信它。SQL 原文出自我写的方案 | C2 改成通过 `biz_id` 关联 `checkin_record`，按 `checkin_record.checkin_date` 分组；C4 改成 `ORDER BY id`（同一用户的写操作被行锁串行化，identity 分配顺序就是发放顺序）。我会同步更新 05 方案的对账 SQL 节（不涉及接口字段） | 架构师（SQL 口径）+ 后端工程师（改文件） |
| P-07 | server/cmd/server/main.go、server/internal/httpapi/router.go:52-61 | 次要 | 方案里写的 `/metrics`（expvar 计数）没做，后端已自报 | 08 前补：至少要有签到 ok / already / 4xx / 5xx 计数和事务耗时；只在内网暴露，不经过网关。如果 SRE 在 08 决定直接接 OTel，这条可以合并过去 | 后端工程师；口径由 SRE 与安全工程师定 |
| P-08 | server/internal/httpapi/middleware.go:122-123 | 次要 | 遇到不认识的 `X-User-Status` 值一律按受限处理，这是失败即安全的做法，我认可；但没有日志，网关以后新增状态值时，会悄悄变成用户签不了 | 不认识的值打一条 `warn`（带 status 原值和 trace_id，不带其他个人信息）；契约里补一句「未知值按受限处理」（澄清，不改字段） | 后端工程师 |
| P-09 | server/internal/httpapi/middleware.go:93-97 | 次要 | panic 发生在 handler 已经写过响应头之后时，recover 里再调 `writeJSON` 会触发 `superfluous WriteHeader` 并拼接出一个坏的 body | `statusRecorder` 记一个 `wroteHeader` 标志，recover 时如果已经写过就只记日志、不再写响应。当前 handler 都是最后一步才写响应，实际触发的概率很低 | 后端工程师 |
| P-10 | server/internal/httpapi/httpapi_test.go | 次要 | 少几个和契约直接相关的用例：① 大写 `X-Request-Id` 重放时要命中同一条记录（实现里 router.go:112 转成了小写，没有测试锁住）；② `store.ErrUnavailable` → 503 `service_unavailable`；③ 503 / 500 的响应体也要是统一外壳 | 用一个返回 `ErrUnavailable` 的假 Store 补 ②③；①直接发两次签到请求，一次大写、一次小写 | 后端工程师；测试专家在 07 用例里覆盖 |
| P-11 | server/internal/store/postgres/postgres.go:192-195 | 次要（仅记录） | 重放和 already 分支走的是 COMMIT（事务里只做了 `INSERT … ON CONFLICT DO NOTHING`），方案写的是 ROLLBACK。结果等价，不影响正确性 | 不用改；如果想和方案一字不差，可以让 service 返回一个哨兵值让存储层 ROLLBACK，收益很小，不建议为此加复杂度 | — |

计数：阻断 0，主要 2（P-01、P-02），次要 9。

## 契约答复

原则：锁定的字段、错误码、header 名都不改；下面全部用澄清解决。需要改 04 交互说明措辞或 PRD 埋点口径的，交给对应角色确认，不涉及接口契约。

| # | 问题 | 答复 | 类型 |
|---|---|---|---|
| A1 | 用 `server_date` 判断跨天是循环的，onResume 什么时候去拉 | 你的做法可以接受：设备时间换算成北京日期**只用来决定要不要去拉**，展示一律用服务端值。再加一个校准手段：本服务每个响应都带 HTTP 标准的 `Date` 头（Go `net/http` 自动加），客户端在每次成功响应时记下 `offset = Date 头 − 设备当前时间`，判断时用 `设备时间 + offset` 换算北京日期，就算设备时间被改了也能判对。触发条件定为：① 换算出的北京日期 ≠ 缓存的 `server_date`；② 距上次成功拉取超过 5 分钟；③ 没有缓存。三者满足任意一条就拉，两次拉取至少间隔 30 秒。`Date` 是标准头，不是新增字段 | 澄清（不改契约字段） |
| A2 | 发出后连接被重置、网关 502/504（可能是 HTML）、响应体解析失败，算什么 | 统一规则：**只有拿到本服务的统一外壳（能解析出 `code`）才算明确结果**。其中 `internal_error` / `service_unavailable` 表示事务已经回滚，换新的 request_id；400 / 401 / 403 / 429 按错误码表处理。其他所有情况（超时、发出后断开、非 JSON、没有外壳的 5xx、网关自己返回的 502/503/504）一律按「结果不明」处理，进入 CONFIRMING，**复用同一个 request_id**。极端情况：服务端 COMMIT 成功但确认包丢了，返回了带外壳的 503，客户端换了新 id 再点，会得到 `already_checked_in` 并显示「今日已签到」，不会多发分。错误码表下面会补一句这条规则 | 澄清（不改契约字段） |
| A3 | 超时后查状态看到已签，分不清是不是本机这次签的 | 建议把确认手段从「GET 状态」换成「**用同一个 request_id 重发一次 POST /checkin**」，契约本来就支持：返回 `ok` 表示这次点击的签到已生效（原请求已提交就原样重放，没提交就现在完成，服务端幂等，不会多发分），按成功处理，弹「签到成功 +N」，N 取 `points_total`；返回 `already_checked_in` 表示是别处签的，显示「今日已签到」，不弹 toast；重发也失败或也不明，就转 FAILED，保留 request_id。服务端 5 秒处理超时比客户端 10 秒短，重发时原请求一定已经结束，不会两个请求同时在跑。这样做会多占 1 次限流额度，可以忽略。行为上的变化是「确认中未签」变成「确认时顺带完成签到」，用户本来就点了签到，这符合他的意图；但 04 交互说明第 52、186、199 行写的是「查一次状态」，措辞要由体验设计师确认后改。体验设计师不同意的话，退回你现在的做法（GET 状态），文案改成「今日已签到」，不弹 +N | 澄清（不改契约字段；交互说明措辞交体验设计师确认） |
| A4 | 第 7 天之后「明天 +N」挂在哪 | `tomorrow_points_preview` 在任何状态下都有效：第 7 天已签时它就是下一周期第 1 天的值（v1 是 10）；未签时按「今天签了、明天继续签」计算。服务端实现（service.go:277-278）和这个口径一致。注意它按**今天生效的规则**计算，如果明天切换规则版本，实际得分以明天为准。挂在哪个位置、文案怎么写是交互问题，不归我管，找体验设计师；从契约角度看，你说的「按钮下方一行」完全可以，不需要新字段 | 澄清（不改契约字段） |
| A5 | 登录和 token 从哪来 | 本服务不解析 token（契约「鉴权」）：客户端只需要在请求里带 `Authorization: Bearer <token>`，网关校验通过后注入 `X-User-Id` / `X-User-Status`。token 由 App 的账号模块提供，签到需求只依赖你定义的 `SessionManager`（`isLoggedIn`、`token()`、`onUnauthorized()`、登录结果 Flow）接口，这个边界我认可。release 包**绝不能**带 `X-User-*`；`DebugHeaderInterceptor` 只在 debug 编译，这个做法正确。项目里还没有登录模块，这属于范围缺口：登录模块谁做、什么时候有，不归我管，找产品经理，由总控升级给用户决定；在那之前用 fake `SessionManager` 联调本地服务 | 澄清（不改契约字段；登录模块归属交总控） |
| A6 | 429 的 `Retry-After` 和「按钮立即恢复」冲突 | 按交互说明来：按钮立即恢复，`Retry-After` 不强制客户端冷却。10 次/分钟是防刷线，正常用户触发不到（同一天第 2 次起就是 `already_checked_in`，在 UI 上按钮已经置灰了）。客户端可以选择在 `Retry-After` 秒内对再次出现的 429 不重复弹 toast，这是实现细节，不需要改契约 | 澄清（不改契约字段） |
| A7 | `checkin_result.timeout` 的口径 | 契约角度的建议（最终口径由产品经理写进 PRD 埋点表）：每次有效点击恰好报一条，在**终态**时报；`latency_ms` 从点击到终态，包含确认阶段。按 A3 的做法：确认时拿到 `ok` → `success`，拿到 `already_checked_in` → `already`，确认后仍然不明 → `timeout`；10 秒超时本身不单独报。另外加一个参数 `confirmed`（bool，表示是不是经过确认阶段得出的结果），方便算「超时但实际成功」的比例。这是客户端埋点参数，不是接口字段 | 澄清（不改接口契约；埋点口径交产品经理确认） |
| A8 | 拦截器注入 `X-Request-Id` 和「重试复用」冲突 | 你说得对，是我在 05「Android 实现要点」里写得不准确。改成：拦截器只负责注入鉴权；`X-Request-Id` 由状态机生成，签到接口用 `@Header` 显式传入。header 名、格式、语义都不变。补一个提醒：OkHttp 的 `retryOnConnectionFailure` 透明重试复用的是同一个 `Request` 对象，header 不变，服务端幂等，所以是安全的；**不要**在 network interceptor 里重新生成这个 header。05 方案会同步改这一句措辞 | 澄清（不改契约字段） |
| B1 | 后端偏离：`UserTx` 新增 `LedgerByBiz(bizType, bizID)` | 接受。这是内部存储接口，不是 HTTP 契约；05 第 4、5 步本来就要求返回当天的发放明细，是我的接口草案漏了取数方法。实现检查：memory 合并「已提交 + 事务内缓冲区」并按 id 倒序；PG 在同一事务里按 `user_id, biz_type, biz_id` 查询，命中 `uq_ledger_biz` 前缀索引，按 `id DESC` 排序，奖励那条在上面，和契约示例一致。05 方案的存储接口草案会补上这个方法 | 澄清（不改契约字段） |
| B2 | 后端偏离：`/metrics` 未做 | 接受延后，按 P-07 在 08 前补，或者合并进 SRE 的 OTel 接入 | 澄清（不改契约字段） |

另外从这次审查里补两条澄清（都不改字段）：① 签到判日的取时点是「拿到账户行锁时的服务端北京时间」（配合 P-01），和 D5「以服务端时间为准」一致；② `X-Request-Id` 大小写不敏感，服务端统一存小写。

**是否需要改契约：否。** 没有任何一条需要回到「技术方案（接口契约锁定）」拍板节点。

## 遗留与补测

**本阶段修复（07 之前）**
1. P-01：把 `today` / `rule` 移进事务闭包，补跨零点乱序单测（后端工程师）。
2. P-10：补大写 request id、503 外壳的用例（后端工程师）。
3. 我这边：把 05 方案的三处措辞同步更新：存储接口补 `LedgerByBiz`、Android 要点里 `X-Request-Id` 不由拦截器注入、错误码表补「没有外壳 = 结果不明」，以及 P-06 的对账 SQL。只改说明和 SQL 口径，不动锁定字段。改 05 是改上游产物，由总控确认后执行。

**补测（需要 Go / PG 环境，本机都没有；装软件、开 Docker 都要用户确认后才执行）**
1. 在 `golang:1.27` 或有 Go 1.26+ 的 CI 里，到 server/ 目录下逐条执行：`gofmt -l .`（应该没有输出）、`go vet ./...`、`go test ./... -race -count=1`、`go build ./cmd/server`。任何一条失败，都以编译器为准，回到本 Review 重新判断。
2. P-02 / P-04：`go get` pgx、`go mod tidy`、在 PG 18 上执行 `migrations/0001_init.up.sql`，跑 `go test -tags pg ./...`（含并发 100、同 id 并发重放、拿锁超时 503）、`go build -tags pg ./cmd/server`，最后跑 `scripts/reconcile.sql`，结果应该为空。这一项是 08 上线前的阻断条件。
3. P-03：08 压测时看 status 接口每次请求的 SQL 次数和 PG QPS；如果 P-03 没修，按「最多 8 次 SQL」重新核算容量。
4. P-05 / P-06：PG 补测时构造「同一用户先 BEGIN 后拿锁」的时序，确认流水排序和 C2 / C4 不误报。

**交给其他角色**
- 体验设计师：A3（确认中改成同 id 重发）、A4（「明天 +N」的位置和文案）。
- 产品经理：A7（`checkin_result` 口径，加 `confirmed` 参数）；A5 登录模块归属，由总控升级给用户。
- 测试专家：07 用例加上 A2 的「结果不明」矩阵（发出后断开、502 HTML、非 JSON 503）、A3 的重发确认、P-01 跨零点乱序、大写 request id。
- SRE 与安全工程师：提供 Go / PG 补测环境；P-07 的指标口径；网关剥掉 `X-User-*` 仍然是 08 的阻断项。

**经验条目（供复盘回流技能包）**
- 踩坑：「今天」这类判定输入，在加锁串行化的事务里必须在**拿到锁之后**再算，否则锁只保证了写入串行，没保证判定依据最新。以后的方案模板在事务流程里要显式写出「取时点」。
- 踩坑：PG 的 `now()` 是事务开始时间，在行锁串行化的场景下，它不代表写入顺序；需要单调顺序时用拿到锁后的 `clock_timestamp()`，或者直接按 identity 排序。对账 SQL 不要按 `created_at` 推导业务日期，要关联业务表的日期字段。
- 更好的做法：没有编译器时，静态审查按「import 和未用变量 → 跨文件签名 → 接口实现 → build tag 互斥 → 测试期望值手算」的固定顺序过，比通读更不容易漏；但结论只能写「静态未发现」，不能写「通过」。
- 更好的做法：客户端「结果不明」的确认手段，优先用同一个幂等键重放写请求，而不是查读接口，这样能区分「本次生效」和「别处已做」。
