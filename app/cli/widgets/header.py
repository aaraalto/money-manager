"""Radiant gradient header widgets."""

from textual.widgets import Static


BANNER = """[#00d26a]  ██████╗  █████╗ ██████╗ ██╗ █████╗ ███╗   ██╗████████╗[/]
[#00b85c]  ██╔══██╗██╔══██╗██╔══██╗██║██╔══██╗████╗  ██║╚══██╔══╝[/]
[#00a050]  ██████╔╝███████║██║  ██║██║███████║██╔██╗ ██║   ██║   [/]
[#008744]  ██╔══██╗██╔══██║██║  ██║██║██╔══██║██║╚██╗██║   ██║   [/]
[#006e38]  ██║  ██║██║  ██║██████╔╝██║██║  ██║██║ ╚████║   ██║   [/]
[#00552c]  ╚═╝  ╚═╝╚═╝  ╚═╝╚═════╝ ╚═╝╚═╝  ╚═╝╚═╝  ╚═══╝   ╚═╝   [/]"""

MINI_BANNER = "[#00d26a bold]RADIANT[/] [dim]Money Manager[/]"

TAGLINE = "[dim]See your money clearly.[/]"


class RadiantHeader(Static):
    """Full Radiant banner header with gradient colors."""

    DEFAULT_CSS = """
    RadiantHeader {
        height: 7;
        padding: 0;
    }
    """

    def __init__(self, show_tagline: bool = True):
        super().__init__()
        self.show_tagline = show_tagline

    def render(self) -> str:
        if self.show_tagline:
            return f"{BANNER}\n{TAGLINE}"
        return BANNER


class MiniHeader(Static):
    """Compact single-line header."""

    DEFAULT_CSS = """
    MiniHeader {
        height: 2;
        padding: 0 1;
        background: #161b22;
        border-bottom: solid #21262d;
    }
    """

    def render(self) -> str:
        return f"{MINI_BANNER}  {TAGLINE}"
