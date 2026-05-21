package metrics

import (
	"sort"
	"sync"
	"sync/atomic"
	"time"
)

type Collector struct {
	mu              sync.Mutex
	latencies       []time.Duration
	statusCodes     map[int]int
	connectionErrs  int64
	timeouts        int64
	non2xx          int64

	totalRequests   int64
	completed       int64

	sortedLatencies []time.Duration
	sortedOnce      sync.Once
}

func NewCollector() *Collector {
	return &Collector{
		latencies:   make([]time.Duration, 0, 10000),
		statusCodes: make(map[int]int),
	}
}

func (c *Collector) Record(result *RequestResult) {
	atomic.AddInt64(&c.completed, 1)

	if result.HasError {
		atomic.AddInt64(&c.totalRequests, 1)
		
		if result.IsTimeout {
			atomic.AddInt64(&c.timeouts, 1)
		} else {
			atomic.AddInt64(&c.connectionErrs, 1)
		}
		return
	}

	c.mu.Lock()
	c.latencies = append(c.latencies, result.Latency)
	c.statusCodes[result.StatusCode]++
	c.mu.Unlock()

	atomic.AddInt64(&c.totalRequests, 1)

	if result.StatusCode < 200 || result.StatusCode >= 300 {
		atomic.AddInt64(&c.non2xx, 1)
	}
}

func (c *Collector) GetStats() *Stats {
	c.mu.Lock()
	defer c.mu.Unlock()

	c.sortedOnce.Do(func() {
		if len(c.latencies) > 0 {
			c.sortedLatencies = make([]time.Duration, len(c.latencies))
			copy(c.sortedLatencies, c.latencies)
			sort.Slice(c.sortedLatencies, func(i, j int) bool {
				return c.sortedLatencies[i] < c.sortedLatencies[j]
			})
		}
	})

	stats := &Stats{
		TotalRequests:  atomic.LoadInt64(&c.totalRequests),
		Completed:      atomic.LoadInt64(&c.completed),
		ConnectionErrs: atomic.LoadInt64(&c.connectionErrs),
		Timeouts:       atomic.LoadInt64(&c.timeouts),
		Non2xx:         atomic.LoadInt64(&c.non2xx),
		StatusCodes:    make(map[int]int),
	}

	for k, v := range c.statusCodes {
		stats.StatusCodes[k] = v
	}

	if len(c.latencies) == 0 {
		return stats
	}

	var total time.Duration
	min := c.latencies[0]
	max := c.latencies[0]

	for _, lat := range c.latencies {
		total += lat
		if lat < min {
			min = lat
		}
		if lat > max {
			max = lat
		}
	}

	avg := total / time.Duration(len(c.latencies))

	stats.Latency = LatencyStats{
		Min: min,
		Avg: avg,
		P50: percentile(c.sortedLatencies, 50),
		P95: percentile(c.sortedLatencies, 95),
		P99: percentile(c.sortedLatencies, 99),
		Max: max,
	}

	return stats
}

func percentile(sorted []time.Duration, p int) time.Duration {
	if len(sorted) == 0 {
		return 0
	}
	idx := int(float64(len(sorted)) * float64(p) / 100.0)
	if idx >= len(sorted) {
		idx = len(sorted) - 1
	}
	if idx < 0 {
		idx = 0
	}
	return sorted[idx]
}

type RequestResult struct {
	StatusCode int
	Latency    time.Duration
	HasError   bool
	IsTimeout  bool
	ErrorMsg   string
}

type LatencyStats struct {
	Min  time.Duration
	Avg  time.Duration
	P50  time.Duration
	P95  time.Duration
	P99  time.Duration
	Max  time.Duration
}

type Stats struct {
	TotalRequests   int64
	Completed       int64
	ConnectionErrs  int64
	Timeouts        int64
	Non2xx          int64
	StatusCodes     map[int]int
	Latency         LatencyStats
}