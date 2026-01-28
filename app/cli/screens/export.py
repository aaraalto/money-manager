"""Export screen for exporting financial data."""

import json
import csv
from pathlib import Path
from datetime import datetime
from textual.app import ComposeResult
from textual.screen import Screen
from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Static, Footer, Button, Input, Label, RadioSet, RadioButton

from app.cli.widgets.header import RadiantHeader


class ExportScreen(Screen):
    """Screen for exporting financial data."""

    BINDINGS = [
        Binding("escape", "go_back", "Back"),
    ]

    def compose(self) -> ComposeResult:
        yield Container(
            RadiantHeader(show_tagline=False),
            Static("Export Your Data", classes="section-header"),

            Vertical(
                Static(
                    "Export all your financial data to a file for backup or analysis.",
                    classes="question-label"
                ),

                Vertical(
                    Label("Export Format"),
                    RadioSet(
                        RadioButton("JSON (single file)", id="format-json", value=True),
                        RadioButton("CSV (multiple files)", id="format-csv"),
                        id="format-select"
                    ),
                    classes="question-group"
                ),

                Vertical(
                    Label("Output Directory"),
                    Input(
                        placeholder="./exports",
                        value="./exports",
                        id="output-dir"
                    ),
                    Static("[dim]Files will be named with timestamp[/]", classes="input-hint"),
                    classes="question-group"
                ),

                Static("", id="export-status"),

                Horizontal(
                    Button("Cancel", id="btn-cancel"),
                    Button("Export", variant="primary", id="btn-export"),
                ),
                id="export-form"
            ),
            id="export-container"
        )
        yield Footer()

    def _do_export(self) -> None:
        """Perform the export."""
        db = self.app.db

        # Get format
        format_set = self.query_one("#format-select", RadioSet)
        export_json = format_set.pressed_index == 0

        # Get output directory
        output_dir_input = self.query_one("#output-dir", Input)
        output_dir = Path(output_dir_input.value.strip() or "./exports")

        status = self.query_one("#export-status", Static)
        status.update("[yellow]Exporting...[/]")

        try:
            data = db.export_all()
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_dir.mkdir(parents=True, exist_ok=True)

            if export_json:
                output_path = output_dir / f"radiant_export_{timestamp}.json"
                with open(output_path, "w") as f:
                    json.dump(data, f, indent=2, default=str)
                status.update(f"[green]Exported to {output_path}[/]")
                self.notify(f"Exported to {output_path}")
            else:
                export_dir = output_dir / f"radiant_export_{timestamp}"
                export_dir.mkdir(parents=True, exist_ok=True)

                files_created = []
                for key, items in data.items():
                    if items and isinstance(items, list) and len(items) > 0:
                        csv_path = export_dir / f"{key}.csv"
                        fieldnames = list(items[0].keys())
                        with open(csv_path, "w", newline="") as f:
                            writer = csv.DictWriter(f, fieldnames=fieldnames)
                            writer.writeheader()
                            for item in items:
                                writer.writerow({
                                    k: str(v) if v is not None else ""
                                    for k, v in item.items()
                                })
                        files_created.append(key)

                status.update(f"[green]Exported {len(files_created)} files to {export_dir}/[/]")
                self.notify(f"Exported to {export_dir}/")

        except Exception as e:
            status.update(f"[red]Error: {e}[/]")
            self.notify(f"Export failed: {e}", severity="error")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "btn-cancel":
            self.app.pop_screen()
        elif event.button.id == "btn-export":
            self._do_export()

    def action_go_back(self) -> None:
        """Go back to previous screen."""
        self.app.pop_screen()
