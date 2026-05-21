import { EventEmitter } from 'events';
import { IdleState, IdleConfig } from '../types/index.js';
import { getCurrentPlatform, Platform } from './window-monitor.js';

export type IdleDetectorEvent = 'idle-detected' | 'activity-resumed' | 'error' | 'stopped';

export interface IdleDetectedEvent {
  state: IdleState.IDLE;
  idleTimeMs: number;
  timestamp: Date;
}

export interface ActivityResumedEvent {
  state: IdleState.ACTIVE;
  previousIdleTimeMs: number;
  timestamp: Date;
}

export interface IdleFetcher {
  getIdleTimeMs(): Promise<number>;
}

export class MockIdleFetcher implements IdleFetcher {
  private idleTimeMs = 0;
  private incrementBy = 0;
  private readonly maxIdleTime: number;

  constructor(maxIdleTime: number = 300000) {
    this.maxIdleTime = maxIdleTime;
  }

  async getIdleTimeMs(): Promise<number> {
    this.idleTimeMs += this.incrementBy;
    if (this.idleTimeMs > this.maxIdleTime) {
      this.idleTimeMs = this.maxIdleTime;
    }
    return this.idleTimeMs;
  }

  setIdleTime(ms: number): void {
    this.idleTimeMs = ms;
  }

  increment(ms: number): void {
    this.incrementBy = ms;
  }
}

export class DarwinIdleFetcher implements IdleFetcher {
  async getIdleTimeMs(): Promise<number> {
    console.warn('[IdleDetector] Darwin: Using mock implementation');
    return this.mockGetIdleTime();
  }

  private mockGetIdleTime(): number {
    return 0;
  }
}

export class WindowsIdleFetcher implements IdleFetcher {
  async getIdleTimeMs(): Promise<number> {
    console.warn('[IdleDetector] Windows: Using mock implementation');
    return this.mockGetIdleTime();
  }

  private mockGetIdleTime(): number {
    return 0;
  }
}

export class LinuxIdleFetcher implements IdleFetcher {
  async getIdleTimeMs(): Promise<number> {
    console.warn('[IdleDetector] Linux: Using mock implementation');
    return this.mockGetIdleTime();
  }

  private mockGetIdleTime(): number {
    return 0;
  }
}

export interface IdleDetectorConfig extends IdleConfig {
  platform?: Platform;
}

export class IdleDetector extends EventEmitter {
  private config: IdleDetectorConfig;
  private fetcher: IdleFetcher;
  private state: IdleState = IdleState.ACTIVE;
  private checkInterval: NodeJS.Timeout | null = null;
  private isRunning = false;
  private gracePeriodTimer: NodeJS.Timeout | null = null;
  private lastActivityTime: Date = new Date();
  private totalIdleTimeMs = 0;

  constructor(config: IdleDetectorConfig, fetcher?: IdleFetcher) {
    super();
    this.config = {
      thresholdSeconds: config.thresholdSeconds ?? 300,
      checkIntervalMs: config.checkIntervalMs ?? 30000,
      gracePeriodMs: config.gracePeriodMs ?? 5000
    };

    if (fetcher) {
      this.fetcher = fetcher;
    } else {
      const platform = config.platform || getCurrentPlatform();
      this.fetcher = this.createFetcher(platform);
    }
  }

  private createFetcher(platform: Platform): IdleFetcher {
    switch (platform) {
      case 'darwin':
        return new DarwinIdleFetcher();
      case 'win32':
        return new WindowsIdleFetcher();
      case 'linux':
        return new LinuxIdleFetcher();
      default:
        return new MockIdleFetcher();
    }
  }

  start(): void {
    if (this.isRunning) {
      return;
    }

    this.isRunning = true;
    this.lastActivityTime = new Date();

    this.check();

    this.checkInterval = setInterval(() => {
      this.check();
    }, this.config.checkIntervalMs);

    if (this.checkInterval.unref) {
      this.checkInterval.unref();
    }
  }

  stop(): void {
    this.isRunning = false;

    if (this.checkInterval) {
      clearInterval(this.checkInterval);
      this.checkInterval = null;
    }

    if (this.gracePeriodTimer) {
      clearTimeout(this.gracePeriodTimer);
      this.gracePeriodTimer = null;
    }

    this.emit('stopped');
  }

  getState(): IdleState {
    return this.state;
  }

  isActive(): boolean {
    return this.isRunning;
  }

  getLastActivityTime(): Date {
    return this.lastActivityTime;
  }

  private async check(): Promise<void> {
    try {
      const idleTimeMs = await this.fetcher.getIdleTimeMs();

      if (this.state === IdleState.ACTIVE) {
        if (idleTimeMs >= this.config.thresholdSeconds * 1000) {
          this.handleIdleDetected(idleTimeMs);
        }
      } else if (this.state === IdleState.IDLE) {
        if (idleTimeMs < this.config.thresholdSeconds * 1000) {
          this.handleActivityResumed(idleTimeMs);
        }
      }
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Unknown error';
      this.emit('error', new Error(`Idle check failed: ${errorMessage}`));
    }
  }

  private handleIdleDetected(idleTimeMs: number): void {
    const thresholdMs = this.config.thresholdSeconds * 1000;

    if (this.gracePeriodTimer) {
      clearTimeout(this.gracePeriodTimer);
      this.gracePeriodTimer = null;
    }

    this.gracePeriodTimer = setTimeout(() => {
      if (this.state === IdleState.ACTIVE) {
        this.state = IdleState.IDLE;
        this.totalIdleTimeMs = idleTimeMs;

        this.emit('idle-detected', {
          state: IdleState.IDLE,
          idleTimeMs,
          timestamp: new Date()
        });
      }
      this.gracePeriodTimer = null;
    }, this.config.gracePeriodMs);
  }

  private handleActivityResumed(idleTimeMs: number): void {
    if (this.gracePeriodTimer) {
      clearTimeout(this.gracePeriodTimer);
      this.gracePeriodTimer = null;
    }

    this.state = IdleState.ACTIVE;
    const previousIdleTime = this.totalIdleTimeMs;
    this.totalIdleTimeMs = 0;
    this.lastActivityTime = new Date();

    this.emit('activity-resumed', {
      state: IdleState.ACTIVE,
      previousIdleTimeMs: previousIdleTime,
      timestamp: new Date()
    });
  }
}

export { IdleState, IdleConfig };