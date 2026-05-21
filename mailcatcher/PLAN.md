# MailCatcher - Implementation Plan

## 1. Project Overview

**Project Name**: MailCatcher  
**Purpose**: Local SMTP mail catcher server that captures all incoming emails and provides a web dashboard to view rendered emails.  
**Stack**: Python 3.10+, Flask, aiosmtpd, SQLite  

**Ports**:  
- SMTP Server: `1025`  
- Web UI: `8080`

---

## 2. Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        MailCatcher                           │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐  │
│  │    SMTP     │    │    Flask     │    │   Storage    │  │
│  │   Server   │───▶│   App        │◀───│   (SQLite +  │  │
│  │ (aiosmtpd) │    │   (Web UI)   │    │   EML files) │  │
│  └──────────────┘    └──────────────┘    └──────────────┘  │
│       Port 1025          Port 8080                          │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Components

1. **SMTP Server (aiosmtpd)**
   - Async SMTP server running on port 1025
   - Accepts all incoming mail (no authentication)
   - Parses email using Python's `email` module
   - Stores to SQLite + EML file

2. **Flask Web Application**
   - Serves web UI on port 8080
   - Renders email list/detail views
   - Provides REST endpoints for actions

3. **Storage Layer**
   - SQLite: Email metadata, searchable fields
   - Filesystem: Raw EML files for download/backup

---

## 3. Features

| Feature | Description |
|---------|-------------|
| **SMTP Capture** | Listen on port 1025, accept all mail, store with timestamp |
| **Email List View** | Paginated list, shows subject, sender, date, has_attachments flag |
| **Email Detail View** | View full headers, plain text, HTML rendered (with sanitization) |
| **Delete Email** | Delete single or bulk delete from list |
| **Download EML** | Download original .eml file for debugging |
| **Search/Filter** | Filter by subject, sender, date range |
| **Clear All** | Delete all captured emails |

---

## 4. Database Schema (SQLite)

```sql
CREATE TABLE emails (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    message_id TEXT UNIQUE,
    subject TEXT,
    sender TEXT,
    recipients TEXT,  -- JSON array
    date TIMESTAMP,
    received_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    text_body TEXT,
    html_body TEXT,
    headers TEXT,     -- JSON object
    has_attachments INTEGER DEFAULT 0,
    eml_filename TEXT
);

CREATE INDEX idx_emails_received_at ON emails(received_at DESC);
CREATE INDEX idx_emails_sender ON emails(sender);
```

---

## 5. File Structure

```
mailcatcher/
├── app.py                 # Flask application
├── smtp_server.py          # aiosmtpd controller
├── storage.py              # Database + file operations
├── models.py               # Email model class
├── templates/
│   ├── base.html           # Base layout
│   ├── index.html          # Email list
│   ├── detail.html         # Email detail
│   └── email_row.html      # Email row partial
├── static/
│   └── style.css           # Simple styling
├── data/
│   ├── mailcatcher.db      # SQLite database
│   └── emails/             # EML files storage
├── requirements.txt       # Dependencies
└── README.md              # Usage instructions
```

---

## 6. API Endpoints

### Web Routes (HTML)

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

---

## 7. implementation Details

### 7.1 SMTP Server (`smtp.py`)

```python
class MailCatcherController:
    """Handle incoming emails and store them."""

    async def handle_RCPT(self, server, session, envelope, address, rcpt_options):
        envelope.rcpt_tos.append(address)
        return '250 OK'

    async def handle_DATA(self, server, session, envelope):
        # Parse email using email.message_from_bytes
        # Extract headers, body (text/html)
        # Store to database
        return '250 Message accepted for delivery'
```

### 7.2 Running Both Servers

Use threading to run Flask and aiosmtpd together:

```python
def run_smtp():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    server = aiosmtpd.Controller(
        MailCatcherController(),
        hostname='0.0.0.0',
        port=1025
    )
    server.start()
    loop.run_forever()

# In main:
smtp_thread = threading.Thread(target=run_smtp, daemon=True)
smtp_thread.start()
app.run(port=8080)
```

### 7.3 Email Rendering

HTML email content should be sanitized before display:

```python
from bleach import clean

def sanitize_html(html):
    """Sanitize HTML to prevent XSS."""
    allowed_tags = [
        'p', 'br', 'b', 'i', 'u', 'em', 'strong',
        'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
        'ul', 'ol', 'li', 'a', 'img', 'table',
        'tr', 'td', 'th', 'thead', 'tbody'
    ]
    return clean(html, tags=allowed_tags, strip=True)
```

### 7.4 EML Generation

Store original raw email for download:

```python
import email
from email.generator import BytesGenerator
import io

def save_eml(envelope_data, email_id):
    """Save original email data as EML file."""
    msg = email.message_from_bytes(envelope_data)
    filename = f"{email_id}.eml"
    path = Path(DATA_DIR) / 'emails' / filename

    with open(path, 'wb') as f:
        gen = BytesGenerator(f)
        gen.flatten(msg)

    return filename
```

---

## 8. Web UI Design

### Email List View

```
┌─────────────────────────────────────────────────────────────┐
│  MailCatcher                                    [Clear All] │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────────────────────────────────────────���─��────┐  │
│  │ ☐ │ Subject          │ From          │ Date   │ 📎 │   │
│  ├─────────────────────────────────────────────────────────┤  │
│  │ ☐ │ Test email      │ sender@..    │ Now    │ ✓  │   │
│  │ ☐ │ Hello world    │ alice@..    │ 5m ago │    │   │
│  │ ☐ │ Order confirm  │ shop@..    │ 1h ago │ ✓  │   │
│  └─────────────────────────────────────────────────────────┘  │
│                                                             │
│                        [Delete Selected]                    │
│                                                             │
│  ────────────────── Page 1 of 3 ───────────────────────  │
└─────────────────────────────────────────────────────────────┘
```

### Email Detail View

```
┌─────────────────────────────────────────────────────────────┐
│  ← Back                                    [Download .eml] │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Subject: Order Confirmation #12345                          │
│  From: orders@example.com                                     │
│  To: user@example.com                                      │
│  Date: Sun, 19 Apr 2026 10:30:00 +0000                     │
│  ───────────────────────────────────────────────────────   │
│                                                             │
│  ┌─[Plain]─[HTML]──────────────────────────────┐         │
│  │                                                │         │
│  │  Thank you for your order!                      │         │
│  │  Order #12345 has been confirmed...              │         │
│  │                                                │         │
│  └────────────────────────────────────────────────┘         │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 9. Dependencies

```
Flask>=3.0.0
aiosmtpd>=1.4.0
python-email~=content
bleach>=6.0.0
SQLAlchemy>=2.0.0
```

---

## 10. Implementation Order

1. **Phase 1: Foundation**
   - `models.py` - Email model, storage layer
   - `storage.py` - Database operations
   - SQLite schema

2. **Phase 2: SMTP Server**
   - `smtp_server.py` - aiosmtpd controller
   - Email parsing logic
   - EML file storage

3. **Phase 3: Web UI**
   - `app.py` - Flask routes
   - `templates/` - HTML templates
   - `static/` - Styling

4. **Phase 4: Features**
   - Delete functionality
   - Download EML
   - Bulk actions
   - Search/filter

5. **Phase 5: Polish**
   - Error handling
   - Edge cases
   - Documentation

---

## 11. Testing Checklist

- [ ] SMTP accepts mail on port 1025
- [ ] Email stored in database with correct fields
- [ ] EML file saved and valid
- [ ] List view shows emails
- [ ] Detail view renders HTML correctly
- [ ] Plain text alternative displays
- [ ] Delete removes email and EML file
- [ ] Download serves valid EML file
- [ ] Both servers run concurrently
- [ ] No data loss on server restart