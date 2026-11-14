package httpapi

import (
	"context"
	"crypto/rand"
	"encoding/hex"
	"math"
	"net/http"
	"regexp"
	"strconv"
	"strings"
	"time"
)

type ctxKey int

const (
	infoKey ctxKey = iota
	identKey
)

// reqInfo 在 trace 中间件里创建，auth 填入 userID，accesslog 读取。
type reqInfo struct {
	traceID string
	userID  string
}

type identity struct {
	UserID     string
	Restricted bool // X-User-Status 不是 active（banned / deactivating / 未知值一律按受限处理）
}

func infoFrom(ctx context.Context) *reqInfo {
	v, _ := ctx.Value(infoKey).(*reqInfo)
	return v
}

func identityFrom(ctx context.Context) identity {
	v, _ := ctx.Value(identKey).(identity)
	return v
}

func newTraceID() string {
	var b [16]byte
	if _, err := rand.Read(b[:]); err != nil {
		return "0000000000000000"
	}
	return hex.EncodeToString(b[:])
}

// traceMW 最外层：给每个响应带 X-Trace-Id。
func (a *API) traceMW(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		info := &reqInfo{traceID: newTraceID()}
		w.Header().Set("X-Trace-Id", info.traceID)
		next.ServeHTTP(w, r.WithContext(context.WithValue(r.Context(), infoKey, info)))
	})
}

type statusRecorder struct {
	http.ResponseWriter
	status int
	wrote  bool // 已经写过响应头（含隐式 200）
}

func (s *statusRecorder) WriteHeader(code int) {
	if !s.wrote {
		s.status = code
	}
	s.wrote = true
	s.ResponseWriter.WriteHeader(code)
}

func (s *statusRecorder) Write(b []byte) (int, error) {
	s.wrote = true
	return s.ResponseWriter.Write(b)
}

// accessLog 只记 user_id、路径、状态码、耗时、trace_id；不记 Authorization、Cookie、请求体。
func (a *API) accessLog(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		start := time.Now()
		sr := &statusRecorder{ResponseWriter: w, status: http.StatusOK}
		next.ServeHTTP(sr, r)
		info := infoFrom(r.Context())
		var uid, tid string
		if info != nil {
			uid, tid = info.userID, info.traceID
		}
		a.log.Info("access",
			"method", r.Method,
			"path", r.URL.Path,
			"status", sr.status,
			"dur_ms", time.Since(start).Milliseconds(),
			"user_id", uid,
			"trace_id", tid)
	})
}

func (a *API) recoverMW(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		defer func() {
			if rec := recover(); rec != nil {
				a.log.Error("panic recovered", "panic", rec)
				// CR P-09：响应头已写出时不能再写一次（会产生 superfluous WriteHeader 和拼接的坏 body）。
				if sr, ok := w.(*statusRecorder); ok && sr.wrote {
					return
				}
				writeJSON(w, http.StatusInternalServerError, "internal_error", "internal error", nil)
			}
		}()
		next.ServeHTTP(w, r)
	})
}

// timeoutMW 给 handler 的 context 设 5 秒超时（契约：服务端先于客户端 10 秒放弃）。
func (a *API) timeoutMW(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		ctx, cancel := context.WithTimeout(r.Context(), 5*time.Second)
		defer cancel()
		next.ServeHTTP(w, r.WithContext(ctx))
	})
}

var userIDRe = regexp.MustCompile(`^[A-Za-z0-9_-]{1,64}$`)

// auth 信任网关注入的 X-User-Id / X-User-Status；缺失或格式不对一律 401。
func (a *API) auth(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		uid := r.Header.Get("X-User-Id")
		if !userIDRe.MatchString(uid) {
			writeJSON(w, http.StatusUnauthorized, "unauthorized", "missing or invalid X-User-Id", nil)
			return
		}
		status := strings.ToLower(strings.TrimSpace(r.Header.Get("X-User-Status")))
		restricted := status != "" && status != "active"
		if restricted && status != "banned" && status != "deactivating" {
			// CR P-08：未知状态值按受限处理（失败即安全），但要留痕，便于发现网关新增了状态值。
			tid := ""
			if info := infoFrom(r.Context()); info != nil {
				tid = info.traceID
			}
			a.log.Warn("unknown X-User-Status, treated as restricted", "status", status, "trace_id", tid)
		}
		if info := infoFrom(r.Context()); info != nil {
			info.userID = uid
		}
		ctx := context.WithValue(r.Context(), identKey, identity{UserID: uid, Restricted: restricted})
		next.ServeHTTP(w, r.WithContext(ctx))
	})
}

// rateLimit 只挂在 POST /api/v1/checkin 上，按 user_id 10 次/分钟；放在 auth 之后。
func (a *API) rateLimit(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if a.cfg.Limiter != nil {
			id := identityFrom(r.Context())
			if ok, retry := a.cfg.Limiter.Allow(id.UserID); !ok {
				secs := int(math.Ceil(retry.Seconds()))
				if secs < 1 {
					secs = 1
				}
				w.Header().Set("Retry-After", strconv.Itoa(secs))
				writeJSON(w, http.StatusTooManyRequests, "rate_limited", "too many requests", nil)
				return
			}
		}
		next.ServeHTTP(w, r)
	})
}
