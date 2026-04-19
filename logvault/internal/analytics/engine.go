package analytics

import (
	"context"
	"time"

	"github.com/logvault/logvault/internal/db"
	"github.com/logvault/logvault/internal/model"
)

type Engine struct {
	db *db.DB
}

func NewEngine(database *db.DB) *Engine {
	return &Engine{db: database}
}

func (e *Engine) Summary(ctx context.Context) (*model.AnalyticsSummary, error) {
	total, err := e.db.CountLogs(ctx, db.LogFilter{})
	if err != nil {
		return nil, err
	}

	last24h := time.Now().Add(-24 * time.Hour)
	count24h, err := e.db.CountLogs(ctx, db.LogFilter{From: last24h})
	if err != nil {
		return nil, err
	}

	errorCount, err := e.db.CountLogs(ctx, db.LogFilter{Level: "ERROR"})
	if err != nil {
		return nil, err
	}

	var errorRate float64
	if count24h > 0 {
		errorRate = float64(errorCount) / float64(count24h) * 100
	}

	services, err := e.db.GetServices(ctx)
	if err != nil {
		return nil, err
	}

	oldest, newest, err := e.db.GetTimeRange(ctx)
	if err != nil {
		return nil, err
	}

	return &model.AnalyticsSummary{
		TotalLogs:   total,
		LogsLast24h:  count24h,
		ErrorCount:  errorCount,
		ErrorRate:   errorRate,
		Services:   services,
		TimeRange: model.TimeRange{
			Oldest: oldest,
			Newest: newest,
		},
	}, nil
}

func (e *Engine) Volume(ctx context.Context, interval string, from, to time.Time) (*model.AnalyticsVolume, error) {
	result, err := e.db.GetVolume(ctx, interval, from, to)
	if err != nil {
		return nil, err
	}

	return &model.AnalyticsVolume{
		Interval: interval,
		Data:     result,
	}, nil
}

func (e *Engine) LevelDistribution(ctx context.Context) (*model.AnalyticsLevelDistribution, error) {
	levels, err := e.db.GetLevelCounts(ctx)
	if err != nil {
		return nil, err
	}

	var total int64
	for _, l := range levels {
		total += l.Count
	}

	byCount := make([]model.AnalyticsLevelCount, 0, len(levels))
	byPercentage := make([]model.AnalyticsLevelCount, 0, len(levels))

	for _, l := range levels {
		percentage := float64(0)
		if total > 0 {
			percentage = float64(l.Count) / float64(total) * 100
		}

		byCount = append(byCount, model.AnalyticsLevelCount{
			Level:      l.Level,
			Count:      l.Count,
			Percentage: percentage,
		})

		byPercentage = append(byPercentage, model.AnalyticsLevelCount{
			Level:      l.Level,
			Count:      l.Count,
			Percentage: percentage,
		})
	}

	return &model.AnalyticsLevelDistribution{
		ByCount:      byCount,
		ByPercentage: byPercentage,
	}, nil
}

func (e *Engine) ServiceBreakdown(ctx context.Context, from, to time.Time) (*model.AnalyticsServiceBreakdown, error) {
	services, err := e.db.GetServiceBreakdown(ctx, from, to)
	if err != nil {
		return nil, err
	}

	data := make([]model.AnalyticsServiceCount, 0, len(services))
	for _, s := range services {
		data = append(data, model.AnalyticsServiceCount{
			Service: s.Service,
			Total:   s.Total,
			Errors:  s.Errors,
		})
	}

	return &model.AnalyticsServiceBreakdown{Data: data}, nil
}