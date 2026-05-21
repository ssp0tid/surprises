# Local-CA Implementation Plan

## Project Overview
- **Project Name**: local-ca
- **Type**: Self-hosted Certificate Authority Management Tool
- **Core Features**: CA management, TLS certificate generation, CSR signing, multi-format export, CLI + Web UI
- **Tech Stack**: Python 3, Flask, SQLite, OpenSSL (cryptography library)

## Architecture

### Directory Structure
```
local-ca/
├── local_ca/
│   ├── __init__.py
│   ├── cli.py              # CLI interface
│   ├── web.py              # Flask web dashboard
│   ├── database.py         # SQLite models and operations
│   ├── crypto_utils.py     # Cryptographic operations
│   ├── cert_manager.py    # Certificate management logic
│   ├── validators.py      # Input validation
│   └── templates/         # Flask templates
│       ├── base.html
│       ├── index.html
│       ├── ca_detail.html
│       ├── cert_detail.html
│       └── create_cert.html
├── data/                  # SQLite database and certs storage
├── local_ca.egg-info/
├── setup.py
├── requirements.txt
├── README.md
└── PLAN.md
```

### Database Schema (SQLite)
```sql
-- Certificate Authorities table
CREATE TABLE cas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    type TEXT NOT NULL CHECK(type IN ('root', 'intermediate')),
    parent_id INTEGER REFERENCES cas(id),
    serial_number TEXT NOT NULL,
    subject TEXT NOT NULL,
    issuer TEXT NOT NULL,
    not_before INTEGER NOT NULL,
    not_after INTEGER NOT NULL,
    key_usage TEXT,
    ext_key_usage TEXT,
    is_ca BOOLEAN DEFAULT 1,
   created_at INTEGER NOT NULL,
    updated_at INTEGER NOT NULL,
    is_active BOOLEAN DEFAULT 1
);

-- Certificates table
CREATE TABLE certificates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ca_id INTEGER NOT NULL REFERENCES cas(id),
    name TEXT NOT NULL,
    common_name TEXT NOT NULL,
    subject TEXT NOT NULL,
    serial_number TEXT NOT NULL,
    not_before INTEGER NOT NULL,
    not_after INTEGER NOT NULL,
    key_usage TEXT,
    ext_key_usage TEXT,
    san TEXT,
    created_at INTEGER NOT NULL,
    is_active BOOLEAN DEFAULT 1
);

-- CSR table
CREATE TABLE csrs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    csr_data TEXT NOT NULL,
    created_at INTEGER NOT NULL
);
```

## Implementation Steps

### Step 1: Core Configuration & Dependencies
- Create requirements.txt with all dependencies
- Create setup.py for package installation
- Define Python package structure

### Step 2: Crypto Utilities (crypto_utils.py)
- RSA key generation
- X.509 certificate creation
- Certificate signing
- PEM/DER encoding
- Key parsing and validation

### Step 3: Database Layer (database.py)
- SQLite connection management
- CRUD operations for CAs, certificates, CSRs
- Migrations/init database

### Step 4: Certificate Manager (cert_manager.py)
- Root CA creation
- Intermediate CA creation (signed by root)
- End-entity certificate generation
- CSR signing functionality
- Certificate chain management
- Export to PEM, P12, JKS formats

### Step 5: Validators (validators.py)
- Input validation for all CLI commands
- Certificate subject validation
- Date validation
- Format validation

### Step 6: CLI Interface (cli.py)
Commands:
- `local-ca init` - Initialize database
- `local-ca ca create` - Create root/intermediate CA
- `local-ca ca list` - List all CAs
- `local-ca ca show <id>` - Show CA details
- `local-ca cert create` - Create TLS certificate
- `local-ca cert list` - List certificates
- `local-ca cert show <id>` - Show certificate details
- `local-ca csr sign` - Sign a CSR
- `local-ca export` - Export in various formats
- `local-ca web` - Start web dashboard

### Step 7: Web Dashboard (web.py)
Routes:
- `/` - Dashboard home
- `/ca` - List CAs
- `/ca/<id>` - CA detail
- `/ca/create` - Create new CA
- `/cert` - List certificates
- `/cert/create` - Create new certificate
- `/cert/<id>` - Certificate detail
- `/csr` - List/sign CSRs
- `/export` - Export interface

### Step 8: Templates
- Bootstrap-styled responsive UI
- Certificate management forms
- Status displays

### Step 9: README.md
- Installation instructions
- Usage examples
- CLI reference
- Web interface guide

## Key Features Detail

### 1. Root CA Creation
- Generate 4096-bit RSA key (or configurable)
- Self-signed X.509 certificate
- 10-year validity (configurable)
- Basic constraints: CA=TRUE
- Key usage: keyCertSign, crlSign

### 2. Intermediate CA Creation
- Generate 4096-bit RSA key
- Signed by root CA
- 5-year validity
- CA=TRUE
- Can sign other intermediate or end-entity certs

### 3. TLS Certificate Generation
- Generate 2048-bit RSA key
- SAN support (DNS, IP, Email)
- Signed by selected CA
- Configurable validity
- Key usage: digitalSignature, keyEncipherment
- Extended key usage: serverAuth, clientAuth

### 4. CSR Signing
- Accept PEM-encoded CSR
- Sign using specified CA
- Return signed certificate

### 5. Export Formats
- **PEM**: Traditional PEM bundle (cert + key)
- **P12/PFX**: PKCS#12 for Windows/Java
- **JKS**: Java KeyStore (requires keytool or custom impl)

## Error Handling
- Input validation errors provide clear messages
- Cryptographic errors handled gracefully
- Database errors with rollback support
- File permission errors
- Certificate expiry warnings

## Testing Checklist
- [ ] Root CA creation and verification
- [ ] Intermediate CA creation chain validation
- [ ] TLS certificate generation with SAN
- [ ] CSR signing workflow
- [ ] All export formats functional
- [ ] CLI commands responsive
- [ ] Web dashboard functional
- [ ] Database persistence
- [ ] Error scenarios handled