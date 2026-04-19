"""Status bar widget."""

from textual.widget import Widget


class StatusBar(Widget):
    """Status bar showing navigation hints and repo info."""

    def __init__(self):
        super().__init__(id="status-bar")
        self.repo_info: str = ""
        self.commit_count: int = 0
        self.branch_count: int = 0

    def set_repo_info(self, path: str, commits: int, branches: int) -> None:
        """Set repository information."""
        self.repo_info = path
        self.commit_count = commits
        self.branch_count = branches
        self.refresh()

    def render(self) -> str:
        """Render the status bar."""
        parts = []

        parts.append(f"Commits: {self.commit_count}")
        parts.append(f"Branches: {self.branch_count}")

        hints = [
            "j/k: nav",
            "g/G: top/bottom",
            "/: search",
            "d: diff",
            "q: quit",
        ]
        parts.extend(hints)

        return " │ ".join(parts)
