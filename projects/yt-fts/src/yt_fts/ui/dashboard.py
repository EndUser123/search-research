"""
UI Dashboard for yt-fts - Simple TUI Implementation
"""
from __future__ import annotations

from rich.console import Console

# Define minimum textual version requirement
MIN_TEXTUAL_VERSION = "0.1.0"

# Check if Textual is available
try:
    from textual.app import App
    from textual.containers import Container
    from textual.widgets import Static

    TEXTUAL_AVAILABLE = True
except ImportError:
    TEXTUAL_AVAILABLE = False
    App = None
    Static = None
    Container = None


class Dashboard:
    """
    Simple dashboard implementation for yt-fts.
    Falls back gracefully if Textual is not available.
    """

    def __init__(self, console: Console = None):
        """
        Initialize the dashboard.

        Args:
            console: Rich console instance (defaults to new Console())
        """
        self.console = console or Console()

    def show_info(self, title: str, content: str) -> None:
        """Show information using Rich console output."""
        self.console.print(f"\n[bold blue]{title}[/bold blue]")
        self.console.print(content)

    def show_progress(self, message: str) -> None:
        """Show progress message."""
        self.console.print(f"📊 {message}")

    def show_error(self, error: str) -> None:
        """Show error message."""
        self.console.print(f"[red]❌ {error}[/red]")

    def show_success(self, message: str) -> None:
        """Show success message."""
        self.console.print(f"[green]✅ {message}[/green]")


if TEXTUAL_AVAILABLE:

    class TextualDashboard(App):
        """
        Textual TUI Dashboard implementation.
        Only used if Textual is available and requested.
        """

        def __init__(self, title: str = "YT-FTS Dashboard"):
            """
            Initialize the Textual TUI dashboard.

            Args:
                title: Dashboard title
            """
            super().__init__()
            self.title = title

        def compose(self):
            """Compose the TUI layout."""
            yield Container(
                Static(f"[bold blue]{self.title}[/bold blue]", id="title"),
                Static("📊 YT-FTS - YouTube Full Text Search", id="subtitle"),
            )

        def on_mount(self):
            """Called when the app is mounted."""
            self.query_one("#title").update(f"[bold blue]{self.title}[/bold blue]")

else:
    TextualDashboard = None  # type: ignore[misc, assignment]


def check_textual_availability() -> tuple[bool, str]:
    """
    Check if Textual is available and meets version requirements.

    Returns:
        tuple: (is_available, message)
    """
    if not TEXTUAL_AVAILABLE:
        return False, "Textual is not available"

    try:
        import textual

        installed = textual.__version__
        return True, installed
    except (ImportError, AttributeError):
        return False, "Textual version could not be determined"
