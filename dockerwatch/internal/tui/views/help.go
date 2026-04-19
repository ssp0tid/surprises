package views

import (
	"fmt"
	"strings"

	"github.com/charmbracelet/lipgloss"
	"github.com/dockerwatch/dockerwatch/internal/tui"
)

func RenderHelp(m interface{}) string {
	var s strings.Builder

	s.WriteString(tui.StyleTitle.Render(" DockerWatch Help ") + "\n")
	s.WriteString(tui.StyleBorder.Render(strings.Repeat("─", 80)) + "\n\n")

	s.WriteString(renderHelpSection("Global Shortcuts", [][]string{
		{"q, Ctrl+C", "Quit application"},
		{"?", "Toggle this help"},
		{"r", "Refresh container list"},
		{"Tab", "Cycle through views"},
	}))

	s.WriteString(renderHelpSection("Dashboard View", [][]string{
		{"↑ / k", "Move cursor up"},
		{"↓ / j", "Move cursor down"},
		{"Enter", "Open container details"},
		{"s", "Start selected container"},
		{"x", "Stop selected container"},
		{"r", "Restart selected container"},
		{"d", "Remove selected container"},
		{"l", "View container logs"},
	}))

	s.WriteString(renderHelpSection("Details View", [][]string{
		{"← / Esc", "Back to dashboard"},
		{"s", "Start container"},
		{"x", "Stop container"},
		{"r", "Restart container"},
		{"l", "View logs"},
		{"c", "View charts"},
	}))

	s.WriteString(renderHelpSection("Logs View", [][]string{
		{"↑ / k", "Scroll up"},
		{"↓ / j", "Scroll down"},
		{"f", "Toggle follow mode"},
		{"t", "Toggle timestamps"},
		{"c", "Clear logs"},
		{"← / Esc", "Back"},
	}))

	s.WriteString("\n" + tui.StyleMuted.Render(" Press ? to return to dashboard ") + "\n")

	return s.String()
}

func renderHelpSection(title string, shortcuts [][]string) string {
	var lines []string

	lines = append(lines, fmt.Sprintf(" %s\n", tui.StyleHeader.Render(title)))

	for _, shortcut := range shortcuts {
		key := tui.StyleHelpKey.Render(shortcut[0])
		desc := tui.StyleHelpDesc.Render(shortcut[1])
		lines = append(lines, fmt.Sprintf("   %-12s %s", key, desc))
	}

	lines = append(lines, "")

	return lipgloss.JoinVertical(lipgloss.Left, lines...)
}