import * as fs from 'fs';
import * as path from 'path';
import * as crypto from 'crypto';

export interface TrackedFile {
  relativePath: string;
  absolutePath: string;
  checksum: string;
  lastModified: number;
  size: number;
}

export interface TrackerState {
  files: Record<string, TrackedFile>;
  lastSync: number;
}

export class FileTracker {
  private state: TrackerState;
  private basePath: string;

  constructor(basePath: string, state?: TrackerState) {
    this.basePath = path.resolve(basePath);
    this.state = state || { files: {}, lastSync: Date.now() };
  }

  private computeChecksum(filePath: string): string {
    const content = fs.readFileSync(filePath);
    return crypto.createHash('sha256').update(content).digest('hex');
  }

  trackFile(relativePath: string): TrackedFile {
    const absolutePath = path.resolve(this.basePath, relativePath);
    
    if (!fs.existsSync(absolutePath)) {
      throw new Error(`File not found: ${absolutePath}`);
    }

    const stats = fs.statSync(absolutePath);
    const checksum = this.computeChecksum(absolutePath);

    const trackedFile: TrackedFile = {
      relativePath,
      absolutePath,
      checksum,
      lastModified: stats.mtimeMs,
      size: stats.size,
    };

    this.state.files[relativePath] = trackedFile;
    return trackedFile;
  }

  async trackPatterns(patterns: string[]): Promise<TrackedFile[]> {
    const tracked: TrackedFile[] = [];

    for (const pattern of patterns) {
      const matches = this.globMatch(pattern);
      for (const match of matches) {
        try {
          const trackedFile = this.trackFile(match);
          tracked.push(trackedFile);
        } catch {
        }
      }
    }

    return tracked;
  }

  private globMatch(pattern: string): string[] {
    const results: string[] = [];
    const normalizedPattern = pattern.replace(/^\.\//, '');
    
    if (normalizedPattern.includes('*')) {
      const parts = normalizedPattern.split('/');
      let searchPath = this.basePath;
      const patternParts: string[] = [];

      for (const part of parts) {
        if (part.includes('*')) {
          patternParts.push(part);
        } else if (part !== '') {
          searchPath = path.join(searchPath, part);
        }
      }

      if (fs.existsSync(searchPath)) {
        this.walkDir(searchPath, patternParts, results);
      }
    } else {
      const fullPath = path.join(this.basePath, normalizedPattern);
      if (fs.existsSync(fullPath) && fs.statSync(fullPath).isFile()) {
        results.push(normalizedPattern);
      }
    }

    return results;
  }

  private walkDir(dir: string, patternParts: string[], results: string[], baseRelative = ''): void {
    if (!fs.existsSync(dir)) return;

    const entries = fs.readdirSync(dir, { withFileTypes: true });
    const currentPattern = patternParts[0];
    const isGlob = currentPattern?.includes('*');
    const remainingPatterns = patternParts.slice(1);

    for (const entry of entries) {
      const relativePath = baseRelative ? `${baseRelative}/${entry.name}` : entry.name;
      
      if (entry.isDirectory()) {
        if (isGlob || remainingPatterns.length > 0) {
          this.walkDir(
            path.join(dir, entry.name),
            isGlob ? patternParts : remainingPatterns,
            results,
            relativePath
          );
        }
      } else if (entry.isFile()) {
        if (!isGlob || this.matchGlob(entry.name, currentPattern)) {
          if (remainingPatterns.length === 0) {
            results.push(relativePath);
          }
        }
      }
    }
  }

  private matchGlob(filename: string, pattern: string): boolean {
    const regexPattern = pattern
      .replace(/\./g, '\\.')
      .replace(/\*/g, '.*')
      .replace(/\?/g, '.');
    return new RegExp(`^${regexPattern}$`).test(filename);
  }

  hasChanged(relativePath: string): boolean {
    const tracked = this.state.files[relativePath];
    if (!tracked) return true;

    if (!fs.existsSync(tracked.absolutePath)) return true;

    const stats = fs.statSync(tracked.absolutePath);
    if (stats.mtimeMs !== tracked.lastModified) {
      return this.computeChecksum(tracked.absolutePath) !== tracked.checksum;
    }

    return false;
  }

  getChanges(): { added: string[]; modified: string[]; deleted: string[] } {
    const added: string[] = [];
    const modified: string[] = [];
    const deleted: string[] = [];

    for (const [relativePath, tracked] of Object.entries(this.state.files)) {
      if (!fs.existsSync(tracked.absolutePath)) {
        deleted.push(relativePath);
      } else if (this.hasChanged(relativePath)) {
        modified.push(relativePath);
      }
    }

    return { added, modified, deleted };
  }

  getState(): TrackerState {
    return this.state;
  }

  setState(state: TrackerState): void {
    this.state = state;
  }

  markSynced(): void {
    this.state.lastSync = Date.now();
  }
}