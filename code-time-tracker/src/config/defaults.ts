/**
 * Code Time Tracker - Default Configuration
 * Matches PLAN.md Section 12
 */

import {
  type AppConfig,
  type DaemonConfig,
  type ApiConfig,
  type LoggingConfig,
  type StorageConfig,
  LogLevel,
} from '../types/index.js';

export const daemonDefaults: DaemonConfig = {
  pollIntervalMs: 5000,
  idleThresholdSeconds: 300,
  idleCheckIntervalMs: 30000,
  maxSessionDurationHours: 8,
  gracePeriodMs: 5000,
};

export const apiDefaults: ApiConfig = {
  port: 3737,
  host: 'localhost',
};

export const loggingDefaults: LoggingConfig = {
  level: LogLevel.INFO,
  maxFiles: 7,
  maxSizeMb: 50,
};

export const storageDefaults: StorageConfig = {
  dbPath: '~/.code-time-tracker/data.db',
  backupPath: '~/.code-time-tracker/backups',
};

export const defaults: AppConfig = {
  daemon: daemonDefaults,
  api: apiDefaults,
  logging: loggingDefaults,
  storage: storageDefaults,
};

export default defaults;