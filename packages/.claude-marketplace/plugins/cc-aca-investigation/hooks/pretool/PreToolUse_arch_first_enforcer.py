# --- plugin bootstrap ---
import sys
from pathlib import Path
_l = Path(__file__).resolve().parent.parent.parent / "__lib"
if str(_l) not in sys.path: sys.path.insert(0, str(_l))
from _bootstrap import bootstrap, state_root; _hooks_dir = bootstrap(__file__)
# --- end bootstrap ---

"""
Arch-First Enforcer - PreToolUse hook

Enforces arch-first workflow when template update declarations are detected.

Problem: LLMs declare "I'll update the template" but then use other tools without
actually updating the template file (Declaration ≠ Execution).

Solution: Block non-arch tools until template is updated, ensuring Read → Edit → Diff workflow.
"""

import json
import re
import sys
from functools import lru_cache
from pathlib import Path

# Import canonical utilities instead of duplicating code
# Use get_terminal_id from runtime_env for proper hook_ledger detection
from __lib.runtime_env import get_terminal_id as canonical_get_terminal_id

# State directory for declaration tracking (must match declaration_reminder.py)
STATE_DIR = state_root()

# Bypass flag
BYPASS_FLAG = "--allow-skip-arch-update"


@lru_cache(maxsize=256)
def _is_arch_file(path: str) -> bool:
    """Check if path is an architecture template file."""
    if not path:
        return False

    # Normalize Windows paths
    path = path.replace("\\", "/")

    # Direct arch/ directory match
    if path.startswith("arch/") or path.startswith(".claude/arch/") or "/arch/" in path:
        return True

    # SKILL.md files (with or without leading /)
    if re.search(r"(?:^|/)SKILL\.md$", path, re.IGNORECASE):
        return True

    # Template patterns
    template_patterns = [
        r"packages/arch/skill/",
        r"\.claude/skills/arch/",
    ]
    for pattern in template_patterns:
        if re.search(pattern, path, re.IGNORECASE):
            return True

    return False


@lru_cache(maxsize=128)
def _get_state_file(terminal_id: str) -> Path:
    """Get path to declaration state file for terminal (cached)."""
    safe_id = re.sub(r"[^a-zA-Z0-9_.-]+", "_", str(terminal_id))
    return STATE_DIR / f"arch_declaration_{safe_id}.json"


def _store_declaration_state(terminal_id: str, path: str) -> None:
    """Store declaration state (for testing coordination with declaration_reminder hook)."""
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    state_file = _get_state_file(terminal_id)
    try:
        with open(state_file, "w", encoding="utf-8") as f:
            json.dump({"path": path, "timestamp": None}, f)
    except OSError:
        pass


def _load_declaration_state(terminal_id: str) -> dict | None:
    """Load declaration state from file.

    FIXED: Removed unnecessary exists() check (TOCTOU anti-pattern).
    The open() call will fail with FileNotFoundError if the file doesn't exist,
    which is caught by the OSError exception handler.
    """
    state_file = _get_state_file(terminal_id)
    try:
        with open(state_file, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError):
        return None


def _clear_declaration_state(terminal_id: str) -> None:
    """Clear declaration state (called after template is updated).

    FIXED: Removed unnecessary exists() check (TOCTOU anti-pattern).
    The unlink() call will fail with FileNotFoundError if the file doesn't exist,
    which is caught by the OSError exception handler.
    """
    state_file = _get_state_file(terminal_id)
    try:
        state_file.unlink()
    except OSError:
        pass


def main():
    """PreToolUse hook entry point."""
    data = json.load(sys.stdin)
    tool_name = data.get("tool_name", "")
    tool_input = data.get("tool_input", {}) or {}

    # Check for bypass flag in prompt
    prompt = data.get("prompt", "")
    if BYPASS_FLAG in prompt:
        print(json.dumps({"decision": "approve"}))
        sys.exit(0)

    # Use canonical terminal ID detection (includes hook_ledger detection)
    terminal_id = canonical_get_terminal_id(data) or "default"

    # Only process if there's an active declaration
    declaration_state = _load_declaration_state(terminal_id)
    if not declaration_state:
        print(json.dumps({"decision": "approve"}))
        sys.exit(0)

    declared_path = declaration_state.get("path", "")

    # Allow Read tool for reading template files
    if tool_name == "Read":
        read_path = tool_input.get("file_path", "")
        if _is_arch_file(read_path):
            # Reading an arch file - clear state and allow
            _clear_declaration_state(terminal_id)
            print(json.dumps({"decision": "approve"}))
            sys.exit(0)
        # Reading non-arch file while declaration exists - block
        # (must read arch file first to complete declaration)

    # Allow Edit/Write tools for arch files
    if tool_name in ("Edit", "Write"):
        edit_path = tool_input.get("path", tool_input.get("file_path", ""))
        if _is_arch_file(edit_path):
            # Updating an arch file - clear state
            _clear_declaration_state(terminal_id)
            print(json.dumps({"decision": "approve"}))
            sys.exit(0)

    # Block other tools until template is updated
    block_message = f"""
⛔ **TEMPLATE UPDATE REQUIRED FIRST**

You declared: "I'll update the template"

Before using {tool_name}, you MUST:
1. **Read** the template file: `{declared_path}`
2. **Edit/Write** the change with diff
3. **Show** the explanation

**Why this matters**: Declaration ≠ Execution. You said you'd update the template,
but haven't invoked Read/Edit tools for `{declared_path}` yet.

To bypass this check: Add {BYPASS_FLAG} to your message.

Complete the template update first, then proceed with other tools.
"""

    print(json.dumps({"decision": "block", "reason": block_message.strip()}))
    sys.exit(2)


if __name__ == "__main__":
    main()
