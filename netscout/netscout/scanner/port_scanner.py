import asyncio
from typing import Optional

from netscout.discovery.ports import COMMON_PORTS, get_service_name


async def scan_port(ip: str, port: int, timeout: float = 1.0) -> tuple[int, bool, str]:
    try:
        reader, writer = await asyncio.wait_for(
            asyncio.open_connection(ip, port),
            timeout=timeout,
        )
        writer.close()
        await writer.wait_closed()
        service = get_service_name(port)
        return (port, True, service)
    except (asyncio.TimeoutError, ConnectionRefusedError, OSError):
        return (port, False, "")


async def scan_ports(
    ip: str,
    ports: list[int],
    concurrency: int = 100,
    timeout: float = 1.0,
) -> dict[int, str]:
    semaphore = asyncio.Semaphore(concurrency)

    async def scan_with_semaphore(port: int) -> tuple[int, bool, str]:
        async with semaphore:
            return await scan_port(ip, port, timeout)

    tasks = [scan_with_semaphore(port) for port in ports]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    open_ports: dict[int, str] = {}
    for result in results:
        if isinstance(result, tuple) and result[1]:
            open_ports[result[0]] = result[2]

    return open_ports
