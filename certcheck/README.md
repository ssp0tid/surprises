# CertCheck - SSL Certificate Checker CLI

A Python CLI tool for checking SSL/TLS certificate expiration dates for domains.

## Features

- Check SSL certificate for any domain:port
- Display certificate details (issuer, subject, validity dates, days remaining)
- Color-coded output (green=valid, yellow=expiring soon, red=expired)
- Alert when certificates expire within configurable days
- Support multiple domains in one command
- Export results to JSON

## Installation

```bash
cd ~/projects/surprises/certcheck
chmod +x certcheck.py
```

## Usage

### Check single domain

```bash
python certcheck.py example.com
```

### Check multiple domains

```bash
python certcheck.py example.com google.com github.com
```

### Custom port

```bash
python certcheck.py example.com -p 8443
```

### Warning threshold

```bash
# Warn if certificate expires within 14 days
python certcheck.py example.com -w 14
```

### Export to JSON

```bash
python certcheck.py example.com -o results.json
```

## Example Output

```
V google.com:443
  Issuer: Google Trust Services
  Subject: *.google.com
  Valid: Mar 30 08:35:08 2026 GMT to Jun 22 08:35:07 2026 GMT
  65 days remaining

V github.com:443
  Issuer: Sectigo Limited
  Subject: github.com
  Valid: Mar  6 00:00:00 2026 GMT to Jun  3 23:59:59 2026 GMT
  46 days remaining

X nonexistent.example.com:443 - DNS error
```

## Requirements

- Python 3.7+
- No external dependencies (uses standard library only)

## License

MIT
