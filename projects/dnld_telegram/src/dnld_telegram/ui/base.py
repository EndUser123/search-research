"""
Base UI interface for all display types
"""

import asyncio
from abc import ABC, abstractmethod
from typing import Any, cast


class BaseUIDisplay(ABC):
    def add_main_task(
        self, task_id: str, description: str, total: int | None = None
    ) -> None:
        """Add a main progress task (default: no-op)"""
        pass

    def start_main_task(self, task_id: str) -> None:
        """Start a main progress task (default: no-op)"""
        pass

    def update_main_task(
        self, task_id: str, advance: int = 0, status: str | None = None
    ) -> None:
        """Update a main progress task (default: no-op)"""
        pass

    def complete_main_task(
        self, task_id: str, final_status: str | None = None
    ) -> None:
        """Complete a main progress task (default: no-op)"""
        pass

    def is_termination_requested(self) -> bool:
        """Check if termination is requested (default: always False)"""
        return False

    """Abstract base class for all UI display types"""

    def __init__(self, console: Any | None = None):
        self.console = console
        self.stats: dict[str, int | float | None | str] = {
            "total_files": 0,
            "downloaded": 0,
            "failed": 0,
            "start_time": None,
            "current_file": "",
        }

    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the UI display"""
        pass

    @abstractmethod
    async def start_progress(self, total_files: int) -> None:
        """Start progress display for total number of files"""
        pass

    @abstractmethod
    async def update_progress(
        self, current: int, filename: str, status: str = "downloading"
    ) -> None:
        """Update progress display"""
        pass

    @abstractmethod
    async def finish_progress(self) -> None:
        """Finish progress display and show summary"""
        pass

    @abstractmethod
    async def cleanup(self) -> None:
        """Cleanup UI resources"""
        pass

    async def __aenter__(self) -> "BaseUIDisplay":
        await self.initialize()
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        await self.cleanup()


class ConcurrentDownloadMixin:
    """Mixin to provide concurrent download capabilities to UI displays"""

    async def download_files_concurrent(
        self, files: list[dict[str, Any]], download_func: Any, max_concurrent: int = 2
    ) -> list[Any]:
        """
        Download files concurrently with progress updates

        Args:
            files: List of file info dictionaries
            download_func: Async function to download a single file
            max_concurrent: Maximum concurrent downloads
        """
        import time

        base_self = cast(BaseUIDisplay, self)

        base_self.stats["total_files"] = float(len(files))
        base_self.stats["start_time"] = float(
            base_self.stats["start_time"] or time.time()
        )

        await base_self.start_progress(len(files))

        # Create semaphore to limit concurrent downloads
        semaphore = asyncio.Semaphore(max_concurrent)
        completed = 0

        async def download_with_semaphore(file_info: dict[str, Any]) -> bool:
            nonlocal completed
            async with semaphore:
                completed += 1
                await base_self.update_progress(
                    completed, file_info["filename"], "downloading"
                )

                try:
                    success = await download_func(file_info)
                    if success:
                        current_downloaded = base_self.stats["downloaded"]
                        if isinstance(current_downloaded, (int, float)):
                            base_self.stats["downloaded"] = (
                                float(current_downloaded) + 1
                            )
                        await base_self.update_progress(
                            completed, file_info["filename"], "completed"
                        )
                    else:
                        current_failed = base_self.stats["failed"]
                        if isinstance(current_failed, (int, float)):
                            base_self.stats["failed"] = float(current_failed) + 1
                        await base_self.update_progress(
                            completed, file_info["filename"], "failed"
                        )
                    return success
                except Exception:
                    current_failed = base_self.stats["failed"]
                    if isinstance(current_failed, (int, float)):
                        base_self.stats["failed"] = float(current_failed) + 1
                    await base_self.update_progress(
                        completed, file_info["filename"], "error"
                    )
                    return False

        # Create tasks for all downloads
        tasks = [download_with_semaphore(file_info) for file_info in files]

        # Execute all downloads concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Count exceptions as failures
        for result in results:
            if isinstance(result, Exception):
                current_failed = base_self.stats["failed"]
                if isinstance(current_failed, (int, float)):
                    base_self.stats["failed"] = float(current_failed) + 1

        await base_self.finish_progress()
        return results


class UIConfig:
    """Configuration for UI displays"""

    def __init__(
        self,
        max_concurrent: int = 2,
        show_progress: bool = True,
        show_speed: bool = True,
        show_eta: bool = True,
        timeout: int = 30,
        icons_on: bool = True,
        ascii_only: bool = False,
        align_stats: bool = True,
        max_name_width: int = 25,
    ):
        self.max_concurrent = max_concurrent
        self.show_progress = show_progress
        self.show_speed = show_speed
        self.show_eta = show_eta
        self.timeout = timeout
        self.icons_on = icons_on
        self.ascii_only = ascii_only
        self.align_stats = align_stats
        self.max_name_width = max_name_width
