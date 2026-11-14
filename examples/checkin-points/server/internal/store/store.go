// Package store 定义存储接口；实现见 memory（默认）和 postgres（-tags pg）。
package store

import (
	"context"
	"errors"
	"time"

	"demoapp/server/internal/civil"
)

var (
	// ErrConflict 唯一约束冲突（user+date、user+request_id、ledger biz）。
	ErrConflict = errors.New("store: unique constraint conflict")
	// ErrUnavailable 存储不可用、拿锁超时、语句超时，对外映射 503。
	ErrUnavailable = errors.New("store: unavailable")
)

// 流水类型与业务类型。
const (
	TypeCheckinBase        = "CHECKIN_BASE"
	TypeCheckinStreakBonus = "CHECKIN_STREAK_BONUS"
	BizCheckin             = "CHECKIN"
)

// CheckinRecord 对应 checkin_record。
type CheckinRecord struct {
	ID          int64
	UserID      string
	CheckinDate civil.Date
	StreakDays  int
	CycleDay    int
	PointsBase  int
	PointsBonus int
	RuleVersion string
	RequestID   string // 小写 UUID 字符串
	CreatedAt   time.Time
}

// LedgerEntry 对应 points_ledger。
type LedgerEntry struct {
	ID           int64
	UserID       string
	Type         string
	Amount       int64
	BalanceAfter int64
	BizType      string
	BizID        string
	Remark       string
	CreatedAt    time.Time // 微秒精度，UTC
}

// Cursor 是流水游标 (created_at, id)；返回「严格排在它之后」的记录。
type Cursor struct {
	CreatedAt time.Time
	ID        int64
}

// Store 是存储接口。
type Store interface {
	// 在同一用户的写事务里执行 fn；内部先确保账户存在并锁住账户行；fn 返回 error 就回滚。
	WithUserTx(ctx context.Context, userID string, fn func(tx UserTx) error) error
	GetCheckinByDate(ctx context.Context, userID string, d civil.Date) (*CheckinRecord, error)
	GetLastCheckinBefore(ctx context.Context, userID string, d civil.Date) (*CheckinRecord, error)
	GetBalance(ctx context.Context, userID string) (balance int64, updatedAt *time.Time, err error)
	// ListLedger 按 created_at DESC, id DESC；调用方多取 1 条用来判断 has_more。
	ListLedger(ctx context.Context, userID string, after *Cursor, limit int) ([]LedgerEntry, error)
}

// UserTx 是同一用户的写事务视图。
type UserTx interface {
	Balance() int64
	FindByRequestID(requestID string) (*CheckinRecord, error)
	GetCheckinByDate(d civil.Date) (*CheckinRecord, error)
	GetLastCheckinBefore(d civil.Date) (*CheckinRecord, error)
	InsertCheckin(r *CheckinRecord) error // 冲突时返回 ErrConflict；成功后回填 ID、CreatedAt
	AppendLedger(e *LedgerEntry) error    // 成功后回填 ID、CreatedAt
	AddBalance(delta int64) (newBalance int64, err error)
	// LedgerByBiz 取某笔业务产生的流水（含本事务内未提交的），按 id 倒序。
	// 这是对技术方案 UserTx 接口的补充：重放 / already_checked_in 需要返回当天发放明细。
	LedgerByBiz(bizType, bizID string) ([]LedgerEntry, error)
}
