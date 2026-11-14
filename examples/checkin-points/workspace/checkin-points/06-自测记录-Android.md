<!-- template: 07-mr-selftest | 负责：各端工程师 | 阶段：06 开发联调 -->
# 合并请求与自测记录：checkin-points（App 每日签到 + 积分）· Android

> **状态声明：本文是实现说明 + 静态走查。android/ 未建、未写任何代码、未编译、未上机。** 下文所有「通过」只表示「设计和契约对得上」，不表示功能可用。代码片段是计划中的实现，没有落盘，没有编译过。

## 引用 <!-- 必填 -->
- /tmp/ra-e2e/app/workspace/checkin-points/05-技术方案.md：接口契约（已锁定）、A1–A6 任务、Android 实现要点、超时约定
- /tmp/ra-e2e/app/workspace/checkin-points/04-交互说明.md：状态机、首页卡片 11 态、积分页状态、文案、可访问性
- /tmp/ra-e2e/app/workspace/checkin-points/04-视觉标注.md：Token、组件清单、走查清单
- /tmp/ra-e2e/app/workspace/checkin-points/02-PRD.md：US-01–US-11、R1–R10、「异常态与边界」、埋点表
- /tmp/ra-e2e/app/README.md：Android Kotlin + Compose，android/ 未建
- 没有知识库，没有以前的结论可引用。

## 项目现状 <!-- 必填 -->
- 探测依据：05 技术方案已于 2026-11-14 探测，本阶段复核结论一致：仓库里**没有 android/**，没有 build.gradle(.kts)、libs.versions.toml、Manifest。没有存量代码，没有「暂缓」技术（RxJava、XML 布局）需要维护。
- 按任务要求，本期不建 Android 工程，所以无法按项目版本核对 API。下面所有版本都是计划值，**未核实最新文档**：Kotlin 2.4.x（05 查到最新 2.4.21）、AGP、Compose BOM、Retrofit / OkHttp / kotlinx.serialization / Paging 3 / Hilt / DataStore。建工程时按 https://developer.android.com/jetpack/compose/bom 和各库 release 页取当前稳定版，并按 AGP 兼容矩阵对齐 Kotlin。
- 没有登录模块、没有设计系统、没有主题：`MaterialTheme`、`extendedColors.success`、`spacing.*` 要在建工程时新建（放 `core-ui`）。

## 改动文件 <!-- 必填 -->
全部为「**计划，未落盘**」。模块和包名是建议，建工程时可调整，但分层不变。

模块：`:app`（Application、Hilt 入口、导航、BuildConfig）、`:core-ui`（主题、`spacing`、`extendedColors`、`Skeleton`、`EmptyState/ErrorState`）、`:core-network`（OkHttp、Json、鉴权拦截器）、`:feature-checkin`（本需求，包名 `com.demoapp.checkin`）。

| 文件（计划，未落盘） | 改动说明 |
|---|---|
| android/gradle/libs.versions.toml、settings.gradle.kts、build.gradle.kts | 建工程；`debug` 才有 `USE_FAKE_CHECKIN` 开关，release 写死 false |
| android/app/src/main/.../DemoApp.kt、MainActivity.kt、nav/AppNavHost.kt | Hilt 入口；路由：首页、积分页（参数 `source`）、登录页（外部提供，本需求只调用） |
| core-ui/.../theme/DemoTheme.kt、Spacing.kt、ExtendedColors.kt | M3 主题、`spacing.*`、`extendedColors.success`（不写裸值） |
| core-ui/.../Skeleton.kt、EmptyState.kt、ErrorState.kt | 通用骨架、空态、失败态 |
| core-network/.../NetworkModule.kt | OkHttp（默认 callTimeout 10s）、Json（`ignoreUnknownKeys=true`）、Retrofit |
| core-network/.../AuthInterceptor.kt | 注入 `Authorization: Bearer`；收到 401 回调 `SessionManager.onUnauthorized()`。**不发送 X-User-Id / X-User-Status**（debug 联调本地服务时由 `DebugHeaderInterceptor` 带，release 不编译） |
| checkin/data/remote/dto/ApiEnvelope.kt、CheckinStatusDto.kt、CheckinResultDto.kt、LedgerItemDto.kt、BalanceDto.kt、LedgerPageDto.kt | DTO，字段严格对应 05 契约 |
| checkin/data/remote/CheckinApi.kt | Retrofit 接口，4 个业务接口 |
| checkin/data/remote/ApiCallMapper.kt | `Response<ApiEnvelope<T>>` / 异常 → `ApiResult`（HTTP 码 + 业务码 + `Retry-After`） |
| checkin/data/CheckinRepository.kt（接口）、RemoteCheckinRepository.kt、FakeCheckinRepository.kt | 真实实现 / mock 实现，Hilt 按 flag 选 |
| checkin/data/FakeCheckinApi.kt | mock 放在 Api 层，错误映射也能被覆盖到（见「mock 方案」） |
| checkin/data/local/CheckinCache.kt | DataStore 缓存：状态、余额、流水首页、待确认 request_id |
| checkin/data/LedgerPagingSource.kt | `PagingSource<String, LedgerItem>`，游标分页 |
| checkin/domain/model/*.kt、Mappers.kt | 领域模型（枚举带 `UNKNOWN`）、DTO→领域映射 |
| checkin/domain/CheckinCoordinator.kt | 单例、`@ApplicationScope`，签到状态机 + request_id 生命周期 + 跨零点刷新判断 |
| checkin/analytics/CheckinAnalytics.kt | 神策埋点封装（接口 + 实现），6 个客户端事件 |
| checkin/ui/CheckinViewModel.kt、PointsViewModel.kt | 薄 ViewModel，只做 State 投影和事件转发 |
| checkin/ui/component/CheckinCard.kt、CheckinPanel.kt、CheckinDayRow.kt、CheckinButton.kt、PointsBalance.kt、LedgerRow.kt、LedgerFooter.kt | 视觉标注里的组件；`CheckinButton` 首页和积分页共用 |
| checkin/ui/HomeCheckinCardEntry.kt、PointsScreen.kt | 首页入口、积分页 |
| checkin/ui/strings（res/values/strings_checkin.xml） | 文案集中放资源，逐字对 PRD |
| 单元测试 / Compose UI 测试 / androidTest | 见「补测清单」，**计划** |

## 实现说明 <!-- 必填 -->

### 1. 分层与依赖方向
`ui (Compose + 薄 ViewModel)` → `domain (CheckinCoordinator, 模型)` → `data (CheckinRepository → CheckinApi / DataStore / PagingSource)`。首页和积分页共用同一个 `CheckinCoordinator` 单例和同一个 `CheckinRepository`，满足「两处入口共用一份状态」。

**为什么把状态机放在单例 Coordinator，而不是放在 ViewModel：**
1. 交互说明规定「请求中返回不取消请求，结果回来后页面已销毁只刷新缓存、不弹 toast」。如果状态机在 `viewModelScope` 里，退出页面会取消协程，请求已发出但结果丢了。放在 `@ApplicationScope` 里不会被取消。
2. 首页点了签到、请求中跳到积分页，积分页的按钮也必须是 loading。两个 ViewModel 各一份状态做不到。

### 2. 数据层：DTO（严格对应 05 契约）
`Json { ignoreUnknownKeys = true }`（契约要求）。枚举字段（`streak_state`、`account_status`、`type`）在 DTO 里保持 `String`，映射到领域层再转枚举并带 `UNKNOWN`，避免服务端新增枚举值时整个解析失败。可空字段按契约：`data`、`next_cursor`、`updated_at`。

```kotlin
// 计划，未落盘，未编译
@Serializable
data class ApiEnvelope<T>(val code: String, val message: String = "", val data: T? = null)
// message 只写日志，不展示（契约）

@Serializable
data class CheckinStatusDto(
    @SerialName("server_date") val serverDate: String,              // yyyy-MM-dd，北京时间
    val timezone: String,                                            // "Asia/Shanghai"
    @SerialName("checked_today") val checkedToday: Boolean,
    @SerialName("can_checkin") val canCheckin: Boolean,
    @SerialName("account_status") val accountStatus: String,         // active | restricted
    @SerialName("streak_state") val streakState: String,             // NONE | ACTIVE | BROKEN
    @SerialName("streak_days") val streakDays: Int,
    @SerialName("cycle_day") val cycleDay: Int,                      // 1..7
    @SerialName("today_points_preview") val todayPointsPreview: Int,
    @SerialName("tomorrow_points_preview") val tomorrowPointsPreview: Int,
    @SerialName("rule_version") val ruleVersion: String,
    val cycle: List<CycleCellDto>,                                   // 7 个
)

@Serializable
data class CycleCellDto(
    val day: Int,
    @SerialName("points_total") val pointsTotal: Int,
    @SerialName("bonus_points") val bonusPoints: Int,
    val checked: Boolean,
    @SerialName("is_today") val isToday: Boolean,
)

@Serializable
data class CheckinResultDto(                                         // ok 和 already_checked_in 结构相同
    @SerialName("checkin_date") val checkinDate: String,
    @SerialName("streak_days") val streakDays: Int,
    @SerialName("cycle_day") val cycleDay: Int,
    @SerialName("points_base") val pointsBase: Int,
    @SerialName("points_bonus") val pointsBonus: Int,
    @SerialName("points_total") val pointsTotal: Int,                // toast 的 N
    val balance: Long,                                               // int64
    @SerialName("rule_version") val ruleVersion: String,
    val ledger: List<LedgerItemDto>,                                 // 1 或 2 条
)

@Serializable
data class LedgerItemDto(
    val id: String,                                                  // string，不是数字
    val type: String,
    val amount: Long,                                                // 有符号
    @SerialName("balance_after") val balanceAfter: Long,
    @SerialName("biz_type") val bizType: String,
    @SerialName("biz_id") val bizId: String,                         // string
    val remark: String,
    @SerialName("created_at") val createdAt: String,                 // RFC 3339 UTC
)

@Serializable
data class BalanceDto(val balance: Long, @SerialName("updated_at") val updatedAt: String? = null)

@Serializable
data class LedgerPageDto(
    val items: List<LedgerItemDto>,
    @SerialName("has_more") val hasMore: Boolean,
    @SerialName("next_cursor") val nextCursor: String? = null,
)
```

Retrofit 接口（base URL `…/api/v1/`，主机待定）：

```kotlin
interface CheckinApi {
    @GET("checkin/status") suspend fun status(): Response<ApiEnvelope<CheckinStatusDto>>

    @POST("checkin")                                                  // 单独的 Retrofit 实例，callTimeout = 10s
    suspend fun checkin(
        @Header("X-Request-Id") requestId: String,                    // UUID，36 位
        @Body body: JsonObject = JsonObject(emptyMap()),              // 契约：Body = {}，不传日期
    ): Response<ApiEnvelope<CheckinResultDto>>

    @GET("points/balance") suspend fun balance(): Response<ApiEnvelope<BalanceDto>>

    @GET("points/ledger")
    suspend fun ledger(
        @Query("cursor") cursor: String? = null,                      // 不透明，原样回传，不解码
        @Query("limit") limit: Int = 20,                              // 1..50
    ): Response<ApiEnvelope<LedgerPageDto>>
}
```

**与 05 的一处细节差异（不是改契约）：** 05 写「拦截器注入 `X-Request-Id`」。这里改成签到接口显式传 `@Header`，因为 request_id 的生命周期（点击时生成、仅确认后重试复用）归状态机管，拦截器每次生成会破坏复用。header 名、格式、语义与契约一致。

`ApiCallMapper` 把响应统一成：

```kotlin
sealed interface ApiResult<out T> {
    data class Ok<T>(val data: T, val code: String) : ApiResult<T>          // 200，code = ok | already_checked_in
    data class Http(val status: Int, val code: String?, val retryAfterSec: Int?) : ApiResult<Nothing>
    data object NotSent : ApiResult<Nothing>      // UnknownHost / ConnectException / 无网：确定没发出去
    data object Ambiguous : ApiResult<Nothing>    // callTimeout（InterruptedIOException）、发出后连接中断、无法解析的 502/504：不知道服务端有没有提交
}
```
非 2xx 时解析 `errorBody()` 里的外壳取业务码；解析失败 `code=null`，只按 HTTP 状态处理。`401` 在 `AuthInterceptor` 里统一回调，不在每个调用点重复写。

### 3. Repository
```kotlin
interface CheckinRepository {
    val status: StateFlow<StatusState>                     // Loading / Content(CheckinStatus, fromCache) / Error(kind)
    val balance: StateFlow<Long?>                          // 签到成功用 result.balance 直接更新
    suspend fun refreshStatus(): ApiResult<CheckinStatus>
    suspend fun checkin(requestId: String): ApiResult<CheckinResult>
    suspend fun refreshBalance()
    fun ledgerPager(): Flow<PagingData<LedgerItem>>        // 带 invalidate()，签到成功后调用
    fun invalidateLedger()
}
```
- `status` 是 `StateFlow`，首页卡片和积分页签到区共同订阅；每次成功拉到就写 DataStore 缓存。
- 无网且有缓存：`Content(fromCache = true)`，积分页余额下方显示「数据可能不是最新」。
- 时间：`created_at` 用 `Instant.parse` 后 `atZone(ZoneId.of("Asia/Shanghai"))` 格式化 `yyyy-MM-dd HH:mm`，**不用设备时区**。

### 4. 签到状态机（CheckinCoordinator）
状态：

```kotlin
sealed interface SubmitState {
    data object Idle : SubmitState
    data object Submitting : SubmitState                    // 0–10s
    data object Confirming : SubmitState                    // >10s 或结果不明，自动查一次状态
    data class Success(val already: Boolean) : SubmitState  // 终态，下次点击或状态刷新时回 Idle
    data class Failed(val reason: FailReason) : SubmitState
}
enum class FailReason { SERVER, RATE_LIMITED, NO_NETWORK, TIMEOUT_UNRESOLVED, FORBIDDEN, UNAUTHORIZED, CLIENT_BUG }
sealed interface UiEvent { data class Toast(val textRes: Int, val args: List<Any> = emptyList()) : UiEvent; data object GoLogin : UiEvent }
```
按钮最终展示由 `(StatusState, SubmitState, isLoggedIn)` 三者推导，不另存一份：

| 条件 | 按钮 |
|---|---|
| 未登录 | 「签到」，点击跳登录 |
| Submitting | loading，禁用 |
| Confirming | loading +「签到结果确认中」，禁用 |
| `checked_today` 或 Success | 「今日已签到」，禁用（不是错误色） |
| `account_status != active` 或 `!can_checkin` 且未签（403） | 禁用 + 「账号状态异常，暂无法签到」（`onSurfaceVariant`） |
| 其他 | 「签到 +N」，N = `today_points_preview` |

> 按钮是否可点以 `can_checkin` 为准，`account_status` 只决定说明文案；遇到未知的 `account_status` 值按「不可签」兜底显示 403 文案。

状态转换与 request_id：

```kotlin
// 计划，未落盘，未编译
@Singleton
class CheckinCoordinator @Inject constructor(
    private val repo: CheckinRepository,
    private val session: SessionManager,
    private val network: NetworkMonitor,
    private val analytics: CheckinAnalytics,
    private val cache: CheckinCache,
    @ApplicationScope private val appScope: CoroutineScope,
    private val uptimeMs: () -> Long = SystemClock::elapsedRealtime,
) {
    private val _submit = MutableStateFlow<SubmitState>(SubmitState.Idle)
    val submit = _submit.asStateFlow()
    private val _events = MutableSharedFlow<UiEvent>(extraBufferCapacity = 1, onBufferOverflow = DROP_OLDEST) // toast 只留最新一条
    val events = _events.asSharedFlow()

    /** 只有「确认后仍未签」才会赋值，用于重试复用；任何明确响应都清空。 */
    private var retryRequestId: String? = null

    fun onCheckinClick(source: String) {
        if (_submit.value is SubmitState.Submitting || _submit.value is SubmitState.Confirming) return  // 防重复，不算一次新点击，也不上报
        val rid = retryRequestId ?: UUID.randomUUID().toString()
        analytics.checkinClick(source, rid, session.isLoggedIn)
        if (!session.isLoggedIn) { analytics.loginPrompt(source); _events.tryEmit(UiEvent.GoLogin); return }   // 登录回来只刷新，不自动签到
        if (!network.isOnline) { finish(rid, ResultKind.NO_NETWORK, null, 0L); _events.tryEmit(Toast(R.string.net_unavailable)); return } // 不发请求，按钮保持可点
        appScope.launch { submit(rid) }          // 不绑定页面生命周期：返回不取消请求
    }

    private suspend fun submit(rid: String) {
        _submit.value = SubmitState.Submitting
        val t0 = uptimeMs()
        when (val r = repo.checkin(rid)) {
            is ApiResult.Ok -> onOk(rid, r.data, already = r.code == "already_checked_in", t0)
            is ApiResult.Http -> when {
                r.status == 401                     -> { retryRequestId = null; _submit.value = Idle; finish(rid, UNAUTHORIZED, "unauthorized", t0); _events.tryEmit(GoLogin) }
                r.status == 403                     -> { retryRequestId = null; _submit.value = Failed(FORBIDDEN); finish(rid, FORBIDDEN, r.code, t0); repo.refreshStatus() }
                r.status == 429                     -> { retryRequestId = null; _submit.value = Idle; finish(rid, RATE_LIMITED, r.code, t0); toast(R.string.too_frequent) } // 按钮立即恢复；Retry-After 只记日志
                r.status == 400                     -> fail(rid, CLIENT_BUG, r.code, t0)      // invalid_request：客户端 bug，toast「签到失败，请重试」+ 上报
                r.status in 500..599 && r.code != null -> fail(rid, SERVER, r.code, t0)       // 500/503：事务已回滚，下次点击换新 id
                else                                -> confirm(rid, t0)                       // 502/504/无法解析：不确定，当歧义处理（见问题 2）
            }
            ApiResult.NotSent  -> { _submit.value = Idle; finish(rid, NO_NETWORK, null, t0); toast(R.string.net_unavailable) }
            ApiResult.Ambiguous -> confirm(rid, t0)
        }
    }

    private suspend fun onOk(rid: String, d: CheckinResult, already: Boolean, t0: Long) {
        retryRequestId = null; cache.clearPending()
        repo.applyCheckinResult(d)                // 更新 balance 和 status 缓存；用 result.checkin_date / cycle_day，不用本地时间
        repo.invalidateLedger()                   // Paging refresh，顶部出现新流水
        repo.refreshStatus()                      // 拉最新格子（cycle、streak_state）
        _submit.value = SubmitState.Success(already)
        if (!already) toast(R.string.checkin_success, d.pointsTotal)   // already：不弹 toast，不报错
        finish(rid, if (already) ALREADY else SUCCESS, null, t0, d)
    }

    private suspend fun confirm(rid: String, t0: Long) {
        _submit.value = SubmitState.Confirming                       // 「签到结果确认中」
        cache.savePending(rid)                                       // 防进程被杀后丢 id
        when (val s = repo.refreshStatus()) {                        // 只查一次，timeout 10s
            is ApiResult.Ok -> if (s.data.checkedToday) {
                retryRequestId = null; cache.clearPending()
                repo.invalidateLedger()
                _submit.value = SubmitState.Success(already = false)
                toast(R.string.checkin_success, s.data.todayPointsPreview)   // 已签时 preview = 今天实际拿到的合计（契约）
                finish(rid, SUCCESS, null, t0)                       // 见问题 3：无法区分是不是本机这次签的
            } else unresolved(rid, t0)
            else -> unresolved(rid, t0)                              // 查询也失败 → 同样按「签到失败，请重试」
        }
    }

    private fun unresolved(rid: String, t0: Long) {
        retryRequestId = rid                                         // 重试复用同一个 request_id，服务端幂等
        _submit.value = SubmitState.Failed(TIMEOUT_UNRESOLVED)
        toast(R.string.checkin_failed); finish(rid, TIMEOUT, null, t0)
    }

    private fun fail(rid: String, reason: FailReason, code: String?, t0: Long) {
        retryRequestId = null                                        // 明确失败：新点击换新 id
        _submit.value = SubmitState.Failed(reason)
        toast(R.string.checkin_failed); finish(rid, FAIL, code, t0)
    }
}
```

要点汇总：
- **request_id**：点击时 `UUID.randomUUID().toString()`（36 位，满足契约）。仅「超时/不明 → 确认后仍未签」这条路径把 id 存进 `retryRequestId`，下一次点击复用；其余所有明确结果（成功、already、401、403、429、400、5xx）都清空，下次点击换新 id。`retryRequestId` 同时写 DataStore（`savePending`），进程被杀后冷启动时：状态显示已签就清掉，未签就保留，下一次点击仍复用。契约支持跨零点用同一 id 重放（D4）。
- **超时分层**：签到走独立 Retrofit，`callTimeout(10s)`；`InterruptedIOException`（含 `SocketTimeoutException`）→ `Ambiguous`。状态查询也设 10s，不重试。服务端 5s/8s 一定先放弃，所以确认时查到的是最终结果（契约「超时约定」）。
- **NotSent 与 Ambiguous 的区分**：`UnknownHostException`、`ConnectException`（连接建立前失败）确定没发出去，按「无网」；其余 IO 异常（发送后断开、读响应时失败）不知道服务端是否提交，走确认流程，避免误导用户重复签到。
- **并发**：`SubmitState` 是 `StateFlow`，`onCheckinClick` 先判断状态再启动协程；为避免同一帧双击的竞态，实际代码用 `compareAndSet(Idle/Success/Failed → Submitting)` 做原子占位（上面片段为了可读省略）。
- **401**：`AuthInterceptor` 统一触发 `SessionManager.onUnauthorized()`（清登录态、跳登录）；登录成功回原页面后调用 `refreshStatus()`，**不自动签到**。状态/余额/流水接口收到 401 同样跳登录（积分页：不展示余额和流水）。
- **toast**：只用一个 `SharedFlow(replay=0, DROP_OLDEST)`，同一时刻最多一条，后来的替换前一条；页面已销毁时没有收集者，事件直接丢弃，只更新缓存，符合「不弹 toast」。
- **成功反馈**：toast「签到成功 +N 积分」（N = `points_total`）；按钮 200ms 淡入淡出；今日格子勾 300ms 缩放；第 3、7 天脉冲 400ms；余额滚动 600ms，数值用 `result.balance`（重放时是当前余额）；触感见下。动画统一用 `LocalReduceMotion`（读 `Settings.Global.ANIMATOR_DURATION_SCALE == 0`）判断，关闭时直接显示结果。触感先用 `View.performHapticFeedback(HapticFeedbackConstants.CONFIRM)`（API 30+，低版本降级为 `VIRTUAL_KEY`）；Compose 的 `HapticFeedbackType.ConfirmTap` 在哪个版本可用**未核实最新文档**，建工程后查官方文档再决定是否替换。

### 5. 跨零点 onResume 刷新（US-10）
- `Lifecycle.Event.ON_RESUME`（首页与积分页的 `repeatOnLifecycle(RESUMED)`）调用 `coordinator.onResume()`：
  1. 当前 `SubmitState` 是 Submitting/Confirming 时不刷新（避免打断）。
  2. 条件刷新：`cachedStatus.serverDate != LocalDate.now(ZoneId.of("Asia/Shanghai"))`，**或**距上次成功拉取 > 5 分钟，**或**没有缓存。满足任一条件就 `refreshStatus()`，且两次刷新间隔至少 30 秒（防设备时间错误时每次 resume 都打接口）。
  3. 刷新期间只有签到区显示局部骨架（`StatusState.Refreshing`，保留旧内容的尺寸），不整页闪。
- 本地时间**只用来决定要不要去拉**，展示内容（按钮、格子、文案）一律取服务端返回值，符合 R1「设备时间不参与判定」。这个触发条件契约里没写透，见问题 1。

### 6. 流水 Paging（游标）
```kotlin
// 计划，未落盘，未编译
class LedgerPagingSource(private val api: CheckinApi) : PagingSource<String, LedgerItem>() {
    override suspend fun load(params: LoadParams<String>): LoadResult<String, LedgerItem> {
        val r = ApiCallMapper.call { api.ledger(cursor = params.key, limit = 20) }
        return when (r) {
            is ApiResult.Ok -> LoadResult.Page(
                data = r.data.items.map(LedgerItemDto::toDomain),
                prevKey = null,
                nextKey = if (r.data.hasMore) r.data.nextCursor else null,   // 游标原样回传
            )
            is ApiResult.Http -> if (r.status == 400 && r.code == "invalid_cursor") LoadResult.Invalid()  // 从第一页重新拉
                                 else LoadResult.Error(LedgerException(r))                                // 401 已在拦截器处理
            else -> LoadResult.Error(LedgerException(r))
        }
    }
    override fun getRefreshKey(state: PagingState<String, LedgerItem>): String? = null  // 刷新总是从首页（游标不可自己构造）
}
```
- `PagingConfig(pageSize = 20, initialLoadSize = 20, prefetchDistance = 5, enablePlaceholders = false)`。**必须显式设 `initialLoadSize = 20`**：默认是 `pageSize × 3 = 60`，会超过契约 `limit` 上限 50 导致 400，也不符合「每页 20 条」。
- 滑到倒数第 5 条触发翻页 = `prefetchDistance = 5`。
- 底部状态由 `loadState.append` 映射：`Loading` → 圈；`Error` → 「加载失败，点击重试」（`retry()`，已加载数据保留，不回顶部）；`endOfPaginationReached` → 「没有更多了」。
- 空态：`refresh is NotLoading && append.endOfPaginationReached && itemCount == 0` → 「还没有积分记录」+「去签到赚积分」（点击：`LazyListState.animateScrollToItem` 到签到区 + `FocusRequester` 给签到按钮）。
- 首屏失败：`refresh is Error && itemCount == 0` → 区块内「加载失败，点击重试」（部分失败只重试流水）。
- 签到成功：`invalidateLedger()` 后 Paging 重新加载首页；`LazyPagingItems` 在 refresh 期间保留旧列表，不显示整页骨架；列表项 `key = { it.id }` + `Modifier.animateItem()` 实现新记录淡入。同一事务的两条流水 `created_at` 相同，按 `id DESC` 排，奖励条在上，与契约 `ledger[0]` 顺序一致。
- 流水行：类型名映射 `CHECKIN_BASE` →「每日签到」、`CHECKIN_STREAK_BONUS` →「连续签到奖励」；未知类型 → `remark`，空则「积分变动」；`amount > 0` 显示 `+N` + `extendedColors.success`，`amount < 0` 显示 `-N` + `onSurface`。行合并为一个无障碍节点：「每日签到，增加 10 积分，2026-11-14 09:12」。
- 分页进出埋点 `points_ledger_load`：每页加载完成或失败各报一次。

### 7. Compose 结构
```
HomeScreen
 └─ CheckinCard(state: CheckinCardUi, onButton, onCardClick)         // 11 态，由 CheckinCardUiMapper 从 (status, submit, login, network) 推导
     ├─ Skeleton | ErrorInline(「加载失败，点击重试」) | NoNetInline
     └─ Row { Icon(redeem / check) ; Column { 「每日签到」; subtitle } ; CheckinButton }

PointsScreen(source)
 ├─ TopAppBar(「我的积分」)
 └─ PullToRefreshBox → LazyColumn
     ├─ item PointsBalance(balance, fromCache)                       // 千分位、displaySmall、tabular nums、600ms 滚动
     ├─ item CheckinPanel
     │    ├─ 标题「每日签到」+ 右上「每日 0 点（北京时间）刷新」（常驻）
     │    ├─ 连签文案（NONE：「每天签到领积分」；BROKEN：「连签已中断，今天重新开始」；ACTIVE：「已连续签到 X 天」）
     │    ├─ CheckinDayRow(cycle: List<CycleCell>)                   // 字体缩放 ≥1.3 → 两行 4+3（用 LocalDensity.fontScale 判断）
     │    └─ CheckinButton（与首页同一个组件）
     ├─ item 「积分明细」标题
     ├─ items(ledger, key = id) { LedgerRow }
     └─ item LedgerFooter(loading | error | end)
```
- 副标题优先级：403 说明 > `streak_state`（NONE / BROKEN / ACTIVE）。`streak_days` 来自服务端，不用本地加 1。
- `CheckinDayCell` 的 `semantics(mergeDescendants = true)` + `contentDescription` 按交互说明三种朗读模板；格子不可点（无 `clickable`）。
- 「明天 +N」（P1）：已签时，在按钮下方显示一行说明「明天签到 +`tomorrow_points_preview`」。原因见问题 4。
- 状态收集用 `collectAsStateWithLifecycle()`。登录跳转返回后把焦点交还签到按钮（`FocusRequester`，导航结果回调）。
- 文案全部在 `strings_checkin.xml`，不在组件里写字符串字面量，便于对 PRD 逐字核对。颜色、字号、间距走 `MaterialTheme` / `spacing` / `extendedColors`，不写裸值。

### 8. 缓存与无网（P1）
- `CheckinCache`（DataStore）存最近一次的状态 JSON、余额、流水首页 JSON、待确认 request_id。进入页面先读缓存立即显示（`fromCache=true`），再拉网络。
- 无网判定：`NetworkMonitor`（`ConnectivityManager.registerDefaultNetworkCallback`，`NET_CAPABILITY_VALIDATED`）。系统说「有网」但请求失败时，以请求结果为准（`NotSent` / `Ambiguous`）。
- 无网且无缓存：首页卡片「网络不可用，请检查网络后重试」；积分页整页 ErrorState +「点击重试」。有缓存：显示缓存，余额区「数据可能不是最新」；点签到：不发请求，toast，按钮保持可点。网络恢复事件**不**触发自动签到。

### 9. 埋点调用点（PRD「埋点与指标」）
`CheckinAnalytics` 接口 + 神策实现（建工程时接 SDK；公共属性 `user_id`/`device_id`/`app_version`/`network_type`/`event_time` 由 SDK 统一带）。服务端事件 `checkin_success` / `points_grant` 不在客户端报。

| 事件 | 调用点 | 参数来源 |
|---|---|---|
| `checkin_entry_expose` | 卡片 / 签到区首次进入可见区（`LaunchedEffect` + `onGloballyPositioned` 可见性 ≥ 50%）；单次页面停留（一个 composition 生命周期）只报一次，用 `rememberSaveable` 标记 | `source` = home / points_page，`is_login`，`today_checked`，`streak_days`（来自 status，未加载完成不报） |
| `checkin_click` | `onCheckinClick` 通过防重判断之后（Submitting/Confirming 中的点击不报） | `source`、`request_id`、`is_login` |
| `checkin_result` | `finish(...)`：每次点击恰好一条 | `request_id`、`result`（success / already / fail / timeout / no_network / unauthorized / forbidden / rate_limited）、`error_code`（服务端业务码，无则空）、`latency_ms`（`uptimeMs` 差值，无网不发请求时为 0） |
| `points_page_view` | 进入积分页（`ON_START` 一次，旋转屏不重复） | `source`、`balance`（已有缓存或拉到后；没有则不报该字段） |
| `points_ledger_load` | `LedgerPagingSource.load` 完成 / 失败 | `page_index`（从 0，用 key→序号映射）、`item_count`、`result`、`latency_ms` |
| `login_prompt_from_checkin` | 未登录点签到时 `source`；登录页返回后补报 `login_result` = success / cancel | 登录结果由登录页回调提供（登录页不在本需求范围，见问题 5） |

`checkin_result` 与状态机的对应：Ok→success；already→already；5xx / 400 → fail；确认后未签或确认也失败 → timeout；NotSent / 无网 → no_network；401 → unauthorized；403 → forbidden；429 → rate_limited。`timeout` 在「最终超时」（确认阶段仍无结论）时报，确认到已签的算 success，口径见问题 7。

### 10. 接口没好时的 mock 方案（一键切换）
- **开关**：`android/app/build.gradle.kts` 里 `debug` buildType：`buildConfigField("boolean", "USE_FAKE_CHECKIN", "true")`；`release` 固定 `false`，并在 CI 里加一条检查（grep release 配置 / lint）防止误带。再加调试菜单里的运行时开关（仅 debug，存 DataStore）和「场景选择器」。
- **注入**：Hilt `CheckinModule` 按 `BuildConfig.USE_FAKE_CHECKIN`（debug 另读运行时开关）提供 `CheckinApi`：`FakeCheckinApi` 或 Retrofit 实例。**mock 放在 Api 层而不是 Repository 层**，这样 `ApiCallMapper`、错误映射、状态机都被真实执行；`FakeCheckinRepository` 只给纯 UI 预览和截图测试用。
- **`FakeCheckinApi`** 内存里保存一个 `FakeServer`（可注入日期，默认当天北京时间），实现契约的核心规则：同一 `X-Request-Id` 重放原结果；同日换 id 返回 `already_checked_in`；`streak_days`、`cycle_day`、`10/10/20/10/10/10/40`、断签重置、第 7 天后第 8 天回周期第 1 天；流水两条同时间、`id` 递增；游标 = 自己编的 base64url `"<微秒>_<id>"`，`limit` 越界返回 400。数据量预置 60 条流水用来测翻页。
- **场景选择器**（debug 菜单，下一次请求按场景返回）：`OK`、`ALREADY_CHECKED_IN`、`UNAUTHORIZED(401)`、`FORBIDDEN(403, account_status=restricted)`、`RATE_LIMITED(429 + Retry-After: 30)`、`SERVER_ERROR(500)`、`UNAVAILABLE(503)`、`TIMEOUT_THEN_COMMITTED`（延迟 11s，实际已提交；后续 status 返回已签）、`TIMEOUT_NOT_COMMITTED`（延迟 11s，未提交）、`CONNECTION_RESET_AFTER_SEND`、`OFFLINE`（抛 `UnknownHostException`）、`BAD_GATEWAY_HTML(502 非 JSON)`、`INVALID_CURSOR`、`CROSS_MIDNIGHT`（拨动 FakeServer 日期 +1 天）、`NEW_USER` / `BROKEN_STREAK` / `DAY7_CHECKED` / `DAY8` / `UNKNOWN_LEDGER_TYPE`（预置数据）。
- **接口联调**：切回真实实现时只改开关；debug 联调本地 Go 服务用 `DebugHeaderInterceptor` 带 `X-User-Id` / `X-User-Status`（仅 debug 编译，release 没有这个类，避免客户端伪造身份 header）。
- **契约锁定防漂移**：把 05 契约里的 3 个 JSON 示例（status、checkin result，加一个 ledger 页）原样放进 `src/test/resources/contract/`，DTO 解析单测直接读它们；后端联调时用真实响应更新这些样例并 diff。

## 自测记录 <!-- 必填 -->
**本期没有 android/ 工程：所有用例都没有执行。** 下表只列已经做的「静态走查」；要执行的用例见「补测清单」。

| 用例 | 命令 / 步骤 | 结果 |
|---|---|---|
| 编译 | `./gradlew :feature-checkin:assembleDebug` | **未执行（无工程）** |
| 单元测试 | `./gradlew testDebugUnitTest` | **未执行（无工程）** |
| Compose UI 测试 | `./gradlew connectedDebugAndroidTest` | **未执行（无工程）** |
| 实机 / 模拟器 | 无 | **未上机** |
| 契约对照走查 | 逐字段对照上文 DTO 与 05 契约 | 完成：DTO 草稿与契约一致，0 处字段偏差；见下表 |
| 状态覆盖走查 | 逐条对照 PRD「异常态与边界」16 行 + 交互说明卡片 11 态 / 积分页 / 按钮 / 流水 | 完成：设计层全部有承接；发现 8 个契约 / 交互问题，见下 |

### A. 契约对照走查
局限：DTO 是我根据契约写的，两者同源，这份走查能发现笔误和遗漏，**不能替代**用真实服务端响应做的解析测试。

| 契约对象 | 契约字段 → DTO | 结论 |
|---|---|---|
| 外壳 | `code` string、`message` string、`data` object\|null → `ApiEnvelope<T>(code, message="", data: T? = null)` | 一致；`message` 不展示 |
| `CheckinStatus`（12 个字段） | `server_date`、`timezone`、`checked_today`、`can_checkin`、`account_status`、`streak_state`、`streak_days`、`cycle_day`、`today_points_preview`、`rule_version`、`tomorrow_points_preview`、`cycle` | 12/12 有对应属性，`@SerialName` 都是 snake_case，类型 String/Boolean/Int/List 一致 |
| `CycleCell`（5） | `day`、`points_total`、`bonus_points`、`checked`、`is_today` | 5/5 一致 |
| `CheckinResult`（9） | `checkin_date`、`streak_days`、`cycle_day`、`points_base`、`points_bonus`、`points_total`、`balance`（int64 → `Long`）、`rule_version`、`ledger` | 9/9 一致；`balance` 用 `Long` |
| `LedgerItem`（8） | `id`(string)、`type`、`amount`(int64)、`balance_after`(int64)、`biz_type`、`biz_id`(string)、`remark`、`created_at` | 8/8 一致；`id`、`biz_id` 是 String；`type` 保持 String，未知值走兜底 |
| 余额 | `balance` int64、`updated_at` string\|null → `BalanceDto(Long, String? = null)` | 一致，新用户 `balance=0, updated_at=null` 能解析 |
| 流水页 | `items`、`has_more`、`next_cursor`(null) → `LedgerPageDto` | 一致；`nextKey` 在 `has_more=false` 时置 null |
| 请求 | `POST /checkin` Header `X-Request-Id`（UUID 36 位）、Body `{}`；`GET /points/ledger?cursor=&limit=`，默认 20，1–50 | 一致；`initialLoadSize` 必须显式 20，否则默认 60 会 400（已写入） |
| 枚举 | `streak_state` NONE/ACTIVE/BROKEN；`account_status` active/restricted；ledger `type` 5 个值 | 映射层带 `UNKNOWN`；`ignoreUnknownKeys = true` |
| 时间 / 时区 | `created_at` RFC 3339 UTC，展示北京时间；日期字段不转换 | 格式化用 `ZoneId.of("Asia/Shanghai")`，不依赖设备时区 |
| 错误码表（11 行） | 200 ok / already；400 invalid_request / invalid_cursor；401；403；404；405；429；500；503 | 前 9 类有明确处理；404 / 405 → 归入 `else`（上报，当「签到失败」）。**502/504 与非 JSON 响应契约没写**，见问题 2 |
| 超时约定 | 客户端 callTimeout 10s | 签到单独 Retrofit，10s；状态查询也 10s |

示例 JSON 的字段（含 3 个示例对象）人工对照了一遍，无多余或缺失键；上表「12/12」「9/9」等数字是我逐个数过的，建工程后由 `ContractFixtureTest` 实测。

### B. 状态覆盖走查

**PRD「异常态与边界」逐行**（✓ = 设计已承接；⚠ = 有疑问，见问题编号）

| # | PRD 场景 | 承接位置 | 结论 |
|---|---|---|---|
| 1 | 空态：没有流水 | `LedgerPagingSource` 空列表 + `EmptyState`；余额 0 | ✓ |
| 2 | 空态：今天未签 | 按钮「签到 +N」，N = `today_points_preview` | ✓ |
| 3 | 加载中 | `Skeleton`；按钮 Submitting loading；`append` Loading 圈 | ✓ |
| 4 | 加载失败（整页 / 下一页） | `StatusState.Error`、`refresh Error`、`append Error`，已加载保留 | ✓（部分失败区块重试按交互补充实现） |
| 5 | 签到失败 | 500/503/400 → `fail()`，toast，新 request_id | ✓ |
| 6 | 无网 | `NetworkMonitor` + `NotSent`；缓存 +「数据可能不是最新」 | ✓ |
| 7 | 未登录 / 401 | `GoLogin`，回来 `refreshStatus`，不自动签到 | ⚠ 问题 5 |
| 8 | 无权限 403 | `FORBIDDEN` → 刷新状态，按钮禁用 + 说明；余额流水可看 | ✓ |
| 9 | 超时 | `Ambiguous` → `Confirming` → 查一次状态；未签则 `retryRequestId` 复用 | ⚠ 问题 2、3 |
| 10 | 重复提交 | 请求中直接 return；`already_checked_in` 当成功、不弹 toast | ✓ |
| 11 | 并发（两台设备） | 一台 ok + toast，另一台 already，余额取 `result.balance` | ✓ |
| 12 | 限流 429 | toast，按钮恢复，不清已有状态 | ✓（Retry-After 仅记日志，见问题 6） |
| 13 | 跨天：停在页面过零点 | `onResume` 条件刷新 | ⚠ 问题 1 |
| 14 | 跨天：23:59:59 点击 | 展示取 `result.checkin_date` / `cycle_day`，不用本地时间 | ✓ |
| 15 | 时区 / 改系统时间 | 常驻副文字「每日 0 点（北京时间）刷新」；时间按 `Asia/Shanghai` 格式化；判日只靠服务端 | ✓ |
| 16 | 断签 / 规则变更 / 余额数值大 | `streak_state=BROKEN` 文案；格子取服务端 `points_total`；`NumberFormat` 千分位，不截断 | ✓ |

**交互说明：首页卡片 11 态**

| 状态 | 推导条件 | 结论 |
|---|---|---|
| 加载中 | `StatusState.Loading` 且无缓存 | ✓ 骨架，卡片不可点；10s 超时转加载失败 |
| 未签 | `!checked_today && can_checkin && ACTIVE` | ✓ |
| 新用户 | `streak_state=NONE` | ✓ 「每天签到领积分」，「签到 +10」（取 preview） |
| 断签 | `streak_state=BROKEN` | ✓ |
| 签到中 | `Submitting` | ✓ 卡片其余区域仍可点进积分页 |
| 已签 | `checked_today` 或 `Success` | ✓ |
| 确认中 | `Confirming` | ✓ |
| 未登录 | `!isLoggedIn` | ✓ 「签到」无 +N，点卡片或按钮都跳登录 |
| 403 | `!can_checkin && account_status != active` | ✓ |
| 加载失败 | `StatusState.Error` 且无缓存 | ✓ 行内文案，不弹 toast |
| 无网 | 无网且无缓存 | ✓；有缓存照常显示缓存卡片 |

**积分页**：首次加载骨架、整页失败、部分失败、无网有缓存、无网无缓存、未登录跳转 ✓；7 天格子 6 种（默认 / 今日已签 / 第 7 天全勾 / 第 8 天只勾第 1 天 / 断签全空 / 新用户）都是纯 `cycle` 数据驱动 ✓；按钮 8 态 ✓；流水 6 态 ✓（预留类型兜底，负数 `onSurface` + 「-」）。「明天 +N」见问题 4。

**视觉走查清单（六大项）**：未建主题和组件，「偏差登记」无从填，全部**待建工程后做**。

### C. 发现的契约 / 交互问题（未改任何上游文件，需要对应角色确认）
| # | 位置 | 问题 | 我的临时处理 | 建议归属 |
|---|---|---|---|---|
| 1 | 契约 `server_date`「客户端用它判断是否跨天」；PRD US-10 | 客户端要先拉状态才知道 `server_date`，所以「用 server_date 判断是否跨天」是循环的，没说 onResume 何时去拉。完全不用本地时间做触发就只能每次 resume 都拉 | 用设备时间换算的北京日期**仅作触发条件**，加 5 分钟间隔和 30 秒节流；展示仍取服务端值。设备时间被改错时只会多拉，不会错判 | 架构师 / 产品：确认可接受；或契约补充用响应 `Date` 头校准 |
| 2 | 契约错误码表、超时约定 | 只覆盖了 10s 超时。发出后连接被重置、网关返回 502/504（可能是 HTML）、响应体解析失败这几类「不知道服务端有没有提交」的情况没有定义；若按「明确失败」处理并换新 request_id，在极端时序下可能多签一次（被唯一约束挡住后变 `already`，不会多发分，但提示不对） | 一律走 CONFIRMING，不换 id | 架构师：契约补一行；交互说明补「结果不明」同超时 |
| 3 | 交互说明「超时 → 查状态已签 → 成功反馈」 | 确认阶段看到 `checked_today=true`，客户端分不清是本机这次签的，还是另一台设备签的。直接弹「签到成功 +N 积分」可能不准确；`today_points_preview` 在已签时是当天实际合计，所以 N 本身是对的 | 按交互说明弹成功 toast | 体验设计师 / 产品：是否改成「今日已签到」不弹 toast。备选做法：确认阶段用**同一个 request_id 重放 POST**，`ok` = 本机签的，`already_checked_in` = 别处签的（契约天然支持，但要改交互说明「查一次状态」的描述） |
| 4 | 交互说明「明天格子带『明天 +N』」（P1） | 周期第 7 天已签时，明天是下一周期第 1 天，7 个格子全已勾，没有格子可挂提示；其他天也没有说明挂在哪一格（格子里已有「+N」数值） | 在按钮下方单独一行文字「明天签到 +N」，N = `tomorrow_points_preview` | 体验设计师：确认位置和文案（PRD 里也没有该文案，属【设计补充】） |
| 5 | 契约鉴权、交互说明未登录 | ① 契约只说网关注入 `X-User-Id`，客户端如何拿 token、登录页的接口（登录成功 / 取消的回调）、`isLoggedIn` 的来源，本需求没有任何上游定义，项目里也没有登录模块；② 积分页「登录取消回到来源页」需要登录页回调 | 定义 `SessionManager` 接口（`isLoggedIn`、`onUnauthorized()`、登录结果 Flow），由登录模块实现；先放 fake | 架构师：确认登录模块归属和接口 |
| 6 | 契约 429 `Retry-After` vs 交互「按钮立即恢复可点」 | 按钮立即恢复，用户连点会连续 429（每分钟 10 次上限），且每次都会弹 toast | 按交互说明实现，`Retry-After` 只写日志；同一时刻 toast 只留一条所以不堆叠 | 体验设计师：是否需要用 `Retry-After` 做短暂冷却（我倾向不改，成本高收益低） |
| 7 | PRD `checkin_result.timeout`「收到签到结果或最终超时」 | 「最终超时」没写清：是请求超过 10s 的时刻，还是确认阶段仍无结论的时刻？两种口径下 success / timeout 的占比不同 | 确认到已签报 `success`，确认后仍未签或查询失败报 `timeout`，10s 超时本身不单独报 | 产品经理 / 数据运营：确认口径，写进埋点表 |
| 8 | 05 契约 vs 05「Android 实现要点」 | 实现要点写「OkHttp 拦截器负责注入 `X-Request-Id`」，与「重试复用同一 id」冲突（拦截器不知道状态机） | 签到接口显式传 `@Header`，见上 | 仅提醒，header 名和语义没变 |

### D. 补测清单（建工程后执行，**当前全部未做**）
1. **解析 / 契约**：`ContractFixtureTest` 读 05 的 3 个示例 + 真实后端响应，断言全部字段；`ignoreUnknownKeys` 多出字段不报错；未知 `streak_state` / `account_status` / ledger `type` 不崩。
2. **状态机单元测试**（`CheckinCoordinator`，Fake Repository + `TestDispatcher`，注入时钟）：Idle→Submitting→Success；`already_checked_in` 无 toast；401 跳登录且清 id；403 禁用且刷新状态；429 按钮恢复；500/503 换新 id；400 当 bug 上报；无网不发请求；`NotSent` / `Ambiguous` 区分；超时确认已签 / 未签 / 查询也失败；**未签后重试复用同一 request_id、成功后清空**；Submitting 中连点只发一次请求（`runTest` 里 `async` 并发点击 100 次）；页面销毁后结果回来不 toast；进程被杀后 pending id 恢复。
3. **跨零点**：`onResume` 的 `serverDate` 变化触发刷新；30 秒节流；Submitting 中不刷新；设备时区改成非 UTC+8（用固定 `ZoneId` 注入）判断结果不变。
4. **Paging**：首页 `limit=20`（`initialLoadSize` 生效）；倒数第 5 条预取；`invalid_cursor` 回第一页；append 失败 `retry()` 不丢数据；签到后新流水出现在顶部且不重复；`has_more=false` 显示「没有更多了」。
5. **Compose UI 测试**：首页卡片 11 态、积分页各状态、7 天格子 6 种、按钮 8 态的快照 / 断言；文案逐字对 PRD 14 条；TalkBack `contentDescription` 三种模板；字体 200% 下格子变 4+3、不出现省略号；深色模式；`ANIMATOR_DURATION_SCALE=0` 下无动画。
6. **实机用例**（至少覆盖主流品牌 × 系统版本，国内可用 WeTest / 阿里云 EMAS 云真机）：Android 8 / 10 / 13 / 14 / 15 各一台；折叠屏展开；手势导航底部不遮挡；`HapticFeedback` 在 API 30 以下降级；弱网（限速 + 丢包）下 10s 超时 → 确认中；飞行模式；前后台切换跨零点（可用调试开关拨动 FakeServer 日期）；两台设备同账号并发点击；改设备时区 / 系统时间。
7. **联调**（后端好之后）：关掉 mock 开关，对照 05 的 14 个 Go 单测场景里和客户端相关的部分跑一遍：同 request_id 重放、同日换 id、第 3 / 7 天、断签、23:59:59 跨天、401 / 403 / 429。
8. **性能 / 稳定性**：积分页滚动 Macrobenchmark；LeakCanary 看 Coordinator 单例不持有 Activity；包体积变化（新增模块仅 Compose + Paging + DataStore，预计影响小，以建工程后 `apk analyzer` 实测为准）；崩溃监控 Bugly 上报 `invalid_request` 类客户端 bug。

## 遗留与建议
- **工程未建、代码未写**：本文只是实现说明，建工程后第一件事是把「改动文件」落盘并按补测清单跑完；在那之前不能说「通过」。
- **上面 8 个问题**要在编码前由对应角色拍板，优先级：问题 2（可能影响提示正确性）> 问题 3（影响文案）> 问题 1、5（影响实现结构）> 其余。
- **灰度 / 降级**：本期契约没有客户端开关字段。建议加一个远程开关（入口显隐 `checkin_enabled`），用于上线后出问题时「客户端隐藏入口」（05 回滚策略里提到的做法）；同时要考虑**老版本客户端 + 新接口**：当前契约只做向后兼容的新增，老客户端 `ignoreUnknownKeys` 即可，但本需求是新功能，没有老版本问题；将来规则变更（如第 3 天数值）因格子数值取服务端，客户端无需发版。
- **隐私合规**：本需求不申请新权限（不做推送，不需要通知权限）。埋点里的 `device_id` 等由神策 SDK 按现有隐私政策收集，不新增个人信息项；SDK 必须在用户同意隐私政策后才初始化（项目启动流程里确认）。流水、余额缓存在 DataStore 里是账号数据，退出登录时必须清空（`SessionManager.onLogout` 钩子）。
- **版本待核实项**：Kotlin / AGP / Compose BOM / Paging / Retrofit / OkHttp / 神策 SDK 版本，触感 API，`PullToRefreshBox` 的稳定性，均**未核实最新文档**；建工程时查官方文档并在 MR 里附链接。
- **技术债提醒**：`CheckinCoordinator` 现在是签到专用；如果以后有第二个写接口（兑换），再抽通用的「幂等请求 + 结果确认」组件，与服务端「抽通用幂等表」同步做。
- **经验条目（供复盘回流技能包）**：① 「签到类幂等接口」的客户端核心是 request_id 的生命周期（仅结果不明时复用），拦截器自动注入会破坏它；② Paging 3 默认 `initialLoadSize = 3 × pageSize`，与服务端 `limit` 上限容易冲突，建工程时必须显式设；③ 请求中返回页面不应取消请求：状态机放 `@ApplicationScope` 单例，不要放 ViewModel；④ 契约里「客户端用 server_date 判断跨天」缺少触发条件，契约评审应让客户端早点介入。
