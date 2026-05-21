"""PortPilot - A CLI tool for port management.

Main CLI entry point.
"""

import click
import sys
import json
from typing import Optional

from scanner import get_open_ports, detect_port_conflicts, check_port_available, find_available_port, PortInfo
from proxy import get_manager


@click.group()
@click.version_option(version='1.0.0')
def cli():
    """PortPilot - Port management CLI tool.
    
    List ports, detect conflicts, and manage port forwarding.
    """
    pass


@cli.command()
@click.option('-j', '--json', 'use_json', is_flag=True, help='Output as JSON')
@click.option('-p', '--protocol', type=click.Choice(['tcp', 'udp', 'all']), default='all', help='Filter by protocol')
@click.option('-s', '--state', type=click.Choice(['listening', 'established', 'all']), default='all', help='Filter by state')
def list_ports(use_json: bool, protocol: str, state: str):
    """List all open ports with process information."""
    click.echo("Scanning for open ports...")
    ports = get_open_ports()
    
    # Filter by protocol
    if protocol != 'all':
        ports = [p for p in ports if p.protocol.lower() == protocol]
    
    # Filter by state
    if state != 'all':
        if state == 'listening':
            ports = [p for p in ports if p.state in ('LISTEN', 'NEW_SYN_RECV')]
        elif state == 'established':
            ports = [p for p in ports if p.state == 'ESTABLISHED']
    
    if use_json:
        data = [{
            'protocol': p.protocol,
            'local_address': p.local_address,
            'local_port': p.local_port,
            'state': p.state,
            'process_name': p.process_name,
            'process_id': p.process_id
        } for p in ports]
        click.echo(json.dumps(data, indent=2))
    else:
        if not ports:
            click.echo("No open ports found.")
            return
        
        # Print header
        click.echo(f"\n{'Protocol':<8} {'Local Address':<20} {'Port':<6} {'State':<12} {'PID':<6} {'Process':<20}")
        click.echo("-" * 80)
        
        for port in ports:
            pid = str(port.process_id) if port.process_id else '-'
            proc = port.process_name if port.process_name else '-'
            click.echo(
                f"{port.protocol:<8} {port.local_address:<20} {port.local_port:<6} "
                f"{port.state:<12} {pid:<6} {proc:<20}"
            )
        
        click.echo(f"\nTotal: {len(ports)} port(s)")


@cli.command()
@click.argument('port', type=int, required=False)
@click.option('-j', '--json', 'use_json', is_flag=True, help='Output as JSON')
def conflicts(port: Optional[int], use_json: bool):
    """Detect port conflicts (same port used by multiple processes)."""
    ports = get_open_ports()
    conflicts = detect_port_conflicts(ports)
    
    if port is not None:
        # Filter for a specific port
        port_conflicts = [
            (p1, p2) for p1, p2 in conflicts 
            if p1.local_port == port
        ]
        conflicts = port_conflicts
    
    if use_json:
        data = [{
            'port': p1.local_port,
            'conflicting_processes': [
                {'name': p1.process_name, 'pid': p1.process_id},
                {'name': p2.process_name, 'pid': p2.process_id}
            ]
        } for p1, p2 in conflicts]
        click.echo(json.dumps(data, indent=2))
    else:
        if not conflicts:
            if port:
                click.echo(f"No conflicts found on port {port}.")
            else:
                click.echo("No port conflicts detected.")
            return
        
        click.echo("\nPort Conflicts Detected:")
        click.echo("-" * 80)
        
        for p1, p2 in conflicts:
            click.echo(f"\nPort {p1.local_port}:")
            click.echo(f"  Process 1: {p1.process_name or 'Unknown'} (PID: {p1.process_id})")
            click.echo(f"  Process 2: {p2.process_name or 'Unknown'} (PID: {p2.process_id})")


@cli.command()
@click.argument('port', type=int)
def check(port: int):
    """Check if a port is available."""
    if check_port_available(port):
        click.echo(f"✓ Port {port} is available")
    else:
        click.echo(f"✗ Port {port} is in use")


@cli.command()
@click.option('--start', default=8000, help='Start of port range')
@click.option('--end', default=9000, help='End of port range')
def available(start: int, end: int):
    """Find an available port in the given range."""
    port = find_available_port(start, end)
    if port:
        click.echo(f"Available port: {port}")
    else:
        click.echo(f"No available ports in range {start}-{end}")


@cli.group()
def forward():
    """Port forwarding commands."""
    pass


@forward.command('add')
@click.argument('source_port', type=int)
@click.argument('dest_host')
@click.argument('dest_port', type=int)
def forward_add(source_port: int, dest_host: str, dest_port: int):
    """Start port forwarding.
    
    Example: portpilot forward add 8080 localhost 3000
    """
    manager = get_manager()
    if manager.start_forwarder(source_port, dest_host, dest_port):
        click.echo(f"[*] Forwarding port {source_port} -> {dest_host}:{dest_port}")
    else:
        click.echo(f"[-] Failed to start forwarder", err=True)
        sys.exit(1)


@forward.command('remove')
@click.argument('source_port', type=int)
def forward_remove(source_port: int):
    """Stop port forwarding."""
    manager = get_manager()
    if manager.stop_forwarder(source_port):
        click.echo(f"[*] Stopped forwarder on port {source_port}")
    else:
        click.echo(f"[-] No forwarder on port {source_port}", err=True)
        sys.exit(1)


@forward.command('list')
def forward_list():
    """List active port forwarders."""
    manager = get_manager()
    forwarders = manager.list_forwarders()
    
    if not forwarders:
        click.echo("No active port forwarders.")
        return
    
    click.echo("\nActive Port Forwarders:")
    click.echo("-" * 50)
    
    for f in forwarders:
        status = "running" if f['running'] else "stopped"
        click.echo(f"  {f['source_port']} -> {f['dest_host']}:{f['dest_port']} [{status}]")


@forward.command('stop')
def forward_stop():
    """Stop all port forwarders."""
    manager = get_manager()
    manager.stop_all()
    click.echo("[*] Stopped all port forwarders")


# Textual TUI imports (optional)
try:
    from textual.app import App, ComposeResult
    from textual.widgets import Header, Footer, DataTable, Static
    from textual.containers import Container
    HAS_TEXTUAL = True
except ImportError:
    HAS_TEXTUAL = False


if HAS_TEXTUAL:
    class PortTableTUI(App):
        """Textual TUI for viewing ports."""
        
        CSS = """
        Screen {
            background: $surface;
        }
        DataTable {
            height: 100%;
            margin: 1;
        }
        """
        
        def compose(self) -> ComposeResult:
            yield Header()
            yield Container(DataTable())
            yield Footer()
        
        def on_mount(self) -> None:
            table = self.query_one(DataTable)
            table.add_columns("Protocol", "Address", "Port", "State", "PID", "Process")
            
            ports = get_open_ports()
            for port in ports:
                table.add_row(
                    port.protocol,
                    port.local_address,
                    port.local_port,
                    port.state,
                    str(port.process_id) if port.process_id else "-",
                    port.process_name if port.process_name else "-"
                )
    
    @cli.command()
    def tui():
        """Launch Textual TUI (requires textual package)."""
        if not HAS_TEXTUAL:
            click.echo("[-] Textual not installed. Install with: pip install textual")
            sys.exit(1)
        
        app = PortTableTUI()
        app.run()


def main():
    """Main entry point."""
    cli()


if __name__ == '__main__':
    main()