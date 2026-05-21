import { execa } from 'execa';
import * as path from 'path';

export interface GitStatus {
  branch: string;
  ahead: number;
  behind: number;
  staged: string[];
  modified: string[];
  untracked: string[];
  conflicted: string[];
}

export interface GitCommit {
  hash: string;
  message: string;
  author: string;
  date: string;
}

export interface GitDiff {
  file: string;
  additions: number;
  deletions: number;
  patch: string;
}

export class GitManager {
  private repoPath: string;
  private gitBin: string = 'git';

  constructor(repoPath: string) {
    this.repoPath = path.resolve(repoPath);
  }

  /**
   * Execute git command
   */
  private async git(...args: string[]): Promise<{ stdout: string; stderr: string }> {
    return execa(this.gitBin, args, {
      cwd: this.repoPath,
      extendEnv: true,
    }) as Promise<{ stdout: string; stderr: string }>;
  }

  /**
   * Execute git command with custom options
   */
  private async gitRaw(
    args: string[],
    options?: { stdio?: 'pipe' | 'inherit' }
  ) {
    return execa(this.gitBin, args, {
      cwd: this.repoPath,
      stdio: options?.stdio || 'pipe',
      extendEnv: true,
    });
  }

  /**
   * Check if directory is a git repository
   */
  async isRepo(): Promise<boolean> {
    try {
      await this.git('rev-parse', '--git-dir');
      return true;
    } catch {
      return false;
    }
  }

  /**
   * Clone repository
   */
  async clone(repoUrl: string): Promise<void> {
    const { execa } = await import('execa');
    await execa(this.gitBin, ['clone', repoUrl, this.repoPath], {
      stdio: 'inherit',
    });
  }

  /**
   * Get current branch name
   */
  async getBranch(): Promise<string> {
    const { stdout } = await this.git('branch', '--show-current');
    return stdout.trim();
  }

  /**
   * Checkout branch
   */
  async checkout(branch: string): Promise<void> {
    await this.git('checkout', branch);
  }

  /**
   * Create and checkout new branch
   */
  async createBranch(branch: string): Promise<void> {
    await this.git('checkout', '-b', branch);
  }

  /**
   * List all branches
   */
  async listBranches(remote = false): Promise<string[]> {
    const args = remote ? ['branch', '-r'] : ['branch'];
    const { stdout } = await this.git(...args);
    
    return stdout
      .split('\n')
      .map((b) => b.trim().replace(/^\* /, ''))
      .filter((b) => b);
  }

  /**
   * Get current git status
   */
  async status(): Promise<GitStatus> {
    const { stdout } = await this.git('status', '--porcelain=v1', '-b');
    const lines = stdout.split('\n').filter((l) => l.trim());

    const status: GitStatus = {
      branch: '',
      ahead: 0,
      behind: 0,
      staged: [],
      modified: [],
      untracked: [],
      conflicted: [],
    };

    // Parse branch line
    const branchLine = lines.find((l) => l.startsWith('## '));
    if (branchLine) {
      const branchMatch = branchLine.match(/^## ([^\s]+)/);
      if (branchMatch) {
        status.branch = branchMatch[1].replace(/\.\.\..*/, '');
        
        // Check ahead/behind
        const aheadMatch = branchLine.match(/ahead (\d+)/);
        const behindMatch = branchLine.match(/behind (\d+)/);
        if (aheadMatch) status.ahead = parseInt(aheadMatch[1], 10);
        if (behindMatch) status.behind = parseInt(behindMatch[1], 10);
      }
    }

    // Parse file lines
    for (const line of lines) {
      if (line.startsWith('## ')) continue;

      const indexStatus = line.substring(0, 1);
      const workTreeStatus = line.substring(1, 2);
      const file = line.substring(3).trim();

      if (indexStatus === '?' || workTreeStatus === '?') {
        status.untracked.push(file);
      } else if (indexStatus === 'U' || workTreeStatus === 'U') {
        status.conflicted.push(file);
      } else if (indexStatus !== ' ' || workTreeStatus !== ' ') {
        status.modified.push(file);
      }
    }

    return status;
  }

  /**
   * Stage files
   */
  async add(files: string | string[]): Promise<void> {
    const fileList = Array.isArray(files) ? files : [files];
    await this.git('add', ...fileList);
  }

  /**
   * Unstage files
   */
  async reset(files: string | string[]): Promise<void> {
    const fileList = Array.isArray(files) ? files : [files];
    await this.git('reset', 'HEAD', ...fileList);
  }

  /**
   * Commit staged changes
   */
  async commit(message: string): Promise<string> {
    const { stdout } = await this.git('commit', '-m', message);
    const { stdout: hash } = await this.git('rev-parse', 'HEAD');
    return hash.trim();
  }

  /**
   * Amend last commit
   */
  async amend(message?: string): Promise<void> {
    const args = ['commit', '--amend', '--no-edit'];
    if (message) {
      args.push('-m', message);
    }
    await this.git(...args);
  }

  /**
   * Get commit history
   */
  async log(maxCount = 10, options?: { file?: string; author?: string }): Promise<GitCommit[]> {
    const args = [
      'log',
      `--max-count=${maxCount}`,
      '--format=%H|%s|%an|%ad',
      '--date=iso',
    ];

    if (options?.file) {
      args.push('--', options.file);
    }
    if (options?.author) {
      args.push(`--author=${options.author}`);
    }

    const { stdout } = await this.git(...args);
    
    return stdout.split('\n').filter((l) => l.trim()).map((line) => {
      const [hash, message, author, date] = line.split('|');
      return {
        hash: hash.trim(),
        message: message.trim(),
        author: author.trim(),
        date: date.trim(),
      };
    });
  }

  /**
   * Get diff between commits, branches, or working tree
   */
  async diff(
    options?: { from?: string; to?: string; file?: string }
  ): Promise<GitDiff[]> {
    const args = ['diff', '--numstat', '--patch'];

    if (options?.from) {
      args.push(options.from);
    }
    if (options?.to) {
      args.push(options.to);
    }
    if (options?.file) {
      args.push('--', options.file);
    }

    const { stdout } = await this.git(...args);
    
    // Parse diff output
    const diffs: GitDiff[] = [];
    const fileRegex = /diff --git a\/(.+?) b\/(.+)/g;
    const numstatRegex = /(\d+|-)\s+(\d+|-)\s+(.+)/g;

    let match;
    let currentFile = '';
    let currentAdditions = 0;
    let currentDeletions = 0;
    let currentPatch = '';

    const lines = stdout.split('\n');
    for (const line of lines) {
      if (line.startsWith('diff --git')) {
        // Save previous
        if (currentFile) {
          diffs.push({
            file: currentFile,
            additions: currentAdditions,
            deletions: currentDeletions,
            patch: currentPatch,
          });
        }
        const fileMatch = line.match(/b\/(.+)/);
        currentFile = fileMatch ? fileMatch[1] : '';
        currentAdditions = 0;
        currentDeletions = 0;
        currentPatch = '';
      } else if (/^\d+\s+\d+/.test(line)) {
        const [add, del] = line.split(/\s+/);
        currentAdditions += parseInt(add, 10) || 0;
        currentDeletions += parseInt(del, 10) || 0;
        currentPatch += line + '\n';
      } else if (currentFile) {
        currentPatch += line + '\n';
      }
    }

    // Add last
    if (currentFile) {
      diffs.push({
        file: currentFile,
        additions: currentAdditions,
        deletions: currentDeletions,
        patch: currentPatch,
      });
    }

    return diffs;
  }

  /**
   * Fetch from remote
   */
  async fetch(remote = 'origin'): Promise<void> {
    await this.git('fetch', remote);
  }

  /**
   * Pull from remote
   */
  async pull(branch: string, remote = 'origin'): Promise<void> {
    await this.git('pull', remote, branch);
  }

  /**
   * Push to remote
   */
  async push(branch: string, remote = 'origin'): Promise<void> {
    await this.git('push', remote, branch);
  }

  /**
   * Force push to remote
   */
  async forcePush(branch: string, remote = 'origin'): Promise<void> {
    await this.git('push', '--force', remote, branch);
  }

  /**
   * Merge branch
   */
  async merge(branch: string, message?: string): Promise<void> {
    const args = ['merge', branch];
    if (message) {
      args.push('-m', message);
    }
    await this.git(...args);
  }

  /**
   * Rebase onto branch
   */
  async rebase(branch: string): Promise<void> {
    await this.git('rebase', branch);
  }

  /**
   * Stash changes
   */
  async stash(message?: string): Promise<void> {
    const args = ['stash', 'push'];
    if (message) {
      args.push('-m', message);
    }
    await this.git(...args);
  }

  /**
   * Pop stash
   */
  async stashPop(): Promise<void> {
    await this.git('stash', 'pop');
  }

  /**
   * List stash
   */
  async stashList(): Promise<{ index: number; message: string }[]> {
    const { stdout } = await this.git('stash', 'list', '--format=%s');
    
    return stdout.split('\n').filter((l) => l.trim()).map((line, index) => ({
      index,
      message: line.trim(),
    }));
  }

  /**
   * Get remote URL
   */
  async getRemote(remote = 'origin'): Promise<string | null> {
    try {
      const { stdout } = await this.git('remote', 'get-url', remote);
      return stdout.trim();
    } catch {
      return null;
    }
  }

  /**
   * Set remote URL
   */
  async setRemote(remote: string, url: string): Promise<void> {
    await this.git('remote', 'set-url', remote, url);
  }

  /**
   * Add remote
   */
  async addRemote(remote: string, url: string): Promise<void> {
    await this.git('remote', 'add', remote, url);
  }
}
