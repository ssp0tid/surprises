// Package models provides data structures for DockerWatch.
//
// This package contains core domain models for container management,
// including container metadata, resource statistics, logs, and health checks.
package models

import "time"

// HealthCheck represents the health status of a container.
type HealthCheck struct {
	Status    HealthStatus
	Failures  int
	LastCheck time.Time
	Info      string
}