package tui

import (
	"strings"

	"github.com/charmbracelet/bubbletea"
	"github.com/dockerwatch/dockerwatch/internal/config"
	"github.com/dockerwatch/dockerwatch/internal/docker"
	"github.com/dockerwatch/dockerwatch/internal/models"
)

type View int

const (
	ViewDashboard View = iota
	ViewDetails
	ViewLogs
	ViewCharts
	ViewHelp
)

type NotificationType int

const (
	TypeInfo NotificationType = iota
	TypeSuccess
	TypeWarning
	TypeError
)

type Notification struct {
	Type    NotificationType
	Message string
}

type Model struct {
	dockerClient *docker.Client
	config       *config.Config

	View              View
	PreviousView      View
	Cursor            int
	Containers        []models.Container
	FilteredContainers []models.Container
	Stats             map[string]*models.Stats
	StatsHistory      map[string][]models.Stats
	Filter            string
	SelectedContainer *models.Container

	Logs           map[string][]models.LogEntry
	LogsFollow     bool
	LogsTimestamps bool

	ShowHelp       bool
	Notifications  []Notification
	ConfirmQuit    bool
	Width          int
	Height         int
}

func NewModel(dockerClient *docker.Client, cfg *config.Config) Model {
	return Model{
		dockerClient: dockerClient,
		config:       cfg,
		View:         ViewDashboard,
		Cursor:       0,
		Containers:   []models.Container{},
		Stats:        make(map[string]*models.Stats),
		StatsHistory: make(map[string][]models.Stats),
		Filter:       "",
		Logs:         make(map[string][]models.LogEntry),
		LogsFollow:   false,
		LogsTimestamps: true,
		ShowHelp:     false,
		Notifications: []Notification{},
		ConfirmQuit:  false,
	}
}

func (m Model) Init() tea.Cmd {
	return nil
}

func (m Model) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
	return m, nil
}

func (m Model) View() string {
	return Render(m)
}

func (m *Model) SetView(view View) {
	m.PreviousView = m.View
	m.View = view
}

func (m *Model) Back() {
	m.View = m.PreviousView
}

func (m *Model) AddNotification(n Notification) {
	m.Notifications = append(m.Notifications, n)
	if len(m.Notifications) > 5 {
		m.Notifications = m.Notifications[1:]
	}
}

func (m Model) GetStats(id string) *models.Stats {
	return m.Stats[id]
}

func (m Model) GetStatsHistory(id string) []models.Stats {
	if id == "" {
		var all []models.Stats
		for _, history := range m.StatsHistory {
			all = append(all, history...)
		}
		return all
	}
	return m.StatsHistory[id]
}

func (m Model) GetContainer() *models.Container {
	return m.SelectedContainer
}

func (m Model) GetLogs(id string) []models.LogEntry {
	return m.Logs[id]
}

func (m *Model) FilterContainers() {
	if m.Filter == "" {
		m.FilteredContainers = m.Containers
		return
	}
	
	var filtered []models.Container
	for _, c := range m.Containers {
		if strings.Contains(strings.ToLower(c.Name), strings.ToLower(m.Filter)) ||
		   strings.Contains(strings.ToLower(c.Image), strings.ToLower(m.Filter)) {
			filtered = append(filtered, c)
		}
	}
	m.FilteredContainers = filtered
}
