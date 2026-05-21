package config

import (
	"time"

	"github.com/surprises/mesh-proxy/pkg/types"
)

type Config struct {
	Version       string                    `mapstructure:"version" yaml:"version"`
	Server        types.ServerConfig         `mapstructure:"server" yaml:"server"`
	Admin         types.AdminConfig         `mapstructure:"admin" yaml:"admin"`
	Defaults      types.DefaultsConfig     `mapstructure:"defaults" yaml:"defaults"`
	CircuitBreaker *CBDefaults             `mapstructure:"circuit_breaker" yaml:"circuit_breaker"`
	RateLimit     *RLDefaults              `mapstructure:"rate_limit" yaml:"rate_limit"`
	Logging       types.LoggingConfig       `mapstructure:"logging" yaml:"logging"`
	Routes        []*types.Route            `mapstructure:"routes" yaml:"routes"`
	Errors        map[string]types.ErrorConfig `mapstructure:"errors" yaml:"errors"`
}

type CBDefaults struct {
	MaxRequests          int           `mapstructure:"max_requests" yaml:"max_requests"`
	Interval            time.Duration `mapstructure:"interval" yaml:"interval"`
	Timeout             time.Duration `mapstructure:"timeout" yaml:"timeout"`
	ReadyToTripFailureRate float64     `mapstructure:"ready_to_trip_failure_rate_threshold" yaml:"ready_to_trip_failure_rate_threshold"`
	MinimumRequests     int           `mapstructure:"minimum_requests" yaml:"minimum_requests"`
}

type RLDefaults struct {
	RequestsPerSecond float64 `mapstructure:"requests_per_second" yaml:"requests_per_second"`
	Burst           int      `mapstructure:"burst" yaml:"burst"`
}

func NewDefaultConfig() *Config {
	return &Config{
		Version: "1.0",
		Server: types.ServerConfig{
			Host:         "0.0.0.0",
			Port:        8080,
			ReadTimeout:  30 * time.Second,
			WriteTimeout: 30 * time.Second,
			IdleTimeout: 120 * time.Second,
		},
		Admin: types.AdminConfig{
			Host:    "127.0.0.1",
			Port:   9090,
			Enabled: true,
		},
		Defaults: types.DefaultsConfig{
			Timeout:       10 * time.Second,
			RetryAttempts: 0,
		},
		CircuitBreaker: &CBDefaults{
			MaxRequests:            100,
			Interval:               10 * time.Second,
			Timeout:                60 * time.Second,
			ReadyToTripFailureRate: 0.5,
			MinimumRequests:       5,
		},
		RateLimit: &RLDefaults{
			RequestsPerSecond: 100,
			Burst:             20,
		},
		Logging: types.LoggingConfig{
			Level:  "info",
			Format: "json",
		},
		Routes:  make([]*types.Route, 0),
		Errors: make(map[string]types.ErrorConfig),
	}
}