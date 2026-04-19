package docker

import (
	"context"
	"fmt"
	"time"
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
				backoff := (1 << attempt) * 100 * 1_000_000_000 // exponential backoff in nanoseconds
				select {
				case <-ctx.Done():
					return ctx.Err()
				case <-time.After(time.Duration(backoff)):
				}
			}
		} else {
			return nil
		}
	}
	return fmt.Errorf("after %d attempts: %w", maxAttempts, lastErr)
}