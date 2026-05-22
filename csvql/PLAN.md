# csvql

**Run SQL queries against CSV/TSV files from the command line.**

Load one or more CSV/TSV files as virtual SQLite tables, run arbitrary SQL (SELECT, JOIN, GROUP BY, aggregates), and output results as formatted tables, CSV, or JSON.

## Tech Stack

- Python 3 (single file, no external dependencies beyond rich)
- sqlite3 (stdlib) — in-memory database engine
- csv (stdlib) — file parsing
- argparse (stdlib) — CLI argument parsing
- rich (pip) — pretty table output
- json (stdlib) — JSON output format

## Constraints

- Single main file: `csvql.py`
- Create a virtual environment for rich dependency
- No external API keys
- Handle files up to ~100MB gracefully
- Auto-detect delimiter (comma vs tab)
- Auto-infer column types (int, float, text)

## File Structure

```
csvql/
├── PLAN.md
├── README.md
├── csvql.py          # Main entry point
├── requirements.txt  # rich
└── examples/
    ├── employees.csv
    ├── departments.csv
    └── sales.csv
```

## Features

### 1. File Loading (`load_files()`)
```python
def load_files(db: sqlite3.Connection, file_paths: list[str]) -> dict[str, list[str]]:
    """
    Load CSV/TSV files into SQLite tables.
    Table name = filename stem (e.g., employees.csv -> employees)
    Returns dict of {table_name: [column_names]}
    """
```
- Auto-detect delimiter using `csv.Sniffer` on first 8KB
- Infer column types by sampling first 100 rows:
  - Try int(val), then float(val), fallback to TEXT
- Create table with inferred types (INTEGER, REAL, TEXT)
- Bulk INSERT with executemany for performance
- Handle: BOM, quoted fields, empty values (NULL), duplicate column names (append _1, _2)

### 2. Type Inference (`infer_column_types()`)
```python
def infer_column_types(rows: list[list[str]], headers: list[str]) -> list[str]:
    """
    Sample rows and return SQLite type for each column.
    Returns list of 'INTEGER', 'REAL', or 'TEXT'.
    """
```
- Skip empty/null values when inferring
- If >80% of non-null values parse as int → INTEGER
- If >80% parse as float → REAL
- Otherwise → TEXT

### 3. Query Execution (`execute_query()`)
```python
def execute_query(db: sqlite3.Connection, sql: str) -> tuple[list[str], list[tuple]]:
    """
    Execute SQL query, return (column_names, rows).
    Raises QueryError on invalid SQL.
    """
```
- Return column names from cursor.description
- Limit rows with --limit flag (default: no limit)
- Timeout protection: set busy_timeout to 30s

### 4. Output Formatting
```python
def format_output(columns: list[str], rows: list[tuple], fmt: str, file=None):
    """
    Output results in specified format.
    fmt: 'table' | 'csv' | 'json' | 'tsv'
    file: optional output file path (default: stdout)
    """
```
- `table`: rich Table with borders, colored headers, row count footer
- `csv`: standard CSV to stdout or file
- `tsv`: tab-separated to stdout or file  
- `json`: array of objects [{col: val, ...}, ...]

### 5. Schema Inspection (`show_schema()`)
```python
def show_schema(db: sqlite3.Connection, tables: dict[str, list[str]]):
    """Print loaded table schemas with column names and types."""
```
- `--schema` flag shows all loaded tables, columns, types, row counts

### 6. CLI Interface (argparse)
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

### 7. Error Handling
- FileNotFoundError → clear message with filename
- csv parsing errors → show line number and content
- SQL syntax errors → show sqlite3 error message with hint
- Empty files → warning, skip loading
- Permission errors → clear message

## Example Usage

```bash
# Simple query
python3 csvql.py employees.csv -q "SELECT name, salary FROM employees WHERE salary > 50000"

# JOIN across files
python3 csvql.py employees.csv departments.csv -q \
  "SELECT e.name, d.dept_name FROM employees e JOIN departments d ON e.dept_id = d.id"

# Aggregate with JSON output
python3 csvql.py sales.csv -q "SELECT product, SUM(amount) as total FROM sales GROUP BY product" -f json

# Show schema
python3 csvql.py *.csv --schema

# Output to file
python3 csvql.py data.csv -q "SELECT * FROM data" -f csv -o filtered.csv
```

## Example Data

### employees.csv
```
id,name,dept_id,salary,hire_date
1,Alice,1,75000,2020-03-15
2,Bob,2,62000,2019-07-22
3,Charlie,1,80000,2018-01-10
4,Diana,3,55000,2021-11-01
5,Eve,2,70000,2020-06-30
```

### departments.csv
```
id,dept_name,location
1,Engineering,Building A
2,Marketing,Building B
3,Sales,Building C
```

### sales.csv
```
id,employee_id,product,amount,date
1,1,Widget,1500.50,2024-01-15
2,3,Gadget,2300.00,2024-01-20
3,2,Widget,800.75,2024-02-01
4,5,Doohickey,3100.00,2024-02-15
5,4,Gadget,1200.00,2024-03-01
```
