"""Summary card widget for displaying financial metrics."""

from textual.widgets import Static
from textual.containers import Vertical


class SummaryCard(Static):
    """A card displaying a financial summary metric."""

    DEFAULT_CSS = """
    SummaryCard {
        width: 1fr;
        height: auto;
        min-height: 5;
        padding: 1 2;
        margin: 0 1 1 0;
        background: #161b22;
        border: round #21262d;
    }

    SummaryCard:hover {
        border: round #006e38;
    }

    SummaryCard .card-title {
        color: #8b949e;
        text-style: bold;
    }

    SummaryCard .card-value {
        color: #00d26a;
        text-style: bold;
    }

    SummaryCard .card-value.positive {
        color: #3fb950;
    }

    SummaryCard .card-value.negative {
        color: #f85149;
    }

    SummaryCard .card-subtitle {
        color: #6e7681;
    }
    """

    def __init__(
        self,
        title: str,
        value: str,
        subtitle: str = "",
        value_type: str = "neutral",  # neutral, positive, negative
        **kwargs
    ):
        super().__init__(**kwargs)
        self.card_title = title
        self.card_value = value
        self.card_subtitle = subtitle
        self.value_type = value_type

    def render(self) -> str:
        value_class = ""
        if self.value_type == "positive":
            value_class = "[green]"
            value_end = "[/]"
        elif self.value_type == "negative":
            value_class = "[red]"
            value_end = "[/]"
        else:
            value_class = "[#00d26a]"
            value_end = "[/]"

        lines = [
            f"[#8b949e]{self.card_title}[/]",
            f"{value_class}{self.card_value}{value_end}",
        ]

        if self.card_subtitle:
            lines.append(f"[#6e7681]{self.card_subtitle}[/]")

        return "\n".join(lines)

    def update_value(self, value: str, value_type: str = "neutral") -> None:
        """Update the card's value."""
        self.card_value = value
        self.value_type = value_type
        self.refresh()
