# Secret Vault - Implementation Plan

**Project:** Secure Local Secrets Manager with AES-256-GCM  
**Approach:** TDD-Oriented with Atomic Commits  
**Language:** Go (recommended for crypto + CLI)

---

## 1. Project Overview

Secret Vault is an offline-first CLI tool for managing local secrets using AES-256-GCM authenticated encryption. Core features include:
- AES-256-GCM with 96-bit random nonces
- Argon2id key derivation (OWASP 2023 parameters)
- Master password protection with secure memory handling
- Clipboard integration with auto-clear
- Single portable encrypted vault file

---

## 2. Architecture

```
CLI Layer → Business Logic → Crypto/Storage → Encrypted Vault File
```

**Security Model:**
- Key derived from password via Argon2id (32-byte salt, 3 iterations, 64MB memory)
- Each secret encrypted with unique nonce
- GCM auth tag prevents tampering
- Memory zeroed after crypto operations

---

## 3. Implementation Phases (20 Commits)

| Phase | Focus | Key Files |
|-------|-------|-----------|
| 1 (5 commits) | Foundation | `internal/crypto/`, `internal/vault/types.go`, `storage.go` |
| 2 (5 commits) | Core CLI | `cmd/add.go`, `get.go`, `list.go`, `delete.go`, `update.go` |
| 3 (5 commits) | Advanced | `export.go`, `import.go`, `search.go`, `group.go`, `backup.go` |
| 4 (5 commits) | Hardening | Timing mitigation, memory locking, integration tests |

---

## 4. File Structure

```
secret-vault/
├── cmd/                    # Cobra CLI commands
│   ├── init.go
│   ├── add.go
│   ├── get.go
│   ├── list.go
│   ├── delete.go
│   ├── update.go
│   ├── export.go
│   └── import.go
├── internal/
│   ├── crypto/
│   │   ├── crypto.go       # AES-256-GCM encrypt/decrypt
│   │   ├── kdf.go          # Argon2id key derivation
│   │   └── memory.go       # Secure memory handling
│   ├── vault/
│   │   ├── types.go        # Vault, Secret types
│   │   ├── storage.go      # Load/save vault file
│   │   └── search.go       # Search functionality
│   └── config/
│       └── config.go       # Configuration
├── tests/
│   ├── unit/
│   │   ├── crypto_test.go
│   │   ├── vault_test.go
│   │   └── kdf_test.go
│   └── integration/
│       └── e2e_test.go
├── main.go
├── go.mod
├── go.sum
└── Makefile
```

---

## 5. Key Technical Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Encryption | AES-256-GCM | NIST-approved, authenticated |
| KDF | Argon2id | OWASP winner, memory-hard |
| Storage | JSON + encrypted blobs | Human-readable, versionable |
| CLI | Cobra + Viper | Battle-tested, composable |
| Password input | `golang.org/x/term` | Cross-platform, masked |
| Nonce size | 96-bit (12 bytes) | GCM recommended |
| Salt size | 32 bytes | Minimum 16, prefer 32 |
| Key size | 256 bits (32 bytes) | Full AES-256 |

---

## 6. Key Derivation Parameters (Argon2id)

```go
Params := &argon2.Params{
    Memory:      64 * 1024, // 64 MB
    Iterations: 3,
    Parallelism: 4,
    SaltLen:    32,
    KeyLen:     32,
}
```

---

## 7. Data Structures

### Vault File Format (JSON)
```json
{
  "version": "1.0",
  "created": "2026-04-19T00:00:00Z",
  "modified": "2026-04-19T00:00:00Z",
  "kdf_salt": "base64-encoded-salt",
  "secrets": [
    {
      "key": "api_key_prod",
      "nonce": "base64-encoded-nonce",
      "ciphertext": "base64-encoded-encrypted-value",
      "created": "2026-04-19T00:00:00Z",
      "modified": "2026-04-19T00:00:00Z"
    }
  ]
}
```

### Secret Type
```go
type Secret struct {
    Key         string    `json:"key"`
    Nonce       string   `json:"nonce"`       // Base64
    Ciphertext  string   `json:"ciphertext"`  // Base64
    Created     time.Time`json:"created"`
    Modified    time.Time`json:"modified"`
}

type Vault struct {
    Version    string    `json:"version"`
    Created    time.Time `json:"created"`
    Modified   time.Time`json:"modified"`
    KDFSalt    string   `json:"kdf_salt"`    // Base64
    Secrets   []Secret  `json:"secrets"`
}
```

---

## 8. CLI Commands

| Command | Purpose | Example |
|---------|---------|---------|
| `vault init` | Create new vault | `vault init` |
| `vault add <key>` | Add secret | `vault add aws_credentials` |
| `vault get <key>` | Retrieve (masked) | `vault get aws_credentials` |
| `vault get <key> -f` | Reveal secret | `vault get aws_credentials -f` |
| `vault list` | List all keys | `vault list` |
| `vault delete <key>` | Remove secret | `vault delete aws_credentials` |
| `vault update <key>` | Modify secret | `vault update aws_credentials` |
| `vault export` | Export to file | `vault export backup.enc` |
| `vault import` | Import from file | `vault import backup.enc` |

### CLI Flags
| Flag | Purpose |
|------|---------|
| `-f, --reveal` | Show secret value (default: hidden) |
| `-c, --clipboard` | Copy to clipboard (auto-clears in 30s) |
| `-g, --group` | Group/tag for organization |
| `-v, --vault` | Custom vault path |

---

## 9. API Specification

### Crypto Package

```go
// GenerateKey derives a key from password using Argon2id
func GenerateKey(password string, salt []byte) ([]byte, error)

// Encrypt encrypts plaintext with AES-256-GCM
func Encrypt(key, plaintext []byte) (nonce, ciphertext []byte, err error)

// Decrypt decrypts ciphertext with AES-256-GCM
func Decrypt(key, nonce, ciphertext []byte) (plaintext []byte, err error)
```

### Vault Package

```go
// New creates a new vault
func New(password string) (*Vault, error)

// Open opens an existing vault
func Open(path, password string) (*Vault, error)

// Save saves vault to disk
func (v *Vault) Save(path string) error

// Add adds a secret
func (v *Vault) Add(key, value string) error

// Get retrieves a secret
func (v *Vault) Get(key string) (string, error)

// Delete removes a secret
func (v *Vault) Delete(key string) error

// List returns all keys
func (v *Vault) List() []string
```

---

## 10. Security Considerations

### Key Management
- **KEK derived, never stored:** Password only in memory during operation
- **Salt stored in vault:** New salt per vault, unique per install
- **No key file:** Master password entered each session

### Memory Handling
- **Avoid `string` for secrets:** Use `[]byte`, zero after use
- **crypto/subtle:** Constant-time comparison
- **runtime.GC:() hint:** Suggest GC after operations

### Timing Mitigation
- **Fixed-delay auth failures:** No timing oracle
- **Constant-time comparisons:** Use `subtle.ConstantTimeCompare`
- **Jitter:** Random sleep on failed attempts

### Attack Surfaces
- **No CLI args for secrets:** Read from stdin/terminal
- **Masked input:** Password not displayed
- **Clipboard timeout:** Auto-clear after 30s

---

## 11. Testing Strategy

### Unit Tests (80%+ coverage)
```go
// Crypto tests
func TestGenerateKey_SamePassword_DifferentSalt_DifferentKey()
func TestEncrypt_Decrypt_RoundTrip()
func TestEncrypt_TamperedCiphertext_Fails()

// Vault tests
func TestVault_Add_Get()
func TestVault_Delete()
func TestVault_List()
func TestVault_PasswordMismatch_Fails()
```

### Integration Tests
```go
func TestE2E_Init_Add_Get_List_Delete()
func TestE2E_Persist_Reload()
func TestE2E_Export_Import()
```

### Security Tests
- **Entropy verification:** Check random bytes
- **Tamper resistance:** Modify vault, verify failure
- **Timing consistency:** Measure operation times

---

## 12. Atomic Commit Strategy

Format: `<type>(<scope>): <description>`

```
 1.  chore: project scaffold (go.mod, Makefile, .gitignore)
 2.  feat(crypto): AES-256-GCM encrypt/decrypt primitives
 3.  feat(crypto): Argon2id key derivation
 4.  feat(crypto): secure memory handling utilities
 5.  feat(vault): vault data structures
 6.  feat(vault): vault storage layer (JSON)
 7.  feat(cli): init command
 8.  feat(cli): add command
 9.  feat(cli): get command
10.  feat(cli): list command
11.  feat(cli): delete command
12.  feat(cli): update command
13.  feat(cli): export command
14.  feat(cli): import command
15.  test(crypto): crypto unit tests
16.  test(vault): vault unit tests
17.  test(cli): integration tests
18.  fix(security): timing attack mitigation
19.  fix(crypto): memory zeroing implementation
20.  chore: release build configuration
```

---

## 13. Acceptance Criteria

| Category | Criteria |
|----------|----------|
| **Functional** | |
| | Vault can be initialized with password |
| | Secrets persist to disk and reload |
| | CRUD operations work correctly |
| | Export/import round-trips successfully |
| **Security** | |
| | Wrong password fails to decrypt |
| | Tampered vault file detected (GCM auth fails) |
| | No plaintext secrets in vault file |
| | Password only in memory during operation |
| **Performance** | |
| | Open vault: <500ms |
| | Add secret: <200ms |
| | Get secret: <100ms |

---

## 14. Questions for Clarification

Before proceeding with implementation, please confirm:

1. **Language:** Go or Python? (Go recommended for crypto + single binary)
2. **Storage location:** Default `~/.secret-vault/vault` or custom path?
3. **Import format:** Support `.env` file import directly?
4. **Release target:** Linux-only or cross-platform?
5. **Clipboard:** Include clipboard functionality with auto-clear?