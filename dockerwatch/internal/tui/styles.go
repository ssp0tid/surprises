package tui

import "github.com/charmbracelet/lipgloss"

// Style variables used across TUI views
var (
	// Base styles
	StyleBase = lipgloss.NewStyle()

	// Status styles
	StatusRunning    = lipgloss.NewStyle().Foreground(lipgloss.Color("green"))
	StatusStopped    = lipgloss.NewStyle().Foreground(lipgloss.Color("red"))
	StatusPaused     = lipgloss.NewStyle().Foreground(lipgloss.Color("yellow"))
	StatusCreated    = lipgloss.NewStyle().Foreground(lipgloss.Color("blue"))
	StatusRestarting = lipgloss.NewStyle().Foreground(lipgloss.Color("yellow"))
	StatusExited      = lipgloss.NewStyle().Foreground(lipgloss.Color("red"))
	StatusDead        = lipgloss.NewStyle().Foreground(lipgloss.Color("gray"))

	// Container styles
	ContainerName         = lipgloss.NewStyle().Bold(true)
	ContainerSelected     = lipgloss.NewStyle().Bold(true).Foreground(lipgloss.Color("green"))
	ContainerID           = lipgloss.NewStyle().Faint(true)

	// Stats styles
	StatsValue  = lipgloss.NewStyle().Foreground(lipgloss.Color("cyan"))
	CPU         = lipgloss.NewStyle().Foreground(lipgloss.Color("green"))
	Memory      = lipgloss.NewStyle().Foreground(lipgloss.Color("blue"))
	Network     = lipgloss.NewStyle().Foreground(lipgloss.Color("yellow"))
	Disk        = lipgloss.NewStyle().Foreground(lipgloss.Color("magenta"))

	// Progress bar styles
	ProgressFill  = lipgloss.NewStyle().Foreground(lipgloss.Color("green"))
	ProgressEmpty = lipgloss.NewStyle().Foreground(lipgloss.Color("gray"))

	// UI element styles
	HelpText       = lipgloss.NewStyle().Foreground(lipgloss.Color("240"))
	SelectedRow    = lipgloss.NewStyle().Background(lipgloss.Color("234"))
	Muted          = lipgloss.NewStyle().Foreground(lipgloss.Color("240"))
	Border         = lipgloss.NewStyle().Foreground(lipgloss.Color("gray"))
	Surface        = lipgloss.NewStyle().Background(lipgloss.Color("235"))
	Title          = lipgloss.NewStyle().Bold(true).Foreground(lipgloss.Color("cyan"))
	Header         = lipgloss.NewStyle().Bold(true).Foreground(lipgloss.Color("white"))
	Accent         = lipgloss.NewStyle().Foreground(lipgloss.Color("cyan"))
	Primary        = lipgloss.NewStyle().Foreground(lipgloss.Color("blue"))

	// Help styles
	HelpKey  = lipgloss.NewStyle().Foreground(lipgloss.Color("green")).Bold(true)
	HelpDesc = lipgloss.NewStyle().Foreground(lipgloss.Color("white"))

	// Log styles
	LogTimestamp = lipgloss.NewStyle().Foreground(lipgloss.Color("240"))
	LogStderr    = lipgloss.NewStyle().Foreground(lipgloss.Color("red"))
	LogStdout    = lipgloss.NewStyle()

	// Health styles
	HealthHealthy   = lipgloss.NewStyle().Foreground(lipgloss.Color("green"))
	HealthUnhealthy = lipgloss.NewStyle().Foreground(lipgloss.Color("red"))
	HealthStarting  = lipgloss.NewStyle().Foreground(lipgloss.Color("yellow"))

	// Table header style
	TableHeader = lipgloss.NewStyle().Bold(true).Foreground(lipgloss.Color("white"))

	// StyleTableHeader is an alias for TableHeader
	StyleTableHeader = TableHeader
	// StyleContainerName is an alias for ContainerName
	StyleContainerName = ContainerName
	// StyleContainerSelected is an alias for ContainerSelected
	StyleContainerSelected = ContainerSelected
	// StyleCPU is an alias for CPU
	StyleCPU = CPU
	// StyleMemory is an alias for Memory
	StyleMemory = Memory
	// StyleNetwork is an alias for Network
	StyleNetwork = Network
	// StyleMuted is an alias for Muted
	StyleMuted = Muted
	// StyleBorder is an alias for Border
	StyleBorder = Border
	// StyleSurface is an alias for Surface
	StyleSurface = Surface
	// StyleTitle is an alias for Title
	StyleTitle = Title
	// StyleAccent is an alias for Accent
	StyleAccent = Accent
	// StyleProgressFill is an alias for ProgressFill
	StyleProgressFill = ProgressFill
	// StyleProgressEmpty is an alias for ProgressEmpty
	StyleProgressEmpty = ProgressEmpty
	// StyleLogTimestamp is an alias for LogTimestamp
	StyleLogTimestamp = LogTimestamp
	// StyleLogStderr is an alias for LogStderr
	StyleLogStderr = LogStderr
	// StyleHeader is an alias for Header
	StyleHeader = Header
	// StyleHelpKey is an alias for HelpKey
	StyleHelpKey = HelpKey
	// StyleHelpDesc is an alias for HelpDesc
	StyleHelpDesc = HelpDesc
	// StylePrimary is an alias for Primary
	StylePrimary = Primary

	// StyleStatsValue is an alias for StatsValue
	StyleStatsValue = StatsValue
)

// GetStatusStyle returns the appropriate style for a container status
func GetStatusStyle(status interface{}) lipgloss.Style {
	switch string(status.(type)) {
	case "running":
		return StatusRunning
	case "stopped", "exited", "dead":
		return StatusStopped
	case "paused":
		return StatusPaused
	case "created":
		return StatusCreated
	case "restarting":
		return StatusRestarting
	default:
		return Muted
	}
}

// GetStatusStyleFromString returns the appropriate style for a container status string
func GetStatusStyleFromString(status string) lipgloss.Style {
	switch status {
	case "running":
		return StatusRunning
	case "stopped", "exited", "dead":
		return StatusStopped
	case "paused":
		return StatusPaused
	case "created":
		return StatusCreated
	case "restarting":
		return StatusRestarting
	default:
		return Muted
	}
}

// GetHealthStyle returns the appropriate style for a health status
func GetHealthStyle(health string) lipgloss.Style {
	switch health {
	case "healthy":
		return HealthHealthy
	case "unhealthy":
		return HealthUnhealthy
	case "starting":
		return HealthStarting
	default:
		return Muted
	}
}

// GetLogStyle returns the appropriate style for a log stream
func GetLogStyle(stream interface{}) lipgloss.Style {
	switch string(stream.(type)) {
	case "stderr":
		return LogStderr
	default:
		return LogStdout
	}
}

// GetLogStyleFromString returns the appropriate style for a log stream string
func GetLogStyleFromString(stream string) lipgloss.Style {
	switch stream {
	case "stderr":
		return LogStderr
	default:
		return LogStdout
	}
}