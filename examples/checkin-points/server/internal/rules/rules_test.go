package rules

import (
	"testing"

	"demoapp/server/internal/civil"
)

func TestCycleDay(t *testing.T) {
	cases := map[int]int{1: 1, 2: 2, 3: 3, 7: 7, 8: 1, 9: 2, 14: 7, 15: 1, 0: 1}
	for streak, want := range cases {
		if got := CycleDay(streak); got != want {
			t.Errorf("CycleDay(%d)=%d want %d", streak, got, want)
		}
	}
}

func TestPointsDefault(t *testing.T) {
	r, err := Default().Effective(civil.Date{Y: 2026, M: 11, D: 14})
	if err != nil {
		t.Fatal(err)
	}
	want := []int{10, 10, 20, 10, 10, 10, 40}
	for day := 1; day <= 7; day++ {
		base, bonus := Points(r, day)
		if base+bonus != want[day-1] {
			t.Errorf("day %d total=%d want %d", day, base+bonus, want[day-1])
		}
	}
}

func TestEffectiveSwitch(t *testing.T) {
	cfg, err := Parse([]byte(`{"versions":[
	 {"rule_version":"v2","effective_date":"2026-11-15","base_points":20,"streak_bonus":[0,0,10,0,0,0,30]},
	 {"rule_version":"v1","effective_date":"2026-01-01","base_points":10,"streak_bonus":[0,0,10,0,0,0,30]}]}`))
	if err != nil {
		t.Fatal(err)
	}
	r, _ := cfg.Effective(civil.Date{Y: 2026, M: 11, D: 14})
	if r.Version != "v1" {
		t.Errorf("11-14 want v1 got %s", r.Version)
	}
	r, _ = cfg.Effective(civil.Date{Y: 2026, M: 11, D: 15})
	if r.Version != "v2" {
		t.Errorf("11-15 want v2 got %s", r.Version)
	}
	if _, err := cfg.Effective(civil.Date{Y: 2025, M: 12, D: 31}); err == nil {
		t.Error("expected ErrNoRule before first effective date")
	}
}

func TestParseRejectsBadConfig(t *testing.T) {
	bad := []string{
		`{}`,
		`{"versions":[{"rule_version":"v1","effective_date":"2026-01-01","base_points":10,"streak_bonus":[0,0,10]}]}`,
		`{"versions":[{"rule_version":"v1","effective_date":"bad","base_points":10,"streak_bonus":[0,0,10,0,0,0,30]}]}`,
		`{"versions":[{"rule_version":"","effective_date":"2026-01-01","base_points":10,"streak_bonus":[0,0,10,0,0,0,30]}]}`,
	}
	for i, s := range bad {
		if _, err := Parse([]byte(s)); err == nil {
			t.Errorf("case %d should fail", i)
		}
	}
}
