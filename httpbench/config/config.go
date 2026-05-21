package config

import (
	"errors"
	"fmt"
	"net/url"
	"time"
)

var (
	ErrMissingURL      = errors.New("URL is required")
	ErrInvalidURL      = errors.New("invalid URL format")
	ErrInvalidDuration = errors.New("duration must be positive")
	ErrInvalidCount    = errors.New("requests must be non-negative")
	ErrInvalidConcurrency = errors.New("concurrency must be at least 1")
	ErrInvalidRate     = errors.New("rate must be non-negative")
)

type Config struct {
	URL         string
	Method      string
	Concurrency int
	Duration    time.Duration
	Requests    int
	Rate        int
	Timeout     time.Duration
	Headers     map[string]string
	Body        string
	BodyFile    string
	Format      string
	Quiet       bool
}

func (c *Config) Validate() error {
	if c.URL == "" {
		return ErrMissingURL
	}

	if _, err := url.Parse(c.URL); err != nil {
		return fmt.Errorf("%w: %v", ErrInvalidURL, err)
	}

	if c.Concurrency < 1 {
		return ErrInvalidConcurrency
	}

	if c.Duration <= 0 && c.Requests <= 0 {
		return fmt.Errorf("either duration or requests must be positive")
	}

	if c.Duration < 0 {
		return ErrInvalidDuration
	}

	if c.Requests < 0 {
		return ErrInvalidCount
	}

	if c.Rate < 0 {
		return ErrInvalidRate
	}

	if c.Timeout <= 0 {
		c.Timeout = 30 * time.Second
	}

	return nil
}

func (c *Config) IsDurationMode() bool {
	return c.Requests <= 0
}

func (c *Config) IsJSON() bool {
	return c.Format == "json"
}