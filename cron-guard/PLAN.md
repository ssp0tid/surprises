# CronGuard - CLI Cron Expression Validator

## Project Overview

**Project Name:** CronGuard
**Type:** Node.js CLI Tool (TypeScript)
**Core Functionality:** Validate cron expressions, view next N run times, generate human-readable descriptions, and detect schedule conflicts
**Target Users:** DevOps engineers, developers, and system administrators who work with cron jobs

---

## Architecture

### Technology Stack
- **Runtime:** Node.js 18+
- **Language:** TypeScript
- **Build Tool:** tsup (for CLI binary generation)
- **CLI Framework:** Commander.js or oclif
- **Key Dependencies:**
  - `cron-parser` (v5.x) - Parsing and next run time calculation
  - `cronstrue` (v3.x) - Human-readable descriptions (zero deps, 2.1M weekly downloads)

### Output
- Node.js CLI package published to npm
- Platform-native binary (macOS, Linux, Windows)

---

## Feature Specification

### Core Features

#### 1. Validate Cron Expression
**CLI Flags:** `--validate`, `-v`, or implicit (default when no flag provided)

```
$ cron-guard "*/5 * * * *"
✓ Valid: 5-field cron expression

$ cron-guard "*/5 * * *"
✗ Invalid: Expected 5 fields, got 4

$ cron-guard "60 * * * *"
✗ Invalid: Field 'minute' out of range (0-59)
```

**Validation Checks:**
- Field count (5 for standard, 6 for seconds-based)
- Field value ranges (second: 0-59, minute: 0-59, hour: 0-23, day: 1-31, month: 1-12, weekday: 0-7)
- Special characters (`,` `-` `*` `/` `?` `L` `W` `#`)
- Invalid combinations (e.g., Feb 31)
- Strict mode: prevent both day-of-month and day-of-week (optional flag)

#### 2. Show Next N Run Times
**CLI Flags:** `--next`, `-n` (requires N value)

```
$ cron-guard "0 9 * * 1" --next 5
Next 5 run times for "0 9 * * 1" (At 09:00 AM, only on Monday):
  1. Mon Apr 27 2026 09:00:00
  2. Mon May 04 2026 09:00:00
  3. Mon May 11 2026 09:00:00
  4. Mon May 18 2026 09:00:00
  5. Mon May 25 2026 09:00:00

$ cron-guard "0 */6 * * *" -n 3 --tz America/New_York
Next 3 run times for "0 */6 * * *" (Every 6 hours) [America/New_York]:
  1. Tue Apr 21 2026 00:00:00
  2. Tue Apr 21 2026 06:00:00
  3. Tue Apr 21 2026 12:00:00
```

**Options:**
- `--tz, --timezone` - Set timezone (default: system local)
- `--from` - Start from specific date (default: now)
- Output format: JSON (`--json`) or human-readable table

#### 3. Human-Readable Description
**CLI Flags:** `--describe`, `-d`

```
$ cron-guard "*/5 * * * *"
Every 5 minutes

$ cron-guard "0 9 * * 1-5"
At 09:00 AM, Monday through Friday

$ cron-guard "0 0 1 * *"
At 12:00 AM, every day of the month

$ cron-guard "0 8,12,18 * * *"
At 08:00 AM, 12:00 PM, and 06:00 PM, every day

$ cron-guard "0 0 L * *" -d
At 12:00 AM, on the last day of the month

$ cron-guard "0 9 * * 1L" -d
At 09:00 AM, on the last Monday of the month

$ cron-guard "0 9 * * 1#2" -d
At 09:00 AM, on the second Monday of the month
```

**Options:**
- `--locale` - Output language (default: English)
- `--verbose` - More detailed description ("At 09:00 AM, every day" vs "At 09:00 AM")
- `--use24hour` - Use 24-hour time format

#### 4. Schedule Conflict Detection
**CLI Flags:** `--check-conflicts`, `-c`

```
$ cron-guard "0 9 * * *" --check-conflicts "0 9 * * 1"
Warning: Schedule conflict detected - both run at exactly the same time (09:00)

$ cron-guard "*/5 * * * *" --check-conflicts "*/10 * * * *"
Analysis: Every 5 mins overlaps with every 10 mins at 0, 10, 20, 30, 40, 50 min marks.

$ cron-guard "30 9 * * 1-5" --check-conflicts "0 10 * * *"
No conflict detected
```

**Conflict Types:**
- Exact overlap (same time)
- Subset relationship (*/5 includes */10)
- Partial overlap (time periods that intersect)

**Batch Mode:**
```
$ cron-guard --check-conflicts --file crontab.txt
Analyzing crontab.txt (12 schedules)...
Warning: Line 3 "30 * * * *" conflicts with Line 7 "*/15 * * * *"
Warning: Line 5 "0 0 * * *" contains both day-of-month and day-of-week (ambiguous)
```

---

## Command Interface

### Usage
```
cron-guard <expression> [options]
cron-guard [command]
```

### Commands

| Command | Alias | Description |
|---------|-------|-------------|
| `validate <expr>` | `v` | Validate a cron expression |
| `next <expr>` | `n` | Show next N run times |
| `describe <expr>` | `d` | Human-readable description |
| `conflicts` | `c` | Check schedule conflicts |

### Global Options

| Flag | Alias | Description | Default |
|------|------|-------------|---------|
| `--help` | `-h` | Show help | - |
| `--version` | `-V` | Show version | - |
| `--json` | `-j` | Output as JSON | false |
| `--quiet` | `-q` | Suppress non-essential output | false |
| `--verbose` | `-v` | Enable verbose output | false |

---

## File Structure

```
cron-guard/
├── src/
│   ├── cli.ts              # CLI entry point (Commander.js)
│   ├── commands/
│   │   ├── validate.ts     # Validation command
│   │   ├── next.ts       # Next run times command
│   │   ├── describe.ts    # Description command
│   │   └── conflicts.ts   # Conflict detection command
│   ├── lib/
│   │   ├── parser.ts      # Cron expression parsing
│   │   ├── validator.ts   # Validation logic
│   │   ├── humanize.ts    # Human-readable conversion
│   │   ├── conflicts.ts  # Conflict detection logic
│   │   └── formatter.ts  # Output formatting
│   └── types/
│       └── index.ts      # TypeScript types
├── test/
│   ├── cli.test.ts
│   ├── parser.test.ts
│   ├── validator.test.ts
│   ├── humanize.test.ts
│   └── conflicts.test.ts
├── package.json
├── tsconfig.json
├── tsup.config.ts
└── README.md
```

---

## Implementation Phases

### Phase 1: Project Setup
- [ ] Initialize Node.js project with TypeScript
- [ ] Configure tsup for CLI binary
- [ ] Set up testing (Vitest or Jest)
- [ ] Install dependencies (cron-parser, cronstrue, commander)
- [ ] Verify build produces working binary

### Phase 2: Core Library
- [ ] Implement parser wrapper with error handling
- [ ] Implement validator with field range checks
- [ ] Implement human-readable converter
- [ ] Implement conflict detector
- [ ] Implement output formatter

### Phase 3: CLI Commands
- [ ] Implement validate command
- [ ] Implement next command with timezone support
- [ ] Implement describe command with i18n
- [ ] Implement conflicts command
- [ ] Add global options (--json, --verbose)

### Phase 4: Polish
- [ ] Add colored output (chalk or picocolors)
- [ ] Add shell completion (bash, zsh, fish)
- [ ] Add integration tests
- [ ] Build and publish

---

## Dependencies

### Required
```json
{
  "cron-parser": "^5.0.0",
  "cronstrue": "^3.0.0",
  "commander": "^13.0.0"
}
```

### Dev
```json
{
  "typescript": "^5.7.0",
  "tsup": "^8.0.0",
  "vitest": "^3.0.0",
  "@types/node": "^22.0.0"
}
```

---

## CLI Examples

### Validate
```bash
$ cron-guard "*/15 * * * *"
✓ Valid: Every 15 minutes

$ cron-guard "59 23 * * *" --strict
✗ Error: Strict mode - Cannot specify day-of-month OR day-of-week
```

### Next Run Times
```bash
$ cron-guard "0 */4 * * *" --next 6 --tz UTC
1. 2026-04-21T00:00:00Z
2. 2026-04-21T04:00:00Z
3. 2026-04-21T08:00:00Z
4. 2026-04-21T12:00:00Z
5. 2026-04-21T16:00:00Z
6. 2026-04-21T20:00:00Z
```

### Describe
```bash
$ cron-guard "0 0 1,15 * *" -d
At 12:00 AM, on day 1 and 15 of the month

$ cron-guard "*/30 * 9-17 * * mon-fri" --verbose
Every 30 minutes, between 09:00 AM and 05:00 PM, Monday through Friday
```

### Conflicts
```bash
$ cron-guard --check-conflicts -f ./crontab
Loaded 5 expressions from ./crontab
✓ No conflicts detected

$ cron-guard --conflicts "*/5 * * *" "*/10 * * *" -j
{
  "conflicts": true,
  "analysis": "*/5 runs 12x/hour, */10 runs 6x/hour",
  "overlap_points": ["*:00", "*:10", "*:20", "*:30", "*:40", "*:50"]
}
```

---

## Success Criteria

1. **Validation:** Correctly identifies valid/invalid expressions with clear error messages
2. **Next Runs:** Accurate next N run times with timezone support
3. **Description:** Human-readable output that accurately reflects expression intent
4. **Conflict Detection:** Detects exact overlaps and subset relationships
5. **UX:** Sub-100ms response time, colored output, JSON output support

---

## Notes

- Use strict mode by default? Consider making optional
- Support 6-field cron (with seconds) - make this a flag
- Conflict detection for many expressions may need optimization
- Consider adding "explain" mode that breaks down each field
- Shell completion would significantly improve UX