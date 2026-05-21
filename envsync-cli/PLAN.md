# envsync-cli: Implementation Plan

## 1. Project Overview

**envsync-cli** - Local environment variable sync manager that syncs `.env` files across projects with AES-256-GCM encryption, project grouping, variable interpolation, and web dashboard.

## 2. Core Features

| Feature | Description |
|---------|-------------|
| **AES-256-GCM Encryption** | All .env files encrypted at rest with derived key from user-provided master password |
| **Project Groups** | Organize projects into logical groups (e.g., "frontend", "backend", "devops") |
| **Variable Interpolation** | Reference values from other variables: `API_BASE_URL=${BASE_URL}/v1` |
| **Git-Ignored Safe Storage** | Encrypted vault file in `.envsync/` directory, added to `.gitignore` |
| **Import/Export** | Import from existing `.env` files, export decrypted `.env` to project |
| **Web Dashboard** | Browser-based UI for viewing/managing variables (optional, local-only) |

## 3. File Structure

```
envsync-cli/
├── src/
│   ├── bin/
│   │   └── main.ts              # Entry point
│   ├── cli/
│   │   ├── index.ts             # CLI command router
│   │   ├── commands/
│   │   │   ├── init.ts          # envsync init
│   │   │   ├── sync.ts          # envsync sync
│   │   │   ├── add.ts          # envsync add VAR=value
│   │   │   ├── remove.ts       # envsync remove VAR
│   │   │   ├── list.ts         # envsync list
│   │   │   ├── import.ts      # envsync import ./path/.env
│   │   │   ├── export.ts      # envsync export
│   │   │   ├── group.ts       # envsync group operations
│   │   │   ├── encrypt.ts     # envsync encrypt ./path/.env
│   │   │   ├── decrypt.ts     # envsync decrypt ./path/.env.enc
│   │   │   └── dashboard.ts  # envsync dashboard
│   │   └── options.ts          # Global CLI options
│   ├── core/
│   │   ├── encryption.ts       # AES-256-GCM implementation
│   │   ├── vault.ts            # Encrypted vault read/write
│   │   ├── interpolator.ts    # Variable interpolation engine
│   │   ├── group-manager.ts   # Project group CRUD
│   │   ├── project-manager.ts # Project registry
│   │   └── key-derivation.ts   # PBKDF2 key derivation
│   ├── config/
│   │   ├── store.ts           # Config file management
│   │   └── schema.ts          # Config validation
│   ├── dashboard/
│   │   ├── server.ts          # Express server
│   │   ├── routes/
│   │   │   ├── api.ts        # REST API endpoints
│   │   │   └── index.ts       # SPA serving
│   │   └── static/
│   │       └── index.html    # Dashboard UI
│   ├── utils/
│   │   ├── logger.ts         # Pretty-printed logs
│   │   ├── prompt.ts         # Input prompts
│   │   ├── validator.ts     # Env var validation
│   │   └── fs.ts            # File system helpers
│   └── types/
│       └── index.ts         # TypeScript interfaces
├── .envsync/
│   ├── config.json          # User config (git-ignored)
│   └── vault.enc            # Encrypted vault (git-ignored)
├── tests/
│   ├── encryption.spec.ts
│   ├── interpolator.spec.ts
│   ├── vault.spec.ts
│   └── integration.spec.ts
├── package.json
├── tsconfig.json
├── .gitignore
├── README.md
└── CONTRIBUTING.md
```

## 4. Dependencies

### Production
- `commander` - CLI argument parsing
- `inquirer` - Interactive prompts  
- `chalk` - Terminal colors
- `cli-table3` - Table output
- `express` - Web dashboard server
- `dotenv` - Parse .env files
- `conf` - Config storage
- `aes-js` or Node crypto - Encryption

### Dev Dependencies
- `typescript`
- `vitest`
- `tsx`

## 5. CLI Commands

```bash
# Initialize new vault
envsync init [--password PASSWORD] [--group GROUP]

# Sync variables to all projects in group
envsync sync [GROUP]

# Add variable
envsync add VAR=value [--project PROJECT] [--group GROUP]

# Remove variable
envsync remove VAR [--project PROJECT] [--group GROUP]

# List all variables
envsync list [--project PROJECT] [--group GROUP] [--decrypted]

# Import from .env file
envsync import ./path/.env [--project PROJECT] [--group GROUP]

# Export to .env file
envsync export [--project PROJECT] [--output ./path/.env]

# Manage groups
envsync group create NAME
envsync group add PROJECT GROUP
envsync group remove PROJECT GROUP
envsync group list

# Web dashboard
envsync dashboard [--port 3000]

# Encrypt/decrypt standalone
envsync encrypt ./path/.env [--password PASSWORD]
envsync decrypt ./path/.env.enc [--password PASSWORD]
```

## 6. Error Handling

- Invalid .env syntax → detailed parse error with line number
- Wrong password → clear "decryption failed" message, allow retry
- Missing group/project → prompt or error with available options
- File permission errors → graceful fallback with temp storage
- Duplicate variables → warn and offer overwrite confirmation

## 7. Security Considerations

- PBKDF2 with 100,000 iterations for key derivation
- AES-256-GCM for authenticated encryption
- No plaintext storage ever (only in memory during sync)
- optional keychain integration for password storage
- Memory wiping after key use
