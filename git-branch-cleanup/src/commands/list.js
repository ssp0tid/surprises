import chalk from 'chalk';
import {
  getLocalBranches,
  getRemoteBranches,
  getMergedBranches,
  getUnmergedBranches,
  getBranchStatus,
  isProtectedBranch
} from '../utils/git.js';
import { success, error, info, header, branchName, mergeStatus, aheadBehind, separator } from '../utils/format.js';

export async function listBranches(options) {
  const { local, remote, mergedTo, unmerged } = options;
  const targetBranch = mergedTo || 'main';

  try {
    let branches = [];
    let branchType = '';

    if (local || (!local && !remote)) {
      const localBranches = await getLocalBranches();
      const filtered = localBranches.filter(b => !isProtectedBranch(b) && b !== targetBranch);
      branches = branches.concat(filtered.map(b => ({ name: b, type: 'local' })));
      branchType = 'local';
    }

    if (remote) {
      const remoteBranches = await getRemoteBranches();
      const filtered = remoteBranches.filter(b => !isProtectedBranch(b));
      branches = branches.concat(filtered.map(b => ({ name: b, type: 'remote' })));
      if (!branchType) branchType = 'remote';
    }

    if (!branchType && branches.length > 0) {
      branchType = 'local';
    }

    if (branches.length === 0) {
      info('No branches found matching criteria.');
      return;
    }

    let mergedList = [];
    let unmergedList = [];

    if (!remote) {
      mergedList = await getMergedBranches(targetBranch);
      unmergedList = await getUnmergedBranches(targetBranch);
    }

    header(`${branchType.charAt(0).toUpperCase() + branchType.slice(1)} Branches`);

    if (unmerged) {
      const branchesToShow = branches.filter(b => unmergedList.includes(b.name) || b.type === 'remote');
      if (branchesToShow.length === 0) {
        info('No unmerged branches found.');
        return;
      }
      for (const branch of branchesToShow) {
        const status = await getBranchStatus(branch.name);
        const statusStr = branch.type === 'remote' ? 'remote' : 'unmerged';
        console.log(`  ${branchName(branch.name, statusStr)}  ${aheadBehind(status)}`);
      }
    } else {
      const branchesToShow = branches.filter(b => mergedList.includes(b.name));
      if (branchesToShow.length === 0) {
        info('No merged branches found.');
        return;
      }
      for (const branch of branchesToShow) {
        const status = await getBranchStatus(branch.name);
        console.log(`  ${branchName(branch.name, 'merged')}  ${aheadBehind(status)}`);
      }
    }

    separator();
    success(`Total: ${branches.length} branches`);
  } catch (err) {
    error(err.message);
    process.exit(1);
  }
}