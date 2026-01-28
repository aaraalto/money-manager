"""
Radiant TUI Application using Textual.
"""
import getpass
from pathlib import Path
from typing import Optional

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Vertical
from textual.widgets import Static, Footer, Input, Button, Label
from textual.screen import Screen

from app.data.database import SecureDatabase


class PasswordScreen(Screen):
    """Screen for entering database password."""

    BINDINGS = [
        Binding("escape", "quit", "Quit"),
    ]

    def __init__(self, first_time: bool = False):
        super().__init__()
        self.first_time = first_time
        self.password: Optional[str] = None
        self.confirm_password: Optional[str] = None

    def compose(self) -> ComposeResult:
        yield Container(
            Static(self._get_banner(), id="banner"),
            Static(
                "Welcome! Set a password to encrypt your data."
                if self.first_time else
                "Enter your password to unlock.",
                id="password-prompt"
            ),
            Input(placeholder="Password", password=True, id="password-input"),
            Input(
                placeholder="Confirm password",
                password=True,
                id="confirm-input",
                classes="hidden" if not self.first_time else ""
            ),
            Button("Unlock", variant="primary", id="unlock-btn"),
            Static("", id="error-message"),
            id="password-container"
        )
        yield Footer()

    def _get_banner(self) -> str:
        return """
[#00d26a]  ██████╗  █████╗ ██████╗ ██╗ █████╗ ███╗   ██╗████████╗[/]
[#00b85c]  ██╔══██╗██╔══██╗██╔══██╗██║██╔══██╗████╗  ██║╚══██╔══╝[/]
[#00a050]  ██████╔╝███████║██║  ██║██║███████║██╔██╗ ██║   ██║   [/]
[#008744]  ██╔══██╗██╔══██║██║  ██║██║██╔══██║██║╚██╗██║   ██║   [/]
[#006e38]  ██║  ██║██║  ██║██████╔╝██║██║  ██║██║ ╚████║   ██║   [/]
[#00552c]  ╚═╝  ╚═╝╚═╝  ╚═╝╚═════╝ ╚═╝╚═╝  ╚═╝╚═╝  ╚═══╝   ╚═╝   [/]
"""

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "unlock-btn":
            self._handle_unlock()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id == "password-input" and not self.first_time:
            self._handle_unlock()
        elif event.input.id == "password-input" and self.first_time:
            self.query_one("#confirm-input", Input).focus()
        elif event.input.id == "confirm-input":
            self._handle_unlock()

    def _handle_unlock(self) -> None:
        password_input = self.query_one("#password-input", Input)
        error_label = self.query_one("#error-message", Static)

        password = password_input.value

        if len(password) < 8:
            error_label.update("[red]Password must be at least 8 characters[/]")
            return

        if self.first_time:
            confirm_input = self.query_one("#confirm-input", Input)
            if password != confirm_input.value:
                error_label.update("[red]Passwords do not match[/]")
                return

        self.password = password
        self.app.post_message(PasswordSubmitted(password))


class PasswordSubmitted:
    """Message sent when password is submitted."""

    def __init__(self, password: str):
        self.password = password


class RadiantApp(App):
    """Main Textual application for Radiant Money Manager."""

    CSS_PATH = "styles/radiant.tcss"
    TITLE = "Radiant Money Manager"

    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("h", "go_home", "Home"),
        Binding("n", "new_checkin", "Check-In"),
        Binding("t", "view_tasks", "Tasks"),
        Binding("e", "export", "Export"),
        Binding("?", "help", "Help"),
    ]

    def __init__(self, data_dir: Path, encrypted: bool = True):
        super().__init__()
        self.data_dir = data_dir
        self.encrypted = encrypted
        self.db: Optional[SecureDatabase] = None

    def on_mount(self) -> None:
        """Called when app is mounted."""
        self.db = SecureDatabase(self.data_dir, encrypted=self.encrypted)

        if self.encrypted:
            first_time = not self.db.db_path.exists()
            self.push_screen(PasswordScreen(first_time=first_time))
        else:
            self._connect_and_show_home(None)

    def on_password_submitted(self, message: PasswordSubmitted) -> None:
        """Handle password submission."""
        self._connect_and_show_home(message.password, from_password_screen=True)

    def _connect_and_show_home(self, password: Optional[str], from_password_screen: bool = False) -> None:
        """Connect to database and show home screen."""
        try:
            self.db.connect(password)
        except Exception as e:
            self.notify(f"Error: {e}", severity="error")
            return

        # Only pop if we came from password screen
        if from_password_screen:
            self.pop_screen()

        from app.cli.screens.home import HomeScreen
        self.push_screen(HomeScreen())

    def action_go_home(self) -> None:
        """Navigate to home screen."""
        if self.db and self.db.is_connected:
            while len(self.screen_stack) > 1:
                self.pop_screen()
            from app.cli.screens.home import HomeScreen
            self.push_screen(HomeScreen())

    def action_new_checkin(self) -> None:
        """Start a new check-in."""
        if self.db and self.db.is_connected:
            from app.cli.screens.balances import BalancesScreen
            self.push_screen(BalancesScreen())

    def action_view_tasks(self) -> None:
        """View financial tasks."""
        if self.db and self.db.is_connected:
            from app.cli.screens.tasks import TasksScreen
            self.push_screen(TasksScreen())

    def action_export(self) -> None:
        """Show export screen."""
        if self.db and self.db.is_connected:
            from app.cli.screens.export import ExportScreen
            self.push_screen(ExportScreen())

    def action_help(self) -> None:
        """Show help."""
        self.notify(
            "h=Home  n=Check-In  t=Tasks  e=Export  q=Quit",
            title="Keyboard Shortcuts"
        )

    def on_unmount(self) -> None:
        """Clean up when app closes."""
        if self.db:
            self.db.close()
