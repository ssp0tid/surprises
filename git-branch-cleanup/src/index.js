#!/usr/bin/env node

import { Command } from 'commander';
import chalk from 'chalk';
import { listBranches } from './commands/list.js';
import { deleteBranches } from './commands/delete.js';
import { validateRepo } from './utils/git.js';
import { error } from './utils/format.js';

const program = new Command();

program
  .name('git-branch-cleanup')
  .description('CLI tool to find and delete merged/unmerged git branches')
  .version('1.0.0')
  .hook('preAction', async (thisCommand) => {
    try {
      await validateRepo();
    } catch (err) {
      error(err.message);
      process.exit(1);
    }
  });

program
  .command('list')
  .description('List branches with merge status')
  .option('-l, --local', 'Show only local branches', false)
  .option('-r, --remote', 'Show only remote branches', false)
  .option('-m, --merged-to <branch>', 'Filter branches merged to specific branch', 'main')
  .option('-u, --unmerged', 'Show unmerged branches instead of merged')
  .action(async (options) => {
    await listBranches(options);
  });

program
  .command('delete')
  .description('Delete selected branches')
  .option('-l, --local', 'Delete only local branches', false)
  .option('-r, --remote', 'Delete only remote branches', false)
  .option('-m, --merged-to <branch>', 'Filter branches merged to specific branch', 'main')
  .option('-d, --dry-run', 'Show what would be deleted without actually deleting', false)
  .option('-f, --force', 'Skip confirmation prompts', false)
  .option('-b, --branches <branches...>', 'Specific branches to delete')
  .action(async (options) => {
    await deleteBranches(options);
  });

program
  .command('cleanup')
  .description('Interactive cleanup mode')
  .option('-l, --local', 'Cleanup only local branches', false)
  .option('-r, --remote', 'Cleanup only remote branches', false)
  .option('-m, --merged-to <branch>', 'Filter branches merged to specific branch', 'main')
  .option('-d, --dry-run', 'Show what would be deleted without actually deleting', false)
  .action(async (options) => {
    await deleteBranches({ ...options, interactive: true });
  });

// Parse args if not being tested
if (process.argv[1]?.endsWith('index.js')) {
  program.parse(process.argv);
}

// Handle unknown commands
program.on('command:*', () => {
  error(`Invalid command: ${program.args.join(' ')}`);
  console.log(`Run '${chalk.cyan('git-branch-cleanup --help')}' for available commands.`);
  process.exit(1);
});

export { program };