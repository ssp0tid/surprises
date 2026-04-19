from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn

from netscout.utils.logging import get_logger


logger = get_logger(__name__)


class ScanProgress:
    def __init__(self, total: int):
        self.total = total
        self.current = 0
        self.progress = Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        )
        self.task_id = None

    def __enter__(self):
        self.progress.__enter__()
        self.task_id = self.progress.add_task("Scanning...", total=self.total)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.progress.__exit__(exc_type, exc_val, exc_tb)

    def update(self, advance: int = 1, description: str = None):
        if self.task_id is not None:
            self.progress.update(self.task_id, advance=advance, description=description)
        self.current += advance
