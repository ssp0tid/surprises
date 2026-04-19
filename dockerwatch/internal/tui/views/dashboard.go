package views

import (
	"fmt"
	"strings"
	"time"

	"github.com/charmbracelet/lipgloss"
	"github.com/dockerwatch/dockerwatch/internal/models"
	"github.com/dockerwatch/dockerwatch/internal/tui"
	"github.com/dockerwatch/dockerwatch/internal/utils"
)

func RenderDashboard(m interface{}) string {
	model := m.(tui.Model)

	var s strings.Builder

	header := buildDashboardHeader()
	s.WriteString(header)

	containers := model.FilteredContainers()

	if len(containers) == 0 {
		s.WriteString(renderEmptyState())
		return s.String()
	}

	for i, c := range containers {
		row := renderContainerRow(c, model, i == model.Cursor)
		s.WriteString(row)
	}

	s.WriteString(renderStatsSummary(model))

	return s.String()
}

func buildDashboardHeader() string {
	headers := []string{
		"CONTAINER",
		"STATUS",
		"CPU",
		"MEMORY",
		"NETWORK",
		"UPTIME",
	}

	widths := []int{25, 10, 8, 12, 15, 10}

	var parts []string
	for i, h := range headers {
		parts = append(parts, tui.StyleTableHeader.Width(widths[i]).Render(h))
	}

	return lipgloss.JoinHorizontal(lipgloss.Top, parts...) + "\n" +
		tui.StyleBorder.Render(strings.Repeat("─", 80)) + "\n"
}

func renderContainerRow(c models.Container, m tui.Model, selected bool) string {
	var parts []string

	nameStyle := tui.StyleContainerName
	if selected {
		nameStyle = tui.StyleContainerSelected
	}
	name := utils.Truncate(c.Name, 23)
	if selected {
		name = "▶ " + name
	}
	parts = append(parts, nameStyle.Width(25).Render(name))

	status := string(c.Status)
	if c.Health != "" && c.Health != models.HealthNone {
		status = fmt.Sprintf("%s (%s)", status, c.Health)
	}
	parts = append(parts, tui.GetStatusStyleFromString(string(c.Status)).Width(10).Render(status))

	stats := m.GetStats(c.ID)
	cpuStr := "-"
	if stats != nil {
		cpuStr = fmt.Sprintf("%.1f%%", stats.CPU.Percentage)
	}
	parts = append(parts, tui.StyleCPU.Width(8).Render(cpuStr))

	memStr := "-"
	if stats != nil {
		memStr = utils.FormatBytes(stats.Memory.Usage)
	}
	parts = append(parts, tui.StyleMemory.Width(12).Render(memStr))

	netStr := "-"
	if stats != nil {
		rx := utils.FormatBytes(stats.Network.RxBytes)
		tx := utils.FormatBytes(stats.Network.TxBytes)
		netStr = fmt.Sprintf("%s/%s", rx, tx)
	}
	parts = append(parts, tui.StyleNetwork.Width(15).Render(netStr))

	uptimeStr := "-"
	if c.Status == models.StatusRunning {
		uptimeStr = utils.FormatDuration(time.Since(c.Created))
	}
	parts = append(parts, tui.StyleMuted.Width(10).Render(uptimeStr))

	row := lipgloss.JoinHorizontal(lipgloss.Top, parts...)

	if !selected {
		return row + "\n"
	}
	return tui.StyleSurface.Render(row) + "\n"
}

func renderEmptyState() string {
	empty := tui.StyleMuted.Render("  No containers found  ")
	return lipgloss.Place(80, 10, lipgloss.Center, lipgloss.Center, empty) + "\n"
}

func renderStatsSummary(m tui.Model) string {
	history := m.GetStatsHistory("")
	if len(history) == 0 {
		return ""
	}

	var totalCPU, totalMem float64
	count := 0

	for _, stats := range m.Stats {
		if stats != nil {
			totalCPU += stats.CPU.Percentage
			totalMem += stats.Memory.Percentage
			count++
		}
	}

	if count == 0 {
		return ""
	}

	avgCPU := totalCPU / float64(count)
	avgMem := totalMem / float64(count)

	cpuBar := buildProgressBar(avgCPU, 100)
	memBar := buildProgressBar(avgMem, 100)

	summary := fmt.Sprintf("\n%s CPU: %s %.1f%%  Memory: %s %.1f%%",
		tui.StyleMuted.Render("Total:"),
		cpuBar, avgCPU,
		memBar, avgMem,
	)

	return summary
}

func buildProgressBar(percent, max float64) string {
	width := 20
	filled := int((percent / max) * float64(width))
	if filled > width {
		filled = width
	}

	empty := strings.Repeat("░", width-filled)
	filled_str := strings.Repeat("█", filled)

	return tui.StyleProgressFill.Render(filled_str) +
		tui.StyleProgressEmpty.Render(empty)
}