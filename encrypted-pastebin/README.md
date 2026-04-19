# Encrypted Pastebin

A secure, self-hosted pastebin service with end-to-end encryption using AES-GCM.

## Features

- **End-to-end encryption** - Content is encrypted server-side using AES-256-GCM
- **Optional password protection** - Add an additional layer of security with a password
- **Burn after reading** - Delete paste after first view
- **Expiration** - Set paste to expire after 1 hour, 1 day, or never
- **Dark theme** - Clean, modern dark interface

## Setup

### Prerequisites

- Python 3.9+

### Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd encrypted-pastebin
   ```

2. Create a virtual environment (optional but recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. (Optional) Set a secret key:
   ```bash
   export SECRET_KEY=$(python -c "import secrets; print(secrets.token_hex(32))")
   ```

5. Run the application:
   ```bash
   python app.py
   ```

6. Open your browser at `http://localhost:5000`

## Security

- **Encryption**: AES-256-GCM via `cryptography` library
- **Key Derivation**: PBKDF2-HMAC-SHA256 with 600,000 iterations
- **Salt/Nonce**: 32-byte salt, 12-byte nonce, generated using `os.urandom`

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Main paste creation form |
| `/create` | POST | Create new encrypted paste |
| `/view/<id>` | GET | View decrypted paste |
| `/verify/<id>` | POST | Verify password for protected paste |
| `/raw/<id>` | GET | View paste as raw text |
| `/error` | - | Error page template |

## License

MIT