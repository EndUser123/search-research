from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class ProgressProto(Protocol):
    """
    Minimal required surface for a progress display used by the downloader.

    Implementations may provide additional methods, but callers should guard their
    usage (e.g., via hasattr) when invoking optional features.
    """

    def add_main_task(
        self, task_id: str, description: str, total: int | None = None
    ) -> None:
        ...

    def start_main_task(self, task_id: str) -> None:
        ...

    def update_main_task(
        self, task_id: str, advance: int = 0, status: str | None = None
    ) -> None:
        ...

    def complete_main_task(
        self, task_id: str, final_status: str | None = None
    ) -> None:
        ...

    # Optional lifecycle hooks – implement if applicable
    def add_download_task(self, filename: str, total_bytes: int) -> str:
        ...

    def start_download_task(self, filename: str) -> None:
        ...

    def update_download_task(self, filename: str, advance: int) -> None:
        ...

    def complete_download_task(self, filename: str) -> None:
        ...

    def error_download_task(self, filename: str, error_msg: str) -> None:
        ...

    # Non-fatal check – implementations that need termination logic can override
    def is_termination_requested(self) -> bool:
        return False
