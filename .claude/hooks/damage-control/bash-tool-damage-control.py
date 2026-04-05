# /// script
# requires-python = ">=3.8"
# dependencies = ["pyyaml"]
# ///
"""
Claude Code Bash Tool Damage Control
====================================

Blocks dangerous Bash commands via PreToolUse hook.
Loads patterns from patterns.yaml.

Exit codes:
  0 = Allow command
  2 = Block command (stderr fed back to Claude)
"""

import json
import os
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple

import yaml

# ============================================================================
# PATH NORMALIZATION (Windows-aware)
# ============================================================================

def normalize_path_for_matching(path: str) -> str:
    r"""Normalize path for case-insensitive, slash-agnostic matching.

    On Windows: P:/, p:/, P:\, p:\ all become the same normalized pattern.
    On Unix: preserves original behavior (case-sensitive).
    """
    # Convert backslashes to forward slashes for consistent matching
    normalized = path.replace('\\', '/')
    return normalized


def escape_for_regex(path: str) -> str:
    """Escape path for regex while maintaining flexible matching.

    Creates a pattern that matches the path with:
    - Case-insensitive matching (for Windows)
    - Either forward or backward slashes
    """
    normalized = normalize_path_for_matching(path)
    # Escape special regex characters
    escaped = re.escape(normalized)
    # Replace escaped slashes with a character class that matches either slash
    escaped = escaped.replace('/', '[/\\\\]')
    return escaped


# ============================================================================
# GLOB PATTERN HANDLING
# ============================================================================

def is_glob_pattern(pattern: str) -> bool:
    """Check if pattern contains glob wildcards."""
    return '*' in pattern or '?' in pattern or '[' in pattern


def glob_to_regex(glob_pattern: str) -> str:
    """Convert a glob pattern to a regex pattern.

    Handles:
    - * -> matches any characters (except slash)
    - ? -> matches single character
    - [abc] -> character class
    """
    normalized = normalize_path_for_matching(glob_pattern)
    # Escape special regex characters except glob wildcards
    regex = ''
    for i, char in enumerate(normalized):
        if char == '*':
            # * matches any sequence (including slashes for destructive patterns)
            regex += '.*'
        elif char == '?':
            regex += '.'
        elif char == '/':
            regex += r'[/\\]'
        elif char == '[':
            # Find the closing bracket
            j = normalized.find(']', i)
            if j != -1:
                regex += normalized[i:j+1]
                i = j
            else:
                regex += '\\['
        else:
            regex += re.escape(char)
    return regex


def has_shell_separators(command: str) -> bool:
    """Detect shell separators that chain commands."""
    return bool(re.search(r'(&&|&|\|\||\||;|\r|\n)', command))


def matches_allowlist(command: str, allow_patterns: List[Dict[str, Any]]) -> bool:
    """Return True if command matches an allowlist regex."""
    for item in allow_patterns:
        pattern = item.get("pattern", "")
        if not pattern:
            continue
        try:
            if re.search(pattern, command, re.IGNORECASE):
                return True
        except re.error:
            continue
    return False


# ============================================================================
# COMMAND PATTERNS FOR PATH PROTECTION
# ============================================================================

# These patterns are used to check if a command targets a protected path
WRITE_PATTERNS = [
    (r'\becho\s+.*{path}', "write"),
    (r'\bprintf\s+.*{path}', "write"),
    (r'\bcat\s+.*{path}', "write"),
]

APPEND_PATTERNS = [
    (r'\btee\s+.*(-a\s+|\s*>>)\s*{path}', "append"),
    (r'>>\s*{path}', "append"),
]

EDIT_PATTERNS = [
    (r'\bnano\s+.*{path}', "edit"),
    (r'\bvi\s+.*{path}', "edit"),
    (r'\bvim\s+.*{path}', "edit"),
    (r'\bcode\s+.*{path}', "edit"),
]

MOVE_COPY_PATTERNS = [
    (r'\bmv\s+.*{path}', "move"),
    (r'\bcp\s+.*{path}', "copy"),
]

DELETE_PATTERNS = [
    (r'\brm\s+.*{path}', "delete"),
    (r'\bunlink\s+.*{path}', "delete"),
    (r'\brmdir\s+.*{path}', "delete"),
    (r'\bshred\s+.*{path}', "delete"),
    # PowerShell delete commands
    (r'\bRemove-Item\s+.*{path}', "delete"),
    (r'\bri\s+.*{path}', "delete"),
    (r'\bdel\s+.*{path}', "delete"),
    (r'\berase\s+.*{path}', "delete"),
]

PERMISSION_PATTERNS = [
    (r'\bchmod\s+.*{path}', "chmod"),
    (r'\bchown\s+.*{path}', "chown"),
    (r'\bchgrp\s+.*{path}', "chgrp"),
]

TRUNCATE_PATTERNS = [
    (r'\btruncate\s+.*{path}', "truncate"),
    (r':\s*>\s*{path}', "truncate"),
]

# Combined patterns for read-only paths (block ALL modifications)
READ_ONLY_BLOCKED = (
    WRITE_PATTERNS +
    APPEND_PATTERNS +
    EDIT_PATTERNS +
    MOVE_COPY_PATTERNS +
    DELETE_PATTERNS +
    PERMISSION_PATTERNS +
    TRUNCATE_PATTERNS
)

# Patterns for no-delete paths (block ONLY delete operations)
NO_DELETE_BLOCKED = DELETE_PATTERNS


# ============================================================================
# CONFIGURATION LOADING
# ============================================================================

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
    """Load patterns from YAML config file."""
    config_path = get_config_path()

    if not config_path.exists():
        print(f"Warning: Config not found at {config_path}", file=sys.stderr)
        return {"bashToolPatterns": [], "zeroAccessPaths": [], "readOnlyPaths": [], "noDeletePaths": []}

    with open(config_path) as f:
        return yaml.safe_load(f) or {}


# ============================================================================
# PATH CHECKING
# ============================================================================

def check_path_patterns(command: str, path: str, patterns: List[Tuple[str, str]], path_type: str) -> Tuple[bool, str]:
    """Check command against a list of patterns for a specific path.

    Supports both:
    - Literal paths: ~/.bashrc, /etc/hosts (prefix matching)
    - Glob patterns: *.lock, *.md, src/* (glob matching)
    """
    if is_glob_pattern(path):
        # Glob pattern - convert to regex for command matching
        glob_regex = glob_to_regex(path)
        for pattern_template, operation in patterns:
            # For glob patterns, we check if the operation + glob appears in command
            # e.g., "rm *.lock" should match DELETE_PATTERNS with *.lock
            try:
                # Build a regex that matches: operation ... glob_pattern
                # Extract the command prefix from pattern_template (e.g., '\brm\s+.*' from '\brm\s+.*{path}')
                cmd_prefix = pattern_template.replace("{path}", "")
                if cmd_prefix and re.search(cmd_prefix + glob_regex, command, re.IGNORECASE):
                    return True, f"Blocked: {operation} operation on {path_type} {path}"
            except re.error:
                continue
    else:
        # Original literal path matching (prefix-based)
        # Use flexible path matching that handles case and slash variations
        path_pattern = escape_for_regex(path)

        # Also check expanded form for ~ paths
        expanded = os.path.expanduser(path)
        expanded_pattern = escape_for_regex(expanded)

        for pattern_template, operation in patterns:
            # Check both original and expanded path forms with case-insensitive matching
            cmd_with_path = pattern_template.replace("{path}", path_pattern)
            cmd_with_expanded = pattern_template.replace("{path}", expanded_pattern)

            try:
                if re.search(cmd_with_path, command, re.IGNORECASE) or re.search(cmd_with_expanded, command, re.IGNORECASE):
                    return True, f"Blocked: {operation} operation on {path_type} {path}"
            except re.error:
                continue

    return False, ""



def appears_as_filepath(command: str, pattern: str) -> bool:
    """Check if pattern appears as a filepath in command, not as code/substring.

    A filepath pattern should be preceded by:
    - Whitespace/command start
    - File operation characters (>, <, |, quotes)
    
    And NOT be part of a larger identifier like:
    - json.dumps()  <- function call
    - module.dump   <- attribute access
    """
    # Build regex that matches pattern as filepath boundary
    # Look for pattern preceded by filepath indicators, not by '.' (attribute access)
    # or '(' (function call suffix)

    # Escape the pattern for regex
    escaped = re.escape(pattern.lstrip('*'))  # Remove leading * for matching

    # Pattern should be at filepath boundary:
    # - After space, start of line, or special chars: > < | " ' ( [ ]
    # - NOT after a dot (attribute access) or directly after '(' (function call)

    # For *.dump patterns, match "something.dump" but not "json.dumps("
    filepath_regex = r'(?<![.\w])([\w/\-.' + r'"]*' + escaped + r')(?![\w(])'

    # Simpler: ensure pattern isn't preceded by '.' or '(' (function/attribute)
    # and isn't followed by '(' (function call)
    lookbehind = r'(?<![.(])'  # Not after . or (
    lookahead = r'(?![\w(])'   # Not followed by word char or (

    try:
        regex = lookbehind + r'[\w/\-."]*' + escaped + lookahead
        return bool(re.search(regex, command))
    except re.error:
        # Fallback to simple search if regex fails
        return pattern in command


def check_command(command: str, config: Dict[str, Any]) -> Tuple[bool, bool, str]:
    """Check if command should be blocked or requires confirmation.

    Returns: (blocked, ask, reason)
      - blocked=True, ask=False: Block the command
      - blocked=False, ask=True: Show confirmation dialog
      - blocked=False, ask=False: Allow the command
    """
    allow_command_patterns = config.get("allowCommandPatterns", [])
    patterns = config.get("bashToolPatterns", [])
    zero_access_paths = config.get("zeroAccessPaths", [])
    read_only_paths = config.get("readOnlyPaths", [])
    no_delete_paths = config.get("noDeletePaths", [])

    # 0. Allowlist narrow, explicit commands (block if chained)
    if allow_command_patterns:
        if has_shell_separators(command):
            if matches_allowlist(command, allow_command_patterns):
                return True, False, (
                    "Blocked: index.lock cleanup must be a single command (no chaining).\n"
                    "Run:\n"
                    "- rm -f P:/.git/index.lock\n"
                    "- Then git add ... / git commit ..."
                )
        elif matches_allowlist(command, allow_command_patterns):
            return False, False, ""

    # 1. Check against patterns from YAML (may block or ask)
    for item in patterns:
        pattern = item.get("pattern", "")
        reason = item.get("reason", "Blocked by pattern")
        should_ask = item.get("ask", False)

        try:
            if re.search(pattern, command, re.IGNORECASE):
                if should_ask:
                    return False, True, reason  # Ask for confirmation
                else:
                    return True, False, f"Blocked: {reason}"  # Block
        except re.error:
            continue

    # 2. Check for ANY access to zero-access paths (including reads)
    for zero_path in zero_access_paths:
        if is_glob_pattern(zero_path):
            # For glob patterns, check if pattern appears as filepath (not code)
            # This prevents false positives like blocking json.dumps() when *.dump is configured
            if appears_as_filepath(command, zero_path):
                return True, False, f"Blocked: zero-access pattern {zero_path} (no operations allowed)"
        else:
            # Non-glob paths: use flexible path matching for zero-access paths
            path_pattern = escape_for_regex(zero_path)
            expanded = os.path.expanduser(zero_path)
            expanded_pattern = escape_for_regex(expanded)

            try:
                if re.search(path_pattern, command, re.IGNORECASE) or re.search(expanded_pattern, command, re.IGNORECASE):
                    return True, False, f"Blocked: zero-access path {zero_path} (no operations allowed)"
            except re.error:
                continue

    # 3. Check for modifications to read-only paths (reads allowed)
    for readonly in read_only_paths:
        blocked, reason = check_path_patterns(command, readonly, READ_ONLY_BLOCKED, "read-only path")
        if blocked:
            return True, False, reason

    # 4. Check for deletions on no-delete paths (read/write/edit allowed)
    for no_delete in no_delete_paths:
        blocked, reason = check_path_patterns(command, no_delete, NO_DELETE_BLOCKED, "no-delete path")
        if blocked:
            return True, False, reason

    return False, False, ""


# ============================================================================
# MAIN
# ============================================================================

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

    # Only process Bash tool
    if tool_name != "Bash":
        sys.exit(0)

    command = tool_input.get("command", "")
    if not command:
        sys.exit(0)

    # Check if command should be blocked
    blocked, ask, reason = check_command(command, config)

    if blocked:
        print(f"SECURITY: {reason}\nCommand: {command}", file=sys.stderr)
        sys.exit(2)
    elif ask:
        ask_mode = os.environ.get("DAMAGE_CONTROL_ASK_MODE", "block").lower()
        if ask_mode == "ask":
            ask_response = {
                "permissionDecision": "ask",
                "permissionDecisionReason": f"{reason}\n\nCommand: {command}",
            }
            print(json.dumps(ask_response))
            sys.exit(0)
        print(f"SECURITY: Blocked (ask disabled): {reason}\nCommand: {command}", file=sys.stderr)
        sys.exit(2)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
