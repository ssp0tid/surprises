package utils

import (
	"fmt"
	"math"
	"time"
)

func FormatBytes(bytes uint64) string {
	if bytes == 0 {
		return "0 B"
	}

	const unit = 1024
	units := []string{"B", "KB", "MB", "GB", "TB", "PB"}
	i := 0
	f := float64(bytes)

	for f >= unit && i < len(units)-1 {
		f /= unit
		i++
	}

	return fmt.Sprintf("%.1f %s", f, units[i])
}

func FormatPercent(percent float64) string {
	return fmt.Sprintf("%.1f%%", percent)
}

func FormatDuration(d time.Duration) string {
	d = d.Round(time.Second)
	h := d / time.Hour
	d -= h * time.Hour
	m := d / time.Minute
	d -= m * time.Minute
	s := d / time.Second

	if h > 0 {
		return fmt.Sprintf("%dh%dm%ds", h, m, s)
	}
	if m > 0 {
		return fmt.Sprintf("%dm%ds", m, s)
	}
	return fmt.Sprintf("%ds", s)
}

func FormatUptime(d time.Duration) string {
	return FormatDuration(d)
}

func Truncate(s string, maxLen int) string {
	if len(s) <= maxLen {
		return s
	}
	return s[:maxLen-3] + "..."
}

func Duration(t time.Time) time.Duration {
	return time.Since(t)
}