import asyncio
import functools
import os
import re
import time
from datetime import datetime

from loguru import logger
from rich.logging import RichHandler

# Global variable to store the current run ID
CURRENT_RUN_ID: str | None = None


def set_run_id(run_id: str):
    """Sets the global run ID for the current execution."""
    global CURRENT_RUN_ID
    CURRENT_RUN_ID = run_id
    logger.debug(f"Set global run ID to: {CURRENT_RUN_ID}")


def get_run_id() -> str | None:
    """Returns the current global run ID."""
    return CURRENT_RUN_ID


class CorrelationIdFilter:
    """A Loguru filter to inject a correlation ID into log records."""

    def __call__(self, record):
        record["extra"]["run_id"] = get_run_id()
        return True


def setup_logging(
    console_level: str = "INFO", file_level: str = "DEBUG", ui_type: str = "rich"
):
    """
    Configures Loguru for console and file logging with rotation and correlation IDs.

    Args:
        console_level: The logging level for console output (e.g., "INFO", "DEBUG").
        file_level: The logging level for file output (e.g., "DEBUG", "INFO").
        ui_type: The UI display type being used (e.g., "tqdm", "rich", "simple").
    """
    logger.remove()  # Remove default handler

    # Add a filter to inject the correlation ID
    correlation_filter = CorrelationIdFilter()

    # Console handler - only add if UI is not tqdm (to prevent dual logging)
    if ui_type.lower() != "tqdm":
        logger.add(
            RichHandler(
                show_time=True,
                show_level=True,
                rich_tracebacks=True,
                tracebacks_suppress=[
                    __import__("tqdm").tqdm
                ],  # Suppress tqdm internal tracebacks
            ),
            level=console_level,
            filter=correlation_filter,
            enqueue=True,  # Use a queue for non-blocking logging
            diagnose=False,  # Disable diagnose for production
        )

    # File handler with rotation and compression
    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)

    # Use a unique identifier for each job run for log file grouping
    # This will be set by the main application entry point
    run_id = (
        CURRENT_RUN_ID if CURRENT_RUN_ID else datetime.now().strftime("%Y%m%d_%H%M%S")
    )
    log_file_base = os.path.join(log_dir, f"telegram_downloader_{run_id}")

    logger.add(
        f"{log_file_base}.log",
        level=file_level,
        rotation="1 MB",  # Rotate every 1 MB
        compression="zip",  # Compress old logs
        enqueue=True,  # Use a queue for non-blocking logging
        filter=correlation_filter,
        format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {extra[run_id]} | {name}:{function}:{line} - {message}",
        serialize=True,  # Serialize log records to JSON
        diagnose=False,  # Disable diagnose for production
    )

    logger.info(
        f"Logging initialized. Console level: {console_level}, File level: {file_level}"
    )
    logger.debug(f"Log files will be stored in: {os.path.abspath(log_dir)}")


def cleanup_old_logs(log_dir: str = "logs", keep_runs: int = 3):
    """
    Cleans up old log files, keeping logs for only the last `keep_runs` job runs.
    A "job run" is identified by the unique run ID in the filename (e.g., telegram_downloader_YYYYMMDD_HHMMSS.log).
    """
    logger.info(
        f"Cleaning up old log files, keeping logs for the last {keep_runs} job runs..."
    )

    log_files = [
        f
        for f in os.listdir(log_dir)
        if f.startswith("telegram_downloader_")
        and f.endswith(".log")
        or f.endswith(".zip")
    ]

    # Group files by run ID
    run_groups = {}
    for f in log_files:
        match = re.match(r"telegram_downloader_(\d{8}_\d{6})", f)
        if match:
            run_id = match.group(1)
            if run_id not in run_groups:
                run_groups[run_id] = []
            run_groups[run_id].append(f)

    # Sort run IDs by date (newest first)
    sorted_run_ids = sorted(run_groups.keys(), reverse=True)

    runs_to_delete = sorted_run_ids[keep_runs:]

    deleted_count = 0
    for run_id in runs_to_delete:
        for filename in run_groups[run_id]:
            file_path = os.path.join(log_dir, filename)
            try:
                os.remove(file_path)
                deleted_count += 1
                logger.debug(f"Deleted old log file: {filename}")
            except Exception as e:
                logger.warning(f"Failed to delete log file {filename}: {e}")

    if deleted_count > 0:
        logger.info(
            f"Cleaned up {deleted_count} old log files from {len(runs_to_delete)} job runs."
        )
    else:
        logger.info("No old log files to clean up.")


# Performance logging decorator
def log_performance(name: str):
    """
    A decorator to log the execution time of a function.
    """

    def decorator(func):
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.perf_counter()
            result = await func(*args, **kwargs)
            end_time = time.perf_counter()
            logger.info(f"Performance: {name} took {end_time - start_time:.4f} seconds")
            return result

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.perf_counter()
            result = func(*args, **kwargs)
            end_time = time.perf_counter()
            logger.info(f"Performance: {name} took {end_time - start_time:.4f} seconds")
            return result

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


# Required imports are now at the top of the file
