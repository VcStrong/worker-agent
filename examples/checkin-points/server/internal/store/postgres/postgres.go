//go:build pg

// Package postgres 是 store.Store 的 PostgreSQL 实现（pgx v5），只在 -tags pg 时编译。
// 注意：本机没有 Go / PG，这份实现 **未编译、未运行**；补测前先在 server/ 下执行
//
//	go get github.com/jackc/pgx/v5@latest && go mod tidy
package postgres

import (
	"context"
	"errors"
	"fmt"
	"time"

	"github.com/jackc/pgx/v5"
	"github.com/jackc/pgx/v5/pgconn"
	"github.com/jackc/pgx/v5/pgxpool"

	"demoapp/server/internal/civil"
	"demoapp/server/internal/store"
)

// Store 是 PG 存储。
type Store struct {
	pool *pgxpool.Pool
}

// New 连接数据库（DATABASE_URL 由环境变量注入，不要写进日志）。
func New(ctx context.Context, dsn string) (*Store, error) {
	pool, err := pgxpool.New(ctx, dsn)
	if err != nil {
		return nil, fmt.Errorf("postgres: connect: %w", err)
	}
	if err := pool.Ping(ctx); err != nil {
		pool.Close()
		return nil, fmt.Errorf("postgres: ping: %w", err)
	}
	return &Store{pool: pool}, nil
}

// Close 关闭连接池。
func (s *Store) Close() { s.pool.Close() }

// Ping 供 /readyz 使用。
func (s *Store) Ping(ctx context.Context) error { return s.pool.Ping(ctx) }

// mapErr 把 pg 错误映射成 store 的哨兵错误：23505 -> ErrConflict；拿锁 / 语句超时 / 连接问题 -> ErrUnavailable。
func mapErr(err error) error {
	if err == nil {
		return nil
	}
	var pgErr *pgconn.PgError
	if errors.As(err, &pgErr) {
		switch pgErr.Code {
		case "23505":
			return store.ErrConflict
		case "55P03", "57014", "40001", "40P01": // lock_not_available, query_canceled, serialization / deadlock
			return fmt.Errorf("%w: %s", store.ErrUnavailable, pgErr.Code)
		}
		return err
	}
	if errors.Is(err, context.DeadlineExceeded) || errors.Is(err, context.Canceled) {
		return fmt.Errorf("%w: %v", store.ErrUnavailable, err)
	}
	var connErr *pgconn.ConnectError
	if errors.As(err, &connErr) {
		return fmt.Errorf("%w: connect", store.ErrUnavailable)
	}
	return err
}

func dateParam(d civil.Date) time.Time { return d.Time() }

type querier interface {
	QueryRow(ctx context.Context, sql string, args ...any) pgx.Row
	Query(ctx context.Context, sql string, args ...any) (pgx.Rows, error)
}

const checkinCols = `id, checkin_date, streak_days, cycle_day, points_base, points_bonus, rule_version, request_id::text, created_at`

func scanCheckin(row pgx.Row, userID string) (*store.CheckinRecord, error) {
	var r store.CheckinRecord
	var date time.Time
	if err := row.Scan(&r.ID, &date, &r.StreakDays, &r.CycleDay, &r.PointsBase, &r.PointsBonus,
		&r.RuleVersion, &r.RequestID, &r.CreatedAt); err != nil {
		if errors.Is(err, pgx.ErrNoRows) {
			return nil, nil
		}
		return nil, mapErr(err)
	}
	r.UserID = userID
	r.CheckinDate = civil.FromTime(date)
	return &r, nil
}

func getCheckinByDate(ctx context.Context, q querier, userID string, d civil.Date) (*store.CheckinRecord, error) {
	return scanCheckin(q.QueryRow(ctx,
		`SELECT `+checkinCols+` FROM checkin_record WHERE user_id=$1 AND checkin_date=$2`,
		userID, dateParam(d)), userID)
}

func getLastCheckinBefore(ctx context.Context, q querier, userID string, d civil.Date) (*store.CheckinRecord, error) {
	return scanCheckin(q.QueryRow(ctx,
		`SELECT `+checkinCols+` FROM checkin_record WHERE user_id=$1 AND checkin_date < $2 ORDER BY checkin_date DESC LIMIT 1`,
		userID, dateParam(d)), userID)
}

const ledgerCols = `id, user_id, type, amount, balance_after, biz_type, biz_id, remark, created_at`

func scanLedger(rows pgx.Rows) ([]store.LedgerEntry, error) {
	defer rows.Close()
	var out []store.LedgerEntry
	for rows.Next() {
		var e store.LedgerEntry
		if err := rows.Scan(&e.ID, &e.UserID, &e.Type, &e.Amount, &e.BalanceAfter,
			&e.BizType, &e.BizID, &e.Remark, &e.CreatedAt); err != nil {
			return nil, mapErr(err)
		}
		e.CreatedAt = e.CreatedAt.UTC()
		out = append(out, e)
	}
	return out, mapErr(rows.Err())
}

// GetCheckinByDate 实现 store.Store。
func (s *Store) GetCheckinByDate(ctx context.Context, userID string, d civil.Date) (*store.CheckinRecord, error) {
	return getCheckinByDate(ctx, s.pool, userID, d)
}

// GetLastCheckinBefore 实现 store.Store。
func (s *Store) GetLastCheckinBefore(ctx context.Context, userID string, d civil.Date) (*store.CheckinRecord, error) {
	return getLastCheckinBefore(ctx, s.pool, userID, d)
}

// GetBalance 实现 store.Store；没有账户返回 0 和 nil。
func (s *Store) GetBalance(ctx context.Context, userID string) (int64, *time.Time, error) {
	var bal int64
	var updated time.Time
	err := s.pool.QueryRow(ctx, `SELECT balance, updated_at FROM points_account WHERE user_id=$1`, userID).Scan(&bal, &updated)
	if errors.Is(err, pgx.ErrNoRows) {
		return 0, nil, nil
	}
	if err != nil {
		return 0, nil, mapErr(err)
	}
	u := updated.UTC()
	return bal, &u, nil
}

// ListLedger 实现 store.Store：(created_at, id) 游标，倒序。
func (s *Store) ListLedger(ctx context.Context, userID string, after *store.Cursor, limit int) ([]store.LedgerEntry, error) {
	var rows pgx.Rows
	var err error
	if after == nil {
		rows, err = s.pool.Query(ctx,
			`SELECT `+ledgerCols+` FROM points_ledger WHERE user_id=$1 ORDER BY created_at DESC, id DESC LIMIT $2`,
			userID, limit)
	} else {
		rows, err = s.pool.Query(ctx,
			`SELECT `+ledgerCols+` FROM points_ledger WHERE user_id=$1 AND (created_at, id) < ($2, $3) ORDER BY created_at DESC, id DESC LIMIT $4`,
			userID, after.CreatedAt, after.ID, limit)
	}
	if err != nil {
		return nil, mapErr(err)
	}
	return scanLedger(rows)
}

// WithUserTx 实现 store.Store：READ COMMITTED；先建账户行，再 SELECT ... FOR UPDATE 锁住它，
// 把同一用户的签到串行化（D2）。fn 返回 error 或 panic 都会回滚。
func (s *Store) WithUserTx(ctx context.Context, userID string, fn func(tx store.UserTx) error) error {
	tx, err := s.pool.Begin(ctx)
	if err != nil {
		return mapErr(err)
	}
	defer func() { _ = tx.Rollback(ctx) }() // Commit 成功后 Rollback 是 no-op

	if _, err := tx.Exec(ctx, `SET LOCAL lock_timeout = '2s'`); err != nil {
		return mapErr(err)
	}
	if _, err := tx.Exec(ctx, `SET LOCAL statement_timeout = '3s'`); err != nil {
		return mapErr(err)
	}
	if _, err := tx.Exec(ctx, `INSERT INTO points_account(user_id) VALUES ($1) ON CONFLICT DO NOTHING`, userID); err != nil {
		return mapErr(err)
	}
	var bal int64
	if err := tx.QueryRow(ctx, `SELECT balance FROM points_account WHERE user_id=$1 FOR UPDATE`, userID).Scan(&bal); err != nil {
		return mapErr(err)
	}
	// CR P-05：now() 是事务开始时间，不代表写入顺序；拿到行锁后取 clock_timestamp()，
	// 同一用户的写入时间因此单调递增。同一事务内的几行共用这个时间。
	var ts time.Time
	if err := tx.QueryRow(ctx, `SELECT clock_timestamp()`).Scan(&ts); err != nil {
		return mapErr(err)
	}
	ut := &userTx{ctx: ctx, tx: tx, userID: userID, balance: bal, ts: ts}
	if err := fn(ut); err != nil {
		return err
	}
	return mapErr(tx.Commit(ctx))
}

type userTx struct {
	ctx     context.Context
	tx      pgx.Tx
	userID  string
	balance int64
	ts      time.Time // 拿到账户行锁之后的 clock_timestamp()，写入 created_at / updated_at
}

func (t *userTx) Balance() int64 { return t.balance }

func (t *userTx) FindByRequestID(requestID string) (*store.CheckinRecord, error) {
	return scanCheckin(t.tx.QueryRow(t.ctx,
		`SELECT `+checkinCols+` FROM checkin_record WHERE user_id=$1 AND request_id=$2::uuid`,
		t.userID, requestID), t.userID)
}

func (t *userTx) GetCheckinByDate(d civil.Date) (*store.CheckinRecord, error) {
	return getCheckinByDate(t.ctx, t.tx, t.userID, d)
}

func (t *userTx) GetLastCheckinBefore(d civil.Date) (*store.CheckinRecord, error) {
	return getLastCheckinBefore(t.ctx, t.tx, t.userID, d)
}

func (t *userTx) InsertCheckin(r *store.CheckinRecord) error {
	err := t.tx.QueryRow(t.ctx,
		`INSERT INTO checkin_record(user_id, checkin_date, streak_days, cycle_day, points_base, points_bonus, rule_version, request_id, created_at)
		 VALUES ($1,$2,$3,$4,$5,$6,$7,$8::uuid,$9) RETURNING id, created_at`,
		t.userID, dateParam(r.CheckinDate), r.StreakDays, r.CycleDay, r.PointsBase, r.PointsBonus, r.RuleVersion, r.RequestID, t.ts,
	).Scan(&r.ID, &r.CreatedAt)
	if err != nil {
		return mapErr(err)
	}
	r.UserID = t.userID
	return nil
}

func (t *userTx) AppendLedger(e *store.LedgerEntry) error {
	err := t.tx.QueryRow(t.ctx,
		`INSERT INTO points_ledger(user_id, type, amount, balance_after, biz_type, biz_id, remark, created_at)
		 VALUES ($1,$2,$3,$4,$5,$6,$7,$8) RETURNING id, created_at`,
		t.userID, e.Type, e.Amount, e.BalanceAfter, e.BizType, e.BizID, e.Remark, t.ts,
	).Scan(&e.ID, &e.CreatedAt)
	if err != nil {
		return mapErr(err)
	}
	e.UserID = t.userID
	e.CreatedAt = e.CreatedAt.UTC()
	return nil
}

func (t *userTx) AddBalance(delta int64) (int64, error) {
	var nb int64
	err := t.tx.QueryRow(t.ctx,
		`UPDATE points_account SET balance = balance + $2, updated_at = $3 WHERE user_id=$1 RETURNING balance`,
		t.userID, delta, t.ts).Scan(&nb)
	if err != nil {
		return 0, mapErr(err)
	}
	t.balance = nb
	return nb, nil
}

func (t *userTx) LedgerByBiz(bizType, bizID string) ([]store.LedgerEntry, error) {
	rows, err := t.tx.Query(t.ctx,
		`SELECT `+ledgerCols+` FROM points_ledger WHERE user_id=$1 AND biz_type=$2 AND biz_id=$3 ORDER BY id DESC`,
		t.userID, bizType, bizID)
	if err != nil {
		return nil, mapErr(err)
	}
	return scanLedger(rows)
}
