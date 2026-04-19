# API Testing Client TUI - Implementation Plan

## Project Overview

- **Project Name**: Aptest
- **Type**: Terminal-based API testing client (Textual TUI)
- **Core Functionality**: Interactive HTTP client for testing REST APIs with request management, history tracking, and response visualization
- **Target Users**: Developers, QA engineers, API integrators

---

## Architecture

### Technology Stack

- **Language**: Go 1.21+
- **TUI Framework**:github.com/textualize/textual (rich TUI framework, Python port available, but using Go's `textual` is actually a Go binding)
- **Note**: Using `textual` bindings directly - the main Go option is `textualize/textual` via cgo or a pure Go alternative
- **Alternative**: Use `charmbracelet/bubbletea` for TUI - more Go-native and actively maintained
- **Actual Stack Selected**:
  - TUI: `github.com/charmbracelet/bubbletea` + `github.com/charmbracelet/bubbles` (list, textinput, textarea)
  - HTTP Client: Standard library `net/http`
  - JSON: `github.com/tidwall/gjson` + `github.com/tidwall/pretty` (fast JSON parsing/formatting)
  - Storage: `github.com/boltdb/bolt` or `github.com/syndtr/goleveldb/leveldb` (embedded DB)
  - File watching/exec: `github.com/fsnotify/fsnotify` for hot-reload

### Project Structure

```
apitest/
├── cmd/
│   └── apitest/main.go           # Entry point
├── internal/
│   ├── app/
│   │   ├── model.go             # Tea model (state management)
│   │   ├── update.go            # Update logic
│   │   └── view.go              # View rendering
│   ├── http/
│   │   ├── client.go            # HTTP client wrapper
│   │   ├── request.go          # Request builder
│   │   └── response.go         # Response parser
│   ├── store/
│   │   ├── db.go                # BoltDB wrapper
│   │   ├── collection.go       # Collection CRUD
│   │   └── history.go           # History management
│   ├── ui/
│   │   ├── panels/
│   │   │   ├── request_panel.go
│   │   │   ├── response_panel.go
│   │   │   ├── history_panel.go
│   │   │   └── collections_panel.go
│   │   ├── components/
│   │   │   ├── method_selector.go
│   │   │   ├── url_input.go
│   │   │   ├── headers_editor.go
│   │   │   ├── body_editor.go
│   │   │   └── json_viewer.go
│   │   └── styles.go            # Theme/CSS
│   └── utils/
│       ├── formatter.go         # JSON formatter
│       └── validator.go         # URL/header validator
├── go.mod
├── go.sum
└── README.md
```

---

## UI Layout

### Main Layout (Split Panels)

```
┌─────────────────────────────────────────────────────────────────┐
│ Header: App Title + Current Collection + Status          [?]  │
├──────────────────────┬──────────────────────────────────────┤
│                      │                                       │
│  REQUEST PANEL       │     RESPONSE PANEL                    │
│  ┌──────────────┐   │   ┌─────────────────────────────────┐ │
│  │ Method: [▼]  │   │   │ Status: 200 OK | Time: 245ms   │ │
│  │ URL:         │   │   │ Headers Tab | Body Tab          │ │
│  │ [__________]│   │   ├─────────────────────────────────┤ │
│  │              │   │   │ {                             │ │
│  │ [Send]       │   │   │   "id": 1,                      │ │
│  └──────────────┘   │   │   "name": "test",                │ │
│                     │   │   "status": "active"            │ │
│  HEADERS TAB        │   │ }                                │ │
│  + Add Header      │   │ └─────────────────────────────────┘ │
│  ┌──────────────┐   │                                       │
│  │ Key: Value   │   │                                       │
│  └──────────────┘                                       │
│                                                             │
│  BODY TAB                                                 │
│  ┌─────────────────────────────────────────────────────┐  │
│  │ {                                                     │ │
│  │   "name": "test",                                     │ │
│  │   "items": [1, 2, 3]                                  │ │
│  │ }                                                     │ │
│  └─────────────────────────────────────────────────────┘  │
├─────────────────────────────────────────────────────────┤
│  HISTORY / COLLECTIONS PANEL (Tab Toggle)                │
│  ┌────────────────────────────────────────────────────┐ │
│  │ [GET]  /api/users        200  45ms  12:30:00         │ │
│  │ [POST] /api/users       201  120ms 12:28:00        │ │
│  │ [PUT]  /api/users/1     200  89ms 12:25:00        │ │
│  └────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
```

### Interaction Flow

1. **Request Panel**: Select method → Enter URL → Edit headers/body → Press Send
2. **Response Panel**: View status, headers, formatted body (syntax highlighted)
3. **Bottom Panel**: Toggle between History and Collections views
4. **Collections**: Create/rename/delete collections, drag requests into them

---

## Data Models

### Request

```go
type Request struct {
    ID          string            `json:"id"`
    Name        string            `json:"name"`
    Method      string            `json:"method"` // GET/POST/PUT/DELETE/PATCH
    URL         string            `json:"url"`
    Headers     map[string]string `json:"headers"`
    Body        string            `json:"body,omitempty"`
    BodyType    string            `json:"body_type"` // json, form, raw
    CreatedAt   time.Time        `json:"created_at"`
    UpdatedAt   time.Time        `json:"updated_at"`
}
```

### RequestHistory

```go
type RequestHistory struct {
    ID          string    `json:"id"`
    Request     Request   `json:"request"`
    StatusCode  int       `json:"status_code"`
    Duration    int64     `json:"duration_ms"`
    ResponseLen int       `json:"response_len"`
    Timestamp   time.Time `json:"timestamp"`
}
```

### Collection

```go
type Collection struct {
    ID          string     `json:"id"`
    Name        string     `json:"name"`
    Description string     `json:"description"`
    Requests    []Request `json:"requests"`
    CreatedAt   time.Time  `json:"created_at"`
    UpdatedAt  time.Time  `json:"updated_at"`
}
```

---

## Feature Specifications

### 1. HTTP Request Execution

- **Methods**: GET, POST, PUT, DELETE, PATCH, HEAD, OPTIONS
- **URL Input**: Full URL with protocol, supports path params
- **Timeout**: Configurable (default 30s)
- **Follow Redirects**: Configurable (default true, max 5)
- **SSL Verification**: Configurable (default true)

### 2. Headers Editor

- **UI**: Add/remove/edit header rows
- **Common Headers**: Quick-add dropdown (Content-Type, Authorization, Accept, Cache-Control)
- **Persistence**: Saved per request in collections

### 3. Body Editor

- **Editor Modes**: JSON, Form URL-Encoded, Raw Text, Binary (file upload)
- **JSON Mode**: Syntax highlighting, validation
- **Auto-format**: Ctrl+Shift+F to format JSON
- **Syntax**: JSON with collapsible nodes

### 4. Response Viewer

- **Status Display**: Code + text + color (green 2xx, yellow 3xx, red 4xx/5xx)
- **Timing**: Request duration in milliseconds
- **Size**: Response body size
- **Tabs**: Body (formatted), Headers, Raw
- **JSON Viewer**: Collapsible tree, search, copy path
- **Search**: Ctrl+F to search in response body

### 5. Request History

- **Auto-save**: Every request saved automatically
- **Display**: Method badge + URL (truncated) + status + time
- **Search**: Filter by URL, method, status code
- **Actions**: Re-send, Save to collection, Delete
- **Limit**: Last 1000 requests (configurable)

### 6. Collections

- **CRUD**: Create, rename, delete collections
- **Operations**: Add request, Remove request, Duplicate request
- **Import/Export**: JSON format for sharing
- **Reorder**: Drag-and-drop (keyboard)

### 7. Keyboard Shortcuts

| Key | Action |
|-----|--------|
| `Enter` | Send request |
| `Ctrl+S` | Save to collection |
| `Ctrl+N` | New request |
| `Ctrl+H` | Toggle history panel |
| `Ctrl+C` | Cancel request |
| `Ctrl+Q` | Quit |
| `Tab` | Next panel |
| `Ctrl+/` | Toggle help |
| `Ctrl+1` | Focus request panel |
| `Ctrl+2` | Focus response panel |
| `Ctrl+3` | Focus history panel |

---

## Implementation Phases

### Phase 1: Core Foundation (Day 1-2)

1. Set up Go module and dependencies
2. Create basic Bubble Tea app with layout
3. Implement HTTP client wrapper
4. Build request panel with method selector + URL input
5. Wire Send button to execute request

### Phase 2: Response Display (Day 2-3)

1. Build response panel with tabs
2. JSON formatting with indent/color
3. Status code with color coding
4. Response headers display
5. Timing display

### Phase 3: Headers & Body Editors (Day 3-4)

1. Headers editor panel (add/remove/edit)
2. Body editor with JSON mode
3. Validation feedback
4. Content-Type auto-detection

### Phase 4: History (Day 4-5)

1. BoltDB integration
2. Auto-save to history
3. History list panel with keyboard nav
4. Re-send from history

### Phase 5: Collections (Day 5-6)

1. Collections CRUD
2. Add request to collection
3. Load from collection
4. Export/import JSON

### Phase 6: Polish (Day 7)

1. Keyboard shortcuts
2. Help overlay
3. Theme support (dark/light)
4. Error handling
5. Documentation

---

## External Dependencies

```go
// go.mod
require (
    github.com/charmbracelet/bubbletea v0.25.0
    github.com/charmbracelet/bubbles v0.17.0
    github.com/charmbracelet/lipgloss v0.9.0
    github.com/tidwall/gjson v1.17.0
    github.com/tidwall/pretty v1.2.1
    github.com/boltdb/bolt v1.3.1
    github.com/google/uuid v1.6.0
)
```

---

## Configuration

### Default Config Location

- `~/.config/apitest/config.json`

### Config Schema

```json
{
  "timeout": 30,
  "max_redirects": 5,
  "verify_ssl": true,
  "history_limit": 1000,
  "theme": "dark",
  "keybindings": {},
  "default_headers": {}
}
```

---

## Acceptance Criteria

### Must Have

- [ ] Execute GET/POST/PUT/DELETE/PATCH requests
- [ ] View formatted JSON response with syntax highlighting
- [ ] Edit headers with add/remove functionality
- [ ] Edit body in JSON mode
- [ ] View request history with re-send capability
- [ ] Create collections and save requests to them
- [ ] Keyboard navigation between all panels
- [ ] Clean exit (no terminal corruption)

### Should Have

- [ ] Import/Export collections as JSON
- [ ] Search in history
- [ ] Response time display
- [ ] Status code color coding

### Nice to Have

- [ ] cURL command copy
- [ ] Request duplication
- [ ] Multiple tabs for requests
- [ ] WebSocket support
- [ ] gRPC support

---

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|-------------|
| JSON large response performance | High | Lazy rendering, pagination |
| Terminal size handling | Medium | Minimum size enforcement |
| Network timeout blocking | Medium | Context with cancel |
| Data corruption | High | BoltDB transactions |