package analytics

import (
	"context"
	"database/sql"
	"sort"
	"time"

	"github.com/jmoiron/sqlx"
)

type AnalyticsWindow string

const (
	Window1Hour   AnalyticsWindow = "1h"
	Window24Hours AnalyticsWindow = "24h"
	Window7Days  AnalyticsWindow = "7d"
	Window30Days AnalyticsWindow = "30d"
)

type Analytics struct {
	TotalRequests     int64            `json:"total_requests"`
	RequestsPerSecond float64          `json:"requests_per_second"`
	ByStatus         map[string]int64 `json:"by_status"`
	ByPath           []PathCount       `json:"by_path"`
	ResponseTime     Percentiles      `json:"response_time"`
	TopIPs           []IPCount        `json:"top_ips"`
}

type Percentiles struct {
	P50 float64 `json:"p50"`
	P90 float64 `json:"p90"`
	P95 float64 `json:"p95"`
	P99 float64 `json:"p99"`
}

type PathCount struct {
	Path  string `json:"path"`
	Count int64  `json:"count"`
}

type IPCount struct {
	IP    string `json:"ip"`
	Count int64  `json:"count"`
}

type HourlyAnalytics struct {
	ID                int64   `db:"id"`
	Hour             string  `db:"hour"`
	Path             string  `db:"path"`
	RequestCount     int64   `db:"request_count"`
	AuthenticatedCount int64 `db:"authenticated_count"`
	Status2xx        int64   `db:"status_2xx"`
	Status3xx        int64   `db:"status_3xx"`
	Status4xx        int64   `db:"status_4xx"`
	Status5xx        int64   `db:"status_5xx"`
	AvgDurationMs    float64 `db:"avg_duration_ms"`
	MinDurationMs    *int64  `db:"min_duration_ms"`
	MaxDurationMs    *int64  `db:"max_duration_ms"`
	CreatedAt        string  `db:"created_at"`
	UpdatedAt        string  `db:"updated_at"`
}

type DailyAnalytics struct {
	ID                int64   `db:"id"`
	Date             string  `db:"date"`
	Path             string  `db:"path"`
	RequestCount     int64   `db:"request_count"`
	AuthenticatedCount int64 `db:"authenticated_count"`
	Status2xx        int64   `db:"status_2xx"`
	Status3xx        int64   `db:"status_3xx"`
	Status4xx        int64   `db:"status_4xx"`
	Status5xx        int64   `db:"status_5xx"`
	AvgDurationMs    float64 `db:"avg_duration_ms"`
	MinDurationMs    *int64  `db:"min_duration_ms"`
	MaxDurationMs    *int64  `db:"max_duration_ms"`
	UniqueIPs        int64   `db:"unique_ips"`
	UniqueAPIKeys    int64   `db:"unique_api_keys"`
	CreatedAt        string  `db:"created_at"`
	UpdatedAt        string  `db:"updated_at"`
}

type AnalyticsService struct {
	db *sqlx.DB
}

func NewAnalyticsService(db *sqlx.DB) *AnalyticsService {
	return &AnalyticsService{db: db}
}

func (as *AnalyticsService) GetAnalytics(ctx context.Context, window AnalyticsWindow) (*Analytics, error) {
	startTime := as.getStartTime(window)

	query := `
	SELECT
		COUNT(*) as total_requests,
		COALESCE(SUM(CASE WHEN status_code >= 200 AND status_code < 300 THEN 1 ELSE 0 END), 0) as status_2xx,
		COALESCE(SUM(CASE WHEN status_code >= 300 AND status_code < 400 THEN 1 ELSE 0 END), 0) as status_3xx,
		COALESCE(SUM(CASE WHEN status_code >= 400 AND status_code < 500 THEN 1 ELSE 0 END), 0) as status_4xx,
		COALESCE(SUM(CASE WHEN status_code >= 500 THEN 1 ELSE 0 END), 0) as status_5xx,
		COALESCE(AVG(duration_ms), 0) as avg_duration
	FROM requests
	WHERE created_at >= ?`

	var result struct {
		TotalRequests int64
		Status2xx    int64
		Status3xx    int64
		Status4xx    int64
		Status5xx    int64
		AvgDuration  float64
	}

	err := as.db.GetContext(ctx, &result, query, startTime.Format(time.RFC3339))
	if err != nil {
		return nil, err
	}

	byPath, err := as.getPathCounts(ctx, startTime)
	if err != nil {
		return nil, err
	}

	topIPs, err := as.getTopIPs(ctx, startTime)
	if err != nil {
		return nil, err
	}

	percentiles, err := as.getPercentiles(ctx, startTime)
	if err != nil {
		return nil, err
	}

	duration := time.Since(startTime)
	rps := float64(result.TotalRequests) / duration.Seconds()

	return &Analytics{
		TotalRequests:     result.TotalRequests,
		RequestsPerSecond: rps,
		ByStatus: map[string]int64{
			"2xx": result.Status2xx,
			"3xx": result.Status3xx,
			"4xx": result.Status4xx,
			"5xx": result.Status5xx,
		},
		ByPath:       byPath,
		ResponseTime: percentiles,
		TopIPs:      topIPs,
	}, nil
}

func (as *AnalyticsService) getStartTime(window AnalyticsWindow) time.Time {
	now := time.Now().UTC()
	switch window {
	case Window1Hour:
		return now.Add(-1 * time.Hour)
	case Window24Hours:
		return now.Add(-24 * time.Hour)
	case Window7Days:
		return now.Add(-7 * 24 * time.Hour)
	case Window30Days:
		return now.Add(-30 * 24 * time.Hour)
	default:
		return now.Add(-1 * time.Hour)
	}
}

func (as *AnalyticsService) getPathCounts(ctx context.Context, since time.Time) ([]PathCount, error) {
	query := `
	SELECT path, COUNT(*) as count
	FROM requests
	WHERE created_at >= ?
	GROUP BY path
	ORDER BY count DESC
	LIMIT 10`

	rows, err := as.db.QueryContext(ctx, query, since.Format(time.RFC3339))
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	var results []PathCount
	for rows.Next() {
		var pc PathCount
		if err := rows.Scan(&pc.Path, &pc.Count); err != nil {
			return nil, err
		}
		results = append(results, pc)
	}

	return results, nil
}

func (as *AnalyticsService) getTopIPs(ctx context.Context, since time.Time) ([]IPCount, error) {
	query := `
	SELECT client_ip, COUNT(*) as count
	FROM requests
	WHERE created_at >= ? AND client_ip IS NOT NULL AND client_ip != ''
	GROUP BY client_ip
	ORDER BY count DESC
	LIMIT 10`

	rows, err := as.db.QueryContext(ctx, query, since.Format(time.RFC3339))
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	var results []IPCount
	for rows.Next() {
		var ipc IPCount
		if err := rows.Scan(&ipc.IP, &ipc.Count); err != nil {
			return nil, err
		}
		results = append(results, ipc)
	}

	return results, nil
}

func (as *AnalyticsService) getPercentiles(ctx context.Context, since time.Time) (Percentiles, error) {
	query := `
	SELECT duration_ms
	FROM requests
	WHERE created_at >= ? AND duration_ms IS NOT NULL
	ORDER BY duration_ms`

	rows, err := as.db.QueryContext(ctx, query, since.Format(time.RFC3339))
	if err != nil {
		return Percentiles{}, err
	}
	defer rows.Close()

	var durations []int64
	for rows.Next() {
		var d int64
		if err := rows.Scan(&d); err != nil {
			return Percentiles{}, err
		}
		durations = append(durations, d)
	}

	if len(durations) == 0 {
		return Percentiles{P50: 0, P90: 0, P95: 0, P99: 0}, nil
	}

	sort.Slice(durations, func(i, j int) bool {
		return durations[i] < durations[j]
	})

	n := len(durations)
	calc := func(p float64) float64 {
		idx := int(float64(n) * p)
		if idx >= n {
			idx = n - 1
		}
		return float64(durations[idx])
	}

	return Percentiles{
		P50: calc(0.50),
		P90: calc(0.90),
		P95: calc(0.95),
		P99: calc(0.99),
	}, nil
}

func (as *AnalyticsService) ComputeHourly(ctx context.Context, hour time.Time) error {
	hourStr := hour.Format("2006-01-02T15:00")

	query := `
	INSERT INTO analytics_hourly (
		hour, path,
		request_count, authenticated_count,
		status_2xx, status_3xx, status_4xx, status_5xx,
		avg_duration_ms, min_duration_ms, max_duration_ms,
		updated_at
	)
	SELECT
		strftime('%Y-%m-%dT%H:00', created_at) as hour,
		path,
		COUNT(*) as request_count,
		SUM(authenticated) as authenticated_count,
		SUM(CASE WHEN status_code >= 200 AND status_code < 300 THEN 1 ELSE 0 END) as status_2xx,
		SUM(CASE WHEN status_code >= 300 AND status_code < 400 THEN 1 ELSE 0 END) as status_3xx,
		SUM(CASE WHEN status_code >= 400 AND status_code < 500 THEN 1 ELSE 0 END) as status_4xx,
		SUM(CASE WHEN status_code >= 500 THEN 1 ELSE 0 END) as status_5xx,
		AVG(duration_ms) as avg_duration_ms,
		MIN(duration_ms) as min_duration_ms,
		MAX(duration_ms) as max_duration_ms,
		datetime('now')
	FROM requests
	WHERE created_at >= ? AND created_at < ?
	GROUP BY hour, path
	ON CONFLICT(hour, path) DO UPDATE SET
		request_count = excluded.request_count,
		authenticated_count = excluded.authenticated_count,
		status_2xx = excluded.status_2xx,
		status_3xx = excluded.status_3xx,
		status_4xx = excluded.status_4xx,
		status_5xx = excluded.status_5xx,
		avg_duration_ms = excluded.avg_duration_ms,
		min_duration_ms = excluded.min_duration_ms,
		max_duration_ms = excluded.max_duration_ms,
		updated_at = excluded.updated_at`

	hourStart := hour
	hourEnd := hour.Add(1 * time.Hour)

	_, err := as.db.ExecContext(ctx, query,
		hourStart.Format(time.RFC3339),
		hourEnd.Format(time.RFC3339))

	return err
}

func (as *AnalyticsService) GetHourlyAnalytics(ctx context.Context, path string, hours int) ([]HourlyAnalytics, error) {
	query := `
	SELECT * FROM analytics_hourly
	WHERE path = ?
	ORDER BY hour DESC
	LIMIT ?`

	var results []HourlyAnalytics
	err := as.db.SelectContext(ctx, &results, query, path, hours)
	if err == sql.ErrNoRows {
		return []HourlyAnalytics{}, nil
	}
	return results, err
}

func (as *AnalyticsService) GetDailyAnalytics(ctx context.Context, path string, days int) ([]DailyAnalytics, error) {
	query := `
	SELECT * FROM analytics_daily
	WHERE path = ?
	ORDER BY date DESC
	LIMIT ?`

	var results []DailyAnalytics
	err := as.db.SelectContext(ctx, &results, query, path, days)
	if err == sql.ErrNoRows {
		return []DailyAnalytics{}, nil
	}
	return results, err
}