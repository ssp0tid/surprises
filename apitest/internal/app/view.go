package app

import (
	"github.com/apitest/apitest/internal/http"
	"github.com/apitest/apitest/internal/ui"
	"github.com/charmbracelet/lipgloss"
)

func (m *Model) View() string {
	if m.Quitting {
		return "Goodbye!\n"
	}

	var mainContent string

	switch m.CurrentPanel {
	case RequestPanel:
		mainContent = m.renderRequestPanel()
	case ResponsePanel:
		mainContent = m.renderResponsePanel()
	case HistoryPanel:
		mainContent = m.renderHistoryPanel()
	case CollectionsPanel:
		mainContent = m.renderCollectionsPanel()
	}

	helpBar := m.renderHelpBar()

	var statusBar string
	if m.IsLoading {
		statusBar = ui.Subtle.Render("Loading...")
	} else if m.ResponseStatus > 0 {
		statusStyle := ui.GetStatusStyle(m.ResponseStatus)
		statusBar = statusStyle.Render(http.GetStatusText(m.ResponseStatus))
		statusBar += " | " + ui.Subtle.Render(formatDuration(m.ResponseTime))
		statusBar += " | " + ui.Subtle.Render(itoa(m.ResponseLength) + " bytes")
	} else {
		statusBar = ui.Subtle.Render("Ready")
	}

	return mainContent + "\n" + helpBar + "\n" + statusBar
}

func (m *Model) renderRequestPanel() string {
	panelTitle := ui.TitleStyle.Render("Request")

	methodInputLabel := ui.Bold.Render("Method:")
	urlInputLabel := ui.Bold.Render("URL:")

	methodInputView := m.MethodInput.View()
	urlInputView := m.URLInput.View()

	var tabs string
	if m.RequestTab == HeadersTab {
		tabs = ui.TabActiveStyle.Render("Headers") + ui.TabStyle.Render("Body")
	} else {
		tabs = ui.TabStyle.Render("Headers") + ui.TabActiveStyle.Render("Body")
	}

	var tabContent string
	if m.RequestTab == HeadersTab {
		tabContent = m.HeadersInput.View()
	} else {
		tabContent = m.BodyInput.View()
	}

	requestContent := lipgloss.JoinVertical(
		lipgloss.Left,
		panelTitle,
		"",
		methodInputLabel+" "+methodInputView,
		urlInputLabel+" "+urlInputView,
		"",
		tabs,
		tabContent,
	)

	responseTitle := ui.HeaderStyle.Render("Response")
	responseContent := m.ResponseBody.View()

	splitView := lipgloss.JoinVertical(
		lipgloss.Left,
		requestContent,
		"",
		lipgloss.JoinHorizontal(
			lipgloss.Top,
			lipgloss.NewStyle().Width(40).Height(20).Render(responseTitle+"\n\n"+responseContent),
			ui.PanelTitleStyle.Render("Status"),
		),
	)

	return ui.BoxStyle.Render(splitView)
}

func (m *Model) renderResponsePanel() string {
	panelTitle := ui.TitleStyle.Render("Response")

	var tabs string
	if m.ResponseTab == ResponseBodyTab {
		tabs = ui.TabActiveStyle.Render("Body") + ui.TabStyle.Render("Headers")
	} else {
		tabs = ui.TabStyle.Render("Body") + ui.TabActiveStyle.Render("Headers")
	}

	content := m.ResponseBody.View()
	if m.ResponseError != "" {
		content = ui.StatusErrorStyle.Render(m.ResponseError)
	}

	responseContent := lipgloss.JoinVertical(
		lipgloss.Left,
		panelTitle,
		"",
		tabs,
		"",
		content,
	)

	return ui.BoxStyle.Render(responseContent)
}

func (m *Model) renderHistoryPanel() string {
	panelTitle := ui.TitleStyle.Render("History")
	historyList := m.HistoryList.View()
	return ui.BoxStyle.Render(
		lipgloss.JoinVertical(
			lipgloss.Left,
			panelTitle,
			"",
			historyList,
		),
	)
}

func (m *Model) renderCollectionsPanel() string {
	panelTitle := ui.TitleStyle.Render("Collections")
	collectionsList := m.CollectionsList.View()
	return ui.BoxStyle.Render(
		lipgloss.JoinVertical(
			lipgloss.Left,
			panelTitle,
			"",
			collectionsList,
		),
	)
}

func (m *Model) renderHelpBar() string {
	helpItems := []string{
		ui.HelpStyle.Render("ctrl+r") + " send",
		ui.HelpStyle.Render("enter") + " send",
		ui.HelpStyle.Render("tab") + " panel",
		ui.HelpStyle.Render("ctrl+h") + " history",
		ui.HelpStyle.Render("ctrl+c") + " quit",
	}

	helpBar := ""
	for i, item := range helpItems {
		if i > 0 {
			helpBar += "  "
		}
		helpBar += item
	}

	return ui.HelpStyle.Render(helpBar)
}