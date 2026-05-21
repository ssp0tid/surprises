# CronGuard

CLI tool for validating cron expressions, viewing next run times, generating human-readable descriptions, and detecting schedule conflicts.

## Installation

### From npm (recommended)

```bash
npm install -g cron-guard
```

### From source

```bash
git clone https://github.com/your-repo/cron-guard.git
cd cron-guard
npm install
npm run build
npm link
```

### Run without installation

```bash
npx cron-guard "*/5 * * * *"
```

Or after building:

```bash
node dist/index.js "*/5 * * * *"
```

## Usage

### Validate a cron expression

```bash
cron-guard "*/5 * * *"
# ✓ Valid: Every 5 minutes

cron-guard "60 * * * *"
# ✗ Invalid: Field 'minute' out of range (0-59)

cron-guard "* * * * *" --strict
# ✗ Invalid: Strict mode - Cannot specify both day-of-month and day-of-week
```

### Show next run times

```bash
cron-guard "0 9 * * *" --next 5
# Next 5 run times for "0 9 * * *" (At 09:00) [America/New_York]:
#   1. 2026-04-27T09:00:00.000-04:00
#   2. 2026-04-28T09:00:00.000-04:00

cron-guard "0 */6 * * *" --next 3 --timezone UTC

# Start from specific date
cron-guard "0 9 * * *" --next 5 --from 2026-01-01
```

### Human-readable description

```bash
cron-guard "*/5 * * * *" --describe
# Every 5 minutes

cron-guard "0 9 * * 1-5" -d
# At 09:00, Monday through Friday

cron-guard "0 0 1 * *" -d
# At 12:00 AM, on day 1 of the month

# Verbose mode
cron-guard "0 9 * * *" -d --verbose
# At 09:00 AM, every day
```

### Detect schedule conflicts

```bash
# Check two expressions for conflicts
cron-guard conflicts "0 9 * * *" "0 9 * * 1"
# ⚠ Schedule conflict detected - both run at exactly the same time

# Check subset relationships
cron-guard conflicts "*/5 * * * *" "*/10 * * * *"
# ⚠ "*/5 * * * *" runs more frequently and includes all times from "*/10 * * * *"

# Batch check from crontab file
cron-guard conflicts --file ./crontab
```

### Using subcommands

```bash
cron-guard validate "*/15 * * * *"
cron-guard next "0 9 * * *" --count 5
cron-guard describe "0 0 L * *"
cron-guard conflicts "0 9 * * *" "0 10 * * *"
```

### JSON output

```bash
cron-guard "*/5 * * * *" --json
# {
#   "valid": true,
#   "description": "Every 5 minutes"
# }

cron-guard "0 9 * * *" --next 3 --json
# {
#   "expression": "0 9 * * *",
#   "timezone": "America/New_York",
#   "nextRuns": ["2026-04-27T09:00:00.000-04:00", ...]
# }
```

## Options

### Global Options

| Flag | Alias | Description | Default |
|------|-------|-------------|---------|
| `--json` | `-j` | Output as JSON | false |
| `--quiet` | `-q` | Suppress non-essential output | false |
| `--help` | `-h` | Show help | - |
| `--version` | `-V` | Show version | - |

### Expression Options

| Flag | Alias | Description | Default |
|------|-------|-------------|---------|
| `--next <n>` | `-n` | Show next N run times | - |
| `--describe` | `-d` | Show human-readable description | - |
| `--timezone <tz>` | `-t` | Set timezone | System local |
| `--from <date>` | `-f` | Start from specific date (ISO format) | Now |
| `--locale <locale>` | `-l` | Locale for description (en, es, fr, de, etc.) | en |
| `--verbose` | `-v` | More detailed description | false |
| `--strict` | `-s` | Reject both day-of-month and day-of-week | false |

## Examples

```bash
# Every 5 minutes
cron-guard "*/5 * * * *"

# Every hour at minute 30
cron-guard "30 * * * *"

# At 9:00 AM on weekdays
cron-guard "0 9 * * 1-5"

# At midnight on the 1st of every month
cron-guard "0 0 1 * *"

# Every 6 hours
cron-guard "0 */6 * * *"

# At 9:00 AM on the last Monday of the month
cron-guard "0 9 * * 1L"

# At 9:00 AM on the second Monday of the month
cron-guard "0 9 * * 1#2"

# Using localizations
cron-guard "0 9 * * *" --describe --locale es
# A las 09:00
```

## Supported Cron Features

- Standard 5-field cron (minute, hour, day of month, month, day of week)
- 6-field cron with seconds
- Special characters: `*`, `/`, `-`, `,`, `?`, `L`, `W`, `#`
- Timezone support via IANA timezone names

## License

MIT
