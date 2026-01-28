"""Balances screen for updating assets and liabilities."""

from textual.app import ComposeResult
from textual.screen import Screen
from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical, ScrollableContainer
from textual.widgets import Static, Footer, Button, Input, Label, Select

from app.cli.widgets.header import RadiantHeader
from app.cli.widgets.currency_input import CurrencyInput
from app.models import Asset, Liability, AssetType, LiquidityStatus


class BalancesScreen(Screen):
    """Screen for updating current balances."""

    BINDINGS = [
        Binding("escape", "go_back", "Back"),
        Binding("enter", "next_field", "Next"),
        Binding("ctrl+s", "save", "Save"),
    ]

    def __init__(self):
        super().__init__()
        self.assets = []
        self.liabilities = []
        self.current_index = 0

    def compose(self) -> ComposeResult:
        yield Container(
            RadiantHeader(show_tagline=False),
            Static("Step 1 of 3: Update Balances", classes="step-indicator"),

            ScrollableContainer(
                Static("Update your current account balances.", classes="question-label"),
                Vertical(id="balances-form"),
                id="form-container"
            ),

            Horizontal(
                Button("Cancel", id="btn-cancel"),
                Button("Next: Expenses", variant="primary", id="btn-next"),
                classes="nav-buttons"
            ),
            id="balances-container",
            classes="questionnaire-container"
        )
        yield Footer()

    async def on_mount(self) -> None:
        """Load existing data."""
        db = self.app.db
        self.assets = db.get_assets()
        self.liabilities = db.get_liabilities()
        await self._build_form()

    async def _build_form(self) -> None:
        """Build the form with current balances."""
        form = self.query_one("#balances-form", Vertical)
        form.remove_children()

        # Assets section
        if self.assets:
            form.mount(Static("[bold]Assets[/]", classes="section-header"))
            for asset in self.assets:
                form.mount(
                    Vertical(
                        Label(f"{asset.name} ({asset.type.value})"),
                        CurrencyInput(
                            value=f"{asset.value:,.2f}",
                            id=f"asset-{asset.id}"
                        ),
                        Static(f"[dim]Current: ${asset.value:,.2f}[/]", classes="input-hint"),
                        classes="question-group"
                    )
                )

        # Liabilities section
        if self.liabilities:
            form.mount(Static("[bold]Liabilities[/]", classes="section-header"))
            for liability in self.liabilities:
                form.mount(
                    Vertical(
                        Label(f"{liability.name}"),
                        CurrencyInput(
                            value=f"{liability.balance:,.2f}",
                            id=f"liability-{liability.id}"
                        ),
                        Static(
                            f"[dim]Current: ${liability.balance:,.2f} @ {liability.interest_rate*100:.1f}%[/]",
                            classes="input-hint"
                        ),
                        classes="question-group"
                    )
                )

        # If no data, show message
        if not self.assets and not self.liabilities:
            form.mount(
                Static(
                    "No accounts found. Add assets and liabilities via the web app or manage.py.",
                    classes="empty-state"
                )
            )

    def _save_balances(self) -> bool:
        """Save updated balances to database."""
        db = self.app.db

        try:
            # Update assets
            for asset in self.assets:
                input_widget = self.query_one(f"#asset-{asset.id}", CurrencyInput)
                asset.value = input_widget.get_value()
                db.save_asset(asset)

            # Update liabilities
            for liability in self.liabilities:
                input_widget = self.query_one(f"#liability-{liability.id}", CurrencyInput)
                liability.balance = input_widget.get_value()
                db.save_liability(liability)

            return True
        except Exception as e:
            self.notify(f"Error saving: {e}", severity="error")
            return False

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "btn-cancel":
            self.app.pop_screen()
        elif event.button.id == "btn-next":
            if self._save_balances():
                self.notify("Balances saved!")
                from app.cli.screens.expenses import ExpensesScreen
                self.app.push_screen(ExpensesScreen())

    def action_go_back(self) -> None:
        """Go back to previous screen."""
        self.app.pop_screen()

    def action_save(self) -> None:
        """Save and continue."""
        if self._save_balances():
            self.notify("Balances saved!")
            from app.cli.screens.expenses import ExpensesScreen
            self.app.push_screen(ExpensesScreen())
