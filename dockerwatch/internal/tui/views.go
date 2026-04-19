package tui

import (
	"fmt"
	"strings"

	"github.com/charmbracelet/lipgloss"
	"github.com/dockerwatch/dockerwatch/internal/models"
	"github.com/dockerwatch/dockerwatch/internal/utils"
)

func Render(m Model) string {
	var s strings.Builder

	switch m.View {
	case ViewDashboard:
		s.WriteString(renderDashboard(m))
	case ViewDetails:
		s.WriteString(renderDetails(m))
	case ViewLogs:
		s.WriteString(renderLogs(m))
	case ViewCharts:
		s.WriteString(renderCharts(m))
	case ViewHelp:
		s.WriteString(renderHelp(m))
	}

	return s.String()
}

func renderDashboard(m Model) string {
	var s strings.Builder

	s.WriteString(StyleTitle.Render(" DockerWatch ") + "\n")
	s.WriteString(StyleBorder.Render(strings.Repeat("─", 80)) + "\n")

	if len(m.Notifications) > 0 {
		notif := m.Notifications[len(m.Notifications)-1]
		style := StyleMuted
		if notif.Type == TypeError {
			style = lipgloss.NewStyle().Foreground(lipgloss.Color("204"))
		} else if notif.Type == TypeSuccess {
			style = lipgloss.NewStyle().Foreground(lipgloss.Color("82"))
		}
		s.WriteString(style.Render(" "+notif.Message) + "\n")
	}

	s.WriteString("\n")

	containers := m.Containers
	if m.Filter != "" {
		var filtered []models.Container
		for _, c := range containers {
			if strings.Contains(strings.ToLower(c.Name), strings.ToLower(m.Filter)) ||
			   strings.Contains(strings.ToLower(c.Image), strings.ToLower(m.Filter)) {
				filtered = append(filtered, c)
			}
		}
		containers = filtered
	}

	if len(containers) == 0 {
		s.WriteString(StyleMuted.Render("  No containers found  ") + "\n")
		return s.String()
	}

	s.WriteString(fmt.Sprintf(" %-25s %-12s %-8s %-12s %-15s %-10s\n",
		StyleTableHeader.Render("CONTAINER"),
		StyleTableHeader.Render("STATUS"),
		StyleTableHeader.Render("CPU"),
		StyleTableHeader.Render("MEMORY"),
		StyleTableHeader.Render("NETWORK"),
		StyleTableHeader.Render("UPTIME"),
	))
	s.WriteString(StyleBorder.Render(strings.Repeat("─", 82)) + "\n")

	for i, c := range containers {
		selected := i == m.Cursor
		row := renderContainerRow(c, m, selected)
		s.WriteString(row)
	}

	s.WriteString("\n")
	s.WriteString(StyleMuted.Render(" [↑↓] Navigate  [Enter] Details  [s] Start  [x] Stop  [r] Restart  [l] Logs  [?] Help  [q] Quit\n"))

	return s.String()
}

func renderContainerRow(c models.Container, m Model, selected bool) string {
	name := utils.Truncate(c.Name, 23)
	if selected {
		name = "▶ " + name
	}

	status := string(c.Status)
	nameStyle := StyleContainerName
	if selected {
		nameStyle = StyleContainerSelected
	}

	cpuStr := "-"
	stats := m.GetStats(c.ID)
	if stats != nil {
		cpuStr = fmt.Sprintf("%.1f%%", stats.CPU.Percentage)
	}

	memStr := "-"
	if stats != nil {
		memStr = utils.FormatBytes(stats.Memory.Usage)
	}

	netStr := "-"
	if stats != nil {
		rx := utils.FormatBytes(stats.Network.RxBytes)
		tx := utils.FormatBytes(stats.Network.TxBytes)
		netStr = fmt.Sprintf("%s/%s", rx, tx)
	}

	uptimeStr := "-"
	if c.Status == models.StatusRunning {
		uptimeStr = utils.FormatDuration(utils.Duration(c.Created))
	}

	return fmt.Sprintf(" %-25s %v %-8s %-12s %-15s %-10s\n",
		nameStyle.Width(25).Render(name),
		GetStatusStyle(c.Status).Width(12).Render(status),
		StyleCPU.Width(8).Render(cpuStr),
		StyleMemory.Width(12).Render(memStr),
		StyleNetwork.Width(15).Render(netStr),
		StyleMuted.Width(10).Render(uptimeStr),
	)
}

func renderDetails(m Model) string {
	var s strings.Builder

	container := m.SelectedContainer
	if container == nil {
		s.WriteString(StyleMuted.Render(" No container selected ") + "\n")
		return s.String()
	}

	s.WriteString(StyleBorder.Render("─") + " Details: " + StyleAccent.Render(container.Name) + "\n")
	s.WriteString(StyleBorder.Render(strings.Repeat("─", 80)) + "\n\n")

	s.WriteString(fmt.Sprintf(" ID:       %s\n", container.ShortID))
	s.WriteString(fmt.Sprintf(" Name:     %s\n", container.Name))
	s.WriteString(fmt.Sprintf(" Image:    %s\n", container.Image))
	s.WriteString(fmt.Sprintf(" Status:   %v\n", GetStatusStyle(container.Status).Render(string(container.Status))))
	s.WriteString(fmt.Sprintf(" Created:  %s\n\n", container.Created.Format("2006-01-02 15:04:05")))

	stats := m.GetStats(container.ID)
	if stats != nil {
		s.WriteString(" Resource Usage:\n")
		s.WriteString(fmt.Sprintf("  CPU:     %s (%.1f%%)\n", StyleCPU.Render("usage"), stats.CPU.Percentage))
		s.WriteString(fmt.Sprintf("  Memory:  %s / %s (%.1f%%)\n",
			StyleMemory.Render(utils.FormatBytes(stats.Memory.Usage)),
			utils.FormatBytes(stats.Memory.Limit),
			stats.Memory.Percentage,
		))
		s.WriteString(fmt.Sprintf("  Network: RX: %s  TX: %s\n\n",
			utils.FormatBytes(stats.Network.RxBytes),
			utils.FormatBytes(stats.Network.TxBytes),
		))
	}

	s.WriteString(StyleMuted.Render(" [↑↓] Navigate  [l] Logs  [c] Charts  [←] Back\n"))

	return s.String()
}

func renderLogs(m Model) string {
	var s strings.Builder

	container := m.SelectedContainer
	if container == nil {
		s.WriteString(StyleMuted.Render(" No container selected ") + "\n")
		return s.String()
	}

	s.WriteString(StyleBorder.Render("─") + " Logs: " + StyleAccent.Render(container.Name) + "\n")
	s.WriteString(StyleBorder.Render(strings.Repeat("─", 80)) + "\n\n")

	logs := m.GetLogs(container.ID)
	if len(logs) == 0 {
		s.WriteString(StyleMuted.Render("  No logs available  ") + "\n")
	} else {
		for _, entry := range logs {
			var line string
			if m.LogsTimestamps {
				line = fmt.Sprintf("%s ", StyleLogTimestamp.Render(entry.Timestamp.Format("15:04:05")))
			}
			stream := "│"
			if entry.Stream == models.StreamStderr {
				stream = "!"
			}
			line += stream + " " + entry.Message
			if entry.Stream == models.StreamStderr {
				s.WriteString(StyleLogStderr.Render(line))
			} else {
				s.WriteString(StyleLogStdout.Render(line))
			}
			s.WriteString("\n")
		}
	}

	s.WriteString("\n" + StyleMuted.Render(" [↑↓] Scroll  [f] Follow  [t] Timestamps  [←] Back\n"))

	return s.String()
}

func renderCharts(m Model) string {
	var s strings.Builder

	container := m.SelectedContainer
	if container == nil {
		s.WriteString(StyleMuted.Render(" No container selected ") + "\n")
		return s.String()
	}

	s.WriteString(StyleBorder.Render("─") + " Charts: " + StyleAccent.Render(container.Name) + "\n")
	s.WriteString(StyleBorder.Render(strings.Repeat("─", 80)) + "\n\n")

	history := m.GetStatsHistory(container.ID)
	if len(history) == 0 {
		s.WriteString(StyleMuted.Render("  Collecting data...  ") + "\n")
	} else {
		s.WriteString(StyleMuted.Render(" CPU History (last 60s):\n"))
		s.WriteString(renderSimpleChart(history, 70))
	}

	s.WriteString("\n" + StyleMuted.Render(" [←] Back to Details\n"))

	return s.String()
}

func renderSimpleChart(history []models.Stats, width int) string {
	if len(history) == 0 {
		return ""
	}

	maxVal := float64(0)
	for _, s := range history {
		if s.CPU.Percentage > maxVal {
			maxVal = s.CPU.Percentage
		}
	}
	if maxVal == 0 {
		maxVal = 100
	}

	var chart strings.Builder
	for i := 0; i < width; i++ {
		idx := (len(history) * i) / width
		if idx >= len(history) {
			idx = len(history) - 1
		}
		val := history[idx].CPU.Percentage
		barLen := int((val / maxVal) * float64(8))
		if barLen > 8 {
			barLen = 8
		}
		chart.WriteString(strings.Repeat("█", barLen+1))
	}

	return " " + StyleProgressFill.Render(chart.String()) + "\n"
}

func renderHelp(m Model) string {
	var s strings.Builder

	s.WriteString(StyleTitle.Render(" DockerWatch Help ") + "\n")
	s.WriteString(StyleBorder.Render(strings.Repeat("─", 80)) + "\n\n")

	s.WriteString(" " + StyleHeader.Render("Global Shortcuts") + "\n")
	s.WriteString("   q, Ctrl+C        Quit application\n")
	s.WriteString("   ?                Toggle this help\n")
	s.WriteString("   r                Refresh container list\n")
	s.WriteString("   Tab              Cycle through views\n\n")

	s.WriteString(" " + StyleHeader.Render("Dashboard View") + "\n")
	s.WriteString("   ↑ / k            Move cursor up\n")
	s.WriteString("   ↓ / j            Move cursor down\n")
	s.WriteString("   Enter            Open container details\n")
	s.WriteString("   s                Start selected container\n")
	s.WriteString("   x                Stop selected container\n")
	s.WriteString("   r                Restart selected container\n")
	s.WriteString("   l                View container logs\n\n")

	s.WriteString(" " + StyleHeader.Render("Details View") + "\n")
	s.WriteString("   ← / Esc          Back to dashboard\n")
	s.WriteString("   l                View logs\n")
	s.WriteString("   c                View charts\n\n")

	s.WriteString("\n" + StyleMuted.Render(" Press ? to return to dashboard ") + "\n")

	return s.String()
}
