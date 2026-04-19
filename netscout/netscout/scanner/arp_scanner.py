import asyncio
from typing import Optional

from netscout.utils.errors import PermissionError, NetworkError
from netscout.utils.logging import get_logger


logger = get_logger(__name__)


async def arp_scan(subnet: str, timeout: int = 3) -> list[dict]:
    loop = asyncio.get_event_loop()
    try:
        return await loop.run_in_executor(None, _sync_arp_scan, subnet, timeout)
    except PermissionError:
        raise
    except Exception as e:
        raise NetworkError(f"ARP scan failed: {e}")


def _sync_arp_scan(subnet: str, timeout: int) -> list[dict]:
    try:
        from scapy.all import ARP, Ether, srp
    except ImportError:
        raise PermissionError("ARP scanning requires root privileges")

    arp_request = ARP(pdst=subnet)
    broadcast = Ether(dst="ff:ff:ff:ff:ff:ff")
    packet = broadcast / arp_request

    answered, _ = srp(packet, timeout=timeout, verbose=False)

    results = []
    for sent, received in answered:
        results.append(
            {
                "ip": received[ARP].psrc,
                "mac": received[ARP].hwsrc,
            }
        )
    return results


async def tcp_discovery_scan(
    subnet: str, timeout: float = 1.0, ports: Optional[list[int]] = None
) -> list[dict]:
    import ipaddress

    if ports is None:
        ports = [80, 443]

    network = ipaddress.ip_network(subnet, strict=False)
    hosts = [str(ip) for ip in network.hosts()]

    results = []
    for ip in hosts:
        for port in ports:
            try:
                reader, writer = await asyncio.wait_for(
                    asyncio.open_connection(ip, port),
                    timeout=timeout,
                )
                writer.close()
                await writer.wait_closed()
                results.append({"ip": ip, "mac": None})
                break
            except (asyncio.TimeoutError, ConnectionRefusedError, OSError):
                continue

    return results
