import * as fs from 'fs';
import * as path from 'path';
import { FileTracker, TrackedFile, TrackerState } from './tracker';
import { Encryptor } from './encryptor';

export interface SyncEngineConfig {
  sourceDir: string;
  destDir: string;
  key: string;
  excludePatterns?: string[];
}

export interface ChangeInfo {
  path: string;
  action: 'added' | 'modified' | 'deleted' | 'unchanged';
}

export interface SyncResult {
  success: boolean;
  filesProcessed: number;
  changes: ChangeInfo[];
  errors: string[];
}

export class SyncEngine {
  private tracker: FileTracker;
  private encryptor: Encryptor;
  private config: {
    sourceDir: string;
    destDir: string;
    key: string;
    excludePatterns: string[];
  };

  constructor(config: SyncEngineConfig) {
    this.config = {
      sourceDir: path.resolve(config.sourceDir),
      destDir: path.resolve(config.destDir),
      key: config.key,
      excludePatterns: config.excludePatterns || [],
    };

    this.tracker = new FileTracker(this.config.sourceDir);
    this.encryptor = new Encryptor(this.config.key);
  }

  private matchesExcludePatterns(filePath: string): boolean {
    const relativePath = path.relative(this.config.sourceDir, filePath);
    for (const pattern of this.config.excludePatterns) {
      if (this.globMatch(relativePath, pattern)) {
        return true;
      }
    }
    return false;
  }

  private globMatch(str: string, pattern: string): boolean {
    const regexPattern = pattern
      .replace(/\./g, '\\.')
      .replace(/\*\*/g, '((?:.*/)?)')
      .replace(/\*/g, '[^/]*')
      .replace(/\?/g, '.');

    return new RegExp(`^${regexPattern}$`).test(str);
  }

  private getRelativePath(filePath: string): string {
    return path.relative(this.config.sourceDir, filePath);
  }

  private getDestPath(filePath: string): string {
    const relativePath = this.getRelativePath(filePath);
    return path.join(this.config.destDir, relativePath);
  }

  async sync(): Promise<SyncResult> {
    const result: SyncResult = {
      success: true,
      filesProcessed: 0,
      changes: [],
      errors: [],
    };

    try {
      const sourceFiles = this.getSourceFiles();

      for (const filePath of sourceFiles) {
        if (this.matchesExcludePatterns(filePath)) {
          continue;
        }

        const relativePath = this.getRelativePath(filePath);

        if (!this.tracker.hasChanged(relativePath)) {
          result.changes.push({
            path: filePath,
            action: 'unchanged',
          });
          continue;
        }

        try {
          await this.encryptFile(filePath, this.getDestPath(filePath));
          this.tracker.trackFile(relativePath);
          result.filesProcessed++;
          result.changes.push({
            path: filePath,
            action: 'modified',
          });
        } catch (error) {
          const message = error instanceof Error ? error.message : 'Unknown error';
          result.errors.push(`Failed to sync ${filePath}: ${message}`);
        }
      }

      if (result.errors.length > 0) {
        result.success = false;
      }

      this.tracker.markSynced();
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Unknown error';
      result.success = false;
      result.errors.push(`Sync failed: ${message}`);
    }

    return result;
  }

  private getSourceFiles(): string[] {
    const files: string[] = [];
    this.scanDirectory(this.config.sourceDir, files);
    return files;
  }

  private scanDirectory(dir: string, files: string[]): void {
    const entries = fs.readdirSync(dir, { withFileTypes: true });
    for (const entry of entries) {
      const fullPath = path.join(dir, entry.name);
      if (entry.isFile() && !this.matchesExcludePatterns(fullPath)) {
        files.push(fullPath);
      } else if (entry.isDirectory() && !entry.name.startsWith('.')) {
        this.scanDirectory(fullPath, files);
      }
    }
  }

  encryptFile(srcPath: string, destPath: string): void {
    const resolvedSrc = path.resolve(srcPath);
    const resolvedDest = path.resolve(destPath);

    if (!fs.existsSync(resolvedSrc)) {
      throw new Error(`Source file does not exist: ${srcPath}`);
    }

    if (this.matchesExcludePatterns(resolvedSrc)) {
      throw new Error(`File matches exclude pattern: ${srcPath}`);
    }

    const stats = fs.statSync(resolvedSrc);
    if (!stats.isFile()) {
      throw new Error(`Source is not a file: ${srcPath}`);
    }

    try {
      const fileContent = fs.readFileSync(resolvedSrc, 'utf8');
      const encrypted = this.encryptor.encrypt(fileContent);

      const output = [
        encrypted.salt,
        encrypted.iv,
        encrypted.tag,
        encrypted.ciphertext,
      ].join('.');

      const destDir = path.dirname(resolvedDest);
      if (!fs.existsSync(destDir)) {
        fs.mkdirSync(destDir, { recursive: true });
      }

      fs.writeFileSync(resolvedDest, output, 'utf8');
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Unknown error';
      throw new Error(`Failed to encrypt ${srcPath}: ${message}`);
    }
  }

  decryptFile(srcPath: string, destPath: string): void {
    const resolvedSrc = path.resolve(srcPath);
    const resolvedDest = path.resolve(destPath);

    if (!fs.existsSync(resolvedSrc)) {
      throw new Error(`Encrypted file does not exist: ${srcPath}`);
    }

    try {
      const encryptedContent = fs.readFileSync(resolvedSrc, 'utf8');
      const parts = encryptedContent.split('.');

      if (parts.length !== 4) {
        throw new Error('Invalid encrypted file format');
      }

      const encrypted = {
        salt: parts[0],
        iv: parts[1],
        tag: parts[2],
        ciphertext: parts[3],
        iterations: 100000,
      };

      const decrypted = this.encryptor.decrypt(encrypted);

      const destDir = path.dirname(resolvedDest);
      if (!fs.existsSync(destDir)) {
        fs.mkdirSync(destDir, { recursive: true });
      }

      fs.writeFileSync(resolvedDest, decrypted, 'utf8');
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Unknown error';
      throw new Error(`Failed to decrypt ${srcPath}: ${message}`);
    }
  }

  listChanges(): ChangeInfo[] {
    const changes: ChangeInfo[] = [];
    const sourceFiles = this.getSourceFiles();
    const trackedChanges = this.tracker.getChanges();

    for (const filePath of sourceFiles) {
      if (this.matchesExcludePatterns(filePath)) {
        continue;
      }

      const relativePath = this.getRelativePath(filePath);

      if (!fs.existsSync(filePath)) {
        changes.push({
          path: filePath,
          action: 'deleted',
        });
      } else if (trackedChanges.modified.includes(relativePath)) {
        changes.push({
          path: filePath,
          action: 'modified',
        });
      }
    }

    for (const deleted of trackedChanges.deleted) {
      const absolutePath = path.join(this.config.sourceDir, deleted);
      if (!this.matchesExcludePatterns(absolutePath)) {
        changes.push({
          path: absolutePath,
          action: 'deleted',
        });
      }
    }

    return changes;
  }

  addFile(filePath: string): TrackedFile {
    const resolvedPath = path.resolve(filePath);

    if (!fs.existsSync(resolvedPath)) {
      throw new Error(`File does not exist: ${filePath}`);
    }

    const stats = fs.statSync(resolvedPath);
    if (!stats.isFile()) {
      throw new Error(`Not a file: ${filePath}`);
    }

    const relativePath = this.getRelativePath(resolvedPath);
    return this.tracker.trackFile(relativePath);
  }

  removeFile(filePath: string): boolean {
    const resolvedPath = path.resolve(filePath);
    const relativePath = this.getRelativePath(resolvedPath);
    const state = this.tracker.getState();
    
    if (state.files[relativePath]) {
      delete state.files[relativePath];
      this.tracker.setState(state);
      return true;
    }
    return false;
  }

  getTracker(): FileTracker {
    return this.tracker;
  }

  getConfig(): Readonly<SyncEngineConfig> {
    return {
      sourceDir: this.config.sourceDir,
      destDir: this.config.destDir,
      key: this.config.key,
      excludePatterns: this.config.excludePatterns,
    };
  }
}