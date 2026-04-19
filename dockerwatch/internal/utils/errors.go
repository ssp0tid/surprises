package utils

import "errors"

var (
	ErrInvalidConfig = errors.New("invalid configuration")
	ErrConnectionFailed = errors.New("connection failed")
	ErrOperationFailed = errors.New("operation failed")
)