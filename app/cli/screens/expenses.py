"""Expenses screen for managing upcoming expenses."""

from datetime import date, timedelta
from textual.app import ComposeResult
from textual.screen import Screen
from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical, ScrollableContainer
from textual.widgets import Static, Footer, Button, Input, Label, Select

from app.cli.widgets.header import RadiantHeader
from app.cli.widgets.currency_input import CurrencyInput
from app.models import UpcomingExpense, RecurrenceType


class ExpensesScreen(Screen):
    """Screen for managing upcoming expenses."""

    BINDINGS = [
        Binding("escape", "go_back", "Back"),
        Binding("ctrl+s", "save_and_next", "Save & Next"),
        Binding("ctrl+n", "add_expense", "Add New"),
    ]

    def __init__(self):
        super().__init__()
        self.expenses = []

    def compose(self) -> ComposeResult:
        yield Container(
            RadiantHeader(show_tagline=False),
            Static("Step 2 of 3: Upcoming Expenses", classes="step-indicator"),

            ScrollableContainer(
                Static("Track your upcoming bills and expenses.", classes="question-label"),

                # Existing expenses
                Static("[bold]Current Expenses[/]", classes="section-header"),
                Vertical(id="expenses-list"),

                # Add new expense form
                Static("[bold]Add New Expense[/]", classes="section-header"),
                Vertical(
                    Horizontal(
                        Vertical(
                            Label("Name"),
                            Input(placeholder="e.g., Rent", id="new-expense-name"),
                            classes="question-group"
                        ),
                        Vertical(
                            Label("Amount"),
                            CurrencyInput(placeholder="0.00", id="new-expense-amount"),
                            classes="question-group"
                        ),
                    ),
                    Horizontal(
                        Vertical(
                            Label("Due Date (YYYY-MM-DD)"),
                            Input(
                                placeholder=date.today().isoformat(),
                                id="new-expense-date"
                            ),
                            classes="question-group"
                        ),
                        Vertical(
                            Label("Category"),
                            Input(placeholder="Bills", id="new-expense-category"),
                            classes="question-group"
                        ),
                    ),
                    Horizontal(
                        Vertical(
                            Label("Recurrence"),
                            Select(
                                options=[
                                    ("None", "none"),
                                    ("Weekly", "weekly"),
                                    ("Bi-weekly", "biweekly"),
                                    ("Monthly", "monthly"),
                                    ("Quarterly", "quarterly"),
                                    ("Yearly", "yearly"),
                                ],
                                id="new-expense-recurrence",
                                value="none"
                            ),
                            classes="question-group"
                        ),
                    ),
                    Button("Add Expense", id="btn-add-expense"),
                    id="new-expense-form"
                ),
                id="form-container"
            ),

            Horizontal(
                Button("Back", id="btn-back"),
                Button("Next: Tasks", variant="primary", id="btn-next"),
                classes="nav-buttons"
            ),
            id="expenses-container",
            classes="questionnaire-container"
        )
        yield Footer()

    async def on_mount(self) -> None:
        """Load existing expenses."""
        await self._refresh_list()

    async def _refresh_list(self) -> None:
        """Refresh the expenses list."""
        db = self.app.db
        self.expenses = db.get_all_expenses()

        expenses_list = self.query_one("#expenses-list", Vertical)
        expenses_list.remove_children()

        if self.expenses:
            for expense in self.expenses:
                due_str = expense.due_date.strftime("%b %d, %Y")
                recur_str = f" ({expense.recurrence.value})" if expense.recurrence != RecurrenceType.NONE else ""

                expenses_list.mount(
                    Horizontal(
                        Static(f"{expense.name}{recur_str}", classes="list-item-title"),
                        Static(f"${expense.amount:,.2f}", classes="list-item-amount"),
                        Static(due_str, classes="list-item-date"),
                        Button("X", id=f"delete-{expense.id}", classes="btn-delete"),
                        classes="list-item"
                    )
                )
        else:
            expenses_list.mount(
                Static("No upcoming expenses. Add one below.", classes="empty-state")
            )

    def _add_expense(self) -> None:
        """Add a new expense from form data."""
        name_input = self.query_one("#new-expense-name", Input)
        amount_input = self.query_one("#new-expense-amount", CurrencyInput)
        date_input = self.query_one("#new-expense-date", Input)
        category_input = self.query_one("#new-expense-category", Input)
        recurrence_select = self.query_one("#new-expense-recurrence", Select)

        name = name_input.value.strip()
        if not name:
            self.notify("Please enter a name", severity="warning")
            return

        amount = amount_input.get_value()
        if amount <= 0:
            self.notify("Please enter a valid amount", severity="warning")
            return

        # Parse date
        date_str = date_input.value.strip() or date.today().isoformat()
        try:
            due_date = date.fromisoformat(date_str)
        except ValueError:
            self.notify("Invalid date format. Use YYYY-MM-DD", severity="warning")
            return

        category = category_input.value.strip() or "Bills"
        recurrence = RecurrenceType(recurrence_select.value)

        # Create and save expense
        expense = UpcomingExpense(
            name=name,
            amount=amount,
            due_date=due_date,
            category=category,
            recurrence=recurrence
        )

        db = self.app.db
        db.save_expense(expense)

        # Clear form
        name_input.value = ""
        amount_input.value = ""
        date_input.value = ""
        category_input.value = ""
        recurrence_select.value = "none"

        self.notify(f"Added expense: {name}")
        self._refresh_list()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        button_id = event.button.id

        if button_id == "btn-back":
            self.app.pop_screen()
        elif button_id == "btn-next":
            from app.cli.screens.tasks import TasksScreen
            self.app.switch_screen(TasksScreen())
        elif button_id == "btn-add-expense":
            self._add_expense()
        elif button_id and button_id.startswith("delete-"):
            expense_id = button_id.replace("delete-", "")
            from uuid import UUID
            db = self.app.db
            db.delete_expense(UUID(expense_id))
            self.notify("Expense deleted")
            self._refresh_list()

    def action_go_back(self) -> None:
        """Go back to previous screen."""
        self.app.pop_screen()

    def action_save_and_next(self) -> None:
        """Save and go to next screen."""
        from app.cli.screens.tasks import TasksScreen
        self.app.switch_screen(TasksScreen())

    def action_add_expense(self) -> None:
        """Focus the add expense form."""
        self.query_one("#new-expense-name", Input).focus()
