package utils

import (
	"strings"

	"github.com/dockerwatch/dockerwatch/internal/models"
)

type Filter struct {
	Status []models.ContainerStatus
	Search string
	Labels map[string]string
}

func NewFilter() *Filter {
	return &Filter{
		Status: []models.ContainerStatus{},
		Labels: make(map[string]string),
	}
}

func (f *Filter) SetSearch(query string) {
	f.Search = query
}

func (f *Filter) SetStatus(status ...models.ContainerStatus) {
	f.Status = status
}

func (f *Filter) SetLabel(key, value string) {
	f.Labels[key] = value
}

func (f *Filter) Match(c *models.Container) bool {
	if len(f.Status) > 0 {
		found := false
		for _, s := range f.Status {
			if c.Status == s {
				found = true
				break
			}
		}
		if !found {
			return false
		}
	}

	if f.Search != "" {
		search := strings.ToLower(f.Search)
		name := strings.ToLower(c.Name)
		image := strings.ToLower(c.Image)

		if !strings.Contains(name, search) && !strings.Contains(image, search) {
			return false
		}
	}

	if len(f.Labels) > 0 {
		for key, value := range f.Labels {
			if c.Labels[key] != value {
				return false
			}
		}
	}

	return true
}

func (f *Filter) MatchAll(containers []models.Container) []models.Container {
	var result []models.Container
	for _, c := range containers {
		if f.Match(&c) {
			result = append(result, c)
		}
	}
	return result
}

type SortField string

const (
	SortByName    SortField = "name"
	SortByStatus  SortField = "status"
	SortByCPU     SortField = "cpu"
	SortByMemory  SortField = "memory"
	SortByCreated SortField = "created"
)

type SortOption struct {
	Field    SortField
	Desc     bool
}

func SortContainers(containers []models.Container, option SortOption) []models.Container {
	result := make([]models.Container, len(containers))
	copy(result, containers)

	switch option.Field {
	case SortByName:
		sortByName(result, option.Desc)
	case SortByStatus:
		sortByStatus(result, option.Desc)
	case SortByCreated:
		sortByCreated(result, option.Desc)
	}

	return result
}

func sortByName(containers []models.Container, desc bool) {
	for i := 0; i < len(containers)-1; i++ {
		for j := i + 1; j < len(containers); j++ {
			cond := containers[i].Name > containers[j].Name
			if desc {
				cond = !cond
			}
			if cond {
				containers[i], containers[j] = containers[j], containers[i]
			}
		}
	}
}

func sortByStatus(containers []models.Container, desc bool) {
	order := map[models.ContainerStatus]int{
		models.StatusRunning:    0,
		models.StatusPaused:     1,
		models.StatusRestarting: 2,
		models.StatusCreated:    3,
		models.StatusExited:     4,
		models.StatusStopped:    5,
		models.StatusDead:       6,
	}

	for i := 0; i < len(containers)-1; i++ {
		for j := i + 1; j < len(containers); j++ {
			iOrder := order[containers[i].Status]
			jOrder := order[containers[j].Status]
			cond := iOrder > jOrder
			if desc {
				cond = !cond
			}
			if cond {
				containers[i], containers[j] = containers[j], containers[i]
			}
		}
	}
}

func sortByCreated(containers []models.Container, desc bool) {
	for i := 0; i < len(containers)-1; i++ {
		for j := i + 1; j < len(containers); j++ {
			cond := containers[i].Created.After(containers[j].Created)
			if desc {
				cond = !cond
			}
			if cond {
				containers[i], containers[j] = containers[j], containers[i]
			}
		}
	}
}
