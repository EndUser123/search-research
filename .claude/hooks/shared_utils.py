#!/usr/bin/env python3
from __future__ import annotations

"""
CSF Hook Shared Utilities

Shared state management, logging, and utility functions for all enforcement hooks.
"""

import hashlib
import json
import os
import re
import threading
from datetime import datetime
from pathlib import Path

# === PATHS ===
STATE_DIR = Path(os.environ.get("CSF_STATE_DIR", "P:/.claude/state"))
LOG_DIR = Path(os.environ.get("CSF_LOG_DIR", "P:/.claude/logs"))
CONFIG_FILE = Path(os.environ.get("CSF_CONFIG_FILE", str(Path(__file__).resolve().parent / "config.json")))

# === BUFFERED I/O ===
_write_buffer = {}
_write_lock = threading.Lock()
_buffer_size = 10  # Flush after 10 writes or explicit flush

# === STATE MANAGEMENT ===

def ensure_dirs():
    """Ensure state and log directories exist."""
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)

def load_state(hook_name: str) -> dict:
    """Load state for a specific hook.

    SECURITY: Refuses to follow symlinks to prevent symlink attacks (SEC-001).
    """
    ensure_dirs()

    # Check buffer first
    with _write_lock:
        if hook_name in _write_buffer:
            return _write_buffer[hook_name].copy()

    state_file = STATE_DIR / f"{hook_name}_state.json"
    # SECURITY: Do not follow symlinks (prevents symlink attacks)
    if state_file.exists() and not state_file.is_symlink():
        try:
            with open(state_file) as f:
                return json.load(f)
        except (OSError, json.JSONDecodeError):
            return {}
    return {}

def save_state(hook_name: str, state: dict, buffered: bool = True):
    """Save state for a specific hook."""
    ensure_dirs()
    state["_updated"] = datetime.now().isoformat()

    if buffered:
        with _write_lock:
            _write_buffer[hook_name] = state
            if len(_write_buffer) >= _buffer_size:
                _flush_state_buffer()
    else:
        _save_state_immediate(hook_name, state)

def _save_state_immediate(hook_name: str, state: dict):
    """Write state to disk immediately.

    SECURITY: Refuses to write if target is a symlink (SEC-001).
    """
    state_file = STATE_DIR / f"{hook_name}_state.json"
    # SECURITY: Do not write to symlinks (prevents symlink attacks)
    if state_file.exists() and state_file.is_symlink():
        # Silently skip writing to symlinked files (security measure)
        return
    try:
        with open(state_file, "w") as f:
            json.dump(state, f, indent=2, default=str)
    except OSError:
        pass

def _flush_state_buffer():
    """Flush all buffered state writes."""
    global _write_buffer
    for name, state in _write_buffer.items():
        _save_state_immediate(name, state)
    _write_buffer.clear()

def flush_all_states():
    """Flush all pending state writes (call before exit)."""
    with _write_lock:
        _flush_state_buffer()

def clear_state(hook_name: str):
    """Clear state for a specific hook.

    SECURITY: Refuses to delete symlinks to prevent accidental data loss (SEC-001).
    """
    state_file = STATE_DIR / f"{hook_name}_state.json"
    # SECURITY: Do not delete symlinks (may target important files)
    if state_file.exists() and not state_file.is_symlink():
        state_file.unlink()

def clear_all_states():
    """Clear all hook states (new session).

    SECURITY: Refuses to delete symlinks to prevent accidental data loss (SEC-001).
    """
    ensure_dirs()
    for state_file in STATE_DIR.glob("*_state.json"):
        # SECURITY: Do not delete symlinks (may target important files)
        if not state_file.is_symlink():
            state_file.unlink()

def get_all_states() -> dict[str, dict]:
    """Load all hook states.

    SECURITY: Refuses to follow symlinks to prevent symlink attacks (SEC-001).
    """
    ensure_dirs()
    states = {}
    for state_file in STATE_DIR.glob("*_state.json"):
        # SECURITY: Do not follow symlinks
        if state_file.is_symlink():
            continue
        hook_name = state_file.stem.replace("_state", "")
        try:
            with open(state_file) as f:
                states[hook_name] = json.load(f)
        except (OSError, json.JSONDecodeError):
            states[hook_name] = {}
    return states

# === LOGGING ===

def log_hook_event(hook_name: str, event_type: str, data: dict):
    """Log a hook event for observability."""
    ensure_dirs()
    log_file = LOG_DIR / f"hooks_{datetime.now().strftime('%Y%m%d')}.jsonl"

    entry = {
        "timestamp": datetime.now().isoformat(),
        "hook": hook_name,
        "event": event_type,
        "data": data
    }

    with open(log_file, "a") as f:
        f.write(json.dumps(entry) + "\n")

def get_recent_logs(hook_name: str | None = None, limit: int = 50) -> list[dict]:
    """Get recent log entries, optionally filtered by hook."""
    ensure_dirs()
    entries = []

    # Get today's and yesterday's logs
    for days_ago in range(2):
        date = datetime.now()
        if days_ago > 0:
            from datetime import timedelta
            date = date - timedelta(days=days_ago)

        log_file = LOG_DIR / f"hooks_{date.strftime('%Y%m%d')}.jsonl"
        if log_file.exists():
            with open(log_file) as f:
                for line in f:
                    try:
                        entry = json.loads(line.strip())
                        if hook_name is None or entry.get("hook") == hook_name:
                            entries.append(entry)
                    except json.JSONDecodeError:
                        pass

    # Sort by timestamp descending, limit
    entries.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
    return entries[:limit]

# === CONFIGURATION ===

def load_config() -> dict:
    """Load hook configuration."""
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE) as f:
                return json.load(f)
        except (OSError, json.JSONDecodeError):
            return default_config()
    return default_config()

def default_config() -> dict:
    return {
        "hooks": {
            "investigation_gate": {"enabled": True, "min_reads": 1},
            "failure_escalation": {"enabled": True, "max_failures": 2, "cooldown_minutes": 30},
            "concern_detection": {"enabled": True},
            "change_propagation": {"enabled": True},
            "success_validator": {"enabled": True, "mode": "warn"}
        },
        "global": {
            "debug": False,
            "log_all_events": False,
            "session_timeout_hours": 2
        }
    }

def save_config(config: dict):
    """Save hook configuration."""
    CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=2)

def safe_json_load(file_path: Path | str, default: dict | None = None) -> dict:
    """Safely load JSON file with error handling.

    Provides consistent error handling for JSON loading across all hooks.
    Handles OSError (file not found, permissions) and json.JSONDecodeError
    (malformed JSON).

    Args:
        file_path: Path to JSON file
        default: Default value to return on error (default: empty dict)

    Returns:
        Parsed JSON dict, or default if loading fails

    Example:
        data = safe_json_load("state.json")
        config = safe_json_load("config.json", default={"enabled": True})
    """
    if default is None:
        default = {}

    path = Path(file_path)
    if not path.exists():
        return default

    try:
        with open(path, encoding='utf-8') as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError):
        return default

# === SESSION MANAGEMENT ===

def get_session_id() -> str:
    """Generate/retrieve current session ID."""
    session_file = STATE_DIR / "current_session.txt"

    if session_file.exists():
        session_id = session_file.read_text().strip()
        # Check if session is still valid (within timeout)
        states = get_all_states()
        for state in states.values():
            if state.get("session_start"):
                age_hours = (datetime.now().timestamp() - state["session_start"]) / 3600
                config = load_config()
                timeout = config.get("global", {}).get("session_timeout_hours", 2)
                if age_hours < timeout:
                    return session_id

    # Generate new session
    session_id = hashlib.md5(
        f"{datetime.now().isoformat()}{os.getpid()}".encode()
    ).hexdigest()[:12]

    session_file.parent.mkdir(parents=True, exist_ok=True)
    session_file.write_text(session_id)

    # Clear old states
    clear_all_states()

    return session_id

def new_session():
    """Force start a new session."""
    session_file = STATE_DIR / "current_session.txt"
    if session_file.exists():
        session_file.unlink()
    clear_all_states()
    return get_session_id()

# === UTILITIES ===

def is_hook_enabled(hook_name: str) -> bool:
    """Check if a specific hook is enabled."""
    config = load_config()
    hook_config = config.get("hooks", {}).get(hook_name, {})
    return hook_config.get("enabled", True)

def get_hook_config(hook_name: str) -> dict:
    """Get configuration for a specific hook."""
    config = load_config()
    return config.get("hooks", {}).get(hook_name, {})

def format_duration(seconds: float) -> str:
    """Format a duration in seconds to human-readable."""
    if seconds < 60:
        return f"{seconds:.0f}s"
    elif seconds < 3600:
        return f"{seconds/60:.0f}m"
    else:
        return f"{seconds/3600:.1f}h"

def validate_path(path: Path | str) -> bool:
    """
    Validate path is well-formed.

    Blocks malformed paths like 'P:__csf' (drive letter without separator).

    Args:
        path: Path to validate

    Returns:
        True if path is valid

    Raises:
        ValueError: If path is malformed
    """
    path_str = str(path).replace("\\", "/")

    # Malformed: drive letter followed immediately by non-separator
    # Examples: "P:__csf", "C:foo/bar"
    if re.match(r'^[A-Za-z]:[^/]', path_str):
        raise ValueError(
            f"Malformed path: '{path}'. "
            f"Drive-letter paths must use separator after colon (e.g., 'P:/' not 'P:'). "
            f"Got: {path_str}"
        )

    return True

def resolve_session_id(data: dict) -> str:
    """Resolve session ID from hook payload with fallback chain.

    Checks multiple key variants in priority order:
    1. Nested session object (id, session_id, sessionId)
    2. Flat payload keys (session_id, sessionId, conversation_id, conversationId)
    3. Environment variable (CLAUDE_SESSION_ID)

    Args:
        data: Hook input payload dict

    Returns:
        Session ID string, or empty string if not found
    """
    # Check nested session object first (Claude Code may nest it)
    session_obj = data.get("session")
    if isinstance(session_obj, dict):
        for key in ("id", "session_id", "sessionId"):
            value = session_obj.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()

    # Check flat payload keys
    for key in ("session_id", "sessionId", "conversation_id", "conversationId"):
        value = data.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()

    # Fallback to environment variable
    env_value = os.environ.get("CLAUDE_SESSION_ID", "").strip()
    return env_value


# === CLI ===

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="CSF Hook Utilities")
    parser.add_argument("command", choices=[
        "status", "clear", "logs", "config", "new-session"
    ])
    parser.add_argument("--hook", help="Specific hook name")
    parser.add_argument("--limit", type=int, default=20, help="Log entry limit")

    args = parser.parse_args()

    if args.command == "status":
        states = get_all_states()
        session = get_session_id()
        print(f"Session: {session}")
        print(f"States: {len(states)}")
        for name, state in states.items():
            updated = state.get("_updated", "unknown")
            print(f"  {name}: updated {updated}")

    elif args.command == "clear":
        if args.hook:
            clear_state(args.hook)
            print(f"Cleared {args.hook} state")
        else:
            clear_all_states()
            print("Cleared all states")

    elif args.command == "logs":
        logs = get_recent_logs(args.hook, args.limit)
        for entry in logs:
            print(f"[{entry['timestamp']}] {entry['hook']}: {entry['event']}")

    elif args.command == "config":
        config = load_config()
        print(json.dumps(config, indent=2))

    elif args.command == "new-session":
        session = new_session()
        print(f"New session: {session}")
