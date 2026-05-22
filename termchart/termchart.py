#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import sys

from data.parser import parse_input
from charts import CHART_TYPES
from charts.sparkline import sparkline
from render.colors import SCHEMES


def get_terminal_width() -> int:
    try:
        return os.get_terminal_size().columns
    except OSError:
        return 80


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="termchart",
        description="Render charts in the terminal from CSV/JSON/stdin data.",
    )
    parser.add_argument(
        "chart_type",
        choices=["bar", "hbar", "line", "scatter", "spark"],
        help="Chart type to render",
    )
    parser.add_argument("-f", "--file", dest="file", help="Input file (CSV or JSON)")
    parser.add_argument("-x", dest="x_col", help="X-axis column name")
    parser.add_argument("-y", dest="y_col", action="append", help="Y-axis column name (repeatable for multi-series)")
    parser.add_argument("-W", "--width", type=int, default=None, help="Chart width in columns (default: terminal width)")
    parser.add_argument("-H", "--height", type=int, default=20, help="Chart height in rows (default: 20)")
    parser.add_argument("-c", "--color", dest="color_scheme", default="rainbow",
                        choices=list(SCHEMES.keys()), help="Color scheme")
    parser.add_argument("-t", "--title", help="Chart title")
    parser.add_argument("-s", "--sort", action="store_true", help="Sort data by value (descending)")
    parser.add_argument("--no-color", action="store_true", help="Disable colors")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    width = args.width or get_terminal_width()
    color_enabled = not args.no_color

    try:
        data = parse_input(args.file)
    except (FileNotFoundError, ValueError) as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    if args.x_col:
        for row in data:
            if args.x_col in row:
                row["label"] = str(row[args.x_col])

    output = ""

    if args.title:
        output += f"{args.title}\n\n"

    try:
        if args.chart_type == "spark":
            values = [float(d.get("value", 0)) for d in data]
            output += sparkline(values, color_enabled=color_enabled,
                                color_scheme=args.color_scheme)

        elif args.chart_type == "hbar":
            chart = CHART_TYPES["hbar"]()
            output += chart.render(data, width=width, color_scheme=args.color_scheme,
                                   sort=args.sort, color_enabled=color_enabled)

        elif args.chart_type == "bar":
            chart = CHART_TYPES["bar"]()
            output += chart.render(data, height=args.height, color_scheme=args.color_scheme,
                                   sort=args.sort, color_enabled=color_enabled)

        elif args.chart_type == "line":
            y_columns = args.y_col or ["value"]
            chart = CHART_TYPES["line"]()
            output += chart.render(data, width=width, height=args.height,
                                   y_columns=y_columns, color_scheme=args.color_scheme,
                                   color_enabled=color_enabled)

        elif args.chart_type == "scatter":
            x_key = args.x_col or "label"
            y_key = (args.y_col[0] if args.y_col else "value")
            x_vals = [float(d.get(x_key, 0)) for d in data]
            y_vals = [float(d.get(y_key, 0)) for d in data]
            chart = CHART_TYPES["scatter"]()
            output += chart.render(x_vals, y_vals, width=width, height=args.height,
                                   color_scheme=args.color_scheme, color_enabled=color_enabled)

    except (ValueError, KeyError, TypeError) as e:
        print(f"Error rendering chart: {e}", file=sys.stderr)
        return 1

    print(output)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        sys.exit(130)
    except BrokenPipeError:
        os.close(sys.stdout.fileno())
        sys.exit(1)
