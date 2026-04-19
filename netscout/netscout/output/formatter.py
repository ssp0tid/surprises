from rich.console import Console
from rich.table import Table

from netscout.discovery.device import Device


class OutputFormatter:
    def __init__(self, verbose: int = 0):
        self.console = Console()
        self.verbose = verbose

    def display_devices(self, devices: list[Device]) -> None:
        table = Table(title="Discovered Devices")

        table.add_column("IP Address", style="cyan")
        table.add_column("Hostname", style="green")
        table.add_column("MAC Address", style="yellow")
        table.add_column("Vendor", style="magenta")
        table.add_column("Open Ports", style="red")

        for device in devices:
            ports_str = ", ".join(map(str, device.ports)) or "None"
            table.add_row(
                str(device.ip),
                device.hostname or "N/A",
                device.mac or "N/A",
                device.mac_vendor or "N/A",
                ports_str,
            )

        self.console.print(table)

    def display_progress(self, current: int, total: int, message: str) -> None:
        if self.verbose > 0:
            self.console.print(f"[{current}/{total}] {message}")

    def display_summary(self, devices: list[Device]) -> None:
        self.console.print(
            f"\n[bold]Scan complete:[/bold] {len(devices)} devices found"
        )
        total_ports = sum(len(d.ports) for d in devices)
        self.console.print(f"Total open ports: {total_ports}")
