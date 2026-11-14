package httpapi

import (
	"context"
	"encoding/json"
	"errors"
	"net/http"

	"demoapp/server/internal/store"
)

// envelope 是统一响应外壳：{"code","message","data"}。
type envelope struct {
	Code    string `json:"code"`
	Message string `json:"message"`
	Data    any    `json:"data"`
}

func writeJSON(w http.ResponseWriter, status int, code, msg string, data any) {
	b, err := json.Marshal(envelope{Code: code, Message: msg, Data: data})
	if err != nil {
		status = http.StatusInternalServerError
		b = []byte(`{"code":"internal_error","message":"encode failed","data":null}`)
	}
	w.Header().Set("Content-Type", "application/json; charset=utf-8")
	w.WriteHeader(status)
	_, _ = w.Write(b)
}

func writeOK(w http.ResponseWriter, code string, data any) {
	writeJSON(w, http.StatusOK, code, "", data)
}

// fail 把内部错误映射成 500 / 503。message 只用于排查，不带内部细节。
func (a *API) fail(w http.ResponseWriter, r *http.Request, err error) {
	if errors.Is(err, store.ErrUnavailable) ||
		errors.Is(err, context.DeadlineExceeded) ||
		errors.Is(err, context.Canceled) {
		writeJSON(w, http.StatusServiceUnavailable, "service_unavailable", "service unavailable", nil)
		return
	}
	info := infoFrom(r.Context())
	traceID := ""
	if info != nil {
		traceID = info.traceID
	}
	a.log.Error("internal error", "err", err.Error(), "trace_id", traceID)
	writeJSON(w, http.StatusInternalServerError, "internal_error", "internal error", nil)
}
