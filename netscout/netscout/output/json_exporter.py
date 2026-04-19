import json
from datetime import datetime
from pathlib import Path

from netscout.discovery.device import Device


def export_json(devices: list[Device], output_path: Path) -> None:
    data = {
        "scan_time": datetime.now().isoformat(),
        "total_devices": len(devices),
        "devices": [
            {
                "ip": str(d.ip),
                "mac": d.mac,
                "hostname": d.hostname,
                "mac_vendor": d.mac_vendor,
                "ports": d.ports,
                "services": d.services,
                "discovered_at": d.discovered_at.isoformat(),
            }
            for d in devices
        ],
    }

    with open(output_path, "w") as f:
        json.dump(data, f, indent=2)
