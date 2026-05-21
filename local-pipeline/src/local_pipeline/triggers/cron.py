"""Cron trigger handler."""

from datetime import datetime
from typing import Any, Callable

from croniter import croniter

from ..parser.models import TriggerConfig


class CronTrigger:
    def __init__(self, config: TriggerConfig, callback: Callable[[], None]):
        if not config.cron:
            raise ValueError("Cron expression required for cron trigger")
        self.cron_expr = config.cron
        self.callback = callback
        self.cron = croniter(self.cron_expr, datetime.now())

    def get_next_run(self) -> datetime:
        return self.cron.get_next()

    def should_run(self) -> bool:
        now = datetime.now()
        next_run = self.cron.get_next()
        threshold = 1
        return abs((now - next_run).total_seconds()) < threshold

    def trigger(self):
        self.callback()
        self.cron = croniter(self.cron_expr, datetime.now())
