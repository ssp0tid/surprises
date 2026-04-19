import csv
from pathlib import Path

from netscout.discovery.device import Device


def export_csv(devices: list[Device], output_path: Path) -> None:
    with open(output_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(
            [
                "IP Address",
                "Hostname",
                "MAC Address",
                "Vendor",
                "Open Ports",
                "Services",
                "Discovered At",
            ]
        )

        for device in devices:
            writer.writerow(
                [
                    str(device.ip),
                    device.hostname or "",
                    device.mac or "",
                    device.mac_vendor or "",
                    ",".join(map(str, device.ports)),
                    ",".join(f"{p}:{s}" for p, s in device.services.items()),
                    device.discovered_at.isoformat(),
                ]
            )
