import { ExecutionContext } from './types.js';
import { VariableResolutionError } from './errors.js';

export class VariableStore {
  private vars: Record<string, any> = {};

  constructor(input: Record<string, string> = {}, env: Record<string, string> = {}) {
    this.vars = { ...env, ...input };
  }

  get(path: string): any {
    const value = this.vars[path];
    if (value === undefined) {
      throw new VariableResolutionError(`Variable not found: ${path}`, path);
    }
    return value;
  }

  set(path: string, value: any): void {
    this.vars[path] = value;
  }

  setMultiple(vars: Record<string, any>): void {
    Object.assign(this.vars, vars);
  }

  interpolate(template: string, context: ExecutionContext): string {
    let result = template;
    result = result.replace(/\$\{(\w+)}/g, (_, name) => {
      return process.env[name] ?? this.vars[name] ?? '';
    });
    result = result.replace(/\{\{input\.(\w+)\}\}/g, (_, name) => {
      return context.input[name] ?? '';
    });
    result = result.replace(/\{\{vars\.(\w+)\}\}/g, (_, name) => {
      return this.vars[name] ?? context.vars[name] ?? '';
    });
    result = result.replace(/\{\{(\w+)\.status\}\}/g, (_, stepId) => {
      return String(context.steps[stepId]?.data?.status ?? '');
    });
    result = result.replace(/\{\{([\w-]+)\.body(?:\.(.+?))?\}\}/g, (_, stepId, path) => {
      const step = context.steps[stepId];
      if (!step?.data?.body) return '';
      if (!path) return step.data.body;
      return this.getNested(step.data.body, path);
    });
    return result;
  }

  private getNested(obj: any, path: string): any {
    const parts = path.split('.');
    let current = obj;
    for (const part of parts) {
      if (current === null || current === undefined) return undefined;
      current = current[part];
    }
    return current;
  }

  resolveStepValue(path: string, context: ExecutionContext): any {
    const match = path.match(/^\{\{(\w+)\.body(?:\.(.+?))?\}\}$/);
    if (!match) return path;
    const [, stepId, jsonPath] = match;
    const step = context.steps[stepId];
    if (!step?.data?.body) return undefined;
    if (!jsonPath) return step.data.body;
    return this.getNested(step.data.body, jsonPath);
  }

  getAll(): Record<string, any> {
    return { ...this.vars };
  }
}

export function evaluateCondition(condition: string, context: ExecutionContext): boolean {
  const store = new VariableStore(context.input, process.env as Record<string, string>);
  store.setMultiple(context.vars);
  let expr = condition;
  expr = expr.replace(/\{\{([a-zA-Z0-9_-]+)\.status\}\}/g, (_, stepId) => {
    return String(context.steps[stepId]?.data?.status ?? 0);
  });
  expr = expr.replace(/(\w+)\s*==\s*['"](.+?)['"]/g, (_, left, right) => {
    return `(vars.${left} === '${right}')`;
  });
  expr = expr.replace(/\{\{vars\.(\w+)\}\}/g, (_, name) => {
    return `(vars.${name})`;
  });
  expr = expr.replace(/(\w+|\d+)\s*==\s*(\d+)/g, (_, left, right) => {
    return left.match(/^\d+$/) 
      ? `(${left} === ${right})` 
      : `(vars.${left} === ${right})`;
  });
  const directEval = expr.match(/^\(([^=]+)\s*(===|==|!=|>|<|>=|<=)\s*([^=]+)\)$/);
  if (directEval) {
    const [, left, op, right] = directEval;
    const l = left.trim();
    const r = right.trim();
    switch (op) {
      case '===': return l === r;
      case '==': return l == r;
      case '!=': return l != r;
      case '>': return Number(l) > Number(r);
      case '<': return Number(l) < Number(r);
      case '>=': return Number(l) >= Number(r);
      case '<=': return Number(l) <= Number(r);
      default: return false;
    }
  }
  const leftSide = expr.match(/^([^=!><]+)\s*(===|==|!=|>|<|>=|<=)\s*(.+)$/);
  if (!leftSide) {
    const varName = expr.trim();
    return !!store.interpolate(`{{vars.${varName}}}`, context);
  }
  const [, left, op, right] = leftSide;
  const l = store.interpolate(left.trim(), context).trim();
  const r = store.interpolate(right.trim(), context).trim();
  switch (op) {
    case '==': return l == r;
    case '!=': return l != r;
    case '>': return Number(l) > Number(r);
    case '<': return Number(l) < Number(r);
    case '>=': return Number(l) >= Number(r);
    case '<=': return Number(l) <= Number(r);
    default: return false;
  }
}