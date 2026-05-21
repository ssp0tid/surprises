# Termail - Textual TUI Email Client

A simple terminal-based email client written in Python using the Textual framework.

## Features

- **IMAP Inbox List**: View emails with subjects, senders, and dates
- **Email Detail View**: Read full email content
- **Compose & Send**: Send emails via SMTP
- **Folder Management**: INBOX, Sent, Drafts, Trash support
- **Search**: Simple search across emails

## Requirements

- Python 3.8+
- Textual library

## Installation

1. Install the required package:

```bash
pip install -r requirements.txt
```

Or directly:

```bash
pip install textual
```

## Configuration

Before using Termail, you need to configure your email account.

1. Run the application:

```bash
cd /home/max/projects/surprises/termail
python app.py
```

2. Press `c` to open the configuration screen, or use the Config button.

3. Enter your email settings:

| Field | Description |
|-------|-------------|
| IMAP Server | Your IMAP server (e.g., imap.gmail.com) |
| IMAP Port | IMAP port (default: 993 for SSL) |
| SMTP Server | Your SMTP server (e.g., smtp.gmail.com) |
| SMTP Port | SMTP port (default: 587 for TLS) |
| Username | Your email address or username |
| Password | Your email password |
| Display Name | Your display name |

4. Click "Save" to save your configuration.

## Usage

### Keyboard Shortcuts

| Key | Action |
|-----|--------|
| `n` | Compose new email |
| `r` | Reply to selected email |
| `d` | Delete selected email |
| `f` | Search emails |
| `c` | Open configuration |
| `q` | Quit application |
| `Escape` | Go back / Close screen |

### Mouse/Button Actions

- **Compose**: Open new email composer
- **Reply**: Reply to selected email
- **Delete**: Move selected email to Trash
- **Search**: Search emails
- **Config**: Open configuration screen

### Navigation

- Use **Up/Down** arrows or click to select folders/emails
- Click on an email to view its contents

## Email Provider Settings

### Gmail
- IMAP Server: `imap.gmail.com`
- IMAP Port: `993` (SSL)
- SMTP Server: `smtp.gmail.com`
- SMTP Port: `587` (TLS)
- Enable "Less secure apps" or use App Password

### Outlook/Hotmail
- IMAP Server: `outlook.office365.com`
- IMAP Port: `993` (SSL)
- SMTP Server: `smtp.office365.com`
- SMTP Port: `587` (TLS)

### Yahoo Mail
- IMAP Server: `imap.mail.yahoo.com`
- IMAP Port: `993` (SSL)
- SMTP Server: `smtp.mail.yahoo.com`
- SMTP Port: `587` (TLS)

## Files

```
termail/
├── app.py           # Main application
├── config.py        # Configuration management
├── imap_client.py   # IMAP client
├── smtp_client.py   # SMTP client
├── requirements.txt # Python dependencies
├── config.json     # Saved configuration (created after first run)
└── README.md       # This file
```

## Security Note

Your password is stored in plain text in `config.json`. For production use, consider:
- Using app-specific passwords
- Using OAuth2 authentication
- Implementing encrypted password storage

## License

This is a simple demonstration project.