# PassGen - Secure Password Generator CLI Tool

## Project Overview

**Project Name**: PassGen  
**Type**: Command-line interface (CLI) tool  
**Core Functionality**: Generate cryptographically secure random passwords with configurable options for length, character types, and advanced features.  
**Target Users**: Developers, security professionals, system administrators, and general users who need to generate secure passwords.  
**Language**: Rust  
**License**: Open source

---

## 1. Architecture Overview

### 1.1 High-Level Design

```
┌─────────────────────────────────────────────────────────────┐
│                        PassGen CLI                          │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │    CLI       │  │   Generator  │  │   Storage    │       │
│  │   Parser     │──│   Engine     │──│   Manager    │       │
│  └──────────────┘  └──────────────┘  └──────────────┘       │
│         │                 │                  │               │
│         ▼                 ▼                  ▼               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │   Output     │  │   Entropy    │  │  Clipboard   │       │
│  │   Formatter  │  │   Calculator │  │   Handler    │       │
│  └──────────────┘  └──────────────┘  └──────────────┘       │
└─────────────────────────────────────────────────────────────┘
```

### 1.2 Module Design

| Module | Responsibility | Public API |
|--------|----------------|------------|
| `cli` | Parse command-line arguments, display help/version | `parse_args() -> Config` |
| `generator` | Core password generation logic | `generate(config) -> Password` |
| `entropy` | Calculate password strength/entropy | `calculate_strength(password) -> Strength` |
| `storage` | Manage password history and exports | `save()`, `load()`, `export()` |
| `clipboard` | Copy password to system clipboard | `copy_to_clipboard(password)` |
| `output` | Format and display results | `display_password()`, `display_stats()` |

---

## 2. Functional Requirements

### 2.1 Core Features

#### 2.1.1 Password Generation

| Feature | Description | Default |
|---------|-------------|---------|
| Length | Specify password length (8-128 characters) | 16 |
| Uppercase | Include uppercase letters (A-Z) | true |
| Lowercase | Include lowercase letters (a-z) | true |
| Numbers | Include numbers (0-9) | true |
| Symbols | Include special characters (!@#$%^&*) | true |
| Custom symbols | Specify custom symbol set | optional |
| Exclude ambiguous | Remove characters (0, O, l, 1, I) | false |
| No duplicate | No repeated characters in password | false |

#### 2.1.2 Pronounceable Passwords

- Generate phonetically pronounceable passwords
- Configurable syllable count
- Optional separator characters
- Example outputs: `kexu-boza-ruvem`, `mifa-tinu-wanoz`

#### 2.1.3 Password Strength Indicator

- Calculate entropy in bits
- Display strength level: Weak / Fair / Good / Strong / Very Strong
- Show estimated crack time

| Entropy (bits) | Strength | Color |
|----------------|----------|-------|
| < 28 | Weak | Red |
| 28-35 | Fair | Yellow |
| 36-59 | Good | Green |
| 60-79 | Strong | Blue |
| >= 80 | Very Strong | Cyan |

#### 2.1.4 Clipboard Integration

- Copy generated password to system clipboard
- Auto-clear clipboard after configurable timeout (default: 30 seconds)
- Visual confirmation on copy

#### 2.1.5 History Management

- Store generated passwords locally (encrypted)
- Display history with timestamps
- Search/filter history
- Clear history option

#### 2.1.6 Export Options

- Export history to file (JSON, CSV, plain text)
- Export formats:
  - JSON: `{ "passwords": [{ "password": "...", "created_at": "...", "length": 16 }] }`
  - CSV: `password,created_at,length,strength`
  - Plain text: One password per line

### 2.2 User Interface

#### 2.2.1 Command Structure

```bash
passgen [OPTIONS] [COMMAND]

Commands:
  generate, gen, g    Generate password(s)
  history, hist      View password history
  clear              Clear password history
  export             Export history
  config             View/set configuration

Options:
  -l, --length <NUM>       Password length (8-128)
  -u, --uppercase          Include uppercase letters
  -l, --lowercase          Include lowercase letters
  -n, --numbers            Include numbers
  -s, --symbols            Include symbols
  --no-ambiguous          Exclude ambiguous characters
  --no-duplicate          No repeated characters
  -c, --count <NUM>        Number of passwords to generate
  -p, --pronounceable      Generate pronounceable password
  --copy                   Copy to clipboard
  --clear-clipboard <SEC>  Auto-clear clipboard after N seconds
  -o, --output <FILE>     Output file (for export)
  -f, --format <FORMAT>   Output format (json, csv, txt)
  --no-history            Don't save to history
  -v, --verbose           Show detailed output
  --version               Show version
  --help                  Show help
```

#### 2.2.2 Interactive Mode

- Interactive mode when no arguments provided
- Guided password generation with prompts

#### 2.2.3 Output Formats

```
# Default output
$ passgen
K9$mNp@2xL#qR8vW

# Verbose output with strength
$ passgen --verbose
Password: K9$mNp@2xL#qR8vW
Length: 16
Entropy: 95.3 bits
Strength: Very Strong
Estimated crack time: 1.2e+15 years
Copied to clipboard!

# Multiple passwords
$ passgen --count 3
vF3#kL9@mNp2QwR
xY7!bZ4&Hi0TjK
qW8$eR5%TyU1pO
```

---

## 3. Technical Specification

### 3.1 Dependencies

```toml
[dependencies]
# CLI parsing
clap = "4.4"           # Command-line argument parser

# Random number generation
rand = "0.8"           # Random number generator
getrandom = "0.2"      # Cryptographically secure random

# Password strength
zxcvbn = "2.6"         # Password strength estimator

# Clipboard
arboard = "3.2"        # Cross-platform clipboard

# Storage
serde = "1.0"          # Serialization
serde_json = "1.0"     # JSON serialization
dirs = "5.0"           # Platform-specific directories
aes-gcm = "0.10"       # Encryption
base64 = "0.21"        # Base64 encoding

# Async (for clipboard timeout)
tokio = { version = "1.35", features = ["time", "sync"] }

# Logging
log = "0.4"            # Logging facade
env_logger = "0.10"    # Logger implementation

# Error handling
anyhow = "1.0"         # Error handling
thiserror = "1.0"      # Custom errors

[dev-dependencies]
criterion = "0.5"      # Benchmarking
tempfile = "3.8"       # Temporary files for tests
```

### 3.2 Project Structure

```
passgen/
├── Cargo.toml
├── src/
│   ├── main.rs           # Entry point
│   ├── cli.rs            # CLI argument parsing
│   ├── config.rs         # Configuration management
│   ├── generator.rs      # Password generation engine
│   ├── entropy.rs        # Password strength calculation
│   ├── storage.rs        # History and encryption
│   ├── clipboard.rs      # Clipboard integration
│   ├── output.rs         # Output formatting
│   ├── errors.rs         # Error types
│   └── lib.rs            # Library exports
├── tests/
│   ├── integration.rs    # Integration tests
│   └── unit.rs           # Unit tests
├── benches/
│   └── benchmark.rs      # Performance benchmarks
├── examples/
│   └── simple.rs         # Usage examples
├── .github/
│   └── workflows/
│       └── ci.yml       # CI configuration
└── README.md
```

### 3.3 Core Algorithms

#### 3.3.1 Secure Random Generation

```rust
// Use OS CSPRNG via getrandom crate
use rand::{rngs::OsRng, Rng, RngCore};

fn generate_password(chars: &[char], length: usize) -> String {
    let mut rng = OsRng;
    let mut buf = vec![0u8; length];
    rng.fill_bytes(&mut buf);
    
    buf.iter()
        .map(|&b| chars[b as usize % chars.len()])
        .collect()
}
```

#### 3.3.2 Entropy Calculation

```
Entropy = log2(charset_size^length)
        = length * log2(charset_size)

Character set sizes:
- Lowercase: 26
- Uppercase: 26
- Digits: 10
- Symbols: ~32
- Combined: ~94
```

#### 3.3.3 Pronounceable Generation

- Use consonant-vowel pattern: CVC, CVCV, CVCVC
- Consonant clusters for natural feel
- Configurable separator

---

## 4. Data Structures

### 4.1 Configuration

```rust
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct GeneratorConfig {
    pub length: usize,
    pub uppercase: bool,
    pub lowercase: bool,
    pub numbers: bool,
    pub symbols: bool,
    pub custom_symbols: Option<String>,
    pub exclude_ambiguous: bool,
    pub no_duplicate: bool,
    pub pronounceable: bool,
    pub syllable_count: Option<usize>,
    pub separator: Option<char>,
}

impl Default for GeneratorConfig {
    fn default() -> Self {
        Self {
            length: 16,
            uppercase: true,
            lowercase: true,
            numbers: true,
            symbols: true,
            custom_symbols: None,
            exclude_ambiguous: false,
            no_duplicate: false,
            pronounceable: false,
            syllable_count: None,
            separator: None,
        }
    }
}
```

### 4.2 Password Entry

```rust
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct PasswordEntry {
    pub password: String,
    pub created_at: DateTime<Utc>,
    pub length: usize,
    pub entropy: f64,
    pub strength: Strength,
    pub config: GeneratorConfig,
}
```

### 4.3 Strength Enum

```rust
#[derive(Clone, Debug, Serialize, Deserialize, PartialEq)]
pub enum Strength {
    Weak,
    Fair,
    Good,
    Strong,
    VeryStrong,
}
```

---

## 5. Error Handling

### 5.1 Error Types

```rust
#[derive(Debug, thiserror::Error)]
pub enum PassgenError {
    #[error("Invalid length: {0}. Must be between 8 and 128")]
    InvalidLength(usize),
    
    #[error("No character sets selected")]
    NoCharacterSets,
    
    #[error("Not enough unique characters for password")]
    InsufficientUniqueChars,
    
    #[error("Clipboard error: {0}")]
    ClipboardError(String),
    
    #[error("Storage error: {0}")]
    StorageError(String),
    
    #[error("Encryption error: {0}")]
    EncryptionError(String),
    
    #[error("IO error: {0}")]
    IoError(#[from] std::io::Error),
    
    #[error("JSON error: {0}")]
    JsonError(#[from] serde_json::Error),
}
```

---

## 6. Configuration Files

### 6.1 Global Config

Location: `~/.config/passgen/config.toml`

```toml
[generator]
default_length = 16
default_uppercase = true
default_lowercase = true
default_numbers = true
default_symbols = true
exclude_ambiguous = false

[clipboard]
auto_copy = false
auto_clear = true
clear_timeout = 30

[storage]
history_enabled = true
max_history = 100
encryption_enabled = true

[output]
verbose = false
color = true
show_entropy = true
show_strength = true
```

---

## 7. Security Considerations

1. **CSPRNG**: Use OS-provided cryptographic random number generator
2. **Memory**: Clear password from memory after use
3. **Clipboard**: Auto-clear clipboard after configurable timeout
4. **History**: Encrypt stored passwords with AES-256-GCM
5. **No logging**: Never log passwords
6. **Secure defaults**: Sensible secure defaults (16 char, all char types)

---

## 8. Testing Strategy

### 8.1 Unit Tests

- Character set generation
- Entropy calculation
- Password generation with all options
- Clipboard functionality
- Storage read/write

### 8.2 Integration Tests

- CLI argument parsing
- End-to-end password generation
- History management
- Export functionality

### 8.3 Property-Based Tests

- Generated passwords always meet constraints
- Entropy calculation accuracy

---

## 9. Implementation Phases

### Phase 1: Core Generator (Week 1)
- [ ] Project setup with Cargo
- [ ] Basic CLI with clap
- [ ] Character set management
- [ ] Random password generation
- [ ] Basic tests

### Phase 2: Advanced Features (Week 2)
- [ ] Pronounceable passwords
- [ ] Password strength/entropy
- [ ] Clipboard integration
- [ ] Verbose output

### Phase 3: Storage & History (Week 3)
- [ ] History storage with encryption
- [ ] History view/clear commands
- [ ] Export functionality (JSON, CSV, TXT)

### Phase 4: Polish (Week 4)
- [ ] Configuration file support
- [ ] Interactive mode
- [ ] Code cleanup and documentation
- [ ] Benchmarking
- [ ] Release build

---

## 10. Milestones

| Milestone | Deliverables | Status |
|-----------|--------------|--------|
| M1 | Basic password generation | Week 1 |
| M2 | All generation options | Week 2 |
| M3 | Strength indicator | Week 2 |
| M4 | Clipboard integration | Week 2 |
| M5 | History management | Week 3 |
| M6 | Export features | Week 3 |
| M7 | Configuration | Week 4 |
| M8 | Release v1.0.0 | Week 4 |

---

## 11. Future Enhancements

- [ ] Password pattern templates (e.g., "CamelCase", "snake_case")
- [ ] Custom dictionaries for pronounceable passwords
- [ ] Password sharing between devices
- [ ] Password expiration reminders
- [ ] Integration with password managers (Bitwarden, 1Password)
- [ ] TUI (terminal user interface) for interactive mode

---

## 12. Success Criteria

1. Generates passwords with configurable character sets
2. Supports all specified options (length, char types, exclude ambiguous, pronounceable)
3. Displays password strength with entropy calculation
4. Copies to clipboard with auto-clear
5. Maintains encrypted password history
6. Exports history in JSON, CSV, and TXT formats
7. Runs on Linux, macOS, and Windows
8. Passes all security audits
9. Benchmark: < 10ms for password generation