"""Webhook trigger handler."""

import hmac
import hashlib
import json
from typing import Any, Callable

from ..config import config


class WebhookTrigger:
    def __init__(self, callback: Callable[[dict[str, Any]], None]):
        self.callback = callback
        self.secret = config.webhooks.secret

    def verify_signature(self, payload: str, signature: str) -> bool:
        if not self.secret:
            return True
        expected = hmac.new(
            self.secret.encode(),
            payload.encode(),
            hashlib.sha256,
        ).hexdigest()
        return hmac.compare_digest(f"sha256={expected}", signature)

    def trigger(self, payload: dict[str, Any], signature: str | None = None):
        payload_str = json.dumps(payload, sort_keys=True)
        if signature and not self.verify_signature(payload_str, signature):
            raise ValueError("Invalid webhook signature")
        self.callback(payload)
