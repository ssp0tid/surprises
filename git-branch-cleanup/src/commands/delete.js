import inquirer from 'inquirer';
import {
  getLocalBranches,
  getRemoteBranches,
  getMergedBranches,
  deleteLocalBranch,
  deleteRemoteBranch,
  isProtectedBranch
} from '../utils/git.js';
import { success, error, info, warn, header, dryRun, promptConfirm } from '../utils/format.js';

export async function deleteBranches(options) {
  const { local, remote, mergedTo, dryRun: isDryRun, force, branches: specificBranches, interactive } = options;
  const targetBranch = mergedTo || 'main';

  try {
    let branchesToDelete = [];

    if (specificBranches && specificBranches.length > 0) {
      branchesToDelete = specificBranches.map(b => ({ name: b, type: local && !remote ? 'local' : (remote ? 'remote' : 'any') }));
    } else {
      const mergedList = await getMergedBranches(targetBranch);

      if (local || (!local && !remote)) {
        const localBranches = await getLocalBranches();
        const deletableLocal = localBranches.filter(b => 
          !isProtectedBranch(b) && b !== targetBranch && mergedList.includes(b)
        );
        branchesToDelete = branchesToDelete.concat(
          deletableLocal.map(b => ({ name: b, type: 'local' }))
        );
      }

      if (remote) {
        const remoteBranches = await getRemoteBranches();
        const mergedList = await getMergedBranches(targetBranch);
        const deletableRemote = remoteBranches.filter(b => 
          !isProtectedBranch(b) && mergedList.includes(b.replace(/^origin\//, ''))
        );
        branchesToDelete = branchesToDelete.concat(
          deletableRemote.map(b => ({ name: b, type: 'remote' }))
        );
      }
    }

    if (branchesToDelete.length === 0) {
      info('No branches to delete.');
      return;
    }

    let selectedBranches = branchesToDelete;

    if (interactive) {
      const answers = await inquirer.prompt([
        {
          type: 'checkbox',
          name: 'branches',
          message: 'Select branches to delete:',
          choices: branchesToDelete.map(b => ({
            name: `${b.name} (${b.type})`,
            value: b
          })),
          pageSize: 15
        }
      ]);
      selectedBranches = answers.branches;
    }

    if (selectedBranches.length === 0) {
      info('No branches selected for deletion.');
      return;
    }

    header('Branches to delete:');
    selectedBranches.forEach(b => {
      console.log(`  - ${b.name} (${b.type})`);
    });

    if (isDryRun) {
      console.log('\n' + dryRun() + 'Would delete ' + selectedBranches.length + ' branch(es)');
      return;
    }

    let shouldProceed = force;

    if (!force) {
      const answers = await inquirer.prompt([
        {
          type: 'confirm',
          name: 'confirm',
          message: `Delete ${selectedBranches.length} branch(es)?`,
          default: false
        }
      ]);
      shouldProceed = answers.confirm;
    }

    if (!shouldProceed) {
      info('Deletion cancelled.');
      return;
    }

    let deleted = 0;
    let failed = 0;

    for (const branch of selectedBranches) {
      try {
        if (branch.type === 'local' || branch.type === 'any') {
          await deleteLocalBranch(branch.name, force);
          success(`Deleted local branch: ${branch.name}`);
          deleted++;
        } else if (branch.type === 'remote') {
          await deleteRemoteBranch(branch.name);
          success(`Deleted remote branch: ${branch.name}`);
          deleted++;
        }
      } catch (err) {
        error(`Failed to delete ${branch.name}: ${err.message}`);
        failed++;
      }
    }

    header('Summary');
    success(`Deleted: ${deleted}`);
    if (failed > 0) {
      warn(`Failed: ${failed}`);
    }
  } catch (err) {
    error(err.message);
    process.exit(1);
  }
}