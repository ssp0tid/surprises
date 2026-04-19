package docker

import (
	"context"

	"github.com/dockerwatch/internal/models"
)

func (c *Client) GetStats(ctx context.Context, id string) (*models.Stats, error) {
	return nil, nil
}

func (c *Client) StreamStats(ctx context.Context, id string) (<-chan *models.Stats, error) {
	return nil, nil
}