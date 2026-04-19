package docker

import (
	"context"
	"fmt"
	"strings"
	"time"

	"github.com/docker/docker/api/types"
	"github.com/docker/docker/api/types/filters"
	"github.com/dockerwatch/dockerwatch/internal/models"
)

// ListContainers returns a list of containers
func (c *Client) ListContainers(ctx context.Context, all bool) ([]models.Container, error) {
	ctx, cancel := context.WithTimeout(ctx, c.timeout)
	defer cancel()

	containerList, err := c.client.ContainerList(ctx, types.ContainerListOptions{
		All: all,
	})
	if err != nil {
		return nil, NewAPIError("list containers", err)
	}

	containers := make([]models.Container, 0, len(containerList))
	for _, container := range containerList {
		c := convertContainer(container)
		containers = append(containers, c)
	}

	return containers, nil
}

// GetContainer returns a single container by ID
func (c *Client) GetContainer(ctx context.Context, id string) (*models.Container, error) {
	ctx, cancel := context.WithTimeout(ctx, c.timeout)
	defer cancel()

	raw, err := c.client.ContainerInspect(ctx, id)
	if err != nil {
		return nil, NewAPIError(fmt.Sprintf("get container %s", id), err)
	}

	container := convertInspectContainer(&raw)
	return &container, nil
}

// InspectContainer returns detailed container information
func (c *Client) InspectContainer(ctx context.Context, id string) (map[string]interface{}, error) {
	ctx, cancel := context.WithTimeout(ctx, c.timeout)
	defer cancel()

	raw, err := c.client.ContainerInspect(ctx, id)
	if err != nil {
		return nil, NewAPIError(fmt.Sprintf("inspect container %s", id), err)
	}

	// Convert to map for flexibility
	result := map[string]interface{}{
		"id":         raw.ID,
		"name":       strings.TrimPrefix(raw.Name, "/"),
		"image":      raw.Config.Image,
		"created":    raw.Created,
		"state":      raw.State.Status,
		"status":     raw.State.Status,
		"labels":     raw.Config.Labels,
		"ports":      raw.NetworkSettings.Ports,
	}

	return result, nil
}

// StartContainer starts a container
func (c *Client) StartContainer(ctx context.Context, id string) error {
	ctx, cancel := context.WithTimeout(ctx, c.timeout)
	defer cancel()

	if err := c.client.ContainerStart(ctx, id, types.ContainerStartOptions{}); err != nil {
		return NewAPIError(fmt.Sprintf("start container %s", id), err)
	}
	return nil
}

// StopContainer stops a container
func (c *Client) StopContainer(ctx context.Context, id string) error {
	ctx, cancel := context.WithTimeout(ctx, c.timeout)
	defer cancel()

	timeout := 10 * time.Second
	if err := c.client.ContainerStop(ctx, id, &timeout); err != nil {
		return NewAPIError(fmt.Sprintf("stop container %s", id), err)
	}
	return nil
}

// RestartContainer restarts a container
func (c *Client) RestartContainer(ctx context.Context, id string) error {
	ctx, cancel := context.WithTimeout(ctx, c.timeout)
	defer cancel()

	timeout := 10 * time.Second
	if err := c.client.ContainerRestart(ctx, id, &timeout); err != nil {
		return NewAPIError(fmt.Sprintf("restart container %s", id), err)
	}
	return nil
}

// RemoveContainer removes a container
func (c *Client) RemoveContainer(ctx context.Context, id string, force bool) error {
	ctx, cancel := context.WithTimeout(ctx, c.timeout)
	defer cancel()

	removeOpts := types.ContainerRemoveOptions{
		Force: force,
	}

	if err := c.client.ContainerRemove(ctx, id, removeOpts); err != nil {
		return NewAPIError(fmt.Sprintf("remove container %s", id), err)
	}
	return nil
}

// PauseContainer pauses a container
func (c *Client) PauseContainer(ctx context.Context, id string) error {
	ctx, cancel := context.WithTimeout(ctx, c.timeout)
	defer cancel()

	if err := c.client.ContainerPause(ctx, id); err != nil {
		return NewAPIError(fmt.Sprintf("pause container %s", id), err)
	}
	return nil
}

// UnpauseContainer unpauses a container
func (c *Client) UnpauseContainer(ctx context.Context, id string) error {
	ctx, cancel := context.WithTimeout(ctx, c.timeout)
	defer cancel()

	if err := c.client.ContainerUnpause(ctx, id); err != nil {
		return NewAPIError(fmt.Sprintf("unpause container %s", id), err)
	}
	return nil
}

// StreamEvents streams Docker events
func (c *Client) StreamEvents(ctx context.Context) (<-chan *DockerEvent, error) {
	eventsChan := make(chan *DockerEvent, 100)

	msgChan, errChan := c.client.Events(ctx, types.EventsOptions{
		Filters: filters.NewArgs(),
	})

	go func() {
		defer close(eventsChan)
		for {
			select {
			case msg, ok := <-msgChan:
				if !ok {
					return
				}
				eventsChan <- &DockerEvent{
					Type:      msg.Type,
					Action:    msg.Action,
					ActorID:   msg.Actor.ID,
					ActorName: msg.Actor.Name,
					Time:      time.Unix(msg.Time, 0),
				}
			case err, ok := <-errChan:
				if !ok {
					return
				}
				// Log error but continue
				_ = err
			case <-ctx.Done():
				return
			}
		}
	}()

	return eventsChan, nil
}

// GetStats returns stats for a container (one-shot)
func (c *Client) GetStats(ctx context.Context, id string) (*models.Stats, error) {
	ctx, cancel := context.WithTimeout(ctx, c.timeout)
	defer cancel()

	resp, err := c.client.ContainerStats(ctx, id, false)
	if err != nil {
		return nil, NewAPIError("get stats", err)
	}
	defer resp.Body.Close()

	var statsJSON types.StatsJSON
	if err := resp.Decode(&statsJSON); err != nil {
		return nil, NewAPIError("decode stats", err)
	}

	return convertStats(id, &statsJSON), nil
}

// Helper functions

func convertContainer(raw types.Container) models.Container {
	name := ""
	if len(raw.Names) > 0 {
		name = strings.TrimPrefix(raw.Names[0], "/")
	}

	status := models.ContainerStatus(raw.State)
	health := models.HealthNone

	// Try to determine health status
	if raw.State == "running" {
		health = models.HealthHealthy
	}

	container := models.Container{
		ID:      raw.ID,
		ShortID: raw.ID[:12],
		Name:    name,
		Image:   raw.Image,
		Status:  status,
		State:   raw.Status,
		Created: time.Unix(raw.Created, 0),
		Labels:  raw.Labels,
		Health:  health,
		Ports:   convertPorts(raw.Ports),
	}

	return container
}

func convertInspectContainer(raw *types.ContainerJSON) models.Container {
	name := strings.TrimPrefix(raw.Name, "/")
	status := models.ContainerStatus(raw.State.Status)
	health := models.HealthNone

	if raw.State.Health != nil {
		health = models.HealthStatus(raw.State.Health.Status)
	}

	container := models.Container{
		ID:      raw.ID,
		ShortID: raw.ID[:12],
		Name:    name,
		Image:   raw.Config.Image,
		Status:  status,
		State:   raw.State.Status,
		Created: raw.Created,
		Labels:  raw.Config.Labels,
		Health:  health,
		Ports:   convertPortsFromInspect(raw.NetworkSettings.Ports),
	}

	return container
}

func convertPorts(ports []types.Port) []models.PortBinding {
	result := make([]models.PortBinding, 0, len(ports))
	for _, p := range ports {
		result = append(result, models.PortBinding{
			HostIP:        p.IP,
			HostPort:      fmt.Sprintf("%d", p.PublicPort),
			ContainerPort: fmt.Sprintf("%d", p.PrivatePort),
			Protocol:      p.Type,
		})
	}
	return result
}

func convertPortsFromInspect(ports map[types.Port][]types.PortBinding) []models.PortBinding {
	result := make([]models.PortBinding, 0)
	for containerPort, bindings := range ports {
		for _, b := range bindings {
			result = append(result, models.PortBinding{
				HostIP:        b.IP,
				HostPort:      b.HostPort,
				ContainerPort: containerPort.Port(),
				Protocol:      containerPort.Proto(),
			})
		}
	}
	return result
}
