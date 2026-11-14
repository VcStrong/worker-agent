// Package clock 提供可注入时钟，统一按北京时间（UTC+8 固定偏移）判日。
package clock

import (
	"sync"
	"time"

	"demoapp/server/internal/civil"
)

// CST 是固定偏移的北京时间；中国大陆无夏令时，不依赖 tzdata（技术方案 D5）。
var CST = time.FixedZone("Asia/Shanghai", 8*3600)

// Clock 是时钟接口。
type Clock interface {
	Now() time.Time
}

// Real 是真实时钟，返回 UTC+8 时间。
type Real struct{}

// Now 返回当前北京时间。
func (Real) Now() time.Time { return time.Now().In(CST) }

// Fixed 是测试用的可调时钟，并发安全。
type Fixed struct {
	mu sync.Mutex
	t  time.Time
}

// NewFixed 创建固定时钟。
func NewFixed(t time.Time) *Fixed { return &Fixed{t: t} }

// Now 返回当前设定的时间（UTC+8）。
func (f *Fixed) Now() time.Time {
	f.mu.Lock()
	defer f.mu.Unlock()
	return f.t.In(CST)
}

// Set 设置时间。
func (f *Fixed) Set(t time.Time) {
	f.mu.Lock()
	f.t = t
	f.mu.Unlock()
}

// Advance 推进时间。
func (f *Fixed) Advance(d time.Duration) {
	f.mu.Lock()
	f.t = f.t.Add(d)
	f.mu.Unlock()
}

// Today 返回时钟当前的北京时间日期。
func Today(c Clock) civil.Date {
	return civil.FromTime(c.Now().In(CST))
}
