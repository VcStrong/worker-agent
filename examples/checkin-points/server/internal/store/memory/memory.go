// Package memory 是 store.Store 的内存实现：每个用户一把写锁（模拟 PG 的账户行锁），
// 事务内先写缓冲区，提交时才落地，回滚就丢弃；模拟三道唯一约束。
package memory

import (
	"context"
	"errors"
	"fmt"
	"sort"
	"sync"
	"time"

	"demoapp/server/internal/civil"
	"demoapp/server/internal/store"
)

// Store 是内存存储。
type Store struct {
	mu            sync.Mutex // 保护 users、id 计数器和 now
	users         map[string]*userState
	nextCheckinID int64
	nextLedgerID  int64
	now           func() time.Time
}

type userState struct {
	txMu sync.Mutex   // 串行化同一用户的写事务
	mu   sync.RWMutex // 保护下面的已提交数据

	balance    int64
	updatedAt  *time.Time
	byDate     map[civil.Date]*store.CheckinRecord
	byReq      map[string]*store.CheckinRecord
	ledger     []store.LedgerEntry
	ledgerKeys map[string]struct{}
}

var (
	_ store.Store  = (*Store)(nil)
	_ store.UserTx = (*tx)(nil)
)

// New 使用真实时间戳。
func New() *Store { return NewWithNow(time.Now) }

// NewWithNow 注入 created_at 的时间来源（测试用；调用发生在内部锁内，注入函数无需自己加锁）。
func NewWithNow(now func() time.Time) *Store {
	return &Store{users: make(map[string]*userState), now: now}
}

func (s *Store) user(id string) *userState {
	s.mu.Lock()
	defer s.mu.Unlock()
	u := s.users[id]
	if u == nil {
		u = &userState{
			byDate:     make(map[civil.Date]*store.CheckinRecord),
			byReq:      make(map[string]*store.CheckinRecord),
			ledgerKeys: make(map[string]struct{}),
		}
		s.users[id] = u
	}
	return u
}

func (s *Store) peek(id string) *userState {
	s.mu.Lock()
	defer s.mu.Unlock()
	return s.users[id]
}

func (s *Store) allocID(p *int64) int64 {
	s.mu.Lock()
	defer s.mu.Unlock()
	*p++
	return *p
}

func (s *Store) stamp() time.Time {
	s.mu.Lock()
	defer s.mu.Unlock()
	return s.now().UTC().Truncate(time.Microsecond)
}

func ledgerKey(bizType, bizID, typ string) string {
	return bizType + "|" + bizID + "|" + typ
}

func lastBefore(m map[civil.Date]*store.CheckinRecord, d civil.Date, best *store.CheckinRecord) *store.CheckinRecord {
	for date, rec := range m {
		if !date.Before(d) {
			continue
		}
		if best == nil || best.CheckinDate.Before(date) {
			best = rec
		}
	}
	return best
}

// WithUserTx 实现 store.Store。
func (s *Store) WithUserTx(ctx context.Context, userID string, fn func(tx store.UserTx) error) error {
	if err := ctx.Err(); err != nil {
		return fmt.Errorf("%w: %v", store.ErrUnavailable, err)
	}
	u := s.user(userID)
	u.txMu.Lock()
	defer u.txMu.Unlock()
	t := &tx{s: s, u: u, userID: userID, keys: make(map[string]struct{})}
	if err := fn(t); err != nil {
		return err // 缓冲区直接丢弃 = 回滚
	}
	t.commit()
	return nil
}

// GetCheckinByDate 实现 store.Store。
func (s *Store) GetCheckinByDate(_ context.Context, userID string, d civil.Date) (*store.CheckinRecord, error) {
	u := s.peek(userID)
	if u == nil {
		return nil, nil
	}
	u.mu.RLock()
	defer u.mu.RUnlock()
	if rec, ok := u.byDate[d]; ok {
		cp := *rec
		return &cp, nil
	}
	return nil, nil
}

// GetLastCheckinBefore 实现 store.Store。
func (s *Store) GetLastCheckinBefore(_ context.Context, userID string, d civil.Date) (*store.CheckinRecord, error) {
	u := s.peek(userID)
	if u == nil {
		return nil, nil
	}
	u.mu.RLock()
	defer u.mu.RUnlock()
	best := lastBefore(u.byDate, d, nil)
	if best == nil {
		return nil, nil
	}
	cp := *best
	return &cp, nil
}

// GetBalance 实现 store.Store；没有账户返回 0 和 nil。
func (s *Store) GetBalance(_ context.Context, userID string) (int64, *time.Time, error) {
	u := s.peek(userID)
	if u == nil {
		return 0, nil, nil
	}
	u.mu.RLock()
	defer u.mu.RUnlock()
	if u.updatedAt == nil {
		return u.balance, nil, nil
	}
	t := *u.updatedAt
	return u.balance, &t, nil
}

func entryLess(e store.LedgerEntry, c store.Cursor) bool {
	if e.CreatedAt.Before(c.CreatedAt) {
		return true
	}
	return e.CreatedAt.Equal(c.CreatedAt) && e.ID < c.ID
}

// ListLedger 实现 store.Store。
func (s *Store) ListLedger(_ context.Context, userID string, after *store.Cursor, limit int) ([]store.LedgerEntry, error) {
	u := s.peek(userID)
	if u == nil {
		return nil, nil
	}
	u.mu.RLock()
	items := make([]store.LedgerEntry, 0, len(u.ledger))
	for _, e := range u.ledger {
		if after != nil && !entryLess(e, *after) {
			continue
		}
		items = append(items, e)
	}
	u.mu.RUnlock()
	sort.Slice(items, func(i, j int) bool {
		if !items[i].CreatedAt.Equal(items[j].CreatedAt) {
			return items[i].CreatedAt.After(items[j].CreatedAt)
		}
		return items[i].ID > items[j].ID
	})
	if limit > 0 && len(items) > limit {
		items = items[:limit]
	}
	return items, nil
}

// tx 是一次写事务；只在持有 u.txMu 的 goroutine 里使用。
type tx struct {
	s        *Store
	u        *userState
	userID   string
	delta    int64
	ts       time.Time
	checkins []*store.CheckinRecord
	ledger   []store.LedgerEntry
	keys     map[string]struct{}
}

func (t *tx) stamp() time.Time {
	if t.ts.IsZero() {
		t.ts = t.s.stamp()
	}
	return t.ts
}

func (t *tx) Balance() int64 {
	t.u.mu.RLock()
	b := t.u.balance
	t.u.mu.RUnlock()
	return b + t.delta
}

func (t *tx) FindByRequestID(requestID string) (*store.CheckinRecord, error) {
	for _, c := range t.checkins {
		if c.RequestID == requestID {
			cp := *c
			return &cp, nil
		}
	}
	t.u.mu.RLock()
	defer t.u.mu.RUnlock()
	if c, ok := t.u.byReq[requestID]; ok {
		cp := *c
		return &cp, nil
	}
	return nil, nil
}

func (t *tx) GetCheckinByDate(d civil.Date) (*store.CheckinRecord, error) {
	for _, c := range t.checkins {
		if c.CheckinDate == d {
			cp := *c
			return &cp, nil
		}
	}
	t.u.mu.RLock()
	defer t.u.mu.RUnlock()
	if c, ok := t.u.byDate[d]; ok {
		cp := *c
		return &cp, nil
	}
	return nil, nil
}

func (t *tx) GetLastCheckinBefore(d civil.Date) (*store.CheckinRecord, error) {
	var best *store.CheckinRecord
	for _, c := range t.checkins {
		if c.CheckinDate.Before(d) && (best == nil || best.CheckinDate.Before(c.CheckinDate)) {
			best = c
		}
	}
	t.u.mu.RLock()
	best = lastBefore(t.u.byDate, d, best)
	t.u.mu.RUnlock()
	if best == nil {
		return nil, nil
	}
	cp := *best
	return &cp, nil
}

func (t *tx) InsertCheckin(r *store.CheckinRecord) error {
	for _, c := range t.checkins {
		if c.CheckinDate == r.CheckinDate || c.RequestID == r.RequestID {
			return store.ErrConflict
		}
	}
	t.u.mu.RLock()
	_, dupDate := t.u.byDate[r.CheckinDate]
	_, dupReq := t.u.byReq[r.RequestID]
	t.u.mu.RUnlock()
	if dupDate || dupReq {
		return store.ErrConflict
	}
	r.ID = t.s.allocID(&t.s.nextCheckinID)
	r.UserID = t.userID
	r.CreatedAt = t.stamp()
	cp := *r
	t.checkins = append(t.checkins, &cp)
	return nil
}

func (t *tx) AppendLedger(e *store.LedgerEntry) error {
	key := ledgerKey(e.BizType, e.BizID, e.Type)
	if _, dup := t.keys[key]; dup {
		return store.ErrConflict
	}
	t.u.mu.RLock()
	_, dup := t.u.ledgerKeys[key]
	t.u.mu.RUnlock()
	if dup {
		return store.ErrConflict
	}
	if e.Amount == 0 {
		return errors.New("memory: ledger amount must be non-zero")
	}
	e.ID = t.s.allocID(&t.s.nextLedgerID)
	e.UserID = t.userID
	e.CreatedAt = t.stamp()
	t.keys[key] = struct{}{}
	t.ledger = append(t.ledger, *e)
	return nil
}

func (t *tx) AddBalance(delta int64) (int64, error) {
	nb := t.Balance() + delta
	if nb < 0 {
		return 0, errors.New("memory: balance would be negative")
	}
	t.delta += delta
	return nb, nil
}

func (t *tx) LedgerByBiz(bizType, bizID string) ([]store.LedgerEntry, error) {
	var out []store.LedgerEntry
	t.u.mu.RLock()
	for _, e := range t.u.ledger {
		if e.BizType == bizType && e.BizID == bizID {
			out = append(out, e)
		}
	}
	t.u.mu.RUnlock()
	for _, e := range t.ledger {
		if e.BizType == bizType && e.BizID == bizID {
			out = append(out, e)
		}
	}
	sort.Slice(out, func(i, j int) bool { return out[i].ID > out[j].ID })
	return out, nil
}

func (t *tx) commit() {
	var ts time.Time
	if t.delta != 0 {
		ts = t.stamp()
	}
	u := t.u
	u.mu.Lock()
	defer u.mu.Unlock()
	for _, c := range t.checkins {
		cp := *c
		u.byDate[c.CheckinDate] = &cp
		u.byReq[c.RequestID] = &cp
	}
	for _, e := range t.ledger {
		u.ledger = append(u.ledger, e)
		u.ledgerKeys[ledgerKey(e.BizType, e.BizID, e.Type)] = struct{}{}
	}
	if t.delta != 0 {
		u.balance += t.delta
		u.updatedAt = &ts
	}
}
