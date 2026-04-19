package docker

import (
	"context"

	"github.com/dockerwatch/internal/models"
)

func (c *Client) GetLogs(ctx context.Context, id string, opts models.LogOptions) ([]models.LogEntry, error) {
	return nil, nil
}

func (c *Client) StreamLogs(ctx context.Context, id string, opts models.LogOptions) (<-chan models.LogEntry, error) {
	return nil, nil
}