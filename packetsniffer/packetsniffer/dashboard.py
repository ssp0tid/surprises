"""Rich live dashboard module."""

from __future__ import annotations

from threading import Event
from typing import Any, Callable

from rich.console import Console
from rich.live import Live
from rich.table import Table
from rich import box

console = Console()


def build_stats_table(stats: dict[str, Any]) -> Table:
    """Build protocol breakdown table."""
    table = Table(
        title="Protocol Breakdown",
        box=box.ROUNDED,
        show_header=True,
        header_style="bold cyan",
    )

    table.add_column("Protocol", justify="center", style="cyan")
    table.add_column("Packets", justify="right", style="green")
    table.add_column("Percentage", justify="right", style="yellow")

    total = stats.get("total", 0)
    for proto in ("tcp", "udp", "icmp", "arp", "dns", "other"):
        count = stats.get(proto, 0)
        pct = (count / total * 100) if total > 0 else 0
        table.add_row(proto.upper(), str(count), f"{pct:.1f}%")

    return table


def build_summary_table(stats: dict[str, Any]) -> Table:
    """Build summary stats table."""
    table = Table(
        title="Summary",
        box=box.ROUNDED,
        show_header=False,
    )

    total_bytes = stats.get("total_bytes", 0)
    mb = total_bytes / (1024 * 1024)
    table.add_row("Total Packets", str(stats.get("total", 0)))
    table.add_row("Total Data", f"{mb:.2f} MB")

    return table


def live_display(
    stats_func: Callable[[], dict[str, Any]],
    stop_event: Event,
    refresh_rate: float = 0.25,
) -> None:
    """Render live stats dashboard with protocol breakdown and summary."""
    with Live(
        screen=True,
        refresh_per_second=1 / refresh_rate,
        console=console,
    ) as live:
        while not stop_event.is_set():
            stats = stats_func()

            main_table = Table(box=box.ROUNDED, padding=(0, 1))
            main_table.add_column(ratio=2)
            main_table.add_column(ratio=1)

            main_table.add_row(
                build_stats_table(stats),
                build_summary_table(stats),
            )

            live.update(main_table)
            stop_event.wait(refresh_rate)
