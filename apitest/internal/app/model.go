package app

import (
	"net/http"
	"time"

	"github.com/charmbracelet/bubbles/list"
	"github.com/charmbracelet/bubbles/textinput"
	tea "github.com/charmbracelet/bubbletea"
	"github.com/charmbracelet/bubbles/textarea"
	"github.com/charmbracelet/bubbles/viewport"
	"github.com/charmbracelet/lipgloss"

	"github.com/apitest/apitest/internal/ui"
	"github.com/apitest/apitest/internal/http"
)

type Panel int

const (
	RequestPanel Panel = iota
	ResponsePanel
	HistoryPanel
	CollectionsPanel
)

type Tab int

const (
	HeadersTab Tab = iota
	BodyTab
)

type ResponseTab int

const (
	ResponseBodyTab ResponseTab = iota
	ResponseHeadersTab
)

type historyItemDelegate struct{}

func (d historyItemDelegate) Height() int                             { return 1 }
func (d historyItemDelegate) Spacing() int                            { return 0 }
func (d historyItemDelegate) Update(msg tea.Msg, m *list.Model) tea.Cmd {
	return nil
}

func (d historyItemDelegate) Render(m list.Model, index int, sb *list.ItemBuilder) {
	h, ok := m.Items()[index].(historyItem)
	if !ok {
		return
	}
	methodStyle := ui.GetMethodStyle(h.Method)
	statusStyle := ui.GetStatusStyle(h.Status)
	urlDisplay := h.URL
	if len(urlDisplay) > 40 {
		urlDisplay = urlDisplay[:40]
	}
	statusStr := statusStyle.Render(h.Status)
	durationStr := formatDuration(h.Duration)
	sb.WriteString(methodStyle.Render(h.Method) + " " + urlDisplay + " " + statusStr + " " + ui.Subtle.Render(durationStr))
}

type collectionItemDelegate struct{}

func (d collectionItemDelegate) Height() int                             { return 1 }
func (d collectionItemDelegate) Spacing() int                            { return 0 }
func (d collectionItemDelegate) Update(msg tea.Msg, m *list.Model) tea.Cmd {
	return nil
}

func (d collectionItemDelegate) Render(m list.Model, index int, sb *list.ItemBuilder) {
	c, ok := m.Items()[index].(collectionItem)
	if !ok {
		return
	}
	count := len(c.Requests)
	sb.WriteString(ui.PanelTitleStyle.Render(c.Name) + " (" + itoa(count) + " requests)")
}

type headerItemDelegate struct{}

func (d headerItemDelegate) Height() int                             { return 1 }
func (d headerItemDelegate) Spacing() int                            { return 0 }
func (d headerItemDelegate) Update(msg tea.Msg, m *list.Model) tea.Cmd {
	return nil
}

func (d headerItemDelegate) Render(m list.Model, index int, sb *list.ItemBuilder) {
	h, ok := m.Items()[index].(headerItem)
	if !ok {
		return
	}
	sb.WriteString(ui.Bold.Render(h.Key) + ": " + h.Value)
}

type historyItem struct {
	ID        string
	Method    string
	URL       string
	Status    int
	Duration  int64
	Timestamp time.Time
}

type collectionItem struct {
	ID        string
	Name      string
	Requests  []Request
}

type headerItem struct {
	Key   string
	Value string
}

type Model struct {
	CurrentPanel  Panel
	RequestTab    Tab
	ResponseTab   ResponseTab

	MethodInput   textinput.Model
	URLInput      textinput.Model
	HeadersInput  textarea.Model
	BodyInput     textarea.Model

	ResponseBody      viewport.Model
	ResponseHeaders   list.Model
	ResponseStatus    int
	ResponseTime      int64
	ResponseLength    int
	ResponseError     string
	IsLoading         bool

	HistoryList     list.Model
	CollectionsList list.Model

	CurrentMethod   string
	CurrentURL      string
	CurrentHeaders map[string]string
	CurrentBody     string

	History     []RequestHistory
	Collections []Collection

	ShowHelp bool
	Quitting bool

	httpClient *HTTPClient
	store      *Store
}

func NewModel() Model {
	methodInput := textinput.New()
	methodInput.Placeholder = "GET"
	methodInput.Focus()
	methodInput.Width = 10

	urlInput := textinput.New()
	urlInput.Placeholder = "https://api.example.com/endpoint"
	urlInput.Width = 50

	headersInput := textarea.New()
	headersInput.Placeholder = "Content-Type: application/json\nAuthorization: Bearer token"
	headersInput.SetHeight(5)
	headersInput.ShowLineNumbers = false

	bodyInput := textarea.New()
	bodyInput.Placeholder = `{"key": "value"}`
	bodyInput.SetHeight(8)
	bodyInput.ShowLineNumbers = false

	responseBody := viewport.New(60, 15)

	historyList := list.New(nil, historyItemDelegate{}, 0, 0)
	historyList.Title = "History"
	historyList.SetShowHelp(false)

	collectionsList := list.New(nil, collectionItemDelegate{}, 0, 0)
	collectionsList.Title = "Collections"
	collectionsList.SetShowHelp(false)

	responseHeadersList := list.New(nil, headerItemDelegate{}, 0, 0)
	responseHeadersList.SetShowHelp(false)

	return Model{
		CurrentPanel:    RequestPanel,
		RequestTab:      HeadersTab,
		ResponseTab:     ResponseBodyTab,

		MethodInput:      methodInput,
		URLInput:         urlInput,
		HeadersInput:     headersInput,
		BodyInput:        bodyInput,

		ResponseBody:     responseBody,
		ResponseHeaders:  responseHeadersList,

		CurrentMethod:  "GET",
		CurrentURL:     "",
		CurrentHeaders: make(map[string]string),
		CurrentBody:    "",

		History:     []RequestHistory{},
		Collections: []Collection{},

		ShowHelp: false,
		Quitting:  false,

		httpClient: NewHTTPClient(),
		store:      nil,
	}
}

func (m *Model) Init() tea.Cmd {
	return nil
}

// itoa converts an integer to a string
func itoa(n int) string {
	if n == 0 {
		return "0"
	}
	var digits []byte
	for n > 0 {
		digits = append(digits, byte('0'+n%10))
		n /= 10
	}
	// reverse
	for i, j := 0, len(digits)-1; i < j; i, j = i+1, j-1 {
		digits[i], digits[j] = digits[j], digits[i]
	}
	return string(digits)
}

// formatDuration formats a duration in milliseconds to a human-readable string
func formatDuration(ms int64) string {
	if ms < 1000 {
		return itoa(int(ms)) + "ms"
	}
	seconds := ms / 1000
	if seconds < 60 {
		return itoa(int(seconds)) + "s"
	}
	minutes := seconds / 60
	secs := seconds % 60
	return itoa(int(minutes)) + "m" + itoa(int(secs)) + "s"
}

type (
	ExecuteRequestMsg   struct{}
	RequestResultMsg    struct{ StatusCode int; Body string; Headers http.Header; Duration time.Duration; Error error }
	SwitchPanelMsg      struct{}
	SwitchRequestTabMsg struct{}
	SwitchResponseTabMsg struct{}
	ToggleHelpMsg       struct{}
)

func renderRequestPanel(m Model) string {
	panelBorder := ui.BoxStyle
	if m.CurrentPanel == RequestPanel {
		panelBorder = ui.SelectedBoxStyle
	}

	methodButtons := ""
	for _, method := range []string{"GET", "POST", "PUT", "DELETE", "PATCH"} {
		style := ui.GetMethodStyle(method)
		if method == m.CurrentMethod {
			methodButtons += style.Render("[" + method + "]") + " "
		} else {
			methodButtons += ui.Subtle.Render(method) + " "
		}
	}

	tabs := ""
	if m.RequestTab == HeadersTab {
		tabs = ui.TabActiveStyle.Render("[Headers]") + " " + ui.TabStyle.Render("[Body]")
	} else {
		tabs = ui.TabStyle.Render("[Headers]") + " " + ui.TabActiveStyle.Render("[Body]")
	}

	content := methodButtons + "\n" + m.URLInput.View() + "\n" + tabs + "\n"
	if m.RequestTab == HeadersTab {
		content += m.HeadersInput.View()
	} else {
		content += m.BodyInput.View()
	}
	content += "\n[SEND]"

	return panelBorder.Render(content)
}

func renderResponsePanel(m Model) string {
	panelBorder := ui.BoxStyle
	if m.CurrentPanel == ResponsePanel {
		panelBorder = ui.SelectedBoxStyle
	}

	content := ""
	if m.IsLoading {
		content = "Loading..."
	} else if m.ResponseError != "" {
		content = ui.StatusErrorStyle.Render("Error: ") + m.ResponseError
	} else if m.ResponseStatus > 0 {
		statusStyle := ui.GetStatusStyle(m.ResponseStatus)
		statusText := statusStyle.Render(itoa(m.ResponseStatus))
		timeText := formatDuration(m.ResponseTime)
		sizeText := itoa(m.ResponseLength) + " bytes"
		content = statusText + " | " + timeText + " | " + sizeText + "\n"
		content += m.ResponseBody.View()
	} else {
		content = "Send a request to see the response"
	}

	return panelBorder.Width(60).Render(content)
}

func renderBottomPanel(m Model) string {
	panelBorder := ui.BoxStyle
	if m.CurrentPanel == HistoryPanel || m.CurrentPanel == CollectionsPanel {
		panelBorder = ui.SelectedBoxStyle
	}

	tabs := ui.TabActiveStyle.Render("[History]") + " " + ui.TabStyle.Render("[Collections]")

	items := make([]list.Item, 0, len(m.History))
	for _, h := range m.History {
		items = append(items, h)
	}
	m.HistoryList.SetItems(items)

	content := tabs + "\n" + m.HistoryList.View()
	return panelBorder.Height(10).Render(content)
}

func renderHelp() string {
	content := `Keyboard Shortcuts:
┌─────────────────────────────────────────┐
│ Enter / Ctrl+R  │ Send request          │
│ Tab             │ Switch panels         │
│ Ctrl+H          │ Focus history         │
│ Ctrl+B          │ Toggle headers/body   │
│ ?               │ Toggle this help      │
│ Ctrl+Q          │ Quit                  │
└─────────────────────────────────────────┘
`
	return ui.BoxStyle.Render(content)
}