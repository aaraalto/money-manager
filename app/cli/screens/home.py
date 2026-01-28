"""Home dashboard screen - Compact layout."""

from textual.app import ComposeResult
from textual.screen import Screen
from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical, ScrollableContainer, Grid
from textual.widgets import Static, Footer, Button

from app.cli.widgets.header import RadiantHeader, MiniHeader


# Financial level definitions
LEVELS = {
    0: ("Crisis", "#f85149", "Expenses exceed income"),
    1: ("Debt War", "#d29922", "Fighting debt"),
    2: ("Stable", "#58a6ff", "Income covers expenses"),
    3: ("Growth", "#3fb950", "Building wealth"),
    4: ("FI", "#a371f7", "Financial Independence"),
    5: ("Fat FIRE", "#f778ba", "Abundant freedom"),
}


class HomeScreen(Screen):
    """Home dashboard showing financial overview."""

    BINDINGS = [
        Binding("n", "new_checkin", "Check-In"),
        Binding("t", "view_tasks", "Tasks"),
        Binding("e", "export", "Export"),
        Binding("r", "refresh", "Refresh"),
    ]

    def compose(self) -> ComposeResult:
        yield MiniHeader()

        with ScrollableContainer(id="home-content"):
            # Level indicator row
            yield LevelIndicator(id="level-indicator")

            # Main metrics row - 5 columns
            with Horizontal(classes="card-row"):
                yield MetricCard("Net Worth", "$0", id="net-worth")
                yield MetricCard("Assets", "$0", id="assets")
                yield MetricCard("Debt", "$0", id="debt")
                yield MetricCard("Tasks", "0", id="tasks-count")
                yield MetricCard("Due", "$0", id="expenses-due")

            # Two column layout for lists
            with Horizontal(classes="two-column"):
                with Vertical(classes="column"):
                    yield Static("TASKS", classes="section-header")
                    yield Vertical(id="tasks-list", classes="task-list")

                with Vertical(classes="column"):
                    yield Static("EXPENSES", classes="section-header")
                    yield Vertical(id="expenses-list", classes="expense-list")

            # Quick actions
            with Horizontal(classes="action-row"):
                yield Button("Check-In", variant="primary", id="btn-checkin")
                yield Button("+ Task", id="btn-add-task")
                yield Button("+ Expense", id="btn-add-expense")
                yield Button("Export", id="btn-export")

        yield Footer()

    async def on_mount(self) -> None:
        """Load data when screen mounts."""
        await self._refresh_data()

    async def _refresh_data(self) -> None:
        """Refresh all dashboard data."""
        db = self.app.db

        # Load data
        assets = db.get_assets()
        liabilities = db.get_liabilities()
        tasks = db.get_upcoming_tasks(days=7)
        expenses = db.get_upcoming_expenses(days=30)
        user_profile = db.get_user_profile()

        # Calculate totals
        total_assets = sum(a.value for a in assets)
        total_debt = sum(l.balance for l in liabilities)
        net_worth = total_assets - total_debt
        total_expenses = sum(e.amount for e in expenses)

        # Update level indicator
        level = user_profile.current_level if user_profile else 0
        try:
            level_indicator = self.query_one("#level-indicator", LevelIndicator)
            level_indicator.update_level(level)
        except Exception:
            pass

        # Update metrics
        self._update_metric("net-worth", f"${net_worth:,.0f}", "positive" if net_worth >= 0 else "negative")
        self._update_metric("assets", f"${total_assets:,.0f}", "neutral")
        self._update_metric("debt", f"${total_debt:,.0f}", "negative" if total_debt > 0 else "neutral")
        self._update_metric("tasks-count", str(len(tasks)), "warning" if tasks else "neutral")
        self._update_metric("expenses-due", f"${total_expenses:,.0f}", "neutral")

        # Update tasks list
        tasks_list = self.query_one("#tasks-list", Vertical)
        tasks_list.remove_children()

        if tasks:
            for task in tasks[:4]:
                due = task.due_date.strftime("%m/%d") if task.due_date else ""
                color = {"high": "red", "medium": "yellow", "low": "dim"}.get(task.priority.value, "")
                tasks_list.mount(Static(f"[{color}]●[/] {task.title[:25]} [dim]{due}[/]", classes="list-item"))
        else:
            tasks_list.mount(Static("[dim]No tasks[/]", classes="empty-state"))

        # Update expenses list
        expenses_list = self.query_one("#expenses-list", Vertical)
        expenses_list.remove_children()

        if expenses:
            for exp in expenses[:4]:
                due = exp.due_date.strftime("%m/%d")
                expenses_list.mount(Static(f"{exp.name[:20]} [#00d26a]${exp.amount:,.0f}[/] [dim]{due}[/]", classes="list-item"))
        else:
            expenses_list.mount(Static("[dim]No expenses[/]", classes="empty-state"))

    def _update_metric(self, metric_id: str, value: str, style: str = "neutral") -> None:
        """Update a metric card value."""
        try:
            card = self.query_one(f"#{metric_id}", MetricCard)
            card.update_value(value, style)
        except Exception:
            pass

    async def action_refresh(self) -> None:
        await self._refresh_data()
        self.notify("Refreshed")

    async def action_new_checkin(self) -> None:
        from app.cli.screens.balances import BalancesScreen
        await self.app.push_screen(BalancesScreen())

    async def action_view_tasks(self) -> None:
        from app.cli.screens.tasks import TasksScreen
        await self.app.push_screen(TasksScreen())

    async def action_export(self) -> None:
        from app.cli.screens.export import ExportScreen
        await self.app.push_screen(ExportScreen())

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-checkin":
            self.action_new_checkin()
        elif event.button.id == "btn-add-task":
            self.action_view_tasks()
        elif event.button.id == "btn-add-expense":
            from app.cli.screens.expenses import ExpensesScreen
            self.app.push_screen(ExpensesScreen())
        elif event.button.id == "btn-export":
            self.action_export()


class MetricCard(Static):
    """Compact metric display card."""

    DEFAULT_CSS = """
    MetricCard {
        width: 1fr;
        height: 4;
        padding: 0 1;
        margin: 0 1 0 0;
        background: #161b22;
        border: round #21262d;
        content-align: center middle;
    }
    MetricCard:last-child {
        margin-right: 0;
    }
    MetricCard:hover {
        border: round #006e38;
    }
    """

    def __init__(self, label: str, value: str, **kwargs):
        super().__init__(**kwargs)
        self.label = label
        self.value = value
        self.style_type = "neutral"

    def render(self) -> str:
        colors = {
            "positive": "#3fb950",
            "negative": "#f85149",
            "warning": "#d29922",
            "neutral": "#00d26a"
        }
        color = colors.get(self.style_type, "#00d26a")
        return f"[#8b949e]{self.label}[/]\n[{color} bold]{self.value}[/]"

    def update_value(self, value: str, style: str = "neutral") -> None:
        self.value = value
        self.style_type = style
        self.refresh()


class LevelIndicator(Static):
    """Financial level indicator with progress bar."""

    DEFAULT_CSS = """
    LevelIndicator {
        width: 100%;
        height: 3;
        padding: 0 1;
        margin-bottom: 1;
        background: #161b22;
        border: round #21262d;
    }
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.level = 0

    def render(self) -> str:
        name, color, desc = LEVELS.get(self.level, LEVELS[0])

        # Create level progress bar
        filled = "█" * (self.level + 1)
        empty = "░" * (5 - self.level)
        progress = f"[{color}]{filled}[/][#21262d]{empty}[/]"

        # Level badge
        badge = f"[{color} bold]LVL {self.level}[/]"

        return f"{badge} [{color}]{name}[/]  {progress}  [dim]{desc}[/]"

    def update_level(self, level: int) -> None:
        self.level = max(0, min(5, level))
        self.refresh()
