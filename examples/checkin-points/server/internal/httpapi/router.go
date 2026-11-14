// Package httpapi 是 HTTP 层：路由、中间件（trace → accesslog → recover → timeout → auth → ratelimit[仅 POST]）、DTO、错误码。
package httpapi

import (
	"context"
	"io"
	"log/slog"
	"net/http"
	"regexp"
	"strconv"
	"strings"

	"demoapp/server/internal/ratelimit"
	"demoapp/server/internal/service"
	"demoapp/server/internal/store"
)

// Config 是 API 的依赖。
type Config struct {
	Service *service.Service
	Limiter *ratelimit.Limiter                // nil 表示关闭签到限流（RATE_LIMIT_ENABLED=false）
	Logger  *slog.Logger                      // nil 则丢弃
	Ready   func(ctx context.Context) error   // nil 表示总是就绪
}

// API 持有依赖。
type API struct {
	cfg Config
	log *slog.Logger
}

// 已知路由 -> 允许的方法，用于把 404 / 405 也包成统一外壳。
var knownRoutes = map[string]string{
	"/api/v1/checkin/status": http.MethodGet,
	"/api/v1/checkin":        http.MethodPost,
	"/api/v1/points/balance": http.MethodGet,
	"/api/v1/points/ledger":  http.MethodGet,
	"/healthz":               http.MethodGet,
	"/readyz":                http.MethodGet,
}

var requestIDRe = regexp.MustCompile(`^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$`)

// New 构建 http.Handler。
func New(cfg Config) http.Handler {
	log := cfg.Logger
	if log == nil {
		log = slog.New(slog.NewTextHandler(io.Discard, nil))
	}
	a := &API{cfg: cfg, log: log}

	mux := http.NewServeMux()
	mux.Handle("GET /api/v1/checkin/status", a.auth(http.HandlerFunc(a.handleStatus)))
	mux.Handle("POST /api/v1/checkin", a.auth(a.rateLimit(http.HandlerFunc(a.handleCheckin))))
	mux.Handle("GET /api/v1/points/balance", a.auth(http.HandlerFunc(a.handleBalance)))
	mux.Handle("GET /api/v1/points/ledger", a.auth(http.HandlerFunc(a.handleLedger)))
	mux.HandleFunc("GET /healthz", func(w http.ResponseWriter, r *http.Request) {
		writeJSONRaw(w, http.StatusOK, `{"status":"ok"}`)
	})
	mux.HandleFunc("GET /readyz", a.handleReady)
	mux.HandleFunc("/", a.fallback)

	return a.traceMW(a.accessLog(a.recoverMW(a.timeoutMW(mux))))
}

func writeJSONRaw(w http.ResponseWriter, status int, body string) {
	w.Header().Set("Content-Type", "application/json; charset=utf-8")
	w.WriteHeader(status)
	_, _ = w.Write([]byte(body))
}

func (a *API) fallback(w http.ResponseWriter, r *http.Request) {
	if allow, ok := knownRoutes[r.URL.Path]; ok {
		w.Header().Set("Allow", allow)
		writeJSON(w, http.StatusMethodNotAllowed, "method_not_allowed", "method not allowed", nil)
		return
	}
	writeJSON(w, http.StatusNotFound, "not_found", "not found", nil)
}

func (a *API) handleReady(w http.ResponseWriter, r *http.Request) {
	if a.cfg.Ready != nil {
		if err := a.cfg.Ready(r.Context()); err != nil {
			writeJSONRaw(w, http.StatusServiceUnavailable, `{"status":"unavailable"}`)
			return
		}
	}
	writeJSONRaw(w, http.StatusOK, `{"status":"ok"}`)
}

func (a *API) handleStatus(w http.ResponseWriter, r *http.Request) {
	id := identityFrom(r.Context())
	v, err := a.cfg.Service.Status(r.Context(), id.UserID, id.Restricted)
	if err != nil {
		a.fail(w, r, err)
		return
	}
	writeOK(w, "ok", toStatusDTO(v))
}

func (a *API) handleCheckin(w http.ResponseWriter, r *http.Request) {
	id := identityFrom(r.Context())
	if id.Restricted {
		writeJSON(w, http.StatusForbidden, "account_restricted", "account restricted", nil)
		return
	}
	rid := r.Header.Get("X-Request-Id")
	if !requestIDRe.MatchString(rid) {
		writeJSON(w, http.StatusBadRequest, "invalid_request", "X-Request-Id must be a UUID", nil)
		return
	}
	res, err := a.cfg.Service.CheckIn(r.Context(), id.UserID, strings.ToLower(rid))
	if err != nil {
		a.fail(w, r, err)
		return
	}
	writeOK(w, res.Code, toResultDTO(res))
}

func (a *API) handleBalance(w http.ResponseWriter, r *http.Request) {
	id := identityFrom(r.Context())
	bal, updated, err := a.cfg.Service.Balance(r.Context(), id.UserID)
	if err != nil {
		a.fail(w, r, err)
		return
	}
	dto := balanceDTO{Balance: bal}
	if updated != nil {
		s := fmtTime(*updated)
		dto.UpdatedAt = &s
	}
	writeOK(w, "ok", dto)
}

func (a *API) handleLedger(w http.ResponseWriter, r *http.Request) {
	id := identityFrom(r.Context())
	q := r.URL.Query()
	limit := 20
	if s := q.Get("limit"); s != "" {
		n, err := strconv.Atoi(s)
		if err != nil || n < 1 || n > 50 {
			writeJSON(w, http.StatusBadRequest, "invalid_request", "limit must be 1-50", nil)
			return
		}
		limit = n
	}
	var after *store.Cursor
	if c := q.Get("cursor"); c != "" {
		cur, err := decodeCursor(c)
		if err != nil {
			writeJSON(w, http.StatusBadRequest, "invalid_cursor", "invalid cursor", nil)
			return
		}
		after = cur
	}
	items, more, err := a.cfg.Service.Ledger(r.Context(), id.UserID, after, limit)
	if err != nil {
		a.fail(w, r, err)
		return
	}
	page := ledgerPageDTO{Items: toLedgerItems(items), HasMore: more}
	if more && len(items) > 0 {
		c := encodeCursor(items[len(items)-1])
		page.NextCursor = &c
	}
	writeOK(w, "ok", page)
}
