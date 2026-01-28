"""Radiant gradient header widget."""

from textual.widgets import Static


BANNER = """[#00d26a]  ██████╗  █████╗ ██████╗ ██╗ █████╗ ███╗   ██╗████████╗[/]
[#00b85c]  ██╔══██╗██╔══██╗██╔══██╗██║██╔══██╗████╗  ██║╚══██╔══╝[/]
[#00a050]  ██████╔╝███████║██║  ██║██║███████║██╔██╗ ██║   ██║   [/]
[#008744]  ██╔══██╗██╔══██║██║  ██║██║██╔══██║██║╚██╗██║   ██║   [/]
[#006e38]  ██║  ██║██║  ██║██████╔╝██║██║  ██║██║ ╚████║   ██║   [/]
[#00552c]  ╚═╝  ╚═╝╚═╝  ╚═╝╚═════╝ ╚═╝╚═╝  ╚═╝╚═╝  ╚═══╝   ╚═╝   [/]"""

TAGLINE = "[dim]See your money clearly. Take control of your future.[/]"


class RadiantHeader(Static):
    """Radiant banner header with gradient colors."""

    DEFAULT_CSS = """
    RadiantHeader {
        height: 8;
        padding: 0 1;
    }
    """

    def __init__(self, show_tagline: bool = True):
        super().__init__()
        self.show_tagline = show_tagline

    def render(self) -> str:
        if self.show_tagline:
            return f"{BANNER}\n{TAGLINE}"
        return BANNER
