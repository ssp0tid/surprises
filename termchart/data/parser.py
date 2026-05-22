from __future__ import annotations

import csv
import json
import sys
from io import StringIO
from pathlib import Path


def parse_input(source: str | None = None, format: str | None = None) -> list[dict]:
    """Parse data from a file path or stdin.

    Supports CSV, JSON, and plain numbers (one per line).
    Returns list of dicts with at minimum 'label' and 'value' keys.
    """
    if source is None:
        raw = sys.stdin.read()
        if not raw.strip():
            raise ValueError("No data received from stdin")
        return _parse_raw(raw, format)

    path = Path(source)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {source}")

    detected_format = format or _detect_format(path)
    raw = path.read_text(encoding="utf-8")
    return _parse_raw(raw, detected_format)


def _detect_format(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix == ".csv":
        return "csv"
    if suffix == ".json":
        return "json"
    return "auto"


def _parse_raw(raw: str, format: str | None) -> list[dict]:
    if format == "csv":
        return _parse_csv(raw)
    if format == "json":
        return _parse_json(raw)

    raw_stripped = raw.strip()
    if raw_stripped.startswith(("{", "[")):
        try:
            return _parse_json(raw)
        except (json.JSONDecodeError, ValueError):
            pass

    if "," in raw_stripped or "\t" in raw_stripped:
        try:
            return _parse_csv(raw)
        except (csv.Error, ValueError):
            pass

    return _parse_plain(raw)


def _parse_csv(raw: str) -> list[dict]:
    reader = csv.DictReader(StringIO(raw))
    rows: list[dict] = []
    for row in reader:
        rows.append(row)

    if not rows:
        raise ValueError("CSV contains no data rows")

    return _normalize_rows(rows)


def _parse_json(raw: str) -> list[dict]:
    data = json.loads(raw)

    if isinstance(data, dict) and "labels" in data and "values" in data:
        labels = data["labels"]
        values = data["values"]
        return [{"label": str(lbl), "value": float(v)} for lbl, v in zip(labels, values)]

    if isinstance(data, list):
        if all(isinstance(item, dict) for item in data):
            return _normalize_rows(data)
        if all(isinstance(item, (int, float)) for item in data):
            return [{"label": str(i), "value": float(v)} for i, v in enumerate(data)]

    raise ValueError("Unsupported JSON structure")


def _parse_plain(raw: str) -> list[dict]:
    values: list[dict] = []
    for i, line in enumerate(raw.strip().split()):
        try:
            values.append({"label": str(i), "value": float(line)})
        except ValueError:
            continue
    if not values:
        raise ValueError("No numeric values found in input")
    return values


def _normalize_rows(rows: list[dict]) -> list[dict]:
    if not rows:
        return []

    keys = list(rows[0].keys())
    numeric_cols = _find_numeric_columns(rows, keys)

    if not numeric_cols:
        raise ValueError("No numeric columns found in data")

    label_col = None
    for k in keys:
        if k not in numeric_cols:
            label_col = k
            break

    result: list[dict] = []
    for i, row in enumerate(rows):
        entry: dict = {}
        entry["label"] = str(row.get(label_col, i)) if label_col else str(i)
        for col in numeric_cols:
            entry[col] = float(row[col])
        if len(numeric_cols) == 1:
            entry["value"] = float(row[numeric_cols[0]])
        result.append(entry)

    return result


def _find_numeric_columns(rows: list[dict], keys: list[str]) -> list[str]:
    numeric: list[str] = []
    for key in keys:
        is_numeric = True
        for row in rows:
            try:
                float(row[key])
            except (ValueError, TypeError):
                is_numeric = False
                break
        if is_numeric:
            numeric.append(key)
    return numeric
