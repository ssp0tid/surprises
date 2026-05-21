# Incident Command Center TUI

A Textual-based Terminal User Interface (TUI) application for on-call engineers to manage production incidents with severity levels (P1-P4), timeline tracking, status updates, and on-call team roster management.

## Features

- **Incident Management**: Create, update, and track incidents with P1 (Critical) to P4 (Low) severity levels
- **Timeline Tracking**: Automatic tracking of status changes, assignments, and notes for each incident
- **Status Workflow**: Declared → Investigating → Identified → Mitigating → Resolved
- **On-Call Roster**: Manage the on-call team (Primary, Secondary, Escalation)
- **SQLite Persistence**: All data stored in local SQLite database
- **Keyboard Navigation**: Full keyboard support with shortcuts

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run the application
python app.py
```

## Requirements

- Python 3.10+
- textual>=8.0.0
- rich>=13.7.0
- sqlalchemy>=2.0.0
- aiosqlite>=0.19.0

## Installation

```bash
# Clone or navigate to the project directory
cd incident-command-center

# Create virtual environment (optional but recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Usage

### Running the Application

```bash
python app.py
```

### Keyboard Shortcuts

| Key | Command |
|-----|---------|
| `n` | Create new incident |
| `r` | Refresh data |
| `q` | Quit application |
| `?` | Show help |
| `↑/↓` | Navigate incident list |
| `Enter` | Select incident |

### Mouse/Button Actions

- **Click incident** in the left sidebar to view details
- **Update Status** button to change incident status
- **Assign** to assign an engineer to the incident
- **Add Note** to add timeline entries
- **Change Severity** to modify severity level
- **Delete Incident** to remove an incident

### Creating an Incident

1. Press `n` or click the "+ New" button
2. Enter a brief title
3. Optionally add a description
4. Select severity level (P1-P4)
5. Optionally assign to an engineer
6. Click "Create Incident"

### Status Workflow

Incidents follow this workflow:
- **Declared** - Initial state when incident is created
- **Investigating** - Team is actively investigating
- **Identified** - Root cause identified
- **Mitigating** - Working on fix/workaround
- **Resolved** - Incident has been resolved

### On-Call Roster

The right panel shows the current on-call team:
- **⭐ Primary** - First responder (primary on-call)
- **👤 Secondary** - Backup responder
- **🚨 Escalation** - Escalation point

## Database

Data is stored in `incidents.db` SQLite database. The database is automatically created on first run.

### Schema

- `incidents` - Main incident table
- `timeline_entries` - Timeline entries for each incident
- `on_call_engineers` - On-call team roster
- `notes` - Additional notes

## Configuration

### Changing Database Location

Modify the `Database` initialization in `app.py`:

```python
self.db = Database("/path/to/custom/db.sqlite")
```

### Custom On-Call Engineers

You can add custom engineers using the UI or by modifying the database directly.

## Troubleshooting

### ImportError: No module named 'textual'

Make sure dependencies are installed:
```bash
pip install -r requirements.txt
```

### Database Locked Error

Ensure only one instance of the app is running.

### Display Issues

The TUI works best in terminals with 256-color support. If display issues occur, try:
- Increasing terminal font size
- Using a different terminal emulator

## Development

### File Structure

```
incident-command-center/
├── app.py           # Main TUI application
├── models.py        # SQLAlchemy models
├── db_manager.py   # Database operations
├── requirements.txt
└── README.md
```

### Adding Custom Features

The application is built using Textual framework. You can extend functionality by:

1. Adding new models in `models.py`
2. Adding new operations in `db_manager.py`
3. Adding new UI components in `app.py`

## License

MIT License - Feel free to use and modify.