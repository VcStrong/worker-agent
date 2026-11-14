package httpapi_test

import (
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"net/http"
	"net/http/httptest"
	"strings"
	"sync/atomic"
	"testing"
	"time"

	"demoapp/server/internal/clock"
	"demoapp/server/internal/httpapi"
	"demoapp/server/internal/ratelimit"
	"demoapp/server/internal/rules"
	"demoapp/server/internal/service"
	"demoapp/server/internal/store"
	"demoapp/server/internal/store/memory"
)

var seq int64

func newRID() string {
	return fmt.Sprintf("00000000-0000-4000-8000-%012d", atomic.AddInt64(&seq, 1))
}

func day(d int) time.Time { return time.Date(2026, 11, d, 10, 0, 0, 0, clock.CST) }

type srv struct {
	h   http.Handler
	clk *clock.Fixed
}

func newSrv(t *testing.T) *srv {
	t.Helper()
	clk := clock.NewFixed(day(1))
	var n int64
	st := memory.NewWithNow(func() time.Time {
		n++
		return time.Date(2026, 1, 1, 0, 0, 0, 0, time.UTC).Add(time.Duration(n) * time.Second)
	})
	svc := service.New(st, clk, rules.Default(), nil)
	frozen := time.Date(2026, 11, 14, 0, 0, 0, 0, time.UTC) // 限流时钟冻结：不补令牌，测试不依赖墙钟
	lim := ratelimit.New(10, time.Minute, func() time.Time { return frozen })
	return &srv{h: httpapi.New(httpapi.Config{Service: svc, Limiter: lim}), clk: clk}
}

type resp struct {
	status int
	header http.Header
	code   string
	data   map[string]any
}

func (s *srv) do(method, path string, hdr map[string]string) resp {
	req := httptest.NewRequest(method, path, strings.NewReader("{}"))
	for k, v := range hdr {
		req.Header.Set(k, v)
	}
	rec := httptest.NewRecorder()
	s.h.ServeHTTP(rec, req)
	var env struct {
		Code string         `json:"code"`
		Data map[string]any `json:"data"`
	}
	_ = json.Unmarshal(rec.Body.Bytes(), &env)
	return resp{status: rec.Code, header: rec.Header(), code: env.Code, data: env.Data}
}

func user(u string) map[string]string { return map[string]string{"X-User-Id": u} }

func post(u, rid string) map[string]string {
	return map[string]string{"X-User-Id": u, "X-Request-Id": rid}
}

const (
	pStatus  = "/api/v1/checkin/status"
	pCheckin = "/api/v1/checkin"
	pBalance = "/api/v1/points/balance"
	pLedger  = "/api/v1/points/ledger"
)

func num(t *testing.T, m map[string]any, k string) float64 {
	t.Helper()
	v, ok := m[k].(float64)
	if !ok {
		t.Fatalf("field %q missing or not a number in %v", k, m)
	}
	return v
}

func TestFlowFirstCheckinStatusBalanceLedger(t *testing.T) {
	s := newSrv(t)

	r := s.do("GET", pStatus, user("u1"))
	if r.status != 200 || r.code != "ok" || r.data["streak_state"] != "NONE" || r.data["can_checkin"] != true ||
		r.data["server_date"] != "2026-11-01" || r.data["timezone"] != "Asia/Shanghai" {
		t.Fatalf("status before: %+v", r)
	}
	if cells, _ := r.data["cycle"].([]any); len(cells) != 7 {
		t.Fatalf("cycle cells: %v", r.data["cycle"])
	}
	if r.header.Get("X-Trace-Id") == "" {
		t.Error("missing X-Trace-Id")
	}

	r = s.do("POST", pCheckin, post("u1", newRID()))
	if r.status != 200 || r.code != "ok" || num(t, r.data, "points_total") != 10 || num(t, r.data, "balance") != 10 ||
		r.data["checkin_date"] != "2026-11-01" || r.data["rule_version"] != "v1" {
		t.Fatalf("checkin: %+v", r)
	}
	ledger, _ := r.data["ledger"].([]any)
	if len(ledger) != 1 {
		t.Fatalf("ledger in result: %v", r.data["ledger"])
	}
	item := ledger[0].(map[string]any)
	if item["type"] != "CHECKIN_BASE" || item["biz_type"] != "CHECKIN" {
		t.Fatalf("ledger item: %v", item)
	}
	if _, ok := item["id"].(string); !ok {
		t.Errorf("id must be string: %v", item["id"])
	}
	if ct, _ := item["created_at"].(string); !strings.HasSuffix(ct, "Z") || len(ct) != len("2026-11-14T01:12:00.123456Z") {
		t.Errorf("created_at format: %v", item["created_at"])
	}

	r = s.do("GET", pStatus, user("u1"))
	if r.data["checked_today"] != true || r.data["can_checkin"] != false || num(t, r.data, "streak_days") != 1 {
		t.Fatalf("status after: %+v", r)
	}

	r = s.do("GET", pBalance, user("u1"))
	if num(t, r.data, "balance") != 10 || r.data["updated_at"] == nil {
		t.Fatalf("balance: %+v", r)
	}

	r = s.do("GET", pLedger, user("u1"))
	items, _ := r.data["items"].([]any)
	if len(items) != 1 || r.data["has_more"] != false || r.data["next_cursor"] != nil {
		t.Fatalf("ledger: %+v", r)
	}
}

func TestBalanceNewUserNullUpdatedAt(t *testing.T) {
	s := newSrv(t)
	r := s.do("GET", pBalance, user("fresh"))
	if r.status != 200 || num(t, r.data, "balance") != 0 || r.data["updated_at"] != nil {
		t.Fatalf("%+v", r)
	}
	r = s.do("GET", pLedger, user("fresh"))
	if items, ok := r.data["items"].([]any); !ok || len(items) != 0 {
		t.Fatalf("empty ledger must be []: %+v", r)
	}
}

func TestDay3Day7Day8OverHTTP(t *testing.T) {
	s := newSrv(t)
	want := []float64{10, 10, 20, 10, 10, 10, 40, 10}
	for i := 1; i <= 8; i++ {
		s.clk.Set(day(i))
		r := s.do("POST", pCheckin, post("u1", newRID()))
		if r.code != "ok" || num(t, r.data, "points_total") != want[i-1] {
			t.Fatalf("day %d: %+v", i, r)
		}
		if i == 8 && (num(t, r.data, "cycle_day") != 1 || num(t, r.data, "streak_days") != 8) {
			t.Fatalf("day 8: %+v", r)
		}
	}
}

func TestDuplicateAndReplayOverHTTP(t *testing.T) {
	s := newSrv(t)
	id := newRID()
	a := s.do("POST", pCheckin, post("u1", id))
	b := s.do("POST", pCheckin, post("u1", id))
	if a.code != "ok" || b.code != "ok" || num(t, b.data, "balance") != 10 {
		t.Fatalf("replay: %+v %+v", a, b)
	}
	c := s.do("POST", pCheckin, post("u1", newRID()))
	if c.status != 200 || c.code != "already_checked_in" || num(t, c.data, "balance") != 10 {
		t.Fatalf("already: %+v", c)
	}
}

func TestCrossMidnightOverHTTP(t *testing.T) {
	s := newSrv(t)
	id := newRID()
	s.clk.Set(time.Date(2026, 11, 1, 23, 59, 59, 999_000_000, clock.CST))
	a := s.do("POST", pCheckin, post("u1", id))
	s.clk.Set(time.Date(2026, 11, 2, 0, 0, 0, 0, clock.CST))
	b := s.do("POST", pCheckin, post("u1", id)) // 跨零点重试，同一个 request_id
	if a.data["checkin_date"] != "2026-11-01" || b.code != "ok" || b.data["checkin_date"] != "2026-11-01" {
		t.Fatalf("a=%+v b=%+v", a, b)
	}
	c := s.do("POST", pCheckin, post("u1", newRID())) // 新 request_id，新的一天
	if c.code != "ok" || c.data["checkin_date"] != "2026-11-02" || num(t, c.data, "streak_days") != 2 {
		t.Fatalf("c=%+v", c)
	}
}

func TestUnauthorized401(t *testing.T) {
	s := newSrv(t)
	for _, p := range []struct{ method, path string }{
		{"GET", pStatus}, {"POST", pCheckin}, {"GET", pBalance}, {"GET", pLedger},
	} {
		hdr := map[string]string{"X-Request-Id": newRID()}
		r := s.do(p.method, p.path, hdr)
		if r.status != 401 || r.code != "unauthorized" {
			t.Errorf("%s %s without user: %+v", p.method, p.path, r)
		}
	}
	for _, bad := range []string{"a b", "a/b", strings.Repeat("x", 65), "用户"} {
		r := s.do("GET", pBalance, map[string]string{"X-User-Id": bad})
		if r.status != 401 {
			t.Errorf("X-User-Id %q should be 401, got %d", bad, r.status)
		}
	}
}

func TestRestricted403(t *testing.T) {
	s := newSrv(t)
	for _, st := range []string{"banned", "deactivating"} {
		h := post("u1", newRID())
		h["X-User-Status"] = st
		r := s.do("POST", pCheckin, h)
		if r.status != 403 || r.code != "account_restricted" {
			t.Errorf("%s checkin: %+v", st, r)
		}
	}
	h := user("u1")
	h["X-User-Status"] = "banned"
	if r := s.do("GET", pLedger, h); r.status != 200 {
		t.Errorf("banned ledger: %+v", r)
	}
	if r := s.do("GET", pBalance, h); r.status != 200 {
		t.Errorf("banned balance: %+v", r)
	}
	r := s.do("GET", pStatus, h)
	if r.status != 200 || r.data["can_checkin"] != false || r.data["account_status"] != "restricted" {
		t.Errorf("banned status: %+v", r)
	}
	// 没有真的发分。
	if r := s.do("GET", pBalance, user("u1")); num(t, r.data, "balance") != 0 {
		t.Errorf("restricted user got points: %+v", r)
	}
}

func TestInvalidRequestID400(t *testing.T) {
	s := newSrv(t)
	for _, id := range []string{"", "not-a-uuid", "00000000-0000-4000-8000-00000000000"} {
		r := s.do("POST", pCheckin, map[string]string{"X-User-Id": "u1", "X-Request-Id": id})
		if r.status != 400 || r.code != "invalid_request" {
			t.Errorf("rid %q: %+v", id, r)
		}
	}
}

func TestRateLimit429(t *testing.T) {
	s := newSrv(t)
	for i := 1; i <= 10; i++ {
		r := s.do("POST", pCheckin, post("limited", newRID()))
		if r.status != 200 {
			t.Fatalf("request %d should pass: %+v", i, r)
		}
	}
	r := s.do("POST", pCheckin, post("limited", newRID()))
	if r.status != 429 || r.code != "rate_limited" {
		t.Fatalf("11th should be 429: %+v", r)
	}
	if ra := r.header.Get("Retry-After"); ra == "" || ra == "0" {
		t.Errorf("Retry-After=%q", ra)
	}
	// 其他用户不受影响；读接口不限流。
	if o := s.do("POST", pCheckin, post("other", newRID())); o.status != 200 {
		t.Errorf("other user: %+v", o)
	}
	if g := s.do("GET", pBalance, user("limited")); g.status != 200 {
		t.Errorf("read should not be limited: %+v", g)
	}
}

func TestLedgerPaginationAndCursorErrors(t *testing.T) {
	s := newSrv(t)
	for i := 1; i <= 7; i++ { // 7 天 = 7 基础 + 2 奖励 = 9 条
		s.clk.Set(day(i))
		s.do("POST", pCheckin, post("u1", newRID()))
	}
	var ids []string
	path := pLedger + "?limit=4"
	for pages := 0; pages < 10; pages++ {
		r := s.do("GET", path, user("u1"))
		if r.status != 200 {
			t.Fatalf("page: %+v", r)
		}
		items, _ := r.data["items"].([]any)
		for _, it := range items {
			ids = append(ids, it.(map[string]any)["id"].(string))
		}
		if r.data["has_more"] == false {
			if r.data["next_cursor"] != nil {
				t.Fatalf("last page must have null cursor: %+v", r)
			}
			break
		}
		cur, ok := r.data["next_cursor"].(string)
		if !ok || cur == "" {
			t.Fatalf("has_more without cursor: %+v", r)
		}
		path = pLedger + "?limit=4&cursor=" + cur
	}
	if len(ids) != 9 {
		t.Fatalf("want 9 entries across pages, got %d: %v", len(ids), ids)
	}
	seen := map[string]bool{}
	for _, id := range ids {
		if seen[id] {
			t.Fatalf("duplicate %s", id)
		}
		seen[id] = true
	}

	for _, q := range []string{"limit=0", "limit=51", "limit=abc", "limit=-1"} {
		if r := s.do("GET", pLedger+"?"+q, user("u1")); r.status != 400 || r.code != "invalid_request" {
			t.Errorf("%s: %+v", q, r)
		}
	}
	for _, c := range []string{"!!!", "bm90LWEtY3Vyc29y", "MV8"} {
		if r := s.do("GET", pLedger+"?cursor="+c, user("u1")); r.status != 400 || r.code != "invalid_cursor" {
			t.Errorf("cursor %q: %+v", c, r)
		}
	}
}

func TestNotFoundAndMethodNotAllowedUseEnvelope(t *testing.T) {
	s := newSrv(t)
	if r := s.do("GET", "/api/v1/nope", nil); r.status != 404 || r.code != "not_found" {
		t.Errorf("404: %+v", r)
	}
	r := s.do("POST", pStatus, user("u1"))
	if r.status != 405 || r.code != "method_not_allowed" || r.header.Get("Allow") != "GET" {
		t.Errorf("405: %+v", r)
	}
	if r := s.do("GET", "/healthz", nil); r.status != 200 {
		t.Errorf("healthz: %+v", r)
	}
}

// CR P-10-①：X-Request-Id 大小写不敏感，大写重放必须命中同一条记录。
func TestUppercaseRequestIDReplaysSameRecord(t *testing.T) {
	s := newSrv(t)
	id := newRID()
	a := s.do("POST", pCheckin, post("u1", strings.ToLower(id)))
	b := s.do("POST", pCheckin, post("u1", strings.ToUpper(id)))
	if a.code != "ok" || b.code != "ok" || num(t, b.data, "balance") != 10 {
		t.Fatalf("a=%+v b=%+v", a, b)
	}
}

// failingStore 的写事务一律返回指定错误。
type failingStore struct {
	store.Store
	err error
}

func (f failingStore) WithUserTx(context.Context, string, func(store.UserTx) error) error {
	return f.err
}

// CR P-10-②③：ErrUnavailable -> 503 service_unavailable，未知错误 -> 500 internal_error，都带统一外壳。
func TestStoreFailuresUseEnvelope(t *testing.T) {
	cases := []struct {
		err    error
		status int
		code   string
	}{
		{fmt.Errorf("%w: lock timeout", store.ErrUnavailable), http.StatusServiceUnavailable, "service_unavailable"},
		{errors.New("boom"), http.StatusInternalServerError, "internal_error"},
	}
	for _, c := range cases {
		svc := service.New(failingStore{Store: memory.New(), err: c.err}, clock.NewFixed(day(1)), rules.Default(), nil)
		h := httpapi.New(httpapi.Config{Service: svc})
		req := httptest.NewRequest("POST", pCheckin, strings.NewReader("{}"))
		req.Header.Set("X-User-Id", "u1")
		req.Header.Set("X-Request-Id", newRID())
		rec := httptest.NewRecorder()
		h.ServeHTTP(rec, req)
		var env struct {
			Code string `json:"code"`
		}
		if err := json.Unmarshal(rec.Body.Bytes(), &env); err != nil || rec.Code != c.status || env.Code != c.code {
			t.Fatalf("err=%v status=%d code=%q body=%s", c.err, rec.Code, env.Code, rec.Body.String())
		}
	}
}
