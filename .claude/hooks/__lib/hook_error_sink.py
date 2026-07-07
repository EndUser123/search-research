"""Unified hook error sink.

All hook __main__ entry points call log_hook_error() on unexpected exceptions
so that errors surface in importer_diagnostics (the authoritative SQLite sink)
rather than disappearing into Claude Code's UI with no persistent record.

Usage in any hook's __main__ block:
    from hook_error_sink import log_hook_error
    try:
        main()
    except SystemExit:
        raise
    except Exception as e:
        import traceback
        log_hook_error(__file__, str(e), traceback.format_exc())
        sys.exit(1)
"""

from __future__ import annotations

import json
import os
import sys
from datetime import UTC, datetime
from pathlib import Path

_FALLBACK_LOG = (
    Path(__file__).resolve().parent.parent
    / "logs" / "diagnostics" / "hook_errors.jsonl"
)


def log_hook_error(
    hook_file: str,
    error_text: str,
    traceback_text: str | None = None,
    session_id: str | None = None,
) -> None:
    """Write a hook runtime error to importer_diagnostics, falling back to JSONL."""
    hook_name = Path(hook_file).name
    ts = datetime.now(UTC).isoformat()

    # Attempt SQLite via cc_diagnostic_logger
    try:
        _lib = Path(__file__).resolve().parent
        if str(_lib) not in sys.path:
            sys.path.insert(0, str(_lib))
        from cc_diagnostic_logger import log_importer_anomaly
        log_importer_anomaly(
            hook_name=hook_name,
            phase="execute",
            error_text=error_text,
            session_id=session_id or os.environ.get("CLAUDE_SESSION_ID"),
            terminal_id=os.environ.get("CLAUDE_TERMINAL_ID"),
            tool_name=None,
            input_hash=None,
            input_bytes=None,
            traceback_text=traceback_text,
        )
        return
    except Exception:
        pass

    # Fallback: append to JSONL
    try:
        _FALLBACK_LOG.parent.mkdir(parents=True, exist_ok=True)
        entry = {
            "ts": ts,
            "hook_name": hook_name,
            "phase": "execute",
            "error_text": error_text[:1000],
            "traceback": (traceback_text or "")[-1000:],
            "session_id": session_id or os.environ.get("CLAUDE_SESSION_ID"),
        }
        from file_lock import append_jsonl_safe
        append_jsonl_safe(_FALLBACK_LOG, entry)
    except OSError:
        pass
