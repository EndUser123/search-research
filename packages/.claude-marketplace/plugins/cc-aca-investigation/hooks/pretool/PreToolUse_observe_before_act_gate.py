# --- plugin bootstrap ---
import sys
from pathlib import Path
_l = Path(__file__).resolve().parent.parent.parent / "__lib"
if str(_l) not in sys.path: sys.path.insert(0, str(_l))
from _bootstrap import bootstrap; _hooks_dir = bootstrap(__file__)
# --- end bootstrap ---

# PreToolUse_observe_before_act_gate.py
"""
Enforces "Observe Completely, Then Act Once" principle.

Two validation checks:
1. Skill structure check: Invoke /skills via Skill tool, or read config/SKILL.md first
2. Analysis scope check: Session-scoped reasoning only (no cross-terminal bleed)
3. Git safety check: DISABLED (read-only git operations are allowed)

Multi-terminal safe: Uses per-terminal state files with timestamp + session_id validation.
"""

import json
import os
import re
import sys
from pathlib import Path
from typing import Any

# =============================================================================
# CONFIGURATION
# =============================================================================

MAX_STATE_AGE_SECONDS = 7200  # 2 hours
STATE_DIR = Path(__file__).resolve().parent / "state" / "observe_before_act"


# =============================================================================
# TOOL NAME HELPER FUNCTIONS
# =============================================================================


def _is_skill_tool(tool_name: str) -> bool:
    """Check if tool is a Skill invocation (capitalized)."""
    return tool_name == "Skill"


def _is_read_tool(tool_name: str) -> bool:
    """Check if tool is a Read variant."""
    return tool_name in {"Read", "read_file"}


def _is_bash_tool(tool_name: str) -> bool:
    """Check if tool is a Bash variant."""
    return tool_name in {"Bash", "bash", "execute_shell_command"}


def _canonical_skill_name(value: str) -> str:
    raw = (value or "").strip().lower()
    if not raw:
        return ""
    raw = raw.lstrip("/")
    if ":" in raw:
        raw = raw.split(":")[-1].strip()
    return raw


def _is_readonly_bash_command(cmd: str) -> bool:
    """Best-effort check: allow only read/search style shell commands."""
    c = (cmd or "").lower()

    # Check for mutating operations first (block these)
    mutating_patterns = [
        " rm ",
        " del ",
        " rmdir ",
        " rd ",
        " mv ",
        " move-item ",
        " cp ",
        " copy-item ",
        " chmod ",
        " chown ",
        " git add ",
        " git commit ",
        " git reset ",
        "git clean ",
        "sed -i",
        "perl -i",  # In-place editing
        " > ",
        " >> ",
        " tee ",
        " set-content ",
        " out-file ",  # Write redirection
    ]
    for pattern in mutating_patterns:
        if pattern in f" {c} ":
            return False

    # Check for write redirection at end/start of command
    import re

    if re.search(r"\s>\s*[^|]", c):  # `> file` or `> file | cmd`
        return False
    if c.strip().startswith(">") or c.strip().startswith(">>"):
        return False

    # Allow read-only operations (explicitly listed for safety)
    readonly_patterns = [
        "cat ",
        "type ",
        "less ",
        "more ",
        "head ",
        "tail ",
        "grep ",
        "rg ",
        "egrep ",
        "find ",
        "ls ",
        "dir ",
        "sed -n ",  # sed -n is read-only (print specific lines)
        "awk 'NR==",  # awk line-specific extraction
        "awk 'FNR==",  # awk file-specific line extraction
        "file ",
        "stat ",
        "wc -l ",
        "nl ",
        "tac ",
        "shred ",  # File inspection
    ]
    return any(pattern in c for pattern in readonly_patterns)


def _loaded_skill_name() -> str:
    """Return canonical loaded skill for current terminal context, if any."""
    try:
        hooks_dir = Path(__file__).resolve().parent
        sys.path.insert(0, str(hooks_dir))
        from skill_execution_state import read_pending_state

        state = read_pending_state() or {}
        return _canonical_skill_name(str(state.get("skill", "")))
    except Exception:
        return ""


# =============================================================================
# STATE MANAGEMENT
# =============================================================================


def _get_state_path(terminal_id: str, session_id: str) -> Path:
    """Per-terminal, per-session state file (multi-terminal + multi-session safe)."""
    safe_terminal = terminal_id.replace("/", "_").replace("\\", "_")
    safe_session = session_id.replace("/", "_").replace("\\", "_")
    return STATE_DIR / f"observe_gate_{safe_terminal}_{safe_session}.json"


def _load_state(terminal_id: str, session_id: str) -> dict[str, Any]:
    """
    Load state for this terminal/session.
    Returns empty dict if file doesn't exist, is stale, session_id mismatch, or terminal_id missing.
    """
    # Graceful degradation: missing terminal_id or session_id returns empty state
    if not terminal_id or not session_id:
        return {}

    state_path = _get_state_path(terminal_id, session_id)

    if not state_path.exists():
        return {}

    try:
        with open(state_path) as f:
            state = json.load(f)

        # Validate timestamp (stale state protection)
        state_ts = state.get("timestamp", 0)
        current_ts = int(os.environ.get("CLAUDE_TIMESTAMP_MS", _current_timestamp_ms()))
        if state_ts < (current_ts - MAX_STATE_AGE_SECONDS * 1000):
            return {}  # Stale state

        # Validate session_id (multi-terminal safety)
        if state.get("session_id") != session_id:
            return {}  # Different session

        return state

    except (json.JSONDecodeError, OSError):
        return {}


def _save_state(terminal_id: str, session_id: str, state: dict[str, Any]) -> None:
    """Save state with current timestamp and session_id."""
    # Graceful degradation: missing terminal_id or session_id → no-op
    if not terminal_id or not session_id:
        return

    state_path = _get_state_path(terminal_id, session_id)
    state_path.parent.mkdir(parents=True, exist_ok=True)

    # Use counters instead of unbounded lists
    state["timestamp"] = _current_timestamp_ms()
    state["session_id"] = session_id

    # Store counters as integers (JSON-safe)
    with open(state_path, "w") as f:
        json.dump(state, f)


def _current_timestamp_ms() -> int:
    """Get current timestamp in milliseconds."""
    import time

    return int(time.time() * 1000)


# =============================================================================
# VALIDATION CHECKS
# =============================================================================


def _check_skill_structure_gate(tool_name: str, tool_input: dict[str, Any]) -> tuple[bool, str]:
    """
    Check #2: Skill structure check.

    Pattern: Manual skill invocation via bash instead of Skill tool OR
             bypassing existing skill structure (config.json/SKILL.md).

    Violation: "Structure-Driven Behavior" - not reading existing skill definition.

    Returns: (allow: bool, message: str)
    """
    if not _is_bash_tool(tool_name):
        return True, ""  # Not a bash command, pass

    cmd = tool_input.get("command", "")
    loaded_skill = _loaded_skill_name()

    # Pattern 1: Check for slash-command syntax (/skill-name)
    # Use re.match with ^ anchor to only match commands STARTING with /skill-name
    # This prevents false positives when /skill appears in arguments (e.g., "python search.py /s")
    slash_match = re.match(r"^/([A-Za-z0-9_-]+)\b", cmd.strip())
    if slash_match:
        skill_name = slash_match.group(1)
        # Resolve paths properly - try multiple possible locations
        hooks_dir = Path(__file__).resolve().parent
        possible_skill_dirs = [
            hooks_dir.parent / "skills" / skill_name,  # .claude/skills/<skill>/
            hooks_dir / "skills" / skill_name,  # .claude/hooks/skills/<skill>/
            Path.cwd() / ".claude" / "skills" / skill_name,  # repo root .claude/skills/<skill>/
        ]

        skill_dir = None
        for candidate in possible_skill_dirs:
            if candidate.exists():
                skill_dir = candidate
                break

        if skill_dir:
            config_file = skill_dir / "config.json"
            skill_md = skill_dir / "SKILL.md"

            # If skill structure exists, agent should use Skill tool
            if config_file.exists() or skill_md.exists():
                # Allow post-load read-only inspection of this exact skill.
                if (
                    loaded_skill
                    and loaded_skill == _canonical_skill_name(skill_name)
                    and _is_readonly_bash_command(cmd)
                ):
                    return True, ""
                reason = (
                    f"Skill structure gate: Skill '{skill_name}' has structured definition "
                    f"({config_file.name if config_file.exists() else skill_md.name}). "
                    f"Use the Skill tool instead of manual bash invocation."
                )
                return False, reason

    # Pattern 2: Check for direct config.json/SKILL.md access
    # Matches: .claude/skills/<name>/config.json or SKILL.md

    # Detect heredoc syntax to limit search scope (prevents false positives)
    # Heredoc content should not be matched by skill path pattern
    heredoc_pattern = r"<<\s*['\"]?(\w+)['\"]?"
    heredoc_match = re.search(heredoc_pattern, cmd)

    # Only search command portion before heredoc (if present)
    if heredoc_match:
        search_scope = cmd[: heredoc_match.start()]
    else:
        search_scope = cmd

    # Detect git commands with skill path arguments (prevents false positives).
    # These often appear after shell prefixes such as `cd repo && ...`, so don't anchor
    # at the start of the full command string.
    # Includes common git workflow commands (status, add, commit for committing own changes)
    git_cmd_pattern = (
        r"(?:^|&&|\|\||;)\s*git\s+(log|show|diff|blame|status|branch|remote|add|commit)\b"
    )
    git_cmd_match = re.search(git_cmd_pattern, search_scope)

    if git_cmd_match:
        # Git command detected - skip skill path check
        # Git commands use paths as filters/history queries, not content reading
        return True, ""

    # Search for skill path pattern in limited scope
    config_pattern = r"\.claude/skills/([A-Za-z0-9_-]+)/(config\.json|SKILL\.md)"
    config_match = re.search(config_pattern, search_scope)
    if config_match:
        skill_name = config_match.group(1)

        # Skip if the match falls inside a URL (e.g. curl/wget fetching from GitHub).
        # Local filesystem paths never start with https://, so this check is unambiguous.
        url_spans = [(m.start(), m.end()) for m in re.finditer(r"https?://\S+", search_scope)]
        if any(start <= config_match.start() < end for start, end in url_spans):
            return True, ""

        # If any skill was already loaded via Skill() this turn, the bypass
        # concern is moot — Skill() was called properly. Skills like
        # /universal-skills-manager legitimately iterate over other skills'
        # SKILL.md files as part of their own workflow.
        if loaded_skill:
            return True, ""

        # === Content-reader gate ===
        # Only block commands that directly output file CONTENT to the terminal.
        # All other commands (wc, stat, python, etc.) are allowed — they compute
        # metadata, run scripts, or process files programmatically.
        #
        # Blocked: cat, head, tail, less, more, bat — direct content output
        # Blocked: grep, rg — content search (use Grep tool instead)
        # Blocked: sed -n, awk '{print}' — content extraction via pipeline
        #
        # Allowed: wc, stat, file, du, test, touch, checksums — metadata only
        # Allowed: python, node, ruby, perl — programmatic access
        # Allowed: cp, mv, diff, git — file management / comparison
        content_reader_pattern = (
            r"(?:^|&&|\|\||;)\s*"
            r"(cat|head|tail|less|more|bat|grep|rg)"
            r"\b"
        )
        if not re.search(content_reader_pattern, search_scope):
            # Not a content-reading command — allow through
            return True, ""

        # Get the matched path for clearer error message
        matched_path = config_match.group(
            0
        )  # Full matched path like ".claude/skills/main/SKILL.md"
        reason = (
            f"Skill structure gate: Direct bash access to skill '{skill_name}' documentation.\n\n"
            f"For reading SKILL.md: Use Read tool → Read('{matched_path}')\n"
            f'For skill execution: Use Skill tool → Skill(skill="{skill_name}")'
        )
        return False, reason

    return True, ""


def _check_analysis_scope_gate(_tool_name: str, _tool_input: dict[str, Any]) -> tuple[bool, str]:
    """
    Check #3: Analysis scope check (REMOVED - was enforcing workflow preference at system level).

    REMOVED: This check was blocking legitimate debugging and investigation work.
    Reading other session data is sometimes necessary for:
    - Debugging hooks that block across terminals
    - Investigating session compaction issues
    - Cross-terminal assessment and debugging

    If session-scoped reasoning is needed, it should be enforced at the skill level,
    not as a system-level hook that blocks all workflows.
    """
    return True, ""


def _check_git_safety_gate(_tool_name: str, _tool_input: dict[str, Any]) -> tuple[bool, str]:
    """
    Check #4: Git command safety (DISABLED).

    This check was blocking read-only git operations (status, diff, log).
    Destructive operations are already handled by PreToolUse_destructive_git_guard.py.

    Returns: (allow: bool, message: str)
    """
    # DISABLED: Read-only git operations should be allowed for "Observe Completely" principle
    # Destructive git operations (reset --hard, clean -f, etc.) are blocked by
    # PreToolUse_destructive_git_guard.py which has proper scope validation
    return True, ""


# =============================================================================
# MAIN HOOK LOGIC
# =============================================================================


def main():
    try:
        raw_data = sys.stdin.read()
        if not raw_data:
            sys.exit(0)
        data = json.loads(raw_data)
    except (json.JSONDecodeError, ValueError):
        sys.exit(0)

    tool_name = data.get("tool_name", "")
    tool_input = data.get("tool_input", {})
    session_id = data.get("session_id", "")
    terminal_id = data.get("terminal_id", "")

    # Load session-scoped state (graceful degradation if missing)
    state = _load_state(terminal_id, session_id)

    # Run validation checks (stop at first failure)
    checks = [
        ("Skill structure", lambda: _check_skill_structure_gate(tool_name, tool_input)),
        ("Analysis scope", lambda: _check_analysis_scope_gate(tool_name, tool_input)),
        ("Git safety", lambda: _check_git_safety_gate(tool_name, tool_input)),
    ]

    for _check_name, check_fn in checks:
        allow, reason = check_fn()
        if not allow:
            # Return structured JSON response
            response = {
                "decision": "block",
                "reason": reason,
                "blocking_hook": f"PreToolUse_observe_before_act_gate.py:{_check_name}",
            }
            print(json.dumps(response))
            sys.exit(2)  # Exit code 2 = block

    # Save updated state
    _save_state(terminal_id, session_id, state)

    # Include any advisories in response
    if state.get("advisories"):
        response = {"continue": True, "advisories": state["advisories"]}
        print(json.dumps(response))
        state["advisories"] = []  # Clear after reporting
        _save_state(terminal_id, session_id, state)

    sys.exit(0)  # Pass


if __name__ == "__main__":
    main()
