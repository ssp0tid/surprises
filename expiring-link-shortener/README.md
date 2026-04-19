# Expiring Link Shortener

Clean self-hosted micro utility for creating temporary short links that automatically expire. No database, no login, no tracking, single file.

✅ No database (uses flat JSON file)
✅ Expire links after X hours or X clicks
✅ Clean responsive web interface
✅ One click copy to clipboard
✅ Shows remaining clicks / expiration time
✅ Proper 404 for expired links
✅ Zero external dependencies except Flask
✅ Single file, run directly
✅ No tracking, no login, no accounts

---

## Usage

### Install
```bash
pip install -r requirements.txt
```

### Run
```bash
python3 app.py
```

Or run on custom host/port:
```bash
python3 app.py 0.0.0.0 8080
```

Then open http://localhost:5000 in your browser.

---

## Features

### Creating links
1. Paste any destination URL
2. Choose expiration time (1 hour up to 30 days)
3. Choose maximum click count (1 click up to unlimited)
4. Click create and copy your short link

### Behaviour
- Links are automatically cleaned up when expired
- Remaining clicks are decremented on every access
- Once expired or clicks run out: permanent 404
- All data stored locally in `links.json`
- No external calls, no analytics, no logs

---

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `BASE_URL` | `http://localhost:5000` | Public base URL for generated short links |

Example:
```bash
BASE_URL=https://links.example.com python3 app.py
```

---

## Deployment

### Systemd service
Create `/etc/systemd/system/linkshortener.service`:
```ini
[Unit]
Description=Expiring Link Shortener
After=network.target

[Service]
User=www-data
WorkingDirectory=/opt/linkshortener
Environment=BASE_URL=https://links.yourdomain.com
ExecStart=/usr/bin/python3 app.py 0.0.0.0 8080
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
systemctl daemon-reload
systemctl enable --now linkshortener
```

---

## Limits (configurable in app.py)
- Maximum expiration: 30 days
- Maximum clicks: 1000
- Short code length: 6 characters

---

## License
MIT - Use for anything, modify as you like.
