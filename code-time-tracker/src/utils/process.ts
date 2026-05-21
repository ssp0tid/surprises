import { WindowInfo } from '../types/index.js';

export function extractProcessName(windowInfo: WindowInfo): string {
  const { processName, processPath } = windowInfo;

  if (processName && processName.trim().length > 0) {
    return normalizeProcessName(processName);
  }

  if (processPath && processPath.trim().length > 0) {
    return extractNameFromPath(processPath);
  }

  return 'unknown';
}

export function normalizeProcessName(processName: string): string {
  return processName
    .toLowerCase()
    .trim()
    .replace(/\.(exe|app|sh|bin)$/i, '');
}

export function extractNameFromPath(path: string): string {
  const normalized = path.trim();

  if (normalized.includes('\\')) {
    const parts = normalized.split('\\');
    const filename = parts[parts.length - 1];
    return normalizeProcessName(filename);
  }

  const parts = normalized.split('/');
  const filename = parts[parts.length - 1];
  return normalizeProcessName(filename);
}

export function normalizePath(path: string): string {
  if (!path) return '';

  let normalized = path.trim();

  if (normalized.startsWith('~')) {
    const home = process.env.HOME || process.env.USERPROFILE || '';
    normalized = normalized.replace(/^~/, home);
  }

  normalized = normalized.replace(/\\/g, '/');
  normalized = normalized.replace(/\/+$/, '');
  normalized = normalized.replace(/\/+/g, '/');

  return normalized;
}

export function createCacheKey(windowInfo: WindowInfo): string {
  const processName = extractProcessName(windowInfo);
  const title = windowInfo.title || '';
  return `${processName}:${title}`;
}

export class LRUCache<K, V> {
  private cache: Map<K, V>;
  private maxSize: number;

  constructor(maxSize: number = 100) {
    this.maxSize = maxSize;
    this.cache = new Map();
  }

  has(key: K): boolean {
    return this.cache.has(key);
  }

  get(key: K): V | undefined {
    if (!this.cache.has(key)) return undefined;

    const value = this.cache.get(key);
    this.cache.delete(key);
    this.cache.set(key, value!);
    return value;
  }

  set(key: K, value: V): void {
    if (this.cache.has(key)) {
      this.cache.delete(key);
    }

    if (this.cache.size >= this.maxSize) {
      const firstKey = this.cache.keys().next().value;
      this.cache.delete(firstKey);
    }

    this.cache.set(key, value);
  }

  clear(): void {
    this.cache.clear();
  }

  size(): number {
    return this.cache.size;
  }
}