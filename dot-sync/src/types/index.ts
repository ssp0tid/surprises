/**
 * TypeScript interfaces for dot-sync
 */

export interface TrackedFile {
  /** Absolute path to the tracked file */
  path: string;
  /** MD5 hash for change detection */
  hash: string;
  /** Last modified timestamp (Unix epoch ms) */
  mtime: number;
  /** File size in bytes */
  size: number;
}

export interface Config {
  /** Source directory containing dotfiles to track */
  sourceDir: string;
  /** Repository URL for dotfile storage */
  repoUrl: string;
  /** Branch to use for sync */
  branch: string;
  /** Encryption settings */
  encryption: EncryptionConfig;
  /** Git settings */
  git: GitConfig;
}

export interface EncryptionConfig {
  /** Enable encryption */
  enabled: boolean;
  /** Encryption algorithm */
  algorithm: 'aes-256-gcm';
  /** Key derivation function */
  kdf: 'pbkdf2';
  /** Key iterations */
  iterations: number;
  /** Key length */
  keyLength: number;
}

export interface GitConfig {
  /** Commit author name */
  authorName: string;
  /** Commit author email */
  authorEmail: string;
  /** Commit message template */
  commitMessage: string;
  /** Auto-commit interval in ms (0 = disabled) */
  autoCommitInterval: number;
}

export interface Manifest {
  /** Manifest version */
  version: string;
  /** Last update timestamp */
  updatedAt: number;
  /** List of tracked files */
  files: TrackedFile[];
  /** Metadata */
  meta: ManifestMeta;
}

export interface ManifestMeta {
  /** Source directory */
  sourceDir: string;
  /** Repository URL */
  repoUrl: string;
  /** Current branch */
  branch: string;
}

export interface GitStatus {
  /** Current branch name */
  branch: string;
  /** List of modified files */
  modified: string[];
  /** List of new/untracked files */
  untracked: string[];
  /** List of staged files */
  staged: string[];
  /** Number of commits ahead of remote */
  ahead: number;
  /** Number of commits behind remote */
  behind: number;
}

export interface GitCommit {
  /** Commit hash (full) */
  hash: string;
  /** Commit hash (short, 7 chars) */
  shortHash: string;
  /** Commit message */
  message: string;
  /** Author name */
  author: string;
  /** Author email */
  authorEmail: string;
  /** Commit timestamp */
  timestamp: number;
}

export interface SyncResult {
  /** Whether sync was successful */
  success: boolean;
  /** Number of files synced */
  filesSynced: number;
  /** List of errors encountered */
  errors: string[];
  /** Commit hash if committed */
  commitHash?: string;
}

export interface EncryptedData {
  /** Initialization vector */
  iv: string;
  /** Authentication tag */
  authTag: string;
  /** Encrypted content (base64) */
  data: string;
}