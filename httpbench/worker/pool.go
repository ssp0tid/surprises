package worker

import (
	"context"
	"sync"
	"sync/atomic"
	"time"

	"httpbench/client"
	"httpbench/config"
	"httpbench/metrics"
)

type Pool struct {
	cfg       *config.Config
	client    *client.HTTPClient
	collector *metrics.Collector

	mu       sync.Mutex
	wg       sync.WaitGroup
	ctx      context.Context
	cancel   context.CancelFunc

	totalSent      int64
	targetRequests int64
	elapsed        time.Duration
}

func NewPool(cfg *config.Config, collector *metrics.Collector) *Pool {
	ctx, cancel := context.WithCancel(context.Background())
	
	p := &Pool{
		cfg:       cfg,
		client:    client.NewHTTPClient(cfg.Timeout),
		collector: collector,
		ctx:       ctx,
		cancel:    cancel,
	}

	if cfg.Requests > 0 {
		p.targetRequests = int64(cfg.Requests)
	}

	return p
}

func (p *Pool) Run() time.Duration {
	startTime := time.Now()
	
	p.wg.Add(p.cfg.Concurrency)
	for i := 0; i < p.cfg.Concurrency; i++ {
		go p.worker(i)
	}

	if p.cfg.IsDurationMode() {
		time.AfterFunc(p.cfg.Duration, p.cancel)
	}

	p.wg.Wait()
	p.cancel()

	return time.Since(startTime)
}

func (p *Pool) worker(id int) {
	defer p.wg.Done()

	var body []byte
	if p.cfg.Body != "" {
		body = []byte(p.cfg.Body)
	} else if p.cfg.BodyFile != "" {
		var err error
		body, err = client.ReadBodyFile(p.cfg.BodyFile)
		if err != nil {
			return
		}
	}

	for {
		select {
		case <-p.ctx.Done():
			return
		default:
		}

		if p.cfg.Requests > 0 {
			sent := atomic.AddInt64(&p.totalSent, 1)
			if sent > p.targetRequests {
				atomic.AddInt64(&p.totalSent, -1)
				return
			}
		}

		result := p.sendRequest(body)
		p.collector.Record(result)

		if p.cfg.Rate > 0 {
			interval := time.Second / time.Duration(p.cfg.Rate)
			select {
			case <-p.ctx.Done():
				return
			case <-time.After(interval):
			}
		}
	}
}

func (p *Pool) sendRequest(body []byte) *metrics.RequestResult {
	result := &metrics.RequestResult{}

	httpResult, err := p.client.Do(p.cfg.Method, p.cfg.URL, p.cfg.Headers, body)
	if err != nil {
		result.HasError = true
		result.IsTimeout = false
		result.ErrorMsg = err.Error()
		return result
	}

	result.StatusCode = httpResult.StatusCode
	result.Latency = httpResult.Elapsed
	result.HasError = httpResult.HasError

	if httpResult.HasError {
		result.IsTimeout = false
		if httpResult.ErrorMessage != "" {
			result.ErrorMsg = httpResult.ErrorMessage
		}
	}

	return result
}

func (p *Pool) Stop() {
	p.cancel()
}