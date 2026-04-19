package main

import (
	"os"

	"github.com/apitest/apitest/internal/app"
	tea "github.com/charmbracelet/bubbletea"
)

func main() {
	p := tea.NewProgram(app.NewModel(), tea.WithAltScreen())
	if _, err := p.Run(); err != nil {
		os.Exit(1)
	}
}