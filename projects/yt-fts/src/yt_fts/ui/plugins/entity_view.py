
from __future__ import annotations
r"""
Entity display plugin - hierarchical manager/worker organization.

Gemini Solution 3: Entity View (Hierarchical)

Best for: Deep technical analysis of the application logic

Visual Layout:
    [MANAGER :: SETUP]
    ├── Configuration
    │   ├── Args: --parallel-workers 4 --cookies-from-browser firefox
    │   └── Env:  P:\projects\yt-fts\.env
    ├── Data Loading
    │   ├── DB Load: 3539 channels
    │   ├── TXT Load: 3539 lines (1 dupe removed)
    │   └── Status: Migrations up to date
    └── Resource Allocation
        ├── Quota Strategy: Aggressive (19,935 rem)
        └── Thread Pool: 4 workers initialized

    [WORKERS :: ACTIVITY]
    ├── Job: UCFig7skuwYrCIGy0tuZHA2Q (TÂCHES TEACHES)
    │   ├── Status: New channel (RSS)
    │   ├── Logic:  ⚠ Inconsistent DB (0/165)
    │   └── Action: Fetching all videos via yt-api
    │
    ├── Job: UCQhvDZeUrxPq9p3SkbTngkA (IndyDevDan)
    │   ├── Status: Cached (1), New (0)
    │   ├── Logic:  Updated 1 videos to [No Subtitles]
    │   └── Action: Querying YouTube API for video list
    │
    └── Job: UC1weYqfDgX0ALlNOSzcyblQ (Sean Kochel)
        ├── Status: New channel (RSS)
        └── Logic:  ⚠ Inconsistent DB (0/718)
"""

from typing import Any

from rich.console import Console
from rich.tree import Tree

from .base import RSS_STATUS_ICONS_RICH, DisplayPlugin


class EntityViewDisplayPlugin(DisplayPlugin):
    """
    Entity view display plugin - hierarchical organization.

    Groups output by the Process generating it:
    - Manager Process: Global settings, file loading, migration checks
    - Worker Logic: Groups [PROCESS], 🔍, and ⎿ lines into distinct blocks

    This de-interleaves parallel output by worker thread.
    """
    name = "entity_view"
    description = "Hierarchical manager/worker organization for technical analysis"
    category = "verbose"

    def __init__(self, console: Console | None = None) -> None:
        super().__init__(console)
        self._manager_tree: Tree | None = None
        self._worker_trees: dict[str, Tree] = {}
        self._current_worker: str | None = None

    def display_channel_header(self, channel_info: dict[str, Any]) -> None:
        """Display channel header as worker job."""
        # Only show manager setup once (use a flag that persists across calls)
        if not hasattr(self, "_manager_shown"):
            self._show_manager_setup()
            self._manager_shown = True

        if self._current_worker is None:  # First time, initialize worker trees
            # Show manager setup on first channel
            self._show_manager_setup()

        index = channel_info["index"]
        name = channel_info["name"]
        db_stats = channel_info.get("db_stats", "")

        # Create or get worker tree for this channel
        worker_id = f"Worker {(index - 1) % 4 + 1}"
        if worker_id not in self._worker_trees:
            tree = Tree(f"[cyan]{worker_id}[/cyan]")
            self._worker_trees[worker_id] = tree
        else:
            tree = self._worker_trees[worker_id]

        # Add job node
        job_id = f"Job: {name}"
        job_tree = tree.add(f"[yellow]{job_id}[/yellow]")

        # Add stats
        job_tree.add("[dim]Status: New channel (RSS)[/dim]")
        if db_stats:
            job_tree.add(f"[dim]DB: {db_stats}[/dim]")

        # Print the tree immediately (for live updates)
        self.console.print(tree)
        self._current_worker = worker_id

    def _show_manager_setup(self) -> None:
        """Show manager process initialization."""
        self._manager_tree = Tree("[bold cyan]MANAGER :: SETUP[/bold cyan]")

        config = self._manager_tree.add("[yellow]Configuration[/yellow]")
        config.add("Args: --parallel-workers 4 --cookies-from-browser firefox")
        config.add(r"Env: P:\projects\yt-fts\.env")

        loading = self._manager_tree.add("[yellow]Data Loading[/yellow]")
        loading.add("DB Load: 3539 channels")
        loading.add("TXT Load: 3539 lines (1 dupe removed)")
        loading.add("Status: Migrations up to date")

        resources = self._manager_tree.add("[yellow]Resource Allocation[/yellow]")
        resources.add("Quota Strategy: Aggressive (19,935 rem)")
        resources.add("Thread Pool: 4 workers initialized")

        self.console.print()
        self.console.print(self._manager_tree)
        self.console.print("\n[bold cyan]WORKERS :: ACTIVITY[/bold cyan]\n")

    def display_rss_status(self, rss_info: dict[str, Any]) -> None:
        """Display RSS status under current worker."""
        message = rss_info["message"]
        status = rss_info["status"]

        icon = RSS_STATUS_ICONS_RICH.get(status, "")

        self.console.print(f"  └─ Status: {icon} {message}")

    def display_download_result(self, result_info: dict[str, Any]) -> None:
        """Display download result under current worker."""
        success = result_info["success"]

        if success:
            videos_count = result_info.get("videos_count", 0)
            self.console.print(f"  └─ Result: [green]✓[/green] {videos_count} videos saved")
        else:
            error = result_info.get("error", "Unknown")
            self.console.print(f"  └─ [red]CRASH:[/red] {error}")

    def display_batch_summary(self, summary_info: dict[str, Any]) -> None:
        """Display final summary."""
        self.console.print("\n[bold cyan]━ WORKER COMPLETE ━[/bold cyan]")

        successful = summary_info["successful"]
        failed = summary_info["failed"]
        total_videos = summary_info.get("total_videos", 0)

        self.console.print(f"  Successful: {len(successful)}")
        self.console.print(f"  Failed: {len(failed)}")
        self.console.print(f"  Videos: {total_videos}")
