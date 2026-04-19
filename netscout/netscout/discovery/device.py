from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field
from pydantic.networks import IPv4Address


class Device(BaseModel):
    ip: IPv4Address
    mac: Optional[str] = None
    hostname: Optional[str] = None
    mac_vendor: Optional[str] = None
    ports: list[int] = Field(default_factory=list)
    services: dict[int, str] = Field(default_factory=dict)
    discovered_at: datetime = Field(default_factory=datetime.now)
    is_alive: bool = True

    class Config:
        arbitrary_types_allowed = True
