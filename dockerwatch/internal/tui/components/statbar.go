package components

import (
	"fmt"
	"strings"

	"github.com/charmbracelet/lipgloss"
	"github.com/dockerwatch/dockerwatch/internal/models"
	"github.com/dockerwatch/dockerwatch/internal/utils"
)

type StatusBar struct {
	Width int
}

func NewStatusBar() *StatusBar {
	return &StatusBar{Width: 80}
}

func (s *StatusBar) RenderStats(stats *models.Stats) string {
	if stats == nil {
		return ""
	}

	var parts []string

	cpuStyle := lipgloss.NewStyle().Foreground(lipgloss.Color("86"))
	cpuStr := fmt.Sprintf("CPU: %s", cpuStyle.Render(fmt.Sprintf("%.1f%%", stats.CPU.Percentage)))
	parts = append(parts, cpuStr)

	memStyle := lipgloss.NewStyle().Foreground(lipgloss.Color("75"))
	memStr := fmt.Sprintf("Mem: %s", memStyle.Render(fmt.Sprintf("%s / %s",
		utils.FormatBytes(stats.Memory.Usage),
		utils.FormatBytes(stats.Memory.Limit))))
	parts = append(parts, memStr)

	netStyle := lipgloss.NewStyle().Foreground(lipgloss.Color("39"))
	netStr := fmt.Sprintf("Net: %s", netStyle.Render(fmt.Sprintf("%s / %s",
		utils.FormatBytes(stats.Network.RxBytes),
		utils.FormatBytes(stats.Network.TxBytes))))
	parts = append(parts, netStr)

	barStyle := lipgloss.NewStyle().Foreground(lipgloss.Color("240"))
	bar := barStyle.Render(" | ")

	return bar + strings.Join(parts, barStyle.Render(" | "))
}

func (s *StatusBar) RenderProgressBar(label string, current, max float64, width int) string {
	if max == 0 {
		max = 100
	}

	percent := current / max
	if percent > 1 {
		percent = 1
	}

	filled := int(percent * float64(width))
	empty := width - filled

	emptyStyle := lipgloss.NewStyle().Foreground(lipgloss.Color("240"))
	filledStyle := lipgloss.NewStyle().Foreground(lipgloss.Color("82"))

	bar := strings.Repeat("█", filled) + strings.Repeat("░", empty)

	return fmt.Sprintf("%s [%s%s] %.1f%%",
		label,
		filledStyle.Render(strings.Repeat("█", filled)),
		emptyStyle.Render(strings.Repeat("░", empty)),
		current)
}

func (s *StatusBar) RenderContainerStatus(c models.Container) string {
	statusStyle := lipgloss.NewStyle()

	switch c.Status {
	case models.StatusRunning:
		statusStyle = statusStyle.Foreground(lipgloss.Color("82"))
	case models.StatusStopped, models.StatusExited, models.StatusDead:
		statusStyle = statusStyle.Foreground(lipgloss.Color("204"))
	case models.StatusPaused:
		statusStyle = statusStyle.Foreground(lipgloss.Color("220"))
	default:
		statusStyle = statusStyle.Foreground(lipgloss.Color("245"))
	}

	return statusStyle.Render(string(c.Status))
}
