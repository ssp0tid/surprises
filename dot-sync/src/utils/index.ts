/**
 * Utilities: logger, path helpers, checksums
 */

import * as crypto from 'crypto';
import * as fs from 'fs';
import * as path from 'path';
import chalk from 'chalk';
import { TrackedFile } from '../types';

// ============================================================
// LOGGER
// ============================================================

export type LogLevel = 'debug' | 'info' | 'warn' | 'error';

export interface LoggerOptions {
  prefix?: string;
  timestamp?: boolean;
  level?: LogLevel;
}

export class Logger {
  private prefix: string;
  private showTimestamp: boolean;
  private minLevel: LogLevel;

  private readonly levelPriority: Record<LogLevel, number> = {
    debug: 0,
    info: 1,
    warn: 2,
    error: 3,
  };

  constructor(options: LoggerOptions = {}) {
    this.prefix = options.prefix || '';
    this.showTimestamp = options.timestamp ?? true;
    this.minLevel = options.level || 'info';
  }

  private format(level: LogLevel, message: string): string {
    const parts: string[] = [];
    if (this.showTimestamp) {
      parts.push(chalk.dim(new Date().toISOString()));
    }
    if (this.prefix) {
      parts.push(chalk.cyan(`[${this.prefix}]`));
    }
    const levelTag = this.formatLevel(level);
    parts.push(levelTag);
    parts.push(message);
    return parts.join(' ');
  }

  private formatLevel(level: LogLevel): string {
    switch (level) {
      case 'debug':
        return chalk.dim('[DEBUG]');
      case 'info':
        return chalk.blue('[INFO]');
      case 'warn':
        return chalk.yellow('[WARN]');
      case 'error':
        return chalk.red('[ERROR]');
    }
  }

  private shouldLog(level: LogLevel): boolean {
    return this.levelPriority[level] >= this.levelPriority[this.minLevel];
  }

  debug(message: string): void {
    if (this.shouldLog('debug')) {
      console.log(this.format('debug', message));
    }
  }

  info(message: string): void {
    if (this.shouldLog('info')) {
      console.log(this.format('info', message));
    }
  }

  warn(message: string): void {
    if (this.shouldLog('warn')) {
      console.warn(this.format('warn', message));
    }
  }

  error(message: string, err?: Error): void {
    if (this.shouldLog('error')) {
      const msg = err ? `${message}: ${err.message}` : message;
      console.error(this.format('error', msg));
    }
  }

  success(message: string): void {
    if (this.shouldLog('info')) {
      console.log(this.format('info', `${chalk.green('✓')} ${message}`));
    }
  }

  setLevel(level: LogLevel): void {
    this.minLevel = level;
  }

  setPrefix(prefix: string): void {
    this.prefix = prefix;
  }
}

export const logger = new Logger({ prefix: 'dot-sync', level: 'info' });

// ============================================================
// PATH UTILITIES
// ============================================================

export function normalizePath(inputPath: string): string {
  return path.normalize(path.resolve(inputPath));
}

export function isAbsolutePath(inputPath: string): boolean {
  return path.isAbsolute(inputPath);
}

export function joinPath(...parts: string[]): string {
  return path.join(...parts);
}

export function relativeToBase(filePath: string, basePath: string): string {
  const normalizedFile = normalizePath(filePath);
  const normalizedBase = normalizePath(basePath);
  return path.relative(normalizedBase, normalizedFile);
}

export function resolveFromBase(relativePath: string, basePath: string): string {
  return path.resolve(basePath, relativePath);
}

export function getFileExtension(filePath: string): string {
  return path.extname(filePath);
}

export function getFileName(filePath: string, withExtension = true): string {
  return withExtension ? path.basename(filePath) : path.basename(filePath, path.extname(filePath));
}

export function getDirectory(filePath: string): string {
  return path.dirname(filePath);
}

export function pathExists(filePath: string): boolean {
  try {
    fs.accessSync(filePath);
    return true;
  } catch {
    return false;
  }
}

export function ensureDirectory(dirPath: string): void {
  if (!fs.existsSync(dirPath)) {
    fs.mkdirSync(dirPath, { recursive: true });
  }
}

export function isDirectory(filePath: string): boolean {
  try {
    return fs.statSync(filePath).isDirectory();
  } catch {
    return false;
  }
}

export function isFile(filePath: string): boolean {
  try {
    return fs.statSync(filePath).isFile();
  } catch {
    return false;
  }
}

// ============================================================
// CHECKSUM FUNCTIONS
// ============================================================

export type ChecksumAlgorithm = 'md5' | 'sha1' | 'sha256' | 'sha512';

export function computeChecksum(
  content: string | Buffer,
  algorithm: ChecksumAlgorithm = 'sha256'
): string {
  const hash = crypto.createHash(algorithm);
  const data = typeof content === 'string' ? Buffer.from(content, 'utf-8') : content;
  return hash.update(data).digest('hex');
}

export function computeFileChecksum(filePath: string, algorithm: ChecksumAlgorithm = 'sha256'): string {
  const content = fs.readFileSync(filePath);
  return computeChecksum(content, algorithm);
}

export function computeTrackedFileChecksum(filePath: string): TrackedFile {
  const stat = fs.statSync(filePath);
  const hash = computeFileChecksum(filePath, 'md5');
  return {
    path: filePath,
    hash,
    mtime: stat.mtimeMs,
    size: stat.size,
  };
}

export function verifyChecksum(content: string | Buffer, expected: string, algorithm: ChecksumAlgorithm = 'sha256'): boolean {
  const actual = computeChecksum(content, algorithm);
  return actual === expected;
}

export function verifyFileChecksum(filePath: string, expected: string, algorithm: ChecksumAlgorithm = 'sha256'): boolean {
  const actual = computeFileChecksum(filePath, algorithm);
  return actual === expected;
}

export function hasFileChanged(filePath: string, tracked: TrackedFile): boolean {
  const stat = fs.statSync(filePath);
  const currentHash = computeFileChecksum(filePath, 'md5');
  return currentHash !== tracked.hash || stat.mtimeMs !== tracked.mtime || stat.size !== tracked.size;
}

// ============================================================
// STRING UTILITIES
// ============================================================

export function truncate(str: string, maxLength: number, ellipsis = '...'): string {
  if (str.length <= maxLength) return str;
  return str.slice(0, maxLength - ellipsis.length) + ellipsis;
}

export function pad(str: string, length: number, char = ' '): string {
  return str.padEnd(length, char);
}

export function shortenHash(hash: string, length = 7): string {
  return hash.slice(0, length);
}

// ============================================================
// MISC UTILITIES
// ============================================================

export function formatBytes(bytes: number, decimals = 2): string {
  if (bytes === 0) return '0 Bytes';
  const k = 1024;
  const dm = decimals < 0 ? 0 : decimals;
  const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
  const i = Math.floor(Math.log(Math.abs(bytes)) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
}

export function formatDuration(ms: number): string {
  if (ms < 1000) return `${ms}ms`;
  if (ms < 60000) return `${(ms / 1000).toFixed(1)}s`;
  const minutes = Math.floor(ms / 60000);
  const seconds = Math.floor((ms % 60000) / 1000);
  return `${minutes}m ${seconds}s`;
}