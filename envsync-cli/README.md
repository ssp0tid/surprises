# envsync-cli

A Python Click CLI tool for syncing `.env` files across projects with AES-256-GCM encryption.

## Features

- **AES-256-GCM Encryption**: All .env files encrypted at rest with derived key from user-provided master password
- **Project Groups**: Organize projects into logical groups (e.g., "frontend", "backend", "devops")
- **Variable Interpolation**: Reference values from other variables: `API_BASE_URL=${BASE_URL}/v1`
- **Git-Ignored Safe Storage**: Encrypted vault file in `.envsync/` directory
- **Import/Export**: Import from existing `.env` files, export decrypted `.env` to project
- **Web Dashboard**: Browser-based UI for viewing/managing variables (optional)

## Installation

```bash
pip install envsync-cli
```

Or install in development mode:

```bash
pip install -e ".[dev]"
```

For dashboard support:

```bash
pip install -e ".[dashboard]"
```

## Quick Start

```bash
envsync init --password YOUR_PASSWORD --group backend
envsync add API_KEY=your-api-key
envsync list
envsync sync backend
```

## Commands

### init

Initialize a new encrypted vault.

```bash
envsync init --password PASSWORD --group GROUP
```

### add

Add a variable.

```bash
envsync add VAR=value
envsync add VAR=value --project myproject
```

Using interactive mode:

```bash
envsync add
```

### remove

Remove a variable.

```bash
envsync remove VAR
envsync remove VAR --global
```

### list

List all variables.

```bash
envsync list
envsync list --project myproject
envsync list --decrypted
```

### import

Import variables from a `.env` file.

```bash
envsync import ./path/.env
envsync import ./path/.env --project myproject
```

### export

Export variables to a `.env` file.

```bash
envsync export
envsync export --output ./output/.env
```

### sync

Sync variables to all projects in a group.

```bash
envsync sync mygroup
```

### group

Manage groups.

```bash
envsync group create mygroup
envsync group delete mygroup
envsync group add myproject mygroup
envsync group remove myproject mygroup
envsync group list
```

### dashboard

Start the web dashboard.

```bash
envsync dashboard --port 3000
```

## Security

- PBKDF2 with 100,000 iterations for key derivation
- AES-256-GCM for authenticated encryption
- No plaintext storage ever (only in memory during sync)
- Vault stored in `.envsync/` directory (git-ignored)

## License

MIT