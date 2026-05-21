# Local CA - Self-hosted Certificate Authority Management Tool

A comprehensive self-hosted Certificate Authority (CA) management tool for generating and managing TLS certificates for local development. Features a CLI interface and web dashboard.

## Features

- **Root CA Creation**: Create self-signed root certificate authorities
- **Intermediate CA**: Create intermediate CAs signed by root CAs
- **TLS Certificates**: Generate TLS/SSL certificates for local development
- **CSR Signing**: Sign Certificate Signing Requests from external tools
- **Multiple Export Formats**: Export as PEM, P12/PKCS12
- **CLI Interface**: Full command-line interface for all operations
- **Web Dashboard**: Flask-based web UI for certificate management

## Installation

### Prerequisites

- Python 3.9 or higher
- OpenSSL (included with Python cryptography package)

### Install Steps

1. Navigate to the project directory:
```bash
cd /home/max/projects/surprises/local-ca
```

2. Create and activate a virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Install the package:
```bash
pip install -e .
```

## Quick Start

### 1. Initialize the database

```bash
local-ca init
```

This creates the SQLite database and certificates directory.

### 2. Create a Root CA

```bash
local-ca ca create --name my-root-ca --common-name "My Local Root CA" --validity-years 10
```

### 3. Create TLS Certificates

```bash
local-ca cert create --name localhost-cert --common-name localhost --ca-id 1 --san localhost,127.0.0.1
```

### 4. Start the Web Dashboard

```bash
local-ca web
```

Then open http://127.0.0.1:5000 in your browser.

## CLI Commands Reference

### Initialization

```bash
local-ca init                  # Initialize database
```

### CA Management

```bash
local-ca ca create --name <name> --common-name <CN> [options]
                           # Create a new CA
    --type [root|intermediate]  CA type (default: root)
    --parent-id <id>             Parent CA ID (for intermediate)
    --country <code>            Country code (2 letters)
    --state <state>             State/province
    --locality <city>          City
    --organization <org>        Organization
    --validity-years <years>    Validity in years (default: 10)
    --key-size <bits>           Key size (default: 4096)

local-ca ca list              # List all CAs
local-ca ca show <id>         # Show CA details
local-ca ca delete <id>      # Delete a CA
```

### Certificate Management

```bash
local-ca cert create --name <name> --common-name <CN> --ca-id <id> [options]
                           # Create a TLS certificate
    --country <code>            Country code
    --state <state>             State/province
    --locality <city>           City
    --organization <org>         Organization
    --email <email>             Email
    --san <name>...           Subject Alternative Names (repeatable)
    --validity-years <years>    Valid in years (default: 1)
    --key-size <bits>          Key size (default: 2048)

local-ca cert list            # List certificates
local-ca cert show <id>       # Show certificate details
local-ca cert delete <id>      # Delete a certificate
local-ca cert export <id> --output <file> --format [pem|p12]
                           # Export certificate
```

### CSR Management

```bash
local-ca csr sign --csr-file <file> --ca-id <id> --name <name> [options]
                           # Sign a CSR
    --validity-years <years>  Validity in years

local-ca csr list             # List CSRs
local-ca csr delete <id>     # Delete a CSR
```

### Web Dashboard

```bash
local-ca web [--host <host>] [--port <port>] [--debug]
```

## Web Dashboard

The web dashboard provides a graphical interface for all operations:

- **Dashboard**: Overview of CAs and certificates
- **CAs**: Create and manage certificate authorities
- **Certificates**: Generate and manage TLS certificates
- **CSRs**: Upload and sign CSR files
- **Export**: Download certificates in various formats

Start the web server:
```bash
local-ca web
```

Default URL: http://127.0.0.1:5000

## Using Certificates

### With Nginx

```nginx
server {
    server_name localhost;
    listen 443 ssl;
    
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/cert-key.pem;
}
```

### With Apache

```apache
SSLEngine on
SSLCertificateFile /path/to/cert.pem
SSLCertificateKeyFile /path/to/cert-key.pem
```

### With Node.js

```javascript
const https = require('https');
const fs = require('fs');

const options = {
    cert: fs.readFileSync('cert.pem'),
    key: fs.readFileSync('cert-key.pem')
};

https.createServer(options, app).listen(443);
```

### With Java/KeyStore

Export to P12 format:
```bash
local-ca cert export 1 --output cert.p12 --format p12 --passphrase changeit
```

Then import to a KeyStore:
```bash
keytool -importkeystore -srckeystore cert.p12 -srcstoretype PKCS12 -destkeystore keystore.jks
```

## Configuration

### Database Location

The SQLite database is stored at:
```
data/local-ca.db
```

### Certificates Location

Generated certificates and keys are stored at:
```
data/certs/
```

## Security Notes

- **Private Key Protection**: Private keys are stored with read permissions (600)
- **Passphrases**: Use passphrases for production certificates
- **Key Sizes**: Use 4096-bit keys for CAs, 2048-bit for certificates
- **Validity**: Keep certificate validity short for development

## Troubleshooting

### Certificate not trusted

For local development, you'll need to add the root CA to your system's trusted roots. On macOS:
```bash
sudo security add-trusted-cert -d -r trustRoot /path/to/root-ca.pem
```

On Windows:
```bash
certutil -addstore "Root" root-ca.pem
```

### Verify certificate

```bash
openssl verify -CAfile root-ca.pem cert.pem
```

### View certificate details

```bash
openssl x509 -in cert.pem -text -noout
```

## Development

### Running Tests

```bash
python -m pytest
```

### Project Structure

```
local-ca/
├── local_ca/
│   ├── __init__.py
│   ├── cli.py              # CLI interface
│   ├── web.py             # Flask web dashboard
│   ├── database.py        # SQLite operations
│   ├── crypto_utils.py   # Cryptographic functions
│   ├── cert_manager.py   # Certificate management
│   ├── validators.py     # Input validation
│   └── templates/       # Flask templates
├── data/                 # Database and certificates
├── requirements.txt
├── setup.py
└── README.md
```

## License

MIT License