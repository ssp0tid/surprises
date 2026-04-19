package docker

import (
	"context"
	"errors"
	"fmt"
	"os"
	"time"

	dockerapi "github.com/docker/docker/api"
	"github.com/docker/docker/api/types"
	"github.com/docker/docker/api/types/filters"
	"github.com/docker/docker/client"
)

// ErrorType represents the type of Docker error
type ErrorType int

const (
	ErrorTypeConnection ErrorType = iota
	ErrorTypeAPI
	ErrorTypeTimeout
	ErrorTypeNotFound
	ErrorTypePermission
	ErrorTypeConflict
	ErrorTypeUnknown
)

// DockerError represents a Docker-specific error
type DockerError struct {
	Type    ErrorType
	Message string
	Cause   error
	Context string
}

func (e *DockerError) Error() string {
	if e.Context != "" {
		return fmt.Sprintf("[%s] %s: %v", e.Context, e.Message, e.Cause)
	}
	return fmt.Sprintf("%s: %v", e.Message, e.Cause)
}

func (e *DockerError) Unwrap() error {
	return e.Cause
}

// Error constructors
func NewConnectionError(ctx string, err error) *DockerError {
	return &DockerError{
		Type:    ErrorTypeConnection,
		Message: "Docker connection failed",
		Cause:   err,
		Context: ctx,
	}
}

func NewAPIError(ctx string, err error) *DockerError {
	return &DockerError{
		Type:    ErrorTypeAPI,
		Message: "Docker API error",
		Cause:   err,
		Context: ctx,
	}
}

func NewNotFoundError(ctx string, resource string, err error) *DockerError {
	return &DockerError{
		Type:    ErrorTypeNotFound,
		Message: fmt.Sprintf("%s not found", resource),
		Cause:   err,
		Context: ctx,
	}
}

func NewTimeoutError(ctx string, err error) *DockerError {
	return &DockerError{
		Type:    ErrorTypeTimeout,
		Message: "Operation timed out",
		Cause:   err,
		Context: ctx,
	}
}

func NewPermissionError(ctx string, err error) *DockerError {
	return &DockerError{
		Type:    ErrorTypePermission,
		Message: "Permission denied",
		Cause:   err,
		Context: ctx,
	}
}

func NewConflictError(ctx string, msg string, err error) *DockerError {
	return &DockerError{
		Type:    ErrorTypeConflict,
		Message: msg,
		Cause:   err,
		Context: ctx,
	}
}

// WithRetry executes a function with retry logic and exponential backoff
func WithRetry(ctx context.Context, maxAttempts int, fn func() error) error {
	var lastErr error
	for attempt := 0; attempt < maxAttempts; attempt++ {
		if err := fn(); err != nil {
			lastErr = err
			if attempt < maxAttempts-1 {
				backoff := time.Duration(1<<attempt) * time.Second
				select {
				case <-ctx.Done():
					return ctx.Err()
				case <-time.After(backoff):
				}
			}
		} else {
			return nil
		}
	}
	return fmt.Errorf("after %d attempts: %w", maxAttempts, lastErr)
}

// Client wraps the Docker client
type Client struct {
	client    *client.Client
	host      string
	timeout   time.Duration
	maxRetries int
	connected bool
}

// NewClient creates a new Docker client
func NewClient(host, apiVersion string, timeout time.Duration, maxRetries int) (*Client, error) {
	clientOpts := []client.Opt{
		client.FromEnv,
		client.WithAPIVersionNegotiation(),
	}

	if apiVersion != "" {
		clientOpts = append(clientOpts, client.WithAPIVersion(apiVersion))
	}

	dockerClient, err := client.NewClientWithOpts(clientOpts...)
	if err != nil {
		return nil, NewConnectionError("initializing client", err)
	}

	// Check for explicit host override
	if host != "" {
		os.Setenv("DOCKER_HOST", host)
	}

	return &Client{
		client:    dockerClient,
		host:      host,
		timeout:   timeout,
		maxRetries: maxRetries,
		connected: false,
	}, nil
}

// Connect establishes connection to Docker
func (c *Client) Connect(ctx context.Context) error {
	ctx, cancel := context.WithTimeout(ctx, c.timeout)
	defer cancel()

	if err := c.client.Ping(ctx); err != nil {
		return NewConnectionError("ping", err)
	}

	c.connected = true
	return nil
}

// Close closes the Docker client connection
func (c *Client) Close() error {
	c.connected = false
	return c.client.Close()
}

// Ping checks if Docker is accessible
func (c *Client) Ping(ctx context.Context) error {
	ctx, cancel := context.WithTimeout(ctx, c.timeout)
	defer cancel()

	_, err := c.client.Ping(ctx)
	if err != nil {
		return NewConnectionError("ping", err)
	}
	return nil
}

// IsConnected returns the connection status
func (c *Client) IsConnected() bool {
	return c.connected
}

// Info returns Docker system information
func (c *Client) Info(ctx context.Context) (*types.Info, error) {
	ctx, cancel := context.WithTimeout(ctx, c.timeout)
	defer cancel()

	info, err := c.client.Info(ctx)
	if err != nil {
		return nil, NewAPIError("info", err)
	}
	return &info, nil
}

// Client returns the underlying Docker client
func (c *Client) Client() *client.Client {
	return c.client
}

// DockerEvent represents a Docker event
type DockerEvent struct {
	Type      string
	Action    string
	ActorID   string
	ActorName string
	Time      time.Time
}
