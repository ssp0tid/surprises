package views

import (
	"fmt"
	"strings"

	"github.com/charmbracelet/lipgloss"
	"github.com/dockerwatch/dockerwatch/internal/models"
	"github.com/dockerwatch/dockerwatch/internal/tui"
	"github.com/dockerwatch/dockerwatch/internal/utils"
)

func RenderDetails(m interface{}) string {
	model := m.(tui.Model)

	container := model.GetContainer()
	if container == nil {
		return tui.StyleMuted.Render("No container selected")
	}

	stats := model.GetStats(container.ID)
	history := model.GetStatsHistory(container.ID)

	var s strings.Builder

	header := fmt.Sprintf(" ← Back to Dashboard              Container: %s\n",
		tui.StyleAccent.Render(container.Name))
	header += tui.StyleBorder.Render(strings.Repeat("─", 80)) + "\n"
	s.WriteString(header)

	s.WriteString(renderContainerInfo(container))

	if stats != nil {
		s.WriteString(renderResourceUsage(stats))
	}

	if len(history) > 0 {
		s.WriteString(renderSimpleChart(history, "CPU", 40))
	}

	s.WriteString(renderDetailActions(container))

	return s.String()
}

func renderContainerInfo(c *models.Container) string {
	var lines []string

	lines = append(lines, "┌─ Container Info ─────────────────────────────────────────────┐")
	lines = append(lines, fmt.Sprintf("│  ID:       %-50s│", c.ShortID))
	lines = append(lines, fmt.Sprintf("│  Name:     %-50s│", c.Name))
	lines = append(lines, fmt.Sprintf("│  Image:    %-50s│", c.Image))

	status := string(c.Status)
	if c.Health != "" && c.Health != models.HealthNone {
		statusStyle := tui.GetHealthStyle(string(c.Health))
		status = fmt.Sprintf("%s (%s)", status, statusStyle.Render(string(c.Health)))
	}
	lines = append(lines, fmt.Sprintf("│  Status:   %-50s│", status))
	lines = append(lines, fmt.Sprintf("│  Created:  %-50s│", c.Created.Format("2006-01-02 15:04:05")))

	if len(c.Ports) > 0 {
		var portStrs []string
		for _, p := range c.Ports {
			if p.HostPort != "" {
				portStrs = append(portStrs, fmt.Sprintf("%s:%s→%s/%s", p.HostIP, p.HostPort, p.ContainerPort, p.Protocol))
			} else {
				portStrs = append(portStrs, fmt.Sprintf("%s/%s", p.ContainerPort, p.Protocol))
			}
		}
		ports := strings.Join(portStrs, ", ")
		lines = append(lines, fmt.Sprintf("│  Ports:    %-50s│", utils.Truncate(ports, 48)))
	}

	lines = append(lines, "└────────────────────────────────────────────────────────────┘")

	return lipgloss.JoinVertical(lipgloss.Left, lines...) + "\n\n"
}

func renderResourceUsage(stats *models.Stats) string {
	var lines []string

	lines = append(lines, "┌─ Resource Usage ──────────────────┐  ┌─ Network I/O ────────────┐")

	cpuStr := fmt.Sprintf("%.1f%% (%d cores)", stats.CPU.Percentage, stats.CPU.OnlineCPUs)
	memStr := fmt.Sprintf("%s / %s (%.1f%%)",
		utils.FormatBytes(stats.Memory.Usage),
		utils.FormatBytes(stats.Memory.Limit),
		stats.Memory.Percentage)
	swapStr := fmt.Sprintf("%s / %s",
		utils.FormatBytes(stats.Memory.SwapUsage),
		utils.FormatBytes(stats.Memory.SwapLimit))

	rxStr := utils.FormatBytes(stats.Network.RxBytes)
	txStr := utils.FormatBytes(stats.Network.TxBytes)
	packetsStr := fmt.Sprintf("%d / %d", stats.Network.RxPackets, stats.Network.TxPackets)
	errorsStr := fmt.Sprintf("%d / %d", stats.Network.RxErrors, stats.Network.TxErrors)

	lines = append(lines, fmt.Sprintf("│  CPU:     %-24s│  │  RX: %-20s│",
		tui.StyleCPU.Render(cpuStr), rxStr))
	lines = append(lines, fmt.Sprintf("│  Memory:  %-24s│  │  TX: %-20s│",
		tui.StyleMemory.Render(memStr), txStr))
	lines = append(lines, fmt.Sprintf("│  Swap:    %-24s│  │  Packets: %-17s│", swapStr, packetsStr))
	lines = append(lines, fmt.Sprintf("│  PIDs:    %-24d│  │  Errors: %-18s│", stats.PIDs, errorsStr))
	lines = append(lines, "└───────────────────────────────────┘  └──────────────────────────┘")

	return lipgloss.JoinVertical(lipgloss.Left, lines...) + "\n\n"
}

func renderSimpleChart(history []models.Stats, label string, width int) string {
	if len(history) < 2 {
		return ""
	}

	var lines []string
	lines = append(lines, fmt.Sprintf("┌─ %s Chart (last %ds) ────────────────────────────────────────┐",
		label, len(history)))

	maxVal := float64(0)
	for _, s := range history {
		val := s.CPU.Percentage
		if val > maxVal {
			maxVal = val
		}
	}
	if maxVal == 0 {
		maxVal = 100
	}

	chart := make([]string, 3)
	for i := 0; i < width; i++ {
		idx := (len(history) * i) / width
		if idx >= len(history) {
			idx = len(history) - 1
		}
		val := history[idx].CPU.Percentage
		barLen := int((val / maxVal) * float64(8))
		chart[0] += "█"
		chart[1] += strings.Repeat("▀", barLen)
		chart[2] += strings.Repeat(" ", barLen)
	}

	lines = append(lines, fmt.Sprintf("│ %s %4.0f%% │", chart[0], maxVal))
	lines = append(lines, fmt.Sprintf("│ %-70s│", chart[1]))
	lines = append(lines, fmt.Sprintf("│ 0%% %67s│", ""))
	lines = append(lines, "└─────────────────────────────────────────────────────────────────────┘")

	return lipgloss.JoinVertical(lipgloss.Left, lines...) + "\n\n"
}

func renderDetailActions(c *models.Container) string {
	actions := []string{
		"[s] Start",
		"[x] Stop",
		"[r] Restart",
		"[l] Logs",
		"[c] Charts",
	}

	return tui.StyleMuted.Render(strings.Join(actions, "  ")) + "\n"
}