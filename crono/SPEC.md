# Crono - Visual Cron Job Scheduler TUI

## Project Overview

**Project Name:** Crono
**Type:** Terminal User Interface (TUI) Application
**Core Functionality:** A visual cron job scheduler and manager built with Python's Textual framework. Enables users to create, edit, validate, and manage cron jobs through an intuitive keyboard-driven dark-themed interface.
**Target Users:** Developers, DevOps engineers, and system administrators who work with scheduled tasks.

---

## UI/UX Specification

### Layout Structure

#### Main Window (Single-screen Application)
- **Header Bar** (2 rows): App title, navigation breadcrumbs
- **Sidebar** (20% width): Job list panel with scrollable view
- **Main Content Area** (80% width): Job details, editor, or logs view
- **Status Bar** (1 row): Footer with keyboard shortcuts hint

#### Layout Regions
```
┌────────────────────────────────────────────────────────────┐
│ Crono - [Navigation Path]                           [?]    │
├──────────────┬───────────────────────────────────────────┤
│              │                                           │
│   Job List   │          Main Content Panel               │
│   Sidebar   │     (Details / Editor / Logs / History)     │
│              │                                           │
│              │                                           │
│  [+ Add Job] │                                           │
├──────────────┴───────────────────────────────────────────┤
│ ↑↓ Navigate │ Enter: Select │ e: Edit │ d: Delete │ q: Quit│
└────────────────────────────────────────────────────────────┘
```

### Visual Design

#### Color Palette (Dark Theme - Terminal Aesthetic)
| Role | Color | Hex Code |
|------|-------|----------|
| Background Primary | Deep Black | `#0d1117` |
| Background Secondary | Charcoal | `#161b22` |
| Background Tertiary | Dark Gray | `#21262d` |
| Surface/Cards | Slate | `#30363d` |
| Border Default | Muted Gray | `#484f58` |
| Border Focus | Electric Blue | `#58a6ff` |
| Text Primary | White | `#f0f6fc` |
| Text Secondary | Light Gray | `#8b949e` |
| Text Muted | Dim Gray | `#6e7681` |
| Accent Primary | Cyan | `#39d4e8` |
| Accent Secondary | Teal | `#3fb9a5` |
| Success | Green | `#3fb950` |
| Warning | Amber | `#d29922` |
| Error | Red | `#f85149` |
| Cron Expression | Purple | `#a371f7` |

#### Typography
- **Font Family:** `JetBrains Mono`, `Fira Code`, `Consolas`, `monospace`
- **Font Sizes:**
  - App Title: 18px, bold
  - Section Headers: 14px, semi-bold
  - Body Text: 13px, regular
  - Code/Cron: 14px, mono-weight
  - Status/Hints: 11px, regular

#### Spacing System
- Base Unit: 4px
- Padding Small: 8px (2 units)
- Padding Medium: 16px (4 units)
- Padding Large: 24px (6 units)
- Margin Between Sections: 16px
- Border Radius: 6px

#### Visual Effects
- Box shadows on focus: `0 0 0 2px #58a6ff`
- Subtle gradients on header: `#161b22` to `#0d1117`
- Smooth transitions: 150ms ease-out
- Hover states: Background lightens by 5%

### Components

#### 1. Job List Item
- States: Default, Hover, Selected, Disabled
- Display: Job name, cron expression (truncated), next run time
- Indicators: Active status (green dot), Paused status (yellow dot)

#### 2. Job Details Panel
- Fields: Name, Command, Cron Expression, Description
- Read-only display with Edit button
- Next 5 run times preview

#### 3. Cron Expression Editor
- Input fields for: minute, hour, day, month, weekday
- Real-time validation with visual feedback
- Human-readable description of schedule
- Next run time preview

#### 4. Job History Log
- Table view: Timestamp, Status (Success/Failed), Duration, Output (truncated)
- Filter by job, status, date range
- Expandable rows for full output

#### 5. Keyboard Navigation
| Key | Action |
|-----|--------|
| ↑/↓ | Navigate job list |
| Enter | Select job / Confirm dialog |
| Tab | Switch between panels |
| e | Edit selected job |
| n | New job |
| d | Delete job (with confirmation) |
| Space | Toggle job active/paused |
| l | View job history |
| r | Run jobnow |
| q / Escape | Quit / Back |
| Ctrl+f | Search jobs |
| F1 | Show help |

---

## Functionality Specification

### Core Features

#### 1. Cron Expression Parser/Validator
- **Parse:** Split cron string into components (minute, hour, day, month, weekday)
- **Validate:**
  - Valid range checks (minute: 0-59, hour: 0-23, day: 1-31, month: 1-12, weekday: 0-6)
  - Special characters supported: `*`, `,`, `-`, `/`, `L`, `W`, `#`
  - Named values (JAN-DEC, SUN-SAT, etc.)
- **Error Messages:** Clear indication of invalid field with suggestion
- **Examples:**
  - `* * * * *` - Every minute
  - `0 9 * * 1-5` - Weekdays at 9:00
  - `0 0 1 * *` - First of every month at midnight

#### 2. Next Run Time Calculator
- **Algorithm:** Calculate next N execution times from current time
- **Features:**
  - Handle all cron special characters
  - Timezone support (default: local)
  - Skip logic for past times
- **Output:** Human-readable relative times ("in 2 hours", "tomorrow at 09:00")

#### 3. Job CRUD Operations
- **Create:** Add new job with validation
- **Read:** View job details, history
- **Update:** Edit job properties
- **Delete:** Remove job with confirmation dialog
- **Job Properties:**
  - `id`: UUID
  - `name`: Display name (required, unique)
  - `command`: Shell command to execute
  - `cron_expression`: Schedule (required, validated)
  - `description`: Optional description
  - `enabled`: Boolean (active/paused)
  - `created_at`: Timestamp
  - `updated_at`: Timestamp
  - `last_run`: Timestamp of last execution
  - `next_run`: Calculated next execution time

#### 4. Job Execution / Simulation
- **Note:** This is a scheduler *manager* UI, not a running daemon
- **Run Now:** Execute job command immediately (simulated - logs attempt)
- **Validate Only:** Test cron expression without saving

#### 5. Job History Logging
- **Storage:** SQLite database or JSON file
- **Log Entry:**
  - `id`: UUID
  - `job_id`: Reference to job
  - `timestamp`: Execution time
  - `status`: success | failed | timeout
  - `duration`: Execution time in seconds
  - `output`: Stdout/stderr capture (truncated for display)
  - `error`: Error message if failed
- **Features:**
  - View last 100 entries per job
  - Filter by status
  - Export to CSV

### Data Flow & Processing

#### Storage Layer
```
jobs.json (or cronodata.db)
├── jobs[]
│   ├── id: string
│   ├── name: string
│   ├── command: string
│   ├── cron_expression: string
│   ├── description: string
│   ├── enabled: boolean
│   ├── created_at: iso8601
│   └── updated_at: iso8601
├── history[]
│   ├── id: string
│   ├── job_id: string
│   ├── timestamp: iso8601
│   ├── status: string
│   ├── duration: float
│   ├── output: string
│   └── error: string
└── settings{}
    └── timezone: string
```

#### Key Modules
1. **cron_parser.py** - Cron expression handling
2. **job_manager.py** - CRUD operations
3. **history.py** - History logging
4. **storage.py** - Data persistence
5. **app.py** - Main Textual application
6. **screens.py** - UI screens
7. **widgets.py** - Reusable UI components

### Edge Cases
- Empty job list: Show welcome screen with "Add your first job"
- Invalid cron expression: Highlight error, prevent save
- Duplicate job name: Show error, suggest alternative
- No history: Show "No execution history yet"
- Network/disk error on save: Show error notification, offer retry

---

## Acceptance Criteria

### Visual Checkpoints
- [ ] Dark theme renders correctly with specified colors
- [ ] Job list scrolls smoothly with keyboard
- [ ] Selected job shows clear focus indicator (blue border)
- [ ] Form validation errors display in red
- [ ] Cron expression highlights special characters in purple

### Functional Checkpoints
- [ ] Can create a new job with valid cron expression
- [ ] Invalid cron shows clear error message
- [ ] Can edit existing job and save changes
- [ ] Can delete job with confirmation
- [ ] Next run times calculate correctly
- [ ] History logs display with proper formatting
- [ ] Keyboard navigation works throughout
- [ ] Application starts without errors

### Technical Checkpoints
- [ ] No type errors (mypy if applicable)
- [ ] All dependencies specified in requirements.txt
- [ ] README includes installation and usage instructions
- [ ] Code follows consistent style (PEP 8)

---

## File Structure
```
crono/
├── SPEC.md
├── README.md
├── requirements.txt
├── pyproject.toml (optional)
├── cron/
│   ├── __init__.py
│   ├── __main__.py
│   ├── cron_parser.py
│   ├── job_manager.py
│   ├── history.py
│   ├── storage.py
│   ├── models.py
│   ├── app.py
│   ├── screens.py
│   └── widgets.py
└── tests/
    └── test_cron_parser.py
```