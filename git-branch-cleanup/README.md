# git-branch-cleanup

CLI tool to find and delete merged/unmerged git branches locally and remotely.

## Features

- List branches with merge status (merged to main, unmerged)
- Interactive branch selection with multi-select
- Delete local and remote branches
- Dry-run mode to preview deletions
- Protected branch safety (main, master, develop)
- Force delete for already-merged branches

## Installation

```bash
cd git-branch-cleanup
npm install
npm link
```

## Usage

### List branches with merge status

```bash
# List all local branches merged to main
git-branch-cleanup list

# List local branches only
git-branch-cleanup list --local

# List remote branches only
git-branch-cleanup list --remote

# Show branches merged to specific branch
git-branch-cleanup list --merged-to develop

# Show unmerged branches
git-branch-cleanup list --unmerged
```

### Delete branches

```bash
# Delete branches merged to main (interactive selection)
git-branch-cleanup delete

# Dry run - show what would be deleted
git-branch-cleanup delete --dry-run

# Force delete without confirmation
git-branch-cleanup delete --force

# Delete specific branches
git-branch-cleanup delete --branches feature-1 feature-2

# Delete remote branches
git-branch-cleanup delete --remote
```

### Interactive cleanup mode

```bash
# Interactive branch selection and deletion
git-branch-cleanup cleanup

# With dry-run
git-branch-cleanup cleanup --dry-run
```

## Options

| Option | Description |
|--------|-------------|
| `-l, --local` | Operate on local branches only |
| `-r, --remote` | Operate on remote branches only |
| `-m, --merged-to <branch>` | Filter branches merged to this branch (default: main) |
| `-u, --unmerged` | Show unmerged branches |
| `-d, --dry-run` | Preview without actually deleting |
| `-f, --force` | Skip confirmation prompts |
| `-b, --branches <branches...>` | Specific branches to delete |

## Protected Branches

The following branches cannot be deleted:
- main
- master
- develop
- HEAD

## License

MIT