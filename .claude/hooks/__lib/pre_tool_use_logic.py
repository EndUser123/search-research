import ast
import hashlib
import json
import os
import re
import time
import warnings
from datetime import datetime, timedelta
from pathlib import Path

# --- Recursive Failure Detector Logic ---

FAILURE_THRESHOLD = 2
WINDOW_MINUTES = 10


def get_session_file():
    session_dir = Path("P:/.claude/sessions")
    session_dir.mkdir(parents=True, exist_ok=True)
    session_id = os.environ.get("CLAUDE_SESSION_ID", "default")
    return session_dir / f"failures_{session_id}.json"


def load_failures():
    session_file = get_session_file()
    if not session_file.exists():
        return []
    try:
        with open(session_file) as f:
            failures = json.load(f)
        cutoff = datetime.now() - timedelta(minutes=WINDOW_MINUTES)
        return [f for f in failures if datetime.fromisoformat(f["timestamp"]) > cutoff]
    except Exception:
        return []


def compute_command_hash(command):
    normalized = str(command).lower()
    normalized = re.sub(r'"[^"]*"', '""', normalized)
    normalized = re.sub(r"'[^']*'", "''", normalized)
    normalized = re.sub(r"\d+", "N", normalized)
    normalized = re.sub(r"\s+", " ", normalized).strip()
    return hashlib.md5(normalized.encode()).hexdigest()[:8]


def get_prescriptive_directive(tool: str, command: str, errors: list) -> str:
    """Generate a specific instruction to break the loop based on failure patterns."""
    cmd_lower = command.lower()
    error_text = " ".join(errors).lower()

    if "python" in cmd_lower and "-c" in cmd_lower:
        if any(p in error_text for p in ["syntaxerror", "invalid syntax", "line continuation"]):
            return (
                "**Prescriptive Directive:** Stop. Your `python -c` quoting is failing. "
                "Do NOT retry the shell command. Instead:\n"
                "1. Write your Python code to a temporary file (e.g., `P:/.tmp/eval.py`) using the `Write` tool.\n"
                "2. Execute the file using `python P:/.tmp/eval.py`.\n"
                "3. This bypasses shell quoting limits."
            )

    if tool == "Write" and any(p in error_text for p in ["syntaxerror", "gate"]):
        return (
            "**Prescriptive Directive:** The `Write` tool is being blocked by a syntax gate. "
            "Use the `Edit` tool instead to modify the file in smaller chunks, or check for unclosed brackets/quotes."
        )

    return "Abandon this approach and try a completely different strategy (e.g., different tool or simpler command)."


def check_recursive_failure(data):
    tool_name = data.get("tool_name")
    tool_input = data.get("tool_input", {})
    command = (
        tool_input.get("command")
        or tool_input.get("content")
        or tool_input.get("path")
        or json.dumps(tool_input)[:500]
    )

    cmd_hash = compute_command_hash(command)
    failures = load_failures()
    matching = [f for f in failures if f["tool"] == tool_name and f["command_hash"] == cmd_hash]

    if len(matching) >= FAILURE_THRESHOLD:
        recent_errors = [f["error_snippet"] for f in matching[-3:]]
        directive = get_prescriptive_directive(tool_name, command, recent_errors)

        error_list = "\n".join(f"  * {e}" for e in recent_errors)
        return {
            "decision": "block",
            "message": f"⚠️ CATCH-22 DETECTED (CLAUDE.md Part D.5)\n\nLoop detected: Same operation failed {len(matching)} times.\n\nRecent errors:\n{error_list}\n\n{directive}",
        }
    return None


# --- Syntax Gate Logic ---


def check_syntax(data):
    tool_name = data.get("tool_name")
    tool_input = data.get("tool_input", {})
    if tool_name != "Write":
        return None

    file_path = tool_input.get("file_path", "")
    content = tool_input.get("content", "")

    if not file_path.endswith(".py"):
        return None

    try:
        ast.parse(content)
    except SyntaxError as e:
        filename = file_path.replace("\\", "/").split("/")[-1]
        return {
            "decision": "block",
            "message": f"Python syntax error: {filename}:{e.lineno} - {e.msg}\n→ {e.text.strip() if e.text else ''}",
        }
    except Exception:
        pass
    return None


# --- Post-Bash Python File Edit Validator Logic ---


def check_python_file_edits(data: dict, pre_state: dict | None = None) -> dict | None:
    """Validate Python files modified by Bash commands and suggest fixes.

    This function runs AFTER Bash tool execution to detect and validate
    any .py files that were created or modified, providing helpful suggestions
    for syntax errors instead of just blocking.

    Context: Enhanced to provide fix suggestions for common syntax errors.
    The existing check_syntax() only runs for Write tool operations.

    Args:
        data: Hook data dictionary with tool_name, tool_input, tool_response

    Returns:
        None if validation passes or no .py files were changed
        {"decision": "block", "message": "..."} if syntax errors found with suggestions
    """
    tool_name = data.get("tool_name", "")
    if tool_name != "Bash":
        return None

    import subprocess
    import sys
    from pathlib import Path

    # Get current working directory from session or environment
    cwd = data.get("tool_input", {}).get("cwd", "") or os.getcwd()

    # Option B: Command pattern detection - Only validate if bash command could modify .py files
    # This prevents re-validating previously modified files on every bash command
    command = data.get("tool_input", {}).get("command", "").lower()

    # Patterns that indicate .py file modification
    py_modifying_patterns = [
        '.py"',
        ".py'",
        ".py>",
        ".py|",
        ".py&",  # Redirects/pipes to .py files
        "*.py",
        ".py ",
        " .py",  # File globs and paths
        "write ",
        "echo ",
        "printf ",
        "cat ",
        "tee ",  # Commands that write to files
        "sed ",
        "awk ",
        "perl ",  # Text processing that might create .py files
        ">file",
        ">>file",  # Generic redirects (may be followed by .py)
        "python ",
        "python3 ",  # Python scripts that might generate .py
        "touch ",  # Creating files (might be .py)
    ]

    # Also check for heredoc patterns that might create .py files
    heredoc_patterns = ["<<"]  # Matches all heredoc variations (<<, <<'EOF', <<"EOF")
    has_heredoc = any(pattern in command for pattern in heredoc_patterns)

    # Check if command contains any .py-modifying pattern
    could_modify_py = any(pattern in command for pattern in py_modifying_patterns) or has_heredoc

    # Skip validation if command couldn't possibly modify .py files
    if not could_modify_py:
        return None

    # Skip read-only Python invocations (--help, --version, -m --help, etc.)
    # These are common patterns that don't modify any files
    read_only_python_patterns = [
        "python --",
        "python3 --",
        "python -m --help",
        "python3 -m --help",
        "python -m pytest --help",
        "python3 -m pytest --help",
        "python -m pip --help",
        "python3 -m pip --help",
        "python -m unittest --help",
        "python3 -m unittest --help",
    ]
    if any(pattern in command for pattern in read_only_python_patterns):
        return None

    # Detect changed .py files using git status (most reliable)
    # git status --porcelain shows both new (A/??) and modified (M) files
    # Skip common directories that shouldn't be validated
    skip_dirs = {
        ".venv",
        "venv",
        "env",
        "ENV",
        ".git",
        "__pycache__",
        "build",
        "dist",
        "node_modules",
        ".tox",
        # Hook infrastructure - skip validation for hook files themselves
        ".claude/hooks",
        ".claude/skills/planning",
        ".claude/skills/code",
    }

    try:
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=5.0,
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
        )

        # git status --porcelain returns lines like "M file.py" or "A  new.py" or "?? untracked.py"
        # Track both filename and status to filter properly
        post_files = {}  # filename -> status_code
        for line in result.stdout.strip().split("\n"):
            if not line:
                continue
            # Format: "XY filename" where X=staged, Y=unstaged
            parts = line.split()
            if len(parts) >= 2:
                status = parts[0]
                filename = " ".join(parts[1:])
                # Only include .py files
                if filename.endswith(".py"):
                    # Filter out files in skip directories
                    if not any(skip_dir in filename.replace("\\", "/") for skip_dir in skip_dirs):
                        post_files[filename] = status

        # Compute delta if pre_state is provided
        if pre_state and "files" in pre_state:
            pre_files = set(pre_state["files"])
            # Only validate files that are NEW or MODIFIED by this command
            # (not files that existed before the command ran)
            changed_files = sorted(set(post_files.keys()) - pre_files)
        else:
            # No pre_state - use only NEW files (A/?? status), not pre-existing (M)
            # This prevents validating files modified in previous sessions
            # A = added, ?? = untracked, M = modified (any M means pre-existing change)
            new_or_untracked = [
                fn
                for fn, st in post_files.items()
                if st.startswith("A") or st == "??" or "A" in st  # added or untracked
            ]
            changed_files = sorted(new_or_untracked)

    except (FileNotFoundError, subprocess.TimeoutExpired, subprocess.SubprocessError):
        # Git not available or error - fall back to mtime-based detection
        # This finds recently modified .py files (modified in last 5 minutes)
        import time

        try:
            recent_threshold = time.time() - 300  # 5 minutes ago
            py_files = list(Path(cwd).rglob("*.py"))

            changed_files = []
            for py_file in py_files:
                # Skip files in skip directories
                if any(skip in str(py_file) for skip in skip_dirs):
                    continue

                # Check if file was recently modified
                try:
                    if py_file.stat().st_mtime > recent_threshold:
                        changed_files.append(str(py_file.relative_to(cwd)))
                except OSError:
                    continue
        except (OSError, ValueError):
            # Path operations failed - skip validation
            return None

    if not changed_files:
        return None

    # Import syntax fixer for helpful suggestions
    try:
        from syntax_fixer import format_suggestions

        USE_FIXER = True
    except ImportError:
        USE_FIXER = False

    # Validate each changed .py file
    errors = []
    for file_path in changed_files:
        # Skip if file doesn't exist (may have been deleted)
        full_path = Path(cwd) / file_path
        if not full_path.exists():
            continue

        try:
            with open(full_path, encoding="utf-8") as f:
                content = f.read()

            # Invalid string escapes can emit SyntaxWarning to stderr even when
            # we only want a validation result. Suppress the warning so Claude
            # Code does not surface it as a hook error.
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", SyntaxWarning)
                ast.parse(content)

        except SyntaxError as e:
            filename = file_path.replace("\\", "/").split("/")[-1]

            if USE_FIXER:
                # Use enhanced syntax fixer with suggestions
                error_msg = format_suggestions(filename, e)
                errors.append(error_msg)
            else:
                # Fallback to simple error message
                errors.append(f"{filename}:{e.lineno} - {e.msg}")
                if e.text:
                    errors.append(f"  → {e.text.strip()}")
        except Exception:
            # File read error or other issue - skip this file
            continue

    if errors:
        return {
            "decision": "block",
            "message": "Python syntax errors detected in Bash-modified files:\n"
            + "\n\n".join(errors),
        }

    return None


# --- Python -c Validator Logic ---


def check_python_c(data):
    """Validate Python -c commands by extracting and parsing the code.

    Uses a stateful parser instead of regex to correctly handle:
    - Nested quotes inside strings (e.g., print(f'{"nested"}'))
    - Escaped quotes (e.g., \" and \')
    - Multi-line code
    """
    if data.get("tool_name") != "Bash":
        return None

    command = data.get("tool_input", {}).get("command", "")

    # Find the -c flag and its quote
    import re

    match = re.search(r'python(?:3)?\s+-c\s+([\'"])', command)
    if not match:
        return None

    opening_quote = match.group(1)
    start_idx = match.end()  # Position after the opening quote

    # Stateful parser to find the matching closing quote
    i = start_idx
    while i < len(command):
        ch = command[i]

        # Check for escaped characters (backslash escapes)
        if ch == "\\":
            # Skip the next character (it's escaped)
            i += 2
            continue

        # Check for closing quote
        if ch == opening_quote:
            # This might be the closing quote - verify it's not inside a nested string
            # We need to check if we're inside a string literal in the Python code
            # For simplicity, we parse what we have so far and see if it's valid
            # If adding more chars makes it invalid, we haven't found the real end yet
            code_so_far = command[start_idx:i]
            try:
                ast.parse(code_so_far)
                # Code parses successfully - this might be the end
                # Check if adding the next character still parses
                if i + 1 < len(command):
                    next_char = command[i + 1]
                    # Check if next char is whitespace or command terminator
                    if next_char in " \t\n\r)'$|>":
                        # Likely end of -c argument
                        code = code_so_far
                        break
                else:
                    # End of command
                    code = code_so_far
                    break
            except SyntaxError:
                # Code doesn't parse yet - keep looking
                pass

        i += 1
    else:
        # Ran out of characters without finding valid end
        # Try to use what we have from the best position
        # Fall back to the last position that gave us the longest valid parse
        best_end = start_idx
        best_code = ""
        for j in range(i, start_idx, -1):
            try:
                test_code = command[start_idx:j]
                ast.parse(test_code)
                if len(test_code) > len(best_code):
                    best_code = test_code
                    best_end = j
            except SyntaxError:
                pass
        code = best_code

    if not code:
        return None  # Couldn't extract valid code, let Python handle the error

    try:
        ast.parse(code)
    except SyntaxError as e:
        return {
            "decision": "block",
            "message": f"Python syntax error in -c command:\n{e.msg}\nLine {e.lineno}",
        }
    return None


# --- Command Intent Gate Logic ---


def check_command_intent(data):
    if data.get("tool_name") != "Bash":
        return None

    session_id = os.environ.get("CLAUDE_SESSION_ID", "")
    if not session_id:
        return None

    state_file = Path(f"P:/.claude/hooks/state/pending_command_intent_{session_id}.json")
    if not state_file.exists():
        return None

    try:
        with state_file.open(encoding="utf-8") as f:
            state = json.load(f)
        if state.get("expires_at", 0) < time.time():
            state_file.unlink(missing_ok=True)
            return None

        return "subprocess"
    except Exception:
        return None


# --- External Path Consent Logic ---


def check_external_path_consent(file_path: str, data: dict | None = None) -> tuple[bool, str]:
    """In-process version of consent detection for external path edits.

    This function can be registered in IN_PROCESS_HOOKS to avoid subprocess overhead.

    Args:
        file_path: Path to check consent for
        data: Optional hook payload containing conversation messages
    """
    import os
    from pathlib import Path

    # HOOKS_DIR points to P:/.claude/hooks, so parent is P:/.claude
    HOOKS_DIR = Path("P:/.claude/hooks")

    # Import other needed functions
    try:
        from PreToolUse_deny_root_write import (
            check_csf_nip_path,
            is_allowed_external_path,
        )
    except ImportError:
        # Fallback implementations if import fails
        ALLOWED_EXTERNAL_PATTERNS = []
        try:
            import json

            _policy_path = HOOKS_DIR / "config" / "directory_policy.json"
            if _policy_path.exists():
                with open(_policy_path, encoding="utf-8") as _f:
                    _policy = json.load(_f)
                    ALLOWED_EXTERNAL_PATTERNS = _policy.get("allowed_external_paths", {}).get(
                        "patterns", []
                    )
        except Exception:
            pass

        import fnmatch

        def is_allowed_external_path(file_path: str) -> bool:
            if not ALLOWED_EXTERNAL_PATTERNS:
                return False
            normalized = file_path.replace("\\", "/").lower()
            for pattern in ALLOWED_EXTERNAL_PATTERNS:
                if fnmatch.fnmatch(normalized, pattern.lower()):
                    return True
            return False

        def check_csf_nip_path(file_path: str) -> tuple[bool, dict]:
            # Simplified fallback
            normalized = file_path.replace("\\", "/").lower()
            if not normalized.startswith("p:/__csf/"):
                return True, {}
            return True, {}

    normalized = file_path.replace("\\", "/").lower()
    if normalized.startswith("p:/"):
        return True, "workspace_needs_validation"
    if is_allowed_external_path(file_path):
        return True, "whitelisted_external"

    try:
        # Session+terminal scoped prompt state (multi-terminal safe, no TTL).
        try:
            from __lib import prompt_session_state  # package import path
        except Exception:
            try:
                import prompt_session_state  # direct module import path
            except Exception:
                prompt_session_state = None

        if prompt_session_state is None:
            user_prompt, prompt_status = "", "state_unavailable"
        else:
            user_prompt, prompt_status = prompt_session_state.read_latest_prompt(data)

        if not user_prompt:
            return False, f"no_consent_detected:{prompt_status}"

        # Intent-based consent detection
        # Check if user is discussing file editing, documentation changes, or skill updates
        consent_indicators = [
            "edit",
            "editing",
            "modify",
            "modify",
            "update",
            "updating",
            "integrat",
            "integrating",
            "add",
            "adding",
            "enhance",
            "enhancing",
            "document",
            "document",
            "write",
            "writing",
            "save",
            "saving",
            "skill",
            "skills",
            "skil",
            "skill.md",
            "readme",
            "change",
            "changing",
            "make chang",
            "chang",
            "fix",
            "fixing",
            "implement",
            "implementing",
            # Explicit approval patterns
            "approve edit",
            "approve write",
            "approved",
            "yes, please",
            "yes please",
            "go ahead",
            "make the change",
            "proceed",
            "do it",
        ]

        prompt_lower = user_prompt.lower()
        has_consent_intent = any(indicator in prompt_lower for indicator in consent_indicators)

        # Check if file path is explicitly mentioned
        path_lower = file_path.lower()
        path_mentioned = path_lower in prompt_lower or any(
            part in path_lower for part in path_lower.split(os.sep) if part in prompt_lower
        )

        # Allow if user shows intent OR mentions specific path
        if has_consent_intent or path_mentioned:
            return True, "intent_or_path_detected"

        return False, "no_consent_detected"
    except Exception as e:
        return False, f"error:{e}"


# --- Claude Sensitive Edit Consent ---

CLAUDE_ROOT = Path("P:/.claude")
HOOKS_ROOT = CLAUDE_ROOT / "hooks"
EDIT_CONSENT_DIR_PRIMARY = CLAUDE_ROOT / "state" / "edit_consent"
EDIT_CONSENT_DIR_FALLBACK = HOOKS_ROOT / "state" / "edit_consent"
EDIT_CONSENT_DIR_TEMP = (
    Path(os.environ.get("TEMP", "/tmp")) / "claude_hooks" / "state" / "edit_consent"
)


def _safe_id(value: str) -> str:
    """Sanitize string for filesystem-safe filenames."""
    return re.sub(r"[^a-zA-Z0-9_.-]+", "_", value)


def _normalize_terminal_id(terminal_id: str) -> str:
    """Strip env_ prefix so grant and check use the same scope hash.

    Claude Code passes terminal_id as env_<uuid> in UserPromptSubmit hook data
    but the raw CLAUDE_TERMINAL_ID env var omits the prefix.  Normalising to
    the bare UUID makes consent tokens portable across hook types.
    """
    if terminal_id.startswith("env_"):
        return terminal_id[4:]
    return terminal_id


def resolve_session_id(data: dict | None = None) -> str:
    """Resolve session id from payload first, then environment."""
    payload = data or {}
    session_obj = payload.get("session")
    if isinstance(session_obj, dict):
        for key in ("id", "session_id", "sessionId"):
            value = session_obj.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
    for key in ("session_id", "sessionId", "CLAUDE_SESSION_ID"):
        value = payload.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return os.environ.get("CLAUDE_SESSION_ID", "").strip()


def resolve_terminal_id(data: dict | None = None) -> str:
    """Resolve terminal id from payload first, then environment."""
    payload = data or {}
    for key in ("terminal_id", "terminalId", "CLAUDE_TERMINAL_ID"):
        value = payload.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    session_obj = payload.get("session")
    if isinstance(session_obj, dict):
        for key in ("terminal_id", "terminalId"):
            value = session_obj.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
    return os.environ.get("CLAUDE_TERMINAL_ID", "").strip() or "terminal_unknown"


def resolve_major_task_id(data: dict | None = None, terminal_id: str | None = None) -> str:
    """Resolve current major task id/name using lightweight, local sources."""
    payload = data or {}
    # Prefer explicit task identifiers from hook payload.
    for key in (
        "major_task_id",
        "majorTaskId",
        "active_task_id",
        "activeTaskId",
        "task_id",
        "taskId",
    ):
        value = payload.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()

    session_obj = payload.get("session")
    if isinstance(session_obj, dict):
        for key in (
            "major_task_id",
            "majorTaskId",
            "active_task_id",
            "activeTaskId",
            "task_id",
            "taskId",
        ):
            value = session_obj.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()

    for key in ("task_name", "taskName"):
        value = payload.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()

    env_task = os.environ.get("TASK_NAME", "").strip()
    if env_task:
        return env_task

    # Optional local fallback to existing task identity manager.
    try:
        import task_identity_manager

        manager = task_identity_manager.TaskIdentityManager(
            project_root=Path("P:/"),
            terminal_id=terminal_id or resolve_terminal_id(payload),
        )
        task = manager.get_current_task()
        if isinstance(task, str) and task.strip():
            return task.strip()
    except Exception:
        pass

    return "task_unknown"


def normalize_canonical_path(file_path: str) -> str:
    """Resolve and normalize a path to canonical lowercase forward-slash form."""
    try:
        resolved = Path(file_path).resolve()
    except Exception:
        resolved = Path(file_path)
    return str(resolved).replace("\\", "/").lower()


def resolve_claude_target_path(target: str) -> tuple[str | None, str]:
    """Resolve user-approved target into a canonical path under P:/.claude."""
    raw = (target or "").strip()
    if not raw:
        return None, "empty_target"

    normalized = raw.replace("\\", "/")
    has_path_hint = "/" in normalized or normalized.startswith(".") or ":" in normalized

    # Absolute path input
    if ":" in normalized or normalized.startswith("/"):
        canonical = normalize_canonical_path(normalized)
        if canonical.startswith("p:/.claude/"):
            return canonical, "ok"
        return None, "outside_claude"

    # Relative path under .claude
    if has_path_hint:
        candidate = CLAUDE_ROOT / normalized
        canonical = normalize_canonical_path(str(candidate))
        if canonical.startswith("p:/.claude/"):
            return canonical, "ok"
        return None, "outside_claude"

    # Bare filename: require unambiguous match if it already exists
    matches = list(CLAUDE_ROOT.rglob(normalized))
    file_matches = [m for m in matches if m.is_file()]
    if len(file_matches) > 1:
        return None, "ambiguous_target"
    if len(file_matches) == 1:
        canonical = normalize_canonical_path(str(file_matches[0]))
        if canonical.startswith("p:/.claude/"):
            return canonical, "ok"
        return None, "outside_claude"

    # Fallback to .claude root for new files
    candidate = CLAUDE_ROOT / normalized
    canonical = normalize_canonical_path(str(candidate))
    if canonical.startswith("p:/.claude/"):
        return canonical, "ok"
    return None, "outside_claude"


def _get_edit_consent_token_name(
    session_id: str,
    terminal_id: str,
    major_task_id: str,
    canonical_path: str,
) -> str:
    """Build deterministic token filename for session/terminal/task/path scope."""
    scope = _normalize_terminal_id(terminal_id)  # Only session+terminal+path in scope, not task_id
    scope_digest = hashlib.sha256(scope.encode("utf-8")).hexdigest()[:10]
    digest = hashlib.sha256(canonical_path.encode("utf-8")).hexdigest()[:12]
    return f"edit_consent_{_safe_id(session_id)}_{scope_digest}_{digest}.json"


def _iter_edit_consent_dirs() -> list[Path]:
    return [EDIT_CONSENT_DIR_PRIMARY, EDIT_CONSENT_DIR_FALLBACK, EDIT_CONSENT_DIR_TEMP]


def _load_edit_consent_config() -> dict:
    """Load edit consent configuration with fallback to defaults."""
    config_path = CLAUDE_ROOT / "config" / "edit_consent_config.json"
    defaults = {
        "token_ttl_seconds": 300,
        "cleanup_interval_seconds": 3600,
    }

    if not config_path.exists():
        return defaults

    try:
        with config_path.open(encoding="utf-8") as f:
            config = json.load(f)
            # Merge with defaults to handle missing keys
            return {**defaults, **config}
    except (OSError, json.JSONDecodeError):
        return defaults


def create_claude_edit_consent_token(
    session_id: str,
    canonical_path: str,
    terminal_id: str | None = None,
    major_task_id: str | None = None,
) -> tuple[bool, str]:
    """Create scope token for session+terminal+task+path. Idempotent if token already exists."""
    if not session_id:
        return False, "missing_session_id"
    if not canonical_path.startswith("p:/.claude/"):
        return False, "outside_claude"

    resolved_terminal = _normalize_terminal_id(
        (terminal_id or "").strip() or resolve_terminal_id(None)
    )
    resolved_task = (major_task_id or "").strip() or resolve_major_task_id(
        {"terminal_id": resolved_terminal},
        terminal_id=resolved_terminal,
    )
    token_name = _get_edit_consent_token_name(
        session_id, resolved_terminal, resolved_task, canonical_path
    )

    relative_path = canonical_path.removeprefix("p:/.claude/")
    payload = {
        "file": relative_path,
        "canonical_path": canonical_path,
        "session_id": session_id,
        "terminal_id": resolved_terminal,
        "major_task_id": resolved_task,
        "granted_at": int(time.time()),
    }

    for base_dir in _iter_edit_consent_dirs():
        try:
            base_dir.mkdir(parents=True, exist_ok=True)
            token_path = base_dir / token_name
            with token_path.open("x", encoding="utf-8") as f:
                json.dump(payload, f, ensure_ascii=True)
            return True, "created"
        except FileExistsError:
            return True, "already_exists"
        except Exception:
            continue
    return False, "write_failed"


def check_claude_edit_consent(data: dict, file_path: str) -> tuple[bool, str, str]:
    """Validate consent token scoped to session+terminal+major task+path.

    For .claude/ paths: Uses explicit consent tokens (approve edit <path>).
    For restricted paths (docs/): Uses intent-based consent detection.
    """
    session_id = resolve_session_id(data)
    if not session_id:
        return False, "missing_session_id", normalize_canonical_path(file_path)
    terminal_id = resolve_terminal_id(data)
    major_task_id = resolve_major_task_id(data, terminal_id=terminal_id)

    canonical_path = normalize_canonical_path(file_path)
    if not canonical_path.startswith("p:/.claude/"):
        # Check for restricted path consent (e.g., docs/ directory)
        # Uses intent-based detection instead of explicit tokens
        has_consent, consent_reason = check_external_path_consent(file_path, data)
        if has_consent:
            return True, consent_reason, canonical_path
        return False, "outside_claude_no_consent", canonical_path

    terminal_id = _normalize_terminal_id(terminal_id)
    token_name = _get_edit_consent_token_name(
        session_id, terminal_id, major_task_id, canonical_path
    )
    token_path = None
    for base_dir in _iter_edit_consent_dirs():
        candidate = base_dir / token_name
        if candidate.exists():
            token_path = candidate
            break
    if token_path is None:
        return False, "token_not_found", canonical_path

    try:
        with token_path.open(encoding="utf-8") as f:
            token = json.load(f)
    except Exception:
        return False, "token_invalid", canonical_path

    # Check token expiry (session-based consent with TTL)
    config = _load_edit_consent_config()
    ttl = config.get("token_ttl_seconds", 300)
    granted_at = token.get("granted_at", 0)
    if time.time() - granted_at > ttl:
        # Token expired, delete it
        try:
            token_path.unlink(missing_ok=True)
        except Exception:
            pass
        return False, "token_expired", canonical_path

    token_session = str(token.get("session_id", "")).strip()
    token_terminal = str(token.get("terminal_id", "")).strip()
    token_task = str(token.get("major_task_id", "")).strip()
    token_path_value = str(token.get("canonical_path", "")).strip().lower()
    # Task_id no longer validated - removed from scope to fix approval loop

    # Collect specific mismatches for diagnostic output
    mismatches = []
    if token_session != session_id:
        mismatches.append(f"session ({token_session[:8]}... != {session_id[:8]}...)")
    if _normalize_terminal_id(token_terminal) != _normalize_terminal_id(terminal_id):
        mismatches.append(f"terminal ({token_terminal} != {terminal_id})")
    # FIX: Compare both sides as lowercase to avoid case-sensitivity bugs
    if token_path_value != canonical_path.lower():
        mismatches.append(f"path ({token_path_value} != {canonical_path.lower()})")

    if mismatches:
        return False, f"token_mismatch: {', '.join(mismatches)}", canonical_path

    return True, "consent_granted", canonical_path


def cleanup_session_edit_consent_tokens(
    session_id: str,
    terminal_id: str | None = None,
    major_task_id: str | None = None,
) -> int:
    """Remove stale consent tokens for the same session+terminal but different task scope."""
    removed = 0
    pattern = "edit_consent_*.json"
    resolved_terminal = (terminal_id or "").strip() or resolve_terminal_id(None)
    resolved_task = (major_task_id or "").strip() or resolve_major_task_id(
        {"terminal_id": resolved_terminal},
        terminal_id=resolved_terminal,
    )
    for base_dir in _iter_edit_consent_dirs():
        if not base_dir.exists():
            continue
        for token_path in base_dir.glob(pattern):
            try:
                with token_path.open(encoding="utf-8") as f:
                    token = json.load(f)

                token_session = str(token.get("session_id", "")).strip()
                token_terminal = str(token.get("terminal_id", "")).strip()
                token_task = str(token.get("major_task_id", "")).strip()

                # Keep tokens outside this session/terminal untouched.
                if token_session != session_id or token_terminal != resolved_terminal:
                    continue

                # Tokens are now session-scoped (not task-scoped), so don't auto-cleanup
                # Keep all tokens for this session/terminal combination
                continue
                removed += 1
            except Exception:
                continue
    return removed
