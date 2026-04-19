import asyncio
from typing import Optional

from netscout.discovery.device import Device
from netscout.scanner.arp_scanner import arp_scan, tcp_discovery_scan
from netscout.scanner.port_scanner import scan_ports
from netscout.scanner.hostname_resolver import resolve_hostname
from netscout.discovery.oui_lookup import OUILookup
from netscout.utils.logging import get_logger


logger = get_logger(__name__)


class ScanScheduler:
    def __init__(
        self,
        concurrency: int = 100,
        timeout: float = 2.0,
        skip_hostname: bool = False,
        skip_oui: bool = False,
        use_tcp_fallback: bool = False,
    ):
        self.concurrency = concurrency
        self.timeout = timeout
        self.skip_hostname = skip_hostname
        self.skip_oui = skip_oui
        self.use_tcp_fallback = use_tcp_fallback
        self.oui_lookup: Optional[OUILookup] = None

        if not skip_oui:
            self.oui_lookup = OUILookup()
            try:
                self.oui_lookup.load()
            except Exception as e:
                logger.warning(f"Failed to load OUI database: {e}")
                self.oui_lookup = None

    async def run_arp_scan(self, subnet: str) -> list[dict]:
        try:
            return await arp_scan(subnet, timeout=int(self.timeout))
        except Exception as e:
            logger.warning(f"ARP scan failed, using TCP fallback: {e}")
            if self.use_tcp_fallback:
                return await tcp_discovery_scan(subnet, timeout=self.timeout)
            return []

    async def run_port_scan(
        self, ip: str, ports: list[int]
    ) -> tuple[list[int], dict[int, str]]:
        open_ports = await scan_ports(
            ip, ports, concurrency=self.concurrency, timeout=self.timeout
        )
        return list(open_ports.keys()), open_ports

    async def run_hostname_resolve(self, ip: str) -> Optional[str]:
        if self.skip_hostname:
            return None
        return await resolve_hostname(ip, timeout=self.timeout)

    def lookup_vendor(self, mac: str) -> Optional[str]:
        if self.skip_oui or self.oui_lookup is None:
            return None
        return self.oui_lookup.lookup(mac)

    async def scan_all(self, subnet: str, ports: list[int]) -> list[Device]:
        devices = []

        arp_results = await self.run_arp_scan(subnet)
        logger.info(f"Found {len(arp_results)} devices via discovery")

        for result in arp_results:
            ip = result["ip"]
            mac = result.get("mac")

            device = Device(ip=ip, mac=mac)

            open_ports, services = await self.run_port_scan(ip, ports)
            device.ports = open_ports
            device.services = services

            device.hostname = await self.run_hostname_resolve(ip)

            if mac:
                device.mac_vendor = self.lookup_vendor(mac)

            devices.append(device)
            logger.debug(f"Scanned {ip}")

        return devices
