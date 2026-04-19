"""Reusable UI widgets for Crono."""

from datetime import datetime
from typing import Optional

from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Static, Button, Input, TextArea, Label, DataTable


COLORS = {
    "bg_primary": "#0d1117",
    "bg_secondary": "#161b22",
    "bg_tertiary": "#21262d",
    "surface": "#30363d",
    "border": "#484f58",
    "border_focus": "#58a6ff",
    "text_primary": "#f0f6fc",
    "text_secondary": "#8b949e",
    "text_muted": "#6e7681",
    "accent": "#39d4e8",
    "accent_secondary": "#3fb9a5",
    "success": "#3fb950",
    "warning": "#d29922",
    "error": "#f85149",
    "cron": "#a371f7",
}


class CronoSection(Vertical):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.styles.background = COLORS["bg_primary"]
        self.styles.border = ("solid", COLORS["border"])
        self.styles.padding = (1, 2)


class CronoCard(Container):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.styles.background = COLORS["surface"]
        self.styles.border = ("solid", COLORS["border"])
        self.styles.padding = 1
        self.styles.border_radius = 6


class CronoLabel(Static):
    def __init__(self, text: str = "", *args, **kwargs):
        super().__init__(text, *args, **kwargs)
        self.styles.color = COLORS["text_secondary"]


class CronoInput(Input):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.styles.background = COLORS["bg_tertiary"]
        self.styles.color = COLORS["text_primary"]
        self.styles.border = ("solid", COLORS["border"])
        self.styles.padding = (0, 1)


class CronoTextArea(TextArea):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.styles.background = COLORS["bg_tertiary"]
        self.styles.color = COLORS["text_primary"]
        self.styles.border = ("solid", COLORS["border"])


class CronoButton(Button):
    def __init__(self, label: str = "", *args, **kwargs):
        super().__init__(label, *args, **kwargs)
        self.styles.background = COLORS["accent"]
        self.styles.color = COLORS["bg_primary"]
        self.styles.border_radius = 4


class CronoDataTable(DataTable):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.styles.background = COLORS["bg_secondary"]
        self.styles.color = COLORS["text_primary"]


class JobListItem(Container):
    def __init__(self, job, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.job = job
        self.styles.background = COLORS["bg_secondary"]
        self.styles.border = ("solid", COLORS["border"])
        self.styles.padding = 1
        self.styles.height = "3"

    def compose(self) -> ComposeResult:
        status_color = COLORS["success"] if self.job.enabled else COLORS["warning"]
        status_icon = "●" if self.job.enabled else "◐"
        yield Container(
            Static(f"[{status_color}]{status_icon}[/] [bold]{self.job.name}[/]"),
            Static(f"[{COLORS['cron']}]{self.job.cron_expression}[/]", classes="cron"),
            classes="job-item-content",
        )


class StatusIndicator(Static):
    def __init__(self, status: str = "success", *args, **kwargs):
        super().__init__(*args, **kwargs)
        color = {
            "success": COLORS["success"],
            "failed": COLORS["error"],
            "timeout": COLORS["warning"],
            "running": COLORS["accent"],
        }.get(status, COLORS["text_muted"])
        self.status = status
        self.update(f"[{color}]{status.upper()}[/]")


def humanize_time(dt) -> str:
    if dt is None:
        return "Never"

    now = datetime.now()
    diff = dt - now
    if diff.total_seconds() < 0:
        return "Past"
    days = diff.days
    hours = diff.seconds // 3600
    minutes = (diff.seconds % 3600) // 60
    if days > 0:
        return f"in {days}d {hours}h"
    elif hours > 0:
        return f"in {hours}h {minutes}m"
    elif minutes > 0:
        return f"in {minutes}m"
    else:
        return "Soon"
