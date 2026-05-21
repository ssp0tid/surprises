# Code Time Tracker - Implementation Plan

## 1. Overview

**Purpose**: Local desktop application that tracks active window focus time per project, runs as a background daemon, and provides a web dashboard with daily/weekly reports.

**Target Users**: Developers who want to understand their coding patterns without cloud dependencies.

---

## 2. Technology Stack

| Layer | Technology | Rationale |
|-------|-----------|-----------|
| **Daemon** | Node.js + native modules | Cross-platform window detection |
| **Database** | SQLite (better-sqlite3) | Zero-config, local-only, ACID |
| **API Server** | Express.js | Lightweight, proven |
| **Dashboard** | Vanilla JS + Chart.js | No build step, minimal dependencies |
| **Window Detection** | OS-specific APIs via node-ffi/native addons | Required for actual focus tracking |

### Why Not Electron?
- Electron adds significant overhead for a simple background service
- Native window management requires platform-specific code anyway
- Simpler deployment with a single Node.js process

---

## 3. File Structure

```
code-time-tracker/
├── src/
│   ├── daemon/
│   │   ├── index.ts              # Main entry, daemon orchestration
│   │   ├── window-monitor.ts     # Active window detection
│   │   ├── idle-detector.ts      # System idle tracking
│   │   ├── activity-recorder.ts  # Write sessions to DB
│   │   └── process-detector.ts   # Map window → project
│   ├── api/
│   │   ├── server.ts             # Express app setup
│   │   ├── routes/
│   │   │   ├── sessions.ts       # CRUD for time sessions
│   │   │   ├── projects.ts       # Project management
│   │   │   ├── reports.ts        # Aggregated reports
│   │   │   └── health.ts         # Daemon status
│   │   └── middleware/
│   │       └── error-handler.ts
│   ├── db/
│   │   ├── schema.sql            # Database schema
│   │   ├── repository.ts         # Data access layer
│   │   └── migrations/
│   │       └── 001_initial.ts
│   ├── config/
│   │   └── defaults.ts           # Default configuration
│   ├── utils/
│   │   ├── logger.ts             # Structured logging
│   │   └── process.ts            # Process name extraction
│   └── types/
│       └── index.ts              # TypeScript interfaces
├── public/
│   ├── index.html                # Dashboard SPA shell
│   ├── css/
│   │   └── dashboard.css
│   └── js/
│       ├── app.js                # Main dashboard logic
│       ├── charts.js             # Chart.js wrappers
│       └── api-client.js         # API communication
├── package.json
├── tsconfig.json
├── SPEC.md                       # Feature specifications
└── README.md
```

---

## 4. Database Schema

```sql
-- Projects (user-defined categorizations)
CREATE TABLE projects (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    color TEXT DEFAULT '#6366f1',
    keywords TEXT,           -- JSON array: ["github", "vscode", "intellij"]
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Time sessions (continuous active periods)
CREATE TABLE sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id TEXT REFERENCES projects(id),
    start_time DATETIME NOT NULL,
    end_time DATETIME,
    duration_seconds INTEGER,
    window_title TEXT,       -- Original window title for debugging
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Idle periods (auto-detected gaps)
CREATE TABLE idle_periods (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    start_time DATETIME NOT NULL,
    end_time DATETIME NOT NULL,
    duration_seconds INTEGER NOT NULL
);

-- Settings (key-value store)
CREATE TABLE settings (
    key TEXT PRIMARY KEY,
    value TEXT
);

-- Indexes for common queries
CREATE INDEX idx_sessions_project_time ON sessions(project_id, start_time);
CREATE INDEX idx_sessions_start_time ON sessions(start_time);
```

---

## 5. API Design

### Base URL: `http://localhost:3737/api/v1`

### 5.1 Sessions

```
GET    /sessions
       Query: ?from=2024-01-01&to=2024-01-31&project_id=abc
       Response: { sessions: [...], total_duration: 36000 }

POST   /sessions
       Body: { project_id, start_time, end_time }
       Response: { id, ... }

DELETE /sessions/:id
       Response: { deleted: true }
```

### 5.2 Projects

```
GET    /projects
       Response: { projects: [...] }

POST   /projects
       Body: { name, color?, keywords? }
       Response: { id, name, ... }

PUT    /projects/:id
       Body: { name?, color?, keywords? }
       Response: { id, name, ... }

DELETE /projects/:id
       Response: { deleted: true }

POST   /projects/:id/merge
       Body: { source_project_id }
       Response: { merged_project_id }
```

### 5.3 Reports

```
GET    /reports/daily
       Query: ?date=2024-01-15
       Response: {
         date: "2024-01-15",
         total_focused_minutes: 240,
         sessions_by_project: [{ project_id, name, minutes }, ...],
         hourly_breakdown: [{ hour, minutes }, ...],
         idle_minutes: 15
       }

GET    /reports/weekly
       Query: ?week=2024-W03
       Response: {
         week: "2024-W03",
         total_focused_hours: 32.5,
         daily_breakdown: [{ date, minutes }, ...],
         top_projects: [{ project_id, name, hours }, ...],
         average_daily_hours: 6.5
       }

GET    /reports/summary
       Query: ?from=2024-01-01&to=2024-01-31
       Response: {
         total_days: 31,
         total_focused_hours: 85,
         most_productive_day: "Tuesday",
         top_project: { name, hours },
         daily_average_hours: 2.7
       }
```

### 5.4 Health & Daemon

```
GET    /health
       Response: {
         status: "running",
         version: "1.0.0",
         uptime_seconds: 86400,
         last_session_at: "2024-01-15T16:30:00Z",
         is_currently_focused: true,
         current_project: { id, name }
       }

POST   /daemon/pause
       Response: { paused: true }

POST   /daemon/resume
       Response: { paused: false }

POST   /daemon/reload
       Response: { reloaded: true }
```

### 5.5 Error Response Format

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid date range",
    "details": {
      "field": "from",
      "reason": "Must be before 'to' date"
    }
  }
}
```

---

## 6. Core Module Design

### 6.1 Daemon Orchestration (`daemon/index.ts`)

```typescript
class Daemon {
  private isPaused: boolean = false;
  private currentSession: ActiveSession | null = null;
  private idleDetector: IdleDetector;
  private windowMonitor: WindowMonitor;
  private activityRecorder: ActivityRecorder;

  async start(): Promise<void> {
    await this.db.initialize();
    this.windowMonitor.on('active-window-changed', this.handleWindowChange.bind(this));
    this.idleDetector.on('idle-detected', this.handleIdle.bind(this));
    this.idleDetector.on('activity-resumed', this.handleActivityResume.bind(this));
    this.windowMonitor.start();
  }

  private async handleWindowChange(newWindow: WindowInfo): Promise<void> {
    if (this.isPaused) return;

    const project = this.projectMatcher.match(newWindow);
    if (project?.id !== this.currentSession?.projectId) {
      await this.endCurrentSession();
      await this.startNewSession(project);
    }
  }
}
```

### 6.2 Window Monitor (`daemon/window-monitor.ts`)

**Responsibility**: Poll active window at regular intervals (every 5 seconds).

| Platform | Method |
|----------|--------|
| macOS | `NSWorkspace.shared.frontmostApplication` |
| Windows | `GetForegroundWindow` + `GetWindowText` |
| Linux | `X11` via `python-xlib` or `xdump` |

```typescript
interface WindowInfo {
  title: string;
  processName: string;
  processPath: string;
  timestamp: Date;
}
```

### 6.3 Project Matcher (`process-detector.ts`)

**Responsibility**: Map window info → project based on keywords.

```typescript
class ProjectMatcher {
  constructor(private projects: Project[], private cache: LRUCache<string, Project>) {}

  match(window: WindowInfo): Project | null {
    const cacheKey = `${window.processName}:${window.title}`;

    if (this.cache.has(cacheKey)) {
      return this.cache.get(cacheKey)!;
    }

    const matched = this.projects.find(project =>
      project.keywords.some(keyword =>
        window.title.toLowerCase().includes(keyword.toLowerCase()) ||
        window.processName.toLowerCase().includes(keyword.toLowerCase())
      )
    );

    this.cache.set(cacheKey, matched ?? null);
    return matched ?? null;
  }
}
```

### 6.4 Idle Detector (`idle-detector.ts`)

**Responsibility**: Detect user inactivity to pause tracking.

| Platform | Method |
|----------|--------|
| macOS | `IOKit` power management, `CGEvent` tap |
| Windows | `GetLastInputInfo` |
| Linux | `X11` screen saver events, `logind` |

```typescript
interface IdleConfig {
  thresholdSeconds: number;     // Default: 300 (5 min)
  checkIntervalMs: number;      // Default: 30000 (30 sec)
  gracePeriodMs: number;       // Default: 5000 (ignore brief gaps)
}
```

**State Machine**:
```
ACTIVE → (idle detected) → IDLE → (activity detected) → ACTIVE
                ↓
          (session in progress)
         End session, record idle period
```

### 6.5 Activity Recorder (`activity-recorder.ts`)

**Responsibility**: Write time sessions to database with deduplication.

```typescript
class ActivityRecorder {
  async recordSession(session: TimeSession): Promise<void> {
    // Merge adjacent sessions for same project (within 30 sec gap)
    // Handle timezone correctly using local time
    // Validate no overlapping sessions
    await this.db.transaction(async tx => {
      await tx.sessions.insert(session);
      await this.updateProjectTotals(session.projectId);
    });
  }
}
```

---

## 7. Dashboard Design

### 7.1 Pages

1. **Today's Focus** (`/`)
   - Today's total focused time (large display)
   - Hourly breakdown bar chart
   - Current/most recent project indicator
   - Quick toggle: pause/resume tracking

2. **Weekly Report** (`/weekly`)
   - Week selector (prev/next arrows)
   - Daily bar chart (Mon-Sun)
   - Project distribution pie chart
   - Total hours + daily average

3. **Projects** (`/projects`)
   - List all projects with total time
   - Add/edit/delete project
   - Color picker for project
   - Keyword editor (what windows match this project)

4. **Settings** (`/settings`)
   - Idle threshold configuration
   - Auto-start on login toggle
   - Export data (JSON/CSV)
   - Clear all data (with confirmation)

### 7.2 Visual Style

- **Theme**: Dark mode default (easier on developer eyes)
- **Colors**:
  - Background: `#0f172a` (slate-900)
  - Cards: `#1e293b` (slate-800)
  - Text: `#f1f5f9` (slate-100)
  - Accent: `#6366f1` (indigo-500)
  - Success: `#22c55e` (green-500)
  - Warning: `#f59e0b` (amber-500)
- **Typography**: System font stack (`-apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif`)
- **Charts**: Chart.js with custom dark theme

---

## 8. Error Handling Strategy

### 8.1 Error Categories

| Category | Handling |
|----------|----------|
| **Transient DB errors** | Retry with exponential backoff (3 attempts) |
| **Window monitor failures** | Log error, continue polling, alert after 5 failures |
| **API validation errors** | Return 400 with detailed message |
| **API server crashes** | Daemon continues; restart server separately |
| **Idle detection failures** | Fall back to always-active mode |

### 8.2 Logging

```typescript
enum LogLevel {
  DEBUG = 0,   // Detailed flow tracing
  INFO = 1,    // Major events (session start/end)
  WARN = 2,    // Recoverable issues (retry succeeded)
  ERROR = 3    // Unrecoverable, needs attention
}

interface LogEntry {
  timestamp: string;
  level: LogLevel;
  module: string;
  message: string;
  context?: Record<string, unknown>;
}
```

**Log rotation**: Keep 7 days of logs, max 50MB total.

### 8.3 Crash Recovery

```typescript
// On startup: check for orphaned sessions (end_time = NULL)
async recoverOrphanedSessions(): Promise<void> {
  const orphans = await this.db.sessions.findAll({ where: { end_time: null }});
  for (const session of orphans) {
    // Cap at reasonable max (8 hours) to prevent runaway sessions
    session.end_time = min(
      session.start_time + 8 hours,
      last_activity_timestamp
    );
    await this.db.sessions.update(session);
  }
}
```

---

## 9. Edge Cases

### 9.1 Time Zone Handling

- All timestamps stored in UTC
- Display converted to local time on frontend
- Sessions split at midnight local time (creates new session for each day)

### 9.2 System Sleep/Hibernate

```
On wake: detect time gap > threshold
  → Record idle period for the gap
  → Resume monitoring from current moment
  → Do NOT retroactively claim those hours
```

### 9.3 Multiple Monitors

- Track whichever window has focus (frontmost)
- If multiple screens have "focused" apps, use most recently activated
- Log multi-monitor edge case for debugging

### 9.4 Project Overlap

**Scenario**: Window matches multiple projects (e.g., "VSCode - github/correct-repo")

**Resolution**: First matching keyword wins (ordered by specificity). Allow manual override on dashboard.

### 9.5 Very Long Sessions

**Cap**: Single session max 8 hours. Auto-split into 8-hour chunks.

**Rationale**: Prevents runaway sessions from bugs; user likely took breaks but forgot to stop tracking.

### 9.6 Clock Skew

- Reject sessions where `end_time < start_time`
- Reject sessions where `duration > 24 hours` (flag as bug)
- Use monotonic clock for duration calculation when possible

### 9.7 Database Corruption

- Use SQLite WAL mode for crash resilience
- Backup database daily (keep 7 days)
- On corruption: restore from backup, log error, notify user

---

## 10. Implementation Phases

### Phase 1: Foundation
- [ ] Project setup (TypeScript, build config)
- [ ] Database schema + repository
- [ ] Basic Express server with health endpoint
- [ ] Logging infrastructure

### Phase 2: Core Tracking
- [ ] Platform-specific window monitor (one OS first)
- [ ] Idle detector
- [ ] Project matcher with keyword storage
- [ ] Session recording to database

### Phase 3: API Layer
- [ ] Sessions CRUD endpoints
- [ ] Projects CRUD endpoints
- [ ] Reports endpoints (daily/weekly)
- [ ] Error handling middleware

### Phase 4: Dashboard
- [ ] Static HTML/CSS/JS shell
- [ ] Today's focus page
- [ ] Weekly report page with charts
- [ ] Projects management page
- [ ] Settings page

### Phase 5: Polish
- [ ] Multi-platform window detection (macOS/Windows/Linux)
- [ ] System tray integration
- [ ] Auto-start on login
- [ ] Data export (JSON/CSV)
- [ ] Crash recovery
- [ ] Log rotation

---

## 11. Dependencies

```json
{
  "dependencies": {
    "better-sqlite3": "^9.4.0",
    "express": "^4.18.2",
    "chart.js": "^4.4.0",
    "date-fns": "^3.3.0",
    "electron-log": "^5.1.0",
    "pino": "^8.18.0",
    "pino-pretty": "^10.3.0",
    "conf": "^12.0.0"
  },
  "devDependencies": {
    "typescript": "^5.3.0",
    "ts-node": "^10.9.0",
    "tsx": "^4.7.0",
    "@types/better-sqlite3": "^7.6.8",
    "@types/express": "^4.17.21",
    "esbuild": "^0.20.0"
  }
}
```

---

## 12. Configuration Defaults

```typescript
const defaults = {
  daemon: {
    pollIntervalMs: 5000,
    idleThresholdSeconds: 300,
    idleCheckIntervalMs: 30000,
    maxSessionDurationHours: 8,
    gracePeriodMs: 5000
  },
  api: {
    port: 3737,
    host: 'localhost'
  },
  logging: {
    level: 'info',
    maxFiles: 7,
    maxSizeMb: 50
  },
  storage: {
    dbPath: '~/.code-time-tracker/data.db',
    backupPath: '~/.code-time-tracker/backups'
  }
};
```

---

## 13. Security Considerations

- **Local-only**: No network exposure by default (localhost only)
- **No telemetry**: Zero external connections
- **Data ownership**: All data stays on user's machine
- **Config isolation**: User config in OS-standard locations

---

## 14. Future Considerations (Out of Scope for V1)

- Pomodoro timer integration
- Goals/exclusions (meetings auto-detected)
- Slack/calendar integration hints
- Multi-machine sync via local network
- Mobile companion app
- AI-based project categorization