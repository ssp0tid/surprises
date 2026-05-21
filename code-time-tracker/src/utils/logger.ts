import * as fs from 'fs';
import * as path from 'path';
import * as os from 'os';

export enum LogLevel {
  DEBUG = 0,
  INFO = 1,
  WARN = 2,
  ERROR = 3
}

export interface LogEntry {
  timestamp: string;
  level: LogLevel;
  module: string;
  message: string;
  context?: Record<string, unknown>;
}

export interface LoggerConfig {
  logDir: string;
  level: LogLevel;
  maxFiles: number;
  maxSizeMb: number;
}

export interface SessionRecord {
  id: number;
  projectId: string | null;
  startTime: Date;
  endTime: Date | null;
  durationSeconds: number | null;
  windowTitle: string | null;
  createdAt: Date;
}

const MAX_SESSION_MS = 8 * 60 * 60 * 1000;

export async function recoverOrphanedSessions(
  getOrphans: () => Promise<SessionRecord[]>,
  updateSession: (session: SessionRecord) => Promise<void>
): Promise<number> {
  const orphans = await getOrphans();
  const now = new Date();
  let recoveredCount = 0;

  for (const session of orphans) {
    if (!session.startTime) continue;

    const maxEndTime = new Date(session.startTime.getTime() + MAX_SESSION_MS);
    const cappedEndTime = now < maxEndTime ? now : maxEndTime;

    session.endTime = cappedEndTime;
    session.durationSeconds = Math.floor(
      (cappedEndTime.getTime() - session.startTime.getTime()) / 1000
    );

    await updateSession(session);
    recoveredCount++;
  }

  return recoveredCount;
}

class Logger {
  private logDir: string;
  private level: LogLevel;
  private maxFiles: number;
  private maxSizeBytes: number;
  private currentLogFile: string;
  private currentLogSize: number = 0;
  private writeStream: fs.WriteStream | null = null;
  private logFileDate: string;
  private initPromise: Promise<void> | null = null;

  constructor(config: Partial<LoggerConfig> = {}) {
    const homeDir = os.homedir();
    this.logDir = config.logDir ?? path.join(homeDir, '.code-time-tracker', 'logs');
    this.level = config.level ?? LogLevel.INFO;
    this.maxFiles = config.maxFiles ?? 7;
    this.maxSizeBytes = (config.maxSizeMb ?? 50) * 1024 * 1024;
    this.logFileDate = this.getDateString(new Date());
    this.currentLogFile = this.getLogFilePath(this.logFileDate);
    this.initPromise = this.initialize();
  }

  private getDateString(date: Date): string {
    return date.toISOString().split('T')[0];
  }

  private getLogFilePath(date: string): string {
    return path.join(this.logDir, `app-${date}.log`);
  }

  private async initialize(): Promise<void> {
    await fs.promises.mkdir(this.logDir, { recursive: true });
    await this.rotateLogsIfNeeded();
    await this.openWriteStream();
  }

  private async openWriteStream(): Promise<void> {
    if (this.writeStream) {
      this.writeStream.end();
    }

    this.writeStream = fs.createWriteStream(this.currentLogFile, {
      flags: 'a',
      encoding: 'utf8'
    });

    try {
      const stats = await fs.promises.stat(this.currentLogFile);
      this.currentLogSize = stats.size;
    } catch {
      this.currentLogSize = 0;
    }
  }

  private async rotateLogsIfNeeded(): Promise<void> {
    const today = this.getDateString(new Date());

    if (this.logFileDate !== today) {
      await this.closeStream();
      this.logFileDate = today;
      this.currentLogFile = this.getLogFilePath(today);
      this.currentLogSize = 0;
      await this.openWriteStream();
    }

    if (this.currentLogSize >= this.maxSizeBytes) {
      await this.closeStream();
      const rotatedPath = this.currentLogFile.replace(
        '.log',
        `-${Date.now()}.log`
      );
      await fs.promises.rename(this.currentLogFile, rotatedPath);
      this.currentLogSize = 0;
      await this.openWriteStream();
    }

    await this.cleanupOldLogs();
  }

  private async cleanupOldLogs(): Promise<void> {
    try {
      const files = await fs.promises.readdir(this.logDir);
      const logFileInfos = await Promise.all(
        files
          .filter(f => f.startsWith('app-') && f.endsWith('.log'))
          .map(async f => {
            const filePath = path.join(this.logDir, f);
            const stats = await fs.promises.stat(filePath);
            return { path: filePath, mtime: stats.mtime };
          })
      );

      logFileInfos.sort((a, b) => b.mtime.getTime() - a.mtime.getTime());

      const toDelete = logFileInfos.slice(this.maxFiles);
      for (const file of toDelete) {
        try {
          await fs.promises.unlink(file.path);
        } catch {}
      }
    } catch {}
  }

  private async closeStream(): Promise<void> {
    return new Promise(resolve => {
      if (this.writeStream) {
        this.writeStream.end(() => {
          this.writeStream = null;
          resolve();
        });
      } else {
        resolve();
      }
    });
  }

  private formatEntry(entry: LogEntry): string {
    const logObject = {
      timestamp: entry.timestamp,
      level: LogLevel[entry.level],
      module: entry.module,
      message: entry.message
    };

    if (entry.context) {
      return JSON.stringify({ ...logObject, context: entry.context }) + '\n';
    }

    return JSON.stringify(logObject) + '\n';
  }

  private async ensureInitialized(): Promise<void> {
    if (this.initPromise) {
      await this.initPromise;
      this.initPromise = null;
    }
  }

  private async write(entry: LogEntry): Promise<void> {
    await this.ensureInitialized();

    if (entry.level < this.level) {
      return;
    }

    await this.rotateLogsIfNeeded();

    const formatted = this.formatEntry(entry);

    if (this.writeStream) {
      return new Promise((resolve, reject) => {
        this.writeStream!.write(formatted, err => {
          if (err) {
            reject(err);
          } else {
            this.currentLogSize += formatted.length;
            resolve();
          }
        });
      });
    }
  }

  async debug(
    module: string,
    message: string,
    context?: Record<string, unknown>
  ): Promise<void> {
    await this.write({
      timestamp: new Date().toISOString(),
      level: LogLevel.DEBUG,
      module,
      message,
      context
    });
  }

  async info(
    module: string,
    message: string,
    context?: Record<string, unknown>
  ): Promise<void> {
    await this.write({
      timestamp: new Date().toISOString(),
      level: LogLevel.INFO,
      module,
      message,
      context
    });
  }

  async warn(
    module: string,
    message: string,
    context?: Record<string, unknown>
  ): Promise<void> {
    await this.write({
      timestamp: new Date().toISOString(),
      level: LogLevel.WARN,
      module,
      message,
      context
    });
  }

  async error(
    module: string,
    message: string,
    context?: Record<string, unknown>
  ): Promise<void> {
    await this.write({
      timestamp: new Date().toISOString(),
      level: LogLevel.ERROR,
      module,
      message,
      context
    });
  }

  async flush(): Promise<void> {
    await this.closeStream();
  }

  getLogDir(): string {
    return this.logDir;
  }

  setLevel(level: LogLevel): void {
    this.level = level;
  }
}

let loggerInstance: Logger | null = null;

export function createLogger(config?: Partial<LoggerConfig>): Logger {
  loggerInstance = new Logger(config);
  return loggerInstance;
}

export function getLogger(): Logger {
  if (!loggerInstance) {
    loggerInstance = new Logger();
  }
  return loggerInstance;
}

export default {
  LogLevel,
  createLogger,
  getLogger,
  recoverOrphanedSessions
};