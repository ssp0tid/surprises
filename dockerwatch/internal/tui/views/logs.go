package views

import (
	"fmt"
	"strings"

	"github.com/charmbracelet/lipgloss"
	"github.com/dockerwatch/dockerwatch/internal/models"
	"github.com/dockerwatch/dockerwatch/internal/tui"
)

func RenderLogs(m interface{}) string {
	model := m.(tui.Model)

	container := model.GetContainer()
	if container == nil {
		return tui.StyleMuted.Render("No container selected")
	}

	var s strings.Builder

	header := fmt.Sprintf(" ← Back to Dashboard              Logs: %s\n",
		tui.StyleAccent.Render(container.Name))
	header += tui.StyleBorder.Render(strings.Repeat("─", 80)) + "\n"
	s.WriteString(header)

	filters := renderLogFilters(model)
	s.WriteString(filters)

	logs := model.GetLogs(container.ID)

	if len(logs) == 0 {
		s.WriteString(tui.StyleMuted.Render("  No logs available  "))
		s.WriteString("\n")
	} else {
		for _, entry := range logs {
			s.WriteString(renderLogEntry(entry, model.LogsTimestamps))
		}
	}

	s.WriteString(renderLogActions(model))

	return s.String()
}

func renderLogFilters(m tui.Model) string {
	filters := fmt.Sprintf("  [Follow: %s] [Timestamps: %s] [c: Clear] [s: Save]\n\n",
		boolToStr(m.LogsFollow),
		boolToStr(m.LogsTimestamps))
	return tui.StyleMuted.Render(filters)
}

func renderLogEntry(entry models.LogEntry, showTimestamp bool) string {
	var parts []string

	if showTimestamp {
		ts := entry.Timestamp.Format("2006-01-02 15:04:05")
		parts = append(parts, tui.StyleLogTimestamp.Render(ts))
	}

	streamIndicator := "│"
	if entry.Stream == models.StreamStderr {
		streamIndicator = "!"
		parts = append(parts, tui.StyleLogStderr.Render(streamIndicator))
	} else {
		parts = append(parts, streamIndicator)
	}

	parts = append(parts, " ")

	style := tui.GetLogStyleFromString(string(entry.Stream))
	parts = append(parts, style.Render(entry.Message))

	return lipgloss.JoinHorizontal(lipgloss.Left, parts...) + "\n"
}

func renderLogActions(m tui.Model) string {
	followStr := "○"
	if m.LogsFollow {
		followStr = "●"
	}

	actions := fmt.Sprintf("  [%s Follow] [↑↓ Scroll] [g: Top] [G: Bottom] [t: Timestamps]\n",
		followStr)
	return tui.StyleMuted.Render(actions)
}

func boolToStr(b bool) string {
	if b {
		return "ON "
	}
	return "OFF"
}