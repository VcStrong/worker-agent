// Package ratelimit 是按 key 计数的进程内令牌桶，会定期清理空闲 key。
package ratelimit

import (
	"math"
	"sync"
	"time"
)

type bucket struct {
	tokens float64
	last   time.Time
}

// Limiter 令牌桶：容量 capacity，每 per 时间补满。
type Limiter struct {
	mu        sync.Mutex
	capacity  float64
	rate      float64 // 每秒补多少
	per       time.Duration
	now       func() time.Time
	buckets   map[string]*bucket
	lastSweep time.Time
}

// New 创建限流器；now 为 nil 时用 time.Now。
func New(capacity int, per time.Duration, now func() time.Time) *Limiter {
	if now == nil {
		now = time.Now
	}
	return &Limiter{
		capacity: float64(capacity),
		rate:     float64(capacity) / per.Seconds(),
		per:      per,
		now:      now,
		buckets:  make(map[string]*bucket),
	}
}

// Allow 消耗 1 个令牌；不允许时返回需要等待的时间。
func (l *Limiter) Allow(key string) (bool, time.Duration) {
	l.mu.Lock()
	defer l.mu.Unlock()
	now := l.now()
	l.sweep(now)
	b, ok := l.buckets[key]
	if !ok {
		b = &bucket{tokens: l.capacity, last: now}
		l.buckets[key] = b
	}
	if el := now.Sub(b.last).Seconds(); el > 0 {
		b.tokens = math.Min(l.capacity, b.tokens+el*l.rate)
		b.last = now
	}
	if b.tokens >= 1 {
		b.tokens--
		return true, 0
	}
	need := (1 - b.tokens) / l.rate
	return false, time.Duration(need * float64(time.Second))
}

// sweep 清理超过 2 个补满周期没有动静的 key（必须持锁调用）。
func (l *Limiter) sweep(now time.Time) {
	if now.Sub(l.lastSweep) < time.Minute {
		return
	}
	l.lastSweep = now
	for k, b := range l.buckets {
		if now.Sub(b.last) > 2*l.per {
			delete(l.buckets, k)
		}
	}
}
