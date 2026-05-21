# Git Branch Cleanup CLI - Implementation Plan

## Project Overview
- **Name**: git-branch-cleanup
- **Type**: CLI Tool (Node.js)
- **Core Functionality**: Find and delete merged/unmerged git branches locally and remotely with interactive selection
- **Target Users**: Developers managing multiple git repositories

## Dependencies
- `commander` - CLI argument parsing
- `simple-git` - Git operations
- `inquirer` - Interactive prompts
- `chalk` - Colored output

## CLI Interface

### Commands
1. `list` - List branches with status (merged/unmerged/merged-to-main)
2. `delete` - Delete selected branches with confirmation
3. `cleanup` - Interactive cleanup mode

### Options
- `--local` - Only operate on local branches (default)
- `--remote` - Only operate on remote branches
- `--merged-to <branch>` - Filter branches merged to specific branch
- `--dry-run` - Show what would be deleted without actually deleting
- `--force` - Skip confirmation prompts

## Features
1. List local/remote branches with merge status
2. Interactive multi-select for branch deletion
3. Preview what will be deleted
4. Support for both local and remote branch cleanup
5. Filter by merge status
6. Dry-run mode for safe operation

## File Structure
```
git-branch-cleanup/
├── package.json
├── src/
│   ├── index.js      # Entry point
│   ├── commands/
│   │   ├── list.js   # List branches
│   │   └── delete.js # Delete branches
│   └── utils/
│       ├── git.js    # Git operations
│       └── format.js # Output formatting
└── README.md
```

## Error Handling
- Validate git repository
- Handle detached HEAD state
- Protect main/master/develop branches
- Handle permission errors