#!/usr/bin/env node

import { Command } from 'commander';
import { CronExpressionParser } from 'cron-parser';
import cronstrue from 'cronstrue';
import process from 'process';

interface ValidationResult {
  valid: boolean;
  error?: string;
  description?: string;
}

interface ConflictResult {
  hasConflict: boolean;
  type?: 'exact' | 'subset' | 'partial';
  analysis?: string;
  overlapPoints?: string[];
}

interface NextRunResult {
  expression: string;
  timezone: string;
  nextRuns: string[];
}

const colors = {
  reset: '\x1b[0m',
  green: '\x1b[32m',
  red: '\x1b[31m',
  yellow: '\x1b[33m',
};

function success(msg: string): string {
  return `${colors.green}✓${colors.reset} ${msg}`;
}

function error(msg: string): string {
  return `${colors.red}✗${colors.reset} ${msg}`;
}

function warning(msg: string): string {
  return `${colors.yellow}⚠${colors.reset} ${msg}`;
}

function validateInput(expression: string): { valid: boolean; error?: string } {
  if (!expression || expression.trim().length === 0) {
    return { valid: false, error: 'Expression cannot be empty' };
  }

  const trimmed = expression.trim();
  
  if (/[;&|`$()]/.test(trimmed)) {
    return { valid: false, error: 'Expression contains invalid characters' };
  }

  const fields = trimmed.split(/\s+/);
  if (fields.length !== 5 && fields.length !== 6) {
    return { valid: false, error: `Expected 5 or 6 fields, got ${fields.length}` };
  }

  return { valid: true };
}

function validateExpression(expression: string, strict = false): ValidationResult {
  try {
    const inputCheck = validateInput(expression);
    if (!inputCheck.valid) {
      return { valid: false, error: inputCheck.error };
    }

    const fields = expression.trim().split(/\s+/);
    
    if (strict) {
      const hasDayOfMonth = !/^(\*|0)$/.test(fields[2]) && fields[2] !== '?';
      const hasDayOfWeek = !/^(\*|0)$/.test(fields[4]) && fields[4] !== '?';
      
      if (hasDayOfMonth && hasDayOfWeek) {
        return { 
          valid: false, 
          error: "Strict mode - Cannot specify both day-of-month and day-of-week" 
        };
      }
    }

    CronExpressionParser.parse(expression);
    
    const description = cronstrue.toString(expression, {
      use24HourTimeFormat: true,
    });
    
    return { valid: true, description };
  } catch (err) {
    const errorMessage = err instanceof Error ? err.message : 'Unknown error';
    return { valid: false, error: errorMessage };
  }
}

function getNextRuns(
  expression: string, 
  count: number, 
  timezone: string, 
  fromDate?: Date
): NextRunResult {
  const interval = CronExpressionParser.parse(expression, {
    currentDate: fromDate || new Date(),
    tz: timezone,
  });
  
  const nextRuns: string[] = [];
  for (let i = 0; i < count; i++) {
    const next = interval.next();
    const isoString = next.toISOString();
    if (isoString) {
      nextRuns.push(isoString);
    }
  }
  
  return { expression, timezone, nextRuns };
}

function checkConflict(expr1: string, expr2: string): ConflictResult {
  try {
    const fields1 = expr1.trim().split(/\s+/);
    const fields2 = expr2.trim().split(/\s+/);
    
    const time1 = `${fields1[1]}:${fields1[0]}`;
    const time2 = `${fields2[1]}:${fields2[0]}`;
    
    const day1 = fields1[4];
    const day2 = fields2[4];
    
    const daysOverlap = (day1 === '*' || day1 === day2) && (day2 === '*' || day2 === day1);
    
    if (time1 === time2 && (daysOverlap || (day1 === '*' && day2 === '*'))) {
      return {
        hasConflict: true,
        type: 'exact',
        analysis: `Both run at exactly the same time`,
      };
    }
    
    const checkSubset = (expr: string, potentialSubset: string): boolean => {
      const fields = expr.split(/\s+/);
      const subFields = potentialSubset.split(/\s+/);
      
      if (fields[0].startsWith('*/') && subFields[0].startsWith('*/')) {
        const base = parseInt(fields[0].slice(2));
        const sub = parseInt(subFields[0].slice(2));
        return sub % base === 0;
      }
      return false;
    };
    
    if (checkSubset(expr1, expr2)) {
      return {
        hasConflict: true,
        type: 'subset',
        analysis: `"${expr1}" runs more frequently and includes all times from "${expr2}"`,
      };
    }
    
    if (checkSubset(expr2, expr1)) {
      return {
        hasConflict: true,
        type: 'subset',
        analysis: `"${expr2}" runs more frequently and includes all times from "${expr1}"`,
      };
    }
    
    return { hasConflict: false };
  } catch {
    return { hasConflict: false };
  }
}

async function parseCrontabFile(filePath: string): Promise<{ line: number; expression: string }[]> {
  const { readFile } = await import('fs/promises');
  const content = await readFile(filePath, 'utf-8');
  const lines: { line: number; expression: string }[] = [];
  
  content.split('\n').forEach((line, index) => {
    const trimmed = line.trim();
    if (trimmed && !trimmed.startsWith('#')) {
      const parts = trimmed.split(/\s+/);
      if (parts.length >= 5) {
        lines.push({ line: index + 1, expression: trimmed });
      }
    }
  });
  
  return lines;
}

const program = new Command();

program
  .name('cron-guard')
  .description('CLI Cron Expression Validator - Validate cron expressions, view next run times, and detect conflicts')
  .version('1.0.0')
  .option('-q, --quiet', 'Suppress non-essential output', false);

program
  .argument('<expression>', 'Cron expression to validate')
  .option('-n, --next <count>', 'Show next N run times')
  .option('-d, --describe', 'Show human-readable description')
  .option('-t, --timezone <tz>', 'Timezone for next run times', Intl.DateTimeFormat().resolvedOptions().timeZone)
  .option('-f, --from <date>', 'Start from specific date (ISO format)')
  .option('-j, --json', 'Output as JSON')
  .option('-v, --verbose', 'Verbose output')
  .option('-s, --strict', 'Strict mode - reject both day-of-month and day-of-week')
  .option('-l, --locale <locale>', 'Locale for description (e.g., en, es, fr, de)', 'en')
  .action(async (expression: string, options: {
    next?: string;
    describe?: boolean;
    timezone?: string;
    from?: string;
    json?: boolean;
    verbose?: boolean;
    strict?: boolean;
    quiet?: boolean;
    locale?: string;
  }) => {
    const results: Record<string, unknown> = {};
    let exitCode = 0;

    const validation = validateExpression(expression, options.strict);
    
    if (!validation.valid) {
      if (options.json) {
        results.valid = false;
        results.error = validation.error;
        console.log(JSON.stringify(results, null, 2));
      } else {
        console.log(error(`Invalid: ${validation.error}`));
      }
      process.exit(1);
    }

    results.valid = true;
    results.description = validation.description;
    
    if (!options.quiet && !options.json) {
      console.log(success(`Valid: ${validation.description}`));
    }

    if (options.describe) {
      try {
        const description = cronstrue.toString(expression, {
          verbose: options.verbose ?? false,
          use24HourTimeFormat: true,
          locale: options.locale || 'en',
        });
        
        if (options.json) {
          results.description = description;
        } else {
          console.log(description);
        }
      } catch (err) {
        const errorMsg = err instanceof Error ? err.message : 'Unknown error';
        if (options.json) {
          results.error = errorMsg;
        } else {
          console.log(error(`Error: ${errorMsg}`));
        }
        exitCode = 1;
      }
    }
    
    if (options.next) {
      const count = parseInt(options.next, 10);
      if (isNaN(count) || count <= 0) {
        if (options.json) {
          results.error = 'Invalid count value';
          console.log(JSON.stringify(results, null, 2));
        } else {
          console.log(error('Invalid count value'));
        }
        process.exit(1);
      }
      
      try {
        const fromDate = options.from ? new Date(options.from) : undefined;
        const nextResult = getNextRuns(expression, count, options.timezone ?? 'UTC', fromDate);
        
        if (options.json) {
          results.nextRuns = nextResult.nextRuns;
          console.log(JSON.stringify(results, null, 2));
        } else {
          console.log(`\nNext ${count} run times for "${expression}"${fromDate ? ` from ${fromDate.toISOString()}` : ''} [${options.timezone}]:`);
          nextResult.nextRuns.forEach((run, i) => {
            console.log(`  ${i + 1}. ${run}`);
          });
        }
      } catch (err) {
        const errorMsg = err instanceof Error ? err.message : 'Unknown error';
        if (options.json) {
          results.error = errorMsg;
          console.log(JSON.stringify(results, null, 2));
        } else {
          console.log(error(`Error calculating next runs: ${errorMsg}`));
        }
        exitCode = 1;
      }
    } else if (!options.describe) {
      if (options.json) {
        console.log(JSON.stringify(results, null, 2));
      }
    }

    process.exit(exitCode);
  });

program
  .command('validate <expression>')
  .description('Validate a cron expression')
  .option('-j, --json', 'Output as JSON')
  .option('-s, --strict', 'Strict mode - reject both day-of-month and day-of-week')
  .action(async (expression: string, options: { json?: boolean; strict?: boolean }) => {
    const validation = validateExpression(expression, options.strict);
    
    if (options.json) {
      console.log(JSON.stringify({
        valid: validation.valid,
        error: validation.valid ? undefined : validation.error,
        description: validation.description,
      }, null, 2));
    } else {
      if (validation.valid) {
        console.log(success(`Valid: ${validation.description}`));
      } else {
        console.log(error(`Invalid: ${validation.error}`));
        process.exit(1);
      }
    }
  });

program
  .command('next <expression>')
  .description('Show next N run times')
  .option('-n, --count <number>', 'Number of run times to show', '5')
  .option('-t, --timezone <tz>', 'Timezone', Intl.DateTimeFormat().resolvedOptions().timeZone)
  .option('-f, --from <date>', 'Start from specific date (ISO format)')
  .option('-j, --json', 'Output as JSON')
  .action(async (expression: string, options: {
    count?: string;
    timezone?: string;
    from?: string;
    json?: boolean;
  }) => {
    const count = parseInt(options.count ?? '5', 10);
    
    const validation = validateExpression(expression);
    if (!validation.valid) {
      if (options.json) {
        console.log(JSON.stringify({ error: validation.error }, null, 2));
      } else {
        console.log(error(`Invalid: ${validation.error}`));
      }
      process.exit(1);
    }
    
    try {
      const fromDate = options.from ? new Date(options.from) : undefined;
      const result = getNextRuns(expression, count, options.timezone ?? 'UTC', fromDate);
      
      if (options.json) {
        console.log(JSON.stringify(result, null, 2));
      } else {
        console.log(`Next ${count} run times for "${expression}" (${validation.description}) [${options.timezone ?? 'UTC'}]:`);
        result.nextRuns.forEach((run, i) => {
          console.log(`  ${i + 1}. ${run}`);
        });
      }
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : 'Unknown error';
      if (options.json) {
        console.log(JSON.stringify({ error: errorMsg }, null, 2));
      } else {
        console.log(error(`Error: ${errorMsg}`));
      }
      process.exit(1);
    }
  });

program
  .command('describe <expression>')
  .description('Show human-readable description')
  .option('-v, --verbose', 'Verbose output')
  .option('-l, --locale <locale>', 'Locale for description', 'en')
  .option('-j, --json', 'Output as JSON')
  .option('--use24hour', 'Use 24-hour time format')
  .action(async (expression: string, options: {
    verbose?: boolean;
    locale?: string;
    json?: boolean;
    use24hour?: boolean;
  }) => {
    const validation = validateExpression(expression);
    if (!validation.valid) {
      if (options.json) {
        console.log(JSON.stringify({ error: validation.error }, null, 2));
      } else {
        console.log(error(`Invalid: ${validation.error}`));
      }
      process.exit(1);
    }
    
    try {
      const description = cronstrue.toString(expression, {
        verbose: options.verbose ?? false,
        use24HourTimeFormat: options.use24hour ?? true,
        locale: options.locale || 'en',
      });

      if (options.json) {
        console.log(JSON.stringify({ expression, description }, null, 2));
      } else {
        console.log(description);
      }
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : 'Unknown error';
      if (options.json) {
        console.log(JSON.stringify({ error: errorMsg }, null, 2));
      } else {
        console.log(error(`Error: ${errorMsg}`));
      }
      process.exit(1);
    }
  });

program
  .command('conflicts <expression1> [expression2]')
  .description('Check for schedule conflicts between cron expressions')
  .option('-f, --file <path>', 'Check expressions from a crontab file')
  .option('-j, --json', 'Output as JSON')
  .action(async (expression1: string, expression2: string | undefined, options: {
    file?: string;
    json?: boolean;
  }) => {
    if (options.file) {
      try {
        const entries = await parseCrontabFile(options.file);
        
        if (options.json) {
          console.log(JSON.stringify({
            file: options.file,
            count: entries.length,
            expressions: entries,
          }, null, 2));
        } else {
          console.log(`Analyzing ${options.file} (${entries.length} schedules)...`);
          
          const conflicts: { line1: number; expr1: string; line2: number; expr2: string; analysis: string }[] = [];
          
          for (let i = 0; i < entries.length; i++) {
            for (let j = i + 1; j < entries.length; j++) {
              const result = checkConflict(entries[i].expression, entries[j].expression);
              if (result.hasConflict) {
                conflicts.push({
                  line1: entries[i].line,
                  expr1: entries[i].expression,
                  line2: entries[j].line,
                  expr2: entries[j].expression,
                  analysis: result.analysis || 'Conflict detected',
                });
              }
            }
          }
          
          if (conflicts.length === 0) {
            console.log(success('No conflicts detected'));
          } else {
            conflicts.forEach(c => {
              console.log(warning(`Line ${c.line1} "${c.expr1}" conflicts with Line ${c.line2} "${c.expr2}"`));
              console.log(`  Analysis: ${c.analysis}`);
            });
          }
        }
      } catch (err) {
        const errorMsg = err instanceof Error ? err.message : 'Unknown error';
        if (options.json) {
          console.log(JSON.stringify({ error: errorMsg }, null, 2));
        } else {
          console.log(error(`Error reading file: ${errorMsg}`));
        }
        process.exit(1);
      }
      return;
    }
    
    if (!expression2) {
      console.log(error('Please provide two expressions or use --file flag'));
      console.log('Usage: cron-guard conflicts <expr1> <expr2>');
      process.exit(1);
    }
    
    const val1 = validateExpression(expression1);
    const val2 = validateExpression(expression2);
    
    if (!val1.valid) {
      console.log(error(`Expression 1 invalid: ${val1.error}`));
      process.exit(1);
    }
    if (!val2.valid) {
      console.log(error(`Expression 2 invalid: ${val2.error}`));
      process.exit(1);
    }
    
    const result = checkConflict(expression1, expression2);
    
    if (options.json) {
      console.log(JSON.stringify({
        expression1,
        expression2,
        hasConflict: result.hasConflict,
        type: result.type,
        analysis: result.analysis,
        overlapPoints: result.overlapPoints,
      }, null, 2));
    } else {
      if (result.hasConflict) {
        console.log(warning(`Schedule conflict detected between "${expression1}" and "${expression2}"`));
        if (result.analysis) {
          console.log(`  Analysis: ${result.analysis}`);
        }
      } else {
        console.log(success('No conflict detected'));
      }
    }
  });

program.parse();