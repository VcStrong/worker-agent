// Package civil 是一个不带时区的日期类型（北京时间自然日），不引入第三方包。
package civil

import (
	"fmt"
	"time"
)

// Date 是年月日，可比较，可以当 map 的 key。
type Date struct {
	Y int
	M time.Month
	D int
}

// FromTime 取 t 所在时区的年月日（调用方负责先转成 UTC+8）。
func FromTime(t time.Time) Date {
	y, m, d := t.Date()
	return Date{Y: y, M: m, D: d}
}

// Time 返回该日 00:00 UTC，仅用于日期运算。
func (d Date) Time() time.Time {
	return time.Date(d.Y, d.M, d.D, 0, 0, 0, 0, time.UTC)
}

// AddDays 加减天数。
func (d Date) AddDays(n int) Date {
	return FromTime(d.Time().AddDate(0, 0, n))
}

// Before 判断 d 是否早于 o。
func (d Date) Before(o Date) bool {
	return d.Time().Before(o.Time())
}

// IsZero 判断是否零值。
func (d Date) IsZero() bool {
	return d.Y == 0 && d.M == 0 && d.D == 0
}

// String 返回 yyyy-MM-dd。
func (d Date) String() string {
	return fmt.Sprintf("%04d-%02d-%02d", d.Y, int(d.M), d.D)
}

// Parse 解析 yyyy-MM-dd。
func Parse(s string) (Date, error) {
	t, err := time.Parse("2006-01-02", s)
	if err != nil {
		return Date{}, err
	}
	return FromTime(t), nil
}
