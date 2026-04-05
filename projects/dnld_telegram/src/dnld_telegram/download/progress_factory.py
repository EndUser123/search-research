"""
Progress Display Factory - Plugin Architecture for Different Progress Modes
Supports: rich (multiple bars), simple (single bar), quiet (minimal)
"""

from typing import Any

from loguru import logger
from rich.console import Console
from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TaskProgressColumn,
    TextColumn,
    TimeRemainingColumn,
)

from ..ui.base import BaseUIDisplay, UIConfig
from ..ui.factory import UIFactory


class RichProgressDisplay(BaseUIDisplay):
    """Rich progress display with multiple progress bars."""

    def __init__(
        self,
        download_dir: str = "downloads",
        console: Console | None = None,
        show_file_progress: bool = True,
        config: UIConfig | None = None,
    ):
        super().__init__(console=console)
        self.console = console or Console()
        self.show_file_progress = show_file_progress
        self.progress = Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            TimeRemainingColumn(),
            console=self.console,
        )
        self.download_tasks: dict[str, Any] = {}
        self.main_tasks: dict[str, Any] = {}

    def render(self) -> Progress:
        return self.progress

    def add_download_task(self, filename: str, total_bytes: int) -> int | None:
        if not self.show_file_progress:
            return None
        task_id = self.progress.add_task(f"Download {filename}", total=total_bytes)
        self.download_tasks[filename] = task_id
        return task_id

    def start_download_task(self, filename: str) -> None:
        if filename in self.download_tasks:
            self.progress.start_task(self.download_tasks[filename])

    def update_download_task(self, filename: str, advance: int) -> None:
        try:
            if filename in self.download_tasks:
                self.progress.update(self.download_tasks[filename], advance=advance)
        except Exception as e:
            logger.error(f"Download progress update error for {filename}: {e}")

    def complete_download_task(self, filename: str) -> None:
        try:
            if filename in self.download_tasks:
                task_id = self.download_tasks[filename]
                self.progress.update(
                    task_id, completed=self.progress.tasks[task_id].total or 100
                )
                self.progress.remove_task(task_id)
                del self.download_tasks[filename]
        except Exception as e:
            logger.error(f"Download complete error for {filename}: {e}")

    def error_download_task(self, filename: str, error: str) -> None:
        try:
            if filename in self.download_tasks:
                task_id = self.download_tasks[filename]
                self.progress.update(task_id, description=f"[red]Error: {filename}")
        except Exception as e:
            logger.error(f"Download error task for {filename}: {e}")

    def add_main_task(
        self, task_id: str, description: str, total: int | None = None
    ) -> None:
        prog_task_id = self.progress.add_task(description, total=total)
        self.main_tasks[task_id] = prog_task_id

    def start_main_task(self, task_id: str) -> None:
        if task_id in self.main_tasks:
            self.progress.start_task(self.main_tasks[task_id])

    def update_main_task(
        self, task_id: str, advance: int = 0, status: str | None = None
    ) -> None:
        if task_id in self.main_tasks:
            task_to_update = self.main_tasks[task_id]
            if advance > 0:
                self.progress.update(task_to_update, advance=advance)
            if status:
                self.progress.update(task_to_update, description=status)

    def complete_main_task(self, task_id: str, final_status: str | None = None) -> None:
        if task_id in self.main_tasks:
            task = self.progress.tasks[self.main_tasks[task_id]]
            if final_status:
                self.progress.update(self.main_tasks[task_id], description=final_status)
            self.progress.update(self.main_tasks[task_id], completed=task.total or 100)


class SimpleProgressDisplay(BaseUIDisplay):
    """Simple progress display with single overall progress bar."""

    def __init__(
        self,
        download_dir: str = "downloads",
        console: Console | None = None,
        config: UIConfig | None = None,
    ):
        super().__init__(console=console)
        self.console = console or Console()
        self.progress = Progress(
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            TimeRemainingColumn(),
            console=self.console,
        )
        self.main_tasks: dict[str, Any] = {}

    def render(self) -> Progress:
        return self.progress

    def add_download_task(self, filename: str, total_bytes: int) -> int | None:
        return None

    def start_download_task(self, filename: str) -> None:
        pass

    def update_download_task(self, filename: str, advance: int) -> None:
        pass

    def complete_download_task(self, filename: str) -> None:
        self.console.print(f"[green]✓[/green] {filename}")

    def error_download_task(self, filename: str, error: str) -> None:
        self.console.print(f"[red]✗[/red] {filename}: {error}")

    def add_main_task(
        self, task_id: str, description: str, total: int | None = None
    ) -> None:
        prog_task_id = self.progress.add_task(description, total=total)
        self.main_tasks[task_id] = prog_task_id

    def start_main_task(self, task_id: str) -> None:
        if task_id in self.main_tasks:
            self.progress.start_task(self.main_tasks[task_id])

    def update_main_task(
        self, task_id: str, advance: int = 0, status: str | None = None
    ) -> None:
        if task_id in self.main_tasks:
            task_to_update = self.main_tasks[task_id]
            if advance > 0:
                self.progress.update(task_to_update, advance=advance)
            if status:
                self.progress.update(task_to_update, description=status)

    def complete_main_task(self, task_id: str, final_status: str | None = None) -> None:
        if task_id in self.main_tasks:
            task = self.progress.tasks[self.main_tasks[task_id]]
            if final_status:
                self.progress.update(self.main_tasks[task_id], description=final_status)
            self.progress.update(self.main_tasks[task_id], completed=task.total or 100)


class QuietProgressDisplay(BaseUIDisplay):
    """Quiet progress display with minimal output."""

    def __init__(
        self,
        download_dir: str = "downloads",
        console: Console | None = None,
        config: UIConfig | None = None,
    ):
        super().__init__(console=console)
        self.console = console or Console()

    def render(self) -> str:
        return ""

    def add_download_task(self, filename: str, total_bytes: int) -> int | None:
        return None

    def start_download_task(self, filename: str) -> None:
        pass

    def update_download_task(self, filename: str, advance: int) -> None:
        pass

    def complete_download_task(self, filename: str) -> None:
        pass

    def error_download_task(self, filename: str, error: str) -> None:
        logger.error(f"{filename}: {error}")

    def add_main_task(
        self, task_id: str, description: str, total: int | None = None
    ) -> None:
        logger.info(f"Starting: {description}")

    def start_main_task(self, task_id: str) -> None:
        # QuietProgressDisplay doesn't maintain tasks - just log
        pass

    def update_main_task(
        self, task_id: str, advance: int = 0, status: str | None = None
    ) -> None:
        if status:
            logger.info(status)

    def complete_main_task(self, task_id: str, final_status: str | None = None) -> None:
        if final_status:
            logger.info(f"Complete: {final_status}")


def create_progress_display(
    mode: str = "rich",
    show_file_progress: bool = True,
    console: Console | None = None,
    download_dir: str = "downloads",
    config: UIConfig | None = None,
    log_level: str | None = None,
) -> BaseUIDisplay:
    """Factory function to create progress display based on mode."""
    # Map old modes to new UI system with A/B differentiation
    mode_mapping = {
        "A": "simple_clean",  # UI A: Simple clean text output (no tqdm)
        "B": "tqdm_enhanced",  # UI B: Enhanced tqdm with statistics
        "rich": "rich",
        "paneled": "rich",
        "production": "tqdm",
        "simple": "simple",
        "quiet": "simple",
        "clean": "simple",
        "gorgeous": "alive",
        "tqdm": "tqdm",
        "alive": "alive",
        "textual": "textual",
    }

    # Map to new UI type
    new_mode = mode_mapping.get(mode, "simple")

    try:
        # Special handling for enhanced tqdm mode
        if new_mode == "tqdm_enhanced":
            return UIFactory.create(
                "tqdm",
                console=console,
                config=config,
                show_file_progress=show_file_progress,
                download_dir=download_dir,
                enhanced_mode=True,  # Enable enhanced mode for UI B
            )
        else:
            # Use the new UI factory system
            return UIFactory.create(
                new_mode,
                console=console,
                config=config,
                show_file_progress=show_file_progress,
                download_dir=download_dir,
            )
    except (ValueError, ImportError) as e:
        logger.warning(
            f"Requested UI mode '{new_mode}' not available or failed to load: {e}. Falling back to default."
        )
        # Fallback to default display if requested type not available
        return UIFactory.get_default(console=console, config=config)
