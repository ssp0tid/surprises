"""Main Textual application for Crono."""

from textual.app import App, ComposeResult
from textual.screen import Screen
from textual.widgets import Header, Footer, Static
from textual.binding import Binding

from crono.screens import JobListScreen


class CronoApp(App):
    TITLE = "Crono"
    SUB_TITLE = "Visual Cron Job Scheduler"
    CSS_PATH = None

    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("f1", "help", "Help"),
    ]

    def __init__(self):
        super().__init__()
        self.dark = True

    def get_default_css(self) -> str:
        return """
        Screen {
            background: #0d1117;
        }
        #crono-header {
            background: #161b22;
            color: #39d4e8;
        }
        #crono-footer {
            background: #161b22;
            color: #8b949e;
        }
        .sidebar {
            background: #161b22;
            border-right: solid #484f58;
        }
        .sidebar-title {
            color: #f0f6fc;
            text-align: center;
            padding: 1;
        }
        .job-item {
            background: #21262d;
            border: solid #484f58;
            padding: 1;
            margin: 0 0 1 0;
        }
        .job-item:hover {
            background: #30363d;
        }
        .job-item-selected {
            border: solid #58a6ff;
        }
        .detail-panel {
            background: #0d1117;
        }
        .detail-header {
            color: #f0f6fc;
            padding: 1 2;
            background: #161b22;
        }
        .detail-content {
            color: #8b949e;
            padding: 2;
        }
        .cron-expression {
            color: #a371f7;
        }
        .status-active {
            color: #3fb950;
        }
        .status-paused {
            color: #d29922;
        }
        .btn-add {
            background: #39d4e8;
            color: #0d1117;
        }
        Static {
            color: #f0f6fc;
        }
        Input {
            background: #21262d;
            color: #f0f6fc;
            border: solid #484f58;
        }
        TextArea {
            background: #21262d;
            color: #f0f6fc;
            border: solid #484f58;
        }
        Button {
            background: #30363d;
            color: #f0f6fc;
        }
        Button:hover {
            background: #484f58;
        }
        Button#btn-primary {
            background: #39d4e8;
            color: #0d1117;
        }
        Button#btn-primary:hover {
            background: #3fb9a5;
        }
        .form-label {
            color: #8b949e;
        }
        .form-error {
            color: #f85149;
        }
        DataTable {
            background: #161b22;
        }
        DataTable > .datatable--cursor {
            background: #30363d;
        }
        """

    def compose(self) -> ComposeResult:
        yield Header(id="crono-header")
        yield JobListScreen()
        yield Footer(id="crono-footer")

    def action_help(self) -> None:
        self.notify(
            "Keys: n=new e=edit d=delete space=toggle r=run l=history q=quit",
            title="Help",
        )

    def action_quit(self) -> None:
        self.exit()
