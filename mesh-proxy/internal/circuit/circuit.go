package circuit

import (
	"context"
	"errors"
	"strings"
	"sync"
	"time"

	"github.com/sony/gobreaker/v2"
)

var (
	ErrCircuitOpen = errors.New("circuit breaker is open")
)

type Circuit struct {
	name    string
	cb     *gobreaker.CircuitBreaker
	mu     sync.RWMutex
	state  gobreaker.State
}

type Settings struct {
	Name        string
	MaxRequests int
	Interval   time.Duration
	Timeout   time.Duration
	Threshold float64
}

func New(name string, settings Settings) *Circuit {
	s := gobreaker.Settings{
		Name:        name,
		MaxRequests: 3,
		Interval:   10 * time.Second,
		Timeout:   60 * time.Second,
		ReadyToTrip: func(c gobreaker.Counts) bool {
			if c.Requests < 5 {
				return false
			}
			failureRatio := float64(c.TotalFailures) / float64(c.Requests)
			return failureRatio >= settings.Threshold
		},
		IsSuccessful: func(err error) bool {
			if err == nil {
				return true
			}
			return !strings.Contains(err.Error(), "5")
		},
	}

	if settings.MaxRequests > 0 {
		s.MaxRequests = settings.MaxRequests
	}
	if settings.Interval > 0 {
		s.Interval = settings.Interval
	}
	if settings.Timeout > 0 {
		s.Timeout = settings.Timeout
	}

	return &Circuit{
		name: name,
		cb:  gobreaker.NewCircuitBreaker(s),
	}
}

func (c *Circuit) Execute(ctx context.Context, fn func() error) error {
	result, err := c.cb.Execute(func() (interface{}, error) {
		return nil, fn()
	})

	if err != nil {
		if errors.Is(err, gobreaker.ErrOpenState) {
			return ErrCircuitOpen
		}
		return err
	}

	if result != nil {
		if err, ok := result.(error); ok {
			return err
		}
	}

	return nil
}

func (c *Circuit) State() gobreaker.State {
	return c.cb.State()
}

func (c *Circuit) IsOpen() bool {
	return c.cb.State() == gobreaker.StateOpen
}

func (c *Circuit) IsHalfOpen() bool {
	return c.cb.State() == gobreaker.StateHalfOpen
}

func (c *Circuit) IsClosed() bool {
	return c.cb.State() == gobreaker.StateClosed
}