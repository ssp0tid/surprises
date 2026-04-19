import asyncio
import socket
from typing import Optional

from netscout.utils.logging import get_logger


logger = get_logger(__name__)


async def resolve_hostname(ip: str, timeout: float = 2.0) -> Optional[str]:
    loop = asyncio.get_event_loop()
    try:
        result = await loop.run_in_executor(None, socket.gethostbyaddr, str(ip))
        hostname = result[0]
        if hostname.endswith(".local"):
            return hostname[:-6]
        return hostname
    except (socket.herror, socket.gaierror, OSError):
        return None


async def resolve_mdns(ip: str, timeout: float = 3.0) -> Optional[str]:
    return None
