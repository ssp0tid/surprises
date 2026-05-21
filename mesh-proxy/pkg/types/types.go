package types

import "time"

// RouteMatch defines how to match incoming requests to a route.
type RouteMatch struct {
	Path        string            // exact or /* wildcard
	PathPrefix  string            // prefix match
	Methods     []string          // HTTP methods
	Headers     map[string]string // header matching
}

// BackendConfig defines the upstream backend service.
type BackendConfig struct {
	URL  string   // Single backend URL
	URLs []string // Multiple backends for load balancing
}

// CBConfig defines circuit breaker settings.
type CBConfig struct {
	Enabled              bool    // Enable CB
	FailureRateThreshold float64 // Failure rate to open (0.0-1.0)
	Timeout             time.Duration // Time in open state
	HalfOpenRequests    int            // Probes in half-open state
	MinRequests         int            // Minimum requests before evaluation
}

// RLConfig defines rate limit settings.
type RLConfig struct {
	RequestsPerSecond float64 // Requests per second
	Burst            int    // Burst allowance
	Key              string // Rate limit key (header:HeaderName, ip, etc)
}

// MockConfig defines mock response settings.
type MockConfig struct {
	Enabled    bool              // Enable mock
	StatusCode int              // HTTP status code
	Headers    map[string]string // Response headers
	Body       string            // Response body
	BodyFile   string           // File containing body
}

// DelayConfig defines delay injection settings.
type DelayConfig struct {
	Fixed  time.Duration // Fixed delay
	Min    time.Duration // Minimum delay
	Max    time.Duration // Maximum delay
	Jitter time.Duration // Random jitter (±)
}

// MirrorConfig defines traffic mirroring settings.
type MirrorConfig struct {
	Enabled      bool    // Enable mirroring
	Target      string  // Shadow service URL
	Percentage  float64 // % of traffic to mirror (0.0-100.0)
	PercentageHeader string // Header containing percentage
}

// Route defines a single route with all its configuration.
type Route struct {
	Name          string       // Route name (required, unique)
	Enabled      bool        // Enable/disable route
	Priority     int        // Route priority (higher = first)
	Criteria     RouteMatch   `yaml:"match"` // Matching rules
	Backend      *BackendConfig // Backend settings
	CircuitBreaker *CBConfig  // Circuit breaker (optional)
	RateLimit    *RLConfig  // Rate limit (optional)
	Mock        *MockConfig // Mock response (optional)
	Delay       *DelayConfig // Delay injection (optional)
	Mirror      *MirrorConfig // Traffic mirror (optional)
	Timeout     time.Duration // Request timeout
}

// ErrorConfig defines custom error responses.
type ErrorConfig struct {
	StatusCode int               // HTTP status code
	Headers   map[string]string // Response headers
	Body      string            // Response body
}

// Stats holds runtime statistics.
type Stats struct {
	RequestsTotal     int64   // Total requests
	RequestsAllowed   int64   // Allowed requests
	RequestsDenied    int64   // Denied requests (rate limited)
	LatencyP50Ms     int64   // P50 latency in ms
	LatencyP99Ms     int64   // P99 latency in ms
}

// ServerConfig defines HTTP server settings.
type ServerConfig struct {
	Host         string        // Bind host
	Port        int           // Bind port
	ReadTimeout time.Duration // Read timeout
	WriteTimeout time.Duration // Write timeout
	IdleTimeout time.Duration // Idle timeout
}

// AdminConfig defines admin API settings.
type AdminConfig struct {
	Host    string // Bind host
	Port   int    // Bind port
	Enabled bool  // Enable admin server
}

// DefaultsConfig defines default settings.
type DefaultsConfig struct {
	Timeout      time.Duration // Default timeout
	RetryAttempts int         // Default retry attempts
}

// LoggingConfig defines logging settings.
type LoggingConfig struct {
	Level  string // Log level
	Format string // Log format (json/text)
}