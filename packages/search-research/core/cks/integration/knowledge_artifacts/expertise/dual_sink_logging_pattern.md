# Dual-Sink Logging Pattern

**Category:** Logging / Observability
**Source:** yt-fts → CKS port
**Tags:** logging, error_handling, user_experience, debug, structured_logs

## Pattern Overview

Separate technical debugging logs from user-facing console output:
- **File sink**: Structured JSON with full technical details (exceptions, stack traces, timing)
- **Console sink**: Clean user-friendly messages only

## Problem Solved

1. **Console noise**: Technical logs clutter user interface
2. **Debug visibility**: Errors shown to users lack technical context for debugging
3. **Rich compatibility**: print() statements corrupt Rich Live displays

## Implementation

```python
"""
Dual-sink logging system for clean separation of technical debug logs and user console output.
"""

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import rich.console
import rich.logging


class StructuredFileFormatter(logging.Formatter):
    """JSON formatter for structured debug logs."""

    def format(self, record: logging.LogRecord) -> str:
        data = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add domain-specific extra fields
        for field in ["entity_id", "operation", "duration_ms", "validation_type"]:
            if hasattr(record, field):
                data[field] = getattr(record, field)

        if record.exc_info:
            data["exception"] = self.formatException(record.exc_info)

        return json.dumps(data, ensure_ascii=False)


class CleanConsoleFormatter(logging.Formatter):
    """Clean formatter for user console output without technical noise."""

    def format(self, record: logging.LogRecord) -> str:
        # Skip debug in console (file only)
        if record.levelno == logging.DEBUG:
            return ""

        # User-facing messages
        if hasattr(record, "user_message"):
            return record.getMessage()

        # Errors with user-friendly context
        if record.levelno >= logging.ERROR:
            if hasattr(record, "user_error"):
                return f"❌ {record.user_error}"
            msg = record.getMessage()
            return f"❌ ERROR: {msg}" if msg else "❌ ERROR: Check debug logs for details"

        return record.getMessage()


class DualSinkLogger:
    """Dual-sink logging: technical→file, user→console."""

    def __init__(self, log_dir: Path, console: rich.console.Console):
        self.log_dir = log_dir
        self.console = console
        self._setup_handlers()

    def _setup_handlers(self):
        root = logging.getLogger()

        # File handler: JSON structured logs
        file_handler = logging.handlers.RotatingFileHandler(
            self.log_dir / "debug.log",
            maxBytes=50 * 1024 * 1024,
            backupCount=5,
        )
        file_handler.setFormatter(StructuredFileFormatter())
        root.addHandler(file_handler)

        # Console handler: clean output only
        console_handler = rich.logging.RichHandler(
            console=self.console,
            show_time=False,
            show_path=False,
            rich_tracebacks=False,
        )
        console_handler.setFormatter(CleanConsoleFormatter())
        root.addHandler(console_handler)

    def log_technical_error(self, error: Exception, context: dict = None):
        """Log full technical details to file, clean message to console."""
        logger = logging.getLogger("technical")
        logger.error(
            str(error),
            exc_info=error,
            extra={"user_error": str(error), **(context or {})},
        )
```

## Usage Examples

```python
from cks.utils import get_logger, log_technical_error, log_operation

# Get a logger for a module
logger = get_logger("validation")

# User-facing message (console only)
logger.info("✓ Validation complete")

# Technical operation log (file only, with context)
log_operation("rag_query", f"Retrieved {count} results", count=count, vector_ids=ids)

# Error with full traceback (file), clean message (console)
try:
    validate_compliance(entity)
except Exception as e:
    log_technical_error(e, context={"entity_id": entity.id, "validation_type": "constitutional"})
    # Console shows: ❌ ERROR: Validation failed
    # File shows: {"timestamp": "...", "exception": "Traceback...", "entity_id": "..."}
```

## Key Design Decisions

1. **DEBUG → file only**: Debug messages clutter console, always go to JSON file
2. **ERROR → both with sanitization**: Technical details in file, clean message on console
3. **Rich compatibility**: No print() in formatters - would corrupt Live displays
4. **Structured fields**: Domain-specific context (entity_id, operation) added as extra fields
5. **Rotating logs**: 50MB per file, 5 backups prevents disk bloat

## When to Use

- **CLI tools**: Users need clean output, developers need debug info
- **Long-running operations**: Progress bars + detailed audit trails
- **Rich UI applications**: Avoid display corruption from rogue logging
- **Production services**: JSON logs for parsing, console for operators

## Domain-Specific Adaptations

| Domain | Extra Fields | User Messages |
|--------|--------------|---------------|
| yt-fts | channel_id, video_id | DOWNLOAD_START, SEARCH_COMPLETE |
| CKS | entity_id, vector_op, validation_type | VALIDATION_START, RAG_QUERY_SUCCESS |
| Web API | request_id, user_id, endpoint | API_REQUEST, API_ERROR |

## Anti-Patterns to Avoid

1. **Don't use print()** - Breaks Rich Live, not captured in logs
2. **Don't log raw exceptions to console** - Users don't need stack traces
3. **Don't skip structured fields** - JSON logs need context for debugging
4. **Don't forget log rotation** - Unbounded log files fill disk
