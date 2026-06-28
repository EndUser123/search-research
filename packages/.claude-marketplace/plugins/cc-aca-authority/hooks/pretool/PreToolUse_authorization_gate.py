

# --- plugin bootstrap ---
import sys
from pathlib import Path

_lib = Path(__file__).resolve().parent.parent.parent / "__lib"
if str(_lib) not in sys.path:
    sys.path.insert(0, str(_lib))
from _bootstrap import bootstrap
_hooks_dir = bootstrap(__file__)
# --- end bootstrap ---

#!/usr/bin/env python3
"""
Authorization Gate Hook (PreToolUse - Bash)

Prevents destructive command execution when user only provided confirmatory
language rather than explicit execution authorization.

Pattern detected: Implied authorization escalation
- User says "that's correct" or "good approach"
- CC interprets as "proceed with execution"
- Destructive action occurs before user can stop it

Fix: Require explicit action verbs before destructive operations.

Constitutional basis:
- CLAUDE Constitution Part D: Plan-Then-Act (wait for approval)
- "Do not combine planning and execution in the same response"
"""

import hashlib
import json
import os
import re
import sys
import time
from pathlib import Path

# Add hooks dir to path for __lib imports
_HOOKS_DIR = Path(__file__).resolve().parent
if str(_HOOKS_DIR) not in sys.path:
    sys.path.insert(0, str(_HOOKS_DIR))

# Add CSF to path for CKS access
_csf_src = Path(__file__).resolve().parent.parent.parent / "__csf" / "src"
if _csf_src.exists():
    sys.path.insert(0, str(_csf_src))

# Import CKS cache for performance
try:
    from _cks_cache import get_cache, maybe_clear_cache

    maybe_clear_cache()  # Clear if environment variable set
    CKS_CACHE_ENABLED = True
except ImportError:
    CKS_CACHE_ENABLED = False

# Import hybrid clock-safe TTL utilities
from __lib.ttl_utils import is_expired

def _model_ready_fallback() -> bool:
    """Fallback function when CKS preload is unavailable."""
    return False

hooks_dir = Path(__file__).resolve().parent

# Import CKS pre-load check (model may be pre-loaded by SessionStart)
try:
    import importlib.util

    preload_spec = importlib.util.spec_from_file_location(
        "SessionStart_cks_preload", hooks_dir / "SessionStart_cks_preload.py"
    )
    if preload_spec and preload_spec.loader:
        preload_module = importlib.util.module_from_spec(preload_spec)
        preload_spec.loader.exec_module(preload_module)
        CKS_PRELOAD_AVAILABLE = True
        is_model_ready = preload_module.is_model_ready
    else:
        CKS_PRELOAD_AVAILABLE = False
        is_model_ready = _model_ready_fallback
except Exception:
    CKS_PRELOAD_AVAILABLE = False
    is_model_ready = _model_ready_fallback

# Import observability for block decision logging
try:
    from __lib.dx_tools_observability import get_metrics

    OBSERVABILITY_AVAILABLE = True
except ImportError:
    OBSERVABILITY_AVAILABLE = False

# CKS trigger words for this hook
HOOK_TRIGGERS = ["delete", "destroy", "reset", "purge", "wipe", "drop"]

# Destructive command patterns (case-insensitive)
DESTRUCTIVE_PATTERNS = [
    # Git destructive
    r"git\s+rm\b",
    r"git\s+reset\s+--hard",
    r"git\s+checkout\s+--\s+",
    r"git\s+clean\s+-[fd]",
    r"git\s+push\s+(-f|--force)",
    r"git\s+branch\s+-[dD]",
    # Python list style (e.g., ['git', 'branch', '-D'])
    r"\['git',\s*'branch',\s*'-[dD]",
    r"\[\"git\",\s*\"branch\",\s*\"-[dD]",
    # Unix destructive
    r"rm\s+-rf?\b",
    r"rm\s+-r\b",
    r"rmdir\s+",
    # Windows destructive
    r"del\s+/[fqs]",
    r"rmdir\s+/[sq]",
    r"rd\s+/[sq]",
    # Database destructive
    r"drop\s+(table|database|schema)",
    r"truncate\s+table",
    r"delete\s+from\s+\w+\s*;?\s*$",  # DELETE without WHERE
]

# Project-safe cache cleanup patterns (auto-approved under project tree)
PROJECT_SAFE_PATTERNS = [
    r"\brm\s+-rf\s+.*__pycache__",  # Cache cleanup under project tree
    r"\bfind\s+.*__pycache__.*-exec\s+rm\s+-rf",  # Find-based cache cleanup
    r"\bfind\s+.*-name\s+['\"]?\*\.pyc['\"]?\s+-delete",  # .pyc deletion
]

# Explicit authorization phrases (user intends execution)
AUTHORIZATION_PATTERNS = [
    # Direct action commands
    r"\bdo\s+it\b",
    r"\bproceed\b",
    r"\bgo\s+ahead\b",
    r"\bexecute\b",
    r"\brun\s+it\b",
    r"\bmake\s+it\s+(so|happen)\b",
    r"\bgo\s+for\s+it\b",
    r"\blet'?s\s+do\s+(it|this|that)\b",
    # Explicit yes + action
    r"\byes[,.]?\s*(do|proceed|go|run|execute|delete|remove)",
    # Imperative verbs for the action
    r"\b(delete|remove|drop|reset|clean|push)\s+(it|them|this|that|the)\b",
    r"\bpush\s+it\b",
    r"\bdelete\s+(it|them|those|the\s+\w+)\b",
    r"\bremove\s+(it|them|those|the\s+\w+)\b",
    # Deployment/release language
    r"\bship\s+it\b",
    r"\bdeploy\s+(it|now|this)\b",
    # Numbered option responses (single digit = proceed)
    r"^\d+\b",  # Any number at start of message = authorization
]

# Confirmatory phrases (NOT authorization - just acknowledging correctness)
CONFIRMATORY_PATTERNS = [
    r"^(that'?s?\s+)?(right|correct|exactly|perfect|optimal)\.?$",
    r"^yes\.?$",
    r"^(that\s+)?(looks?|sounds?)\s+good\.?$",
    r"^(that\s+)?makes?\s+sense\.?$",
    r"^good\s+(approach|plan|idea|thinking)\.?$",
    r"^(that'?s?\s+)?(it|the\s+one)\.?$",
    r"^(I\s+)?(agree|confirmed?)\.?$",
    r"^nice\.?$",
    r"^great\.?$",
    r"^ok(ay)?\.?$",
    r"^(you'?re?|that'?s?)\s+(right|correct)\.?$",
]

# Patterns that indicate Python code is executing subprocess commands
SUBPROCESS_PATTERNS = [
    r"subprocess\.(run|call|Popen|check_output|check_call)",
    r"os\.system",
    r"os\.spawn",
    r"os\.popen",
    r"commands\.getoutput",
    r"os\.system\(",
]

# Short bare affirmative words (without action context)
BARE_AFFIRMATIVES = {"yes", "yep", "yeah", "yup", "sure", "ok", "okay", "k", "right", "correct"}

# Compiled regex patterns for performance
PYTHON_C_PATTERN = re.compile(r'python\s*-c\s+["\'](.+?)["\']', re.IGNORECASE | re.DOTALL)

def _remove_shell_comments(line: str) -> str:
    """Remove shell comments from a single line, respecting quotes.

    Args:
        line: A single line of shell command text.

    Returns:
        The line with comments (text after # outside quotes) removed.
    """
    in_single = False
    in_double = False

    for i, char in enumerate(line):
        if char == '"' and not in_single:
            in_double = not in_double
        elif char == "'" and not in_double:
            in_single = not in_single
        elif char == "#" and not (in_single or in_double):
            return line[:i]

    return line

def _extract_python_c_match(command: str) -> re.Match | None:
    """Extract Python -c pattern match from command.

    Args:
        command: The command string to search.

    Returns:
        Regex match object if Python -c pattern found, else None.
    """
    return PYTHON_C_PATTERN.search(command)

def _contains_subprocess_call(code: str) -> bool:
    """Check if Python code contains subprocess calls.

    Args:
        code: Python code string to check.

    Returns:
        True if code contains subprocess patterns, False otherwise.
    """
    for pattern in SUBPROCESS_PATTERNS:
        if re.search(pattern, code, re.IGNORECASE):
            return True
    return False

def extract_actual_command(command: str) -> str:
    """Extract the actual command by removing wrappers that contain false positives.

    Cases to handle:
    - python -c "..." -> Extract code content to check for subprocess patterns
    - shell comments (# ...) -> Ignore commented text
    - chained commands (cmd1 && cmd2) -> Check each part

    Args:
        command: The raw command string.

    Returns:
        The command that should actually be checked for destructive patterns.
        Empty string if command is safe Python code without subprocess calls.
    """
    # Check for Python -c wrappers (the content inside is code, not shell)
    python_match = _extract_python_c_match(command)
    if python_match:
        python_code = python_match.group(1)

        # If Python code contains subprocess calls, return original for full checking
        if _contains_subprocess_call(python_code):
            return command

        # No subprocess calls - this is just Python code, not a shell command
        return ""

    # Remove shell comments (everything after # outside quotes)
    lines = command.split("\n")
    code_lines = [_remove_shell_comments(line) for line in lines]

    return "\n".join(code_lines).strip()

def _check_destructive_patterns(text: str) -> str | None:
    """Check if text matches any destructive command patterns.

    Args:
        text: The command text to check.

    Returns:
        The first matching pattern, or None if no match.
    """
    text_lower = text.lower()
    for pattern in DESTRUCTIVE_PATTERNS:
        if re.search(pattern, text_lower, re.IGNORECASE):
            return pattern
    return None

def _check_python_c_destructive(command: str) -> str | None:
    """Check if Python -c command contains destructive patterns.

    Args:
        command: The full command string containing Python -c.

    Returns:
        The matching destructive pattern if found, None otherwise.
    """
    python_match = _extract_python_c_match(command)
    if not python_match:
        return None

    python_code = python_match.group(1).lower()

    # Check inside the Python code content for destructive patterns
    return _check_destructive_patterns(python_code)

def is_destructive_command(command: str) -> str | None:
    """Check if command matches destructive patterns. Returns matched pattern.

    Args:
        command: The command string to check.

    Returns:
        The matched destructive pattern, or None if safe.
    """
    actual_command = extract_actual_command(command)

    # If actual_command is empty, this was safe Python code
    if not actual_command:
        return None

    # Check the extracted command for destructive patterns
    pattern_match = _check_destructive_patterns(actual_command)
    if pattern_match:
        return pattern_match

    # For Python -c with subprocess, also check inside the Python code
    python_pattern = _check_python_c_destructive(command)
    if python_pattern:
        return python_pattern

    return None

def _log_block_decision(command: str, working_dir: str, reason: str, pattern: str = "") -> None:
    """Log authorization gate block decisions for analysis and pattern refinement.

    Args:
        command: The blocked command
        working_dir: Working directory where command would run
        reason: Reason for block (e.g., "not_project_safe", "no_authorization")
        pattern: Pattern that matched (if any)
    """
    if not OBSERVABILITY_AVAILABLE:
        return

    try:
        import json
        from datetime import datetime

        # Create logs directory
        hooks_dir = Path(__file__).resolve().parent
        logs_dir = Path("P:/") / ".claude" / "logs"
        logs_dir.mkdir(parents=True, exist_ok=True)

        # Log file path
        log_file = logs_dir / "auth_blocks.jsonl"

        # Create log entry
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "command": command,
            "working_dir": working_dir,
            "reason": reason,
            "pattern": pattern,
        }

        # Append to JSONL file
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry) + "\n")

        # Also record to metrics
        metrics = get_metrics()
        metrics.record_event("auth", "blocked", 1)

    except Exception as e:
        # Graceful degradation - don't break hook on logging failures
        verbose = os.environ.get("DX_TOOLS_METRICS_VERBOSE", "false").lower() == "true"
        if verbose:
            print(f"Warning: Could not log block decision: {e}")

def has_explicit_authorization(text: str, command: str = "", working_dir: str = "") -> bool:
    """Check if text contains explicit authorization language.

    Args:
        text: The user message text to check.
        command: The command being checked (for project-safe patterns).
        working_dir: The working directory (for project-safe patterns).

    Returns:
        True if explicit authorization pattern found.
    """
    text_lower = text.lower().strip()

    # NEW: Check for project-safe cache cleanup operations
    if command and working_dir:
        if is_project_safe_operation(command, working_dir):
            return True

    for pattern in AUTHORIZATION_PATTERNS:
        if re.search(pattern, text_lower, re.IGNORECASE):
            return True
    return False

def is_project_safe_operation(command: str, working_dir: str) -> bool:
    """Check if command is a safe cache cleanup operation under project tree.

    Args:
        command: The command string to check
        working_dir: The working directory where command will run

    Returns:
        True if command is safe cache cleanup under project tree, False otherwise
    """
    # Must match safe pattern AND be under project tree (P:/)
    import re

    matched_pattern = ""
    for pattern in PROJECT_SAFE_PATTERNS:
        if re.search(pattern, command, re.IGNORECASE):
            matched_pattern = pattern
            break

    if not matched_pattern:
        # Log block decision and return False
        _log_block_decision(command, working_dir, reason="not_safe_pattern", pattern="")
        return False

    # Now verify working directory is under project tree
    try:
        # Check original string format first to catch Unix-style system paths
        # Unix absolute paths starting with / (except /mnt/p/) are system paths
        if working_dir.startswith("/") and not working_dir.startswith("/mnt/p"):
            # Log block decision and return False
            _log_block_decision(
                command, working_dir, reason="not_project_tree", pattern=matched_pattern
            )
            return False

        # Check for Windows drive letters other than P:\
        if len(working_dir) >= 2 and working_dir[1] == ":":
            if not working_dir.upper().startswith("P:"):
                # Log block decision and return False
                _log_block_decision(
                    command, working_dir, reason="not_project_tree", pattern=matched_pattern
                )
                return False

        # Normalize without filesystem resolution to avoid hangs on mapped/network drives.
        normalized_working_dir = str(Path(working_dir)).replace("/", "\\").upper()
        if not normalized_working_dir.startswith("P:\\"):
            # Log block decision and return False
            _log_block_decision(
                command, working_dir, reason="not_project_tree", pattern=matched_pattern
            )
            return False
    except (OSError, ValueError):
        # Log block decision and return False
        _log_block_decision(
            command, working_dir, reason="path_resolution_error", pattern=matched_pattern
        )
        return False

    # Auto-approved! Record metrics
    if OBSERVABILITY_AVAILABLE:
        metrics = get_metrics()
        metrics.record_event("auth", "auto_approved", 1)

    return True

def _is_bare_affirmative(text: str) -> bool:
    """Check if text is a bare affirmative without action verbs.

    Args:
        text: The text to check.

    Returns:
        True if text is a short bare affirmative.
    """
    if len(text) >= 50:
        return False

    first_word = text.split()[0] if text.split() else ""
    return first_word.rstrip(".,!") in BARE_AFFIRMATIVES

def _matches_confirmatory_pattern(line: str) -> bool:
    """Check if a line matches any confirmatory pattern.

    Args:
        line: A single line of text to check.

    Returns:
        True if line matches a confirmatory pattern.
    """
    for pattern in CONFIRMATORY_PATTERNS:
        if re.match(pattern, line, re.IGNORECASE):
            return True
    return False

def is_confirmatory_only(text: str) -> bool:
    """Check if text is ONLY confirmatory (no action intent).

    Args:
        text: The user message text to check.

    Returns:
        True if text appears to be confirmatory-only without authorization.
    """
    text_lower = text.lower().strip()

    # If explicit authorization anywhere, not confirmatory-only
    if has_explicit_authorization(text):
        return False

    # Check each line for confirmatory patterns
    lines = [line.strip() for line in text_lower.split("\n") if line.strip()]

    if not lines:
        return False

    # Check if matches confirmatory patterns
    for line in lines:
        if _matches_confirmatory_pattern(line):
            return True

    # Short affirmative responses without action verbs
    if _is_bare_affirmative(text_lower):
        return True

    return False

def _extract_text_from_content_block(block: dict) -> str | None:
    """Extract text from a message content block.

    Args:
        block: A content block (dict or str).

    Returns:
        Extracted text string, or None if not a text block.
    """
    if isinstance(block, dict) and block.get("type") == "text":
        return block.get("text", "")
    if isinstance(block, str):
        return block
    return None

def _extract_text_from_message(msg: dict) -> str | None:
    """Extract text content from a conversation message.

    Args:
        msg: A message dictionary with role and content.

    Returns:
        Extracted text content, or None if not extractable.
    """
    if msg.get("role") != "user":
        return None

    content = msg.get("content", "")
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        texts = [_extract_text_from_content_block(block) for block in content]
        texts = [t for t in texts if t is not None]
        return "\n".join(texts)

    return None

def get_last_user_message(input_data: dict) -> str:
    """Extract the last user message from conversation context.

    Args:
        input_data: The hook input data containing conversation history.

    Returns:
        The last user message text, or empty string if not found.
    """
    # First check if conversation is directly available
    conversation = (
        input_data.get("conversation", [])
        or input_data.get("messages", [])
        or input_data.get("history", [])
    )

    if conversation:
        for msg in reversed(conversation):
            if isinstance(msg, dict):
                text = _extract_text_from_message(msg)
                if text:
                    return text

    # Try reading from transcript file if available
    transcript_path = input_data.get("transcript_path", "")
    if transcript_path:
        try:
            transcript_file = Path(transcript_path)
            if transcript_file.exists():
                # Read the last few user messages from transcript
                # Transcript is JSONL - each line is a JSON object
                lines = []
                with open(transcript_file, encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line:
                            try:
                                lines.append(json.loads(line))
                            except json.JSONDecodeError:
                                pass

                # Walk backward to find last user message
                for item in reversed(lines):
                    if isinstance(item, dict):
                        # Check for role-based messages (Anthropic format)
                        if item.get("role") == "user":
                            content = item.get("content", "")
                            if isinstance(content, str):
                                return content
                            if isinstance(content, list):
                                # Handle content blocks
                                for block in content:
                                    if isinstance(block, dict) and block.get("type") == "text":
                                        return block.get("text", "")
                        # Check for message-based format (OpenAI format)
                        elif "message" in item:
                            msg = item.get("message", {})
                            if isinstance(msg, dict) and msg.get("role") == "user":
                                content = msg.get("content", "")
                                if isinstance(content, str):
                                    return content
        except Exception:
            pass  # Transcript reading failed, continue to fallbacks

    # Fallback: check prompt, content, and input fields
    for key in ["prompt", "content", "input"]:
        value = input_data.get(key, "")
        if value:
            return str(value)

    return ""

# =============================================================================
# Authorization State Management - Fix for assistant response caching
# =============================================================================

STATE_DIR = Path("P:/.claude/state")
STATE_TTL = 300  # 5 minutes

def _resolve_state_identifiers(input_data: dict) -> tuple:
    """Resolve session_id and terminal_id for state file naming.

    Args:
        input_data: Hook input data.

    Returns:
        Tuple of (session_id, terminal_id).
    """
    # Try multiple sources for session_id
    session_id = (
        input_data.get("session_id")
        or input_data.get("sessionId")
        or os.environ.get("CLAUDE_SESSION_ID", "default")
    )

    # Try multiple sources for terminal_id
    terminal_id = (
        input_data.get("terminal_id")
        or input_data.get("terminalId")
        or os.environ.get("CLAUDE_TERMINAL_ID", "default")
    )

    return session_id, terminal_id

def _get_state_file_path(session_id: str, terminal_id: str) -> Path:
    """Get the path to the authorization state file.

    Args:
        session_id: Session identifier.
        terminal_id: Terminal identifier.

    Returns:
        Path to the state file.
    """
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    filename = f"auth_gate_{session_id}_{terminal_id}.json"
    return STATE_DIR / filename

def check_authorization_state(input_data: dict, command: str) -> dict | None:
    """Check if there's a pending authorization awaiting user response.

    Args:
        input_data: Hook input data.
        command: The command being executed.

    Returns:
        State dict if awaiting response and valid, None otherwise.
    """
    session_id, terminal_id = _resolve_state_identifiers(input_data)
    state_file = _get_state_file_path(session_id, terminal_id)

    if not state_file.exists():
        return None

    try:
        state = json.loads(state_file.read_text())
        blocked_at = state.get("blocked_at", 0)

        # Check TTL (hybrid clock-safe: handles old wall-clock timestamps correctly)
        if blocked_at > 0 and _is_expired(blocked_at, STATE_TTL):
            # State expired - clean up
            state_file.unlink(missing_ok=True)
            return None

        # Verify command matches (prevents state confusion)
        command_hash = state.get("command_hash", "")
        current_hash = hashlib.md5(command.encode()).hexdigest()[:8]
        if command_hash != current_hash:
            # Different command - clean up old state
            state_file.unlink(missing_ok=True)
            return None

        return state

    except (json.JSONDecodeError, OSError, ValueError):
        # Corrupted state file - clean up
        state_file.unlink(missing_ok=True)
        return None

def write_awaiting_state(input_data: dict, command: str) -> None:
    """Write state file indicating awaiting user response to authorization prompt.

    Args:
        input_data: Hook input data.
        command: The command being blocked.
    """
    session_id, terminal_id = _resolve_state_identifiers(input_data)
    state_file = _get_state_file_path(session_id, terminal_id)

    command_hash = hashlib.md5(command.encode()).hexdigest()[:8]

    state = {
        "command": command[:200],  # Truncate for storage
        "command_hash": command_hash,
        "blocked_at": time.time(),
        "awaiting_response": True,
        "session_id": session_id,
        "terminal_id": terminal_id,
    }

    try:
        state_file.write_text(json.dumps(state))
    except OSError:
        pass  # Graceful degradation - state file is optional

def cleanup_awaiting_state(input_data: dict) -> None:
    """Remove authorization state file after successful authorization.

    Args:
        input_data: Hook input data.
    """
    session_id, terminal_id = _resolve_state_identifiers(input_data)
    state_file = _get_state_file_path(session_id, terminal_id)
    state_file.unlink(missing_ok=True)

# NOTE: get_last_assistant_message removed - was checking wrong message source
# After a block, the user responds "1" in their message, not the assistant's.
# The fix: Check last_user_msg instead of last_assistant_msg for authorization.

def main():
    try:
        input_data = json.load(sys.stdin)
    except json.JSONDecodeError:
        print(json.dumps({"decision": "approve"}))
        return

    # Get the command being executed
    tool_input = input_data.get("tool_input", {})
    command = tool_input.get("command", "")

    if not command:
        print(json.dumps({"decision": "approve"}))
        return

    # Respect risk_tier_gate's classification - if already checked, allow
    if input_data.get("tier_checked"):
        print(json.dumps({"decision": "approve"}))
        return

    # Check if destructive
    destructive_match = is_destructive_command(command)

    if not destructive_match:
        print(json.dumps({"decision": "approve"}))
        return

    # Destructive command detected - check authorization
    last_user_msg = get_last_user_message(input_data)

    # Check if there's a pending authorization awaiting response
    auth_state = check_authorization_state(input_data, command)
    if auth_state:
        # We blocked this command earlier and are awaiting user response.
        # When a pending authorization exists, bare affirmatives like "yes" ARE
        # authorization - the user is saying "yes, do it" to the proposed action.
        # This is different from confirming a description ("yes, that's right").
        if has_explicit_authorization(last_user_msg, command, input_data.get("cwd", "")):
            # Explicit action words like "proceed", "do it", "delete it", or "0" / "1"
            cleanup_awaiting_state(input_data)
            print(json.dumps({"decision": "approve"}))
            return

        # When pending auth exists, bare affirmatives ("yes", "yeah", "sure") ARE authorization
        # because the user is responding to "Should I delete X?" - not confirming a description
        text_lower = last_user_msg.lower().strip()
        if text_lower in BARE_AFFIRMATIVES:
            cleanup_awaiting_state(input_data)
            print(json.dumps({"decision": "approve"}))
            return
        # Fall through to re-prompt if no authorization in user response

    if not last_user_msg:
        # No user message context - be cautious, block
        result = {
            "decision": "block",
            "reason": (
                "[AUTHORIZATION GATE] Destructive command detected without user context.\n\n"
                f"Command: {command[:100]}...\n"
                f"Pattern: {destructive_match}\n\n"
                "Cannot verify user authorization.\n\n"
                "Select:\n"
                "  0 - Proceed\n"
                "  1 - Skip/Cancel"
            ),
            "blocking_hook": "PreToolUse_authorization_gate.py",
        }

        # Query CKS for related decisions if triggers match (with caching)
        if any(trigger in command.lower() for trigger in HOOK_TRIGGERS):
            try:
                # Add CSF staging to path for discovery service
                _csf_staging = Path("P:/__csf/.staging")
                if str(_csf_staging) not in sys.path:
                    sys.path.insert(0, str(_csf_staging))

                from cks_daemon_discovery import query_cks_daemon

                # Check cache first
                cached_advisory = None
                if CKS_CACHE_ENABLED:
                    cache = get_cache()
                    cached_advisory = cache.get(command)

                if cached_advisory:
                    result["reason"] += cached_advisory
                else:
                    # Cache miss: query CKS via dynamic daemon (fast!)
                    response = query_cks_daemon(command, limit=1)
                    if response:
                        results = response.get("results", [])
                        if results and len(results) > 0:
                            r = results[0]
                            title = r.get("title", "Decision")
                            content = r.get("content", "")[:150]
                            advisory = f"\n\n💡 **Related decision**:\n   {title}\n   {content}..."

                            # Cache for future queries
                            if CKS_CACHE_ENABLED:
                                cache.set(command, advisory)

                            result["reason"] += advisory

                # Debug logging
                if CKS_CACHE_ENABLED and os.environ.get("CKS_CACHE_DEBUG"):
                    # Claude Code treats stderr as hook error - silence this
                    # print(f"[CKS] {cache.stats()}", file=sys.stderr)
                    pass
            except (ImportError, AttributeError, OSError, RuntimeError):
                pass  # CKS unavailable - advisory is optional

        print(json.dumps(result))
        return

    # Check for explicit authorization
    if has_explicit_authorization(last_user_msg):
        print(json.dumps({"decision": "approve"}))
        return

    # Check if confirmatory-only
    if is_confirmatory_only(last_user_msg):
        # NEW: Write awaiting state before blocking
        write_awaiting_state(input_data, command)

        result = {
            "decision": "block",
            "reason": (
                "[AUTHORIZATION GATE] Destructive command requires explicit authorization.\n\n"
                f"Command: {command[:100]}\n"
                f"Pattern: {destructive_match}\n\n"
                f'User said: "{last_user_msg[:100]}"\n'
                "This appears to be confirmation, not authorization to execute.\n\n"
                "Select:\n"
                "  0 - Proceed\n"
                "  1 - Skip/Cancel"
            ),
            "blocking_hook": "PreToolUse_authorization_gate.py",
        }

        # Query CKS for related decisions if triggers match (with caching)
        if any(trigger in command.lower() for trigger in HOOK_TRIGGERS):
            try:
                # Add CSF staging to path for discovery service
                _csf_staging = Path("P:/__csf/.staging")
                if str(_csf_staging) not in sys.path:
                    sys.path.insert(0, str(_csf_staging))

                from cks_daemon_discovery import query_cks_daemon

                # Check cache first
                cached_advisory = None
                if CKS_CACHE_ENABLED:
                    cache = get_cache()
                    cached_advisory = cache.get(command)

                if cached_advisory:
                    result["reason"] += cached_advisory
                else:
                    # Cache miss: query CKS via dynamic daemon (fast!)
                    response = query_cks_daemon(command, limit=1)
                    if response:
                        results = response.get("results", [])
                        if results and len(results) > 0:
                            r = results[0]
                            title = r.get("title", "Decision")
                            content = r.get("content", "")[:150]
                            advisory = f"\n\n💡 **Related decision**:\n   {title}\n   {content}..."

                            # Cache for future queries
                            if CKS_CACHE_ENABLED:
                                cache.set(command, advisory)

                            result["reason"] += advisory

                # Debug logging
                if CKS_CACHE_ENABLED and os.environ.get("CKS_CACHE_DEBUG"):
                    # Claude Code treats stderr as hook error - silence this
                    # print(f"[CKS] {cache.stats()}", file=sys.stderr)
                    pass
            except (ImportError, AttributeError, OSError, RuntimeError):
                pass  # CKS unavailable - advisory is optional

        print(json.dumps(result))
        return

    # Ambiguous - allow but could add warning
    print(json.dumps({"decision": "approve"}))

if __name__ == "__main__":
    main()