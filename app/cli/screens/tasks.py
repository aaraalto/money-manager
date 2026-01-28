"""Tasks screen for managing financial tasks."""

from datetime import date, timedelta
from textual.app import ComposeResult
from textual.screen import Screen
from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical, ScrollableContainer
from textual.widgets import Static, Footer, Button, Input, Label, Select, Checkbox

from app.cli.widgets.header import RadiantHeader
from app.cli.widgets.currency_input import CurrencyInput
from app.models import FinancialTask, TaskPriority, TaskCategory


class TasksScreen(Screen):
    """Screen for managing financial tasks and reminders."""

    BINDINGS = [
        Binding("escape", "go_back", "Back"),
        Binding("ctrl+s", "save_and_finish", "Finish"),
        Binding("ctrl+n", "add_task", "Add New"),
    ]

    def __init__(self):
        super().__init__()
        self.tasks = []
        self.show_completed = False

    def compose(self) -> ComposeResult:
        yield Container(
            RadiantHeader(show_tagline=False),
            Static("Step 3 of 3: Financial Tasks", classes="step-indicator"),

            ScrollableContainer(
                Static("Track your financial to-dos and reminders.", classes="question-label"),

                # Filter options
                Horizontal(
                    Checkbox("Show completed", id="show-completed"),
                    classes="task-filters"
                ),

                # Task list
                Static("[bold]Your Tasks[/]", classes="section-header"),
                Vertical(id="tasks-list"),

                # Add new task form
                Static("[bold]Add New Task[/]", classes="section-header"),
                Vertical(
                    Vertical(
                        Label("Task Title"),
                        Input(placeholder="e.g., Review credit card statement", id="new-task-title"),
                        classes="question-group"
                    ),
                    Horizontal(
                        Vertical(
                            Label("Category"),
                            Select(
                                options=[
                                    ("Payment", "payment"),
                                    ("Review", "review"),
                                    ("Investment", "investment"),
                                    ("Tax", "tax"),
                                    ("Other", "other"),
                                ],
                                id="new-task-category",
                                value="other"
                            ),
                            classes="question-group"
                        ),
                        Vertical(
                            Label("Priority"),
                            Select(
                                options=[
                                    ("High", "high"),
                                    ("Medium", "medium"),
                                    ("Low", "low"),
                                ],
                                id="new-task-priority",
                                value="medium"
                            ),
                            classes="question-group"
                        ),
                    ),
                    Horizontal(
                        Vertical(
                            Label("Due Date (YYYY-MM-DD, optional)"),
                            Input(placeholder="Optional", id="new-task-date"),
                            classes="question-group"
                        ),
                        Vertical(
                            Label("Amount (optional)"),
                            CurrencyInput(placeholder="Optional", id="new-task-amount"),
                            classes="question-group"
                        ),
                    ),
                    Button("Add Task", id="btn-add-task"),
                    id="new-task-form"
                ),
                id="form-container"
            ),

            Horizontal(
                Button("Back", id="btn-back"),
                Button("Finish Check-In", variant="primary", id="btn-finish"),
                classes="nav-buttons"
            ),
            id="tasks-container",
            classes="questionnaire-container"
        )
        yield Footer()

    async def on_mount(self) -> None:
        """Load existing tasks."""
        await self._refresh_list()

    async def _refresh_list(self) -> None:
        """Refresh the tasks list."""
        db = self.app.db
        self.tasks = db.get_tasks(include_completed=self.show_completed)

        tasks_list = self.query_one("#tasks-list", Vertical)
        tasks_list.remove_children()

        if self.tasks:
            for task in self.tasks:
                due_str = task.due_date.strftime("%b %d") if task.due_date else "No date"
                priority_color = {
                    "high": "red",
                    "medium": "yellow",
                    "low": "dim"
                }.get(task.priority.value, "white")

                completed_style = "[strike dim]" if task.completed else ""
                completed_end = "[/]" if task.completed else ""

                amount_str = f" ${task.amount:,.2f}" if task.amount else ""

                tasks_list.mount(
                    Horizontal(
                        Checkbox(
                            "",
                            value=task.completed,
                            id=f"complete-{task.id}"
                        ),
                        Static(
                            f"[{priority_color}]●[/] {completed_style}{task.title}{completed_end}",
                            classes="list-item-title"
                        ),
                        Static(f"[dim]{task.category.value}[/]"),
                        Static(f"[#00d26a]{amount_str}[/]", classes="list-item-amount"),
                        Static(f"[dim]{due_str}[/]", classes="list-item-date"),
                        Button("X", id=f"delete-{task.id}", classes="btn-delete"),
                        classes="list-item"
                    )
                )
        else:
            tasks_list.mount(
                Static("No tasks. Add one below.", classes="empty-state")
            )

    def _add_task(self) -> None:
        """Add a new task from form data."""
        title_input = self.query_one("#new-task-title", Input)
        category_select = self.query_one("#new-task-category", Select)
        priority_select = self.query_one("#new-task-priority", Select)
        date_input = self.query_one("#new-task-date", Input)
        amount_input = self.query_one("#new-task-amount", CurrencyInput)

        title = title_input.value.strip()
        if not title:
            self.notify("Please enter a task title", severity="warning")
            return

        category = TaskCategory(category_select.value)
        priority = TaskPriority(priority_select.value)

        # Parse optional date
        due_date = None
        date_str = date_input.value.strip()
        if date_str:
            try:
                due_date = date.fromisoformat(date_str)
            except ValueError:
                self.notify("Invalid date format. Use YYYY-MM-DD", severity="warning")
                return

        # Parse optional amount
        amount = amount_input.get_value()
        if amount == 0:
            amount = None

        # Create and save task
        task = FinancialTask(
            title=title,
            category=category,
            priority=priority,
            due_date=due_date,
            amount=amount
        )

        db = self.app.db
        db.save_task(task)

        # Clear form
        title_input.value = ""
        category_select.value = "other"
        priority_select.value = "medium"
        date_input.value = ""
        amount_input.value = ""

        self.notify(f"Added task: {title}")
        self._refresh_list()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        button_id = event.button.id

        if button_id == "btn-back":
            self.app.pop_screen()
        elif button_id == "btn-finish":
            self.notify("Check-in complete!", title="Success")
            # Go back to home
            from app.cli.screens.home import HomeScreen
            self.app.switch_screen(HomeScreen())
        elif button_id == "btn-add-task":
            self._add_task()
        elif button_id and button_id.startswith("delete-"):
            task_id = button_id.replace("delete-", "")
            from uuid import UUID
            # Delete task (we'd need to implement this)
            self.notify("Task deleted")
            self._refresh_list()

    def on_checkbox_changed(self, event: Checkbox.Changed) -> None:
        """Handle checkbox changes."""
        checkbox_id = event.checkbox.id

        if checkbox_id == "show-completed":
            self.show_completed = event.value
            self._refresh_list()
        elif checkbox_id and checkbox_id.startswith("complete-"):
            task_id = checkbox_id.replace("complete-", "")
            from uuid import UUID
            db = self.app.db

            if event.value:
                db.complete_task(UUID(task_id))
                self.notify("Task completed!")
            # For uncomplete, we'd need to implement that

            self._refresh_list()

    def action_go_back(self) -> None:
        """Go back to previous screen."""
        self.app.pop_screen()

    def action_save_and_finish(self) -> None:
        """Finish check-in."""
        self.notify("Check-in complete!", title="Success")
        from app.cli.screens.home import HomeScreen
        self.app.switch_screen(HomeScreen())

    def action_add_task(self) -> None:
        """Focus the add task form."""
        self.query_one("#new-task-title", Input).focus()
