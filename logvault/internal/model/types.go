package model

import (
	"encoding/json"
	"time"
)

// LogLevel represents the severity level of a log entry
type LogLevel string

// Log level constants
const (
	LogLevelDebug LogLevel = "DEBUG"
	LogLevelInfo  LogLevel = "INFO"
	LogLevelWarn  LogLevel = "WARN"
	LogLevelError LogLevel = "ERROR"
	LogLevelFatal LogLevel = "FATAL"
)

// String returns the string representation of LogLevel
// Used for validation
func (l LogLevel) String() string {
	return string(l)
}

// IsValid checks if the LogLevel is a valid level
func (l LogLevel) IsValid() bool {
	switch l {
	case LogLevelDebug, LogLevelInfo, LogLevelWarn, LogLevelError, LogLevelFatal:
		return true
	default:
		return false
	}
}

// LogEntry represents a single log entry in the system
type LogEntry struct {
	ID        string          `json:"id"`
	Timestamp time.Time       `json:"timestamp"`
	Level     LogLevel        `json:"level"`
	Service   string          `json:"service"`
	Host      string          `json:"host"`
	Message   string          `json:"message"`
	Metadata  json.RawMessage `json:"metadata,omitempty"`
	Raw       string          `json:"raw,omitempty"`
}

// LogEntryRequest represents the request body for POST /api/v1/logs
type LogEntryRequest struct {
	Timestamp *time.Time       `json:"timestamp,omitempty"`
	Level     LogLevel         `json:"level"`
	Service   string           `json:"service"`
	Host      string           `json:"host"`
	Message   string           `json:"message"`
	Metadata  json.RawMessage  `json:"metadata,omitempty"`
	Raw       string           `json:"raw,omitempty"`
}

// LogQueryParams represents query parameters for GET /api/v1/logs
type LogQueryParams struct {
	Query    string    `form:"q"`
	Level    string    `form:"level"`
	Service  string    `form:"service"`
	Host     string    `form:"host"`
	From     time.Time `form:"from"`
	To       time.Time `form:"to"`
	Limit    int       `form:"limit"`
	Cursor   string    `form:"cursor"`
	Sort     string    `form:"sort"`
	Order    string    `form:"order"`
}

// PaginatedResponse represents a paginated response for log queries
type PaginatedResponse struct {
	Logs   []LogEntry `json:"logs"`
	Cursor string     `json:"cursor,omitempty"`
	Total  int64      `json:"total"`
}

// ErrorDetails contains additional error information
type ErrorDetails map[string]interface{}

// ErrorResponse represents an error response from the API
type ErrorResponse struct {
	Error ErrorDetail `json:"error"`
}

// ErrorDetail contains the error code, message, and optional details
type ErrorDetail struct {
	Code    string       `json:"code"`
	Message string       `json:"message"`
	Details ErrorDetails `json:"details,omitempty"`
}

// AuthRequest represents a login request
type AuthRequest struct {
	Username string `json:"username"`
	Password string `json:"password"`
}

// User represents user information
type User struct {
	ID       string `json:"id"`
	Username string `json:"username"`
}

// AuthResponse represents a login response
type AuthResponse struct {
	Token string `json:"token"`
	User  User   `json:"user"`
}

// AnalyticsSummary represents summary metrics for analytics
type AnalyticsSummary struct {
	TotalLogs     int64     `json:"total_logs"`
	LogsLast24h   int64     `json:"logs_last_24h"`
	ErrorCount    int64     `json:"error_count"`
	ErrorRate     float64   `json:"error_rate"`
	Services      []string  `json:"services"`
	TimeRange     TimeRange `json:"time_range"`
}

// TimeRange represents a time range for analytics
type TimeRange struct {
	Oldest time.Time `json:"oldest"`
	Newest time.Time `json:"newest"`
}

// AnalyticsVolume represents log volume over time
type AnalyticsVolume struct {
	Interval string          `json:"interval"`
	Data     []VolumePoint  `json:"data"`
}

// VolumePoint represents a single data point in volume analytics
type VolumePoint struct {
	Timestamp time.Time `json:"timestamp"`
	Count     int64     `json:"count"`
}

// AnalyticsLevelCount represents log level distribution
type AnalyticsLevelCount struct {
	Level      LogLevel `json:"level"`
	Count      int64    `json:"count"`
	Percentage float64  `json:"percentage"`
}

// AnalyticsServiceCount represents service-level analytics
type AnalyticsServiceCount struct {
	Service string `json:"service"`
	Total   int64  `json:"total"`
	Errors  int64  `json:"errors"`
}

// AnalyticsServiceBreakdown represents the response for service analytics
type AnalyticsServiceBreakdown struct {
	Data []AnalyticsServiceCount `json:"data"`
}

// AnalyticsLevelDistribution represents the response for level analytics
type AnalyticsLevelDistribution struct {
	ByCount       []AnalyticsLevelCount `json:"by_count"`
	ByPercentage  []AnalyticsLevelCount `json:"by_percentage"`
}

// IngestResponse represents the response for log ingestion
type IngestResponse struct {
	ID      string `json:"id"`
	Success bool   `json:"success"`
}

// BatchIngestRequest represents a batch of log entries
type BatchIngestRequest struct {
	Logs []LogEntryRequest `json:"logs"`
}

// BatchIngestResponse represents the response for batch log ingestion
type BatchIngestResponse struct {
	Success bool   `json:"success"`
	Count   int    `json:"count"`
	ID      string `json:"id,omitempty"`
}