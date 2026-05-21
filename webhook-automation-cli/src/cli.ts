import { Command } from 'commander';
import { parseWorkflowFile, validateWorkflow, parseWorkflow } from './yaml.js';
import { WorkflowEngine } from './engine.js';
import chalk from 'chalk';
import ora from 'ora';

export function createCli(): Command {
  const program = new Command();
  program
    .name('webhook')
    .description('Webhook Automation CLI - Chain HTTP requests with variables and conditionals')
    .version('1.0.0');

  program
    .command('validate')
    .description('Validate a workflow file')
    .argument('<file>', 'Path to workflow YAML file')
    .action(async (file: string) => {
      const spinner = ora('Validating workflow...').start();
      try {
        const workflow = await parseWorkflowFile(file);
        const result = validateWorkflow(workflow);
        if (result.valid) {
          spinner.succeed(chalk.green('Workflow is valid'));
          console.log(chalk.bold(`Workflow: ${workflow.name}`));
          console.log(`Steps: ${workflow.steps.length}`);
        } else {
          spinner.fail(chalk.red('Workflow validation failed'));
          for (const error of result.errors) {
            console.log(chalk.red(`  ${error.path}: ${error.message}`));
          }
          process.exit(1);
        }
      } catch (error) {
        spinner.fail(chalk.red('Validation error'));
        console.log(chalk.red(`  ${error instanceof Error ? error.message : String(error)}`));
        process.exit(1);
      }
    });

  program
    .command('run')
    .description('Run a workflow')
    .argument('<file>', 'Path to workflow YAML file')
    .option('-i, --input <items...>', 'Input variables (key=value)')
    .option('-e, --env <items...>', 'Environment variables (key=value)')
    .option('-v, --verbose', 'Verbose output')
    .action(async (file: string, options: { input?: string[], env?: string[], verbose?: boolean }) => {
      const spinner = ora('Loading workflow...').start();
      try {
        const workflow = await parseWorkflowFile(file);
        spinner.succeed(chalk.green(`Loaded: ${workflow.name}`));
        const input: Record<string, string> = {};
        if (options.input) {
          for (const item of options.input) {
            const [key, value] = item.split('=');
            if (key && value) {
              input[key] = value;
            }
          }
        }
        if (options.env) {
          for (const item of options.env) {
            const [key, value] = item.split('=');
            if (key && value) {
              process.env[key] = value;
            }
          }
        }
        if (options.verbose) {
          console.log(chalk.gray(`Input: ${JSON.stringify(input)}`));
        }
        const engine = new WorkflowEngine({ verbose: options.verbose });
        const result = await engine.execute(workflow, input);
        console.log(chalk.bold('\n--- Results ---'));
        for (const step of result.steps) {
          const statusColor = step.status === 'success' ? chalk.green : step.status === 'skipped' ? chalk.yellow : chalk.red;
          console.log(`${step.stepId}: ${statusColor(step.status)} (${step.duration}ms)`);
          if (step.data) {
            console.log(chalk.gray(`  ${JSON.stringify(step.data).substring(0, 200)}`));
          }
          if (step.error) {
            console.log(chalk.red(`  Error: ${step.error.message}`));
          }
        }
        console.log(chalk.bold(`\nTotal: ${result.duration}ms`));
        if (result.success) {
          console.log(chalk.green.bold('\nWorkflow completed successfully'));
          process.exit(0);
        } else {
          console.log(chalk.red.bold(`\nWorkflow failed: ${result.error}`));
          process.exit(1);
        }
      } catch (error) {
        spinner.fail(chalk.red('Execution error'));
        console.log(chalk.red(`  ${error instanceof Error ? error.message : String(error)}`));
        process.exit(1);
      }
    });

  return program;
}