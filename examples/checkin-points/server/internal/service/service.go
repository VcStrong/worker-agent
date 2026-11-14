// Package service 实现签到用例：判日、连签计算、幂等、发分，以及状态、余额、流水查询。
// 只依赖 store 接口和 clock。
package service

import (
	"context"
	"errors"
	"io"
	"log/slog"
	"strconv"
	"time"

	"demoapp/server/internal/civil"
	"demoapp/server/internal/clock"
	"demoapp/server/internal/rules"
	"demoapp/server/internal/store"
)

// 业务码。
const (
	CodeOK      = "ok"
	CodeAlready = "already_checked_in"
)

// 连签状态。
const (
	StreakNone   = "NONE"
	StreakActive = "ACTIVE"
	StreakBroken = "BROKEN"
)

// Service 是签到服务。
type Service struct {
	st    store.Store
	clk   clock.Clock
	rules *rules.Config
	log   *slog.Logger
}

// New 创建服务；log 为 nil 时丢弃日志。
func New(st store.Store, clk clock.Clock, cfg *rules.Config, log *slog.Logger) *Service {
	if log == nil {
		log = slog.New(slog.NewTextHandler(io.Discard, nil))
	}
	return &Service{st: st, clk: clk, rules: cfg, log: log}
}

// CheckinResult 对应契约 CheckinResult；Code 是 ok / already_checked_in。
type CheckinResult struct {
	Code        string
	Date        civil.Date
	StreakDays  int
	CycleDay    int
	PointsBase  int
	PointsBonus int
	PointsTotal int
	Balance     int64
	RuleVersion string
	Ledger      []store.LedgerEntry
}

// CheckIn 执行签到，流程严格对应技术方案「签到事务流程」。
func (s *Service) CheckIn(ctx context.Context, userID, requestID string) (*CheckinResult, error) {
	var lastErr error
	// 撞唯一约束（理论上被账户行锁挡住，这里是兜底）时整笔回滚后重查一次，走重放 / already 分支。
	for attempt := 0; attempt < 2; attempt++ {
		var res *CheckinResult
		var isNew bool
		err := s.st.WithUserTx(ctx, userID, func(tx store.UserTx) error {
			// CR P-01：「今天」和规则版本必须在拿到账户锁之后再算，
			// 这样后拿到锁的请求一定看得到前序已提交的记录，跨零点乱序不会误判断签。
			today := clock.Today(s.clk)
			rule, e := s.rules.Effective(today)
			if e != nil {
				return e
			}
			res, isNew, e = s.checkInTx(tx, userID, requestID, today, rule)
			return e
		})
		if err == nil {
			if isNew {
				s.emit(userID, requestID, res)
			}
			return res, nil
		}
		if !errors.Is(err, store.ErrConflict) {
			return nil, err
		}
		lastErr = err
	}
	return nil, lastErr
}

func (s *Service) checkInTx(tx store.UserTx, userID, requestID string, today civil.Date, rule rules.Rule) (*CheckinResult, bool, error) {
	// 步骤 4：同 request_id 原样重放（含跨零点重试）。
	rec, err := tx.FindByRequestID(requestID)
	if err != nil {
		return nil, false, err
	}
	if rec != nil {
		res, err := buildResult(tx, rec, CodeOK)
		return res, false, err
	}
	// 步骤 5：今天已签。
	rec, err = tx.GetCheckinByDate(today)
	if err != nil {
		return nil, false, err
	}
	if rec != nil {
		res, err := buildResult(tx, rec, CodeAlready)
		return res, false, err
	}
	// 步骤 6：连签计算。
	last, err := tx.GetLastCheckinBefore(today)
	if err != nil {
		return nil, false, err
	}
	streak := 1
	if last != nil && last.CheckinDate == today.AddDays(-1) {
		streak = last.StreakDays + 1
	}
	cycleDay := rules.CycleDay(streak)
	base, bonus := rules.Points(rule, cycleDay)

	// 步骤 7：插入签到记录。
	rec = &store.CheckinRecord{
		UserID:      userID,
		CheckinDate: today,
		StreakDays:  streak,
		CycleDay:    cycleDay,
		PointsBase:  base,
		PointsBonus: bonus,
		RuleVersion: rule.Version,
		RequestID:   requestID,
	}
	if err := tx.InsertCheckin(rec); err != nil {
		return nil, false, err
	}
	// 步骤 8：流水（基础一条，有奖励再加一条，奖励的 id 更大所以排在上面）。
	bizID := strconv.FormatInt(rec.ID, 10)
	bal := tx.Balance()
	if base > 0 {
		bal += int64(base)
		e := &store.LedgerEntry{Type: store.TypeCheckinBase, Amount: int64(base), BalanceAfter: bal,
			BizType: store.BizCheckin, BizID: bizID, Remark: "每日签到"}
		if err := tx.AppendLedger(e); err != nil {
			return nil, false, err
		}
	}
	if bonus > 0 {
		bal += int64(bonus)
		e := &store.LedgerEntry{Type: store.TypeCheckinStreakBonus, Amount: int64(bonus), BalanceAfter: bal,
			BizType: store.BizCheckin, BizID: bizID, Remark: "连续签到奖励"}
		if err := tx.AppendLedger(e); err != nil {
			return nil, false, err
		}
	}
	// 步骤 9：余额。
	if total := int64(base + bonus); total > 0 {
		if _, err := tx.AddBalance(total); err != nil {
			return nil, false, err
		}
	}
	res, err := buildResult(tx, rec, CodeOK)
	return res, true, err
}

func buildResult(tx store.UserTx, rec *store.CheckinRecord, code string) (*CheckinResult, error) {
	items, err := tx.LedgerByBiz(store.BizCheckin, strconv.FormatInt(rec.ID, 10))
	if err != nil {
		return nil, err
	}
	return &CheckinResult{
		Code:        code,
		Date:        rec.CheckinDate,
		StreakDays:  rec.StreakDays,
		CycleDay:    rec.CycleDay,
		PointsBase:  rec.PointsBase,
		PointsBonus: rec.PointsBonus,
		PointsTotal: rec.PointsBase + rec.PointsBonus,
		Balance:     tx.Balance(),
		RuleVersion: rec.RuleVersion,
		Ledger:      items,
	}, nil
}

// emit 在事务提交后打服务端埋点事件（checkin_success / points_grant）。
func (s *Service) emit(userID, requestID string, res *CheckinResult) {
	s.log.Info("checkin_success",
		"event", "checkin_success",
		"user_id", userID,
		"checkin_date", res.Date.String(),
		"streak_days", res.StreakDays,
		"cycle_day", res.CycleDay,
		"points_base", res.PointsBase,
		"points_bonus", res.PointsBonus,
		"rule_version", res.RuleVersion,
		"request_id", requestID)
	for _, e := range res.Ledger {
		s.log.Info("points_grant",
			"event", "points_grant",
			"user_id", userID,
			"type", e.Type,
			"amount", e.Amount,
			"balance_after", e.BalanceAfter,
			"biz_id", e.BizID)
	}
}

// Cell 是 7 天周期的一个格子。
type Cell struct {
	Day         int
	PointsTotal int
	BonusPoints int
	Checked     bool
	IsToday     bool
}

// StatusView 对应契约 CheckinStatus。
type StatusView struct {
	ServerDate      civil.Date
	CheckedToday    bool
	CanCheckin      bool
	Restricted      bool
	StreakState     string
	StreakDays      int
	CycleDay        int
	TodayPreview    int
	TomorrowPreview int
	RuleVersion     string
	Cycle           []Cell
}

// Status 计算签到状态（只读，不加锁）。
func (s *Service) Status(ctx context.Context, userID string, restricted bool) (*StatusView, error) {
	today := clock.Today(s.clk)
	rule, err := s.rules.Effective(today)
	if err != nil {
		return nil, err
	}
	rec, err := s.st.GetCheckinByDate(ctx, userID, today)
	if err != nil {
		return nil, err
	}
	v := &StatusView{ServerDate: today, Restricted: restricted, RuleVersion: rule.Version}
	var anchor *store.CheckinRecord // 本周期里最近的一条已签记录
	checkedUpTo := 0
	if rec != nil {
		anchor = rec
		v.CheckedToday = true
		v.StreakState = StreakActive
		v.StreakDays = rec.StreakDays
		v.CycleDay = rec.CycleDay
		v.TodayPreview = rec.PointsBase + rec.PointsBonus
		checkedUpTo = rec.CycleDay
	} else {
		last, err := s.st.GetLastCheckinBefore(ctx, userID, today)
		if err != nil {
			return nil, err
		}
		switch {
		case last == nil:
			v.StreakState = StreakNone
			v.CycleDay = 1
		case last.CheckinDate == today.AddDays(-1):
			anchor = last
			v.StreakState = StreakActive
			v.StreakDays = last.StreakDays
			v.CycleDay = last.StreakDays%7 + 1
			checkedUpTo = v.CycleDay - 1
		default:
			v.StreakState = StreakBroken
			v.CycleDay = 1
		}
		base, bonus := rules.Points(rule, v.CycleDay)
		v.TodayPreview = base + bonus
	}
	nb, nbo := rules.Points(rule, v.CycleDay%7+1)
	v.TomorrowPreview = nb + nbo
	v.CanCheckin = !v.CheckedToday && !restricted

	v.Cycle = make([]Cell, 0, 7)
	for i := 1; i <= 7; i++ {
		base, bonus := rules.Points(rule, i)
		cell := Cell{Day: i, Checked: i <= checkedUpTo, IsToday: i == v.CycleDay}
		if cell.Checked && anchor != nil {
			// R5：已签格子取记录里的实际值，不随规则变更。
			var actual *store.CheckinRecord
			if i == anchor.CycleDay {
				actual = anchor
			} else {
				d := anchor.CheckinDate.AddDays(-(anchor.CycleDay - i))
				actual, err = s.st.GetCheckinByDate(ctx, userID, d)
				if err != nil {
					return nil, err
				}
			}
			if actual != nil {
				base, bonus = actual.PointsBase, actual.PointsBonus
			}
		}
		cell.PointsTotal = base + bonus
		cell.BonusPoints = bonus
		v.Cycle = append(v.Cycle, cell)
	}
	return v, nil
}

// Balance 返回余额和更新时间；新用户返回 0 和 nil。
func (s *Service) Balance(ctx context.Context, userID string) (int64, *time.Time, error) {
	return s.st.GetBalance(ctx, userID)
}

// Ledger 返回一页流水（最多 limit 条）和是否还有更多；after 为 nil 表示首页。
func (s *Service) Ledger(ctx context.Context, userID string, after *store.Cursor, limit int) ([]store.LedgerEntry, bool, error) {
	items, err := s.st.ListLedger(ctx, userID, after, limit+1)
	if err != nil {
		return nil, false, err
	}
	more := len(items) > limit
	if more {
		items = items[:limit]
	}
	return items, more, nil
}
