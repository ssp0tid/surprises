# Shell Script Hub

A CLI tool to organize, tag, search, and execute shell scripts with variable templating and execution history tracking.

## Features

- **Script Registry** - Store and manage shell scripts in a local SQLite database
- **Tag Organization** - Organize scripts with custom tags
- **Full-Text Search** - Search across script names, descriptions, and content
- **Template Variables** - Use `{{variable}}` syntax for dynamic script execution
- **Execution History** - Track when scripts were run, what variables were used, and the results
- **Import/Export** - Move scripts in and out of the hub

## Installation

### From Source

```bash
# Clone or download the project
cd shell-script-hub

# Install in development mode
pip install -e .

# Or install dependencies only
pip install -e ".[dev]"
```

### Verify Installation

```bash
shell-script-hub --help
```

## Quick Start

```bash
# 1. Initialize the hub in your project directory
shell-script-hub init

# 2. Add your first script
shell-script-hub add deploy.sh -d "Deploy application to production" -t "deploy,ops"

# 3. List all scripts
shell-script-hub list

# 4. Run a script
shell-script-hub run deploy.sh -v env=production
```

## CLI Commands

### init

Initialize the script hub in the current directory. Creates a `.shell_script_hub/scripts.db` SQLite database.

```bash
shell-script-hub init
```

**Output:**
```
Initialized shell-script-hub at /path/to/current/.shell_script_hub/scripts.db
```

---

### add

Add a shell script to the registry.

```bash
shell-script-hub add <script_path> [options]
```

**Arguments:**
- `script_path` - Path to the script file (must exist)

**Options:**
- `-n, --name TEXT` - Name for the script (default: filename without extension)
- `-d, --description TEXT` - Script description
- `-t, --tags TEXT` - Comma-separated tags
- `-u, --update` - Update existing script instead of failing

**Examples:**

```bash
# Add with automatic name (from filename)
shell-script-hub add ./scripts/backup.sh -t "backup,daily"

# Add with custom name and description
shell-script-hub add ./deploy.sh -n deploy-prod -d "Deploy to production" -t "deploy,prod"

# Update an existing script
shell-script-hub add ./updated-script.sh -n my-script -u
```

---

### list

List all registered scripts, optionally filtered by tag or search query.

```bash
shell-script-hub list [options]
```

**Options:**
- `-t, --tag TEXT` - Filter by tag
- `-s, --search TEXT` - Search query

**Examples:**

```bash
# List all scripts
shell-script-hub list

# Filter by tag
shell-script-hub list -t deploy

# Search scripts
shell-script-hub list -s backup
```

**Output:**
```
┌─────────────┬─────────────────────┬──────────┐
│ Name       │ Description          │ Tags     │
├─────────────┼─────────────────────┼──────────┤
│ deploy-prod │ Deploy to production │ deploy   │
│ backup-db  │ Daily database backup│ backup  │
└─────────────┴─────────────────────┴──────────┘
```

---

### search

Full-text search across all script metadata and content.

```bash
shell-script-hub search <query>
```

**Arguments:**
- `query` - Search term

**Examples:**

```bash
shell-script-hub search docker
shell-script-hub search "git clone"
```

---

### run

Execute a registered script with variable substitution.

```bash
shell-script-hub run <name> [options]
```

**Arguments:**
- `name` - Script name to execute

**Options:**
- `-v, --var TEXT` - Variables as `key=value` (can be repeated)
- `-a, --all-vars TEXT` - Variables as JSON string

**Template Syntax:**

Scripts support `{{variable}}` syntax for variable substitution:

```bash
#!/bin/bash
echo "Deploying {{environment}} to {{region}}"
kubectl apply -f {{manifest_path}}
```

**Examples:**

```bash
# Run with single variable
shell-script-hub run deploy-prod -v environment=production

# Run with multiple variables
shell-script-hub run deploy-prod -v environment=production -v region=us-west-2

# Run with JSON variables
shell-script-hub run deploy-prod -a '{"environment": "production", "region": "us-west-2"}'
```

**Exit Code:**
- Returns the script's exit code (0 = success, non-zero = failure)
- If variables are missing, exits with error and lists missing variables

---

### history

View execution history for scripts.

```bash
shell-script-hub history [options]
```

**Options:**
- `-n, --script-name TEXT` - Filter by script name
- `-l, --limit INTEGER` - Limit results (default: 50)

**Output:**
```
┌─────────────┬───────────┬────────────────────┐
│ Script      │ Exit Code │ Executed At         │
├─────────────┼───────────┼────────────────────┤
│ deploy-prod │ 0         │ 2024-01-15 10:30:00 │
│ deploy-prod │ 0         │ 2024-01-14 10:28:00 │
└─────────────┴───────────┴────────────────────┘
```

---

### export

Export a registered script to a file.

```bash
shell-script-hub export <name> [options]
```

**Arguments:**
- `name` - Script name to export

**Options:**
- `-o, --output PATH` - Output file (default: stdout)

**Examples:**

```bash
# Export to file
shell-script-hub export deploy-prod -o ./my-deploy.sh

# Print to stdout
shell-script-hub export deploy-prod
```

---

### import

Import a script from a file.

```bash
shell-script-hub import <file_path> [options]
```

**Arguments:**
- `file_path` - Path to the script file (must exist)

**Options:**
- `-n, --name TEXT` - Name for the script (default: filename)
- `-d, --description TEXT` - Script description
- `-t, --tags TEXT` - Comma-separated tags
- `-u, --update` - Update existing script

**Examples:**

```bash
# Import from file
shell-script-hub import ./backup.sh -t "backup,daily"

# Import with custom name
shell-script-hub import ./legacy-script.sh -n my-new-script -d "Legacy backup script"
```

## Database

The hub uses SQLite stored at `.shell_script_hub/scripts.db`.

**Schema:**

- `scripts` table: id, name, description, content, tags, created_at, updated_at
- `execution_history` table: id, script_id, script_name, variables_used, exit_code, output, error, executed_at

## Development

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run linters
ruff check .
black --check .

# Run tests
pytest
```

## License

MIT