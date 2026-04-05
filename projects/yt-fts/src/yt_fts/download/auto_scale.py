"""
Adaptive parallel worker scaling based on operation mode and system constraints.

Key principles:
1. Metadata mode (min_saved=0): High parallelism - API calls are read-only
2. Subtitle mode (min_saved>0): Low parallelism - SQLite writes limit concurrency
3. System constraints: CPU cores, memory, and database lock tolerance
"""
from __future__ import annotations

import multiprocessing
from typing import Any, Literal


def get_optimal_workers(
    mode: Literal["metadata", "subtitles", "mixed"],
    max_workers: int | None = None,
    quota_remaining: int | None = None,
    cpu_cores: int | None = None,
) -> int:
    """
    Calculate optimal number of parallel workers based on operation mode.

    Args:
        mode: "metadata" (API only), "subtitles" (yt-dlp downloads), or "mixed"
        max_workers: User-specified maximum (if set, use this directly)
        quota_remaining: Remaining API quota (for metadata mode limiting)
        cpu_cores: System CPU cores (auto-detected if None)

    Returns:
        Optimal number of parallel workers
    """
    # User override takes precedence
    if max_workers is not None:
        return max_workers

    # Auto-detect CPU cores
    if cpu_cores is None:
        cpu_cores = multiprocessing.cpu_count()

    # Mode-based scaling
    if mode == "metadata":
        # API calls are read-only - can be highly parallel
        # Limit by: CPU cores and practical API rate limits
        workers = min(cpu_cores * 2, 16)  # Up to 2x CPU cores, max 16

        # Reduce if quota is running low (to avoid exhausting all keys at once)
        if quota_remaining is not None and quota_remaining < 5000:
            workers = min(workers, 4)  # Conservative with low quota

    elif mode == "subtitles":
        # SQLite writes limit effectiveness
        # Practical limit: 2-4 workers regardless of CPU
        workers = min(cpu_cores, 4)  # Up to CPU cores, max 4

    else:  # mixed
        # Balance between API calls and downloads
        workers = min(cpu_cores, 6)  # Conservative middle ground

    return max(1, workers)  # At least 1 worker


def get_jobs_per_worker(
    workers: int,
    mode: Literal["metadata", "subtitles", "mixed"],
) -> int:
    """
    Calculate jobs per worker (threadpool size for downloads).

    For metadata mode: jobs=1 (API is serial)
    For subtitle mode: jobs=1-2 (SQLite write contention)
    """
    if mode == "metadata":
        return 1  # API calls are serial, parallelism is across workers
    if mode == "subtitles":
        return 1 if workers > 2 else 2  # Reduce jobs with more workers
    return 1


# Preset configurations for common scenarios
PRESETS: dict[str, dict[str, int | float]] = {
    "metadata-fast": {"workers": 8, "jobs": 1, "delay": 0},
    "metadata-balanced": {"workers": 4, "jobs": 1, "delay": 0},
    "subtitles-safe": {"workers": 2, "jobs": 1, "delay": 1},
    "subtitles-max": {"workers": 3, "jobs": 2, "delay": 0},
    "mixed": {"workers": 4, "jobs": 1, "delay": 0.5},
}


def apply_preset(preset_name: str, overrides: dict[str, Any] | None = None) -> dict[str, Any]:
    """Apply a preset configuration with optional overrides."""
    config = PRESETS.get(preset_name, PRESETS["mixed"]).copy()
    if overrides:
        config.update(overrides)
    return config
