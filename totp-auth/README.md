# TOTP-Auth

CLI TOTP/HOTP Authenticator with encrypted storage.

## Installation

```bash
pip install totp-auth
```

Or install from source:

```bash
cd totp-auth
pip install -e .
```

## First Run

On first run, you'll be prompted to set a master password:

```bash
$ totp-auth list
First run: set your master password
Set master password: ********
Confirm password: ********
```

This password encrypts your accounts stored at `~/.local/share/totp-auth/accounts.enc`.

## Usage

### Add Account

Add an account manually:

```bash
totp-auth add --manual --issuer GitHub --account me@example.com --secret JBSWY3DPEHPK3PXP
```

Or from QR code screenshot:

```bash
totp-auth add --qr screenshot.png
```

### List Accounts

```bash
$ totp-auth list
┌──────────┬─────────────────────┬──────────┐
│ Issuer   │ Account              │ Code     │
├──────────┼─────────────────────┼──────────┤
│ GitHub   │ me@example.com     │ 123456   │
└──────────┴─────────────────────┴──────────┘
```

JSON format:

```bash
totp-auth list -f json
```

Plain format:

```bash
totp-auth list -f plain
```

### Generate Code

Generate for specific account:

```bash
totp-auth generate github
```

Copy to clipboard:

```bash
totp-auth generate -c
```

Watch mode (auto-refresh):

```bash
totp-auth generate -w
```

Quiet mode (code only):

```bash
totp-auth generate -q
```

### Delete Account

```bash
totp-auth delete github
```

With confirmation skip:

```bash
totp-auth delete github -f
```

## Options

Global options:

- `-v, --verbose`: Enable verbose output
- `-c, --config PATH`: Custom config file path
- `--version`: Show version

## Exit Codes

- `0`: Success
- `1`: General error
- `2`: Invalid arguments
- `3`: Account not found
- `4`: Encryption/auth failure

## Security

- AES-256-GCM encryption
- PBKDF2-HMAC-SHA256 key derivation (480,000 iterations)
- Master password required to unlock accounts

## Requirements

- Python 3.9+
- pyotp
- cryptography
- click
- pyperclip
- Pillow
- qrcode
- pyzbar