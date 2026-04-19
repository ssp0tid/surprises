import ipaddress
import socket
from typing import Optional


def parse_subnet(subnet: str) -> list[str]:
    network = ipaddress.ip_network(subnet, strict=False)
    return [str(ip) for ip in network.hosts()]


def get_local_subnet() -> Optional[str]:
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()

        parts = local_ip.split(".")
        return f"{parts[0]}.{parts[1]}.{parts[2]}.0/24"
    except Exception:
        return None


def validate_subnet(subnet: str) -> bool:
    try:
        network = ipaddress.ip_network(subnet, strict=False)
        return network.num_addresses > 0
    except ValueError:
        return False


def format_mac(mac: str) -> str:
    mac = mac.replace("-", ":").upper()
    if len(mac) == 12:
        return ":".join([mac[i : i + 2] for i in range(0, 12, 2)])
    return mac
