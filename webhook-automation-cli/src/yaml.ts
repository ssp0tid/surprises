import { parse as yamlParse } from 'yaml';
import { readFile } from 'fs/promises';
import { Workflow, Step, ValidationResult, ValidationError as ValidationErrorType } from './types.js';
import { YamlParseError, ValidationError } from './errors.js';

export async function parseWorkflowFile(filePath: string): Promise<Workflow> {
  try {
    const content = await readFile(filePath, 'utf-8');
    return parseWorkflow(content, filePath);
  } catch (error) {
    if (error instanceof YamlParseError || error instanceof ValidationError) {
      throw error;
    }
    throw new YamlParseError(`Failed to read file: ${filePath}`, filePath);
  }
}

export function parseWorkflow(content: string, source?: string): Workflow {
  try {
    const parsed = yamlParse(content);
    if (!parsed) {
      throw new YamlParseError('Empty workflow file', source);
    }
    if (!parsed.name) {
      throw new ValidationError('Workflow must have a name', ['name']);
    }
    if (!parsed.steps || !Array.isArray(parsed.steps)) {
      throw new ValidationError('Workflow must have steps array', ['steps']);
    }
    validateSteps(parsed.steps, source);
    return parsed as Workflow;
  } catch (error) {
    if (error instanceof YamlParseError || error instanceof ValidationError) {
      throw error;
    }
    throw new YamlParseError(`Failed to parse YAML: ${error}`, source);
  }
}

function validateSteps(steps: any[], source?: string): void {
  const ids = new Set<string>();
  for (const step of steps) {
    if (!step.id) {
      throw new ValidationError('Step must have an id', ['steps']);
    }
    if (ids.has(step.id)) {
      throw new ValidationError(`Duplicate step id: ${step.id}`, ['steps']);
    }
    ids.add(step.id);
    if (!step.type) {
      throw new ValidationError(`Step ${step.id} must have a type`, ['steps']);
    }
    const validTypes = ['http', 'condition', 'set', 'delay', 'log'];
    if (!validTypes.includes(step.type)) {
      throw new ValidationError(
        `Step ${step.id} invalid type: ${step.type}. Valid: ${validTypes.join(', ')}`,
        ['steps']
      );
    }
  }
}

export function validateWorkflow(workflow: Workflow): ValidationResult {
  const errors: ValidationErrorType[] = [];
  if (!workflow.name) {
    errors.push({ path: 'name', message: 'Workflow name is required' });
  }
  if (!workflow.steps || !Array.isArray(workflow.steps)) {
    errors.push({ path: 'steps', message: 'Steps must be an array' });
  } else {
    try {
      validateSteps(workflow.steps);
    } catch (error) {
      if (error instanceof ValidationError) {
        errors.push({ path: 'steps', message: error.message });
      }
    }
  }
  return { valid: errors.length === 0, errors };
}