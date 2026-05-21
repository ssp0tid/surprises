"""Account data model."""

import hashlib
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Optional


@dataclass
class Account:
    issuer: str
    account_name: str
    secret: str
    otp_type: str = "totp"
    algorithm: str = "SHA1"
    digits: int = 6
    period: int = 30
    counter: int = 0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def __post_init__(self):
        now = datetime.now(timezone.utc)
        if self.created_at is None:
            self.created_at = now
        if self.updated_at is None:
            self.updated_at = now
        self.otp_type = self.otp_type.lower()
        self.algorithm = self.algorithm.upper()
        if self.otp_type not in ("totp", "hotp"):
            raise ValueError(f"otp_type must be 'totp' or 'hotp', got {self.otp_type}")
        if self.digits not in (6, 8):
            raise ValueError(f"digits must be 6 or 8, got {self.digits}")
        if self.period < 1:
            raise ValueError(f"period must be positive, got {self.period}")

    @property
    def id(self) -> str:
        key = f"{self.issuer}:{self.account_name}"
        return hashlib.sha256(key.encode()).hexdigest()[:16]

    def to_dict(self) -> dict:
        data = asdict(self)
        data["id"] = self.id
        data["created_at"] = self.created_at.isoformat()
        data["updated_at"] = self.updated_at.isoformat()
        return data

    @classmethod
    def from_dict(cls, data: dict) -> "Account":
        data = data.copy()
        data.pop("id", None)
        for field_name in ("created_at", "updated_at"):
            if isinstance(data.get(field_name), str):
                data[field_name] = datetime.fromisoformat(data[field_name])
        return cls(**data)

    def update_counter(self, new_counter: int):
        self.counter = new_counter
        self.updated_at = datetime.now(timezone.utc)
