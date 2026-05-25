#!/usr/bin/env python3
"""PreToolUse_type_validator - Block type mismatches at write-time.

Blocks .py files at workspace root to prevent type-mismatch violations.
Detects double-extension bypass (e.g. malware.py.txt) by checking all filename segments.
Fail-closed on policy errors, fail-open on transient errors.
"""
from __future__ import annotations


# --- plugin bootstrap ---
import sys as _s; from pathlib import Path as _P

def _normalize_stdout(data: dict) -> dict:
    """Normalize hook output to Claude Code Zod-valid schema."""
    if data.get('decision') == 'allow':
        return {'decision': 'approve'}
    if data.get('decision') == 'block':
        return {'decision': 'block', 'reason': data.get('reason', '')}
    if 'allow' in data:
        if data['allow'] is False:
            return {'decision': 'block', 'reason': data.get('reason', '')}
        return {'decision': 'approve'}
    if 'continue' in data:
        if data['continue'] is False:
            return {'decision': 'block', 'reason': data.get('reason', '')}
        return {'decision': 'approve'}
    if 'ok' in data:
        return {'decision': 'approve'}
    return data


_l = _P(__file__).resolve().parent.parent.parent / "__lib"
if str(_l) not in _s.path: _s.path.insert(0, str(_l))
from _bootstrap import bootstrap; _hooks_dir = bootstrap(__file__)
# --- end bootstrap ---


import json
import os
import sys
from pathlib import Path

# Add hooks dir to path for imports
hooks_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, hooks_dir)
sys.path.insert(0, os.path.join(hooks_dir, "__lib"))

from type_validator import get_file_category

POLICY_PATH = "P:/.claude/hooks/config/directory_policy.json"

# Code extensions that should be blocked at workspace root
# (double-extension bypass detection)
CODE_EXTENSIONS = frozenset({
    ".py", ".pyi", ".pyc", ".pyo", ".pyw",
    ".js", ".mjs", ".cjs",
    ".exe", ".bat", ".ps1", ".sh", ".bash",
    ".rb", ".go", ".rs", ".java", ".cpp", ".c", ".h",
})


def _get_workspace_root() -> str:
    """Get the workspace root path."""
    return "P:/"


def _load_policy() -> dict:
    """Load directory_policy.json. Returns empty dict on failure."""
    try:
        with open(POLICY_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError):
        return {}


def _get_allowed_config_extensions(policy: dict) -> set[str]:
    """Extract allowed config file extensions from policy."""
    ws_root = policy.get("workspace_root", {})
    allowed = ws_root.get("allowed_config_files", [])
    # Build extension set from allowed entries
    exts = set()
    for entry in allowed:
        if entry.startswith("."):
            exts.add(entry.lower())
        elif "." in entry:
            ext = "." + entry.split(".")[-1]
            exts.add(ext.lower())
    return exts


def _has_code_extension_in_segments(filename: str) -> bool:
    """Check if any filename segment (except last) is a code extension.

    For double-extension bypass detection:
    - 'malware.py.txt' -> segments ['malware', 'py', 'txt'] -> 'py' in CODE_EXTENSIONS -> True
    - 'script.py.config' -> segments ['script', 'py', 'config'] -> 'py' in CODE_EXTENSIONS -> True
    - 'document.txt' -> segments ['document', 'txt'] -> 'txt' not in CODE_EXTENSIONS -> False

    Algorithm: Split the full filename by '.' and check all segments except
    the last (the extension). Any segment matching a code extension = block.
    """
    path = Path(filename)
    name = path.name
    if "." not in name:
        return False
    # Split the full name by '.' - all segments except last are "interior"
    segments = name.split(".")
    # Check all segments except the last (which is the extension)
    for seg in segments[:-1]:
        if f".{seg.lower()}" in CODE_EXTENSIONS:
            return True
    return False


def _is_in_hooks_dir(file_path: str) -> bool:
    """Check if file path is inside the hooks directory."""
    try:
        hooks_abs = Path(hooks_dir).resolve()
        file_abs = Path(file_path).resolve()
        # Check if file is under hooks directory
        return hooks_abs in file_abs.parents or file_abs == hooks_abs
    except (OSError, ValueError):
        return False


def check_type_mismatch(file_path: str) -> dict:
    """Check if a file operation would cause a type mismatch violation.

    Returns:
        dict with 'continue' (bool) and 'reason' (str)
    """
    path_obj = Path(file_path)
    filename = path_obj.name

    # Load policy
    policy = _load_policy()
    if not policy:
        # Fail-closed on policy error (missing/invalid policy)
        return {
            "continue": False,
            "reason": "TYPE MISMATCH: Policy load failed - blocking for safety. "
                     "Cannot verify file type without valid policy.",
            "terminal_id": os.environ.get("CLAUDE_TERMINAL_ID", "unknown"),
            "session_id": os.environ.get("CLAUDE_SESSION_ID", "unknown"),
        }

    # Load allowed config extensions
    allowed_exts = _get_allowed_config_extensions(policy)

    workspace_root = _get_workspace_root()

    # Check if file is at workspace root
    try:
        path_abs = Path(file_path).resolve()
        root_abs = Path(workspace_root).resolve()
        is_at_root = path_abs == root_abs or (
            str(path_abs.parent).replace("\\", "/") == str(root_abs).replace("\\", "/")
        )
    except (OSError, ValueError):
        # Fail-open on transient path resolution error
        return {
            "continue": True,
            "reason": "TYPE MISMATCH (transient): Could not resolve path - allowing temporarily.",
        }

    if not is_at_root:
        # Not at root, allow
        return {"continue": True}

    # Special case: .md files in hooks dir are standard, allow
    if filename.endswith(".md") and _is_in_hooks_dir(file_path):
        return {"continue": True}

    # Check for code extension at root
    file_category = get_file_category(file_path)
    suffix = path_obj.suffix.lower()
    has_code_ext = suffix in CODE_EXTENSIONS
    has_code_in_segments = _has_code_extension_in_segments(filename)

    # Block: direct code extension at root (e.g. script.py)
    if has_code_ext:
        allowed_exts_display = ", ".join(sorted(allowed_exts)) if allowed_exts else ".toml, .cfg, .json, etc."
        return {
            "continue": False,
            "reason": f"TYPE MISMATCH: {filename} is a {file_category} file, not a config file.\n\n"
                     f"Config files at this location: {allowed_exts_display}\n"
                     f"Suggested location: .claude/hooks/ (for Python files)",
            "terminal_id": os.environ.get("CLAUDE_TERMINAL_ID", "unknown"),
            "session_id": os.environ.get("CLAUDE_SESSION_ID", "unknown"),
        }

    # Block: double-extension bypass (e.g. malware.py.txt)
    if has_code_in_segments:
        return {
            "continue": False,
            "reason": f"TYPE MISMATCH: {filename} is a double-extension file (code extension in filename segments), not a config file.\n\n"
                     f"Suggested location: .claude/hooks/ (for Python files)",
            "terminal_id": os.environ.get("CLAUDE_TERMINAL_ID", "unknown"),
            "session_id": os.environ.get("CLAUDE_SESSION_ID", "unknown"),
        }

    # Allow non-code files at root
    return {"continue": True}


def main() -> None:
    """Read hook input from stdin, check type mismatch, write result to stdout."""
    try:
        data = json.load(sys.stdin)
    except (json.JSONDecodeError, OSError):
        # Fail-open on transient stdin error
        print(json.dumps({"decision": "approve"}))
        return

    tool_name = data.get("tool_name", "")
    if tool_name not in ("Write", "Edit"):
        print(json.dumps({"decision": "approve"}))
        return

    tool_input = data.get("tool_input", {})
    file_path = tool_input.get("file_path", "")

    if not file_path:
        print(json.dumps({"decision": "approve"}))
        return

    result = check_type_mismatch(file_path)
    print(json.dumps(_normalize_stdout(result)))


if __name__ == "__main__":
    main()
