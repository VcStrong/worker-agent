package httpapi

import (
	"strconv"
	"time"

	"demoapp/server/internal/service"
	"demoapp/server/internal/store"
)

// 以下 DTO 严格对应技术方案「接口契约」，字段名 snake_case。

type cycleCellDTO struct {
	Day         int  `json:"day"`
	PointsTotal int  `json:"points_total"`
	BonusPoints int  `json:"bonus_points"`
	Checked     bool `json:"checked"`
	IsToday     bool `json:"is_today"`
}

type checkinStatusDTO struct {
	ServerDate            string         `json:"server_date"`
	Timezone              string         `json:"timezone"`
	CheckedToday          bool           `json:"checked_today"`
	CanCheckin            bool           `json:"can_checkin"`
	AccountStatus         string         `json:"account_status"`
	StreakState           string         `json:"streak_state"`
	StreakDays            int            `json:"streak_days"`
	CycleDay              int            `json:"cycle_day"`
	TodayPointsPreview    int            `json:"today_points_preview"`
	TomorrowPointsPreview int            `json:"tomorrow_points_preview"`
	RuleVersion           string         `json:"rule_version"`
	Cycle                 []cycleCellDTO `json:"cycle"`
}

type ledgerItemDTO struct {
	ID           string `json:"id"`
	Type         string `json:"type"`
	Amount       int64  `json:"amount"`
	BalanceAfter int64  `json:"balance_after"`
	BizType      string `json:"biz_type"`
	BizID        string `json:"biz_id"`
	Remark       string `json:"remark"`
	CreatedAt    string `json:"created_at"`
}

type checkinResultDTO struct {
	CheckinDate string          `json:"checkin_date"`
	StreakDays  int             `json:"streak_days"`
	CycleDay    int             `json:"cycle_day"`
	PointsBase  int             `json:"points_base"`
	PointsBonus int             `json:"points_bonus"`
	PointsTotal int             `json:"points_total"`
	Balance     int64           `json:"balance"`
	RuleVersion string          `json:"rule_version"`
	Ledger      []ledgerItemDTO `json:"ledger"`
}

type balanceDTO struct {
	Balance   int64   `json:"balance"`
	UpdatedAt *string `json:"updated_at"`
}

type ledgerPageDTO struct {
	Items      []ledgerItemDTO `json:"items"`
	HasMore    bool            `json:"has_more"`
	NextCursor *string         `json:"next_cursor"`
}

// fmtTime 输出 RFC 3339 UTC，微秒精度，例如 2026-11-14T01:12:00.123456Z。
func fmtTime(t time.Time) string {
	return t.UTC().Format("2006-01-02T15:04:05.000000Z")
}

func toLedgerItem(e store.LedgerEntry) ledgerItemDTO {
	return ledgerItemDTO{
		ID:           strconv.FormatInt(e.ID, 10),
		Type:         e.Type,
		Amount:       e.Amount,
		BalanceAfter: e.BalanceAfter,
		BizType:      e.BizType,
		BizID:        e.BizID,
		Remark:       e.Remark,
		CreatedAt:    fmtTime(e.CreatedAt),
	}
}

func toLedgerItems(es []store.LedgerEntry) []ledgerItemDTO {
	out := make([]ledgerItemDTO, 0, len(es))
	for _, e := range es {
		out = append(out, toLedgerItem(e))
	}
	return out
}

func toStatusDTO(v *service.StatusView) checkinStatusDTO {
	acct := "active"
	if v.Restricted {
		acct = "restricted"
	}
	cells := make([]cycleCellDTO, 0, len(v.Cycle))
	for _, c := range v.Cycle {
		cells = append(cells, cycleCellDTO{
			Day: c.Day, PointsTotal: c.PointsTotal, BonusPoints: c.BonusPoints,
			Checked: c.Checked, IsToday: c.IsToday,
		})
	}
	return checkinStatusDTO{
		ServerDate:            v.ServerDate.String(),
		Timezone:              "Asia/Shanghai",
		CheckedToday:          v.CheckedToday,
		CanCheckin:            v.CanCheckin,
		AccountStatus:         acct,
		StreakState:           v.StreakState,
		StreakDays:            v.StreakDays,
		CycleDay:              v.CycleDay,
		TodayPointsPreview:    v.TodayPreview,
		TomorrowPointsPreview: v.TomorrowPreview,
		RuleVersion:           v.RuleVersion,
		Cycle:                 cells,
	}
}

func toResultDTO(r *service.CheckinResult) checkinResultDTO {
	return checkinResultDTO{
		CheckinDate: r.Date.String(),
		StreakDays:  r.StreakDays,
		CycleDay:    r.CycleDay,
		PointsBase:  r.PointsBase,
		PointsBonus: r.PointsBonus,
		PointsTotal: r.PointsTotal,
		Balance:     r.Balance,
		RuleVersion: r.RuleVersion,
		Ledger:      toLedgerItems(r.Ledger),
	}
}
