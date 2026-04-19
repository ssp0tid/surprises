#!/usr/bin/env python3
"""PingPlot - Network Latency Visualizer with ASCII sparkline graphs."""

import argparse
import csv
import re
import subprocess
import sys
import time
import statistics
from dataclasses import dataclass
from typing import Optional

try:
    from rich.console import Console
    from rich.table import Table

    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False


@dataclass
class PingResult:
    seq: int
    time: Optional[float]
    success: bool
    error: Optional[str] = None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="pingplot.py",
        description="Network latency visualizer with ASCII sparkline graphs",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s -H google.com -c 10
  %(prog)s --host 8.8.8.8 --count 5 --csv results.csv
        """,
    )
    parser.add_argument("-H", "--host", required=True, help="Host to ping")
    parser.add_argument(
        "-c", "--count", type=int, default=5, help="Number of pings", metavar="N"
    )
    parser.add_argument("--csv", metavar="FILE", help="Output to CSV file")
    return parser.parse_args()


def check_ping_command() -> bool:
    try:
        subprocess.run(
            ["ping", "-V"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )
        return True
    except FileNotFoundError:
        return False


def get_ping_cmd(host: str) -> list:
    return (
        ["ping", "-n", "1", host]
        if sys.platform == "win32"
        else ["ping", "-c", "1", host]
    )


def parse_ping_output(host: str, seq: int) -> PingResult:
    cmd = get_ping_cmd(host)
    try:
        result = subprocess.run(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=5
        )
        output = result.stdout.lower()
        stderr_output = result.stderr.lower()

        # Check for host-related errors (may be in stderr)
        error_output = output + stderr_output
        if any(
            msg in error_output
            for msg in [
                "unknown host",
                "could not find host",
                "name or service not known",
                "no route to host",
            ]
        ):
            return PingResult(seq=seq, time=None, success=False, error="Host not found")
        if (
            "request timed out" in error_output
            or "destination host unreachable" in error_output
        ):
            return PingResult(
                seq=seq, time=None, success=False, error="Request timed out"
            )

        for line in result.stdout.split("\n"):
            if "time=" in line:
                # Check for <1ms or similar sub-millisecond times
                sub_ms_match = re.search(
                    r"time[=<](\d+\.?\d*)\s*ms", line, re.IGNORECASE
                )
                if sub_ms_match:
                    return PingResult(
                        seq=seq, time=float(sub_ms_match.group(1)), success=True
                    )
                match = re.search(r"time=([\d.]+)\s*ms", line, re.IGNORECASE)
                if match:
                    return PingResult(seq=seq, time=float(match.group(1)), success=True)

        return PingResult(seq=seq, time=None, success=False, error="Parse error")

    except subprocess.TimeoutExpired:
        return PingResult(seq=seq, time=None, success=False, error="Request timed out")
    except FileNotFoundError:
        return PingResult(
            seq=seq, time=None, success=False, error="Ping command not found"
        )
    except Exception as e:
        return PingResult(seq=seq, time=None, success=False, error=str(e))


def generate_sparkline(latencies: list[Optional[float]], width: int = 40) -> str:
    valid = [l for l in latencies if l is not None]
    if not valid:
        return "█" * width

    min_val, max_val = min(valid), max(valid)
    val_range = max_val - min_val if max_val != min_val else 1
    chars = "▁▂▃▄▅▆▇█"

    sparkline = []
    for lat in latencies:
        if lat is None:
            sparkline.append("×")
        else:
            normalized = int((lat - min_val) / val_range * 7)
            normalized = max(0, min(7, normalized))
            sparkline.append(chars[normalized])
    return "".join(sparkline)


def get_color_for_latency(latency: Optional[float]) -> str:
    if latency is None:
        return "red"
    if latency < 50:
        return "green"
    if latency < 100:
        return "yellow"
    if latency < 200:
        return "magenta"
    return "red"


def print_results_console(results: list[PingResult], host: str):
    if RICH_AVAILABLE:
        print_results_rich(results, host)
    else:
        print_results_plain(results, host)


def print_results_rich(results: list[PingResult], host: str):
    console = Console()
    latencies = [r.time for r in results if r.success]
    packet_loss = (len([r for r in results if not r.success]) / len(results)) * 100

    console.print(f"\n[bold]PingPlot - {host}[/bold]")
    console.print(
        f" Packets: {len(results)} sent, {len(latencies)} received, {packet_loss:.1f}% loss\n"
    )
    console.print(
        f"[dim]Latency:[/dim] {generate_sparkline([r.time for r in results])}\n"
    )

    table = Table(show_header=True, header_style="bold")
    table.add_column("Seq", justify="right")
    table.add_column("Latency", justify="right")
    table.add_column("Status")

    for r in results:
        color = get_color_for_latency(r.time)
        if r.success:
            table.add_row(
                str(r.seq),
                f"[{color}]{r.time:.2f} ms[/{color}]" if r.time else "-",
                f"[{color}]OK[/{color}]",
            )
        else:
            table.add_row(str(r.seq), "-", f"[{color}]{r.error or 'Failed'}[/{color}]")

    console.print(table)

    if latencies:
        console.print(
            f"\n[dim]RTT min/avg/max = {min(latencies):.2f}/{statistics.mean(latencies):.2f}/{max(latencies):.2f} ms[/dim]"
        )


def print_results_plain(results: list[PingResult], host: str):
    print(f"\n{'=' * 50}\nPingPlot - {host}\n{'=' * 50}\n")
    latencies = [r.time for r in results if r.success]
    packet_loss = (len([r for r in results if not r.success]) / len(results)) * 100

    print(
        f"Packets: {len(results)} sent, {len(latencies)} received, {packet_loss:.1f}% loss\n"
    )
    print(f"Latency: {generate_sparkline([r.time for r in results])}\n")

    print(f"{'Seq':<6} {'Latency':<12} {'Status'}")
    print("-" * 35)
    for r in results:
        if r.success:
            print(f"{r.seq:<6} {f'{r.time:.2f} ms' if r.time else '-':<12} OK")
        else:
            print(f"{r.seq:<6} {'-':<12} {r.error or 'Failed'}")

    if latencies:
        print(
            f"\nRTT min/avg/max = {min(latencies):.2f}/{statistics.mean(latencies):.2f}/{max(latencies):.2f} ms"
        )


def write_csv(results: list[PingResult], filepath: str):
    with open(filepath, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["sequence", "latency_ms", "success", "error"])
        for r in results:
            writer.writerow(
                [
                    r.seq,
                    r.time if r.time is not None else "",
                    "yes" if r.success else "no",
                    r.error or "",
                ]
            )
    print(f"\nResults written to: {filepath}")


def main():
    args = parse_args()

    if args.count < 1:
        print("Error: count must be at least 1", file=sys.stderr)
        sys.exit(1)

    if not check_ping_command():
        print("Error: ping command not found. Please install ping.", file=sys.stderr)
        sys.exit(1)

    print(f"Pinging {args.host} with {args.count} packets...\n")
    results: list[PingResult] = []

    for i in range(1, args.count + 1):
        result = parse_ping_output(args.host, i)
        results.append(result)
        status = (
            f"{result.time:.2f} ms" if result.success else f"FAILED ({result.error})"
        )
        print(f"  {i}: {status}")
        if i < args.count:
            time.sleep(0.2)

    print_results_console(results, args.host)

    if args.csv:
        write_csv(results, args.csv)

    packet_loss = len([r for r in results if not r.success]) / len(results)
    sys.exit(0 if packet_loss == 0 else 1)


if __name__ == "__main__":
    main()
