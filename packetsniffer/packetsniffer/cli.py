"""Click CLI entry point."""

from __future__ import annotations

import threading
from pathlib import Path
from threading import Event

import click

from .capture import capture_packets, start_capture
from .dashboard import live_display
from .export import export_csv, export_json
from .filters import parse_filter
from .parser import dissect_packet
from .stats import PacketStats


@click.group()
@click.option("--iface", default=None, help="Network interface to capture on")
@click.option("--verbose", "-v", count=True, help="Increase verbosity")
@click.pass_context
def cli(ctx: click.Context, iface: str | None, verbose: int) -> None:
    """PacketSniffer - Network packet analyzer."""
    ctx.ensure_object(dict)
    ctx.obj["iface"] = iface
    ctx.obj["verbose"] = verbose


@cli.command()
@click.option("--count", type=int, default=10, help="Number of packets to capture")
@click.option("--filter", "-f", "bpf_filter", help="BPF filter (e.g., 'tcp port 80')")
@click.option("--output", "-o", "output_path", type=click.Path(), help="Export file")
@click.option(
    "--format",
    "export_format",
    type=click.Choice(["json", "csv"]),
    default="json",
    help="Export format",
)
@click.pass_context
def capture(
    ctx: click.Context,
    count: int,
    bpf_filter: str | None,
    output_path: str | None,
    export_format: str,
) -> None:
    """Capture network packets."""
    try:
        if bpf_filter:
            bpf_filter = parse_filter(bpf_filter)
    except ValueError as e:
        click.echo(f"Error: {e}", err=True)
        return

    packets = capture_packets(
        iface=ctx.obj.get("iface"),
        bpf_filter=bpf_filter,
        count=count,
    )

    parsed = [dissect_packet(pkt) for pkt in packets]

    if output_path:
        path = Path(output_path)
        if export_format == "json":
            export_json(parsed, path)
        else:
            export_csv(parsed, path)
        click.echo(f"Exported {len(packets)} packets to {output_path}")
    else:
        for pkt in parsed:
            click.echo(pkt)


@cli.command()
@click.option("--filter", "-f", "bpf_filter", help="BPF filter")
@click.option("--duration", type=int, help="Capture duration in seconds (not implemented)")
@click.pass_context
def live(ctx: click.Context, bpf_filter: str | None, duration: int | None) -> None:
    """Live capture with stats dashboard."""
    try:
        if bpf_filter:
            bpf_filter = parse_filter(bpf_filter)
    except ValueError as e:
        click.echo(f"Error: {e}", err=True)
        return

    stats = PacketStats()
    stop_event = Event()

    def packet_handler(pkt) -> None:
        parsed = dissect_packet(pkt)
        stats.record(parsed)

    capture_thread = threading.Thread(
        target=start_capture,
        args=(ctx.obj.get("iface"), bpf_filter, packet_handler, stop_event),
    )
    capture_thread.start()

    try:
        live_display(stats.get_snapshot, stop_event)
    except KeyboardInterrupt:
        stop_event.set()

    capture_thread.join(timeout=2)


@cli.command()
@click.option("--count", type=int, default=100, help="Number of packets to capture")
@click.option("--filter", "-f", "bpf_filter", help="BPF filter")
@click.pass_context
def stats(
    ctx: click.Context,
    count: int,
    bpf_filter: str | None,
) -> None:
    """Capture packets and display statistics."""
    try:
        if bpf_filter:
            bpf_filter = parse_filter(bpf_filter)
    except ValueError as e:
        click.echo(f"Error: {e}", err=True)
        return

    packets = capture_packets(
        iface=ctx.obj.get("iface"),
        bpf_filter=bpf_filter,
        count=count,
    )

    parsed = [dissect_packet(pkt) for pkt in packets]

    stat_tracker = PacketStats()
    for pkt in parsed:
        stat_tracker.record(pkt)

    snapshot = stat_tracker.get_snapshot()

    click.echo("Packet Statistics:")
    click.echo(f"  TCP:    {snapshot['tcp']}")
    click.echo(f"  UDP:    {snapshot['udp']}")
    click.echo(f"  ICMP:   {snapshot['icmp']}")
    click.echo(f"  ARP:    {snapshot['arp']}")
    click.echo(f"  DNS:    {snapshot['dns']}")
    click.echo(f"  Other:  {snapshot['other']}")
    click.echo(f"  Total:  {snapshot['total']}")
    click.echo(f"  Bytes:  {snapshot['total_bytes']}")


@cli.command()
def interfaces() -> None:
    """List available network interfaces."""
    from scapy.all import get_if_list

    ifs = get_if_list()
    if not ifs:
        click.echo("No interfaces found.")
        return

    click.echo("Available interfaces:")
    for iface in ifs:
        click.echo(f"  - {iface}")


if __name__ == "__main__":
    cli()
