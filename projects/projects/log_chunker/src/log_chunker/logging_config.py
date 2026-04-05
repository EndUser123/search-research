"""Modern logging configuration using loguru with best practices."""

import sys
from datetime import datetime
from pathlib import Path

try:
    from loguru import logger

    HAS_LOGURU = True
except ImportError:
    import logging

    HAS_LOGURU = False


def setup_logging(
    log_level: str = "INFO",
    log_dir: str | None = None,
    app_name: str = "log_chunker",
    enable_rotation: bool = True,
    fresh_log_per_run: bool = True,
) -> None:
    """
    Setup modern logging with loguru or fallback to standard logging.

    Features:
    - Fresh log file per run with timestamp
    - Automatic rotation (10MB max, 5 files retained)
    - Structured logging with context
    - Color-coded console output
    - Performance-optimized

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
        log_dir: Directory for log files (default: logs/)
        app_name: Application name for log files
        enable_rotation: Enable log rotation
        fresh_log_per_run: Create new log file for each run
    """

    # Setup log directory
    if log_dir is None:
        log_dir = Path("logs")
    else:
        log_dir = Path(log_dir)

    log_dir.mkdir(exist_ok=True)

    if HAS_LOGURU:
        _setup_loguru_logging(
            log_level, log_dir, app_name, enable_rotation, fresh_log_per_run
        )
    else:
        _setup_standard_logging(
            log_level, log_dir, app_name, enable_rotation, fresh_log_per_run
        )


def _setup_loguru_logging(
    log_level: str,
    log_dir: Path,
    app_name: str,
    enable_rotation: bool,
    fresh_log_per_run: bool,
) -> None:
    """Setup loguru logging with advanced features."""

    # Remove default handler
    logger.remove()

    # Console handler with colors and formatting
    logger.add(
        sys.stderr,
        level=log_level,
        format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
        "<level>{message}</level>",
        colorize=True,
        backtrace=True,
        diagnose=True,
    )

    # File handler
    if fresh_log_per_run:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = log_dir / f"{app_name}_{timestamp}.log"
    else:
        log_file = log_dir / f"{app_name}.log"

    file_config = {
        "sink": str(log_file),
        "level": log_level,
        "format": "{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} | {message}",
        "backtrace": True,
        "diagnose": True,
        "serialize": False,  # Human-readable format
    }

    if enable_rotation:
        file_config.update(
            {
                "rotation": "10 MB",  # Rotate when file reaches 10MB
                "retention": "7 days",  # Keep logs for 7 days
                "compression": "zip",  # Compress old logs
            }
        )

    logger.add(**file_config)

    # Add context for the session
    logger.info(f"Logging initialized - Level: {log_level}, File: {log_file}")


def _setup_standard_logging(
    log_level: str,
    log_dir: Path,
    app_name: str,
    enable_rotation: bool,
    fresh_log_per_run: bool,
) -> None:
    """Fallback to standard Python logging with rotation."""

    import logging
    import logging.handlers

    # Clear existing handlers
    logging.getLogger().handlers.clear()

    # Create formatters
    console_formatter = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    file_formatter = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S.%f",
    )

    # Console handler
    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setLevel(getattr(logging, log_level))
    console_handler.setFormatter(console_formatter)

    # File handler
    if fresh_log_per_run:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = log_dir / f"{app_name}_{timestamp}.log"

        file_handler = logging.FileHandler(str(log_file))
    else:
        log_file = log_dir / f"{app_name}.log"

        if enable_rotation:
            file_handler = logging.handlers.RotatingFileHandler(
                str(log_file),
                maxBytes=10 * 1024 * 1024,  # 10MB
                backupCount=5,
                encoding="utf-8",
            )
        else:
            file_handler = logging.FileHandler(str(log_file))

    file_handler.setLevel(getattr(logging, log_level))
    file_handler.setFormatter(file_formatter)

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level))
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)

    root_logger.info(
        f"Standard logging initialized - Level: {log_level}, File: {log_file}"
    )


def get_logger(name: str = __name__):
    """Get logger instance - works with both loguru and standard logging."""
    if HAS_LOGURU:
        return logger.bind(name=name)
    else:
        return logging.getLogger(name)


# Convenience function for common use case
def init_app_logging(
    verbose: bool = False, quiet: bool = False, log_dir: str | None = None
) -> None:
    """Initialize logging for the application with common settings."""

    if quiet:
        level = "WARNING"
    elif verbose:
        level = "DEBUG"
    else:
        level = "INFO"

    setup_logging(
        log_level=level,
        log_dir=log_dir,
        app_name="log_chunker",
        enable_rotation=True,
        fresh_log_per_run=True,
    )
