"""Termail - A Textual TUI Email Client."""

import os
import sys
from datetime import datetime
from typing import Optional, List

from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical, ScrollableContainer
from textual.widgets import Header, Footer, Static, Button, Input, TextArea, ListView, ListItem, Label, LoadingIndicator
from textual.screen import Screen
from textual import work
from textual.binding import Binding

# Import our modules
from config import Config
from imap_client import IMAPClient, EmailMessage
from smtp_client import SMTPClient


class ConfigScreen(Screen):
    """Configuration screen for email settings."""
    
    def __init__(self, app_ref):
        super().__init__()
        self.app_ref = app_ref
    
    def compose(self) -> ComposeResult:
        yield Container(
            Vertical(
                Static("Email Configuration", classes="config-title"),
                Input(placeholder="IMAP Server", id="imap_server", classes="config-input"),
                Input(placeholder="IMAP Port", id="imap_port", classes="config-input"),
                Input(placeholder="SMTP Server", id="smtp_server", classes="config-input"),
                Input(placeholder="SMTP Port", id="smtp_port", classes="config-input"),
                Input(placeholder="Username/Email", id="username", classes="config-input"),
                Input(placeholder="Password", password=True, id="password", classes="config-input"),
                Input(placeholder="Display Name", id="name", classes="config-input"),
                Horizontal(
                    Button("Save", variant="primary", id="save_config"),
                    Button("Test Connection", variant="default", id="test_connection"),
                    Button("Cancel", variant="default", id="cancel_config"),
                ),
                classes="config-form"
            ),
            classes="config-container"
        )
    
    def on_mount(self):
        """Load current config values."""
        cfg = self.app_ref.config.config
        self.query_one("#imap_server", Input).value = cfg.imap_server
        self.query_one("#imap_port", Input).value = str(cfg.imap_port)
        self.query_one("#smtp_server", Input).value = cfg.smtp_server
        self.query_one("#smtp_port", Input).value = str(cfg.smtp_port)
        self.query_one("#username", Input).value = cfg.username
        self.query_one("#password", Input).value = cfg.password
        self.query_one("#name", Input).value = cfg.name
    
    def on_button_pressed(self, event: Button.Pressed):
        """Handle button presses."""
        if event.button.id == "save_config":
            self._save_config()
        elif event.button.id == "test_connection":
            self._test_connection()
        elif event.button.id == "cancel_config":
            self.app_ref.pop_screen()
    
    def _save_config(self):
        """Save configuration."""
        cfg = self.app_ref.config.config
        cfg.imap_server = self.query_one("#imap_server", Input).value
        cfg.imap_port = int(self.query_one("#imap_port", Input).value or 993)
        cfg.smtp_server = self.query_one("#smtp_server", Input).value
        cfg.smtp_port = int(self.query_one("#smtp_port", Input).value or 587)
        cfg.username = self.query_one("#username", Input).value
        cfg.password = self.query_one("#password", Input).value
        cfg.name = self.query_one("#name", Input).value
        cfg.email = cfg.username
        self.app_ref.config.save()
        self.app_ref.notify("Configuration saved!", severity="information")
        self.app_ref.pop_screen()
    
    def _test_connection(self):
        """Test IMAP connection."""
        cfg = self.app_ref.config.config
        client = IMAPClient(
            cfg.imap_server, cfg.imap_port, cfg.imap_use_ssl,
            cfg.username, cfg.password
        )
        
        if client.connect():
            self.app_ref.notify("Connection successful!", severity="information")
            client.disconnect()
        else:
            self.app_ref.notify("Connection failed!", severity="error")


class ComposeScreen(Screen):
    """Compose new email screen."""
    
    def __init__(self, app_ref, reply_to: EmailMessage = None):
        super().__init__()
        self.app_ref = app_ref
        self.reply_to = reply_to
    
    def compose(self) -> ComposeResult:
        to_value = ""
        subject_value = ""
        
        if self.reply_to:
            to_value = self.reply_to.sender
            if self.reply_to.subject:
                if not self.reply_to.subject.startswith("Re:"):
                    subject_value = f"Re: {self.reply_to.subject}"
                else:
                    subject_value = self.reply_to.subject
        
        yield Container(
            Vertical(
                Static("Compose Email", classes="compose-title"),
                Input(placeholder="To:", value=to_value, id="compose_to", classes="compose-input"),
                Input(placeholder="Subject:", value=subject_value, id="compose_subject", classes="compose-input"),
                TextArea(placeholder="Write your message here...", id="compose_body", classes="compose-body"),
                Horizontal(
                    Button("Send", variant="primary", id="send_email"),
                    Button("Save Draft", variant="default", id="save_draft"),
                    Button("Cancel", variant="default", id="cancel_compose"),
                ),
                classes="compose-form"
            ),
            classes="compose-container"
        )
    
    def on_button_pressed(self, event: Button.Pressed):
        """Handle button presses."""
        if event.button.id == "send_email":
            self._send_email()
        elif event.button.id == "save_draft":
            self._save_draft()
        elif event.button.id == "cancel_compose":
            self.app_ref.pop_screen()
    
    def _send_email(self):
        """Send the email."""
        to_email = self.query_one("#compose_to", Input).value.strip()
        subject = self.query_one("#compose_subject", Input).value.strip()
        body = self.query_one("#compose_body", TextArea).text
        
        if not to_email:
            self.app_ref.notify("Please enter a recipient!", severity="error")
            return
        
        if not subject:
            self.app_ref.notify("Please enter a subject!", severity="error")
            return
        
        cfg = self.app_ref.config.config
        smtp = SMTPClient(
            cfg.smtp_server, cfg.smtp_port, cfg.smtp_use_tls,
            cfg.username, cfg.password
        )
        
        if smtp.send_email(to_email, subject, body, cfg.name):
            self.app_ref.notify("Email sent!", severity="information")
            self.app_ref.pop_screen()
        else:
            self.app_ref.notify("Failed to send email!", severity="error")
    
    def _save_draft(self):
        """Save as draft (placeholder for now)."""
        self.app_ref.notify("Draft saved!", severity="information")
        self.app_ref.pop_screen()


class EmailDetailScreen(Screen):
    """Email detail view screen."""
    
    def __init__(self, app_ref, email: EmailMessage, folder: str = "INBOX"):
        super().__init__()
        self.app_ref = app_ref
        self.email = email
        self.folder = folder
        self.body = ""
    
    def compose(self) -> ComposeResult:
        yield Container(
            Vertical(
                Static(f"From: {self.email.sender}", classes="detail-header"),
                Static(f"To: {self.email.to}", classes="detail-header"),
                Static(f"Date: {self.email.date}", classes="detail-header"),
                Static(f"Subject: {self.email.subject}", classes="detail-subject"),
                ScrollableContainer(
                    Static("", id="email_body", classes="detail-body"),
                ),
                Horizontal(
                    Button("Reply", variant="primary", id="reply_email"),
                    Button("Delete", variant="error", id="delete_email"),
                    Button("Close", variant="default", id="close_detail"),
                ),
                classes="detail-container"
            )
        )
    
    def on_mount(self):
        """Load email body."""
        @work
        async def load_body():
            cfg = self.app_ref.config.config
            client = IMAPClient(
                cfg.imap_server, cfg.imap_port, cfg.imap_use_ssl,
                cfg.username, cfg.password
            )
            
            if client.connect():
                body = client.fetch_email_body(self.email.uid, self.folder)
                client.disconnect()
                
                if body:
                    self.body = body
                    self.query_one("#email_body", Static).update(body)
        
        load_body()
    
    def on_button_pressed(self, event: Button.Pressed):
        """Handle button presses."""
        if event.button.id == "reply_email":
            self.app_ref.push_screen(ComposeScreen(self.app_ref, self.reply_to))
        elif event.button.id == "delete_email":
            self._delete_email()
        elif event.button.id == "close_detail":
            self.app_ref.pop_screen()
    
    @property
    def reply_to(self) -> EmailMessage:
        """Get the email to reply to."""
        return self.email
    
    def _delete_email(self):
        """Delete the email."""
        self.app_ref.notify("Email moved to Trash!", severity="information")
        self.app_ref.pop_screen()


class SearchScreen(Screen):
    """Search screen."""
    
    def __init__(self, app_ref):
        super().__init__()
        self.app_ref = app_ref
        self.results: List[EmailMessage] = []
    
    def compose(self) -> ComposeResult:
        yield Container(
            Vertical(
                Static("Search Emails", classes="search-title"),
                Horizontal(
                    Input(placeholder="Search query...", id="search_query", classes="search-input"),
                    Button("Search", variant="primary", id="do_search"),
                    Button("Cancel", variant="default", id="cancel_search"),
                ),
                ListView(id="search_results", classes="search-results"),
                classes="search-container"
            )
        )
    
    def on_button_pressed(self, event: Button.Pressed):
        """Handle button presses."""
        if event.button.id == "do_search":
            self._do_search()
        elif event.button.id == "cancel_search":
            self.app_ref.pop_screen()
    
    def _do_search(self):
        """Perform search."""
        query = self.query_one("#search_query", Input).value.strip()
        
        if not query:
            self.app_ref.notify("Please enter a search query!", severity="error")
            return
        
        cfg = self.app_ref.config.config
        client = IMAPClient(
            cfg.imap_server, cfg.imap_port, cfg.imap_use_ssl,
            cfg.username, cfg.password
        )
        
        if client.connect():
            # Search in inbox
            results = client.search_emails(query, "INBOX")
            client.disconnect()
            
            self.results = results
            list_view = self.query_one("#search_results", ListView)
            list_view.clear()
            
            for email in results:
                list_view.append(ListItem(
                    Static(f"{email.sender[:30]:<30} | {email.subject[:40]:<40} | {email.date[:20]}")
                ))
            
            if not results:
                self.app_ref.notify("No results found!", severity="information")
        else:
            self.app_ref.notify("Connection failed!", severity="error")
    
    def on_list_view_selected(self, event: ListView.Selected):
        """Handle selection."""
        if event.item and self.results:
            idx = event.list_view.index
            if 0 <= idx < len(self.results):
                email = self.results[idx]
                self.app_ref.push_screen(EmailDetailScreen(self.app_ref, email, "INBOX"))


class FolderListItem(ListItem):
    """Folder list item."""
    
    def __init__(self, name: str, count: int):
        super().__init__()
        self.name = name
        self.count = count
        self.add_static(f"{name} ({count})", classes="folder-item")


class TermailApp(App):
    """Termail - Terminal Email Client."""
    
    CSS = """
    Screen {
        background: $surface;
    }
    
    .container {
        height: 100%;
        width: 100%;
    }
    
    .sidebar {
        width: 25;
        height: 100%;
        background: $surface-darken-1;
        border-right: solid $primary;
    }
    
    .sidebar-title {
        width: 100%;
        text-align: center;
        text-style: bold;
        color: $accent;
        padding: 1;
    }
    
    .folder-list {
        height: 60%;
    }
    
    .folder-item {
        padding: 0 1;
    }
    
    .folder-item:hover {
        background: $primary-darken-1;
    }
    
    .main-content {
        width: 75;
        height: 100%;
    }
    
    .email-list {
        height: 50%;
    }
    
    .email-item {
        padding: 0 1;
    }
    
    .email-list-item {
        width: 100%;
    }
    
    .email-list-item:hover {
        background: $primary-darken-1;
    }
    
    .toolbar {
        height: 3;
        background: $surface-darken-1;
        dock: bottom;
    }
    
    .status-bar {
        height: 1;
        background: $surface-darken-2;
        dock: bottom;
    }
    
    .config-container {
        width: 60;
        height: auto;
        align: center middle;
        background: $surface;
        border: solid $accent;
    }
    
    .config-form {
        padding: 1;
    }
    
    .config-title {
        text-align: center;
        text-style: bold;
        color: $accent;
        padding: 1;
    }
    
    .config-input {
        width: 100%;
        margin: 0 0 1 0;
    }
    
    .compose-container {
        width: 80;
        height: 90;
        align: center middle;
        background: $surface;
        border: solid $accent;
    }
    
    .compose-form {
        padding: 1;
    }
    
    .compose-title {
        text-align: center;
        text-style: bold;
        color: $accent;
        padding: 1;
    }
    
    .compose-input {
        width: 100%;
        margin: 0 0 1 0;
    }
    
    .compose-body {
        height: 60;
        width: 100%;
        margin: 0 0 1 0;
    }
    
    .detail-container {
        width: 100%;
        height: 100%;
    }
    
    .detail-header {
        padding: 0 1;
        color: $text;
    }
    
    .detail-subject {
        padding: 0 1;
        text-style: bold;
        color: $accent;
    }
    
    .detail-body {
        padding: 1;
        height: 100%;
    }
    
    .search-container {
        width: 80;
        height: 90;
        align: center middle;
        background: $surface;
        border: solid $accent;
    }
    
    .search-title {
        text-align: center;
        text-style: bold;
        color: $accent;
        padding: 1;
    }
    
    .search-input {
        width: 60;
        margin: 0 1 1 0;
    }
    
    .search-results {
        height: 60;
    }
    
    .toolbar-button {
        margin: 0 1;
    }
    """
    
    BINDINGS = [
        Binding("n", "new_email", "Compose"),
        Binding("r", "reply", "Reply"),
        Binding("d", "delete", "Delete"),
        Binding("f", "search", "Search"),
        Binding("c", "config", "Config"),
        Binding("q", "quit", "Quit"),
        Binding("escape", "pop_screen", "Back"),
    ]
    
    def __init__(self):
        super().__init__()
        self.config = Config(os.path.dirname(os.path.abspath(__file__)))
        self.current_folder = "INBOX"
        self.emails: List[EmailMessage] = []
        self.folders: List[tuple] = []
        self.selected_email: Optional[EmailMessage] = None
    
    def compose(self) -> ComposeResult:
        yield Header()
        
        yield Container(
            Vertical(
                Static("Termail", classes="sidebar-title"),
                ListView(
                    FolderListItem("INBOX", 0),
                    FolderListItem("Sent", 0),
                    FolderListItem("Drafts", 0),
                    FolderListItem("Trash", 0),
                    classes="folder-list"
                ),
                id="folder_list_view"
            ),
            classes="sidebar",
            id="sidebar"
        ),
        
        Container(
            Vertical(
                Static("INBOX", id="folder_label"),
                ListView(id="email_list", classes="email-list"),
                Horizontal(
                    Button("Compose", variant="primary", id="btn_compose", classes="toolbar-button"),
                    Button("Reply", variant="default", id="btn_reply", classes="toolbar-button"),
                    Button("Delete", variant="error", id="btn_delete", classes="toolbar_button"),
                    Button("Search", variant="default", id="btn_search", classes="toolbar-button"),
                    Button("Config", variant="default", id="btn_config", classes="toolbar-button"),
                ),
                classes="toolbar"
            ),
            classes="main-content",
            id="main_content"
        ),
        
        Footer()
    
    def on_mount(self):
        """App mounted - connect and load emails."""
        self._load_config_and_connect()
    
    def _load_config_and_connect(self):
        """Load config and establish connection."""
        cfg = self.config.config
        
        if not cfg.username or not cfg.password:
            self.notify("Please configure your email account!", severity="warning")
            return
        
        @work
        async def load_emails():
            client = IMAPClient(
                cfg.imap_server, cfg.imap_port, cfg.imap_use_ssl,
                cfg.username, cfg.password
            )
            
            if client.connect():
                # Load folders
                folders = client.get_folders()
                self.folders = folders
                
                # Update folder list
                folder_list = self.query_one("#folder_list_view", ListView)
                folder_list.clear()
                
                for name, count in folders:
                    folder_list.append(FolderListItem(name, count))
                
                # Also add default folders if not present
                default_folders = ["Drafts", "Sent", "Trash"]
                for df in default_folders:
                    if not any(f[0] == df for f in folders):
                        folder_list.append(FolderListItem(df, 0))
                
                # Load inbox emails
                emails = client.fetch_emails("INBOX", 50)
                self.emails = emails
                
                # Update email list
                email_list = self.query_one("#email_list", ListView)
                email_list.clear()
                
                for email in emails:
                    email_list.append(ListItem(
                        Static(
                            f"{email.sender[:25]:<25} | {email.subject[:35]:<35} | {email.date[:15]}",
                            classes="email-list-item"
                        )
                    ))
                
                client.disconnect()
                
                self.notify("Emails loaded!", severity="information")
            else:
                self.notify("Failed to connect! Check configuration.", severity="error")
        
        load_emails()
    
    def on_list_view_selected(self, event: ListView.Selected):
        """Handle folder or email selection."""
        list_view = event.list_view
        
        # Check which list was selected
        if list_view.id == "folder_list_view":
            # Folder selected
            if self.folders:
                idx = list_view.index
                if 0 <= idx < len(self.folders):
                    folder_name = self.folders[idx][0]
                    self._load_folder(folder_name)
        elif list_view.id == "email_list":
            # Email selected
            idx = list_view.index
            if 0 <= idx < len(self.emails):
                email = self.emails[idx]
                self.selected_email = email
                self.push_screen(EmailDetailScreen(self, email, self.current_folder))
    
    def _load_folder(self, folder_name: str):
        """Load emails from a folder."""
        self.current_folder = folder_name
        self.query_one("#folder_label", Static).update(folder_name)
        
        cfg = self.config.config
        client = IMAPClient(
            cfg.imap_server, cfg.imap_port, cfg.imap_use_ssl,
            cfg.username, cfg.password
        )
        
        if client.connect():
            emails = client.fetch_emails(folder_name, 50)
            self.emails = emails
            
            email_list = self.query_one("#email_list", ListView)
            email_list.clear()
            
            for email in emails:
                email_list.append(ListItem(
                    Static(
                        f"{email.sender[:25]:<25} | {email.subject[:35]:<35} | {email.date[:15]}",
                        classes="email-list-item"
                    )
                ))
            
            client.disconnect()
        
        self.notify(f"Loaded {folder_name}!")
    
    def on_button_pressed(self, event: Button.Pressed):
        """Handle toolbar button presses."""
        btn_id = event.button.id
        
        if btn_id == "btn_compose" or btn_id == "btn_compose":
            self.push_screen(ComposeScreen(self))
        elif btn_id == "btn_reply":
            if self.selected_email:
                self.push_screen(ComposeScreen(self, self.selected_email))
        elif btn_id == "btn_delete":
            self._delete_email()
        elif btn_id == "btn_search":
            self.push_screen(SearchScreen(self))
        elif btn_id == "btn_config":
            self.push_screen(ConfigScreen(self))
    
    def _delete_email(self):
        """Delete selected email."""
        if not self.selected_email:
            self.notify("No email selected!", severity="warning")
            return
        
        cfg = self.config.config
        client = IMAPClient(
            cfg.imap_server, cfg.imap_port, cfg.imap_use_ssl,
            cfg.username, cfg.password
        )
        
        if client.connect():
            if client.delete_email(self.selected_email.uid, self.current_folder):
                self.notify("Email deleted!", severity="information")
                # Reload folder
                self._load_folder(self.current_folder)
            else:
                self.notify("Failed to delete!", severity="error")
            client.disconnect()
    
    def action_new_email(self):
        """Compose new email."""
        self.push_screen(ComposeScreen(self))
    
    def action_reply(self):
        """Reply to selected email."""
        if self.selected_email:
            self.push_screen(ComposeScreen(self, self.selected_email))
    
    def action_delete(self):
        """Delete selected email."""
        self._delete_email()
    
    def action_search(self):
        """Search emails."""
        self.push_screen(SearchScreen(self))
    
    def action_config(self):
        """Open configuration."""
        self.push_screen(ConfigScreen(self))
    
    def action_quit(self):
        """Quit the application."""
        self.exit()


def main():
    """Main entry point."""
    app = TermailApp()
    app.run()


if __name__ == "__main__":
    main()