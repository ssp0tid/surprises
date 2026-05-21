/**
 * Code Time Tracker - TypeScript Type Definitions
 * Matches PLAN.md Section 6
 */

// =============================================================================
// Core Data Types
// =============================================================================

/**
 * Information about the currently active window
 */
export interface WindowInfo {
  title: string;
  processName: string;
  processPath: string;
  timestamp: Date;
}

/**
 * A continuous time session tracking focused work
 */
export interface TimeSession {
  id?: number;
  projectId: string;
  startTime: Date;
  endTime?: Date | null;
  durationSeconds?: number | null;
  windowTitle?: string | null;
  createdAt?: Date;
}

/**
 * A user-defined project categorization
 */
export interface Project {
  id: string;
  name: string;
  color: string;
  keywords: string[];
  createdAt?: Date;
  updatedAt?: Date;
}

/**
 * An idle period detected by the system
 */
export interface IdlePeriod {
  id?: number;
  startTime: Date;
  endTime: Date;
  durationSeconds: number;
}

// =============================================================================
// Configuration Types
// =============================================================================

/**
 * Idle detection configuration
 */
export interface IdleConfig {
  thresholdSeconds: number;
  checkIntervalMs: number;
  gracePeriodMs: number;
}

/**
 * Daemon configuration options
 */
export interface DaemonConfig {
  pollIntervalMs: number;
  idleThresholdSeconds: number;
  idleCheckIntervalMs: number;
  maxSessionDurationHours: number;
  gracePeriodMs: number;
}

/**
 * API server configuration
 */
export interface ApiConfig {
  port: number;
  host: string;
}

/**
 * Logging configuration
 */
export interface LoggingConfig {
  level: LogLevel;
  maxFiles: number;
  maxSizeMb: number;
}

/**
 * Storage paths configuration
 */
export interface StorageConfig {
  dbPath: string;
  backupPath: string;
}

/**
 * Full application configuration
 */
export interface AppConfig {
  daemon: DaemonConfig;
  api: ApiConfig;
  logging: LoggingConfig;
  storage: StorageConfig;
}

// =============================================================================
// Logging Types
// =============================================================================

/**
 * Log severity levels
 */
export enum LogLevel {
  DEBUG = 0,
  INFO = 1,
  WARN = 2,
  ERROR = 3
}

/**
 * A single log entry
 */
export interface LogEntry {
  timestamp: string;
  level: LogLevel;
  module: string;
  message: string;
  context?: Record<string, unknown>;
}

// =============================================================================
// API Response Types
// =============================================================================

/**
 * Sessions list response
 */
export interface SessionsResponse {
  sessions: TimeSession[];
  totalDuration: number;
}

/**
 * Projects list response
 */
export interface ProjectsResponse {
  projects: Project[];
}

/**
 * Daily report data
 */
export interface DailyReport {
  date: string;
  totalFocusedMinutes: number;
  sessionsByProject: ProjectMinutes[];
  hourlyBreakdown: HourlyMinutes[];
  idleMinutes: number;
}

/**
 * Project with accumulated minutes
 */
export interface ProjectMinutes {
  projectId: string;
  name: string;
  minutes: number;
}

/**
 * Hourly breakdown entry
 */
export interface HourlyMinutes {
  hour: number;
  minutes: number;
}

/**
 * Weekly report data
 */
export interface WeeklyReport {
  week: string;
  totalFocusedHours: number;
  dailyBreakdown: DailyMinutes[];
  topProjects: ProjectHours[];
  averageDailyHours: number;
}

/**
 * Daily breakdown entry
 */
export interface DailyMinutes {
  date: string;
  minutes: number;
}

/**
 * Project with accumulated hours
 */
export interface ProjectHours {
  projectId: string;
  name: string;
  hours: number;
}

/**
 * Summary report data
 */
export interface SummaryReport {
  totalDays: number;
  totalFocusedHours: number;
  mostProductiveDay: string;
  topProject: TopProject;
  dailyAverageHours: number;
}

/**
 * Top project info
 */
export interface TopProject {
  name: string;
  hours: number;
}

/**
 * Daemon health status response
 */
export interface HealthStatus {
  status: 'running' | 'paused';
  version: string;
  uptimeSeconds: number;
  lastSessionAt: string | null;
  isCurrentlyFocused: boolean;
  currentProject: { id: string; name: string } | null;
}

/**
 * Error response format
 */
export interface ErrorResponse {
  error: {
    code: string;
    message: string;
    details?: Record<string, unknown>;
  };
}

// =============================================================================
// Daemon Types
// =============================================================================

/**
 * Active session being tracked
 */
export interface ActiveSession {
  projectId: string;
  startTime: Date;
  windowTitle: string;
}

/**
 * Idle state machine states
 */
export enum IdleState {
  ACTIVE = 'ACTIVE',
  IDLE = 'IDLE'
}

// =============================================================================
// Database Types
// =============================================================================

/**
 * Key-value setting entry
 */
export interface Setting {
  key: string;
  value: string;
}

/**
 * Create session input (for POST requests)
 */
export interface CreateSessionInput {
  projectId: string;
  startTime: Date;
  endTime?: Date;
}

/**
 * Create project input (for POST requests)
 */
export interface CreateProjectInput {
  name: string;
  color?: string;
  keywords?: string[];
}

/**
 * Update project input (for PUT requests)
 */
export interface UpdateProjectInput {
  name?: string;
  color?: string;
  keywords?: string[];
}

/**
 * Merge projects request body
 */
export interface MergeProjectsInput {
  sourceProjectId: string;
}