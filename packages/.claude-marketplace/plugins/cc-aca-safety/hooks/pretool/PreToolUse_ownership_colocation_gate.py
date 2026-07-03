"""
Ownership-Colocation Gate - PreToolUse UNIVERSAL hook

Write-time safety net: blocks creation of files under known shared-infra-looking
directories when no explicit bypass flag is present.

Two tiers:
  STRICT_PATHS  - locations that are wrong when a single consumer exists.
                  Writing here is blocked unless --allow-shared-infra is set.
  ADVISORY_PATHS - look shared but are legitimately shared.
                  UPS nudge already fired; allow silently here.

Companion to ownership_colocation_nudge.py (UserPromptSubmit planning-time check).
"""

from __future__ import annotations

# --- plugin bootstrap ---
import sys
from pathlib import Path
_l = Path(__file__).resolve().parent.parent.parent / "__lib"
if str(_l) not in sys.path: sys.path.insert(0, str(_l))
from _bootstrap import bootstrap; _hooks_dir = bootstrap(__file__)
# --- end bootstrap ---


import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

# ---------------------------------------------------------------------------
# Path categories
# ---------------------------------------------------------------------------

# Locations that are almost always wrong when there's exactly one consumer.
# Matching is against the normalised path (forward slashes).
#
# SCOPE NOTE: STRICT_PATHS is intentionally narrow — it covers only paths
# where solo-consumer placement errors have actually been observed (.claude/proxy/
# being the canonical incident that motivated this gate). Do NOT speculatively
# add paths. Add reactively after a real incident demonstrates the pattern.
# Broad coverage → more false positives → bypass flag becomes a reflex.
STRICT_PATHS: list[re.Pattern[str]] = [
    re.compile(r"\.claude[/\\]proxy[/\\]", re.IGNORECASE),
    re.compile(r"\.claude[/\\]infrastructure[/\\]", re.IGNORECASE),
    re.compile(r"\.claude[/\\]adapters[/\\]", re.IGNORECASE),
]

# Locations that look shared but are legitimately used by multiple consumers.
# UPS nudge already reminded the model at planning time — allow silently here.
ADVISORY_PATHS: list[re.Pattern[str]] = [
    re.compile(r"\.claude[/\\]shared[/\\]", re.IGNORECASE),
    re.compile(r"\.claude[/\\]lib[/\\]", re.IGNORECASE),
    re.compile(r"\.claude[/\\]__lib[/\\]", re.IGNORECASE),
    re.compile(r"\.claude[/\\]utils[/\\]", re.IGNORECASE),
]

BYPASS_FLAG = "--allow-shared-infra"

_BLOCK_LOG = _hooks_dir.parent / "logs" / "diagnostics" / "pretooluse_blocks.jsonl"


def _log_block(file_path: str, tool_name: str) -> None:
    """Append a block event to the flat-file diagnostics log (Action 5)."""
    try:
        _BLOCK_LOG.parent.mkdir(parents=True, exist_ok=True)
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "hook": "ownership_colocation_gate",
            "tool": tool_name,
            "path": file_path,
        }
        with _BLOCK_LOG.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(entry) + "\n")
    except OSError:
        pass  # Never let logging failure block the hook output


def _normalize(path: str) -> str:
    """Normalise path separators for cross-platform matching."""
    return path.replace("\\", "/")


def _extract_path(tool_name: str, tool_input: dict) -> str:
    """Extract the target file path from tool input."""
    if tool_name == "Write":
        return tool_input.get("file_path", "")
    if tool_name in ("Edit", "MultiEdit"):
        return tool_input.get("file_path", tool_input.get("path", ""))
    return ""


def _matches(path: str, patterns: list[re.Pattern[str]]) -> bool:
    norm = _normalize(path)
    return any(p.search(norm) for p in patterns)


def _prompt_has_bypass(data: dict) -> bool:
    """Return True if the user's prompt contains the bypass flag."""
    prompt = ""
    # Try common locations for the current prompt text
    for key in ("prompt", "userPrompt", "user_prompt"):
        val = data.get(key, "")
        if isinstance(val, str) and val:
            prompt = val
            break
    # Also check env override
    if os.environ.get("OWNERSHIP_COLOCATION_BYPASS", "").lower() in ("1", "true"):
        return True
    return BYPASS_FLAG in prompt



def run(data: dict) -> dict | None:
    """In-process execution entry point."""
    tool_name = data.get("tool_name", "")
    if tool_name not in ("Write", "Edit", "MultiEdit"):
        return None

    tool_input = data.get("tool_input", {})
    if not isinstance(tool_input, dict):
        return None

    file_path = _extract_path(tool_name, tool_input)
    if not file_path:
        return None

    # Advisory paths -- UPS nudge already fired; allow silently
    if _matches(file_path, ADVISORY_PATHS):
        return None

    # Strict paths -- block unless bypass flag present
    if _matches(file_path, STRICT_PATHS):
        if _prompt_has_bypass(data):
            return None

        _log_block(file_path, tool_name)
        lines = [
            "OWNERSHIP-COLOCATION VIOLATION",
            "",
            f"Attempted write: {file_path}",
            "",
            "This path implies SHARED infrastructure, but it may have exactly one consumer.",
            "",
            "Before writing here, verify consumer count:",
            "  grep -r 'proxy' --include='*.py' --include='*.md' skills/ hooks/",
            "  (Adapt the search term to match the infrastructure you're placing.)",
            "",
            "Decision:",
            "  - Exactly one consumer: place it INSIDE that consumer's directory instead.",
            "  - Multiple consumers (N >= 2): this shared location is correct.",
            "",
            "See Pattern 6 (questioning_patterns.md): 'Who Exclusively Owns This?'",
            "",
            "To bypass: Run the grep above, confirm N consumers, then add to your message:",
            f"  {BYPASS_FLAG} [N-consumers]",
            "  Example: --allow-shared-infra 3-consumers",
        ]
        return {
            "decision": "block",
            "reason": chr(10).join(lines),
            "blocking_hook": "PreToolUse_ownership_colocation_gate.py",
        }

    # No match -- allow
    return None


def main() -> None:
    raw = sys.stdin.read()
    try:
        data = json.loads(raw)
    except (json.JSONDecodeError, ValueError):
        # Malformed input — fail open
        print("{}")
        sys.exit(0)

    tool_name = data.get("tool_name", "")
    if tool_name not in ("Write", "Edit", "MultiEdit"):
        print("{}")
        sys.exit(0)

    tool_input = data.get("tool_input", {})
    if not isinstance(tool_input, dict):
        print("{}")
        sys.exit(0)

    file_path = _extract_path(tool_name, tool_input)
    if not file_path:
        print("{}")
        sys.exit(0)

    # Advisory paths — UPS nudge already fired; allow silently
    if _matches(file_path, ADVISORY_PATHS):
        print("{}")
        sys.exit(0)

    # Strict paths — block unless bypass flag present
    if _matches(file_path, STRICT_PATHS):
        if _prompt_has_bypass(data):
            print("{}")
            sys.exit(0)

        _log_block(file_path, tool_name)
        block_message = f"""\
⛔ OWNERSHIP-COLOCATION VIOLATION

Attempted write: {file_path}

This path implies SHARED infrastructure, but it may have exactly one consumer.

Before writing here, verify consumer count:
  grep -r 'proxy' --include='*.py' --include='*.md' skills/ hooks/
  (Adapt the search term to match the infrastructure you're placing.)

Decision:
  • Exactly one consumer → place it INSIDE that consumer's directory instead.
  • Multiple consumers (N ≥ 2) → this shared location is correct.

See Pattern 6 (questioning_patterns.md): "Who Exclusively Owns This?"

To bypass: Run the grep above, confirm N consumers, then add to your message:
  `{BYPASS_FLAG} [N-consumers]`
  Example: --allow-shared-infra 3-consumers
"""
        print(json.dumps({"decision": "block", "reason": block_message.strip()}))
        sys.exit(2)

    # No match — allow
    print("{}")
    sys.exit(0)


if __name__ == "__main__":
    main()
