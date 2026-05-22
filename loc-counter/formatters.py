"""Output formatters for loc-counter results."""

import csv
import io
import json

from counter import FileStats, LangSummary


def format_table(summaries: list[LangSummary], total: LangSummary) -> str:
    """Format results as an aligned ASCII table with separator lines and totals row."""
    headers = ["Language", "Files", "Code", "Comments", "Blanks", "Total"]
    col_widths = [len(h) for h in headers]

    rows: list[list[str]] = []
    for s in summaries:
        row = [s.language, str(s.files), str(s.code), str(s.comments), str(s.blanks), str(s.total)]
        rows.append(row)
        for i, val in enumerate(row):
            col_widths[i] = max(col_widths[i], len(val))

    total_row = ["Total", str(total.files), str(total.code), str(total.comments), str(total.blanks), str(total.total)]
    for i, val in enumerate(total_row):
        col_widths[i] = max(col_widths[i], len(val))

    def format_row(values: list[str]) -> str:
        parts = []
        for i, val in enumerate(values):
            if i == 0:
                parts.append(f" {val:<{col_widths[i]}} ")
            else:
                parts.append(f" {val:>{col_widths[i]}} ")
        return "".join(parts)

    sep_width = sum(col_widths) + len(col_widths) * 2 + len(col_widths) - 1
    separator = "\u2500" * sep_width

    lines = [separator, format_row(headers), separator]
    for row in rows:
        lines.append(format_row(row))
    lines.append(separator)
    lines.append(format_row(total_row))
    lines.append(separator)

    return "\n".join(lines)


def format_table_by_file(file_stats: list[FileStats]) -> str:
    """Format per-file results as an aligned ASCII table."""
    headers = ["File", "Language", "Code", "Comments", "Blanks", "Total"]
    col_widths = [len(h) for h in headers]

    rows: list[list[str]] = []
    for fs in file_stats:
        row = [fs.path, fs.language, str(fs.code), str(fs.comments), str(fs.blanks), str(fs.total)]
        rows.append(row)
        for i, val in enumerate(row):
            col_widths[i] = max(col_widths[i], len(val))

    def format_row(values: list[str]) -> str:
        parts = []
        for i, val in enumerate(values):
            if i <= 1:
                parts.append(f" {val:<{col_widths[i]}} ")
            else:
                parts.append(f" {val:>{col_widths[i]}} ")
        return "".join(parts)

    sep_width = sum(col_widths) + len(col_widths) * 2 + len(col_widths) - 1
    separator = "\u2500" * sep_width

    lines = [separator, format_row(headers), separator]
    for row in rows:
        lines.append(format_row(row))
    lines.append(separator)

    return "\n".join(lines)


def format_json(summaries: list[LangSummary], total: LangSummary) -> str:
    """Format results as JSON with languages array and total object."""
    data = {
        "languages": [
            {
                "language": s.language,
                "files": s.files,
                "code": s.code,
                "comments": s.comments,
                "blanks": s.blanks,
                "total": s.total,
            }
            for s in summaries
        ],
        "total": {
            "files": total.files,
            "code": total.code,
            "comments": total.comments,
            "blanks": total.blanks,
            "total": total.total,
        },
    }
    return json.dumps(data, indent=2)


def format_json_by_file(file_stats: list[FileStats]) -> str:
    """Format per-file results as JSON."""
    data = {
        "files": [
            {
                "path": fs.path,
                "language": fs.language,
                "code": fs.code,
                "comments": fs.comments,
                "blanks": fs.blanks,
                "total": fs.total,
            }
            for fs in file_stats
        ]
    }
    return json.dumps(data, indent=2)


def format_csv(summaries: list[LangSummary], total: LangSummary) -> str:
    """Format results as CSV with header row."""
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Language", "Files", "Code", "Comments", "Blanks", "Total"])
    for s in summaries:
        writer.writerow([s.language, s.files, s.code, s.comments, s.blanks, s.total])
    writer.writerow(["Total", total.files, total.code, total.comments, total.blanks, total.total])
    return output.getvalue().rstrip("\n")


def format_csv_by_file(file_stats: list[FileStats]) -> str:
    """Format per-file results as CSV."""
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["File", "Language", "Code", "Comments", "Blanks", "Total"])
    for fs in file_stats:
        writer.writerow([fs.path, fs.language, fs.code, fs.comments, fs.blanks, fs.total])
    return output.getvalue().rstrip("\n")
