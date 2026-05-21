"""
Incident Command Center TUI - Main Application
A Textual application for on-call engineers to manage incidents.
"""
import asyncio
from datetime import datetime
from typing import Optional

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.color import Color
from textual.containers import Container, Horizontal, Vertical, VerticalScroll
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import (
    Button,
    Header,
    Footer,
    ListItem,
    ListView,
    Static,
    TextArea,
    Input,
    Label,
    TabbedContent,
    Tabs,
    Tab,
)
from textual import on
from rich.console import Console
from rich.table import Table

from models import Database, Incident, TimelineEntry, OnCallEngineer, IncidentStatus, Severity
from db_manager import IncidentManager, TimelineManager, OnCallManager


# Color scheme for severity levels
SEVERITY_COLORS = {
    "P1": "#ff4444",  # Red
    "P2": "#ff8800",  # Orange
    "P3": "#ffcc00",  # Yellow
    "P4": "#4488ff",  # Blue
}

STATUS_COLORS = {
    "Declared": "#888888",
    "Investigating": "#ff4444",
    "Identified": "#ff8800",
    "Mitigating": "#ffcc00",
    "Resolved": "#44cc44",
}


def severity_badge(severity: str) -> str:
    """Generate a styled severity badge."""
    color = SEVERITY_COLORS.get(severity, "#888888")
    return f"[{color}]{severity}[/{color}]"


def status_indicator(status: str) -> str:
    """Generate a styled status indicator."""
    color = STATUS_COLORS.get(status, "#888888")
    return f"[{color}]{status}[/{color}]"


class IncidentListItem(ListItem):
    """Custom list item for displaying an incident in the sidebar."""

    def __init__(self, incident: Incident):
        self.incident = incident
        title = f"{severity_badge(incident.severity)} {incident.title[:40]}"
        if len(incident.title) > 40:
            title += "..."
        super().__init__(
            Static(title, classes="incident-title"),
            Static(f"#{incident.id} {status_indicator(incident.status)}", classes="incident-meta"),
            id=f"incident-item-{incident.id}"
        )


class IncidentSidebar(Vertical):
    """Sidebar containing the list of incidents."""

    BINDINGS = [
        Binding("n", "create_incident", "New Incident", priority=True),
        Binding("r", "refresh_list", "Refresh", priority=True),
    ]

    def __init__(self, incident_manager: IncidentManager):
        super().__init__()
        self.incident_manager = incident_manager

    def compose(self) -> ComposeResult:
        yield Static("INCIDENTS", classes="sidebar-header")
        yield ListView(id="incident-list", classes="incident-list")
        with Horizontal(classes="sidebar-actions"):
            yield Button("+ New", id="btn-new-incident", variant="primary", classes="sidebar-btn")
            yield Button("⟳", id="btn-refresh", classes="sidebar-btn", tooltip="Refresh list")

    async def load_incidents(self) -> None:
        """Load and display all incidents."""
        list_view = self.query_one("#incident-list", ListView)
        incidents = await self.incident_manager.get_all_incidents()
        
        list_view.clear()
        for incident in incidents:
            list_view.append(IncidentListItem(incident))
        
        if incidents:
            list_view.index = 0

    @on(ListView.Selected, "#incident-list")
    async def on_incident_selected(self, event: ListView.Selected) -> None:
        """Handle incident selection."""
        if isinstance(event.item, IncidentListItem):
            self.app.selected_incident_id = event.item.incident.id
            await self.app.update_detail_panel()

    @on(Button.Pressed, "#btn-new-incident")
    async def on_new_incident(self) -> None:
        """Open new incident dialog."""
        self.app.action_create_incident()

    @on(Button.Pressed, "#btn-refresh")
    async def on_refresh(self) -> None:
        """Refresh the incident list."""
        await self.load_incidents()
        await self.app.update_detail_panel()

    def action_refresh_list(self) -> None:
        """Refresh action binding."""
        asyncio.create_task(self.load_incidents())
        asyncio.create_task(self.app.update_detail_panel())


class IncidentDetailPanel(Vertical):
    """Main panel showing details of the selected incident."""

    def __init__(self, incident_manager: IncidentManager, timeline_manager: TimelineManager):
        super().__init__()
        self.incident_manager = incident_manager
        self.timeline_manager = timeline_manager
        self.current_incident: Optional[Incident] = None

    def compose(self) -> ComposeResult:
        with VerticalScroll(id="detail-scroll"):
            yield Static("Select an incident to view details", id="detail-placeholder", classes="placeholder-text")
            
            with Container(id="detail-content", classes="hidden"):
                # Header section
                yield Static("", id="detail-severity", classes="detail-severity")
                yield Static("", id="detail-title", classes="detail-title")
                yield Static("", id="detail-meta", classes="detail-meta")
                
                # Status section
                with Horizontal(id="status-section"):
                    yield Label("Status:", classes="detail-label")
                    yield Static("", id="detail-status")
                    with Horizontal(classes="status-buttons"):
                        yield Button("Update Status", id="btn-update-status", variant="primary")
                
                # Assignment section
                with Horizontal(id="assignment-section"):
                    yield Label("Assigned:", classes="detail-label")
                    yield Static("", id="detail-assigned")
                    with Horizontal(classes="assign-buttons"):
                        yield Button("Assign", id="btn-assign", variant="success")
                
                # Description section
                yield Label("Description:", classes="detail-label")
                yield Static("", id="detail-description", classes="detail-description")
                
                # Timeline section
                yield Label("Timeline:", classes="detail-label")
                yield ListView(id="timeline-list", classes="timeline-list")
                with Horizontal():
                    yield TextArea(placeholder="Add a note...", id="note-input", classes="note-input")
                    yield Button("Add Note", id="btn-add-note", variant="primary")
                
                # Actions section
                with Horizontal(id="actions-section"):
                    yield Button("Change Severity", id="btn-change-severity", variant="warning")
                    yield Button("Delete Incident", id="btn-delete", variant="error")

    async def update_content(self, incident_id: Optional[int]) -> None:
        """Update the detail panel with incident data."""
        placeholder = self.query_one("#detail-placeholder", Static)
        content = self.query_one("#detail-content", Container)
        
        if incident_id is None:
            placeholder.remove_class("hidden")
            content.add_class("hidden")
            self.current_incident = None
            return
        
        incident = await self.incident_manager.get_incident(incident_id)
        if incident is None:
            placeholder.remove_class("hidden")
            content.add_class("hidden")
            self.current_incident = None
            return
        
        self.current_incident = incident
        placeholder.add_class("hidden")
        content.remove_class("hidden")
        
        # Update header
        severity_static = self.query_one("#detail-severity", Static)
        severity_static.update(f"[b]{severity_badge(incident.severity)}[/b]")
        
        title_static = self.query_one("#detail-title", Static)
        title_static.update(f"[b]{incident.title}[/b]")
        
        meta_static = self.query_one("#detail-meta", Static)
        created = incident.created_at.strftime("%Y-%m-%d %H:%M") if incident.created_at else "Unknown"
        updated = incident.updated_at.strftime("%Y-%m-%d %H:%M") if incident.updated_at else "Unknown"
        meta_static.update(f"ID: #{incident.id} | Created: {created} | Updated: {updated}")
        
        # Update status
        status_static = self.query_one("#detail-status", Static)
        status_static.update(f"[b]{status_indicator(incident.status)}[/b]")
        
        # Update assignment
        assigned_static = self.query_one("#detail-assigned", Static)
        if incident.assigned_to:
            assigned_static.update(f"[b]{incident.assigned_to}[/b]")
        else:
            assigned_static.update("[i]Unassigned[/i]")
        
        # Update description
        desc_static = self.query_one("#detail-description", Static)
        if incident.description:
            desc_static.update(incident.description)
        else:
            desc_static.update("[i]No description[/i]")
        
        # Update timeline
        await self.update_timeline(incident_id)

    async def update_timeline(self, incident_id: int) -> None:
        """Update the timeline list."""
        timeline_view = self.query_one("#timeline-list", ListView)
        entries = await self.timeline_manager.get_timeline(incident_id)
        
        timeline_view.clear()
        for entry in entries:
            icon = self._get_entry_icon(entry.entry_type)
            time_str = entry.created_at.strftime("%H:%M") if entry.created_at else ""
            author_str = f" by {entry.created_by}" if entry.created_by else ""
            content = f"[dim]{time_str}[/dim] {icon} {entry.content}{author_str}"
            timeline_view.append(ListItem(Static(content), classes=f"timeline-entry timeline-{entry.entry_type}"))

    def _get_entry_icon(self, entry_type: str) -> str:
        """Get icon for timeline entry type."""
        icons = {
            "status_change": "🔄",
            "note": "📝",
            "assignment": "👤",
        }
        return icons.get(entry_type, "•")

    @on(Button.Pressed, "#btn-update-status")
    async def on_update_status(self) -> None:
        """Update incident status."""
        if self.current_incident:
            self.app.show_status_dialog(self.current_incident)

    @on(Button.Pressed, "#btn-assign")
    async def on_assign(self) -> None:
        """Assign incident to an engineer."""
        if self.current_incident:
            self.app.show_assign_dialog(self.current_incident)

    @on(Button.Pressed, "#btn-add-note")
    async def on_add_note(self) -> None:
        """Add a note to the incident."""
        if self.current_incident:
            try:
                note_input = self.query_one("#note-input", TextArea)
                content = note_input.text.strip()
                if content:
                    await self.timeline_manager.add_note(
                        self.current_incident.id, content, self.app.current_user
                    )
                    note_input.text = ""
                    await self.update_timeline(self.current_incident.id)
            except Exception as e:
                self.app.notify(f"Error adding note: {str(e)}")

    @on(Button.Pressed, "#btn-change-severity")
    async def on_change_severity(self) -> None:
        """Change incident severity."""
        if self.current_incident:
            self.app.show_severity_dialog(self.current_incident)

    @on(Button.Pressed, "#btn-delete")
    async def on_delete(self) -> None:
        """Delete the incident."""
        if self.current_incident:
            self.app.show_delete_confirmation(self.current_incident)


class OnCallRosterPanel(Vertical):
    """Panel showing the on-call team roster."""

    def __init__(self, oncall_manager: OnCallManager):
        super().__init__()
        self.oncall_manager = oncall_manager

    def compose(self) -> ComposeResult:
        yield Static("ON-CALL ROSTER", classes="sidebar-header")
        yield ListView(id="roster-list", classes="roster-list")
        with Horizontal(classes="sidebar-actions"):
            yield Button("+ Add", id="btn-add-engineer", variant="success", classes="sidebar-btn")
            yield Button("⟳", id="btn-refresh-roster", classes="sidebar-btn", tooltip="Refresh roster")

    async def load_roster(self) -> None:
        """Load and display the on-call roster."""
        list_view = self.query_one("#roster-list", ListView)
        engineers = await self.oncall_manager.get_active_engineers()
        
        list_view.clear()
        for eng in engineers:
            role_icon = {"primary": "⭐", "secondary": "👤", "escalation": "🚨"}.get(eng.role, "•")
            item = ListItem(
                Static(f"{role_icon} [b]{eng.name}[/b]"),
                Static(f"{eng.email} ({eng.role})", classes="roster-meta"),
                id=f"engineer-{eng.id}"
            )
            list_view.append(item)

    @on(Button.Pressed, "#btn-add-engineer")
    async def on_add_engineer(self) -> None:
        """Add a new engineer."""
        self.app.show_add_engineer_dialog()

    @on(Button.Pressed, "#btn-refresh-roster")
    async def on_refresh(self) -> None:
        """Refresh the roster."""
        await self.load_roster()


class StatusDialog(Container):
    """Dialog for updating incident status."""

    def __init__(self, incident: Incident, incident_manager: IncidentManager, app: App):
        super().__init__()
        self.incident = incident
        self.incident_manager = incident_manager
        self.app = app

    def compose(self) -> ComposeResult:
        yield Static(f"Update Status for #{self.incident.id}: {self.incident.title}", classes="dialog-title")
        with Vertical(classes="dialog-content"):
            yield Label("Select new status:")
            for status in IncidentStatus:
                yield Button(
                    status.value,
                    id=f"status-{status.value}",
                    classes="status-option",
                    variant="primary" if status.value == self.incident.status else "default"
                )
        with Horizontal():
            yield Button("Cancel", id="btn-cancel", variant="default")
        yield Button("×", id="btn-close", classes="close-btn")

    @on(Button.Pressed)
    async def on_status_selected(self, event: Button.Pressed) -> None:
        button_id = event.button.id
        if button_id == "btn-cancel" or button_id == "btn-close":
            await self.app.dismiss()
        elif button_id and button_id.startswith("status-"):
            new_status = button_id.replace("status-", "")
            await self.incident_manager.update_status(
                self.incident.id, new_status, self.app.current_user
            )
            await self.app.dismiss()
            await self.app.refresh_all()


class AssignDialog(Container):
    """Dialog for assigning an incident to an engineer."""

    def __init__(self, incident: Incident, incident_manager: IncidentManager, oncall_manager: OnCallManager, app: App):
        super().__init__()
        self.incident = incident
        self.incident_manager = incident_manager
        self.oncall_manager = oncall_manager
        self.app = app
        self.engineers: list = []

    def compose(self) -> ComposeResult:
        yield Static(f"Assign #{self.incident.id}: {self.incident.title}", classes="dialog-title")
        with Vertical(classes="dialog-content"):
            yield Label("Select engineer:")
            yield Static("Loading engineers...", id="engineers-loading")
            yield Vertical(id="engineer-buttons", classes="engineer-buttons")
            yield Label("Or enter name:", classes="input-label")
            yield Input(placeholder="Engineer name...", id="assign-input")
            yield Button("Assign", id="btn-do-assign", variant="success")
        with Horizontal():
            yield Button("Cancel", id="btn-cancel", variant="default")
        yield Button("×", id="btn-close", classes="close-btn")

    async def on_mount(self) -> None:
        """Load engineers when dialog opens."""
        # Remove loading message and load engineers
        loading = self.query_one("#engineers-loading", Static)
        loading.remove()
        buttons_container = self.query_one("#engineer-buttons", Vertical)
        
        self.engineers = await self.oncall_manager.get_active_engineers()
        for eng in self.engineers:
            buttons_container.append(
                Button(
                    f"{eng.name} ({eng.role})",
                    id=f"assign-{eng.id}",
                    variant="primary" if eng.role == "primary" else "default",
                    classes="assign-option"
                )
            )

    @on(Button.Pressed)
    async def on_assign_selected(self, event: Button.Pressed) -> None:
        button_id = event.button.id
        if button_id == "btn-cancel" or button_id == "btn-close":
            await self.app.dismiss()
        elif button_id == "btn-do-assign":
            assign_input = self.query_one("#assign-input", Input)
            if assign_input.value.strip():
                await self.incident_manager.assign_incident(
                    self.incident.id, assign_input.value.strip(), self.app.current_user
                )
                await self.app.dismiss()
                await self.app.refresh_all()
        elif button_id and button_id.startswith("assign-"):
            engineer_id = int(button_id.replace("assign-", ""))
            engineer = next((e for e in self.engineers if e.id == engineer_id), None)
            if engineer:
                await self.incident_manager.assign_incident(
                    self.incident.id, engineer.name, self.app.current_user
                )
                await self.app.dismiss()
                await self.app.refresh_all()


class SeverityDialog(Container):
    """Dialog for changing incident severity."""

    def __init__(self, incident: Incident, incident_manager: IncidentManager, app: App):
        super().__init__()
        self.incident = incident
        self.incident_manager = incident_manager
        self.app = app

    def compose(self) -> ComposeResult:
        yield Static(f"Change Severity for #{self.incident.id}", classes="dialog-title")
        with Vertical(classes="dialog-content"):
            yield Label("Select new severity:")
            for sev in ["P1", "P2", "P3", "P4"]:
                color = SEVERITY_COLORS[sev]
                is_selected = sev == self.incident.severity
                yield Button(
                    f"{severity_badge(sev)}",
                    id=f"sev-{sev}",
                    variant="primary" if is_selected else "default",
                    classes="severity-option"
                )
            yield Label(f"Current: {severity_badge(self.incident.severity)}", classes="current-severity")
        with Horizontal():
            yield Button("Cancel", id="btn-cancel", variant="default")
        yield Button("×", id="btn-close", classes="close-btn")

    @on(Button.Pressed)
    async def on_severity_selected(self, event: Button.Pressed) -> None:
        button_id = event.button.id
        if button_id == "btn-cancel" or button_id == "btn-close":
            await self.app.dismiss()
        elif button_id and button_id.startswith("sev-"):
            new_severity = button_id.replace("sev-", "")
            await self.incident_manager.update_severity(
                self.incident.id, new_severity, self.app.current_user
            )
            await self.app.dismiss()
            await self.app.refresh_all()


class NewIncidentDialog(Container):
    """Dialog for creating a new incident."""

    def __init__(self, incident_manager: IncidentManager, app: App):
        super().__init__()
        self.incident_manager = incident_manager
        self.app = app

    def compose(self) -> ComposeResult:
        yield Static("Create New Incident", classes="dialog-title")
        with Vertical(classes="dialog-content"):
            yield Label("Title:", classes="input-label")
            yield Input(placeholder="Brief description of the incident...", id="incident-title")
            yield Label("Description:", classes="input-label")
            yield TextArea(placeholder="Detailed description...", id="incident-desc", height=4)
            yield Label("Severity:", classes="input-label")
            with Horizontal(classes="severity-select"):
                for sev in ["P1", "P2", "P3", "P4"]:
                    yield Button(
                        f"{severity_badge(sev)}",
                        id=f"new-sev-{sev}",
                        variant="primary" if sev == "P3" else "default",
                        classes="sev-btn"
                    )
            yield Label("Assign to:", classes="input-label")
            yield Input(placeholder="Engineer name (optional)...", id="incident-assign")
            yield Button("Create Incident", id="btn-create", variant="success", classes="create-btn")
        with Horizontal():
            yield Button("Cancel", id="btn-cancel", variant="default")
        yield Button("×", id="btn-close", classes="close-btn")

    @on(Button.Pressed, ".sev-btn")
    async def on_severity_select(self, event: Button.Pressed) -> None:
        """Highlight selected severity."""
        for btn in self.query(".sev-btn"):
            btn.variant = "default"
        event.button.variant = "primary"

    def _get_selected_severity(self) -> str:
        """Get currently selected severity."""
        for btn in self.query(".sev-btn"):
            if btn.variant == "primary":
                return btn.id.replace("new-sev-", "")
        return "P3"

    @on(Button.Pressed)
    async def on_create(self, event: Button.Pressed) -> None:
        button_id = event.button.id
        if button_id == "btn-cancel" or button_id == "btn-close":
            await self.app.dismiss()
        elif button_id == "btn-create":
            title_input = self.query_one("#incident-title", Input)
            desc_input = self.query_one("#incident-desc", TextArea)
            assign_input = self.query_one("#incident-assign", Input)
            
            title = title_input.value.strip()
            if not title:
                title_input.focus()
                return
            
            incident = await self.incident_manager.create_incident(
                title=title,
                description=desc_input.text.strip(),
                severity=self._get_selected_severity(),
                assigned_to=assign_input.value.strip() or None
            )
            await self.app.dismiss()
            self.app.selected_incident_id = incident.id
            await self.app.refresh_all()


class AddEngineerDialog(Container):
    """Dialog for adding a new on-call engineer."""

    def __init__(self, oncall_manager: OnCallManager, app: App):
        super().__init__()
        self.oncall_manager = oncall_manager
        self.app = app

    def compose(self) -> ComposeResult:
        yield Static("Add On-Call Engineer", classes="dialog-title")
        with Vertical(classes="dialog-content"):
            yield Label("Name:", classes="input-label")
            yield Input(placeholder="Engineer name...", id="eng-name")
            yield Label("Email:", classes="input-label")
            yield Input(placeholder="engineer@company.com", id="eng-email")
            yield Label("Role:", classes="input-label")
            with Horizontal(classes="role-select"):
                yield Button("Primary", id="role-primary", variant="primary", classes="role-btn")
                yield Button("Secondary", id="role-secondary", variant="default", classes="role-btn")
                yield Button("Escalation", id="role-escalation", variant="default", classes="role-btn")
            yield Button("Add Engineer", id="btn-add-eng", variant="success", classes="create-btn")
        with Horizontal():
            yield Button("Cancel", id="btn-cancel", variant="default")
        yield Button("×", id="btn-close", classes="close-btn")

    def _get_selected_role(self) -> str:
        """Get currently selected role."""
        for btn in self.query(".role-btn"):
            if btn.variant == "primary":
                return btn.id.replace("role-", "")
        return "secondary"

    @on(Button.Pressed, ".role-btn")
    async def on_role_select(self, event: Button.Pressed) -> None:
        """Highlight selected role."""
        for btn in self.query(".role-btn"):
            btn.variant = "default"
        event.button.variant = "primary"

    @on(Button.Pressed)
    async def on_add(self, event: Button.Pressed) -> None:
        button_id = event.button.id
        if button_id == "btn-cancel" or button_id == "btn-close":
            await self.app.dismiss()
        elif button_id == "btn-add-eng":
            name_input = self.query_one("#eng-name", Input)
            email_input = self.query_one("#eng-email", Input)
            
            name = name_input.value.strip()
            email = email_input.value.strip()
            
            if not name or not email:
                return
            
            await self.oncall_manager.add_engineer(name, email, self._get_selected_role())
            await self.app.dismiss()
            await self.app.refresh_roster()


class ConfirmDialog(Container):
    """Confirmation dialog for delete operations."""

    def __init__(self, message: str, on_confirm, app: App):
        super().__init__()
        self.message = message
        self.on_confirm = on_confirm
        self.app = app

    def compose(self) -> ComposeResult:
        yield Static("⚠️ Confirm Action", classes="dialog-title")
        yield Static(self.message, classes="confirm-message")
        with Horizontal():
            yield Button("Cancel", id="btn-cancel", variant="default")
            yield Button("Confirm", id="btn-confirm", variant="error")

    @on(Button.Pressed)
    async def on_button(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-confirm":
            await self.on_confirm()
        await self.app.dismiss()


class IncidentCommandCenter(App):
    """Main TUI Application for Incident Command Center."""

    CSS = """
    /* Layout */
    Screen {
        layout: grid;
        grid-size: 3 1;
        grid-columns: 1fr 2fr 1fr;
    }

    /* Sidebar styling */
    IncidentSidebar {
        width: 100%;
        height: 100%;
        background: $surface-darken-1;
        border-right: solid $border;
    }

    /* On-call roster styling */
    OnCallRosterPanel {
        width: 100%;
        height: 100%;
        background: $surface-darken-1;
        border-left: solid $border;
    }

    /* Main detail panel */
    IncidentDetailPanel {
        width: 100%;
        height: 100%;
        padding: 1 2;
    }

    /* Sidebar header */
    .sidebar-header {
        height: 3;
        width: 100%;
        background: $primary;
        color: $text;
        content-align: center middle;
        text-style: bold;
        padding: 1 0;
    }

    /* Incident list */
    .incident-list {
        height: 1fr;
        padding: 0 1;
    }

    .incident-title {
        width: 100%;
        height: auto;
        padding: 1 0;
    }

    .incident-meta {
        width: 100%;
        height: auto;
        color: $text-muted;
        padding: 0 0 1 0;
    }

    /* Roster list */
    .roster-list {
        height: 1fr;
        padding: 0 1;
    }

    .roster-meta {
        width: 100%;
        color: $text-muted;
    }

    /* Sidebar actions */
    .sidebar-actions {
        height: auto;
        padding: 1;
        align: center middle;
        spacing: 1;
    }

    .sidebar-btn {
        min-width: 16;
    }

    /* Detail panel */
    #detail-scroll {
        height: 100%;
    }

    .placeholder-text {
        width: 100%;
        height: 100%;
        content-align: center middle;
        color: $text-muted;
        text-style: italic;
    }

    #detail-content {
        padding: 1 0;
    }

    .detail-severity {
        height: 3;
        width: 100%;
    }

    .detail-title {
        height: auto;
        width: 100%;
        text-size: 150%;
        text-style: bold;
        margin-bottom: 1;
    }

    .detail-meta {
        width: 100%;
        color: $text-muted;
        margin-bottom: 2;
    }

    .detail-label {
        width: 100%;
        text-style: bold;
        margin-top: 2;
        margin-bottom: 1;
    }

    .detail-description {
        width: 100%;
        height: auto;
        padding: 1;
        background: $surface-darken-2;
        margin-bottom: 1;
    }

    /* Timeline */
    .timeline-list {
        height: 25vh;
        margin-bottom: 1;
    }

    .timeline-entry {
        padding: 0.5 1;
    }

    /* Note input */
    .note-input {
        height: 5;
        margin-bottom: 1;
    }

    /* Status section */
    #status-section, #assignment-section, #actions-section {
        height: auto;
        spacing: 1;
        margin-bottom: 1;
    }

    /* Actions section */
    #actions-section {
        margin-top: 2;
        spacing: 1;
    }

    /* Dialog styling */
    Dialog {
        border: thick $primary;
        background: $surface;
    }

    .dialog-title {
        width: 100%;
        text-align: center;
        text-style: bold;
        text-size: 120%;
        margin-bottom: 2;
        color: $accent;
    }

    .dialog-content {
        width: 100%;
        padding: 1 2;
    }

    .input-label {
        width: 100%;
        text-style: bold;
        margin-top: 1;
        margin-bottom: 0.5;
    }

    .close-btn {
        width: 3;
        height: 3;
        position: absolute top right;
    }

    .status-option, .assign-option, .severity-option {
        width: 100%;
        margin: 0.5 0;
    }

    .current-severity {
        margin-top: 1;
        text-align: center;
    }

    .severity-select, .role-select {
        spacing: 1;
        height: auto;
        margin-bottom: 1;
    }

    .sev-btn, .role-btn {
        min-width: 20;
    }

    .create-btn {
        width: 100%;
        margin-top: 2;
    }

    .confirm-message {
        width: 100%;
        text-align: center;
        margin: 2 0;
    }

    /* Hidden class */
    .hidden {
        display: none;
    }

    /* Button spacing */
    Button {
        margin: 0 0.5;
    }
    """

    BINDINGS = [
        Binding("q", "quit", "Quit", show=True),
        Binding("n", "create_incident", "New Incident"),
        Binding("r", "refresh", "Refresh"),
        Binding("?", "toggle_help", "Help"),
    ]

    selected_incident_id: reactive[Optional[int]] = reactive(None)
    current_user: str = "On-Call Engineer"

    def __init__(self):
        super().__init__()
        self.db = Database("incidents.db")
        self.incident_manager = IncidentManager(self.db)
        self.timeline_manager = TimelineManager(self.db)
        self.oncall_manager = OnCallManager(self.db)

    async def on_mount(self) -> None:
        """Initialize the application."""
        # Initialize database
        await self.db.init_db()
        await self.oncall_manager.seed_default_engineers()

        # Load data
        await self.query_one(IncidentSidebar).load_incidents()
        await self.query_one(OnCallRosterPanel).load_roster()

    def compose(self) -> ComposeResult:
        yield Header()
        yield IncidentSidebar(self.incident_manager)
        yield IncidentDetailPanel(self.incident_manager, self.timeline_manager)
        yield OnCallRosterPanel(self.oncall_manager)
        yield Footer()

    async def update_detail_panel(self) -> None:
        """Update the detail panel."""
        panel = self.query_one(IncidentDetailPanel)
        await panel.update_content(self.selected_incident_id)

    async def refresh_all(self) -> None:
        """Refresh all panels."""
        sidebar = self.query_one(IncidentSidebar)
        await sidebar.load_incidents()
        await self.update_detail_panel()

    async def refresh_roster(self) -> None:
        """Refresh the roster panel."""
        roster = self.query_one(OnCallRosterPanel)
        await roster.load_roster()

    def action_create_incident(self) -> None:
        """Create a new incident."""
        self.push_screen(NewIncidentDialog(self.incident_manager, self))

    def action_refresh(self) -> None:
        """Refresh action."""
        asyncio.create_task(self.refresh_all())

    def action_toggle_help(self) -> None:
        """Toggle help display."""
        # Simple help notification
        self.notify("Commands: [n]ew incident, [r]efresh, [q]uit, [?] help")

    # Dialog methods
    def show_status_dialog(self, incident: Incident) -> None:
        """Show status update dialog."""
        self.push_screen(StatusDialog(incident, self.incident_manager, self))

    def show_assign_dialog(self, incident: Incident) -> None:
        """Show assignment dialog."""
        self.push_screen(AssignDialog(incident, self.incident_manager, self.oncall_manager, self))

    def show_severity_dialog(self, incident: Incident) -> None:
        """Show severity change dialog."""
        self.push_screen(SeverityDialog(incident, self.incident_manager, self))

    def show_delete_confirmation(self, incident: Incident) -> None:
        """Show delete confirmation dialog."""
        async def do_delete():
            await self.incident_manager.delete_incident(incident.id)
            self.selected_incident_id = None
            await self.refresh_all()
        
        self.push_screen(ConfirmDialog(
            f"Are you sure you want to delete incident #{incident.id}?\n\nThis action cannot be undone.",
            do_delete,
            self
        ))

    def show_add_engineer_dialog(self) -> None:
        """Show add engineer dialog."""
        self.push_screen(AddEngineerDialog(self.oncall_manager, self))


async def main():
    """Main entry point."""
    app = IncidentCommandCenter()
    await app.run_async()


if __name__ == "__main__":
    asyncio.run(main())
