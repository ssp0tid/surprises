package tui

import (
	"context"
	"strconv"
	"time"

	"github.com/charmbracelet/bubbletea"
	"github.com/dockerwatch/internal/config"
	"github.com/dockerwatch/internal/docker"
	"github.com/dockerwatch/dockerwatch/internal/models"
)

type App struct {
	dockerClient *docker.Client
	config       *config.Config
	model        Model
}

func New(dockerClient *docker.Client, cfg *config.Config) *App {
	return &App{
		dockerClient: dockerClient,
		config:       cfg,
		model:        NewModel(dockerClient, cfg),
	}
}

func (a *App) Run() error {
	p := tea.NewProgram(a.model, tea.WithAltScreen())
	return p.Run()
}

func (m Model) Init() tea.Cmd {
	return func() tea.Msg {
		ctx := context.Background()
		containers, err := m.dockerClient.ListContainers(ctx, true)
		if err != nil {
			return err
		}
		return containers
	}
}

func (m Model) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
	switch msg := msg.(type) {
	case []models.Container:
		m.Containers = msg
		m.FilterContainers()
		return m, nil

	case error:
		m.AddNotification(Notification{Type: TypeError, Message: msg.Error()})
		return m, nil

	case tea.WindowSizeMsg:
		m.Width = msg.Width
		m.Height = msg.Height
		return m, nil

	case tea.KeyMsg:
		return m.handleKeyPress(msg)
	}

	return m, nil
}

func (m *Model) handleKeyPress(msg tea.KeyMsg) (Model, tea.Cmd) {
	key := msg.String()

	switch key {
	case "ctrl+c", "q":
		if m.ConfirmQuit {
			return *m, tea.Quit
		}
		m.ConfirmQuit = true
		m.AddNotification(Notification{Type: TypeWarning, Message: "Press q again to quit"})
		return *m, nil

	case "?":
		if m.View == ViewHelp {
			m.Back()
		} else {
			m.SetView(ViewHelp)
		}
		return *m, nil

	case "r":
		return *m, func() tea.Msg {
			ctx := context.Background()
			containers, err := m.dockerClient.ListContainers(ctx, true)
			if err != nil {
				return err
			}
			return containers
		}

	case "tab":
		switch m.View {
		case ViewDashboard:
			m.SetView(ViewDetails)
		case ViewDetails:
			m.SetView(ViewLogs)
		case ViewLogs:
			m.SetView(ViewCharts)
		case ViewCharts:
			m.SetView(ViewHelp)
		case ViewHelp:
			m.SetView(ViewDashboard)
		}
		return *m, nil

	case "up", "k":
		if m.Cursor > 0 {
			m.Cursor--
		}
		return *m, nil

	case "down", "j":
		if m.Cursor < len(m.Containers)-1 {
			m.Cursor++
		}
		return *m, nil

	case "enter":
		if len(m.Containers) > 0 && m.Cursor < len(m.Containers) {
			m.SelectedContainer = &m.Containers[m.Cursor]
			m.SetView(ViewDetails)
		}
		return *m, nil

	case "s":
		if len(m.Containers) > 0 && m.Cursor < len(m.Containers) {
			container := m.Containers[m.Cursor]
			return *m, func() tea.Msg {
				ctx := context.Background()
				if err := m.dockerClient.StartContainer(ctx, container.ID); err != nil {
					return err
				}
				return Notification{Type: TypeSuccess, Message: "Container started"}
			}
		}

	case "x":
		if len(m.Containers) > 0 && m.Cursor < len(m.Containers) {
			container := m.Containers[m.Cursor]
			return *m, func() tea.Msg {
				ctx := context.Background()
				if err := m.dockerClient.StopContainer(ctx, container.ID); err != nil {
					return err
				}
				return Notification{Type: TypeSuccess, Message: "Container stopped"}
			}
		}

	case "R":
		if len(m.Containers) > 0 && m.Cursor < len(m.Containers) {
			container := m.Containers[m.Cursor]
			return *m, func() tea.Msg {
				ctx := context.Background()
				if err := m.dockerClient.RestartContainer(ctx, container.ID); err != nil {
					return err
				}
				return Notification{Type: TypeSuccess, Message: "Container restarted"}
			}
		}

	case "l":
		if len(m.Containers) > 0 {
			container := m.Containers[m.Cursor]
			m.SelectedContainer = &container
			m.SetView(ViewLogs)
		}
		return *m, nil

	case "escape", "left", "esc":
		if m.View != ViewDashboard {
			m.Back()
		}
		return *m, nil

	case "c":
		if m.View == ViewDetails || m.View == ViewCharts {
			m.SetView(ViewCharts)
		}
		return *m, nil

	case "t":
		if m.View == ViewLogs {
			m.LogsTimestamps = !m.LogsTimestamps
		}
		return *m, nil

	case "f":
		if m.View == ViewLogs {
			m.LogsFollow = !m.LogsFollow
		}
		return *m, nil
	}

	return *m, nil
}

func (m *Model) refreshContainers() {
	ctx := context.Background()
	containers, err := m.dockerClient.ListContainers(ctx, true)
	if err != nil {
		m.AddNotification(Notification{Type: TypeError, Message: err.Error()})
		return
	}
	m.Containers = containers
	m.FilterContainers()
}

func (m *Model) startContainer(id string) {
	ctx := context.Background()
	if err := m.dockerClient.StartContainer(ctx, id); err != nil {
		m.AddNotification(Notification{Type: TypeError, Message: err.Error()})
		return
	}
	m.AddNotification(Notification{Type: TypeSuccess, Message: "Container started"})
	time.AfterFunc(500*time.Millisecond, m.refreshContainers)
}

func (m *Model) stopContainer(id string) {
	ctx := context.Background()
	if err := m.dockerClient.StopContainer(ctx, id); err != nil {
		m.AddNotification(Notification{Type: TypeError, Message: err.Error()})
		return
	}
	m.AddNotification(Notification{Type: TypeSuccess, Message: "Container stopped"})
	time.AfterFunc(500*time.Millisecond, m.refreshContainers)
}

func (m *Model) restartContainer(id string) {
	ctx := context.Background()
	if err := m.dockerClient.RestartContainer(ctx, id); err != nil {
		m.AddNotification(Notification{Type: TypeError, Message: err.Error()})
		return
	}
	m.AddNotification(Notification{Type: TypeSuccess, Message: "Container restarted"})
	time.AfterFunc(500*time.Millisecond, m.refreshContainers)
}

func ParseInt(s string) int {
	i, _ := strconv.Atoi(s)
	return i
}
