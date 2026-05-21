/**
 * Storage management: file store and manifest handling
 */

import * as fs from 'fs';
import * as path from 'path';
import { Manifest, ManifestMeta, TrackedFile } from '../types';
import { computeChecksum, hasFileChanged, logger } from '../utils';

const MANIFEST_FILENAME = '.dot-sync-manifest.json';
const STORAGE_DIR = '.dot-sync';

export class FileStore {
  private basePath: string;
  private storagePath: string;

  constructor(basePath: string) {
    this.basePath = basePath;
    this.storagePath = path.join(basePath, STORAGE_DIR);
    this.ensureStorage();
  }

  private ensureStorage(): void {
    if (!fs.existsSync(this.storagePath)) {
      fs.mkdirSync(this.storagePath, { recursive: true });
    }
  }

  getBasePath(): string {
    return this.basePath;
  }

  getStoragePath(): string {
    return this.storagePath;
  }

  private getFilePath(filename: string): string {
    return path.join(this.storagePath, filename);
  }

  read<T>(filename: string): T | null {
    const filePath = this.getFilePath(filename);
    try {
      const content = fs.readFileSync(filePath, 'utf-8');
      return JSON.parse(content) as T;
    } catch (err) {
      if ((err as NodeJS.ErrnoException).code === 'ENOENT') {
        return null;
      }
      throw err;
    }
  }

  write<T>(filename: string, data: T): void {
    const filePath = this.getFilePath(filename);
    const content = JSON.stringify(data, null, 2);
    fs.writeFileSync(filePath, content, 'utf-8');
  }

  exists(filename: string): boolean {
    return fs.existsSync(this.getFilePath(filename));
  }

  delete(filename: string): void {
    const filePath = this.getFilePath(filename);
    if (fs.existsSync(filePath)) {
      fs.unlinkSync(filePath);
    }
  }

  listFiles(): string[] {
    try {
      return fs.readdirSync(this.storagePath);
    } catch {
      return [];
    }
  }
}

export class ManifestManager {
  private fileStore: FileStore;
  private manifest: Manifest | null = null;

  constructor(basePath: string) {
    this.fileStore = new FileStore(basePath);
    this.load();
  }

  private load(): void {
    this.manifest = this.fileStore.read<Manifest>(MANIFEST_FILENAME);
  }

  private save(): void {
    if (this.manifest) {
      this.fileStore.write(MANIFEST_FILENAME, this.manifest);
    }
  }

  getManifest(): Manifest | null {
    return this.manifest;
  }

  init(sourceDir: string, repoUrl: string, branch: string): Manifest {
    this.manifest = {
      version: '1.0.0',
      updatedAt: Date.now(),
      files: [],
      meta: {
        sourceDir,
        repoUrl,
        branch,
      },
    };
    this.save();
    logger.info(`Initialized manifest at ${this.fileStore.getStoragePath()}`);
    return this.manifest;
  }

  isInitialized(): boolean {
    return this.manifest !== null;
  }

  updateMeta(meta: Partial<ManifestMeta>): void {
    if (!this.manifest) {
      throw new Error('Manifest not initialized');
    }
    this.manifest.meta = { ...this.manifest.meta, ...meta };
    this.manifest.updatedAt = Date.now();
    this.save();
  }

  addFile(filePath: string, tracked: TrackedFile): void {
    if (!this.manifest) {
      throw new Error('Manifest not initialized');
    }
    const existingIndex = this.manifest.files.findIndex(f => f.path === filePath);
    if (existingIndex >= 0) {
      this.manifest.files[existingIndex] = tracked;
    } else {
      this.manifest.files.push(tracked);
    }
    this.manifest.updatedAt = Date.now();
    this.save();
    logger.debug(`Added/updated file: ${filePath}`);
  }

  removeFile(filePath: string): void {
    if (!this.manifest) {
      throw new Error('Manifest not initialized');
    }
    const index = this.manifest.files.findIndex(f => f.path === filePath);
    if (index >= 0) {
      this.manifest.files.splice(index, 1);
      this.manifest.updatedAt = Date.now();
      this.save();
      logger.debug(`Removed file: ${filePath}`);
    }
  }

  getTrackedFile(filePath: string): TrackedFile | undefined {
    return this.manifest?.files.find(f => f.path === filePath);
  }

  getAllTracked(): TrackedFile[] {
    return this.manifest?.files || [];
  }

  isTracked(filePath: string): boolean {
    return this.manifest?.files.some(f => f.path === filePath) || false;
  }

  filterChanged(trackedList: TrackedFile[]): { changed: TrackedFile[]; unchanged: TrackedFile[]; missing: TrackedFile[] } {
    const changed: TrackedFile[] = [];
    const unchanged: TrackedFile[] = [];
    const missing: TrackedFile[] = [];

    for (const tracked of trackedList) {
      if (!fs.existsSync(tracked.path)) {
        missing.push(tracked);
      } else if (hasFileChanged(tracked.path, tracked)) {
        changed.push(tracked);
      } else {
        unchanged.push(tracked);
      }
    }

    return { changed, unchanged, missing };
  }

  getStats(): { totalFiles: number; totalSize: number } {
    const files = this.manifest?.files || [];
    return {
      totalFiles: files.length,
      totalSize: files.reduce((sum, f) => sum + f.size, 0),
    };
  }

  reset(): void {
    this.manifest = null;
    this.fileStore.delete(MANIFEST_FILENAME);
    logger.info('Manifest reset');
  }
}

// Export a singleton for the working directory
let globalManifestManager: ManifestManager | null = null;

export function initManifestManager(basePath: string): ManifestManager {
  globalManifestManager = new ManifestManager(basePath);
  return globalManifestManager;
}

export function getManifestManager(): ManifestManager | null {
  return globalManifestManager;
}