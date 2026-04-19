package views

import (
	"fmt"
	"strings"

	"github.com/charmbracelet/lipgloss"
	"github.com/dockerwatch/dockerwatch/internal/models"
	"github.com/dockerwatch/dockerwatch/internal/tui"
)

func RenderCharts(m interface{}) string {
	model := m.(tui.Model)

	container := model.GetContainer()
	if container == nil {
		return tui.StyleMuted.Render("No container selected")
	}

	history := model.GetStatsHistory(container.ID)
	if len(history) == 0 {
		return tui.StyleMuted.Render("No stats history available. Wait for data collection...")
	}

	var s strings.Builder

	header := fmt.Sprintf(" ← Back to Dashboard              Charts: %s\n",
		tui.StyleAccent.Render(container.Name))
	header += tui.StyleBorder.Render(strings.Repeat("─", 80)) + "\n"
	s.WriteString(header)

	s.WriteString(renderFullChart(history, "CPU Usage", func(s *models.Stats) float64 {
		return s.CPU.Percentage
	}, 100, 30))

	s.WriteString(renderFullChart(history, "Memory Usage", func(s *models.Stats) float64 {
		return s.Memory.Percentage
	}, 100, 30))

	s.WriteString(renderNetworkChart(history, 30))

	s.WriteString("\n" + tui.StyleMuted.Render("  [←] Back to Details\n"))

	return s.String()
}

func renderFullChart(history []models.Stats, title string, getValue func(*models.Stats) float64, maxVal, width int) string {
	var lines []string

	lines = append(lines, fmt.Sprintf("┌─ %s ────────────────────────────────────────────────────┐", title))

	max := float64(0)
	for i := range history {
		val := getValue(&history[i])
		if val > max {
			max = val
		}
	}
	if max == 0 {
		max = float64(maxVal)
	}

	chartWidth := 70
	chart := make([]rune, chartWidth)

	for i := 0; i < chartWidth; i++ {
		idx := (len(history) * i) / chartWidth
		if idx >= len(history) {
			idx = len(history) - 1
		}
		val := getValue(&history[idx])
		barLen := int((val / max) * float64(chartWidth-2))
		if barLen > chartWidth-2 {
			barLen = chartWidth - 2
		}
		chart[i] = '█'
		for j := 1; j <= barLen; j++ {
			if i-j >= 0 {
				chart[i-j] = '▄'
			}
		}
	}

	chartStr := string(chart)
	lines = append(lines, fmt.Sprintf("│ %s │", chartStr))
	lines = append(lines, fmt.Sprintf("│ 0%% %66s%.0f%% │", "", max))
	lines = append(lines, "└───────────────────────────────────────────────────────────────────┘")

	return lipgloss.JoinVertical(lipgloss.Left, lines...) + "\n\n"
}

func renderNetworkChart(history []models.Stats, width int) string {
	var lines []string

	lines = append(lines, "┌─ Network I/O ─────────────────────────────────────────────────┐")

	var totalRx, totalTx uint64
	for _, s := range history {
		totalRx += s.Network.RxBytes
		totalTx += s.Network.TxBytes
	}

	maxTotal := totalRx
	if totalTx > maxTotal {
		maxTotal = totalTx
	}

	rxBarLen := int((float64(totalRx) / float64(maxTotal+1)) * 33)
	txBarLen := int((float64(totalTx) / float64(maxTotal+1)) * 33)

	rxBar := strings.Repeat("█", rxBarLen)
	txBar := strings.Repeat("█", txBarLen)

	lines = append(lines, fmt.Sprintf("│ RX: %-33s %d bytes │",
		tui.StyleNetwork.Render(rxBar), totalRx))
	lines = append(lines, fmt.Sprintf("│ TX: %-33s %d bytes │",
		tui.StylePrimary.Render(txBar), totalTx))
	lines = append(lines, "└───────────────────────────────────────────────────────────────────┘")

	return lipgloss.JoinVertical(lipgloss.Left, lines...) + "\n\n"
}