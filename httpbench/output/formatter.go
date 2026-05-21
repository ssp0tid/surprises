package output

import (
	"encoding/json"
	"fmt"
	"time"

	"httpbench/config"
	"httpbench/metrics"
)

type Formatter interface {
	Format(stats *metrics.Stats, cfg *config.Config, duration time.Duration) string
}

type TextFormatter struct{}

func (f *TextFormatter) Format(stats *metrics.Stats, cfg *config.Config, duration time.Duration) string {
	rps := float64(stats.Completed) / duration.Seconds()

	output := fmt.Sprintf("Running %s test @ %s\n", formatDuration(duration), cfg.URL)
	output += fmt.Sprintf(" %d workers, %d requests completed\n", cfg.Concurrency, stats.Completed)
	output += fmt.Sprintf("\n")
	output += fmt.Sprintf("  RPS: %.2f\n", rps)
	output += fmt.Sprintf("  Latency:\n")
	output += fmt.Sprintf("    min: %s\n", formatDuration(stats.Latency.Min))
	output += fmt.Sprintf("    avg: %s\n", formatDuration(stats.Latency.Avg))
	output += fmt.Sprintf("    p50: %s\n", formatDuration(stats.Latency.P50))
	output += fmt.Sprintf("    p95: %s\n", formatDuration(stats.Latency.P95))
	output += fmt.Sprintf("    p99: %s\n", formatDuration(stats.Latency.P99))
	output += fmt.Sprintf("    max: %s\n", formatDuration(stats.Latency.Max))
	output += fmt.Sprintf("\n")

	if len(stats.StatusCodes) > 0 {
		output += fmt.Sprintf("  HTTP Status Codes:\n")
		total := float64(stats.Completed)
		for code, count := range stats.StatusCodes {
			pct := 0.0
			if total > 0 {
				pct = float64(count) / total * 100
			}
			output += fmt.Sprintf("    %d: %d (%.1f%%)\n", code, count, pct)
		}
		output += fmt.Sprintf("\n")
	}

	output += fmt.Sprintf("  Errors:\n")
	output += fmt.Sprintf("    connection errors: %d\n", stats.ConnectionErrs)
	output += fmt.Sprintf("    timeouts: %d\n", stats.Timeouts)
	output += fmt.Sprintf("    non-2xx: %d\n", stats.Non2xx)

	return output
}

type JSONFormatter struct{}

func (f *JSONFormatter) Format(stats *metrics.Stats, cfg *config.Config, duration time.Duration) string {
	rps := float64(stats.Completed) / duration.Seconds()

	data := map[string]interface{}{
		"test": map[string]interface{}{
			"url":              cfg.URL,
			"method":           cfg.Method,
			"concurrency":      cfg.Concurrency,
			"duration_seconds": duration.Seconds(),
			"timestamp":       time.Now().UTC().Format(time.RFC3339),
		},
		"summary": map[string]interface{}{
			"requests":  stats.Completed,
			"rps":       rps,
			"success":   stats.Completed - stats.ConnectionErrs - stats.Timeouts,
			"errors":    stats.ConnectionErrs + stats.Timeouts,
		},
		"latency": map[string]interface{}{
			"min_ms":  stats.Latency.Min.Milliseconds(),
			"avg_ms":  stats.Latency.Avg.Milliseconds(),
			"p50_ms":  stats.Latency.P50.Milliseconds(),
			"p95_ms":  stats.Latency.P95.Milliseconds(),
			"p99_ms":  stats.Latency.P99.Milliseconds(),
			"max_ms":  stats.Latency.Max.Milliseconds(),
		},
		"status_codes": stats.StatusCodes,
		"errors": map[string]interface{}{
			"connection_errors": stats.ConnectionErrs,
			"timeouts":          stats.Timeouts,
			"non_2xx":           stats.Non2xx,
		},
	}

	jsonBytes, err := json.MarshalIndent(data, "", "  ")
	if err != nil {
		return fmt.Sprintf(`{"error": "failed to format JSON: %v"}`, err)
	}

	return string(jsonBytes)
}

func formatDuration(d time.Duration) string {
	if d < time.Millisecond {
		return fmt.Sprintf("%.0fus", float64(d.Microseconds()))
	}
	if d < time.Second {
		return fmt.Sprintf("%.0fms", float64(d.Milliseconds()))
	}
	return fmt.Sprintf("%.2fs", d.Seconds())
}

func GetFormatter(cfg *config.Config) Formatter {
	if cfg.IsJSON() {
		return &JSONFormatter{}
	}
	return &TextFormatter{}
}