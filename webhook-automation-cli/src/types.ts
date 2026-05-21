// Core type definitions for Webhook Automation CLI

export type StepType = 'http' | 'condition' | 'set' | 'delay' | 'log';
export type StepResultStatus = 'success' | 'failure' | 'skipped';

export interface Workflow {
  name: string;
  version?: string;
  description?: string;
  settings?: WorkflowSettings;
  input?: Record<string, string>;
  steps: Step[];
}

export interface WorkflowSettings {
  timeout?: number;
  retry?: RetrySettings;
  env?: Record<string, string>;
}

export interface RetrySettings {
  maxAttempts?: number;
  delay?: number;
  backoff?: 'linear' | 'exponential';
}

export interface Step {
  id: string;
  name?: string;
  type: StepType;
  // HTTP step
  request?: HttpRequest;
  // Condition step
  condition?: string;
  onTrue?: string;
  onFalse?: string | Step[];
  // Set step
  vars?: Record<string, string>;
  // Delay step
  duration?: number;
  // Log step
  message?: string;
  level?: 'debug' | 'info' | 'warn' | 'error';
  // Common
  timeout?: number;
  retries?: number;
  stopOnError?: boolean;
}

export interface HttpRequest {
  url: string;
  method: HttpMethod;
  headers?: Record<string, string>;
  query?: Record<string, string>;
  body?: any;
}

export type HttpMethod = 'GET' | 'POST' | 'PUT' | 'PATCH' | 'DELETE';

export interface StepResult {
  stepId: string;
  status: StepResultStatus;
  data?: any;
  error?: Error;
  duration: number;
}

export interface ExecutionContext {
  workflow: Workflow;
  input: Record<string, string>;
  vars: Record<string, any>;
  steps: Record<string, StepResult>;
  startTime: number;
}

export interface ValidationResult {
  valid: boolean;
  errors: ValidationError[];
}

export interface ValidationError {
  path: string;
  message: string;
}

export interface CliOptions {
  file?: string;
  input?: string[];
  env?: string[];
  verbose?: boolean;
}