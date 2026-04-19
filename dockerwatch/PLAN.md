# DockerWatch - Implementation Plan

## Overview

**Project**: DockerWatch - Real-time Docker container monitoring dashboard with TUI interface
**Language**: Go (for native Docker SDK integration and Bubble Tea ecosystem)
**Target Users**: DevOps engineers, system administrators, developers managing containerized applications

---

## 1. Architecture Overview

### 1.1 High-Level Design

```
┌─────────────────────────────────────────────────────────────────┐
│                        DockerWatch TUI                           │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐ │
│  │  Dashboard  │  │   Logs      │  │  Container Details      │ │
│  │   View     │  │   View      │  │     View                 │ │
│  └──────┬──────┘  └──────┬──────┘  └───────────┬─────────────┘ │
│         │                 │                      │               │
│  ┌──────▼────────────────▼──────────────────────▼─────────────┐ │
│  │                     State Manager                          │ │
│  └──────────────────────────┬────────────────────────────────┘ │
│                             │                                    │
│  ┌──────────────────────────▼────────────────────────────────┐  │
│  │              Docker API Integration Layer                  │  │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  │  │
│  │  │ Container│  │  Stats   │  │  Logs    │  │Lifecycle │  │  │
│  │  │  List    │  │ Streaming│  │ Streaming│  │  Manager │  │  │
│  │  └──────────┘  └──────────┘  └──────────┘  └──────────┘  │  │
│  └──────────────────────────┬────────────────────────────────┘  │
│                             │                                    │
│                      Docker Engine API                            │
│                   (via Docker SDK for Go)                        │
└─────────────────────────────────────────────────────────────────┘
```

### 1.2 Technology Stack

| Component | Technology | Version | Rationale |
|-----------|------------|--------|-----------|
| Language | Go | 1.21+ | Native Docker SDK, excellent concurrency |
| TUI Framework | Bubble Tea | v2.x | Elm architecture, production-ready |
| TUI Components | Bubbles | latest | Table, viewport, spinners |
| Styling | Lip Gloss | latest | Declarative terminal styling |
| Docker SDK | docker/docker | v27+ | Official Go SDK |
| Configuration | Viper | v1.x | YAML/TOML support |
| Logging | log/slog | stdlib | Structured logging |

---

## 2. File Structure

```
dockerwatch/
├── cmd/
│   └── dockerwatch/
│       └── main.go                 # Application entry point
│
├── internal/
│   ├── config/
│   │   ├── config.go               # Configuration loader
│   │   └── defaults.go             # Default settings
│   │
│   ├── docker/
│   │   ├── client.go               # Docker client wrapper
│   │   ├── container.go             # Container operations
│   │   ├── stats.go                # Stats streaming
│   │   ├── logs.go                 # Logs streaming
│   │   └── errors.go               # Docker-specific errors
│   │
│   ├── models/
│   │   ├── container.go            # Container data model
│   │   ├── stats.go                # Stats data model
│   │   ├── log.go                  # Log entry model
│   │   └── health.go               # Health check model
│   │
│   ├── tui/
│   │   ├── app.go                  # Main Bubble Tea application
│   │   ├── model.go                # Root model
│   │   ├── styles.go               # Lip Gloss styles
│   │   │
│   │   ├── views/
│   │   │   ├── dashboard.go        # Dashboard view (container list)
│   │   │   ├── details.go          # Container details view
│   │   │   ├── logs.go             # Logs viewer view
│   │   │   ├── charts.go           # Stats charts view
│   │   │   └── help.go             # Help/commands view
│   │   │
│   │   └── components/
│   │       ├── table.go            # Container table component
│   │       ├── statbar.go          # Stats bar component
│   │       ├── spinner.go          # Loading spinner component
│   │       └── progress.go          # Progress indicators
│   │
│   └── utils/
│       ├── format.go               # Formatting utilities
│       ├── filter.go               # Container filtering/sorting
│       └── errors.go               # General error utilities
│
├── config.yaml                     # Default configuration
├── go.mod                          # Go module file
├── go.sum                          # Dependencies checksum
├── Makefile                        # Build automation
└── README.md                       # Documentation
```

---

## 3. Data Models

### 3.1 Container Model

```go
// internal/models/container.go
type Container struct {
    ID          string            // Full container ID
    ShortID     string            // First 12 characters
    Name        string            // Container name (without leading /)
    Image       string            // Image name
    Status      ContainerStatus   // running, stopped, paused, etc.
    State       string            // Human-readable state
    Created     time.Time         // Creation timestamp
    Ports       []PortBinding     // Port mappings
    Labels      map[string]string // Container labels
    Health      HealthStatus      // Health check status
}

type ContainerStatus string

const (
    StatusRunning ContainerStatus = "running"
    StatusStopped ContainerStatus = "stopped"
    StatusPaused  ContainerStatus = "paused"
    StatusCreated ContainerStatus = "created"
    StatusRestarting ContainerStatus = "restarting"
    StatusExited  ContainerStatus = "exited"
    StatusDead    ContainerStatus = "dead"
)

type PortBinding struct {
    HostIP       string
    HostPort     string
    ContainerPort string
    Protocol     string
}

type HealthStatus string

const (
    HealthHealthy   HealthStatus = "healthy"
    HealthUnhealthy HealthStatus = "unhealthy"
    HealthStarting  HealthStatus = "starting"
    HealthNone      HealthStatus = "" // No health check defined
)
```

### 3.2 Stats Model

```go
// internal/models/stats.go
type Stats struct {
    ContainerID  string
    Timestamp    time.Time
    CPU          CPUStats
    Memory       MemoryStats
    Network      NetworkStats
    Disk         DiskStats
    PIDs         int
}

type CPUStats struct {
    Percentage   float64          // Calculated CPU %
    Usage        uint64           // Total CPU usage (nanoseconds)
    SystemUsage  uint64           // System CPU usage
    OnlineCPUs   int              // Number of online CPUs
    PerCoreUsage []float64        // Per-core percentages
}

type MemoryStats struct {
    Usage        uint64           // Current memory usage (bytes)
    Limit        uint64           // Memory limit (bytes)
    Percentage   float64          // Usage percentage
    SwapUsage    uint64           // Swap usage (bytes)
    SwapLimit    uint64           // Swap limit (bytes)
}

type NetworkStats struct {
    RxBytes      uint64           // Bytes received
    TxBytes      uint64           // Bytes transmitted
    RxPackets    uint64           // Packets received
    TxPackets    uint64           // Packets transmitted
    RxErrors     uint64           // Receive errors
    TxErrors     uint64           // Transmit errors
    // For multi-interface support
    Interfaces   []InterfaceStats
}

type InterfaceStats struct {
    Name         string
    RxBytes      uint64
    TxBytes      uint64
}

type DiskStats struct {
    ReadBytes    uint64           // Bytes read
    WriteBytes   uint64           // Bytes written
    IoServiceBytesRecursive []IOCounter
}

type IOCounter struct {
    Major, Minor uint64
    Op          string
    Value       uint64
}
```

### 3.3 Log Model

```go
// internal/models/log.go
type LogEntry struct {
    Timestamp    time.Time
    ContainerID  string
    Message      string
    Stream       LogStream         // stdout or stderr
    IsPartial    bool              // Multi-line message chunk
}

type LogStream string

const (
    StreamStdout LogStream = "stdout"
    StreamStderr LogStream = "stderr"
)

type LogOptions struct {
    Follow       bool              // Stream logs
    Tail         int               // Number of lines to fetch
    Since        time.Time         // Logs since timestamp
    Timestamps   bool              // Include timestamps
    Details      bool              // Include extra details
}
```

---

## 4. API Design

### 4.1 Docker Client Interface

```go
// internal/docker/client.go
type Client interface {
    // Connection
    Ping(ctx context.Context) error
    Info(ctx context.Context) (*types.Info, error)

    // Container Operations
    ListContainers(ctx context.Context, opts ListOptions) ([]Container, error)
    GetContainer(ctx context.Context, id string) (*Container, error)
    InspectContainer(ctx context.Context, id string) (*types.ContainerJSON, error)

    // Lifecycle Management
    StartContainer(ctx context.Context, id string) error
    StopContainer(ctx context.Context, id string, timeout time.Duration) error
    RestartContainer(ctx context.Context, id string, timeout time.Duration) error
    RemoveContainer(ctx context.Context, id string, opts RemoveOptions) error
    PauseContainer(ctx context.Context, id string) error
    UnpauseContainer(ctx context.Context, id string) error

    // Stats Streaming
    StreamStats(ctx context.Context, id string) (<-chan *Stats, error)
    StreamAllStats(ctx context.Context) (<-chan map[string]*Stats, error)

    // Logs Streaming
    StreamLogs(ctx context.Context, id string, opts LogOptions) (<-chan *LogEntry, error)

    // Health
    GetHealthStatus(ctx context.Context, id string) (HealthStatus, error)

    // Events
    StreamEvents(ctx context.Context) (<-chan *DockerEvent, error)
}

type ListOptions struct {
    All     bool                  // Include stopped containers
    Filters filters.Args
}

type RemoveOptions struct {
    Force   bool                  // Force removal
    Volume  bool                  // Remove volumes
}

type DockerEvent struct {
    Type      string              // container, image, volume, etc.
    Action    string              // start, stop, die, etc.
    Actor     Actor
    Time      time.Time
}
```

### 4.2 Docker Client Implementation

```go
// internal/docker/client.go
type dockerClient struct {
    client    *docker.Client
    baseURL   string
    version   string
}

// NewDockerClient creates a new Docker client
// Supports: local socket, TCP, SSH
func NewDockerClient(opts ...Option) (*dockerClient, error) {
    client, err := client.NewClientWithOpts(
        client.FromEnv,
        client.WithAPIVersionNegotiation(),
    )
    if err != nil {
        return nil, fmt.Errorf("failed to create Docker client: %w", err)
    }

    dc := &dockerClient{
        client:  client,
        baseURL: os.Getenv("DOCKER_HOST"),
        version: client.ClientVersion(),
    }

    for _, opt := range opts {
        opt(dc)
    }

    return dc, nil
}
```

---

## 5. TUI Application Design

### 5.1 Application State Model

```go
// internal/tui/model.go
type Model struct {
    // Views
    currentView  View
    selectedContainer string
    cursor       int

    // Data
    containers   []Container
    stats        map[string]*Stats
    statsHistory map[string][]Stats  // Historical data for charts
    logs         map[string][]LogEntry
    events       []DockerEvent

    // Docker client
    docker       docker.Client

    // UI State
    width        int
    height       int
    isLoading    bool
    loadingMsg   string
    filter       Filter
    sortField    SortField
    sortDesc     bool

    // Error handling
    err          error
    notifications []Notification

    // View state
    logsViewport viewport.Model
    chartWindow  int              // Time window for charts (seconds)
}

type View int

const (
    ViewDashboard View = iota
    ViewDetails
    ViewLogs
    ViewCharts
    ViewHelp
)

type Filter struct {
    Status      []ContainerStatus
    Search      string
    Labels      map[string]string
}

type SortField string

const (
    SortByName    SortField = "name"
    SortByStatus  SortField = "status"
    SortByCPU     SortField = "cpu"
    SortByMemory  SortField = "memory"
    SortByNetwork SortField = "network"
)
```

### 5.2 Update Loop

```go
// internal/tui/app.go
func (m Model) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
    switch msg := msg.(type) {

    // Window resize
    case tea.WindowSizeMsg:
        m.width = msg.Width
        m.height = msg.Height
        return m, nil

    // Keyboard input
    case tea.KeyMsg:
        return m.handleKeyPress(msg)

    // Stats update from background
    case StatsMsg:
        m.stats = msg.Stats
        return m, nil

    // Container list update
    case ContainersMsg:
        m.containers = msg.Containers
        return m, nil

    // Log entry from stream
    case LogMsg:
        m.logs[msg.ContainerID] = append(m.logs[msg.ContainerID], msg.Entry)
        // Keep only last N entries
        if len(m.logs[msg.ContainerID]) > maxLogEntries {
            m.logs[msg.ContainerID] = m.logs[msg.ContainerID][-maxLogEntries:]
        }
        return m, nil

    // Docker event
    case EventMsg:
        m.events = append(m.events, msg.Event)
        return m.handleDockerEvent(msg.Event)

    // Error
    case ErrMsg:
        m.err = msg.Err
        m.addNotification(Notification{
            Type:    TypeError,
            Message: msg.Err.Error(),
        })
        return m, nil

    // Loading state
    case LoadingMsg:
        m.isLoading = msg.IsLoading
        m.loadingMsg = msg.Message
        return m, nil
    }

    return m, nil
}
```

### 5.3 Message Types

```go
// internal/tui/messages.go
type (
    // Data messages
    StatsMsg struct {
        ContainerID string
        Stats       *Stats
    }
    ContainersMsg struct {
        Containers []Container
    }
    LogMsg struct {
        ContainerID string
        Entry       *LogEntry
    }
    EventMsg struct {
        Event *DockerEvent
    }

    // Control messages
    ErrMsg struct {
        Err error
    }
    LoadingMsg struct {
        IsLoading bool
        Message   string
    }
    Notification struct {
        Type    NotificationType
        Message string
        Time    time.Time
    }
    NotificationType int
)

const (
    TypeInfo NotificationType = iota
    TypeSuccess
    TypeWarning
    TypeError
)

// Commands
func RefreshContainers() tea.Cmd
func StreamStats(containerID string) tea.Cmd
func StreamAllStats() tea.Cmd
func StreamLogs(containerID string) tea.Cmd
func StartContainer(id string) tea.Cmd
func StopContainer(id string) tea.Cmd
func RestartContainer(id string) tea.Cmd
func RemoveContainer(id string) tea.Cmd
```

---

## 6. View Specifications

### 6.1 Dashboard View (Default)

```
┌────────────────────────────────────────────────────────────────────────┐
│  DockerWatch                                          [Help: ?] [Quit: q]│
├────────────────────────────────────────────────────────────────────────┤
│                                                                        │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │ CONTAINER      │ STATUS  │ CPU% │ MEM%    │ NETWORK I/O │ UPTIME│   │
│  ├────────────────┼─────────┼──────┼─────────┼─────────────┼──────┤   │
│  │ ▶ web-app     │ running │ 12.3 │ 256MiB  │ 1.2MB/3.4MB │ 2d5h  │   │
│  │   db-postgres │ running │  4.1 │ 512MiB  │ 2.1MB/8.2MB │ 5d3h  │   │
│  │   cache-redis │ running │  1.2 │  64MiB  │ 512KB/1MB   │ 1d2h  │   │
│  │   api-server  │ running │ 23.5 │ 128MiB  │ 5.6MB/2.1MB │ 6d1h  │   │
│  │ ○ nginx-proxy │ stopped │    - │      -  │         -   │    -  │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                        │
│  [▶ Start] [■ Stop] [↻ Restart] [Logs] [✕ Remove]    [Refresh: r]     │
│                                                                        │
│  CPU Usage:  [████████████████████░░░░░░░░░░░░] 41.1%                 │
│  Memory:     [██████████████████████████████░░░] 85.2%                 │
│                                                                        │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │ Events: container:start (web-app, 2s ago)                        │   │
│  │         container:stop (nginx-proxy, 15m ago)                    │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                        │
│  [Tab: Switch View] [↑↓: Navigate] [Enter: Details]                     │
└────────────────────────────────────────────────────────────────────────┘
```

### 6.2 Container Details View

```
┌────────────────────────────────────────────────────────────────────────┐
│  ← Back to Dashboard                              Container: web-app   │
├────────────────────────────────────────────────────────────────────────┤
│                                                                        │
│  ┌─ Container Info ──────────────────────────────────────────────────┐  │
│  │  ID:        a1b2c3d4e5f6                                         │  │
│  │  Name:      web-app                                              │  │
│  │  Image:     nginx:1.25-alpine                                     │  │
│  │  Status:    running (healthy)                                     │  │
│  │  Created:   2024-01-15 10:30:00                                   │  │
│  │  Ports:     80/tcp → 0.0.0.0:8080, 443/tcp → 0.0.0.0:8443         │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│                                                                        │
│  ┌─ Resource Usage ───────────────────────────┬─ Network I/O ─────────┐  │
│  │  CPU:      12.3%  (4 cores)              │  RX: 1.2MB            │  │
│  │  Memory:   256MiB / 512MiB (50.0%)       │  TX: 3.4MB            │  │
│  │  Swap:     0B / 256MiB                   │  Packets: 1.2K/3.4K   │  │
│  │  PIDs:     12                             │  Errors: 0/0          │  │
│  │  CPU Chart (last 60s):                   └───────────────────────┘  │
│  │  ▂▃▅▇█▇▅▃▂▃▅▇█▇▅▃▂▃▅▇█▇▅▃▂▃▅▇█▇▅▃▂▃▅▇█▇▅▃▂▃▅▇█▇▅▃▂▃▅▇█▇           │
│  └───────────────────────────────────────────────────────────────────┘  │
│                                                                        │
│  ┌─ Health Checks ──────────────────────────────────────────────────┐  │
│  │  Status:    ✓ Healthy                                            │  │
│  │  Failures:  0                                                    │  │
│  │  Last Check: 30s ago                                             │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│                                                                        │
│  [▶ Start] [■ Stop] [↻ Restart] [↻↻ Inspect] [✕ Remove] [Logs]        │
│                                                                        │
└────────────────────────────────────────────────────────────────────────┘
```

### 6.3 Logs View

```
┌────────────────────────────────────────────────────────────────────────┐
│  ← Back                                         Logs: web-app          │
├────────────────────────────────────────────────────────────────────────┤
│                                                                        │
│  Filters: [All ▼] [Search: ________________________] [Timestamps ☑]    │
│                                                                        │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │ 2024-01-15 12:30:01 [nginx] Starting nginx...                   │   │
│  │ 2024-01-15 12:30:02 [nginx] Configuration complete              │   │
│  │ 2024-01-15 12:30:02 [nginx] 127.0.0.1 - - [15/Jan/2024:12:30:02] │   │
│  │ 2024-01-15 12:30:02 [nginx] "GET /health HTTP/1.1" 200 62        │   │
│  │ 2024-01-15 12:30:05 [nginx] 192.168.1.100 - - [15/Jan/2024:...]  │   │
│  │ 2024-01-15 12:30:05 [nginx] "GET /api/users HTTP/1.1" 200 1523   │   │
│  │ 2024-01-15 12:30:10 [ERROR] Database connection timeout         │   │
│  │ 2024-01-15 12:30:10 [WARN] Retrying connection (attempt 1/3)    │   │
│  │ 2024-01-15 12:30:11 [INFO] Connection restored                   │   │
│  │ 2024-01-15 12:30:15 [nginx] 192.168.1.101 - - [15/Jan/2024:...] │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                        │
│  [↓ Scroll] [↑ Scroll] [f: Follow] [Ctrl+C: Stop Follow]              │
│  [c: Clear] [s: Save to file]                                          │
│                                                                        │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 7. Error Handling

### 7.1 Error Types

```go
// internal/docker/errors.go
type ErrorType int

const (
    ErrorTypeConnection ErrorType = iota
    ErrorTypeAPI
    ErrorTypeTimeout
    ErrorTypeNotFound
    ErrorTypePermission
    ErrorTypeConflict
    ErrorTypeUnknown
)

type DockerError struct {
    Type    ErrorType
    Message string
    Cause   error
    Context string
}

func (e *DockerError) Error() string {
    if e.Context != "" {
        return fmt.Sprintf("[%s] %s: %s", e.Context, e.Message, e.Cause)
    }
    return fmt.Sprintf("%s: %s", e.Message, e.Cause)
}

// Error wrapping helpers
func NewConnectionError(ctx string, err error) *DockerError {
    return &DockerError{
        Type:    ErrorTypeConnection,
        Message: "Docker connection failed",
        Cause:   err,
        Context: ctx,
    }
}

func NewAPIError(ctx string, err error) *DockerError {
    // Parse Docker API error codes
    var apiErr *dockerapi.Error
    if errors.As(err, &apiErr) {
        return &DockerError{
            Type:    mapErrorType(apiErr.StatusCode),
            Message: apiErr.Message,
            Cause:   err,
            Context: ctx,
        }
    }
    return &DockerError{
        Type:    ErrorTypeAPI,
        Message: "Docker API error",
        Cause:   err,
        Context: ctx,
    }
}

func mapErrorType(statusCode int) ErrorType {
    switch statusCode {
    case 404:
        return ErrorTypeNotFound
    case 409:
        return ErrorTypeConflict
    case 403:
        return ErrorTypePermission
    default:
        return ErrorTypeAPI
    }
}
```

### 7.2 Recovery Strategies

```go
// Retry logic with exponential backoff
func WithRetry(ctx context.Context, maxAttempts int, fn func() error) error {
    var lastErr error
    for attempt := 0; attempt < maxAttempts; attempt++ {
        if err := fn(); err != nil {
            lastErr = err
            if attempt < maxAttempts-1 {
                backoff := time.Duration(math.Pow(2, float64(attempt))) * time.Second
                select {
                case <-ctx.Done():
                    return ctx.Err()
                case <-time.After(backoff):
                    continue
                }
            }
        }
        return nil
    }
    return fmt.Errorf("after %d attempts: %w", maxAttempts, lastErr)
}

// Connection resilience
type ResilientClient struct {
    client    *docker.Client
    onConnect func() error
    onDisconnect func(error)
}

func (r *ResilientClient) ExecuteWithReconnect(ctx context.Context, fn func() error) error {
    err := fn()
    if err != nil {
        var connErr *dockerapi.Error
        if errors.As(err, &connErr) && connErr.StatusCode == 500 &&
           strings.Contains(connErr.Message, "client is disconnecting") {
            if reconnectErr := r.reconnect(); reconnectErr != nil {
                return fmt.Errorf("reconnect failed: %w", reconnectErr)
            }
            return fn()
        }
    }
    return err
}
```

### 7.3 User-Facing Error Display

```go
// Display errors in TUI with appropriate formatting
func FormatError(err error) string {
    var dockerErr *DockerError
    if errors.As(err, &dockerErr) {
        icon := "❌"
        switch dockerErr.Type {
        case ErrorTypeConnection:
            icon = "🔌"
        case ErrorTypeTimeout:
            icon = "⏱"
        case ErrorTypeNotFound:
            icon = "🔍"
        case ErrorTypePermission:
            icon = "🔒"
        case ErrorTypeConflict:
            icon = "⚠️"
        }
        return fmt.Sprintf("%s %s", icon, dockerErr.Error())
    }
    return fmt.Sprintf("❌ %s", err.Error())
}
```

---

## 8. Edge Cases & Handling

### 8.1 Connection Issues

| Scenario | Detection | Handling |
|----------|----------|----------|
| Docker not running | Ping fails | Show "Docker not running" message, retry option |
| Socket permission denied | EACCES error | Suggest `sudo` or adding user to docker group |
| Connection timeout | Context deadline exceeded | Retry with backoff, show progress |
| Connection lost mid-stream | Read error on stream | Auto-reconnect with indicator, resume data |
| API version mismatch | API version negotiation fails | Log warning, attempt fallback |

### 8.2 Data Edge Cases

| Scenario | Handling |
|----------|----------|
| No containers exist | Show empty state with helpful message |
| Container deleted while viewing | Graceful removal from list, notification |
| Stats unavailable (container stopped) | Show "N/A", disable stats view |
| Very long container names | Truncate with ellipsis, tooltip for full name |
| Very high CPU (>900%) | Cap display at reasonable max, note multi-core |
| Memory limit not set | Show "unlimited" instead of percentage |
| Network stats unavailable | Show "N/A", log warning |
| Container with no logs | Show "No logs available" message |
| Log buffer overflow | Keep last N entries, show notification |

### 8.3 UI Edge Cases

| Scenario | Handling |
|----------|----------|
| Terminal too small | Minimum size check, resize prompt |
| Rapid key presses | Debounce input handling |
| High-frequency updates | Throttle renders, batch updates |
| Unicode in container names/logs | Proper encoding handling |
| Very long log lines | Line wrapping, horizontal scroll option |
| Color terminal vs monochrome | Detect and adapt styling |

### 8.4 Race Conditions

| Scenario | Prevention |
|----------|------------|
| Container state changes during operation | Use container ID, not name |
| Stats stream vs container stop | Check container exists before processing |
| Multiple concurrent operations on same container | Operation queue or mutex per container |
| Model update during view render | Immutable updates, channel-based communication |

---

## 9. Configuration

### 9.1 Configuration File

```yaml
# config.yaml
app:
  name: "DockerWatch"
  refresh_interval: 2s        # Stats refresh interval
  log_buffer_size: 1000       # Max log entries per container
  max_history_points: 60    # Data points for charts

docker:
  host: ""                   # Docker socket (default: /var/run/docker.sock)
  # host: "tcp://localhost:2375"  # Alternative
  api_version: ""            # Auto-detect
  timeout: 10s               # API timeout
  max_retries: 3             # Retry attempts

ui:
  theme: "dark"              # dark, light, auto
  color_scheme: "default"   # default, monokai, dracula, nord
  show_stopped: true        # Include stopped containers
  show_system: false         # Include system containers
  compact_mode: false        # Compact table layout

columns:
  visible: ["name", "status", "cpu", "memory", "network", "uptime"]
  order: ["name", "status", "cpu", "memory", "network", "uptime"]

shortcuts:
  quit: "q"
  help: "?"
  refresh: "r"
  start: "s"
  stop: "x"
  restart: "R"
  logs: "l"
  details: "Enter"
```

### 9.2 Configuration Loader

```go
// internal/config/config.go
type Config struct {
    App      AppConfig
    Docker   DockerConfig
    UI       UIConfig
    Columns  ColumnsConfig
    Shortcuts ShortcutsConfig
}

func Load(path string) (*Config, error) {
    v := viper.New()
    v.SetConfigFile(path)
    v.SetConfigType("yaml")

    // Set defaults
    setDefaults(v)

    if err := v.ReadInConfig(); err != nil {
        if errors.Is(err, fs.ErrNotExist) {
            // Use defaults if no config file
            return defaultConfig(), nil
        }
        return nil, fmt.Errorf("failed to read config: %w", err)
    }

    var cfg Config
    if err := v.Unmarshal(&cfg); err != nil {
        return nil, fmt.Errorf("failed to unmarshal config: %w", err)
    }

    return &cfg, nil
}
```

---

## 10. Keyboard Shortcuts

### 10.1 Global Shortcuts

| Key | Action |
|-----|--------|
| `q` / `Ctrl+C` | Quit application |
| `?` | Toggle help view |
| `r` | Force refresh all data |
| `Tab` | Cycle through views |
| `1-4` | Switch to view (1=Dashboard, 2=Details, 3=Logs, 4=Help) |

### 10.2 Dashboard View Shortcuts

| Key | Action |
|-----|--------|
| `↑` / `k` | Move cursor up |
| `↓` / `j` | Move cursor down |
| `Enter` | Open container details |
| `s` | Start selected container |
| `x` / `S` | Stop selected container |
| `r` | Restart selected container |
| `d` | Remove selected container |
| `l` | View container logs |
| `/` | Focus search filter |
| `o` | Sort options menu |
| `f` | Filter menu |

### 10.3 Details View Shortcuts

| Key | Action |
|-----|--------|
| `Esc` / `←` | Back to dashboard |
| `s` | Start container |
| `x` | Stop container |
| `r` | Restart container |
| `i` | Inspect (full JSON) |
| `l` | View logs |
| `c` | View charts |

### 10.4 Logs View Shortcuts

| Key | Action |
|-----|--------|
| `↑` / `k` | Scroll up |
| `↓` / `j` | Scroll down |
| `g` | Go to top |
| `G` | Go to bottom |
| `f` / `F` | Toggle follow mode |
| `t` | Toggle timestamps |
| `c` | Clear logs |
| `s` | Save to file |
| `Esc` | Back |

---

## 11. Implementation Phases

### Phase 1: Core Infrastructure
- [ ] Project setup (Go module, dependencies)
- [ ] Configuration system
- [ ] Docker client wrapper
- [ ] Basic Bubble Tea application
- [ ] Container list display

### Phase 2: Stats & Monitoring
- [ ] Stats streaming implementation
- [ ] CPU calculation
- [ ] Memory display
- [ ] Network I/O tracking
- [ ] Auto-refresh mechanism

### Phase 3: Lifecycle Management
- [ ] Start/Stop/Restart containers
- [ ] Container removal
- [ ] Operation confirmation dialogs
- [ ] Error handling & notifications

### Phase 4: Logs & Details
- [ ] Log streaming
- [ ] Logs viewer with filtering
- [ ] Container details view
- [ ] Health check display

### Phase 5: Polish
- [ ] Charts for historical data
- [ ] Keyboard shortcuts
- [ ] Help view
- [ ] Error recovery
- [ ] Edge case handling
- [ ] Testing

---

## 12. Testing Strategy

### 12.1 Unit Tests

```go
// Test data models
func TestStats_CalculateCPUPercentage(t *testing.T)
func TestContainer_ShortID(t *testing.T)
func TestFormatBytes(t *testing.T)

// Test configuration
func TestConfig_Load(t *testing.T)
func TestConfig_Defaults(t *testing.T)

// Test utilities
func TestFilter_Container(t *testing.T)
func TestSort_Containers(t *testing.T)
```

### 12.2 Integration Tests

```go
// Require Docker running
// Use testcontainers or real Docker socket

func TestDockerClient_ListContainers(t *testing.T)
func TestDockerClient_Stats(t *testing.T)
func TestDockerClient_Lifecycle(t *testing.T)
func TestDockerClient_Logs(t *testing.T)
```

### 12.3 UI Tests

```go
// Use tea.TestProgram for TUI testing
func TestDashboardView_Render(t *testing.T)
func TestKeyBindings(t *testing.T)
func TestNavigation(t *testing.T)
```

---

## 13. Dependencies

```go
// go.mod
module github.com/dockerwatch

go 1.21

require (
    github.com/charmbracelet/bubbletea v2.0.0+
    github.com/charmbracelet/bubbles v0.20.0+
    github.com/charmbracelet/lipgloss v0.11.0+
    github.com/docker/docker v27.0.0+
    github.com/docker/docker/client v27.0.0+
    github.com/spf13/viper v1.19.0
    github.com/stretchr/testify v1.9.0
)
```

---

## 14. Performance Considerations

1. **Stats Streaming**: Use single stream per container, not polling
2. **Render Optimization**: Only re-render changed cells
3. **Log Buffer**: Limit in-memory log entries, implement rolling buffer
4. **Concurrent Operations**: Limit parallel Docker API calls
5. **Memory**: Use value types where possible, avoid unnecessary copies
6. **CPU**: Batch UI updates, avoid per-frame allocations

---

## 15. Future Enhancements (Out of Scope)

- Container creation/editing
- Multi-host monitoring
- Web UI mode
- Metrics export (Prometheus)
- Alerts and notifications
- Container exec (attach to container)
- Resource limit editing

---

## 16. References

- [Docker Engine API](https://docs.docker.com/engine/api/)
- [Go Docker SDK](https://pkg.go.dev/github.com/docker/docker)
- [Bubble Tea Documentation](https://github.com/charmbracelet/bubbletea)
- [Lip Gloss Styling](https://github.com/charmbracelet/lipgloss)
- [Bubbles Components](https://github.com/charmbracelet/bubbles)
