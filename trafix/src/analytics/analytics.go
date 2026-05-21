package analytics

import (
	"context"
	"sync"
	"time"

	"github.com/rs/zerolog"

	"trafix/config"
	"trafix/utils"
)

type Analytics struct {
	config *config.Config
	logger zerolog.Logger

	mu             sync.RWMutex
	totalRequests  int64
	totalResponses int64
	errorCount     int64
	requestTimes   []time.Duration
	startTime     time.Time
}

type Metrics struct {
	TotalRequests   int64         `json:"total_requests"`
	TotalResponses int64         `json:"total_responses"`
	ErrorCount     int64         `json:"error_count"`
	Uptime         time.Duration `json:"uptime"`
	AvgResponseTime time.Duration `json:"avg_response_time"`
	RequestsPerSecond float64     `json:"requests_per_second"`
}

func NewAnalytics(cfg *config.Config) *Analytics {
	return &Analytics{
		config:     cfg,
		logger:    utils.GetLogger(),
		startTime: time.Now(),
	}
}

func (a *Analytics) RecordRequest() {
	a.mu.Lock()
	defer a.mu.Unlock()
	a.totalRequests++
}

func (a *Analytics) RecordResponse(statusCode int) {
	a.mu.Lock()
	defer a.mu.Unlock()
	a.totalResponses++

	if statusCode >= 400 {
		a.errorCount++
	}
}

func (a *Analytics) RecordRequestTime(d time.Duration) {
	a.mu.Lock()
	defer a.mu.Unlock()

	a.requestTimes = append(a.requestTimes, d)
	if len(a.requestTimes) > 1000 {
		a.requestTimes = a.requestTimes[1:]
	}
}

func (a *Analytics) GetMetrics() Metrics {
	a.mu.RLock()
	defer a.mu.RUnlock()

	avgResponseTime := time.Millisecond * 0
	if len(a.requestTimes) > 0 {
		var total time.Duration
		for _, t := range a.requestTimes {
			total += t
		}
		avgResponseTime = total / time.Duration(len(a.requestTimes))
	}

	uptime := time.Since(a.startTime)
	rps := float64(a.totalRequests) / uptime.Seconds()

	return Metrics{
		TotalRequests:    a.totalRequests,
		TotalResponses: a.totalResponses,
		ErrorCount:     a.errorCount,
		Uptime:        uptime,
		AvgResponseTime: avgResponseTime,
		RequestsPerSecond: rps,
	}
}

func (a *Analytics) Reset() {
	a.mu.Lock()
	defer a.mu.Unlock()
	a.totalRequests = 0
	a.totalResponses = 0
	a.errorCount = 0
	a.requestTimes = nil
	a.startTime = time.Now()
}