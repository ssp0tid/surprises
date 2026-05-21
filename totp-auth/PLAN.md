# TOTP-Auth Implementation Plan

## 1. Overview

**Project Name:** totp-auth
**Type:** CLI TOTP/HOTP Authenticator
**Core Functionality:** Generate 2FA codes, manage accounts with encrypted local storage
**Target Users:** Developers, security-conscious users who prefer CLI over mobile apps

---

## 2. File Structure

```
totp-auth/
├── totpauth/
│   ├── __init__.py          # Package init
│   ├── __main__.py          # Entry point: totp-auth [...]
│   ├── cli.py               # CLI command parsing & dispatch
│   ├── commands/
│   │   ├── __init__.py
│   │   ├── add.py           # Add account (manual/QR)
│   │   ├── list.py          # List accounts
│   │   ├── generate.py      # Generate HOTP/TOTP code
│   │   ├── copy.py          # Copy code to clipboard
│   │   └── delete.py        # Delete account
│   ├── core/
│   │   ├── __init__.py
│   │   ├── otp.py           # HOTP/TOTP generation (pyotp wrapper)
│   │   ├── qr.py            # QR code parsing
│   │   └── crypto.py        # Encryption/decryption (cryptography)
│   ├── storage/
│   │   ├── __init__.py
│   │   └── store.py         # Encrypted JSON storage
│   ├── models/
│   │   ├── __init__.py
│   │   └── account.py       # Account dataclass
│   └── exceptions.py       # Custom exceptions
├── tests/
│   ├── __init__.py
│   ├── test_commands.py
│   ├── test_core.py
│   ├── test_storage.py
│   └── fixtures/
│       ├── valid_totp.png
│       ├── valid_hotp.png
│       └── encrypted_store.json.enc
├── scripts/
│   └── demo_gen.sh         # Demo script
├── config.yaml             # Optional config
├── pyproject.toml          # Project metadata & deps
└── README.md               # User-facing docs
```

---

## 3. Dependencies

### Runtime
| Package | Purpose | Version |
|---------|---------|---------|
| `pyotp` | HOTP/TOTP generation | `>=2.9.0` |
| `qrcode` | QR code generation | `>=7.4.2` |
| `Pillow` | Image processing for QR | `>=10.0.0` |
| `cryptography` | AES encryption | `>=41.0.0` |
| `click` | CLI framework | `>=8.1.0` |
| `pyperclip` | Clipboard access | `>=1.8.0` |

### Dev/Testing
| Package | Purpose |
|---------|---------|
| `pytest` | Testing framework |
| `pytest-cov` | Coverage reporting |
| `pytest-mock` | Mocking for tests |
| `hypothesis` | Property-based testing |

---

## 4. Data Model

### Account Schema
```python
@dataclass
class Account:
    issuer: str           # Service name (e.g., "GitHub", "Google")
    account_name: str     # User identifier (e.g., "user@example.com")
    secret: str          # Base32-encoded secret
    otp_type: str        # "totp" or "hotp"
    algorithm: str       # "SHA1", "SHA256", "SHA512" (default: "SHA1")
    digits: int          # 6 or 8 (default: 6)
    period: int          # Time step in seconds (default: 30)
    counter: int         # HOTP counter (default: 0)
    created_at: datetime # Auto-set on creation
    updated_at: datetime # Auto-set on update

    # Computed from issuer + account_name
    @property
    def id(self) -> str:
        return hashlib.sha256(f"{self.issuer}:{self.account_name}".encode()).hexdigest()[:16]
```

### Storage File Format
- **Location:** `~/.local/share/totp-auth/accounts.enc`
- **Format:** AES-256-GCM encrypted JSON
- **Structure:**
```json
{
  "version": 1,
  "accounts": [
    {
      "id": "a1b2c3d4e5f6",
      "issuer": "GitHub",
      "account_name": "dev@example.com",
      "secret": "JBSWY3DPEHPK3PXP",
      "otp_type": "totp",
      "algorithm": "SHA1",
      "digits": 6,
      "period": 30,
      "counter": 0,
      "created_at": "2024-01-15T10:30:00Z",
      "updated_at": "2024-01-15T10:30:00Z"
    }
  ],
  "salt": "<32-byte-random-hex>"
}
```

---

## 5. CLI API Design

### Command Structure
```
totp-auth [OPTIONS] COMMAND [ARGS]...
```

### Global Options
| Option | Description |
|--------|-------------|
| `-v, --verbose` | Enable verbose output |
| `-c, --config PATH` | Custom config file path |
| `--version` | Show version and exit |
| `--help` | Show help and exit |

### Commands

#### 1. `add` - Add New Account
```
totp-auth add [OPTIONS]
  --manual                    Manual secret entry (interactive)
  --issuer TEXT               Service issuer (e.g., GitHub)
  --account TEXT              Account name/email
  --secret TEXT              Base32 secret (required for --manual)
  --totp | --hotp            OTP type (default: totp)
  --algorithm SHA1|SHA256|SHA512  Algorithm (default: SHA1)
  --digits 6|8               Digit count (default: 6)
  --period SECONDS           TOTP period (default: 30)
  -y, --yes                  Skip confirmation

totp-auth add --qr <screenshot.png>
totp-auth add --manual --issuer GitHub --account me@email.com --secret JBSWY3DPEHPK3PXP
```

**QR Code Parsing:**
- Accept PNG/JPG screenshot via `--qr` flag
- Use `PIL` to load image, `qrcode` to decode
- Parse otpauth:// URI format:
  ```
  otpauth://totp/Example:user@example.com?secret=JBSWY3DPEHPK3PXP&issuer=Example&algorithm=SHA1&digits=6&period=30
  otpauth://hotp/Example:user@example.com?secret=JBSWY3DPEHPK3PXP&counter=0
  ```

#### 2. `list` - List Accounts
```
totp-auth list [OPTIONS]
  -f, --format table|json|plain  Output format (default: table)
  -q, --quiet                   Show only codes, no labels
```

**Output Examples:**
```
table:
┌──────────┬─────────────────────┬──────────┐
│ Issuer   │ Account              │ Code     │
├──────────┼─────────────────────┼──────────┤
│ GitHub   │ dev@example.com     │ 123456   │
│ Google   │ me@gmail.com        │ 789012   │
└──────────┴─────────────────────┴──────────┘

json:
[{"issuer":"GitHub","account":"dev@example.com","code":"123456"}]

plain:
GitHub:dev@example.com:123456
```

#### 3. `generate` - Generate Code
```
totp-auth generate [OPTIONS] [ID_OR_ISSUER]
  -c, --clipboard            Copy to clipboard
  -q, --quiet               Print code only
  -w, --watch               Watch mode (auto-refresh)
```

**Examples:**
```
totp-auth generate github:me@email.com    # Generate for specific account
totp-auth generate github               # Generate for first match
totp-auth generate -c                   # Interactive selection then copy
totp-auth generate -w                    # Watch mode (updates every period)
```

#### 4. `copy` - Copy Code to Clipboard
```
totp-auth copy [OPTIONS] [ID_OR_ISSUER]
  -c, --clipboard            (alias for copy command)
  -t, --timeout SECONDS      Clear clipboard after N seconds (default: 30)
```

#### 5. `delete` - Delete Account
```
totp-auth delete [OPTIONS] ID_OR_ISSUER
  -f, --force                Skip confirmation
```

---

## 6. Encryption Design

### Algorithm: AES-256-GCM
- **Key Derivation:** PBKDF2-HMAC-SHA256
- **Salt:** 32 bytes random (stored in file)
- **Iterations:** 480,000 (OWASP recommended for 2024)
- **IV:** 12 bytes random per encryption

### Master Password Flow
1. On first run, prompt user to set master password
2. Derive encryption key from password + salt
3. Store salt in encrypted file header
4. Key is held in memory for session lifetime
5. Optional: auto-lock after N minutes of inactivity

### Encryption API
```python
class CryptoManager:
    def __init__(self, password: str, salt: Optional[bytes] = None):
        self.key = self.derive_key(password, salt)

    def derive_key(self, password: str, salt: bytes) -> bytes:
        # PBKDF2-HMAC-SHA256, 480k iterations
        pass

    def encrypt(self, data: bytes) -> tuple[bytes, bytes]:
        # Returns (ciphertext, nonce)
        pass

    def decrypt(self, ciphertext: bytes, nonce: bytes) -> bytes:
        pass

    @classmethod
    def generate_salt(cls) -> bytes:
        # 32 bytes secure random
        pass
```

---

## 7. Error Handling

### Exception Hierarchy
```
TotpAuthError (base)
├── AccountNotFoundError
├── DuplicateAccountError
├── InvalidSecretError
├── InvalidQRCodeError
│   ├── QRDecodeError
│   ├── InvalidOtpAuthURLError
├── EncryptionError
│   ├── InvalidPasswordError
│   ├── CorruptedDataError
├── ClipboardError
└── CLIError
    ├── InvalidArgumentError
    └── MissingArgumentError
```

### Error Handling Strategy
1. **User-friendly messages:** No stack traces for common errors
2. **Exit codes:**
   - `0`: Success
   - `1`: General error
   - `2`: Invalid arguments
   - `3`: Account not found
   - `4`: Encryption/auth failure
3. **Verbose mode:** Show full traceback only with `-v`
4. **Recovery:** Provide actionable suggestions

### Examples
```
$ totp-auth generate nonexistent
Error: Account 'nonexistent' not found.
Run 'totp-auth list' to see available accounts.

$ totp-auth add --manual --secret INVALID
Error: Invalid secret 'INVALID'.
Secrets must be Base32-encoded (A-Z, 2-7).

$ totp-auth add --qr broken.png
Error: No QR code found in image.
Ensure the QR code is clearly visible and not damaged.
```

---

## 8. Implementation Priorities

### Phase 1: Core CLI & Storage (MVP)
- [ ] CLI framework with `click`
- [ ] Encrypted JSON storage
- [ ] `add --manual` command
- [ ] `list` command
- [ ] `generate` command and basic TOTP support
- [ ] Basic error handling

### Phase 2: QR & Extended Features
- [ ] QR code scanning from screenshots
- [ ] HOTP support
- [ ] Copy to clipboard with auto-clear
- [ ] `--watch` mode
- [ ] Delete command

### Phase 3: Polish
- [ ] Configuration file support
- [ ] Auto-lock timeout
- [ ] Multiple accounts with same issuer
- [ ] Export/import functionality
- [ ] Comprehensive tests

---

## 9. Key Implementation Notes

### QR Code parsing with PIL + qrcode
```python
from PIL import Image
import qrcode

def parse_qr_screenshot(path: str) -> str:
    img = Image.open(path)
    # Convert to grayscale for better recognition
    if img.mode != 'L':
        img = img.convert('L')

    # Use zbar for better compatibility, fallback to qrcode
    try:
        result = zbar.scan_codes(img)
        if result:
            return result[0].decode('utf-8')
    except Exception:
        pass

    # Fallback to pyzbar
    from pyzbar import pyzbar
    decoded = pyzbar.decode(img)
    if decoded:
        return decoded[0].data.decode('utf-8')

    raise InvalidQRCodeError("No QR code found in image")
```

### pyotp Integration
```python
import pyotp

def generate_totp(secret: str, digits: int = 6, period: int = 30) -> str:
    totp = pyotp.TOTP(secret, digits=digits, interval=period)
    return totp.now()

def generate_hotp(secret: str, counter: int, digits: int = 6) -> str:
    hotp = pyotp.HOTP(secret, digits=digits)
    return hotp.at(counter)
```

### Clipboard with pyperclip
```python
import pyperclip
import threading

def copy_with_timeout(text: str, timeout: int = 30):
    pyperclip.copy(text)

    def clear_clipboard():
        pyperclip.copy("")
        # Or restore previous content

    timer = threading.Timer(timeout, clear_clipboard)
    timer.start()
```

---

## 10. Testing Strategy

### Test Coverage Targets
- Core OTP generation: 100%
- Encryption/decryption: 100%
- Storage read/write: 100%
- CLI commands: 80%+

### Test Fixtures
- Valid TOTP QR screenshot
- Valid HOTP QR screenshot
- Encrypted store with known password
- Various invalid inputs

---

## 11. Future Considerations (Out of Scope)

- Cloud sync / encrypted backup
- TOTP QR generation (display on screen)
- Mobile companion app
- Desktop notifications for code expiry
- YubiKey / hardware token support