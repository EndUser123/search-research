# dev/view_logs.py
"""
A safe, self-contained script to view the project's structured JSON logs.
This script uses the existing `rich` library dependency.

Usage:
    python dev/view_logs.py
"""

import json
from pathlib import Path

try:
    from rich.console import Console
    from rich.syntax import Syntax
except ImportError:
    print(
        "Error: The 'rich' library is not installed. Please run 'pip install -r requirements.txt'"
    )
    exit(1)

LOG_FILE = Path(__file__).parent.parent / "logs" / "yt_sync_structured.log"


def view_logs():
    """Reads and pretty-prints the structured log file."""
    console = Console()

    if not LOG_FILE.exists():
        console.print(
            f"[bold red]Log file not found at:[/] [yellow]{LOG_FILE}[/yellow]"
        )
        return

    console.print(f"📄 [bold]Displaying logs from:[/] [cyan]{LOG_FILE}[/cyan]\n")

    with open(LOG_FILE, encoding="utf-8") as f:
        for line in f:
            try:
                # Parse each line as a separate JSON object
                log_entry = json.loads(line)
                # Use rich's Syntax to pretty-print and colorize the JSON
                pretty_json = Syntax(
                    json.dumps(log_entry, indent=2),
                    "json",
                    theme="monokai",
                    line_numbers=False,
                )
                console.print(pretty_json)
                console.print("-" * 20)
            except json.JSONDecodeError:
                # If a line isn't valid JSON, print it as plain text
                console.print(f"[dim]Unparsable line:[/] {line.strip()}")


if __name__ == "__main__":
    view_logs()
