package service_test

import (
	"context"
	"fmt"
	"sync"
	"sync/atomic"
	"testing"
	"time"

	"demoapp/server/internal/civil"
	"demoapp/server/internal/clock"
	"demoapp/server/internal/rules"
	"demoapp/server/internal/service"
	"demoapp/server/internal/store"
	"demoapp/server/internal/store/memory"
)

var ridSeq int64

func rid() string { return fmt.Sprintf("rid-%d", atomic.AddInt64(&ridSeq, 1)) }

// 每次调用时间戳 +1 秒，保证 created_at 严格递增（在 memory 内部锁内调用，无需加锁）。
func counterNow() func() time.Time {
	base := time.Date(2026, 1, 1, 0, 0, 0, 0, time.UTC)
	var n int64
	return func() time.Time {
		n++
		return base.Add(time.Duration(n) * time.Second)
	}
}

type env struct {
	svc *service.Service
	clk *clock.Fixed
}

// day(d) = 2026-11-d 10:00 北京时间。
func day(d int) time.Time { return time.Date(2026, 11, d, 10, 0, 0, 0, clock.CST) }

func newEnv(t *testing.T, cfg *rules.Config) *env {
	t.Helper()
	if cfg == nil {
		cfg = rules.Default()
	}
	clk := clock.NewFixed(day(1))
	st := memory.NewWithNow(counterNow())
	return &env{svc: service.New(st, clk, cfg, nil), clk: clk}
}

func (e *env) sign(t *testing.T, user string, d int) *service.CheckinResult {
	t.Helper()
	e.clk.Set(day(d))
	res, err := e.svc.CheckIn(context.Background(), user, rid())
	if err != nil {
		t.Fatalf("CheckIn day %d: %v", d, err)
	}
	return res
}

func TestFirstCheckin(t *testing.T) {
	e := newEnv(t, nil)
	res := e.sign(t, "u1", 1)
	if res.Code != service.CodeOK || res.StreakDays != 1 || res.CycleDay != 1 {
		t.Fatalf("unexpected: %+v", res)
	}
	if res.PointsBase != 10 || res.PointsBonus != 0 || res.PointsTotal != 10 || res.Balance != 10 {
		t.Fatalf("points: %+v", res)
	}
	if res.Date.String() != "2026-11-01" || res.RuleVersion != "v1" {
		t.Fatalf("date/rule: %+v", res)
	}
	if len(res.Ledger) != 1 || res.Ledger[0].Type != store.TypeCheckinBase || res.Ledger[0].BalanceAfter != 10 {
		t.Fatalf("ledger: %+v", res.Ledger)
	}
}

func TestStreakRewardsDay3Day7Day8(t *testing.T) {
	e := newEnv(t, nil)
	wantTotal := []int{10, 10, 20, 10, 10, 10, 40, 10}
	wantCycle := []int{1, 2, 3, 4, 5, 6, 7, 1}
	var balance int64
	for i := 1; i <= 8; i++ {
		res := e.sign(t, "u1", i)
		if res.PointsTotal != wantTotal[i-1] {
			t.Errorf("day %d total=%d want %d", i, res.PointsTotal, wantTotal[i-1])
		}
		if res.CycleDay != wantCycle[i-1] || res.StreakDays != i {
			t.Errorf("day %d cycle=%d streak=%d", i, res.CycleDay, res.StreakDays)
		}
		balance += int64(wantTotal[i-1])
		if res.Balance != balance {
			t.Errorf("day %d balance=%d want %d", i, res.Balance, balance)
		}
		if i == 3 || i == 7 {
			if len(res.Ledger) != 2 || res.Ledger[0].Type != store.TypeCheckinStreakBonus || res.Ledger[1].Type != store.TypeCheckinBase {
				t.Errorf("day %d ledger order: %+v", i, res.Ledger)
			}
			if res.Ledger[0].BalanceAfter != balance {
				t.Errorf("day %d bonus balance_after=%d want %d", i, res.Ledger[0].BalanceAfter, balance)
			}
		}
	}
}

func TestBrokenStreakResets(t *testing.T) {
	e := newEnv(t, nil)
	e.sign(t, "u1", 1)
	e.sign(t, "u1", 2)
	// 第 3 天不签；第 4 天状态应为 BROKEN，签到后 streak=1、cycle=1。
	e.clk.Set(day(4))
	st, err := e.svc.Status(context.Background(), "u1", false)
	if err != nil {
		t.Fatal(err)
	}
	if st.StreakState != service.StreakBroken || st.StreakDays != 0 || st.CycleDay != 1 || !st.CanCheckin {
		t.Fatalf("status: %+v", st)
	}
	res := e.sign(t, "u1", 4)
	if res.StreakDays != 1 || res.CycleDay != 1 || res.PointsTotal != 10 || res.Balance != 30 {
		t.Fatalf("after break: %+v", res)
	}
}

func TestDuplicateSameDayNewRequestID(t *testing.T) {
	e := newEnv(t, nil)
	first := e.sign(t, "u1", 3)
	second, err := e.svc.CheckIn(context.Background(), "u1", rid())
	if err != nil {
		t.Fatal(err)
	}
	if second.Code != service.CodeAlready {
		t.Fatalf("code=%s", second.Code)
	}
	if second.Balance != first.Balance || second.PointsTotal != first.PointsTotal || len(second.Ledger) != len(first.Ledger) {
		t.Fatalf("already must echo today's record: %+v vs %+v", second, first)
	}
	bal, _, _ := e.svc.Balance(context.Background(), "u1")
	items, _, _ := e.svc.Ledger(context.Background(), "u1", nil, 50)
	if bal != 10 || len(items) != 1 {
		t.Fatalf("no extra grant: bal=%d ledger=%d", bal, len(items))
	}
}

func TestSameRequestIDReplay(t *testing.T) {
	e := newEnv(t, nil)
	e.clk.Set(day(1))
	id := rid()
	a, err := e.svc.CheckIn(context.Background(), "u1", id)
	if err != nil {
		t.Fatal(err)
	}
	b, err := e.svc.CheckIn(context.Background(), "u1", id)
	if err != nil {
		t.Fatal(err)
	}
	if a.Code != service.CodeOK || b.Code != service.CodeOK {
		t.Fatalf("replay must return ok: %s %s", a.Code, b.Code)
	}
	if len(b.Ledger) != 1 || b.Ledger[0].ID != a.Ledger[0].ID || b.Balance != 10 {
		t.Fatalf("replay differs: %+v vs %+v", a, b)
	}
}

func TestReplayAcrossMidnight(t *testing.T) {
	e := newEnv(t, nil)
	id := rid()
	e.clk.Set(time.Date(2026, 11, 1, 23, 59, 59, 999_000_000, clock.CST))
	a, err := e.svc.CheckIn(context.Background(), "u1", id)
	if err != nil {
		t.Fatal(err)
	}
	e.clk.Set(time.Date(2026, 11, 2, 0, 0, 0, 0, clock.CST))
	b, err := e.svc.CheckIn(context.Background(), "u1", id)
	if err != nil {
		t.Fatal(err)
	}
	if b.Code != service.CodeOK || b.Date.String() != "2026-11-01" || a.Date != b.Date {
		t.Fatalf("cross-midnight replay should return original day: %+v", b)
	}
	bal, _, _ := e.svc.Balance(context.Background(), "u1")
	if bal != 10 {
		t.Fatalf("balance=%d want 10 (no double grant)", bal)
	}
}

func TestMidnightBoundaryJudgesDay(t *testing.T) {
	e := newEnv(t, nil)
	e.clk.Set(time.Date(2026, 11, 1, 23, 59, 59, 999_000_000, clock.CST))
	a, _ := e.svc.CheckIn(context.Background(), "u1", rid())
	e.clk.Set(time.Date(2026, 11, 2, 0, 0, 0, 0, clock.CST))
	b, _ := e.svc.CheckIn(context.Background(), "u1", rid())
	if a == nil || b == nil {
		t.Fatal("nil result")
	}
	if a.Date.String() != "2026-11-01" || b.Date.String() != "2026-11-02" || a.Code != service.CodeOK || b.Code != service.CodeOK {
		t.Fatalf("a=%+v b=%+v", a, b)
	}
	if b.StreakDays != 2 || b.Balance != 20 {
		t.Fatalf("streak should continue across midnight: %+v", b)
	}
	// UTC 时间 16:00 = 北京时间次日 00:00：用 UTC 表示的时钟也必须按北京时间判日。
	e.clk.Set(time.Date(2026, 11, 2, 16, 0, 0, 0, time.UTC))
	c, _ := e.svc.CheckIn(context.Background(), "u1", rid())
	if c == nil || c.Date.String() != "2026-11-03" {
		t.Fatalf("UTC input must be judged in UTC+8: %+v", c)
	}
}

// gateStore 让第一个进入 WithUserTx 的调用停在「拿锁之前」，模拟请求 A 先到、后拿到锁。
type gateStore struct {
	store.Store
	armed   int32 // 1 时才拦截
	calls   int32
	entered chan struct{}
	release chan struct{}
}

func (g *gateStore) WithUserTx(ctx context.Context, userID string, fn func(tx store.UserTx) error) error {
	if atomic.LoadInt32(&g.armed) == 1 && atomic.AddInt32(&g.calls, 1) == 1 {
		close(g.entered)
		<-g.release
	}
	return g.Store.WithUserTx(ctx, userID, fn)
}

// CR P-01：A 在 23:59:59.99 到达但迟迟没拿到锁，B 在 00:00:00.01 到达并先拿到锁。
// 「今天」在拿锁后才算，所以 A 拿到锁时看到的是次日，只会得到 already_checked_in，
// 不会在次日记录之后再补写前一天的记录（否则次日的连签会被错误判成断签）。
func TestMidnightOutOfOrderLockDoesNotWriteOlderDay(t *testing.T) {
	cfg := rules.Default()
	clk := clock.NewFixed(day(1))
	g := &gateStore{Store: memory.NewWithNow(counterNow()), entered: make(chan struct{}), release: make(chan struct{})}
	svc := service.New(g, clk, cfg, nil)
	ctx := context.Background()

	for d := 1; d <= 2; d++ {
		clk.Set(day(d))
		if _, err := svc.CheckIn(ctx, "u1", rid()); err != nil {
			t.Fatalf("seed day %d: %v", d, err)
		}
	}
	atomic.StoreInt32(&g.armed, 1) // 从现在起，第一个进入的调用是 A

	clk.Set(time.Date(2026, 11, 3, 23, 59, 59, 990_000_000, clock.CST))
	type out struct {
		res *service.CheckinResult
		err error
	}
	aCh := make(chan out, 1)
	go func() {
		r, err := svc.CheckIn(ctx, "u1", rid())
		aCh <- out{r, err}
	}()
	<-g.entered // A 已进入但还没拿到锁

	clk.Set(time.Date(2026, 11, 4, 0, 0, 0, 10_000_000, clock.CST))
	b, err := svc.CheckIn(ctx, "u1", rid()) // B 先拿到锁
	if err != nil {
		t.Fatal(err)
	}
	if b.Code != service.CodeOK || b.Date.String() != "2026-11-04" {
		t.Fatalf("B: %+v", b)
	}

	close(g.release)
	a := <-aCh
	if a.err != nil {
		t.Fatal(a.err)
	}
	if a.res.Code != service.CodeAlready || a.res.Date.String() != "2026-11-04" {
		t.Fatalf("A must be judged on the day it got the lock: %+v", a.res)
	}
	bal, _, _ := svc.Balance(ctx, "u1")
	if bal != 30 { // 第 1、2 天各 10 + 第 4 天 10（第 3 天没签，第 4 天 streak=1）
		t.Fatalf("balance=%d want 30", bal)
	}
	rec, err := g.Store.GetCheckinByDate(ctx, "u1", civil.Date{Y: 2026, M: 11, D: 3})
	if err != nil || rec != nil {
		t.Fatalf("no record may be written for the older day after the newer one: rec=%+v err=%v", rec, err)
	}
}

func TestConcurrentCheckinOnlyOneSucceeds(t *testing.T) {
	e := newEnv(t, nil)
	e.clk.Set(day(5))
	const n = 100
	var wg sync.WaitGroup
	var okCount, alreadyCount, errCount int64
	start := make(chan struct{})
	for i := 0; i < n; i++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			<-start
			res, err := e.svc.CheckIn(context.Background(), "u1", rid())
			switch {
			case err != nil:
				atomic.AddInt64(&errCount, 1)
			case res.Code == service.CodeOK:
				atomic.AddInt64(&okCount, 1)
			case res.Code == service.CodeAlready:
				atomic.AddInt64(&alreadyCount, 1)
			}
		}()
	}
	close(start)
	wg.Wait()
	if okCount != 1 || alreadyCount != n-1 || errCount != 0 {
		t.Fatalf("ok=%d already=%d err=%d", okCount, alreadyCount, errCount)
	}
	bal, _, _ := e.svc.Balance(context.Background(), "u1")
	items, _, _ := e.svc.Ledger(context.Background(), "u1", nil, 50)
	if bal != 10 || len(items) != 1 {
		t.Fatalf("bal=%d ledger=%d", bal, len(items))
	}
}

func TestConcurrentSameRequestIDReplaysOneResult(t *testing.T) {
	e := newEnv(t, nil)
	e.clk.Set(day(5))
	id := rid()
	var wg sync.WaitGroup
	var bad int64
	for i := 0; i < 50; i++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			res, err := e.svc.CheckIn(context.Background(), "u1", id)
			if err != nil || res.Code != service.CodeOK || res.PointsTotal != 10 {
				atomic.AddInt64(&bad, 1)
			}
		}()
	}
	wg.Wait()
	bal, _, _ := e.svc.Balance(context.Background(), "u1")
	if bad != 0 || bal != 10 {
		t.Fatalf("bad=%d bal=%d", bad, bal)
	}
}

func TestStatusStates(t *testing.T) {
	e := newEnv(t, nil)
	ctx := context.Background()

	e.clk.Set(day(1))
	st, err := e.svc.Status(ctx, "u1", false)
	if err != nil {
		t.Fatal(err)
	}
	if st.StreakState != service.StreakNone || st.CycleDay != 1 || st.TodayPreview != 10 || st.TomorrowPreview != 10 || len(st.Cycle) != 7 {
		t.Fatalf("NONE: %+v", st)
	}

	e.sign(t, "u1", 1)
	e.sign(t, "u1", 2)
	e.sign(t, "u1", 3)
	// 第 4 天未签：连签 3，今天是周期第 4 天，格子 1-3 已签，明天（第 5 天）10 分。
	e.clk.Set(day(4))
	st, _ = e.svc.Status(ctx, "u1", false)
	if st.StreakState != service.StreakActive || st.StreakDays != 3 || st.CycleDay != 4 || st.CheckedToday {
		t.Fatalf("ACTIVE: %+v", st)
	}
	for i, c := range st.Cycle {
		wantChecked := i < 3
		if c.Checked != wantChecked || c.IsToday != (c.Day == 4) {
			t.Errorf("cell %d: %+v", i+1, c)
		}
	}
	if st.Cycle[2].PointsTotal != 20 || st.Cycle[2].BonusPoints != 10 || st.Cycle[6].PointsTotal != 40 {
		t.Errorf("cells: %+v", st.Cycle)
	}
	if st.TodayPreview != 10 || st.TomorrowPreview != 10 {
		t.Errorf("preview: %+v", st)
	}

	// 已签：streak 含今天，today_points_preview 是实际值。
	e.sign(t, "u1", 4)
	st, _ = e.svc.Status(ctx, "u1", false)
	if !st.CheckedToday || st.CanCheckin || st.StreakDays != 4 || st.CycleDay != 4 || st.TodayPreview != 10 {
		t.Fatalf("checked today: %+v", st)
	}

	// 第 7 天签完，第 8 天：cycle_day=1，格子全部清空；streak_days 仍是 7。
	e.sign(t, "u1", 5)
	e.sign(t, "u1", 6)
	e.sign(t, "u1", 7)
	e.clk.Set(day(8))
	st, _ = e.svc.Status(ctx, "u1", false)
	if st.StreakDays != 7 || st.CycleDay != 1 {
		t.Fatalf("day8: %+v", st)
	}
	for _, c := range st.Cycle {
		if c.Checked {
			t.Errorf("day 8 cells must be cleared: %+v", c)
		}
	}

	// 受限账号：状态可查，不能签。
	st, _ = e.svc.Status(ctx, "u1", true)
	if st.CanCheckin || !st.Restricted {
		t.Fatalf("restricted: %+v", st)
	}
}

func TestRuleVersionSwitch(t *testing.T) {
	cfg, err := rules.Parse([]byte(`{"versions":[
	 {"rule_version":"v1","effective_date":"2026-01-01","base_points":10,"streak_bonus":[0,0,10,0,0,0,30]},
	 {"rule_version":"v2","effective_date":"2026-11-02","base_points":20,"streak_bonus":[0,0,10,0,0,0,30]}]}`))
	if err != nil {
		t.Fatal(err)
	}
	e := newEnv(t, cfg)
	a := e.sign(t, "u1", 1)
	b := e.sign(t, "u1", 2)
	if a.RuleVersion != "v1" || a.PointsTotal != 10 || b.RuleVersion != "v2" || b.PointsTotal != 20 || b.Balance != 30 {
		t.Fatalf("a=%+v b=%+v", a, b)
	}
	// R5：规则变更后，已签格子取记录里的实际值。
	st, _ := e.svc.Status(context.Background(), "u1", false)
	if st.Cycle[0].PointsTotal != 10 || st.Cycle[1].PointsTotal != 20 || st.Cycle[2].PointsTotal != 30 {
		t.Fatalf("cells: %+v", st.Cycle)
	}
}

func TestLedgerPaginationStableUnderInsert(t *testing.T) {
	e := newEnv(t, nil)
	ctx := context.Background()
	for d := 1; d <= 8; d++ { // 8 天 = 8 条基础 + 第 3、7 天各 1 条奖励 = 10 条
		e.sign(t, "u1", d)
	}
	var all []store.LedgerEntry
	p, more, err := e.svc.Ledger(ctx, "u1", nil, 4)
	if err != nil || len(p) != 4 || !more {
		t.Fatalf("page1 len=%d more=%v err=%v", len(p), more, err)
	}
	all = append(all, p...)
	// 翻页中间插入新流水（第 9 天签到）。
	e.sign(t, "u1", 9)
	for more {
		last := p[len(p)-1]
		p, more, err = e.svc.Ledger(ctx, "u1", &store.Cursor{CreatedAt: last.CreatedAt, ID: last.ID}, 4)
		if err != nil {
			t.Fatal(err)
		}
		all = append(all, p...)
	}
	if len(all) != 10 {
		t.Fatalf("want 10 original entries, got %d", len(all))
	}
	seen := map[int64]bool{}
	for i, en := range all {
		if seen[en.ID] {
			t.Fatalf("duplicate id %d", en.ID)
		}
		seen[en.ID] = true
		if i > 0 && all[i-1].ID <= en.ID {
			t.Fatalf("order must be id desc: %d then %d", all[i-1].ID, en.ID)
		}
	}
	// 新签到的流水在首页最前面。
	top, _, _ := e.svc.Ledger(ctx, "u1", nil, 1)
	if len(top) != 1 || seen[top[0].ID] {
		t.Fatalf("new entry should be first and not among old ones: %+v", top)
	}
}

func TestBalanceNewUser(t *testing.T) {
	e := newEnv(t, nil)
	bal, upd, err := e.svc.Balance(context.Background(), "nobody")
	if err != nil || bal != 0 || upd != nil {
		t.Fatalf("bal=%d upd=%v err=%v", bal, upd, err)
	}
	items, more, err := e.svc.Ledger(context.Background(), "nobody", nil, 20)
	if err != nil || len(items) != 0 || more {
		t.Fatalf("items=%d more=%v err=%v", len(items), more, err)
	}
}
