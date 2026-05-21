// Custom error classes for Webhook Automation CLI

export class WorkflowError extends Error {
  constructor(message: string, public stepId?: string) {
    super(message);
    this.name = 'WorkflowError';
    Error.captureStackTrace(this, this.constructor);
  }
}

export class ValidationError extends WorkflowError {
  constructor(message: string, public errors: string[]) {
    super(message);
    this.name = 'ValidationError';
  }
}

export class StepExecutionError extends WorkflowError {
  constructor(
    message: string,
    stepId: string,
    public statusCode?: number,
    public response?: any,
    public retryable: boolean = false
  ) {
    super(message, stepId);
    this.name = 'StepExecutionError';
  }
}

export class TimeoutError extends StepExecutionError {
  constructor(stepId: string, public timeoutMs: number) {
    super(`Timeout after ${timeoutMs}ms`, stepId);
    this.name = 'TimeoutError';
    this.retryable = true;
  }
}

export class VariableResolutionError extends WorkflowError {
  constructor(message: string, public variable: string) {
    super(message);
    this.name = 'VariableResolutionError';
  }
}

export class ConditionError extends WorkflowError {
  constructor(message: string, stepId: string, public condition: string, public evaluated: any) {
    super(message, stepId);
    this.name = 'ConditionError';
  }
}

export class SecurityError extends WorkflowError {
  constructor(message: string, public reason: string) {
    super(message);
    this.name = 'SecurityError';
  }
}

export class YamlParseError extends WorkflowError {
  constructor(message: string, public file?: string) {
    super(message);
    this.name = 'YamlParseError';
  }
}