# /// script
# requires-python = ">=3.8"
# dependencies = ["pyyaml"]
# ///
"""
Claude Code Edit Tool Damage Control
=====================================

Blocks edits to protected files via PreToolUse hook on Edit tool.
Loads zeroAccessPaths and readOnlyPaths from patterns.yaml.

Exit codes:
  0 = Allow edit
  2 = Block edit (stderr fed back to Claude)
"""

import fnmatch
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple

import yaml


def is_glob_pattern(pattern: str) -> bool:
    """Check if pattern contains glob wildcards."""
    return '*' in pattern or '?' in pattern or '[' in pattern


def normalize_case_slash(value: str) -> str:
    """Normalize slashes and case for consistent matching."""
    normalized = value.replace('\\', '/')
    if os.name == "nt":
        normalized = normalized.lower()
    return normalized


def normalize_path(value: str) -> str:
    """Normalize a filesystem path for comparisons."""
    expanded = os.path.expanduser(value)
    normalized = os.path.normpath(expanded)
    return normalize_case_slash(normalized)


def normalize_glob(value: str) -> str:
    """Normalize a glob pattern without collapsing wildcards."""
    expanded = os.path.expanduser(value)
    return normalize_case_slash(expanded)


def match_path(file_path: str, pattern: str) -> bool:
    """Match file path against pattern, supporting both prefix and glob matching."""
    if not pattern:
        return False

    if is_glob_pattern(pattern):
        normalized_path = normalize_path(file_path)
        normalized_pattern = normalize_glob(pattern)
        pattern_variants = [normalized_pattern, normalized_pattern.rstrip('/')]

        basename = os.path.basename(normalized_path)
        for candidate in pattern_variants:
            if not candidate:
                continue
            # Match against basename for patterns like *.pem, .env*
            if fnmatch.fnmatch(basename, candidate):
                return True
            # Also try full path match for patterns like /path/*.pem
            if fnmatch.fnmatch(normalized_path, candidate):
                return True
            if fnmatch.fnmatch(normalized_path + '/', candidate):
                return True
        return False
    else:
        # Prefix matching (original behavior for directories)
        normalized_path = normalize_path(file_path)
        normalized_pattern = normalize_path(pattern).rstrip('/')
        if normalized_path == normalized_pattern:
            return True
        if normalized_path.startswith(normalized_pattern + '/'):
            return True
        return False


def get_config_path() -> Path:
    """Get path to patterns.yaml, checking multiple locations."""
    # 1. Check project hooks directory (installed location)
    project_dir = os.environ.get("CLAUDE_PROJECT_DIR")
    if project_dir:
        project_config = Path(project_dir) / ".claude" / "hooks" / "damage-control" / "patterns.yaml"
        if project_config.exists():
            return project_config

    # 2. Check script's own directory (installed location)
    script_dir = Path(__file__).resolve().parent
    local_config = script_dir / "patterns.yaml"
    if local_config.exists():
        return local_config

    # 3. Check skill root directory (development location)
    skill_root = script_dir.parent.parent / "patterns.yaml"
    if skill_root.exists():
        return skill_root

    return local_config  # Default, even if it doesn't exist


def load_config() -> Dict[str, Any]:
    """Load config from YAML."""
    config_path = get_config_path()

    if not config_path.exists():
        return {"zeroAccessPaths": [], "readOnlyPaths": []}

    with open(config_path) as f:
        config = yaml.safe_load(f) or {}

    return config


def check_path(file_path: str, config: Dict[str, Any]) -> Tuple[bool, str]:
    """Check if file_path is blocked. Returns (blocked, reason)."""
    # Check zero-access paths first (no access at all)
    for zero_path in config.get("zeroAccessPaths", []):
        if match_path(file_path, zero_path):
            return True, f"zero-access path {zero_path} (no operations allowed)"

    # Check read-only paths (edits not allowed)
    for readonly in config.get("readOnlyPaths", []):
        if match_path(file_path, readonly):
            return True, f"read-only path {readonly}"

    return False, ""


def main() -> None:
    config = load_config()

    # Read hook input from stdin
    try:
        input_data = json.load(sys.stdin)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON input: {e}", file=sys.stderr)
        sys.exit(1)

    tool_name = input_data.get("tool_name", "")
    tool_input = input_data.get("tool_input", {})

    # Only check Edit and MultiEdit tools
    if tool_name not in ("Edit", "MultiEdit"):
        sys.exit(0)

    paths: List[str] = []
    if tool_name == "Edit":
        file_path = tool_input.get("file_path", "")
        if file_path:
            paths.append(file_path)
    else:
        edits = tool_input.get("edits", [])
        if isinstance(edits, list):
            for edit in edits:
                if isinstance(edit, dict):
                    edit_path = edit.get("file_path", "")
                    if edit_path:
                        paths.append(edit_path)

    if not paths:
        sys.exit(0)

    # Check if file is blocked
    for file_path in paths:
        blocked, reason = check_path(file_path, config)
        if blocked:
            print(f"SECURITY: Blocked edit to {reason}: {file_path}", file=sys.stderr)
            sys.exit(2)

    sys.exit(0)


if __name__ == "__main__":
    main()
