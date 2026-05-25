"""PostToolUse hook to record locally-found artifacts into session ledger.

Monitors Grep, Glob, and Read tool results. When matches are found,
records the search keyword and source path into artifact_ledger for
later cross-validation against external fetch/install commands.
"""
import json
import re
import sys
from pathlib import Path

# --- plugin bootstrap ---
_l = Path(__file__).resolve().parent.parent.parent / "__lib"
if str(_l) not in sys.path: sys.path.insert(0, str(_l))
from _bootstrap import bootstrap; _hooks_dir = bootstrap(__file__)
# --- end bootstrap ---
from artifact_ledger import record

TRACKED_TOOLS = {"Grep", "Glob", "Read"}


def run(data: dict) -> dict | None:
    """Record found artifacts from Grep/Glob/Read into ledger.

    Args:
        data: Hook input dict with tool_name, tool_input, tool_response, etc.

    Returns:
        None (advisory hook, always allows)
    """
    tool = data.get("tool_name", "")
    if tool not in TRACKED_TOOLS:
        return None

    session_id = data.get("session_id", "")
    if not session_id:
        return None

    ti = data.get("tool_input", {}) or {}
    resp = data.get("tool_response", "") or ""

    # Convert response to string if dict
    if isinstance(resp, dict):
        resp = json.dumps(resp)

    # Extract keyword from tool input
    keyword = ti.get("pattern") or ti.get("file_path", "")
    if not keyword:
        return None

    # Use stem for file paths; full pattern for regex/glob
    if "/" in str(keyword) or "\\" in str(keyword):
        keyword = Path(str(keyword)).stem
    keyword = str(keyword)

    # Extract source paths from response (first few matches)
    # Windows paths: C:\path\to\file.py, Unix paths: /path/to/file.py, relative: src/file.py
    sources = re.findall(
        r"[A-Za-z]:[\\/][^\s:]*\.(?:py|md|jsonl|json|ts|js)|"
        r"/[^\s:]*\.(?:py|md|jsonl|json|ts|js)|"
        r"[^\s:]*[\\/][^\s:]*\.(?:py|md|jsonl|json|ts|js)",
        resp
    )[:3]

    # If Read tool, use the file path directly
    if tool == "Read" and not sources:
        sources = [ti.get("file_path", "")]

    turn = data.get("turn_index", 0)
    for src in sources:
        if src:
            # Normalize Windows paths to forward slashes for consistent matching
            src = Path(src).as_posix()
            record(session_id, keyword, src, turn)

    return None
