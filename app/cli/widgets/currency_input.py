"""Currency input widget with formatting."""

from textual.widgets import Input
from textual.validation import Validator, ValidationResult
import re


class CurrencyValidator(Validator):
    """Validator for currency inputs."""

    def validate(self, value: str) -> ValidationResult:
        # Allow empty
        if not value:
            return self.success()

        # Remove currency symbols and commas
        cleaned = value.replace("$", "").replace(",", "").strip()

        # Check if it's a valid number
        try:
            float(cleaned)
            return self.success()
        except ValueError:
            return self.failure("Please enter a valid amount")


class CurrencyInput(Input):
    """Input widget for currency amounts."""

    DEFAULT_CSS = """
    CurrencyInput {
        width: 100%;
    }

    CurrencyInput:focus {
        border: tall #006e38;
    }

    CurrencyInput.-valid {
        border: tall #3fb950;
    }

    CurrencyInput.-invalid {
        border: tall #f85149;
    }
    """

    def __init__(
        self,
        placeholder: str = "0.00",
        value: str = "",
        **kwargs
    ):
        super().__init__(
            placeholder=f"$ {placeholder}",
            value=value,
            validators=[CurrencyValidator()],
            **kwargs
        )

    def get_value(self) -> float:
        """Get the numeric value of the input."""
        if not self.value:
            return 0.0

        # Remove currency symbols and commas
        cleaned = self.value.replace("$", "").replace(",", "").strip()

        try:
            return float(cleaned)
        except ValueError:
            return 0.0

    def set_value(self, amount: float) -> None:
        """Set the input value from a float."""
        self.value = f"{amount:,.2f}"
