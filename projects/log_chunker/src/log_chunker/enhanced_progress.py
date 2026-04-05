"""
Enhanced Progress Bar and Display System for Log Chunker.
"""

from collections.abc import Generator
from contextlib import contextmanager
from typing import Any

from rich.console import Console
from rich.live import Live
from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TaskID,
    TextColumn,
    TimeElapsedColumn,
)
from rich.table import Table


class ProgressTracker:
    def __init__(self, console: Console, transient: bool = True):
        self.progress = Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeElapsedColumn(),
            console=console,
            transient=transient,
        )
        self.live = Live(self.progress)
        self.tasks: dict[str, TaskID] = {}

    @contextmanager
    def track_operation(
        self, description: str, total: float = 100.0
    ) -> Generator[TaskID, None, None]:
        task_id = self.progress.add_task(description, total=total)
        self.tasks[description] = task_id
        try:
            with self.live:
                yield task_id
        finally:
            self.progress.update(task_id, completed=total)

    def update_progress(self, task_id: TaskID, advance: float):
        self.progress.update(task_id, advance=advance)

    def update_task_description(self, task_id: TaskID, description: str):
        self.progress.update(task_id, description=description)


class EnhancedDisplaySystem:
    def __init__(self, console: Console):
        self.console = console
        self.progress_tracker = ProgressTracker(console)

    def display_content_analysis(self, analysis_data):
        """Display content analysis - handles both Dict and ContentAnalysis objects."""
        table = Table(title="Content Analysis Summary")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="magenta")

        # Handle ContentAnalysis object or dict
        if hasattr(analysis_data, "model_dump"):
            # Pydantic model
            data_dict = analysis_data.model_dump()
        elif hasattr(analysis_data, "__dict__"):
            # Dataclass or object with attributes
            data_dict = analysis_data.__dict__
        else:
            # Already a dict
            data_dict = analysis_data

        for key, value in data_dict.items():
            table.add_row(key.replace("_", " ").title(), str(value))
        self.console.print(table)

    def display_final_summary(self, result: Any):
        table = Table(title="Final Summary")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="magenta")
        table.add_row("Total Chunks", str(len(result.chunks)))
        table.add_row("Total Processing Time", f"{result.total_processing_time:.2f}s")
        self.console.print(table)

    @contextmanager
    def track_preprocessing(self) -> Generator[TaskID, None, None]:
        with self.progress_tracker.track_operation("Preprocessing") as task_id:
            yield task_id

    @contextmanager
    def track_chunk_creation(self, total_chunks: int) -> Generator[TaskID, None, None]:
        with self.progress_tracker.track_operation(
            "Creating Chunks", total=total_chunks
        ) as task_id:
            yield task_id

    @contextmanager
    def track_intelligence_generation(
        self, total_steps: int
    ) -> Generator[TaskID, None, None]:
        with self.progress_tracker.track_operation(
            "Generating Intelligence Report", total=total_steps
        ) as task_id:
            yield task_id

    @contextmanager
    def track_report_saving(self) -> Generator[TaskID, None, None]:
        with self.progress_tracker.track_operation("Saving Reports") as task_id:
            yield task_id

    def display_simple_status(self, message: str, style: str):
        self.console.print(f"[{style}]{message}[/{style}]")


import re
from contextlib import nullcontext


class SimpleDisplaySystem:
    """Lightweight display system without Rich progress bars."""

    def __init__(self, console=None):
        self.console = console or self._create_simple_console()

    def _create_simple_console(self):
        """Create a simple console that just prints to stdout."""

        class SimpleConsole:
            def print(self, text, style=None):
                # Strip Rich markup for simple output
                clean_text = re.sub(r"\[.*?\]", "", str(text))
                print(clean_text)

        return SimpleConsole()

    def display_simple_status(self, message: str, style: str = ""):
        """Display a simple status message."""
        print(f"{message}")

    def display_content_analysis(self, analysis_data: dict[str, Any]):
        """Display content analysis in simple format."""
        print("\nContent Analysis:")
        for key, value in analysis_data.items():
            print(f"  {key}: {value}")

    def display_final_summary(self, result: Any):
        """Display final summary in simple format."""
        print("\nSummary:")
        print(f"  Total Chunks: {len(result.chunks)}")
        total_time = getattr(result, "total_processing_time", 0)
        print(f"  Processing Time: {total_time:.2f}s")

    # Context manager methods for compatibility with EnhancedDisplaySystem
    def track_preprocessing(self):
        """Dummy context manager for preprocessing tracking."""
        return self._dummy_context()

    def track_chunk_creation(self, total_chunks: int):
        """Dummy context manager for chunk creation tracking."""
        return self._dummy_context()

    def track_intelligence_generation(self, total_steps: int):
        """Dummy context manager for intelligence generation tracking."""
        return self._dummy_context()

    def track_report_saving(self):
        """Dummy context manager for report saving tracking."""
        return self._dummy_context()

    def _dummy_context(self):
        """Create a dummy context manager that does nothing."""
        return nullcontext()
