// Package models provides data structures for DockerWatch.
//
// This package contains core domain models for container management,
// including container metadata, resource statistics, logs, and health checks.
package models

import "time"

// Container represents a Docker container with its metadata and state.
type Container struct {
	ID          string            // Full container ID
	ShortID     string            // First 12 characters
	Name        string            // Container name (without leading /)
	Image       string            // Image name
	Status      ContainerStatus   // running, stopped, paused, etc.
	State       string            // Human-readable state
	Created     time.Time         // Creation timestamp
	Ports       []PortBinding     // Port mappings
	Labels      map[string]string // Container labels
	Health      HealthStatus      // Health check status
}

// ContainerStatus represents the operational state of a container.
type ContainerStatus string

// Container status constants.
const (
	StatusRunning    ContainerStatus = "running"
	StatusStopped    ContainerStatus = "stopped"
	StatusPaused     ContainerStatus = "paused"
	StatusCreated    ContainerStatus = "created"
	StatusRestarting ContainerStatus = "restarting"
	StatusExited     ContainerStatus = "exited"
	StatusDead       ContainerStatus = "dead"
)

// PortBinding represents a port mapping between host and container.
type PortBinding struct {
	HostIP        string
	HostPort      string
	ContainerPort string
	Protocol      string
}

// HealthStatus represents the health check state of a container.
type HealthStatus string

// Health status constants.
const (
	HealthHealthy   HealthStatus = "healthy"
	HealthUnhealthy HealthStatus = "unhealthy"
	HealthStarting  HealthStatus = "starting"
	HealthNone      HealthStatus = "" // No health check defined
)

// SetShortID sets the short ID to the first 12 characters of the full ID.
func (c *Container) SetShortID() {
	if len(c.ID) > 12 {
		c.ShortID = c.ID[:12]
	} else {
		c.ShortID = c.ID
	}
}

// Uptime returns the duration since the container was created.
func (c *Container) Uptime() time.Duration {
	return time.Since(c.Created)
}

// String returns the string representation of ContainerStatus.
func (s ContainerStatus) String() string {
	return string(s)
}

// String returns the string representation of HealthStatus.
func (h HealthStatus) String() string {
	if h == "" {
		return "none"
	}
	return string(h)
}