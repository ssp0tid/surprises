package ratelimit

import (
	"errors"
	"net/http"
	"sync"

	"golang.org/x/time/rate"
)

var ErrRateLimited = errors.New("rate limit exceeded")

type Limiter struct {
	limiters map[string]*rate.Limiter
	mu       sync.RWMutex
	rps      float64
	burst    int
	keyHeader string
}

func New(rps float64, burst int, keyHeader string) *Limiter {
	return &Limiter{
		limiters:  make(map[string]*rate.Limiter),
		rps:      rps,
		burst:    burst,
		keyHeader: keyHeader,
	}
}

func (l *Limiter) getKey(r *http.Request) string {
	if l.keyHeader != "" {
		if key := r.Header.Get(l.keyHeader); key != "" {
			return key
		}
	}
	return r.RemoteAddr
}

func (l *Limiter) Allow(r *http.Request) error {
	key := l.getKey(r)

	l.mu.RLock()
	limiter, exists := l.limiters[key]
	l.mu.RUnlock()

	if !exists {
		l.mu.Lock()
		if l.limiters[key] == nil {
			l.limiters[key] = rate.NewLimiter(rate.Limit(l.rps), l.burst)
		}
		limiter = l.limiters[key]
		l.mu.Unlock()
	}

	if !limiter.Allow() {
		return ErrRateLimited
	}
	return nil
}

func (l *Limiter) Wait(r *http.Request) error {
	key := l.getKey(r)

	l.mu.RLock()
	limiter, exists := l.limiters[key]
	l.mu.RUnlock()

	if !exists {
		l.mu.Lock()
		if l.limiters[key] == nil {
			l.limiters[key] = rate.NewLimiter(rate.Limit(l.rps), l.burst)
		}
		limiter = l.limiters[key]
		l.mu.Unlock()
	}

	return limiter.Wait(r.Context())
}