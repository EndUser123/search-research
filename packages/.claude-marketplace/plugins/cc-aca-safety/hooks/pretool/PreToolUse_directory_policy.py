#!/usr/bin/env python3
from __future__ import annotations

# --- plugin bootstrap ---
import sys
from pathlib import Path
_l = Path(__file__).resolve().parent.parent.parent / "__lib"
if str(_l) not in sys.path: sys.path.insert(0, str(_l))
from _bootstrap import bootstrap; _hooks_dir = bootstrap(__file__)
# --- end bootstrap ---


"""
Directory Policy Enforcement Hook
==================================
Comprehensive enforcement of directory_policy.json:
- External path consent validation
- CSF NIP path validation
- General path validation (root, patterns, blocked paths)
- Content size checks
"""

import fnmatch
import json
import logging
import os
import re
import logging as _li

_POLICY_DIR = Path(__file__).resolve().parent
_LOG_DIR = Path("P:/") / ".claude" / "logs" / "diagnostics"
_LOG_DIR.mkdir(parents=True, exist_ok=True)
_logger = _li.getLogger(__name__)
_handler = _li.FileHandler(_LOG_DIR / "hook_stderr.log", encoding="utf-8")
_handler.setFormatter(_li.Formatter("%(asctime)s %(levelname)s %(message)s"))
_logger.addHandler(_handler)
_logger.setLevel(_li.WARNING)

import sys
import threading
import time
from typing import Any

# Import specialized modules from local hooks directory
hooks_dir = os.path.dirname(os.path.abspath(__file__))
if hooks_dir not in sys.path:
    sys.path.insert(0, hooks_dir)

hooks_lib = os.path.join(hooks_dir, "__lib")
if hooks_lib not in sys.path:
    sys.path.insert(0, hooks_lib)

# Import auto-logging decorator after path bootstrap so __lib is resolvable
try:
    from __lib.hook_base import hook_main
except ImportError:
    from hook_base import hook_main  # type: ignore

from pathlib import Path as PathLib

try:
    from __lib.path_validator import PathValidator
except ImportError:
    from path_validator import PathValidator  # type: ignore
from violation_reporter import ViolationReporter

# CSF NIP path validation (optional)
try:
    from csf_nip_deny_violations import format_violation_message as csf_format_violation
    from csf_nip_path_validator import CSFNIPPathValidator

    CSF_NIP_AVAILABLE = True
except ImportError:
    CSF_NIP_AVAILABLE = False

ALLOWED_EXTERNAL_PATTERNS: list[str] = []
ALLOWED_EXTERNAL_EXACT_PATHS: list[str] = []
# Thread safety lock for ALLOWED_EXTERNAL_PATTERNS access in multi-terminal environments
# Module-level globals without locks are a concurrency anti-pattern
_ALLOWED_EXTERNAL_PATTERNS_LOCK = threading.Lock()

# Telemetry tracking for monitoring
_lock_contention_count = 0
_lock_wait_total = 0.0
_fallback_count = 0
_lock = threading.Lock()


# JSON schema for directory_policy.json validation
def _validate_directory_policy_schema(policy: dict, policy_path: str) -> list[str]:
    """Validate directory_policy.json structure.

    Returns list of error messages (empty if valid).
    """
    errors = []

    def validate_path(value: Any, path: str) -> None:
        if not isinstance(value, str):
            errors.append(f"{path}: must be string, got {type(value).__name__}")
        elif not value:
            errors.append(f"{path}: cannot be empty string")

    # Check allowed_external_paths.patterns
    if "allowed_external_paths" in policy:
        external = policy["allowed_external_paths"]
        if not isinstance(external, dict):
            errors.append("allowed_external_paths: must be object")
        else:
            if "patterns" in external:
                patterns = external["patterns"]
                if not isinstance(patterns, list):
                    errors.append("allowed_external_paths.patterns: must be array")
                else:
                    for i, pattern in enumerate(patterns):
                        validate_path(pattern, f"allowed_external_paths.patterns[{i}]")

    # Check claude_restricted_paths
    if "claude_restricted_paths" in policy:
        restricted = policy["claude_restricted_paths"]
        if not isinstance(restricted, dict):
            errors.append("claude_restricted_paths: must be object")
        else:
            paths = restricted.get("paths", [])
            if not isinstance(paths, list):
                errors.append("claude_restricted_paths.paths: must be array")
            else:
                for i, entry in enumerate(paths):
                    if isinstance(entry, dict):
                        path_val = entry.get("path")
                        validate_path(path_val, f"claude_restricted_paths.paths[{i}].path")
                    else:
                        validate_path(entry, f"claude_restricted_paths.paths[{i}]")

    # Check blocked_paths
    if "blocked_paths" in policy:
        blocked = policy["blocked_paths"]
        if not isinstance(blocked, list):
            errors.append("blocked_paths: must be array")
        else:
            for i, path in enumerate(blocked):
                validate_path(path, f"blocked_paths[{i}]")

    # Check allowed_config_files
    if "allowed_config_files" in policy:
        allowed = policy["allowed_config_files"]
        if not isinstance(allowed, list):
            errors.append("allowed_config_files: must be array")
        else:
            for i, filename in enumerate(allowed):
                validate_path(filename, f"allowed_config_files[{i}]")

    return errors


try:
    # Use _hooks_dir (bootstrap-resolved GLOBAL hooks dir), not hooks_dir
    # (this file's own dir). After the plugin migration this hook lives in
    # hooks/pretool/, so dirname(__file__) no longer points at the global
    # hooks dir where config/ lives — using it left the allowlist empty and
    # blocked every external path (memory, plans, state) as "path traversal".
    _policy_path = PathLib(_hooks_dir) / "config" / "directory_policy.json"
    if _policy_path.exists():
        with open(_policy_path, encoding="utf-8") as _f:
            _policy = json.load(_f)
            # Validate JSON schema before using config
            _validation_errors = _validate_directory_policy_schema(_policy, str(_policy_path))
            if _validation_errors:
                _logger.error(f"Directory policy schema validation errors in {_policy_path}:")
                for _err in _validation_errors:
                    _logger.info(f"  - {_err}")
                print(
                    "Using default configuration (empty ALLOWED_EXTERNAL_PATTERNS)", file=sys.stderr
                )
                # ALLOWED_EXTERNAL_PATTERNS remains empty list (default)
            else:
                ALLOWED_EXTERNAL_PATTERNS = _policy.get("allowed_external_paths", {}).get(
                    "patterns", []
                )
                # Load exact_paths as well for precise matching
                ALLOWED_EXTERNAL_EXACT_PATHS = _policy.get("allowed_external_paths", {}).get(
                    "exact_paths", []
                )
                # Diagnostic: confirm external path patterns loaded
                print(
                    f"Directory policy: ALLOWED_EXTERNAL_PATTERNS loaded ({len(ALLOWED_EXTERNAL_PATTERNS)} patterns)",
                    file=sys.stderr,
                )
except (OSError, json.JSONDecodeError) as e:
    # Log the specific error for debugging but continue with defaults
    _fallback_count += 1
    _logger.info(f"Directory policy config error: {e.__class__.__name__}: {e}")
    print(
        f"Fallback count: {_fallback_count} (monitoring: >10% indicates environment issue)",
        file=sys.stderr,
    )
    # ALLOWED_EXTERNAL_PATTERNS remains empty list (default)


def is_allowed_external_path(file_path: str) -> bool:
    # Thread-safe access to ALLOWED_EXTERNAL_PATTERNS with timeout and monitoring
    global _lock_contention_count, _lock_wait_total

    _lock_start = time.perf_counter()
    _acquired = _ALLOWED_EXTERNAL_PATTERNS_LOCK.acquire(timeout=1.0)
    _lock_wait = time.perf_counter() - _lock_start

    if not _acquired:
        # Lock timeout - fail-safe: assume not allowed
        _logger.warning(f"Warning: Lock acquisition timeout after {_lock_wait:.3f}s")
        return False

    try:
        # Track lock contention metrics
        _lock_contention_count += 1
        _lock_wait_total += _lock_wait

        if _lock_wait > 0.050:  # Log if wait exceeds 50ms
            print(
                f"Lock contention: {_lock_wait * 1000:.1f}ms wait (total: {_lock_contention_count} acquisitions, {_lock_wait_total:.3f}s cumulative)",
                file=sys.stderr,
            )

        # Copy lists to avoid holding lock during iteration
        patterns = list(ALLOWED_EXTERNAL_PATTERNS) if ALLOWED_EXTERNAL_PATTERNS else []
        exact_paths = list(ALLOWED_EXTERNAL_EXACT_PATHS) if ALLOWED_EXTERNAL_EXACT_PATHS else []
    finally:
        _ALLOWED_EXTERNAL_PATTERNS_LOCK.release()

    if not patterns and not exact_paths:
        return False

    normalized = file_path.replace("\\", "/").lower()

    # Check exact paths first (highest priority)
    for exact_path in exact_paths:
        if normalized == exact_path.lower():
            return True
        # Also check if normalized file path is under an allowed exact directory
        if normalized.startswith(exact_path.lower()) and len(normalized) > len(exact_path):
            # If the exact path ends with a separator (directory), startswith is sufficient
            # Otherwise verify the next char after the prefix is a separator
            # to prevent "p:/.stagingxy" from matching "p:/.staging"
            if exact_path.lower().endswith(("/", "\\")):
                return True
            if normalized[len(exact_path)] in ("/", "\\"):
                return True

        # Handle case where exact_path has trailing slash but normalized path doesn't
        # e.g., "P:/.staging" should match directory "P:/.staging/"
        if exact_path.lower().endswith(("/", "\\")):
            prefix_without_slash = exact_path.lower()[:-1]
            if normalized.startswith(prefix_without_slash) and len(normalized) >= len(prefix_without_slash):
                # P:/.staging matches P:/.staging/ directory
                # P:/.stagingxy should NOT match P:/.staging/ (but P:/.staging/file can)
                # Check next char after prefix is a separator or end-of-string
                remaining = normalized[len(prefix_without_slash):]
                if remaining.startswith(("/", "\\")) or remaining == "":
                    return True

    # Check patterns with fnmatch
    for pattern in patterns:
        if fnmatch.fnmatch(normalized, pattern.lower()):
            return True
        # Handle patterns ending with /* (match directory prefix)
        # e.g., c:/users/*/.claude/plans/* should match c:/users/brsth/.claude/plans
        if pattern.lower().endswith("/*"):
            # Check if the path matches the pattern prefix (without the /*)
            prefix_pattern = pattern.lower()[:-2]  # Remove /*
            if fnmatch.fnmatch(normalized, prefix_pattern):
                return True
            # Also check if normalized path is a prefix of what the pattern would match
            # e.g., path "c:/users/brsth/.claude/plans" should match pattern "c:/users/*/.claude/plans/*"
            # because brsth matches *

    return False


def check_csf_nip_path(file_path: str) -> tuple[bool, dict]:
    if not CSF_NIP_AVAILABLE:
        return True, {}
    normalized = file_path.replace("\\", "/").lower()
    if not normalized.startswith("p:/__csf/"):
        return True, {}
    validator = CSFNIPPathValidator()
    result = validator.validate_csf_nip_operation(file_path)
    return result["is_safe"], result


# DEPRECATED: Old subprocess version - kept for fallback only
# Use check_external_path_consent from pre_tool_use_logic instead

# Content size limits prevent Claude from writing oversized config files
# that slow down session startup or exceed tool buffer limits.
# settings.json: Active session config (kept small for fast loads)
# default: Catch-all for other Claude configs
CLAUDE_CONFIG_SIZE_LIMITS = {
    "settings.json": 100 * 1024,  # 100KB - session state must load quickly
    "default": 1024 * 1024,  # 1MB - allows large prompt templates
}

DIRECTORY_CREATING_COMMANDS = ["mkdir", "md", "New-Item"]
FILE_CREATING_COMMANDS = ["touch", "New-Item", "ni", "echo", "cat", "tee"]
SAFE_REDIRECT_TARGETS = ["/dev/null", "NUL", "CON"]

# Interpreter commands whose script arguments are READ/execute, not write targets
# Paths appearing after these commands should not be treated as file write targets
INTERPRETER_COMMANDS = frozenset(
    {
        "python",
        "python3",
        "python2",
        "pypy",
        "pypy3",
        "node",
        "nodejs",
        "ruby",
        "ruby2",
        "perl",
        "perl5",
        "bash",
        "sh",
        "zsh",
        "fish",
        "dash",
        "ash",
        "pwsh",
        "powershell",
        "cmd",
        "comspec",
        "lua",
        "php",
        "tclsh",
        "wish",
        "expect",
        "java",
        "javac",
        "jar",
        "kotlin",
        "scala",
        "go",
        "rustc",
        "cargo",
        "nim",
        "nimble",
        "hs",
        "ghc",
        "ghci",
        "hugs",
        "r",
        "Rscript",
        "julia",
        "octave",
        "matlab",
        "scip",
        "csc",
        "vbc",
        "mcs",
        "mono",
        "perl6",
        "rakudo",
        "cperl",
        "hy",
        "IronPython",
        "ipy",
        "ipy3",
        "env",
        "script",
        "rlwrap",
        "ed",
    }
)


def _is_interpreter_script_path(command: str, path: str) -> bool:
    """Check if path is a script argument to an interpreter command.

    When running 'python script.py' or 'node app.js', the script path is being
    READ/executed, not written. This is different from 'mkdir path' where the
    path IS being created/written.

    Args:
        command: Full bash command string
        path: Extracted path to check

    Returns:
        True if path appears to be a script argument to an interpreter command
    """
    cmd_lower = command.lower()

    # Build pattern: interpreter followed by path
    # This catches: python path, node path, ruby path, etc.
    # Also catches: python -c "code", python -m module (NOT script paths)
    for interpreter in INTERPRETER_COMMANDS:
        # Check if interpreter appears in command
        # Pattern: interpreter followed by the path (possibly with flags between)
        # We need to check if the path appears AFTER the interpreter as a script arg

        # Find the interpreter position
        import re as _re

        # Match: interpreter [flags/args] path
        # Where path is the extracted path (with / or \ as separators)
        # We want to check if path appears as an argument (not inside quotes for other purposes)
        pattern = _re.compile(
            r"\b"
            + _re.escape(interpreter)
            + r'(?:\s+(?:-[\w-]+|--[\w-]+|\'[^\']*\'|"[^"]*"|\S+))*'
            + r"\s+"
            + _re.escape(path)
            + r"(?:\s|$|\"|\')",
            _re.IGNORECASE,
        )
        if pattern.search(cmd_lower):
            return True

        # Simpler check: if interpreter appears in command and path is a script-like argument
        # This catches edge cases where the above pattern might miss something
        if f" {interpreter} " in f" {cmd_lower} " or cmd_lower.startswith(f"{interpreter} "):
            # Check if path looks like a script file (.py, .js, .rb, .sh, etc.)
            path_lower = path.lower()
            script_extensions = (
                ".py",
                ".pyw",
                ".pyc",
                ".pyo",
                ".js",
                ".mjs",
                ".cjs",
                ".jsx",
                ".ts",
                ".tsx",
                ".rb",
                ".rbw",
                ".rake",
                ".gemspec",
                ".pl",
                ".pm",
                ".t",
                ".pod",
                ".sh",
                ".bash",
                ".zsh",
                ".fish",
                ".ash",
                ".dash",
                ".ps1",
                ".psm1",
                ".psd1",
                ".bat",
                ".cmd",
                ".com",
                ".lua",
                ".php",
                ".tcl",
                ".tk",
                ".java",
                ".kt",
                ".scala",
                ".groovy",
                ".go",
                ".rs",
                ".c",
                ".cpp",
                ".h",
                ".hpp",
                ".cs",
                ".fs",
                ".fsx",
                ".r",
                ".R",
                ".RData",
                ".rda",
                ".jl",
                ".m",
                ".oct",
                ".sci",
                ".hs",
                ".lhs",
                ".ghci",
                ".clj",
                ".cljs",
                ".cljc",
                ".edn",
                ".ex",
                ".exs",
                ".erl",
                ".hrl",
                ".fs",
                ".fsx",
                ".fsscript",
                ".nim",
                ".nims",
                ".hy",
                ".pyxi",
                ".rkt",
                ".rktd",
                ".rktl",
            )
            if any(path_lower.endswith(ext) for ext in script_extensions):
                return True

    return False


# Pre-compiled regex patterns for path extraction (performance optimization)
# Pattern groups: Windows paths (A:), Unix paths (/), redirect operators, tee, mkdir, touch, open()
_PATTERN_MKDIR_WIN = re.compile(
    r'mkdir\s+(?:-p\s+)?["\']?([A-Za-z]:[\\/][^\s"\';&|]+)', re.IGNORECASE
)
_PATTERN_MKDIR_UNIX = re.compile(r'mkdir\s+(?:-p\s+)?["\']?(/[^\s"\';&|]+)', re.IGNORECASE)
_PATTERN_TOUCH = re.compile(r'touch\s+["\']?([A-Za-z]:[\\/][^\s"\';&|]+)', re.IGNORECASE)
_PATTERN_REDIRECT_WIN = re.compile(r'>\s*["\']?([A-Za-z]:[\\/][^\s"\';&|]+)', re.IGNORECASE)
_PATTERN_APPEND_WIN = re.compile(r'>>\s*["\']?([A-Za-z]:[\\/][^\s"\';&|]+)', re.IGNORECASE)
_PATTERN_TEE_WIN = re.compile(r'tee\s+(?:-a\s+)?["\']?([A-Za-z]:[\\/][^\s"\']+)', re.IGNORECASE)
_PATTERN_TEE_UNIX = re.compile(r'tee\s+(?:-a\s+)?["\']?(/[^\s"\']+)', re.IGNORECASE)
_PATTERN_CAT_REDIRECT_WIN = re.compile(
    r'cat\s+>\s*["\']?([A-Za-z]:[\\/][^\s"\';&|]+)', re.IGNORECASE
)
_PATTERN_CAT_REDIRECT_UNIX = re.compile(r'cat\s+>\s*["\']?(/[^\s"\';&|]+)', re.IGNORECASE)
_PATTERN_CAT_REDIRECT_QUOTED = re.compile(r'cat\s+>\s*"([^"]+)"', re.IGNORECASE)
_PATTERN_CAT_REDIRECT_SQUOTE = re.compile(r"cat\s+>\s*'([^']+)'", re.IGNORECASE)
_PATTERN_OPEN_WIN_DQUOTE = re.compile(r'open\("([A-Za-z]:[\\/][^\s"]+)"\s*,\s*"w"', re.IGNORECASE)
_PATTERN_OPEN_UNIX_DQUOTE = re.compile(r'open\("(/[^\s"]+)"\s*,\s*"w"', re.IGNORECASE)
_PATTERN_OPEN_WIN_SQUOTE = re.compile(r"open\('([A-Za-z]:[\\/][^\s']+)'\s*,\s*'w'", re.IGNORECASE)
_PATTERN_OPEN_UNIX_SQUOTE = re.compile(r"open\('(/[^\s']+)'\s*,\s*'w'", re.IGNORECASE)

# NEW: Patterns for relative paths (when command is run from P:/ directory)
# These detect paths without drive letters, which are relative to the current directory
_PATTERN_REDIRECT_RELATIVE = re.compile(r'>\s*["\']?([^:/\s"\';&|]+?)(?:["\']?\s*$)', re.IGNORECASE)
_PATTERN_APPEND_RELATIVE = re.compile(r'>>\s*["\']?([^:/\s"\';&|]+?)(?:["\']?\s*$)', re.IGNORECASE)
_PATTERN_TOUCH_RELATIVE = re.compile(r'touch\s+["\']?([^:/\s"\';&|]+)', re.IGNORECASE)
_PATTERN_MKDIR_RELATIVE = re.compile(
    r'mkdir\s+(?:-p\s+)?["\']?(?!(?:\w:|[/\0]))([^:/\s"\';&|]+)', re.IGNORECASE
)

# Consolidated pattern list for iteration
BASH_PATH_PATTERNS = [
    _PATTERN_MKDIR_WIN,  # Detects: mkdir -p P:/path/to/dir
    _PATTERN_MKDIR_UNIX,  # Detects: mkdir -p /path/to/dir
    _PATTERN_TOUCH,  # Detects: touch P:/file.txt
    _PATTERN_REDIRECT_WIN,  # Detects: echo "data" > P:/file.txt
    _PATTERN_APPEND_WIN,  # Detects: echo "log" >> P:/log.txt
    _PATTERN_TEE_WIN,  # Detects: echo "data" | tee P:/file.txt
    _PATTERN_TEE_UNIX,  # Detects: echo "data" | tee /path/to/file
    _PATTERN_CAT_REDIRECT_WIN,  # Detects: cat > P:/output.txt << EOF
    _PATTERN_CAT_REDIRECT_UNIX,  # Detects: cat > /path/to/output << EOF
    _PATTERN_CAT_REDIRECT_QUOTED,  # Detects: cat > "path with spaces/file.txt"
    _PATTERN_CAT_REDIRECT_SQUOTE,  # Detects: cat > 'quoted path.txt'
    _PATTERN_OPEN_WIN_DQUOTE,  # Detects: open("P:/file.txt", "w")
    _PATTERN_OPEN_UNIX_DQUOTE,  # Detects: open("/path/to/file", "w")
    _PATTERN_OPEN_WIN_SQUOTE,  # Detects: open('P:/file.txt', 'w')
    _PATTERN_OPEN_UNIX_SQUOTE,  # Detects: open('/path/to/file', 'w')
    _PATTERN_REDIRECT_RELATIVE,  # Detects: echo "data" > file.txt (relative)
    _PATTERN_APPEND_RELATIVE,  # Detects: echo "log" >> file.txt (relative)
    _PATTERN_TOUCH_RELATIVE,  # Detects: touch file.txt (relative)
    _PATTERN_MKDIR_RELATIVE,  # Detects: mkdir dir (relative)
]


def extract_paths_from_bash(command: str) -> list[str]:
    """Extract file paths from bash commands that write to files.

    This function detects file-write operations in bash commands across
    multiple patterns: redirect operators (>), append (>>), tee, mkdir,
    touch, and Python's open() function within inline scripts.

    Pattern detection includes:
    - Redirect operators: echo "data" > P:/file.txt, echo "log" >> P:/log.txt
    - Tee command: echo "content" | tee P:/output.txt
    - Heredoc: cat > P:/output.txt << EOF
    - Directory creation: mkdir -p P:/new/dir, touch P:/newfile.txt
    - Python inline: python -c "open('P:/file.txt', 'w').write('data')"

    Args:
        command: The bash command string to parse for file paths.

    Returns:
        A list of unique file paths detected in the command. Returns empty
        list if no file-write operations are found. Paths are returned in
        their original form (preserves Windows backslashes and Unix forward
        slashes as detected).

    Examples:
        >>> extract_paths_from_bash('echo "data" > P:/result.txt')
        ['P:/result.txt']

        >>> extract_paths_from_bash('echo "content" | tee P:/file.txt')
        ['P:/file.txt']

        >>> extract_paths_from_bash('cat > P:/output.txt << EOF\\ndata\\nEOF')
        ['P:/output.txt']

        >>> extract_paths_from_bash('python -c "open(\'P:/file.txt\', \'w\')"')
        ['P:/file.txt']

        >>> extract_paths_from_bash('echo "hello"')
        []

        >>> extract_paths_from_bash('git status')
        []
    """
    paths: list[str] = []

    for pattern in BASH_PATH_PATTERNS:
        matches = pattern.findall(command)
        paths.extend(matches)

    return list(set(paths))


def check_content_size(file_path: str, content: str) -> tuple[bool, str]:
    if not content or not file_path.replace("\\", "/").lower().startswith("p:/.claude/"):
        return True, ""
    filename = file_path.replace("\\", "/").split("/")[-1]
    limit = CLAUDE_CONFIG_SIZE_LIMITS.get(filename, CLAUDE_CONFIG_SIZE_LIMITS["default"])
    if len(content.encode("utf-8")) > limit:
        return False, f"Content size exceeds limit for {filename}"
    return True, ""


def _validate_path_security(path: str, project_dir: str, working_dir: str) -> str | dict:
    """Validate that path doesn't escape project directory.

    This helper function consolidates duplicated path security validation logic
    to ensure security fixes only need to be applied in one place.

    Args:
        path: The file path to validate (can be absolute or relative)
        project_dir: The project root directory for boundary checking
        working_dir: The current working directory for resolving relative paths

    Returns:
        Normalized path string if safe
        Block dict if path traversal detected
    """
    if re.match(r"^[A-Za-z]:|^/", path):
        # Absolute path - validate it doesn't escape project directory
        resolved = PathLib(path).resolve()
        try:
            resolved.relative_to(PathLib(project_dir))
            return path
        except ValueError:
            # Before blocking, check if this is an allowed external path
            if is_allowed_external_path(path):
                return path  # Allow whitelisted external paths
            return {
                "decision": "block",
                "message": f"Path traversal detected: {path}\nResolved path escapes project directory: {project_dir}",
                "blocking_hook": "PreToolUse_directory_policy.py",
            }
    else:
        # Relative path - resolve against working directory with boundary check
        resolved = (PathLib(working_dir) / path).resolve()
        try:
            # Verify resolved path is within project directory
            resolved.relative_to(PathLib(project_dir))
            return str(resolved)
        except ValueError:
            # Path traversal attempt detected (e.g., ../../etc/passwd)
            # Before blocking, check if this is an allowed external path
            if is_allowed_external_path(path):
                return str(resolved)  # Allow whitelisted external paths
            return {
                "decision": "block",
                "message": f"Path traversal detected: {path}\nResolved path escapes project directory: {project_dir}",
                "blocking_hook": "PreToolUse_directory_policy.py",
            }


def run(data: dict, verbose: bool = False) -> dict | None:
    """In-process execution entry point. RETURNS block dict or None."""
    # Check both old and new env var names for backward compatibility
    enabled = os.environ.get(
        "DIRECTORY_POLICY_ENABLED", os.environ.get("DENY_ROOT_WRITE_ENABLED", "true")
    )
    if enabled.lower() != "true":
        return None

    tool_name = data.get("tool_name", "")
    tool_input = data.get("tool_input", {})

    # Surgical bypass: Read is never blocked by directory policy.
    # Per session requirement (2026-06-26): "read anything, anywhere, anywhen"
    # applies only to Read; Write/Edit/Bash retain all five policy layers.
    if tool_name == "Read":
        return None

    # Determine the working directory for resolving relative paths
    # For bash commands, use os.getcwd() to get the actual working directory
    # For other tools, use CLAUDE_PROJECT_DIR (or fall back to P:/)
    if tool_name == "Bash":
        # Use actual current working directory for bash commands
        try:
            working_dir = os.getcwd().replace("\\", "/")
        except (OSError, FileNotFoundError) as e:
            # Fallback to project directory if CWD is inaccessible
            global _fallback_count
            _fallback_count += 1
            working_dir = os.environ.get("CLAUDE_PROJECT_DIR", "P:/").replace("\\", "/")
            print(
                f"Warning: CWD inaccessible ({e}), using project_dir: {working_dir}",
                file=sys.stderr,
            )
    else:
        # Use project directory for file operations (Write/Edit/etc)
        working_dir = os.environ.get("CLAUDE_PROJECT_DIR", "P:/").replace("\\", "/")

    # Project directory for validation (might differ from working directory)
    project_dir = os.environ.get("CLAUDE_PROJECT_DIR", "P:/").replace("\\", "/")

    path_validator = PathValidator()
    violation_reporter = ViolationReporter()

    paths_to_check = []
    if tool_name == "Bash":
        command = tool_input.get("command", "") or ""
        if not command:
            return None
        paths_to_check = extract_paths_from_bash(command)

        # DEFENSIVE: Filter out interpreter script paths
        # Commands like 'python script.py', 'node app.js' are READ/execute operations,
        # not write operations. Even if the extraction somehow captures them, filter them out.
        # This is belt-and-suspenders: the extraction patterns shouldn't match these,
        # but we add explicit filtering for clarity and defense-in-depth.
        if paths_to_check:
            filtered_paths = [
                p for p in paths_to_check if not _is_interpreter_script_path(command, p)
            ]
            # DEFENSIVE: Filter out flag-like strings and drive letters
            # The relative path pattern can incorrectly capture flags like "-p" or drive letters
            # when the command uses quoted Windows paths (e.g., mkdir -p "P:/path")
            flag_chars = frozenset({"-", "--"})

            def is_valid_path_candidate(p: str) -> bool:
                if not p:
                    return False
                # Block single drive letter "P:" or "P" - Windows paths should be captured
                # by the WIN pattern, not the REL pattern
                if len(p) <= 2 and p.endswith(":"):
                    return False
                # Block flags like -p, --flag
                if any(p.startswith(flag) for flag in flag_chars):
                    return False
                return True

            filtered_paths = [p for p in filtered_paths if is_valid_path_candidate(p)]
            # Only log if we actually filtered something (verbose mode)
            if verbose and len(filtered_paths) < len(paths_to_check):
                removed = set(paths_to_check) - set(filtered_paths)
                print(f"[directory_policy] Filtered interpreter script paths: {removed}")
            paths_to_check = filtered_paths

        # Convert relative paths to absolute paths with security validation
        # Uses helper function to consolidate validation logic and ensure
        # security fixes only need to be applied in one place
        absolute_paths = []
        for path in paths_to_check:
            result = _validate_path_security(path, project_dir, working_dir)
            if isinstance(result, dict):
                # Block dict returned - path traversal detected
                return result
            absolute_paths.append(result)
        paths_to_check = absolute_paths
    else:
        file_path = tool_input.get("file_path", "")
        if file_path:
            # Apply same path normalization and security validation as bash commands
            # to prevent access control bypass via Write/Edit tools
            # Uses helper function to consolidate validation logic
            result = _validate_path_security(file_path, project_dir, working_dir)
            if isinstance(result, dict):
                # Block dict returned - path traversal detected
                return result
            paths_to_check = [result]

            # Content size check (use normalized path)
            size_ok, size_err = check_content_size(paths_to_check[0], tool_input.get("content", ""))
            if not size_ok:
                return {
                    "decision": "block",
                    "message": size_err,
                    "blocking_hook": "PreToolUse_directory_policy.py",
                }

    for path in paths_to_check:
        # SECURITY BOUNDARY LAYER 0: Hook infrastructure exemption
        # Hook files and infrastructure are always allowed to prevent self-blocking
        normalized_for_check = path.replace("\\", "/").lower()
        # Strip drive prefix for startswith checks (e.g., "p:/" -> "")
        if normalized_for_check.startswith("p:/"):
            normalized_for_check = normalized_for_check[3:]
        elif normalized_for_check.startswith("P:/"):
            normalized_for_check = normalized_for_check[3:]
        hook_infra_paths = (
            ".claude/hooks/",
            ".claude/skills/planning/",
            ".claude/skills/code/",
            ".claude/skills/sqa/",  # SQA skill tests (self-referential quality audit)
            ".claude/.evidence/",  # Session evidence directories (critique, gto, pre-mortem, adversarial)
            ".claude/plans/adversarial/",  # Adversarial review findings and workflow artifacts
        )
        if any(normalized_for_check.startswith(p.lower()) for p in hook_infra_paths):
            continue  # Allow hook infrastructure paths

        # SECURITY BOUNDARY LAYER 1: Policy enforcement (project root writes blocked)
        # This check runs FIRST to establish clear policy boundary before security checks
        normalized = path.replace("\\", "/").lower()
        if normalized.startswith(project_dir.lower()):
            # Check if this is a direct project root file (not in subdirectories)
            rel_path = normalized[len(project_dir.lower()) :].lstrip("/")
            # Block any direct child of project root (no slash in rel_path)
            # This prevents: P:/file.txt, P:/=0.6.0, P:/test.json, etc.
            if "/" not in rel_path:
                # Whitelist of known-good root files that are allowed
                allowed_root_files = frozenset(
                    {
                        "readme.md",
                        "license",
                        "license.md",
                        "notice",
                        "pyproject.toml",
                        "setup.py",
                        "setup.cfg",
                        ".gitignore",
                        ".gitattributes",
                        ".dockerignore",
                        "changelog.md",
                        "contributing.md",
                        "security.md",
                        "claude.md",  # Project constitution
                        ".env",  # Environment configuration file
                    }
                )
                # Check if this is a known-good root file (case-insensitive match on lowercase name)
                # But FIRST check if it's a .py file - uppercase extensions like SETUP.PY must still be blocked
                # because they bypass the Write/Edit type validator
                is_py_extension = rel_path.lower().endswith(".py")
                # Special case: setup.py (case-sensitive!) is whitelisted as it's a legitimate root file
                # But uppercase variants like SETUP.PY bypass the Write/Edit type validator and must be blocked
                # We check the original path segments (before lowercasing) to detect uppercase extensions
                path_segments = path.replace("\\", "/").split("/")
                filename = path_segments[-1] if path_segments else ""
                has_uppercase_py_ext = filename.upper().endswith(".PY") and not filename.endswith(
                    ".py"
                )
                is_setup_py = rel_path == "setup.py"
                # Uppercase .PY extensions bypass type validator - never whitelist them
                if rel_path.lower() in allowed_root_files and (
                    not is_py_extension or (is_setup_py and not has_uppercase_py_ext)
                ):
                    continue  # Allow known-good root files (except non-setup .py files and uppercase .py)
                # Block .py files at root - type mismatch (code files belong in packages/, .claude/hooks/, etc.)
                # This catches Bash commands like "echo content > P:/script.py" that bypass Write/Edit hooks
                if is_py_extension and (not is_setup_py or has_uppercase_py_ext):
                    return {
                        "decision": "block",
                        "message": f"Cannot write .py file to project root: {path}\n"
                        f"Python files belong in: packages/, .claude/hooks/, scripts/, or module directories.\n"
                        f"Do not write .py files directly to P:/",
                        "blocking_hook": "PreToolUse_directory_policy.py",
                    }
                return {
                    "decision": "block",
                    "message": f"Cannot write to project root: {path}\nUse appropriate subdirectories (.claude/, docs/, packages/, etc.)",
                    "blocking_hook": "PreToolUse_directory_policy.py",
                }

        # SECURITY BOUNDARY LAYER 2: CSF NIP validation
        csf_ok, csf_res = check_csf_nip_path(path)
        if not csf_ok:
            return {
                "decision": "block",
                "message": f"CSF NIP Violation: {path}",
                "blocking_hook": "PreToolUse_directory_policy.py",
            }

        # SECURITY BOUNDARY LAYER 3: General path validation
        # This includes path traversal checks via PathValidator
        val_res = path_validator.validate_file_operation(path, project_dir)
        if not val_res["is_safe"]:
            msg = violation_reporter.format_violation_message(val_res["violation_type"], path)
            return {
                "decision": "block",
                "message": msg,
                "blocking_hook": "PreToolUse_directory_policy.py",
            }

    return None


@hook_main
def main() -> None:
    # Check for emergency bypass flag (for recovery from hook bugs)
    _bypass_fail_safe = (
        os.environ.get("DIRECTORY_POLICY_BYPASS_FAIL_SAFE", "false").lower() == "true"
    )

    try:
        data = json.load(sys.stdin)
        res = run(data, verbose=True)
        if res:
            print(json.dumps(res))
            sys.exit(2)
        sys.exit(0)
    except (json.JSONDecodeError, ValueError) as e:
        # Only bypass on parse errors - allow through for other hook errors
        logger = logging.getLogger(__name__)
        logger.error("Hook input parse failed: %s", e, exc_info=True)

        if _bypass_fail_safe:
            # Emergency bypass mode - fail-open with warning for parse errors only
            _logger.warning(f"Warning: DIRECTORY_POLICY_BYPASS_FAIL_SAFE=true - allowing operation despite parse error: {e}")
            sys.exit(0)  # Fail-open for emergency recovery only
        else:
            # Fail-safe: block the operation on parse error
            block_result = {
                "decision": "block",
                "message": f"Hook input parse failed (fail-safe): {e.__class__.__name__}: {e}\nTo bypass for emergency recovery: set DIRECTORY_POLICY_BYPASS_FAIL_SAFE=true",
                "blocking_hook": "PreToolUse_directory_policy.py",
                "error_type": str(e.__class__.__name__),
                "error_message": str(e),
            }
            print(json.dumps(block_result))
            sys.exit(2)  # Block on error (fail-safe)


if __name__ == "__main__":
    main()
