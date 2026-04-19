# CertCheck - SSL Certificate Checker CLI

## Project Overview
- **Name**: CertCheck  
- **Type**: Python CLI tool
- **Purpose**: Check SSL/TLS certificate expiration dates for domains

## Features
- Check SSL certificate for any domain:port
- Display certificate details (issuer, subject, validity dates, days remaining)
- Alert when certificates expire within configurable days
- Support multiple domains
- Export results to JSON
- Color-coded output (green=valid, yellow=expiring soon, red=expired)

## File Structure
- certcheck.py (main CLI)
- requirements.txt

## Dependencies
- Python standard library (ssl, socket, datetime, json, argparse)
- colorama for colored output

## CLI Design
```
python certcheck.py check example.com
python certcheck.py check example.com google.com
python certcheck.py watch --days 30
python certcheck.py export --format json
```

## Error Handling
- Connection errors (timeout, refused)
- Certificate parsing errors
- Invalid domain handling
