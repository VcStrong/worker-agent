package httpapi

import (
	"encoding/base64"
	"errors"
	"fmt"
	"strconv"
	"strings"
	"time"

	"demoapp/server/internal/store"
)

var errBadCursor = errors.New("invalid cursor")

// encodeCursor 生成 base64url（无 padding）的 "<created_at Unix 微秒>_<id>"，对客户端不透明。
func encodeCursor(e store.LedgerEntry) string {
	raw := fmt.Sprintf("%d_%d", e.CreatedAt.UnixMicro(), e.ID)
	return base64.RawURLEncoding.EncodeToString([]byte(raw))
}

// decodeCursor 解码；任何异常都返回 errBadCursor，不 panic。
func decodeCursor(s string) (*store.Cursor, error) {
	b, err := base64.RawURLEncoding.DecodeString(s)
	if err != nil {
		return nil, errBadCursor
	}
	parts := strings.Split(string(b), "_")
	if len(parts) != 2 {
		return nil, errBadCursor
	}
	micros, err := strconv.ParseInt(parts[0], 10, 64)
	if err != nil {
		return nil, errBadCursor
	}
	id, err := strconv.ParseInt(parts[1], 10, 64)
	if err != nil || id < 0 {
		return nil, errBadCursor
	}
	return &store.Cursor{CreatedAt: time.UnixMicro(micros).UTC(), ID: id}, nil
}
