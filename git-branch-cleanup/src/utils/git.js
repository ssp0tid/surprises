import simpleGit from 'simple-git';
import { error } from './format.js';

const PROTECTED_BRANCHES = ['main', 'master', 'develop', 'HEAD'];

export function isProtectedBranch(branchName) {
  const normalized = branchName.replace(/^origin\//, '').replace(/^remotes\//, '');
  return PROTECTED_BRANCHES.includes(normalized.toLowerCase());
}

export async function validateRepo() {
  const git = simpleGit();
  const isRepo = await git.checkIsRepo();

  if (!isRepo) {
    throw new Error('Not a git repository. Run this command from a git repo.');
  }

  const status = await git.status();
  if (status.detached) {
    throw new Error('Cannot operate in detached HEAD state. Checkout a branch first.');
  }
}

export async function getLocalBranches() {
  const git = simpleGit();
  const branches = await git.branchLocal();
  return branches.all.filter(b => !b.startsWith('remotes/'));
}

export async function getRemoteBranches() {
  const git = simpleGit();
  const branches = await git.branch(['-a']);
  return branches.all.filter(b => b.startsWith('remotes/'));
}

export async function getMergedBranches(targetBranch = 'main') {
  const git = simpleGit();
  try {
    const branches = await git.branchLocal();
    const merged = [];

    for (const branch of branches.all) {
      if (isProtectedBranch(branch)) continue;
      if (branch.startsWith('remotes/')) continue;
      if (branch === targetBranch) continue;

      try {
        await git.raw(['merge-base', '--is-ancestor', branch, targetBranch]);
        merged.push(branch);
      } catch {
      }
    }

    return merged;
  } catch {
    return [];
  }
}

export async function getUnmergedBranches(targetBranch = 'main') {
  const git = simpleGit();
  try {
    const branches = await git.branchLocal();
    const allBranches = branches.all.filter(b => !b.startsWith('remotes/'));
    const merged = await getMergedBranches(targetBranch);

    return allBranches.filter(b =>
      !isProtectedBranch(b) &&
      b !== targetBranch &&
      !merged.includes(b)
    );
  } catch {
    return [];
  }
}

export async function deleteLocalBranch(branchName, force = false) {
  const git = simpleGit();

  if (isProtectedBranch(branchName)) {
    throw new Error(`Cannot delete protected branch: ${branchName}`);
  }

  const flags = force ? ['-D'] : ['-d'];
  await git.branch([...flags, branchName]);
}

export async function deleteRemoteBranch(branchName) {
  const git = simpleGit();

  if (isProtectedBranch(branchName)) {
    throw new Error(`Cannot delete protected branch: ${branchName}`);
  }

  const remoteName = branchName.replace(/^origin\//, '');

  try {
    await git.push('origin', remoteName, { delete: true });
  } catch (err) {
    throw new Error(`Failed to delete remote branch: ${err.message}`);
  }
}

export async function getBranchStatus(branchName) {
  const git = simpleGit();
  try {
    const status = await git.status();
    if (!status.tracking) {
      return { ahead: 0, behind: 0 };
    }
    const aheadBehind = await git.raw(['rev-list', '--left-right', '--count', `${branchName}...${status.tracking}`]);
    const parts = aheadBehind.trim().split('\t');
    return {
      ahead: parseInt(parts[0]) || 0,
      behind: parseInt(parts[1]) || 0
    };
  } catch {
    return { ahead: 0, behind: 0 };
  }
}