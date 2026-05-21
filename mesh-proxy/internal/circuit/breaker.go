package circuit

import (
	"errors"
	"fmt"
	"sync"
	"sync/atomic"
	"time"

	"github.com/surprises/mesh-proxy/pkg/types"
)

var Err circuitOpen = errors.New("circuit breaker is open")

type circuitState int

const (
	stateClosed circuitState = iota
	stateOpen
	stateHalfOpen
)

type Breaker struct {
	name          string
	maxRequests  int
	interval     time.Duration
	timeout      time.Duration
	failureRate   float64
	minRequests   int

	mu            sync.RWMutex
	requestCount int
	failureCount int
	lastFailure  time.Time
	state        circuitState
	expiry       time.Time
}

func New(name string) *Breaker {
	return NewWithConfig(name, nil)
}

func NewWithConfig(name string, cfg *types.CBConfig) *Breaker {
	settings := struct {
		maxRequests  int
		failureRate float64
		minRequests int
		timeout    time.Duration
	}{
		maxRequests: 100,
		failureRate: 0.5,
		minRequests: 5,
		timeout:   60 * time.Second,
	}

	if cfg != nil {
		if cfg.MaxRequests > 0 {
			settings.maxRequests = cfg.MaxRequests
		}
		if cfg.FailureRateThreshold > 0 {
			settings.failureRate = cfg.FailureRateThreshold
		}
		if cfg.MinRequests > 0 {
			settings.minRequests = cfg.MinRequests
		}
		if cfg.Timeout > 0 {
			settings.timeout = cfg.Timeout
		}
	}

	return &Breaker{
		name:         name,
		maxRequests:  settings.maxRequests,
		timeout:    settings.timeout,
		failureRate: settings.failureRate,
		minRequests: settings.minRequests,
		state:      stateClosed,
	}
}

func (cb *Breaker) Allow() error {
	if state := cb.getState(); state != stateClosed && state != stateHalfOpen {
		return Err
	}
	return nil
}

func (cb *Breaker) Execute(fn func() error) error {
	if err := cb.Allow(); err != nil {
		return err
	}

	atomic.AddInt32((*int32)(&cb.requestCount), 1)

	err := fn()
	cb.recordResult(err)

	return err
}

func (cb *Breaker) recordResult(err error) {
	cb.mu.Lock()
	defer cb.mu.Unlock()

	if err != nil {
		cb.failureCount++
		cb.lastFailure = time.Now()
	}

	switch cb.state {
	case stateClosed:
		if cb.requestCount >= int32(cb.minRequests) &&
			float64(cb.failureCount)/float64(cb.requestCount) >= cb.failureRate {
			cb.state = stateOpen
			cb.expiry = time.Now().Add(cb.timeout)
			cb.failureCount = 0
			cb.requestCount = 0
		}
	case stateOpen:
		if time.Now().After(cb.expiry) {
			cb.state = stateHalfOpen
		}
	}
}

func (cb *Breaker) getState() circuitState {
	cb.mu.RLock()
	state := cb.state
	expiry := cb.expiry
	cb.mu.RUnlock()

	if state == stateOpen && time.Now().After(expiry) {
		return stateHalfOpen
	}
	return state
}

func (cb *Breaker) State() string {
	switch cb.getState() {
	case stateClosed:
		return "closed"
	case stateOpen:
		return "open"
	case stateHalfOpen:
		return "half-open"
	}
	return "unknown"
}

func (cb *Breaker) Ready() bool {
	return cb.getState() != stateOpen
}

func (cb *Breaker) Reset() {
	cb.mu.Lock()
	defer cb.mu.Unlock()
	cb.state = stateClosed
	cb.failureCount = 0
	cb.requestCount = 0
}

func (cb *Breaker) GetStats() map[string]interface{} {
	cb.mu.RLock()
	defer cb.mu.RUnlock()

	stateStr := "unknown"
	switch cb.state {
	case stateClosed:
		stateStr = "closed"
	case stateOpen:
		stateStr = "open"
	case stateHalfOpen:
		stateStr = "half-open"
	}

	return map[string]interface{}{
		"name":           cb.name,
		"state":          stateStr,
		"request_count":  cb.requestCount,
		"failure_count":  cb.failureCount,
		"failure_rate":   cb.failureRate,
		"last_failure":   cb.lastFailure,
	}
}

func (cb *Breaker) String() string {
	return fmt.Sprintf("circuit(%s, %s)", cb.name, cb.State())
}