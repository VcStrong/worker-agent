// Package rules 加载带版本的奖励规则，并提供纯函数 CycleDay / Points。
package rules

import (
	"encoding/json"
	"errors"
	"fmt"
	"os"
	"sort"

	"demoapp/server/internal/civil"
)

// ErrNoRule 表示没有生效日 <= 今天的规则版本。
var ErrNoRule = errors.New("rules: no effective rule version")

// Rule 是一个规则版本。
type Rule struct {
	Version       string
	EffectiveDate civil.Date
	BasePoints    int
	StreakBonus   [7]int // 下标 0 对应周期第 1 天
}

// Config 是按生效日升序排列的规则集合。
type Config struct {
	versions []Rule
}

type fileRule struct {
	RuleVersion   string `json:"rule_version"`
	EffectiveDate string `json:"effective_date"`
	BasePoints    int    `json:"base_points"`
	StreakBonus   []int  `json:"streak_bonus"`
}

type fileConfig struct {
	Versions []fileRule `json:"versions"`
}

const defaultJSON = `{"versions":[{"rule_version":"v1","effective_date":"2026-01-01","base_points":10,"streak_bonus":[0,0,10,0,0,0,30]}]}`

// Default 返回内置的 v1 规则（和 configs/rules.json 一致）。
func Default() *Config {
	c, err := Parse([]byte(defaultJSON))
	if err != nil {
		panic(err)
	}
	return c
}

// Load 从文件加载。
func Load(path string) (*Config, error) {
	b, err := os.ReadFile(path)
	if err != nil {
		return nil, fmt.Errorf("rules: read %s: %w", path, err)
	}
	return Parse(b)
}

// Parse 解析并校验 JSON。
func Parse(data []byte) (*Config, error) {
	var fc fileConfig
	if err := json.Unmarshal(data, &fc); err != nil {
		return nil, fmt.Errorf("rules: parse: %w", err)
	}
	if len(fc.Versions) == 0 {
		return nil, errors.New("rules: no versions")
	}
	out := make([]Rule, 0, len(fc.Versions))
	for _, fr := range fc.Versions {
		if fr.RuleVersion == "" {
			return nil, errors.New("rules: empty rule_version")
		}
		d, err := civil.Parse(fr.EffectiveDate)
		if err != nil {
			return nil, fmt.Errorf("rules: %s effective_date: %w", fr.RuleVersion, err)
		}
		if fr.BasePoints < 0 {
			return nil, fmt.Errorf("rules: %s base_points < 0", fr.RuleVersion)
		}
		if len(fr.StreakBonus) != 7 {
			return nil, fmt.Errorf("rules: %s streak_bonus must have 7 items", fr.RuleVersion)
		}
		r := Rule{Version: fr.RuleVersion, EffectiveDate: d, BasePoints: fr.BasePoints}
		for i, b := range fr.StreakBonus {
			if b < 0 {
				return nil, fmt.Errorf("rules: %s streak_bonus[%d] < 0", fr.RuleVersion, i)
			}
			r.StreakBonus[i] = b
		}
		out = append(out, r)
	}
	sort.Slice(out, func(i, j int) bool { return out[i].EffectiveDate.Before(out[j].EffectiveDate) })
	for i := 1; i < len(out); i++ {
		if out[i].EffectiveDate == out[i-1].EffectiveDate {
			return nil, fmt.Errorf("rules: duplicate effective_date %s", out[i].EffectiveDate)
		}
	}
	return &Config{versions: out}, nil
}

// Effective 返回生效日 <= d 的最新版本。
func (c *Config) Effective(d civil.Date) (Rule, error) {
	var found *Rule
	for i := range c.versions {
		if !d.Before(c.versions[i].EffectiveDate) {
			found = &c.versions[i]
		}
	}
	if found == nil {
		return Rule{}, ErrNoRule
	}
	return *found, nil
}

// CycleDay 把连签天数换成周期第几天（1–7）。streak < 1 按 1 处理。
func CycleDay(streak int) int {
	if streak < 1 {
		return 1
	}
	return (streak-1)%7 + 1
}

// Points 返回周期第 cycleDay 天的基础分和连签奖励。
func Points(r Rule, cycleDay int) (base, bonus int) {
	if cycleDay < 1 || cycleDay > 7 {
		cycleDay = CycleDay(cycleDay)
	}
	return r.BasePoints, r.StreakBonus[cycleDay-1]
}
