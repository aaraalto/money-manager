"""Home dashboard screen."""

from textual.app import ComposeResult
from textual.screen import Screen
from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical, ScrollableContainer
from textual.widgets import Static, Footer, Button, Label

from app.cli.widgets.header import RadiantHeader
from app.cli.widgets.summary_card import SummaryCard


class HomeScreen(Screen):
    """Home dashboard showing financial overview."""

    BINDINGS = [
        Binding("n", "new_checkin", "New Check-In"),
        Binding("t", "view_tasks", "Tasks"),
        Binding("e", "export", "Export"),
        Binding("r", "refresh", "Refresh"),
    ]

    def compose(self) -> ComposeResult:
        yield RadiantHeader()

        with ScrollableContainer(id="home-content"):
            # Summary Cards Row
            with Horizontal(classes="card-row"):
                yield SummaryCard(
                    title="Net Worth",
                    value="Loading...",
                    subtitle="",
                    id="net-worth-card"
                )
                yield SummaryCard(
                    title="Total Assets",
                    value="Loading...",
                    subtitle="",
                    id="assets-card"
                )
                yield SummaryCard(
                    title="Total Debt",
                    value="Loading...",
                    subtitle="",
                    value_type="negative",
                    id="debt-card"
                )

            # Tasks and Expenses Row
            with Horizontal(classes="card-row"):
                yield SummaryCard(
                    title="Upcoming Tasks",
                    value="Loading...",
                    subtitle="Due this week",
                    id="tasks-card"
                )
                yield SummaryCard(
                    title="Upcoming Expenses",
                    value="Loading...",
                    subtitle="Next 30 days",
                    id="expenses-card"
                )

            # Upcoming Tasks Section
            yield Static("Upcoming Tasks", classes="section-header")
            yield Vertical(id="tasks-list", classes="task-list")

            # Upcoming Expenses Section
            yield Static("Upcoming Expenses", classes="section-header")
            yield Vertical(id="expenses-list", classes="expense-list")

            # Quick Actions
            yield Static("Quick Actions", classes="section-header")
            with Horizontal(classes="card-row"):
                yield Button("New Check-In", variant="primary", id="btn-checkin")
                yield Button("Add Task", id="btn-add-task")
                yield Button("Add Expense", id="btn-add-expense")

        yield Footer()

    async def on_mount(self) -> None:
        """Load data when screen mounts."""
        await self._refresh_data()

    async def _refresh_data(self) -> None:
        """Refresh all dashboard data."""
        db = self.app.db

        # Load financial data
        assets = db.get_assets()
        liabilities = db.get_liabilities()
        tasks = db.get_upcoming_tasks(days=7)
        expenses = db.get_upcoming_expenses(days=30)

        # Calculate totals
        total_assets = sum(a.value for a in assets)
        total_debt = sum(l.balance for l in liabilities)
        net_worth = total_assets - total_debt

        # Update cards
        net_worth_card = self.query_one("#net-worth-card", SummaryCard)
        net_worth_card.card_value = f"${net_worth:,.2f}"
        net_worth_card.value_type = "positive" if net_worth >= 0 else "negative"
        net_worth_card.refresh()

        assets_card = self.query_one("#assets-card", SummaryCard)
        assets_card.card_value = f"${total_assets:,.2f}"
        assets_card.card_subtitle = f"{len(assets)} accounts"
        assets_card.refresh()

        debt_card = self.query_one("#debt-card", SummaryCard)
        debt_card.card_value = f"${total_debt:,.2f}"
        debt_card.card_subtitle = f"{len(liabilities)} accounts"
        debt_card.refresh()

        tasks_card = self.query_one("#tasks-card", SummaryCard)
        tasks_card.card_value = str(len(tasks))
        tasks_card.refresh()

        expenses_card = self.query_one("#expenses-card", SummaryCard)
        total_upcoming = sum(e.amount for e in expenses)
        expenses_card.card_value = f"${total_upcoming:,.2f}"
        expenses_card.refresh()

        # Update tasks list
        tasks_list = self.query_one("#tasks-list", Vertical)
        tasks_list.remove_children()

        if tasks:
            for task in tasks[:5]:  # Show top 5
                due_str = task.due_date.strftime("%b %d") if task.due_date else "No date"
                priority_color = {
                    "high": "red",
                    "medium": "yellow",
                    "low": "dim"
                }.get(task.priority.value, "white")

                tasks_list.mount(
                    Static(
                        f"[{priority_color}]●[/] {task.title}  [dim]{due_str}[/]",
                        classes="list-item"
                    )
                )
        else:
            tasks_list.mount(
                Static("No upcoming tasks", classes="empty-state")
            )

        # Update expenses list
        expenses_list = self.query_one("#expenses-list", Vertical)
        expenses_list.remove_children()

        if expenses:
            for expense in expenses[:5]:  # Show top 5
                due_str = expense.due_date.strftime("%b %d")
                expenses_list.mount(
                    Static(
                        f"{expense.name}  [#00d26a]${expense.amount:,.2f}[/]  [dim]{due_str}[/]",
                        classes="list-item"
                    )
                )
        else:
            expenses_list.mount(
                Static("No upcoming expenses", classes="empty-state")
            )

    async def action_refresh(self) -> None:
        """Refresh dashboard data."""
        await self._refresh_data()
        self.notify("Data refreshed")

    async def action_new_checkin(self) -> None:
        """Start a new check-in."""
        from app.cli.screens.balances import BalancesScreen
        await self.app.push_screen(BalancesScreen())

    async def action_view_tasks(self) -> None:
        """View tasks screen."""
        from app.cli.screens.tasks import TasksScreen
        await self.app.push_screen(TasksScreen())

    async def action_export(self) -> None:
        """Show export screen."""
        from app.cli.screens.export import ExportScreen
        await self.app.push_screen(ExportScreen())

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "btn-checkin":
            self.action_new_checkin()
        elif event.button.id == "btn-add-task":
            self.action_view_tasks()
        elif event.button.id == "btn-add-expense":
            from app.cli.screens.expenses import ExpensesScreen
            self.app.push_screen(ExpensesScreen())
