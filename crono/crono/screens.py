"""UI screens for Crono application."""

from datetime import datetime

from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import (
    Static,
    Button,
    Input,
    TextArea,
    Label,
    DataTable,
    Header,
    Footer,
)
from textual.binding import Binding
from textual import work

from crono import cron_parser
from crono import job_manager
from crono.models import CronJob
from crono import widgets as w
from crono.widgets import JobListItem
from crono import history


COLORS = w.COLORS


class JobListScreen(Screen):
    CSS = """
    Screen {
        background: $bg_primary;
    }
    .sidebar {
        background: $bg_secondary;
        border-right: solid $border;
        width: 25%;
    }
    .main-content {
        background: $bg_primary;
    }
    .job-item {
        background: $bg_tertiary;
        border: solid $border;
        padding: 1;
        height: 3;
    }
    .job-item-selected {
        border: solid $border_focus;
    }
    .job-item:hover {
        background: $surface;
    }
    .detail-section {
        background: $bg_secondary;
        border: solid $border;
        padding: 2;
        margin: 1;
    }
    .detail-label {
        color: $text_secondary;
    }
    .detail-value {
        color: $text_primary;
    }
    .detail-cron {
        color: $cron;
    }
    .btn-primary {
        background: $accent;
        color: $bg_primary;
    }
    .btn-danger {
        background: $error;
        color: $text_primary;
    }
    Static { color: $text_primary; }
    Input {
        background: $bg_tertiary;
        color: $text_primary;
        border: solid $border;
    }
    TextArea {
        background: $bg_tertiary;
        color: $text_primary;
    }
    DataTable {
        background: $bg_secondary;
    }
    """

    BINDINGS = [
        Binding("n", "new_job", "New Job"),
        Binding("e", "edit_job", "Edit"),
        Binding("d", "delete_job", "Delete"),
        Binding("space", "toggle_job", "Toggle"),
        Binding("r", "run_job", "Run Now"),
        Binding("l", "view_history", "History"),
        Binding("q,escape", "quit", "Quit"),
    ]

    def __init__(self):
        super().__init__()
        self.jobs = []
        self.selected_index = 0

    def compose(self) -> ComposeResult:
        yield Horizontal(
            Vertical(
                Static("Jobs", classes="sidebar-title"),
                Vertical(id="job-list"),
                Button("+ Add Job", id="btn-add", variant="primary"),
                classes="sidebar",
            ),
            Vertical(
                Static(id="detail-header"),
                Static(id="detail-content"),
                id="detail-panel",
                classes="main-content",
            ),
        )

    def on_mount(self) -> None:
        self.load_jobs()

    def load_jobs(self) -> None:
        self.jobs = job_manager.JobManager.get_all_jobs()
        job_list = self.query_one("#job-list", Vertical)
        job_list.remove_children()
        for i, job in enumerate(self.jobs):
            item = JobListItem(job, id=f"job-{i}")
            if i == self.selected_index:
                item.styles.border = ("solid", COLORS["border_focus"])
            job_list.mount(item)
        self.update_detail()

    def update_detail(self) -> None:
        header = self.query_one("#detail-header", Static)
        content = self.query_one("#detail-content", Static)
        if not self.jobs:
            header.update("")
            content.update("[dim]No jobs yet. Press 'n' to create one.[/]")
            return
        job = self.jobs[self.selected_index]
        next_runs = cron_parser.get_next_run(job.cron_expression, 5)
        run_str = (
            "\n".join(
                [
                    f"  {i + 1}. {dt.strftime('%Y-%m-%d %H:%M')}"
                    for i, dt in enumerate(next_runs)
                ]
            )
            if next_runs
            else "  Unable to calculate"
        )
        header.update(f"[bold]{job.name}[/]")
        content.update(f"""[dim]Details for:[/] {job.name}

[dim]Command:[/]
  [cron]{job.command}[/]

[dim]Schedule:[/]
  [cron]{job.cron_expression}[/]
  {cron_parser.to_human_readable(job.cron_expression)}

[dim]Description:[/]
  {job.description or "[dim]No description[/]"}

[dim]Status:[/]
  {"[success]Active[/]" if job.enabled else "[warning]Paused[/]"}

[dim]Next runs:[/]
{run_str}
""")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-add":
            self.app.push_screen(JobEditScreen(None))

    def action_toggle_job(self) -> None:
        if not self.jobs:
            return
        job = self.jobs[self.selected_index]
        updated, error = job_manager.JobManager.toggle_job(job.id)
        if error:
            self.app.notify(error, severity="error")
        else:
            self.load_jobs()

    def action_delete_job(self) -> None:
        if not self.jobs:
            return
        job = self.jobs[self.selected_index]
        self.app.push_screen(ConfirmScreen(f"Delete '{job.name}'?", self.load_jobs))

    def action_edit_job(self) -> None:
        if not self.jobs:
            return
        job = self.jobs[self.selected_index]
        self.app.push_screen(JobEditScreen(job))

    def action_new_job(self) -> None:
        self.app.push_screen(JobEditScreen(None))

    def action_run_job(self) -> None:
        if not self.jobs:
            return
        job = self.jobs[self.selected_index]
        self.app.notify(f"Running {job.name}...")
        record = history.run_and_log(job)
        if record.status == "success":
            self.app.notify(f"{job.name} completed successfully")
        else:
            self.app.notify(f"{job.name} failed: {record.error}", severity="error")
        self.load_jobs()

    def action_view_history(self) -> None:
        if not self.jobs:
            return
        job = self.jobs[self.selected_index]
        self.app.push_screen(HistoryScreen(job))

    def action_quit(self) -> None:
        self.app.exit()


class JobEditScreen(Screen):
    CSS = """
    Screen {
        background: $bg_primary;
    }
    .form-container {
        background: $bg_secondary;
        border: solid $border;
        padding: 2;
        margin: 2;
    }
    .form-label {
        color: $text_secondary;
        margin-bottom: 0;
    }
    .form-input {
        background: $bg_tertiary;
        color: $text_primary;
        border: solid $border;
        margin-bottom: 1;
    }
    .form-error {
        color: $error;
    }
    .btn-row {
        height: 3;
        align: right middle;
    }
    """

    BINDINGS = [
        Binding("escape", "cancel", "Cancel"),
    ]

    def __init__(self, job: CronJob | None):
        super().__init__()
        self.job = job
        self.is_new = job is None

    def compose(self) -> ComposeResult:
        title = "New Job" if self.is_new else f"Edit: {self.job.name}"
        yield Vertical(
            Static(f"[bold]{title}[/]", id="form-title"),
            Container(
                Vertical(
                    Label("Job Name", classes="form-label"),
                    Input(placeholder="my-job", id="input-name", classes="form-input"),
                    Label("Command", classes="form-label"),
                    TextArea(
                        placeholder="echo 'Hello World'",
                        id="input-command",
                        classes="form-input",
                    ),
                    Label("Cron Expression", classes="form-label"),
                    Input(
                        placeholder="* * * * *", id="input-cron", classes="form-input"
                    ),
                    Static("", id="cron-preview", classes="form-label"),
                    Label("Description", classes="form-label"),
                    TextArea(
                        placeholder="Optional description",
                        id="input-description",
                        classes="form-input",
                    ),
                    classes="form-container",
                ),
            ),
            Horizontal(
                Button("Save", id="btn-save", variant="primary"),
                Button("Cancel", id="btn-cancel"),
                classes="btn-row",
            ),
        )

    def on_mount(self) -> None:
        if self.job:
            self.query_one("#input-name", Input).value = self.job.name
            self.query_one("#input-command", TextArea).load_text(self.job.command)
            self.query_one("#input-cron", Input).value = self.job.cron_expression
            self.query_one("#input-description", TextArea).load_text(
                self.job.description
            )
        self.update_cron_preview()

    def on_input_changed(self, event: Input.Changed) -> None:
        if event.input.id == "input-cron":
            self.update_cron_preview()

    def update_cron_preview(self) -> None:
        cron = self.query_one("#input-cron", Input).value
        preview = self.query_one("#cron-preview", Static)
        if cron:
            valid, error = cron_parser.validate(cron)
            if valid:
                preview.update(f"[dim]{cron_parser.to_human_readable(cron)}[/]")
            else:
                preview.update(f"[error]{error}[/]")
        else:
            preview.update("")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-save":
            self.save_job()
        elif event.button.id == "btn-cancel":
            self.app.pop_screen()

    def action_cancel(self) -> None:
        self.app.pop_screen()

    def save_job(self) -> None:
        name = self.query_one("#input-name", Input).value.strip()
        command = self.query_one("#input-command", TextArea).text.strip()
        cron = self.query_one("#input-cron", Input).value.strip()
        description = self.query_one("#input-description", TextArea).text.strip()

        if not name or not command or not cron:
            self.app.notify("All fields required", severity="error")
            return

        if self.is_new:
            job, error = job_manager.JobManager.create_job(
                name, command, cron, description
            )
        else:
            job, error = job_manager.JobManager.update_job(
                self.job.id, name, command, cron, description
            )

        if error:
            self.app.notify(error, severity="error")
        else:
            self.app.notify(f"Job {'created' if self.is_new else 'updated'}")
            self.app.pop_screen()


class HistoryScreen(Screen):
    CSS = """
    Screen {
        background: $bg_primary;
    }
    .history-title {
        background: $bg_secondary;
        padding: 1;
    }
    .history-table {
        background: $bg_secondary;
    }
    """

    BINDINGS = [
        Binding("escape", "cancel", "Back"),
    ]

    def __init__(self, job: CronJob):
        super().__init__()
        self.job = job

    def compose(self) -> ComposeResult:
        yield Vertical(
            Static(f"History: {self.job.name}", classes="history-title"),
            DataTable(id="history-table"),
            Button("Back", id="btn-back"),
        )

    def on_mount(self) -> None:
        table = self.query_one("#history-table", DataTable)
        table.add_columns("Time", "Status", "Duration", "Output")
        records = history.get_history_for_job(self.job.id)
        for record in records:
            output = (record.output or record.error or "")[:50].replace("\n", " ")
            table.add_row(
                record.timestamp.strftime("%Y-%m-%d %H:%M"),
                record.status,
                history.format_duration(record.duration),
                output,
            )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-back":
            self.app.pop_screen()

    def action_cancel(self) -> None:
        self.app.pop_screen()


class ConfirmScreen(Screen):
    CSS = """
    Screen {
        background: $bg_primary;
    }
    .confirm-box {
        background: $bg_secondary;
        border: solid $border;
        padding: 2;
        align: center middle;
    }
    """

    BINDINGS = [
        Binding("escape", "cancel", "Cancel"),
    ]

    def __init__(self, message: str, on_confirm):
        super().__init__()
        self.message = message
        self.on_confirm = on_confirm

    def compose(self) -> ComposeResult:
        yield Container(
            Static(f"[bold]{self.message}[/]", classes="confirm-box"),
            Horizontal(
                Button("Yes, Delete", id="btn-confirm", variant="error"),
                Button("Cancel", id="btn-cancel"),
            ),
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-confirm":
            job_list_screen = self.app.screen
            if hasattr(job_list_screen, "jobs"):
                idx = job_list_screen.selected_index
                if job_list_screen.jobs:
                    job = job_list_screen.jobs[idx]
                    job_manager.JobManager.delete_job(job.id)
                    new_count = len(job_list_screen.jobs) - 1
                    if new_count > 0:
                        job_list_screen.selected_index = min(idx, new_count - 1)
                    else:
                        job_list_screen.selected_index = 0
                    job_list_screen.load_jobs()
        self.app.pop_screen()

    def action_cancel(self) -> None:
        self.app.pop_screen()
