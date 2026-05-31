"""PreToolUse hook enforcing evidence hierarchy: local sources before external fetch.

Blocks WebFetch/WebSearch/npm install/pip install when a local artifact
was recently found (same keyword) to enforce 'search local first' principle.

Bypass: export IGNORE_LOCAL_EVIDENCE=1
"""



# --- plugin bootstrap ---
import sys
from pathlib import Path

_lib = Path(__file__).resolve().parent.parent.parent / "__lib"
if str(_lib) not in sys.path:
    sys.path.insert(0, str(_lib))
from _bootstrap import bootstrap
_hooks_dir = bootstrap(__file__)
# --- end bootstrap ---

import os
import re
import sys
from pathlib import Path

from artifact_ledger import find_matches

EXTERNAL_TOOLS = {"WebFetch", "WebSearch"}
# Bash commands that trigger external fetch/install checks
EXTERNAL_BASH = re.compile(
    r"\b(curl|wget|npm\s+install|pip\s+install|pip\s+search|brew\s+install|"
    r"mcp__serpapi__search|mcp__brave__brave_web_search|mcp__MiniMax__web_search)\b",
    re.IGNORECASE
)


def _extract_query(data: dict) -> str:
    """Extract search query from tool input.

    Returns:
        Combined query string from URL, search terms, or bash command.
    """
    tool = data.get("tool_name", "")
    ti = data.get("tool_input", {}) or {}

    if tool in EXTERNAL_TOOLS:
        url = ti.get("url", "")
        query = ti.get("query", "")
        prompt = ti.get("prompt", "")
        return f"{url} {query} {prompt}"

    if tool == "Bash":
        cmd = ti.get("command", "")
        if EXTERNAL_BASH.search(cmd):
            return cmd

    return ""


def _get_session_id(data: dict) -> str | None:
    """Extract session_id from hook input with fallback to env var.

    Returns:
        session_id if found, None otherwise
    """
    session_id = data.get("session_id") or os.environ.get("CLAUDE_SESSION_ID")
    return str(session_id) if session_id else None


def run(data: dict) -> dict | None:
    """Check if external fetch contradicts recent local findings.

    Args:
        data: Hook input dict

    Returns:
        None to allow, or dict with block signal (exit 2)
    """
    session_id = _get_session_id(data)
    if not session_id:
        return None

    query = _extract_query(data)
    if not query:
        return None

    # Check for bypass via env var (user sets: export IGNORE_LOCAL_EVIDENCE=1)
    # Note: PreToolUse data does not carry the user's message text, so
    # string-in-message bypass cannot work here; env var is the correct mechanism.
    if os.environ.get("IGNORE_LOCAL_EVIDENCE"):
        return None

    # Search ledger for matching keywords
    matches = find_matches(session_id, query)
    if not matches:
        return None

    # Found contradictory evidence: local source was just found
    citations = "\n".join(
        f"  • '{m['keyword']}' found at {m['source']} (turn {m['turn']})"
        for m in matches[:3]
    )

    msg = (
        f"⛔ EVIDENCE HIERARCHY: Local source already asserted\n\n"
        f"You previously located:\n{citations}\n\n"
        f"This action queries external sources for the same topic. "
        f"Either use the local source or add --ignore-local-evidence with justification."
    )

    print(msg, file=sys.stderr)
    return {"decision": "block", "reason": msg}


if __name__ == "__main__":
    # Manual test
    test_data = {
        "session_id": "test-123",
        "tool_name": "WebFetch",
        "tool_input": {"url": "https://example.com", "query": "sqd skill"},
    }
    result = run(test_data)
    print(f"Result: {result}")
