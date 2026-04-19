// Package models provides data structures for DockerWatch.
//
// This package contains core domain models for container management,
// including container metadata, resource statistics, logs, and health checks.
package models

import "time"

// LogEntry represents a single log line from a container.
type LogEntry struct {
	Timestamp   time.Time
	ContainerID string
	Message     string
	Stream      LogStream  // stdout or stderr
	IsPartial   bool       // Multi-line message chunk
}

// LogStream represents the output stream type.
type LogStream string

// Log stream constants.
const (
	StreamStdout LogStream = "stdout"
	StreamStderr LogStream = "stderr"
)

// LogOptions defines options for fetching container logs.
type LogOptions struct {
	Follow     bool      // Stream logs
	Tail       int       // Number of lines to fetch
	Since      time.Time // Logs since timestamp
	Timestamps bool      // Include timestamps
	Details    bool      // Include extra details
}