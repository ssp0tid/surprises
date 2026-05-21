import chalk from 'chalk';

// Success message with green checkmark
export function success(message) {
  console.log(chalk.green('✓') + ' ' + message);
}

// Error message with red X
export function error(message) {
  console.error(chalk.red('✗') + ' ' + message);
}

// Warning message with yellow warning sign
export function warn(message) {
  console.log(chalk.yellow('⚠') + ' ' + message);
}

// Info message with blue info sign
export function info(message) {
  console.log(chalk.blue('ℹ') + ' ' + message);
}

// Section header
export function header(text) {
  console.log('\n' + chalk.bold.underline(text));
}

// Branch name with color based on status
export function branchName(name, status) {
  switch (status) {
    case 'merged':
      return chalk.green(name);
    case 'unmerged':
      return chalk.yellow(name);
    case 'current':
      return chalk.cyan(name);
    case 'protected':
      return chalk.red(name);
    default:
      return chalk.white(name);
  }
}

// Merge status indicator
export function mergeStatus(isMerged) {
  if (isMerged === undefined) return chalk.gray('?');
  return isMerged ? chalk.green('merged') : chalk.yellow('unmerged');
}

// Ahead/behind status
export function aheadBehind(status) {
  if (!status || (status.ahead === 0 && status.behind === 0)) {
    return chalk.gray('up to date');
  }
  
  const parts = [];
  if (status.ahead > 0) {
    parts.push(chalk.green(`↑${status.ahead}`));
  }
  if (status.behind > 0) {
    parts.push(chalk.red(`↓${status.behind}`));
  }
  
  return parts.join(chalk.gray(' | '));
}

// Table row helper
export function tableRow(columns, widths) {
  const row = columns.map((col, i) => {
    const str = String(col);
    return str.padEnd(widths[i]);
  }).join('  ');
  console.log(row);
}

// Separator line
export function separator(char = '─', length = 60) {
  console.log(chalk.gray(char.repeat(length)));
}

// Prompt confirmation
export function promptConfirm(message) {
  return chalk.yellow('?') + ' ' + chalk.bold(message) + ' ';
}

// Dry-run indicator
export function dryRun() {
  return chalk.bgYellow.black(' DRY RUN ') + ' ';
}

// Summary statistics
export function summary(label, count, color = 'white') {
  const colorFn = chalk[color] || chalk.white;
  console.log('  ' + label + ': ' + colorFn(count));
}