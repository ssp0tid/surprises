import { Workflow, Step, StepResult, ExecutionContext, StepType } from './types.js';
import { VariableStore, evaluateCondition } from './variables.js';
import { executeHttpStep } from './http.js';
import { WorkflowError, StepExecutionError } from './errors.js';
import { validateWorkflow } from './yaml.js';

export interface EngineConfig {
  verbose?: boolean;
}

export interface ExecutionResult {
  success: boolean;
  steps: StepResult[];
  error?: string;
  duration: number;
}

export class WorkflowEngine {
  private config: EngineConfig;

  constructor(config: EngineConfig = {}) {
    this.config = config;
  }

  async execute(workflow: Workflow, input: Record<string, string> = {}): Promise<ExecutionResult> {
    const validation = validateWorkflow(workflow);
    if (!validation.valid) {
      return {
        success: false,
        steps: [],
        error: validation.errors.map(e => `${e.path}: ${e.message}`).join(', '),
        duration: 0,
      };
    }
    const startTime = Date.now();
    const context: ExecutionContext = {
      workflow,
      input,
      vars: { ...input },
      steps: {},
      startTime,
    };
    const varStore = new VariableStore(input, workflow.settings?.env || {});
    try {
      for (const step of workflow.steps) {
        const result = await this.executeStep(step, context, varStore);
        context.steps[step.id] = result;
        if (result.status === 'failure' && step.stopOnError) {
          throw new StepExecutionError(`Step ${step.id} failed`, step.id);
        }
        if (step.condition) {
          const conditionMet = result.data?.result;
          if (!conditionMet) {
            this.log(`Step ${step.id} condition not met; controlling flow with onTrue/onFalse`);
            if (step.onFalse) {
              if (step.onFalse === 'stop') {
                break;
              }
            }
          } else if (step.onTrue) {
            if (step.onTrue === 'stop') {
              break;
            }
          }
        }
      }
      return {
        success: true,
        steps: Object.values(context.steps),
        duration: Date.now() - startTime,
      };
    } catch (error) {
      return {
        success: false,
        steps: Object.values(context.steps),
        error: error instanceof Error ? error.message : String(error),
        duration: Date.now() - startTime,
      };
    }
  }

  private async executeStep(step: Step, context: ExecutionContext, varStore: VariableStore): Promise<StepResult> {
    const startTime = Date.now();
    this.log(`Executing step: ${step.id} (${step.type})`);
    switch (step.type) {
      case 'http':
        return this.executeHttp(step, context, startTime);
      case 'condition':
        return this.executeCondition(step, context, startTime);
      case 'set':
        return this.executeSet(step, context, varStore, startTime);
      case 'delay':
        return this.executeDelay(step, startTime);
case 'log':
        return this.executeLog(step, context, varStore, startTime);
      default:
        return { stepId: step.id, status: 'failure', error: new Error(`Unknown step type: ${step.type}`), duration: 0 };
    }
  }

  private async executeHttp(step: Step, context: ExecutionContext, startTime: number): Promise<StepResult> {
    if (!step.request) {
      throw new StepExecutionError(`Step ${step.id} missing request config`, step.id);
    }
    const timeout = step.timeout || context.workflow.settings?.timeout || 30000;
    const result = await executeHttpStep(step.id, step.request, timeout, context);
    this.log(`Step ${step.id} completed with status ${result.status}`);
    return result;
  }

  private async executeCondition(step: Step, context: ExecutionContext, startTime: number): Promise<StepResult> {
    if (!step.condition) {
      throw new StepExecutionError(`Step ${step.id} missing condition`, step.id);
    }
    const result = evaluateCondition(step.condition, context);
    this.log(`Condition ${step.condition} = ${result}`);
    return { stepId: step.id, status: 'success', data: { result }, duration: Date.now() - startTime };
  }

  private async executeSet(step: Step, context: ExecutionContext, varStore: VariableStore, startTime: number): Promise<StepResult> {
    if (!step.vars) {
      throw new StepExecutionError(`Step ${step.id} missing vars config`, step.id);
    }
    const resolved: Record<string, any> = {};
    for (const [key, value] of Object.entries(step.vars)) {
      resolved[key] = varStore.interpolate(value, context);
    }
    varStore.setMultiple(resolved);
    context.vars = { ...context.vars, ...resolved };
    this.log(`Set variables: ${Object.keys(resolved).join(', ')}`);
    return { stepId: step.id, status: 'success', data: { vars: resolved }, duration: Date.now() - startTime };
  }

  private async executeDelay(step: Step, startTime: number): Promise<StepResult> {
    const duration = step.duration || 1000;
    await new Promise(resolve => setTimeout(resolve, duration));
    this.log(`Delayed ${duration}ms`);
    return { stepId: step.id, status: 'success', data: { duration }, duration: Date.now() - startTime };
  }

  private async executeLog(step: Step, context: ExecutionContext, varStore: VariableStore, startTime: number): Promise<StepResult> {
    const message = step.message ? varStore.interpolate(step.message, context) : '';
    this.log(message);
    return { stepId: step.id, status: 'success', data: { message }, duration: Date.now() - startTime };
  }

  private log(message: string): void {
    if (this.config.verbose) {
      console.log(message);
    }
  }
}