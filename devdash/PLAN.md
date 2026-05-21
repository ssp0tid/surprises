# DevDash - Local Developer Dashboard

## 1. Project Overview

**Project Name**: DevDash
**Project Type**: Local Development Environment Management Tool
**Core Functionality**: Discovers, monitors, and manages local development servers (Node.js, Python Flask/FastAPI, Go, etc.) through a web interface with real-time updates.
**Target Users**: Software developers running multiple local dev services simultaneously.

---

## 2. Technical Stack

| Component | Technology | Version |
|-----------|------------|---------|
| Backend Framework | Flask | 3.x |
| Process Monitoring | psutil | 5.9.x |
| Real-time Updates | Flask-SocketIO | 5.x |
| Async Events | python-socketio[client] | 6.x |
| Frontend | Vanilla JS + TailwindCSS | 3.x |
| Process Management | subprocess (stdlib) | - |
| Log Tailing | tailer (stdlib) | - |

---

## 3. File Structure

```
devdash/
├── devdash/
│   ├── __init__.py
│   ├── app.py                    # Flask application factory
│   ├── config.py                 # Configuration settings
│   ├── models/
│   │   ├── __init__.py
│   │   └── service.py            # Service data models
│   ├── services/
│   │   ├── __init__.py
│   │   ├── discoverer.py         # Process/port discovery
│   │   ├── monitor.py            # CPU/memory monitoring
│   │   ├── log_viewer.py         # Log file tailing
│   │   └── process_manager.py    # Process restart/kill
│   ├── api/
│   │   ├── __init__.py
│   │   ├── routes/
│   │   │   ├── __init__.py
│   │   │   ├── services.py       # Service CRUD endpoints
│   │   │   ├── logs.py            # Log streaming endpoints
│   │   │   └── actions.py         # Restart/kill endpoints
│   │   └── websocket.py           # Real-time updates handler
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── logger.py              # Logging setup
│   │   └── validators.py          # Input validation
│   └── templates/
│       └── index.html             # Main dashboard UI
├── static/
│   ├── css/
│   │   └── styles.css             # Custom styles
│   └── js/
│       └── app.js                 # Frontend logic
├── logs/                          # DevDash's own logs
├── requirements.txt
├── config.yaml                    # User configuration
├── run.py                         # Entry point
└── README.md
```

---

## 4. Data Models

### 4.1 Service Model

```python
@dataclass
class Service:
    id: str                           # Unique identifier (port-based)
    name: str                        # Auto-detected or user-defined name
    pid: int                         # Process ID
    port: int                        # Listening port
    protocol: str                    # "http" or "https"
    process_type: str               # "node", "python", "go", "java", "ruby", "unknown"
    command: str                     # Full command line
    cpu_percent: float               # CPU usage (0-100)
    memory_mb: float                 # Memory usage in MB
    memory_percent: float            # Memory % of total
    uptime_seconds: int              # Process uptime
    status: str                      # "running", "stopped", "error"
    log_file: Optional[str]          # Path to log file if detectable
    started_at: datetime             # When first detected
    last_updated: datetime           # Last update timestamp
```

### 4.2 Discovery Patterns

| Process Type | Detection Method | Log Locations |
|--------------|------------------|---------------|
| Node.js | `command contains "node"` + port scan | `*.log`, stdout |
| Python Flask | `command contains "flask" or "python"` | stdout, stderr |
| Python FastAPI | `command contains "fastapi" or "uvicorn"` | stdout, stderr |
| Go | `command contains "go run" or binary` | stdout, stderr |
| Java | `command contains "java"` + port scan | stdout, stderr |
| Ruby | `command contains "rails" or "ruby"` | `log/*.log` |
| PHP | `command contains "php" or "artisan serve"` | `storage/logs/*.log` |

---

## 5. API Design

### 5.1 REST Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/services` | List all discovered services |
| GET | `/api/services/<id>` | Get service details |
| GET | `/api/services/<id>/metrics` | Get CPU/memory history |
| GET | `/api/services/<id>/logs` | Get recent log lines |
| POST | `/api/services/<id>/restart` | Restart a service |
| POST | `/api/services/<id>/kill` | Kill a service |
| POST | `/api/services/<id>/rename` | Rename a service |
| GET | `/api/ports` | List all ports in use |
| GET | `/api/system` | System-wide stats |

### 5.2 WebSocket Events

| Event | Direction | Payload |
|-------|-----------|---------|
| `service:discovered` | Server → Client | New service object |
| `service:updated` | Server → Client | Updated service object |
| `service:stopped` | Server → Client | Service ID |
| `metrics:update` | Server → Client | { service_id, cpu, memory, timestamp } |
| `log:new_line` | Server → Client | { service_id, line, timestamp } |
| `subscribe` | Client → Server | { service_id } |
| `unsubscribe` | Client → Server | { service_id } |

### 5.3 Response Format

**Success Response:**
```json
{
  "success": true,
  "data": { ... },
  "timestamp": "2024-01-15T10:30:00Z"
}
```

**Error Response:**
```json
{
  "success": false,
  "error": {
    "code": "SERVICE_NOT_FOUND",
    "message": "Service with ID 'abc123' not found"
  },
  "timestamp": "2024-01-15T10:30:00Z"
}
```

---

## 6. Implementation Details

### 6.1 Service Discovery (services/discoverer.py)

```python
class ServiceDiscoverer:
    def __init__(self, scan_ports: List[int] = None):
        self.scan_ports = scan_ports or DEFAULT_DEV_PORTS
        self.known_processes = {}  # pid -> Service

    def discover(self) -> List[Service]:
        """Scan for all development server processes."""
        services = []
        for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'create_time']):
            try:
                if self._is_dev_server(proc):
                    service = self._create_service(proc)
                    services.append(service)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        return services

    def _is_dev_server(self, proc) -> bool:
        """Check if process is a dev server."""
        # Check process name and command line
        # Detect common dev server patterns
        pass

    def get_port_processes(self, port: int) -> Optional[Service]:
        """Find process listening on specific port."""
        pass
```

### 6.2 Monitoring (services/monitor.py)

```python
class ServiceMonitor:
    def __init__(self, update_interval: float = 2.0):
        self.update_interval = update_interval
        self._running = False

    async def start(self):
        """Start background monitoring loop."""
        while self._running:
            await self._collect_metrics()
            await asyncio.sleep(self.update_interval)

    def get_metrics(self, pid: int) -> Dict:
        """Get current CPU/memory for process."""
        proc = psutil.Process(pid)
        with proc.oneshot():
            return {
                'cpu_percent': proc.cpu_percent(interval=0.1),
                'memory_mb': proc.memory_info().rss / 1024 / 1024,
                'memory_percent': proc.memory_percent(),
                'num_threads': proc.num_threads(),
                'status': proc.status(),
                'uptime': time.time() - proc.create_time()
            }
```

### 6.3 Log Viewer (services/log_viewer.py)

```python
class LogViewer:
    def __init__(self, max_lines: int = 1000):
        self.max_lines = max_lines
        self._file_positions = {}  # service_id -> file position

    async def tail_logs(self, service_id: str, callback: Callable):
        """Stream new log lines via callback."""
        # Detect log file location
        # Track file position
        # Yield new lines as they appear
        pass

    def get_recent_logs(self, service_id: str, lines: int = 100) -> List[str]:
        """Get N most recent log lines."""
        pass
```

### 6.4 Process Manager (services/process_manager.py)

```python
class ProcessManager:
    def restart_service(self, service_id: str) -> bool:
        """Restart a service by killing and re-running."""
        # 1. Get original command from stored service
        # 2. Kill the process
        # 3. Start new process with same command
        # 4. Update service registry
        pass

    def kill_service(self, service_id: str) -> bool:
        """Force kill a service."""
        pass

    def get_process_tree(self, pid: int) -> List[psutil.Process]:
        """Get all child processes."""
        pass
```

---

## 7. Web Dashboard

### 7.1 UI Layout

```
┌─────────────────────────────────────────────────────────────┐
│  DevDash                              [System: 4 services] │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  Node App    │  │  Flask API    │  │  Go Server   │      │
│  │  :3000       │  │  :5000        │  │  :8080       │      │
│  │  ● running   │  │  ● running   │  │  ● running   │      │
│  │  CPU: 12%    │  │  CPU: 3%      │  │  CPU: 8%     │      │
│  │  MEM: 180MB  │  │  MEM: 45MB    │  │  MEM: 62MB   │      │
│  │  [Restart]   │  │  [Restart]   │  │  [Restart]   │      │
│  │  [Kill]      │  │  [Kill]      │  │  [Kill]      │      │
│  │  [Logs]      │  │  [Logs]      │  │  [Logs]      │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐  │
│  │  Logs: Node App (:3000)              [Clear] [Download]│
│  ├─────────────────────────────────────────────────────┤  │
│  │  [10:30:01] Server started on port 3000            │  │
│  │  [10:30:02] Connected to database                   │  │
│  │  [10:30:05] GET /api/users 200 15ms                 │  │
│  │  ...                                                │  │
│  └─────────────────────────────────────────────────────┘  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 7.2 Real-time Updates

```javascript
// WebSocket connection
const socket = io();

// Subscribe to all service updates
socket.on('service:updated', (service) => {
    updateServiceCard(service);
});

// Subscribe to specific service logs
socket.emit('subscribe', { service_id: 'node-3000' });

socket.on('log:new_line', (data) => {
    appendLogLine(data.service_id, data.line);
});

// Polling fallback (if WebSocket fails)
setInterval(fetchServices, 5000);
```

---

## 8. Configuration (config.yaml)

```yaml
devdash:
  host: "127.0.0.1"
  port: 7890
  debug: false

discovery:
  scan_interval: 5  # seconds
  ports:
    - 3000    # Node.js common
    - 3001    # Node.js alternative
    - 4200    # Angular
    - 5000    # Flask default
    - 5001    # Flask alternative
    - 8000    # Django/FastAPI
    - 8080    # Java/Go common
    - 8888    # Jupyter
    - 9000    # PHP
  excluded_pids: []  # PIDs to ignore
  process_blacklist:  # Process names to ignore
    - chrome
    - firefox
    - slack

monitoring:
  update_interval: 2  # seconds
  history_length: 60  # number of data points to keep

logs:
  max_lines: 1000
  auto_detect_logfiles: true
  log_directory: "logs"

actions:
  confirm_before_kill: true
  allow_restart: true
```

---

## 9. Edge Cases & Error Handling

### 9.1 Process Discovery Edge Cases

| Scenario | Handling |
|----------|----------|
| Process exits between discovery and detail fetch | Return 404, remove from list |
| Process belongs to different user | Skip (AccessDenied) |
| Zombie process | Mark as "zombie", show warning |
| Process name too long | Truncate at 100 chars |
| Port already closed | Mark service as "stopped" |
| Multiple processes on same port | Show all, mark conflict |

### 9.2 Resource Monitoring Edge Cases

| Scenario | Handling |
|----------|----------|
| CPU spike during measurement | Use rolling average |
| Memory measurement fails | Return last known value + warning |
| Process terminates during monitoring | Gracefully remove from monitoring |
| High CPU causing lag | Increase update interval automatically |

### 9.3 Log Viewing Edge Cases

| Scenario | Handling |
|----------|----------|
| Log file deleted | Show error, stop streaming |
| Log file rotated | Detect rotation, follow new file |
| Log file too large | Only read last 10MB |
| Binary log file | Detect and show warning |
| Permission denied | Show error, suggest fix |

### 9.4 Process Management Edge Cases

| Scenario | Handling |
|----------|----------|
| Process refuses to kill | Force kill after 5s timeout |
| Restart command not available | Show error, suggest manual restart |
| Process respawns immediately | Detect and warn about supervisor |
| Service has child processes | Kill entire process tree |

### 9.5 Network/WebSocket Edge Cases

| Scenario | Handling |
|----------|----------|
| WebSocket connection lost | Auto-reconnect with exponential backoff |
| Client disconnected | Stop sending updates for that client |
| Too many concurrent clients | Limit to 10 per instance |
| Browser tab inactive | Reduce update frequency |

---

## 10. Implementation Phases

### Phase 1: Core Discovery & Monitoring
- [ ] Flask app setup with SocketIO
- [ ] Service discovery (basic process scanning)
- [ ] CPU/memory monitoring loop
- [ ] REST API for services list/details

### Phase 2: Web Dashboard
- [ ] HTML/CSS dashboard template
- [ ] Service cards with status
- [ ] WebSocket integration for real-time updates
- [ ] Basic styling with TailwindCSS

### Phase 3: Log Viewing
- [ ] Log file detection
- [ ] Log streaming via WebSocket
- [ ] Log viewer UI component

### Phase 4: Process Actions
- [ ] Kill service functionality
- [ ] Restart service functionality
- [ ] Confirmation dialogs

### Phase 5: Polish & Edge Cases
- [ ] Error handling improvements
- [ ] Configuration file support
- [ ] System tray (optional)
- [ ] Auto-refresh on tab focus

---

## 11. Security Considerations

1. **Local-only binding**: Bind to `127.0.0.1` by default
2. **No authentication**: Local dev tool, but consider optional password
3. **Process access**: Only monitor processes running as same user
4. **Log file access**: Respect file permissions
5. **Command injection**: Sanitize process commands before execution

---

## 12. Acceptance Criteria

- [ ] Discovers Node.js, Python, Go dev servers running on common ports
- [ ] Shows real-time CPU and memory usage for each service
- [ ] Web UI updates automatically without page refresh
- [ ] Can view live logs for each service
- [ ] Can restart/stop services from UI
- [ ] Handles process termination gracefully
- [ ] Works on macOS, Linux (Windows optional)
- [ ] Startup time < 3 seconds
- [ ] Memory footprint < 50MB

---

## 13. Future Enhancements

- System tray icon for background operation
- Browser notifications for service crashes
- Service dependency mapping
- Startup script management
- Docker container monitoring
- Multi-machine support (via SSH)
- Metrics history and graphing
- Export/import configuration
