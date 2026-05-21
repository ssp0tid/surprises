# dot-sync Implementation Plan

## 1. Project Overview

**Project Name:** dot-sync  
**Type:** CLI Tool (Node.js/TypeScript)  
**Core Functionality:** Synchronize dotfiles across machines with encryption, conflict resolution, git-based storage, and selective sharing.  
**Target Users:** Developers who maintain dotfiles across multiple machines and want secure, flexible synchronization.

---

## 2. File Structure

```
dot-sync/
├── src/
│   ├── cli/
│   │   ├── index.ts              # CLI entry point
│   │   ├── commands/
│   │   │   ├── init.ts           # Initialize dot-sync in a directory
│   │   │   ├── add.ts            # Add files to tracking
│   │   │   ├── remove.ts         # Remove files from tracking
│   │   │   ├── sync.ts           # Sync with remote
│   │   │   ├── status.ts         # Show tracked files status
│   │   │   ├── share.ts          # Share files with team/machine
│   │   │   ├── unshare.ts        # Stop sharing files
│   │   │   └── config.ts         # Manage configuration
│   │   └── options/              # Shared CLI options
│   ├── core/
│   │   ├── index.ts              # Core API exports
│   │   ├── tracker.ts            # File tracking logic
│   │   ├── sync-engine.ts        # Main sync orchestration
│   │   ├── encryptor.ts          # Encryption/decryption (AES-256-GCM)
│   │   ├── git-manager.ts        # Git operations wrapper
│   │   ├── conflict-resolver.ts  # Conflict detection & resolution
│   │   └── share-manager.ts      # Selective sharing logic
│   ├── storage/
│   │   ├── index.ts
│   │   ├── file-store.ts         # Virtual file storage
│   │   ├── manifest.ts           # Track file metadata
│   │   └── cache.ts              # Local cache management
│   ├── config/
│   │   ├── index.ts
│   │   ├── schema.ts             # Config validation schema
│   │   └── defaults.ts           # Default configuration
│   ├── utils/
│   │   ├── index.ts
│   │   ├── logger.ts             # Logging utility
│   │   ├── path.ts               # Path utilities (expand, normalize)
│   │   ├── checksum.ts           # File checksums
│   │   └── crypto.ts             # Crypto utilities
│   └── types/
│       ├── index.ts
│       ├── manifest.ts           # Manifest file types
│       ├── config.ts             # Config types
│       └── events.ts             # Event types
├── test/
│   ├── unit/
│   │   ├── encryptor.test.ts
│   │   ├── tracker.test.ts
│   │   ├── conflict-resolver.test.ts
│   │   └── share-manager.test.ts
│   ├── integration/
│   │   ├── sync.test.ts
│   │   └── git-manager.test.ts
│   └── fixtures/                 # Test fixtures
├── scripts/
│   ├── build.ts                  # Build script
│   └── release.ts                # Release script
├── .vscode/
│   └── settings.json
├── package.json
├── tsconfig.json
├── tsconfig.build.json
├── eslint.config.js
├── prettier.config.js
├── vitest.config.ts
└── README.md
```

---

## 3. Dependencies

### Production Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| `commander` | ^12.x | CLI framework |
| `conf` | ^12.x | Config storage |
| `chalk` | ^5.x | Terminal colors |
| `ora` | ^8.x | Spinners/loading states |
| `execa` | ^9.x | Git command execution |
| `enquirer` | ^2.x | Interactive prompts |
| `dot-prop` | ^5.x | Nested config access |
| `ajv` | ^8.x | JSON schema validation |
| `async-mutex` | ^1.x | Concurrency control |
| `diff` | ^5.x | Text diff for conflicts |
| `memfs` | ^4.x | In-memory file system for tests |

### Dev Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| `typescript` | ^5.x | Type safety |
| `vitest` | ^2.x | Testing framework |
| `tsx` | ^4.x | TypeScript execution |
| `eslint` | ^9.x | Linting |
| `prettier` | ^3.x | Code formatting |
| `pkg` | ^5.x | Binary distribution |
| `release-it` | ^17.x | Publishing |
| `@types/node` | ^22.x | Node types |

---

## 4. Core Features & Implementation

### 4.1 File Tracking

```typescript
// Core tracking API
interface Tracker {
  add(paths: string[]): Promise<TrackedFile[]>;
  remove(paths: string[]): Promise<void>;
  list(): TrackedFile[];
  status(): Promise<FileStatus[]>;
  isTracked(path: string): boolean;
}

interface TrackedFile {
  id: string;              // UUID
  originalPath: string;    // e.g., ~/.bashrc
  relativePath: string;    // e.g., bashrc
  checksum: string;        // SHA-256
  encrypted: boolean;
  shared: boolean;
  sharedWith: string[];    // machine IDs
  lastSynced: number;      // timestamp
  version: number;
}
```

**Implementation Notes:**
- Track files by relative path from `$HOME`
- Generate unique ID per file
- Store checksums for change detection
- Support glob patterns in `add` command

### 4.2 Encryption

```typescript
interface Encryptor {
  encrypt(data: Buffer, key: Buffer): Promise<EncryptedData>;
  decrypt(data: EncryptedData, key: Buffer): Promise<Buffer>;
  generateKey(): Buffer;
  deriveKey(passphrase: string, salt: Buffer): Promise<Buffer>;
}

interface EncryptedData {
  ciphertext: Buffer;
  iv: Buffer;
  authTag: Buffer;
  salt?: Buffer;
}
```

**Implementation Notes:**
- Use AES-256-GCM for authenticated encryption
- Derive key from passphrase using PBKDF2 (100,000 iterations)
- Store salt with encrypted file
- Encrypt files individually (not whole archive)
- Default: encrypt all tracked files
- Option: `--no-encrypt` for public dotfiles

### 4.3 Git-Based Storage

```typescript
interface GitManager {
  init(remoteUrl: string): Promise<void>;
  clone(remoteUrl: string, targetDir: string): Promise<void>;
  add(files: string[]): Promise<void>;
  commit(message: string): Promise<string>; // returns commit hash
  push(): Promise<void>;
  pull(): Promise<void>;
  fetch(): Promise<void>;
  getHistory(limit: number): Promise<Commit[]>;
  getFileAtCommit(path: string, commit: string): Promise<Buffer>;
  createBranch(name: string): Promise<void>;
  checkout(branch: string): Promise<void>;
}

interface Commit {
  hash: string;
  message: string;
  author: string;
  date: number;
  files: string[];
}
```

**Implementation Notes:**
- Use `execa` for git operations (not child_process directly)
- Store encrypted files in `.dot-sync/storage/`
- Store manifest in `.dot-sync/manifest.json.enc`
- Use separate branch for dot-sync data
- Default branch: `dot-sync`
- Remote: user-provided (GitHub, GitLab, etc.)

### 4.4 Conflict Resolution

```typescript
type ConflictStrategy = 'prompt' | 'keep-local' | 'keep-remote' | 'merge';

interface ConflictResolver {
  detect(local: FileState, remote: FileState): Conflict | null;
  resolve(conflict: Conflict, strategy: ConflictStrategy): Promise<Resolution>;
  merge(local: string, remote: string): Promise<string>;
}

interface Conflict {
  path: string;
  localVersion: FileState;
  remoteVersion: FileState;
  commonAncestor: FileState;
}

interface Resolution {
  action: 'keep-local' | 'keep-remote' | 'merged' | 'manual';
  content?: string;
  message?: string;
}
```

**Conflict Detection:**
1. Compare checksums - if different, conflict exists
2. Check timestamps - if both modified after last sync, conflict
3. Check version numbers in manifest

**Resolution Strategies:**
- `prompt`: Show diff, ask user which version
- `keep-local`: Always prefer local
- `keep-remote`: Always prefer remote
- `merge`: Attempt 3-way merge (for text files)

**Merge Logic:**
- Use `diff` library for text files
- If merge fails (binary or complex conflict), fallback to manual
- Show unified diff for manual resolution

### 4.5 Selective Sharing

```typescript
interface ShareManager {
  share(files: string[], withMachines: string[]): Promise<void>;
  unshare(files: string[]): Promise<void>;
  listShared(): SharedFile[];
  getSharedWith(fileId: string): string[];
  addMachine(machine: MachineConfig): Promise<void>;
  listMachines(): MachineConfig[];
  removeMachine(machineId: string): Promise<void>;
}

interface MachineConfig {
  id: string;           // UUID
  name: string;         // e.g., "work-laptop"
  publicKey: string;    // For encrypting shared files
  lastSeen: number;
}

interface SharedFile {
  fileId: string;
  sharedWith: string[];
  permission: 'read' | 'write';
}
```

**Sharing Implementation:**
- Each machine has RSA key pair
- Shared files encrypted with recipient's public key
- Machine public keys stored in `.dot-sync/machines.json.enc`
- Use hybrid encryption: RSA for key exchange, AES for content

**Permission Levels:**
- `read`: Recipient can decrypt and read
- `write`: (future) Recipient can modify and sync back

---

## 5. CLI API Design

### Global Options

```
-V, --version          Show version
--verbose              Enable verbose logging
--quiet                Suppress non-error output
--config <path>        Custom config file path
--no-color             Disable colors
```

### Commands

#### `dot-sync init [directory]`

Initialize dot-sync in a directory.

```
Arguments:
  directory              Directory to initialize (default: current)

Options:
  --remote <url>        Git remote URL
  --passphrase <str>    Encryption passphrase (prompts if omitted)
  --branch <name>       Branch name (default: dot-sync)

Examples:
  dot-sync init
  dot-sync init --remote git@github.com:user/dotfiles.git
```

#### `dot-sync add <patterns...>`

Add files to tracking.

```
Arguments:
  patterns               Glob patterns or paths to track

Options:
  --no-encrypt          Don't encrypt these files
  --share-with <machines>  Share with machines (comma-separated IDs)

Examples:
  dot-sync add ~/.bashrc ~/.zshrc
  dot-sync add "~/.**" --exclude "~/.**.local"
  dot-sync add ~/.gitconfig --share-with machine1,machine2
```

#### `dot-sync remove <patterns...>`

Remove files from tracking.

```
Options:
  --force                Don't prompt for confirmation
  --keep-local           Keep local file, just stop tracking

Examples:
  dot-sync remove ~/.bashrc
  dot-sync remove "~/.*"
```

#### `dot-sync sync`

Sync with remote repository.

```
Options:
  --strategy <name>      Conflict strategy: prompt, keep-local, keep-remote, merge
  --force                Force push (overwrite remote)
  --dry-run              Show what would be synced
  --push-only            Only push, don't pull
  --pull-only            Only pull, don't push

Examples:
  dot-sync sync
  dot-sync sync --strategy keep-remote
  dot-sync sync --dry-run
```

#### `dot-sync status`

Show tracked files status.

```
Options:
  --short                One-line output
  --json                 JSON output
  --watch                Watch for changes

Examples:
  dot-sync status
  dot-sync status --json
```

#### `dot-sync share <files> --with <machines>`

Share files with machines.

```
Arguments:
  files                  Files to share (by path or ID)
  machines               Machine IDs to share with

Options:
  --revoke               Stop sharing instead

Examples:
  dot-sync share ~/.bashrc --with work-laptop
  dot-sync share 550e8400-e29b --with machine1,machine2
```

#### `dot-sync machine add`

Add a machine for sharing.

```
Options:
  --name <name>          Machine name
  --id <id>              Machine ID (for receiving shares)
  --public-key <path>    Public key file path

Examples:
  dot-sync machine add --name work-laptop
```

#### `dot-sync machine list`

List all machines.

```
Options:
  --json                 JSON output
```

#### `dot-sync config [key] [value]`

Get/set configuration.

```
Arguments:
  key                    Config key (dot notation supported)
  value                  New value (omit to get current)

Examples:
  dot-sync config remote.url
  dot-sync config remote.url git@github.com:user/dotfiles.git
  dot-sync config encryption.enabled false
```

---

## 6. Error Handling

### Error Types

```typescript
enum ErrorCode {
  // Init errors
  E_NOT_INITIALIZED = 'E_NOT_INITIALIZED',
  E_ALREADY_INITIALIZED = 'E_ALREADY_INITIALIZED',
  E_INVALID_REMOTE = 'E_INVALID_REMOTE',
  
  // Tracking errors
  E_FILE_NOT_FOUND = 'E_FILE_NOT_FOUND',
  E_ALREADY_TRACKED = 'E_ALREADY_TRACKED',
  E_NOT_TRACKED = 'E_NOT_TRACKED',
  E_PERMISSION_DENIED = 'E_PERMISSION_DENIED',
  
  // Sync errors
  E_CONFLICT = 'E_CONFLICT',
  E_GIT_ERROR = 'E_GIT_ERROR',
  E_PUSH_FAILED = 'E_PUSH_FAILED',
  E_PULL_FAILED = 'E_PULL_FAILED',
  E_MERGE_FAILED = 'E_MERGE_FAILED',
  
  // Encryption errors
  E_ENCRYPTION_FAILED = 'E_ENCRYPTION_FAILED',
  E_DECRYPTION_FAILED = 'E_DECRYPTION_FAILED',
  E_INVALID_PASSPHRASE = 'E_INVALID_PASSPHRASE',
  
  // Sharing errors
  E_MACHINE_NOT_FOUND = 'E_MACHINE_NOT_FOUND',
  E_NOT_SHARED_WITH_YOU = 'E_NOT_SHARED_WITH_YOU',
  E_INVALID_PUBLIC_KEY = 'E_INVALID_PUBLIC_KEY',
}

class DotSyncError extends Error {
  code: ErrorCode;
  details?: unknown;
  suggestion?: string;  // How to fix
}
```

### Error Display

```bash
# Human-readable (default)
Error: File not found
  Code: E_FILE_NOT_FOUND
  File: /home/user/.bashrc
  Suggestion: Check if the file exists

# JSON mode
{
  "error": {
    "code": "E_FILE_NOT_FOUND",
    "message": "File not found",
    "details": { "path": "/home/user/.bashrc" },
    "suggestion": "Check if the file exists"
  }
}
```

### Recovery Strategies

| Error | Recovery |
|-------|----------|
| `E_NOT_INITIALIZED` | Prompt to run `dot-sync init` |
| `E_GIT_ERROR` | Show git error, suggest checking remote |
| `E_CONFLICT` | Enter conflict resolution flow |
| `E_INVALID_PASSPHRASE` | Re-prompt for passphrase (3 attempts) |
| `E_PUSH_FAILED` | Offer to retry or force push |

---

## 7. Edge Cases

### File System

1. **Symlinks**: Resolve to real path, track target
2. **Broken symlinks**: Warn but don't track
3. **Hidden files**: Include by default (`~/.*`)
4. **Very large files**: Warn if > 10MB, configurable limit
5. **Binary files**: Store as-is (can't merge)
6. **Read-only files**: Warn, offer to chmod
7. **Files outside $HOME**: Support via absolute paths

### Git Operations

1. **No remote**: Offer to create or skip push
2. **Out of sync**: Force push option, warn about data loss
3. **Detached HEAD**: Warn user, offer to checkout branch
4. **Merge conflicts in git itself**: Abort and report
5. **Large repo**: Use shallow clone option
6. **Authentication**: Support SSH keys and token

### Encryption

1. **Corrupted encrypted file**: Report, offer to redownload
2. **Wrong passphrase**: Clear key from memory, re-prompt
3. **Key derivation failure**: Exponential backoff on retries
4. **Salt mismatch**: Indicates tampering, alert user

### Sharing

1. **Machine offline**: Queue share, sync when online
2. **Revoked access**: Clear local decrypted files
3. **Expired public key**: Prompt to request new one
4. **Self-share**: Prevent, warn user

### Conflict Resolution

1. **Binary conflict**: Can't merge, prompt to choose
2. **Deleted locally vs modified remotely**: Prompt for action
3. **Deleted remotely vs modified locally**: Prompt for action
4. **Both deleted**: Remove locally, no conflict
5. **Circular dependencies**: Not applicable (files, not packages)

---

## 8. Configuration

### Config File

Location: `~/.config/dot-sync/config.json`

```json
{
  "version": "1.0.0",
  "remote": {
    "url": "git@github.com:user/dotfiles.git",
    "branch": "dot-sync"
  },
  "encryption": {
    "enabled": true,
    "algorithm": "aes-256-gcm"
  },
  "sync": {
    "autoPush": false,
    "autoPull": false,
    "conflictStrategy": "prompt",
    "excludePatterns": ["*.log", "node_modules/**"]
  },
  "tracking": {
    "defaultDirectory": "~/dotfiles",
    "encryptByDefault": true
  },
  "sharing": {
    "defaultPermission": "read"
  },
  "logging": {
    "level": "info",
    "file": null
  }
}
```

### Manifest File

Location: `.dot-sync/manifest.json.enc`

```json
{
  "version": "1.0.0",
  "machineId": "uuid-v4",
  "files": [
    {
      "id": "uuid-v4",
      "originalPath": "/home/user/.bashrc",
      "relativePath": "bashrc",
      "checksum": "sha256:abc123...",
      "encrypted": true,
      "shared": false,
      "sharedWith": [],
      "lastSynced": 1700000000000,
      "version": 3
    }
  ],
  "machines": [
    {
      "id": "uuid-v4",
      "name": "work-laptop",
      "publicKey": "-----BEGIN PUBLIC KEY-----\n...",
      "addedAt": 1699900000000,
      "lastSeen": 1700000000000
    }
  ]
}
```

---

## 9. Security Considerations

1. **Passphrase**: Never store, derive key on-demand, clear from memory
2. **Private keys**: Encrypted at rest with passphrase
3. **Key material**: Use Node.js crypto random for IV/salt
4. **Memory**: Clear sensitive data after use
5. **Audit trail**: Log all sync operations (not file contents)
6. **Remote trust**: Warn about MITM on first clone

---

## 10. Development Phases

### Phase 1: Core (Week 1)
- [ ] Project setup (TypeScript, ESLint, Vitest)
- [ ] CLI framework with Commander
- [ ] Config management
- [ ] File tracker
- [ ] Basic sync (no conflicts)

### Phase 2: Encryption (Week 2)
- [ ] AES-256-GCM encryption
- [ ] Key derivation
- [ ] Encrypted storage/retrieval

### Phase 3: Git Integration (Week 3)
- [ ] Git manager wrapper
- [ ] Push/pull operations
- [ ] Branch management

### Phase 4: Conflict Resolution (Week 4)
- [ ] Conflict detection
- [ ] Resolution strategies
- [ ] Merge logic for text files

### Phase 5: Sharing (Week 5)
- [ ] Machine management
- [ ] Public key encryption
- [ ] Share/unshare operations

### Phase 6: Polish (Week 6)
- [ ] Error handling polish
- [ ] Edge cases
- [ ] Documentation
- [ ] Binary distribution

---

## 11. Testing Strategy

### Unit Tests
- Encryptor: encrypt/decrypt roundtrip
- Tracker: add/remove/list
- ConflictResolver: all strategies
- Path utilities: expand/normalize

### Integration Tests
- Full sync cycle (add → encrypt → push → pull → decrypt)
- Conflict scenarios
- Share/unshare flow

### Manual Testing
- Fresh init on new machine
- Pull from existing remote
- Multiple conflict resolutions

---

## 12. Binary Distribution

```bash
# Build for current platform
npm run build

# Cross-compile
npm run build:mac    # macOS x64 + arm64
npm run build:linux  # Linux x64
npm run build:win    # Windows x64

# Output: dist/dot-sync-{version}-{platform}-{arch}
```

---

This plan provides a complete roadmap for implementing dot-sync with all requested features.