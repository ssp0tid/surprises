package ui

import "github.com/charmbracelet/lipgloss"

var (
	Subtle    = lipgloss.NewStyle().Foreground(lipgloss.Color("241"))
	Bold      = lipgloss.NewStyle().Bold(true)
	Italic    = lipgloss.NewStyle().Italic(true)

	TitleStyle = lipgloss.NewStyle().
			Foreground(lipgloss.Color("86")).
			Bold(true).
			Padding(0, 1)

	HeaderStyle = lipgloss.NewStyle().
			Foreground(lipgloss.Color("227")).
			Bold(true).
			Padding(0, 1)

	PanelTitleStyle = lipgloss.NewStyle().
				Foreground(lipgloss.Color("75")).
				Bold(true).
			Padding(0, 1)

	BoxStyle = lipgloss.NewStyle().
		Border(lipgloss.NormalBorder()).
		BorderForeground(lipgloss.Color("240")).
		Padding(1)

	SelectedBoxStyle = lipgloss.NewStyle().
			Border(lipgloss.NormalBorder()).
			BorderForeground(lipgloss.Color("75")).
			Foreground(lipgloss.Color("75")).
			Padding(1)

	InputStyle = lipgloss.NewStyle().
			Foreground(lipgloss.Color("255")).
			Background(lipgloss.Color("236")).
			Padding(0, 1)

	ButtonStyle = lipgloss.NewStyle().
			Foreground(lipgloss.Color("255")).
			Background(lipgloss.Color("68")).
			Bold(true).
			Padding(0, 2)

	ButtonFocusedStyle = lipgloss.NewStyle().
				Foreground(lipgloss.Color("255")).
				Background(lipgloss.Color("68")).
				Bold(true).
				Padding(0, 2).
				Underline(true)

	StatusOKStyle = lipgloss.NewStyle().
			Foreground(lipgloss.Color("76"))

	StatusRedirectStyle = lipgloss.NewStyle().
				Foreground(lipgloss.Color("220"))

	StatusErrorStyle = lipgloss.NewStyle().
			Foreground(lipgloss.Color("196"))

	MethodGetStyle    = lipgloss.NewStyle().Foreground(lipgloss.Color("76")).Bold(true)
	MethodPostStyle   = lipgloss.NewStyle().Foreground(lipgloss.Color("220")).Bold(true)
	MethodPutStyle    = lipgloss.NewStyle().Foreground(lipgloss.Color("226")).Bold(true)
	MethodDeleteStyle = lipgloss.NewStyle().Foreground(lipgloss.Color("196")).Bold(true)
	MethodPatchStyle  = lipgloss.NewStyle().Foreground(lipgloss.Color("141")).Bold(true)

	TabStyle = lipgloss.NewStyle().
			Foreground(lipgloss.Color("241")).
			Padding(0, 1)

	TabActiveStyle = lipgloss.NewStyle().
			Foreground(lipgloss.Color("255")).
			Background(lipgloss.Color("68")).
			Padding(0, 1)

	HelpStyle = lipgloss.NewStyle().
			Foreground(lipgloss.Color("241"))

	JSONKeyStyle   = lipgloss.NewStyle().Foreground(lipgloss.Color("75"))
	JSONStringStyle = lipgloss.NewStyle().Foreground(lipgloss.Color("72"))
	JSONNumberStyle = lipgloss.NewStyle().Foreground(lipgloss.Color("218"))
	JSONBoolStyle   = lipgloss.NewStyle().Foreground(lipgloss.Color("209"))
	JSONNullStyle   = lipgloss.NewStyle().Foreground(lipgloss.Color("241"))
)

func GetMethodStyle(method string) lipgloss.Style {
	switch method {
	case "GET":
		return MethodGetStyle
	case "POST":
		return MethodPostStyle
	case "PUT":
		return MethodPutStyle
	case "DELETE":
		return MethodDeleteStyle
	case "PATCH":
		return MethodPatchStyle
	default:
		return MethodGetStyle
	}
}

func GetStatusStyle(code int) lipgloss.Style {
	if code >= 200 && code < 300 {
		return StatusOKStyle
	} else if code >= 300 && code < 400 {
		return StatusRedirectStyle
	}
	return StatusErrorStyle
}