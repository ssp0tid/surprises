# csvql

Run SQL queries against CSV/TSV files from the command line.

Load one or more CSV/TSV files as virtual SQLite tables, run arbitrary SQL (SELECT, JOIN, GROUP BY, aggregates), and output results as formatted tables, CSV, or JSON.

## Installation

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Usage

```
usage: csvql.py [-h] [-q QUERY] [-f FORMAT] [-o OUTPUT] [--schema] [--limit N]
                [--no-header] [--delimiter DELIM] files [files ...]

positional arguments:
  files              CSV/TSV files to load (table name = filename stem)

options:
  -q, --query QUERY  SQL query to execute (required unless --schema)
  -f, --format FMT   Output format: table, csv, tsv, json (default: table)
  -o, --output FILE  Write output to file instead of stdout
  --schema           Show loaded table schemas and exit
  --limit N          Limit output rows (default: unlimited)
  --no-header        CSV files have no header row (use col1, col2, ...)
  --delimiter DELIM  Force delimiter instead of auto-detect
  -h, --help         Show help message
```

## Examples

```bash
# Simple query
python3 csvql.py examples/employees.csv -q "SELECT name, salary FROM employees WHERE salary > 50000"

# JOIN across files
python3 csvql.py examples/employees.csv examples/departments.csv -q \
  "SELECT e.name, d.dept_name FROM employees e JOIN departments d ON e.dept_id = d.id"

# Aggregate with JSON output
python3 csvql.py examples/sales.csv -q "SELECT product, SUM(amount) as total FROM sales GROUP BY product" -f json

# Show schema
python3 csvql.py examples/*.csv --schema

# Output to file
python3 csvql.py examples/employees.csv -q "SELECT * FROM employees" -f csv -o filtered.csv
```

## Features

- Auto-detects delimiter (comma, tab, semicolon, pipe)
- Infers column types (INTEGER, REAL, TEXT) from data
- Handles BOM, quoted fields, empty values, duplicate column names
- Multiple output formats: rich table, CSV, TSV, JSON
- JOIN across multiple files
- Schema inspection mode
- Row limit support
- Graceful error messages for common issues
