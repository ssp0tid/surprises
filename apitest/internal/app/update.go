package app

import (
	"strings"

	"github.com/apitest/apitest/internal/http"
	tea "github.com/charmbracelet/bubbletea"
	"github.com/charmbracelet/bubbles/list"
)

type (
	executeRequestMsg  struct{}
	requestDoneMsg    struct{ response *http.Response }
	requestFailedMsg struct{ err error }
	updateHistoryMsg  struct{}
)

func (m *Model) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
	var cmd tea.Cmd

	switch msg := msg.(type) {
	case tea.WindowSizeMsg:
		m.ResponseBody.Width = msg.Width - 4
		m.ResponseBody.Height = msg.Height / 2
		return m, nil

	case tea.KeyMsg:
		return m.handleKeyPress(msg)

	case executeRequestMsg:
		return m.executeRequest()

	case requestDoneMsg:
		return m.handleRequestDone(msg)

	case requestFailedMsg:
		return m.handleRequestFailed(msg)

	case updateHistoryMsg:
		return m.updateHistoryList()

	default:
		m.MethodInput, cmd = m.MethodInput.Update(msg)
		m.URLInput, _ = m.URLInput.Update(msg)
		m.HeadersInput, _ = m.HeadersInput.Update(msg)
		m.BodyInput, _ = m.BodyInput.Update(msg)
		m.ResponseBody, _ = m.ResponseBody.Update(msg)
	}

	return m, cmd
}

func (m *Model) handleKeyPress(msg tea.KeyMsg) (tea.Model, tea.Cmd) {
	switch keypress := msg.String(); keypress {
	case "ctrl+c", "q":
		m.Quitting = true
		return m, tea.Quit

	case "tab":
		if m.CurrentPanel == RequestPanel {
			m.CurrentPanel = ResponsePanel
		} else {
			m.CurrentPanel = RequestPanel
		}
		return m, nil

	case "ctrl+h":
		m.CurrentPanel = HistoryPanel
		m.updateHistoryList()
		return m, nil

	case "ctrl+r":
		if m.CurrentURL == "" {
			return m, nil
		}
		m.IsLoading = true
		m.ResponseBody.SetContent("Loading...")
		return m, tea.Cmd(func() tea.Msg {
			return executeRequestMsg{}
		})

	case "ctrl+b":
		m.CurrentPanel = RequestPanel
		if m.RequestTab == HeadersTab {
			m.RequestTab = BodyTab
		} else {
			m.RequestTab = HeadersTab
		}
		return m, nil

	case "1":
		if m.CurrentPanel == HistoryPanel {
			m = m.selectHistoryItem(0)
		}
		return m, nil

	case "2":
		if m.CurrentPanel == HistoryPanel {
			m = m.selectHistoryItem(1)
		}
		return m, nil

	case "3":
		if m.CurrentPanel == HistoryPanel {
			m = m.selectHistoryItem(2)
		}
		return m, nil

	case "enter":
		if m.CurrentPanel == RequestPanel {
			m.CurrentMethod = m.MethodInput.Value()
			m.CurrentURL = m.URLInput.Value()
			m.CurrentHeaders = parseHeaders(m.HeadersInput.Value())
			m.CurrentBody = m.BodyInput.Value()

			if m.CurrentURL == "" {
				return m, nil
			}
			m.IsLoading = true
			m.ResponseBody.SetContent("Loading...")
			return m, tea.Cmd(func() tea.Msg {
				return executeRequestMsg{}
			})
		}
	}

	return m, nil
}

func (m *Model) executeRequest() (tea.Model, tea.Cmd) {
	return m, func() tea.Msg {
		resp, err := m.httpClient.DoRequest(
			m.CurrentMethod,
			m.CurrentURL,
			m.CurrentHeaders,
			m.CurrentBody,
		)
		if err != nil {
			return requestFailedMsg{err: err}
		}
		return requestDoneMsg{response: resp}
	}
}

func (m *Model) handleRequestDone(msg requestDoneMsg) (tea.Model, tea.Cmd) {
	m.IsLoading = false
	m.ResponseStatus = msg.response.StatusCode
	m.ResponseTime = msg.response.Duration.Milliseconds()
	m.ResponseLength = len(msg.response.BodyBytes)

	if msg.response.Error != nil {
		m.ResponseError = msg.response.Error.Error()
		m.ResponseBody.SetContent(m.ResponseError)
		return m, m.updateHistoryListCmd()
	}

	m.ResponseBody.SetContent(msg.response.Body)

	respHeaders := make([]headerItem, 0)
	for k, v := range msg.response.Headers {
		respHeaders = append(respHeaders, headerItem{Key: k, Value: strings.Join(v, ", ")})
	}
	m.ResponseHeaders.SetItems(respHeaders)

	return m, m.updateHistoryListCmd()
}

func (m *Model) handleRequestFailed(msg requestFailedMsg) (tea.Model, tea.Cmd) {
	m.IsLoading = false
	m.ResponseError = msg.err.Error()
	m.ResponseBody.SetContent("Error: " + m.ResponseError)
	return m, nil
}

func (m *Model) updateHistoryListCmd() tea.Cmd {
	return func() tea.Msg {
		return updateHistoryMsg{}
	}
}

func (m *Model) updateHistoryList() (tea.Model, tea.Cmd) {
	if m.store == nil {
		return m, nil
	}

	history := m.store.History
	items := make([]list.Item, len(history))
	for i := range history {
		items[i] = historyItem{
			ID:       history[i].ID,
			Method:   history[i].Request.Method,
			URL:      history[i].Request.URL,
			Status:   history[i].StatusCode,
			Duration: history[i].Duration,
			Timestamp: history[i].Timestamp,
		}
	}
	m.HistoryList.SetItems(items)

	return m, nil
}

func (m *Model) selectHistoryItem(index int) *Model {
	items := m.HistoryList.Items()
	if index < 0 || index >= len(items) {
		return m
	}

	h, ok := items[index].(historyItem)
	if !ok {
		return m
	}

	for _, hist := range m.store.History {
		if hist.ID == h.ID {
			m.CurrentMethod = hist.Request.Method
			m.CurrentURL = hist.Request.URL
			m.CurrentBody = hist.Request.Body

			m.MethodInput.SetValue(hist.Request.Method)
			m.URLInput.SetValue(hist.Request.URL)
			m.BodyInput.SetValue(hist.Request.Body)

			headerLines := make([]string, 0)
			for k, v := range hist.Request.Headers {
				headerLines = append(headerLines, k+": "+v)
			}
			m.HeadersInput.SetValue(strings.Join(headerLines, "\n"))

			m.CurrentPanel = RequestPanel
			break
		}
	}

	return m
}

func parseHeaders(input string) map[string]string {
	headers := make(map[string]string)
	lines := strings.Split(input, "\n")
	for _, line := range lines {
		line = strings.TrimSpace(line)
		if line == "" {
			continue
		}
		parts := strings.SplitN(line, ":", 2)
		if len(parts) == 2 {
			hdrKey := strings.TrimSpace(parts[0])
			value := strings.TrimSpace(parts[1])
			headers[hdrKey] = value
		}
	}
	return headers
}