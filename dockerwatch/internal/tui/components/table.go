package components

import (
	"fmt"
	"strings"

	"github.com/charmbracelet/lipgloss"
	"github.com/dockerwatch/dockerwatch/internal/models"
	"github.com/dockerwatch/dockerwatch/internal/utils"
)

type Table struct {
	Headers []string
	Widths  []int
	Rows    [][]string
}

func NewTable() *Table {
	return &Table{
		Headers: []string{},
		Widths:  []int{},
		Rows:    [][]string{},
	}
}

func (t *Table) SetHeaders(headers []string, widths []int) {
	t.Headers = headers
	t.Widths = widths
}

func (t *Table) AddRow(row []string) {
	t.Rows = append(t.Rows, row)
}

func (t *Table) Render() string {
	if len(t.Headers) == 0 {
		return ""
	}

	var result strings.Builder

	headerStyle := lipgloss.NewStyle().Bold(true).Foreground(lipgloss.Color("245"))
	for i, h := range t.Headers {
		width := 10
		if i < len(t.Widths) {
			width = t.Widths[i]
		}
		result.WriteString(headerStyle.Width(width).Render(h))
	}
	result.WriteString("\n")

	borderStyle := lipgloss.NewStyle().Foreground(lipgloss.Color("240"))
	result.WriteString(borderStyle.Render(strings.Repeat("─", 82)) + "\n")

	for _, row := range t.Rows {
		for i, cell := range row {
			width := 10
			if i < len(t.Widths) {
				width = t.Widths[i]
			}
			cellStyle := lipgloss.NewStyle().Foreground(lipgloss.Color("252"))
			result.WriteString(cellStyle.Width(width).Render(utils.Truncate(cell, width-2)))
		}
		result.WriteString("\n")
	}

	return result.String()
}

func (t *Table) RenderContainerRow(c models.Container, stats *models.Stats, selected bool, width int) string {
	name := c.Name
	if selected {
		name = "▶ " + name
	}

	status := string(c.Status)
	cpuStr := "-"
	memStr := "-"
	netStr := "-"
	uptimeStr := "-"

	if stats != nil {
		cpuStr = fmt.Sprintf("%.1f%%", stats.CPU.Percentage)
		memStr = utils.FormatBytes(stats.Memory.Usage)
		netStr = fmt.Sprintf("%s/%s",
			utils.FormatBytes(stats.Network.RxBytes),
			utils.FormatBytes(stats.Network.TxBytes))
	}

	if c.Status == models.StatusRunning {
		uptimeStr = utils.FormatDuration(utils.Duration(c.Created))
	}

	row := fmt.Sprintf(" %-25s %-12s %-8s %-12s %-15s %-10s\n",
		truncateWidth(name, 25),
		status,
		cpuStr,
		memStr,
		netStr,
		uptimeStr,
	)

	if selected {
		style := lipgloss.NewStyle().Background(lipgloss.Color("238"))
		row = style.Render(row)
	}

	return row
}

func truncateWidth(s string, width int) string {
	if len(s) >= width {
		return s[:width-3] + "..."
	}
	return s
}
