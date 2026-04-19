# apitest

A Go TUI API client built with Bubble Tea.

## Features

- Send HTTP requests (GET, POST, PUT, DELETE, PATCH)
- Custom headers and body support
- Response viewer with formatted JSON
- Request history persistence
- Collections for organizing requests

## Dependencies

- [bubbletea](https://github.com/charmbracelet/bubbletea) - TUI framework
- [bubbles](https://github.com/charmbracelet/bubbles) - UI components
- [lipgloss](https://github.com/charmbracelet/lipgloss) - Styling
- [boltdb](https://github.com/boltdb/bolt) - Local storage

## Building

```bash
go build -o apitest .
```

## Running

```bash
./apitest
```

Or run directly:

```bash
go run .
```

## Keyboard Shortcuts

| Key | Action |
|-----|--------|
| `Enter` | Send request |
| `Ctrl+R` | Send request |
| `Tab` | Switch panels |
| `Ctrl+H` | View history |
| `Ctrl+B` | Toggle headers/body |
| `Ctrl+C` | Quit |

## Project Structure

```
.
├── main.go                 # Entry point
├── cmd/apitest/main.go    # Alternative entry
├── internal/
│   ├── app/
│   │   ├── model.go       # Model definition
│   │   ├── update.go    # Update logic (tea.Update)
│   │   ├── view.go     # View rendering (tea.View)
│   │   ├── store.go    # Persistence
│   │   ├── http_client.go
│   │   └── model_types.go
│   ├── http/
│   │   └── client.go    # HTTP client
│   └── ui/
│       └── styles.go    # UI styles
└── go.mod
```

## Usage

1. Enter the HTTP method (GET, POST, PUT, DELETE, PATCH)
2. Enter the URL
3. Add headers (optional) - one per line: `Key: Value`
4. Add body (optional) for POST/PUT/PATCH
5. Press Enter or Ctrl+R to send

The response will display in the right panel with status, time, and formatted JSON.