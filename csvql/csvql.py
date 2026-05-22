#!/usr/bin/env python3
"""csvql - Run SQL queries against CSV/TSV files from the command line."""

import argparse
import csv
import json
import os
import sqlite3
import sys
from pathlib import Path


class CsvqlError(Exception):
    """Base error for csvql."""


class QueryError(CsvqlError):
    """Invalid SQL query."""


class FileLoadError(CsvqlError):
    """Error loading a CSV/TSV file."""


def detect_delimiter(file_path: str, forced_delimiter: str | None = None) -> str:
    """Auto-detect delimiter using csv.Sniffer on first 8KB."""
    if forced_delimiter:
        return forced_delimiter
    try:
        with open(file_path, "r", newline="", encoding="utf-8-sig") as f:
            sample = f.read(8192)
        dialect = csv.Sniffer().sniff(sample, delimiters=",\t;|")
        return dialect.delimiter
    except csv.Error:
        return ","


def deduplicate_headers(headers: list[str]) -> list[str]:
    """Append _1, _2, etc. to duplicate column names."""
    seen: dict[str, int] = {}
    result = []
    for h in headers:
        name = h.strip() if h.strip() else "col"
        if name in seen:
            seen[name] += 1
            result.append(f"{name}_{seen[name]}")
        else:
            seen[name] = 0
            result.append(name)
    return result


def infer_column_types(rows: list[list[str]], headers: list[str]) -> list[str]:
    """
    Sample rows and return SQLite type for each column.
    Returns list of 'INTEGER', 'REAL', or 'TEXT'.
    If >80% of non-null values parse as int -> INTEGER.
    If >80% parse as float -> REAL.
    Otherwise -> TEXT.
    """
    sample = rows[:100]
    num_cols = len(headers)
    types = []

    for col_idx in range(num_cols):
        int_count = 0
        float_count = 0
        total = 0

        for row in sample:
            if col_idx >= len(row):
                continue
            val = row[col_idx].strip()
            if val == "" or val.lower() == "null":
                continue
            total += 1
            try:
                int(val)
                int_count += 1
                continue
            except ValueError:
                pass
            try:
                float(val)
                float_count += 1
            except ValueError:
                pass

        if total == 0:
            types.append("TEXT")
        elif int_count / total > 0.8:
            types.append("INTEGER")
        elif (int_count + float_count) / total > 0.8:
            types.append("REAL")
        else:
            types.append("TEXT")

    return types


def load_files(
    db: sqlite3.Connection,
    file_paths: list[str],
    no_header: bool = False,
    forced_delimiter: str | None = None,
) -> dict[str, list[str]]:
    """
    Load CSV/TSV files into SQLite tables.
    Table name = filename stem (e.g., employees.csv -> employees)
    Returns dict of {table_name: [column_names]}
    """
    tables: dict[str, list[str]] = {}

    for file_path in file_paths:
        if not os.path.exists(file_path):
            raise FileLoadError(f"File not found: {file_path}")

        if not os.access(file_path, os.R_OK):
            raise FileLoadError(f"Permission denied: {file_path}")

        if os.path.getsize(file_path) == 0:
            print(f"Warning: Skipping empty file: {file_path}", file=sys.stderr)
            continue

        table_name = Path(file_path).stem
        table_name = table_name.replace("-", "_").replace(" ", "_")

        delimiter = detect_delimiter(file_path, forced_delimiter)

        try:
            with open(file_path, "r", newline="", encoding="utf-8-sig") as f:
                reader = csv.reader(f, delimiter=delimiter)

                if no_header:
                    rows = list(reader)
                    if not rows:
                        print(
                            f"Warning: Skipping empty file: {file_path}",
                            file=sys.stderr,
                        )
                        continue
                    num_cols = max(len(r) for r in rows)
                    headers = [f"col{i + 1}" for i in range(num_cols)]
                else:
                    try:
                        headers_raw = next(reader)
                    except StopIteration:
                        print(
                            f"Warning: Skipping empty file: {file_path}",
                            file=sys.stderr,
                        )
                        continue
                    headers = deduplicate_headers(headers_raw)
                    rows = list(reader)

        except csv.Error as e:
            raise FileLoadError(f"CSV parsing error in {file_path}: {e}") from e
        except UnicodeDecodeError as e:
            raise FileLoadError(
                f"Encoding error in {file_path}: {e}. Try saving as UTF-8."
            ) from e

        if not rows:
            print(
                f"Warning: File has headers but no data: {file_path}", file=sys.stderr
            )
            col_types = ["TEXT"] * len(headers)
        else:
            col_types = infer_column_types(rows, headers)

        col_defs = ", ".join(
            f'"{h}" {t}' for h, t in zip(headers, col_types, strict=False)
        )
        create_sql = f'CREATE TABLE IF NOT EXISTS "{table_name}" ({col_defs})'

        try:
            db.execute(create_sql)
        except sqlite3.Error as e:
            raise FileLoadError(
                f"Error creating table for {file_path}: {e}"
            ) from e

        if rows:
            placeholders = ", ".join(["?"] * len(headers))
            insert_sql = f'INSERT INTO "{table_name}" VALUES ({placeholders})'

            converted_rows = []
            for row_idx, row in enumerate(rows):
                padded = row + [""] * (len(headers) - len(row))
                padded = padded[: len(headers)]

                converted = []
                for col_idx, val in enumerate(padded):
                    val = val.strip()
                    if val == "" or val.lower() == "null":
                        converted.append(None)
                    elif col_types[col_idx] == "INTEGER":
                        try:
                            converted.append(int(val))
                        except ValueError:
                            converted.append(val)
                    elif col_types[col_idx] == "REAL":
                        try:
                            converted.append(float(val))
                        except ValueError:
                            converted.append(val)
                    else:
                        converted.append(val)
                converted_rows.append(converted)

            try:
                db.executemany(insert_sql, converted_rows)
            except sqlite3.Error as e:
                raise FileLoadError(
                    f"Error inserting data from {file_path}: {e}"
                ) from e

        db.commit()
        tables[table_name] = headers

    return tables


def execute_query(
    db: sqlite3.Connection, sql: str, limit: int | None = None
) -> tuple[list[str], list[tuple]]:
    """
    Execute SQL query, return (column_names, rows).
    Raises QueryError on invalid SQL.
    """
    if limit is not None:
        sql_upper = sql.strip().upper()
        if "LIMIT" not in sql_upper.split("--")[0]:
            sql = f"{sql.rstrip().rstrip(';')} LIMIT {limit}"

    try:
        cursor = db.execute(sql)
        columns = [desc[0] for desc in cursor.description] if cursor.description else []
        rows = cursor.fetchall()
        return columns, rows
    except sqlite3.OperationalError as e:
        msg = str(e)
        hint = ""
        if "no such table" in msg:
            hint = "\nHint: Table names are derived from filenames (without extension)."
        elif "no such column" in msg:
            hint = "\nHint: Use --schema to see available columns."
        elif "near" in msg:
            hint = "\nHint: Check SQL syntax near the indicated position."
        raise QueryError(f"SQL error: {msg}{hint}") from e
    except sqlite3.Error as e:
        raise QueryError(f"Database error: {e}") from e


def format_output(
    columns: list[str],
    rows: list[tuple],
    fmt: str,
    file: str | None = None,
):
    """
    Output results in specified format.
    fmt: 'table' | 'csv' | 'json' | 'tsv'
    file: optional output file path (default: stdout)
    """
    output = _render_output(columns, rows, fmt)

    if file:
        with open(file, "w", encoding="utf-8") as f:
            f.write(output)
        print(f"Output written to {file}", file=sys.stderr)
    else:
        print(output, end="")


def _render_output(columns: list[str], rows: list[tuple], fmt: str) -> str:
    """Render output to string."""
    if fmt == "json":
        data = []
        for row in rows:
            obj = {}
            for col, val in zip(columns, row, strict=False):
                obj[col] = val
            data.append(obj)
        return json.dumps(data, indent=2, default=str) + "\n"

    elif fmt == "csv":
        import io

        buf = io.StringIO()
        writer = csv.writer(buf)
        writer.writerow(columns)
        writer.writerows(rows)
        return buf.getvalue()

    elif fmt == "tsv":
        import io

        buf = io.StringIO()
        writer = csv.writer(buf, delimiter="\t")
        writer.writerow(columns)
        writer.writerows(rows)
        return buf.getvalue()

    elif fmt == "table":
        return _render_rich_table(columns, rows)

    else:
        return _render_rich_table(columns, rows)


def _render_rich_table(columns: list[str], rows: list[tuple]) -> str:
    """Render a rich formatted table."""
    try:
        from rich.console import Console
        from rich.table import Table

        table = Table(show_header=True, header_style="bold cyan", show_lines=False)
        for col in columns:
            table.add_column(col)
        for row in rows:
            table.add_row(*[str(v) if v is not None else "NULL" for v in row])

        table.caption = f"{len(rows)} row{'s' if len(rows) != 1 else ''}"

        console = Console()
        with console.capture() as capture:
            console.print(table)
        return capture.get()

    except ImportError:
        lines = []
        col_widths = [len(c) for c in columns]
        for row in rows:
            for i, val in enumerate(row):
                col_widths[i] = max(col_widths[i], len(str(val) if val is not None else "NULL"))

        header = " | ".join(c.ljust(col_widths[i]) for i, c in enumerate(columns))
        separator = "-+-".join("-" * w for w in col_widths)
        lines.append(header)
        lines.append(separator)
        for row in rows:
            line = " | ".join(
                (str(v) if v is not None else "NULL").ljust(col_widths[i])
                for i, v in enumerate(row)
            )
            lines.append(line)
        lines.append(f"\n({len(rows)} row{'s' if len(rows) != 1 else ''})")
        return "\n".join(lines) + "\n"


def show_schema(db: sqlite3.Connection, tables: dict[str, list[str]]):
    """Print loaded table schemas with column names and types."""
    try:
        from rich.console import Console
        from rich.table import Table

        console = Console()

        for table_name, columns in tables.items():
            cursor = db.execute(f'SELECT COUNT(*) FROM "{table_name}"')
            row_count = cursor.fetchone()[0]

            cursor = db.execute(f'PRAGMA table_info("{table_name}")')
            col_info = cursor.fetchall()

            schema_table = Table(
                title=f"📋 {table_name} ({row_count} rows)",
                show_header=True,
                header_style="bold green",
            )
            schema_table.add_column("Column", style="cyan")
            schema_table.add_column("Type", style="yellow")

            for col in col_info:
                schema_table.add_row(col[1], col[2])

            console.print(schema_table)
            console.print()

    except ImportError:
        for table_name, columns in tables.items():
            cursor = db.execute(f'SELECT COUNT(*) FROM "{table_name}"')
            row_count = cursor.fetchone()[0]
            cursor = db.execute(f'PRAGMA table_info("{table_name}")')
            col_info = cursor.fetchall()

            print(f"\nTable: {table_name} ({row_count} rows)")
            print("-" * 40)
            for col in col_info:
                print(f"  {col[1]:<20} {col[2]}")


def build_parser() -> argparse.ArgumentParser:
    """Build the CLI argument parser."""
    parser = argparse.ArgumentParser(
        prog="csvql",
        description="Run SQL queries against CSV/TSV files from the command line.",
        epilog="Examples:\n"
        "  csvql employees.csv -q \"SELECT * FROM employees WHERE salary > 50000\"\n"
        "  csvql employees.csv departments.csv -q \"SELECT e.name, d.dept_name FROM employees e JOIN departments d ON e.dept_id = d.id\"\n"
        "  csvql sales.csv -q \"SELECT product, SUM(amount) FROM sales GROUP BY product\" -f json\n",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "files",
        nargs="+",
        help="CSV/TSV files to load (table name = filename stem)",
    )
    parser.add_argument(
        "-q", "--query",
        help="SQL query to execute (required unless --schema)",
    )
    parser.add_argument(
        "-f", "--format",
        choices=["table", "csv", "tsv", "json"],
        default="table",
        help="Output format (default: table)",
    )
    parser.add_argument(
        "-o", "--output",
        help="Write output to file instead of stdout",
    )
    parser.add_argument(
        "--schema",
        action="store_true",
        help="Show loaded table schemas and exit",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Limit output rows (default: unlimited)",
    )
    parser.add_argument(
        "--no-header",
        action="store_true",
        help="CSV files have no header row (use col1, col2, ...)",
    )
    parser.add_argument(
        "--delimiter",
        default=None,
        help="Force delimiter instead of auto-detect",
    )

    return parser


def main():
    """Main entry point."""
    parser = build_parser()
    args = parser.parse_args()

    if not args.schema and not args.query:
        parser.error("Either --query or --schema is required.")

    db = sqlite3.connect(":memory:")
    db.execute("PRAGMA busy_timeout = 30000")

    try:
        tables = load_files(db, args.files, args.no_header, args.delimiter)

        if not tables:
            print("Error: No files were loaded successfully.", file=sys.stderr)
            sys.exit(1)

        if args.schema:
            show_schema(db, tables)
            sys.exit(0)

        columns, rows = execute_query(db, args.query, args.limit)

        if not columns:
            print("Query returned no results.", file=sys.stderr)
            sys.exit(0)

        format_output(columns, rows, args.format, args.output)

    except FileLoadError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except QueryError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nInterrupted.", file=sys.stderr)
        sys.exit(130)
    finally:
        db.close()


if __name__ == "__main__":
    main()
