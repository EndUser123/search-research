"""cc-lazy-closure-debt UserPromptSubmit hook — surfaces prior deferrals as
additionalContext so the model is aware of untracked debt from previous turns.

Reads P:/.claude/state/cc-lazy-closure-debt/{terminal_id}.jsonl, filters to
items newer than 24h, takes the 5 most recent, and returns them in a
readable "Xh ago" format. Empty store -> no additionalContext.
"""
from __future__ import annotations

# --- plugin bootstrap ---
import sys
from pathlib import Path

_lib = Path(__file__).resolve().parent.parent.parent / "__lib"
if str(_lib) not in sys.path:
    sys.path.insert(0, str(_lib))
from _bootstrap import bootstrap
_hooks_dir = bootstrap(__file__)
# --- end bootstrap ---

import json
import os
import re
import sys
import time
from pathlib import Path

from debt_store import recent_deferrals, _safe_id  # noqa: E402
from workflow_review import (  # noqa: E402
    classify_workflow,
    format_workflow_review,
    format_workflow_review_stats,
    record_workflow_review,
    summarize_workflow_reviews,
)

MAX_AGE_H = 24.0
MAX_COUNT = 5
_DEBT_REVIEW_RE = re.compile(r"(?<!\w)/debt\s+review\b|\bdebt\s+review\b", re.IGNORECASE)


def _resolve_terminal_id(data: dict) -> str:
    session_obj = data.get("session") or {}
    if isinstance(session_obj, dict):
        tid = session_obj.get("terminal_id") or session_obj.get("terminalId")
        if tid:
            return str(tid)
    tid = data.get("terminal_id") or data.get("terminalId")
    if tid:
        return str(tid)
    return os.environ.get("CLAUDE_TERMINAL_ID", "default")


def _format_age(ts: int, now: int) -> str:
    delta = max(0, int(now) - int(ts))
    if delta < 60:
        return f"{delta}s ago"
    if delta < 3600:
        return f"{delta // 60}m ago"
    if delta < 86400:
        return f"{delta // 3600}h ago"
    return f"{delta // 86400}d ago"


def _format_occurrence_suffix(item: dict) -> str:
    count = int(item.get("occurrences", 1) or 1)
    return f" x{count}" if count > 1 else ""


def _format_context(items: list[dict]) -> str:
    if not items:
        return ""
    now = int(time.time())
    formatted = [
        (
            f"\"{it.get('phrase','')}\""
            f" ({_format_age(int(it.get('ts', 0)), now)})"
            f"{_format_occurrence_suffix(it)}"
        )
        for it in items
    ]
    n = len(items)
    if n == 1:
        body = formatted[0]
    else:
        # Simple "a, b, and c" joining for readability
        if n == 2:
            body = f"{formatted[0]} and {formatted[1]}"
        else:
            body = ", ".join(formatted[:-1]) + f", and {formatted[-1]}"
    if n == 1:
        first_phrase = formatted[0].split(" (")[0].strip('"')
        task_directive = (
            'On this turn, call TaskCreate exactly once with subject="Deferral: '
            + first_phrase
            + '" to formalize the one pending deferral above, then briefly '
            'acknowledge. Do not run /debt.'
        )
    else:
        task_directive = (
            f"On this turn, call TaskCreate {n} times — one task per unique deferral "
            "phrase listed above, with subject='Deferral: <phrase>' for each — "
            "then briefly acknowledge. Do not run /debt."
        )
    return (
        f"[cc-lazy-closure-debt] You have {n} pending deferral "
        f"{'item' if n == 1 else 'items'} from previous turns: {body}. "
        + task_directive
    )



def _format_review_context(terminal_id: str, data: dict, items: list[dict]) -> str:
    review = classify_workflow(data, items)
    record_workflow_review(data, review)
    stats_line = ""
    prompt_text = " ".join(
        str((data.get(key, "") or "")) for key in ("prompt", "user_prompt", "message", "response")
    )
    if _DEBT_REVIEW_RE.search(prompt_text):
        stats = summarize_workflow_reviews(terminal_id)
        stats_line = format_workflow_review_stats(stats)
    return "\n".join(
        block for block in (format_workflow_review(review), stats_line) if block
    )


def run(data: dict) -> dict:
    """Main entry point.

    Returns a hookDecision dict with additionalContext when debt exists,
    or a no-op Continue-true when the store is empty.
    """
    terminal_id = _safe_id(_resolve_terminal_id(data))
    items = recent_deferrals(
        terminal_id=terminal_id,
        max_age_h=MAX_AGE_H,
        max_count=MAX_COUNT,
    )
    if not items:
        return {"continue": True}
    review_context = _format_review_context(terminal_id, data, items)
    return {
        "continue": True,
        "hookSpecificOutput": {
            "hookEventName": "UserPromptSubmit",
            "additionalContext": "\n\n".join(
                block for block in (_format_context(items), review_context) if block
            ),
        },
    }


if __name__ == "__main__":
    raw = sys.stdin.read()
    try:
        data = json.loads(raw) if raw.strip() else {}
    except json.JSONDecodeError:
        data = {}
    result = run(data)
    print(json.dumps(result))
    sys.exit(0)
