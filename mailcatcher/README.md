# MailCatcher

A local SMTP mail catcher server that captures all incoming emails and provides a web dashboard to view rendered emails.

## Features

- **SMTP Server** - Listens on port 1025, accepts all incoming mail (no authentication required)
- **Web Dashboard** - View, search, and filter captured emails on port 8080
- **Email Details** - View headers, plain text, and sanitized HTML content
- **Attachments** - Download original .eml files for debugging
- **Search & Filter** - Filter by subject, sender, and date range
- **Bulk Actions** - Delete individual emails or bulk delete
- **Clear All** - Remove all captured emails at once

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Run the Server

Start both the SMTP server and web UI:

```bash
python app.py
```

Or use the smtp_server module for separate processes:

```bash
# Terminal 1 - Start SMTP server
python -c "from smtp_server import run_smtp; run_smtp()"

# Terminal 2 - Start web UI
python app.py
```

### 3. Access the Web UI

Open your browser to: http://localhost:8080

### 4. Send Test Emails

Send emails to port 1025. Example using Python:

```python
import smtplib
from email.mime.text import MIMEText

msg = MIMEText("Test email body")
msg['Subject'] = "Test Subject"
msg['From'] = "sender@example.com"
msg['To'] = "recipient@example.com"

with smtplib.SMTP('localhost', 1025) as smtp:
    smtp.send_message(msg)
```

Or using mail command:

```bash
echo "Test email body" | mail -s "Test Subject" -S smtp=localhost -S from=sender@example.com recipient@example.com
```

## Configuration

### Ports

- **SMTP Server**: 1025 (configurable in `smtp_server.py`)
- **Web UI**: 8080 (configurable in `app.py`)

### Data Storage

- **Database**: `data/mailcatcher.db` (SQLite)
- **EML Files**: `data/emails/` directory

## API Endpoints

### Web Routes

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Email list (paginated) |
| GET | `/email/<id>` | Email detail view |
| POST | `/email/<id>/delete` | Delete single email |
| POST | `/emails/delete` | Bulk delete |
| GET | `/email/<id>/download` | Download EML file |
| POST | `/emails/clear` | Clear all emails |

### API Routes (JSON)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/emails` | List emails (JSON) |
| GET | `/api/emails/<id>` | Get email (JSON) |

## Development

### Project Structure

```
mailcatcher/
├── app.py                 # Flask application
├── smtp_server.py         # aiosmtpd controller
├── storage.py             # Database operations
├── models.py              # Email model
├── templates/             # HTML templates
│   ├── base.html
│   ├── index.html
│   ├── detail.html
│   └── error.html
├── static/
│   └── style.css          # Styling
├── data/
│   ├── mailcatcher.db     # SQLite database
│   └── emails/            # EML files
├── requirements.txt
└── README.md
```

### Requirements

- Python 3.10+
- Flask >= 3.0.0
- aiosmtpd >= 1.4.0
- bleach >= 6.0.0
- SQLAlchemy >= 2.0.0
- python-dateutil

## Security Notes

- HTML content is sanitized using `bleach` to prevent XSS attacks
- The SMTP server accepts all mail without authentication (local use only)
- No encryption on SMTP or web connections (development use)

## License

MIT