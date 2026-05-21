import { EventEmitter } from 'events';
import { WindowInfo } from '../types/index.js';

export type Platform = 'darwin' | 'win32' | 'linux';

export function getCurrentPlatform(): Platform {
  const platform = process.platform;
  if (platform === 'darwin' || platform === 'win32' || platform === 'linux') {
    return platform;
  }
  return 'linux';
}

export type WindowMonitorEvent = 'active-window-changed' | 'error' | 'stopped';

export interface WindowChangedEvent {
  previous: WindowInfo | null;
  current: WindowInfo;
}

export interface WindowFetcher {
  getActiveWindow(): Promise<WindowInfo | null>;
}

export class MockWindowFetcher implements WindowFetcher {
  private windows: WindowInfo[] = [];
  private currentIndex = 0;

  constructor(windows?: WindowInfo[]) {
    if (windows && windows.length > 0) {
      this.windows = windows;
    } else {
      this.windows = [
        {
          title: 'Visual Studio Code - project/src/index.ts',
          processName: 'Code',
          processPath: '/Applications/Visual Studio Code.app',
          timestamp: new Date()
        },
        {
          title: 'Chrome - GitHub',
          processName: 'Google Chrome',
          processPath: '/Applications/Google Chrome.app',
          timestamp: new Date()
        },
        {
          title: 'Terminal',
          processName: 'Terminal',
          processPath: '/Applications/Utilities/Terminal.app',
          timestamp: new Date()
        },
        {
          title: 'Safari - Apple',
          processName: 'Safari',
          processPath: '/Applications/Safari.app',
          timestamp: new Date()
        }
      ];
    }
  }

  async getActiveWindow(): Promise<WindowInfo | null> {
    const window = this.windows[this.currentIndex];
    this.currentIndex = (this.currentIndex + 1) % this.windows.length;
    return {
      ...window,
      timestamp: new Date()
    };
  }
}

export class DarwinWindowFetcher implements WindowFetcher {
  async getActiveWindow(): Promise<WindowInfo | null> {
    console.warn('[WindowMonitor] Darwin: Using mock implementation');
    return {
      title: 'Terminal',
      processName: 'Terminal',
      processPath: '/Applications/Utilities/Terminal.app',
      timestamp: new Date()
    };
  }
}

export class WindowsWindowFetcher implements WindowFetcher {
  async getActiveWindow(): Promise<WindowInfo | null> {
    console.warn('[WindowMonitor] Windows: Using mock implementation');
    return {
      title: 'Visual Studio Code',
      processName: 'Code',
      processPath: 'C:\\Program Files\\Microsoft VS Code\\Code.exe',
      timestamp: new Date()
    };
  }
}

export class LinuxWindowFetcher implements WindowFetcher {
  async getActiveWindow(): Promise<WindowInfo | null> {
    console.warn('[WindowMonitor] Linux: Using mock implementation');
    return {
      title: 'Code - /home/project/src/index.ts',
      processName: 'code',
      processPath: '/usr/bin/code',
      timestamp: new Date()
    };
  }
}

export interface WindowMonitorConfig {
  pollIntervalMs: number;
  platform?: Platform;
}

export class WindowMonitor extends EventEmitter {
  private config: WindowMonitorConfig;
  private fetcher: WindowFetcher;
  private currentWindow: WindowInfo | null = null;
  private pollInterval: NodeJS.Timeout | null = null;
  private isRunning = false;
  private consecutiveFailures = 0;
  private readonly maxConsecutiveFailures = 5;

  constructor(config: WindowMonitorConfig, fetcher?: WindowFetcher) {
    super();
    this.config = config;

    if (fetcher) {
      this.fetcher = fetcher;
    } else {
      const platform = config.platform || getCurrentPlatform();
      this.fetcher = this.createFetcher(platform);
    }
  }

  private createFetcher(platform: Platform): WindowFetcher {
    switch (platform) {
      case 'darwin':
        return new DarwinWindowFetcher();
      case 'win32':
        return new WindowsWindowFetcher();
      case 'linux':
        return new LinuxWindowFetcher();
      default:
        return new MockWindowFetcher();
    }
  }

  start(): void {
    if (this.isRunning) {
      return;
    }

    this.isRunning = true;
    this.consecutiveFailures = 0;

    this.poll();

    this.pollInterval = setInterval(() => {
      this.poll();
    }, this.config.pollIntervalMs);

    if (this.pollInterval.unref) {
      this.pollInterval.unref();
    }
  }

  stop(): void {
    this.isRunning = false;

    if (this.pollInterval) {
      clearInterval(this.pollInterval);
      this.pollInterval = null;
    }

    this.emit('stopped');
  }

  getCurrentWindow(): WindowInfo | null {
    return this.currentWindow;
  }

  isActive(): boolean {
    return this.isRunning;
  }

  private async poll(): Promise<void> {
    try {
      const window = await this.fetcher.getActiveWindow();

      this.consecutiveFailures = 0;

      if (!window) {
        return;
      }

      if (this.hasWindowChanged(window)) {
        const previous = this.currentWindow;
        this.currentWindow = window;

        this.emit('active-window-changed', {
          previous,
          current: window
        });
      }
    } catch (error) {
      this.consecutiveFailures++;
      const errorMessage = error instanceof Error ? error.message : 'Unknown error';

      this.emit('error', new Error(`Window poll failed: ${errorMessage}`));

      if (this.consecutiveFailures >= this.maxConsecutiveFailures) {
        console.error(
          `[WindowMonitor] ${this.consecutiveFailures} consecutive failures - alerting user`
        );
      }
    }
  }

  private hasWindowChanged(newWindow: WindowInfo): boolean {
    if (!this.currentWindow) {
      return true;
    }

    return (
      this.currentWindow.processName !== newWindow.processName ||
      this.currentWindow.title !== newWindow.title
    );
  }
}

export { WindowInfo };