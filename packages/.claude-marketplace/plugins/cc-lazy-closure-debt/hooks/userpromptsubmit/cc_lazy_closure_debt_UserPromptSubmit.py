"""cc-lazy-closure-debt UserPromptSubmit hook — surfaces prior deferrals as
additionalContext so the model is aware of untracked debt from previous turns.

Also ingests new Stop-block residues (gate-residue FP loop v1), classifies
them against the current turn, and emits TaskCreate directives for confirmed_FP
blocks (one promotion per ledger_id ever, via tombstone).

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
from gate_residue import (  # noqa: E402
    classify_block,
    ingest_new_blocks,
    mark_promoted,
    promoted_ledger_ids,
    recent_residue,
    record_classification,
)
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


# --- gate-residue helpers (v1 -- PreToolUse is a documented gap) -------------

def _extract_tool_use_content(message_content: object) -> list[dict]:
    """Extract tool_use blocks, matching the skill-guard schema exactly."""
    if not isinstance(message_content, list):
        return []
    tools: list[dict] = []
    for block in message_content:
        if isinstance(block, dict) and block.get("type") == "tool_use":
            name = str(block.get("name", "")).strip()
            if name:
                tools.append(block)
    return tools


def _extract_text_content(message_content: object) -> str:
    """Extract text blocks, matching the skill-guard schema exactly."""
    if isinstance(message_content, list):
        return " ".join(
            block.get("text", "")
            for block in message_content
            if isinstance(block, dict) and block.get("type") == "text"
        )
    if isinstance(message_content, str):
        return message_content
    return ""


def _read_post_block_turn(data: dict) -> tuple[list[dict], str]:
    """Reverse-scan the transcript for the CURRENT turn's tool_use blocks + text.

    Reuses the proven _parse_transcript_snapshot schema (skill-guard, fact #4).
    Returns (tools, text). Safe: returns empty on any error.
    """
    transcript_path = data.get("transcript_path")
    if not transcript_path:
        return [], ""

    try:
        transcript = Path(transcript_path)
        if not transcript.exists():
            return [], ""
        content = transcript.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return [], ""

    all_tools: list[dict] = []
    turn_text: str = ""
    found_assistant = False

    try:
        for line in reversed(content.strip().split("\n")):
            if not line.strip():
                continue
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue

            msg_type = entry.get("type", "")
            message = entry.get("message", entry)
            if not isinstance(message, dict):
                message = {}
            message_content = message.get("content", entry.get("content", ""))
            role = entry.get("role", "") or message.get("role", "")

            is_assistant = (
                (msg_type == "message" and role == "assistant")
                or msg_type == "assistant"
                or role == "assistant"
            )
            is_user = role == "user" or msg_type == "user"

            if is_assistant:
                if found_assistant and is_user:
                    break
                if not found_assistant:
                    turn_text = _extract_text_content(message_content)
                    found_assistant = True
                all_tools.extend(_extract_tool_use_content(message_content))
            elif is_user and msg_type != "system-reminder":
                text = _extract_text_content(message_content).strip()
                if text and not text.startswith("Base directory for this skill"):
                    if not found_assistant:
                        break
                    elif found_assistant:
                        break
    except Exception:
        return [], ""

    return all_tools, turn_text


def _format_residue_context(residue_rows: list[dict]) -> str:
    """One-line summary of unresolved/disputed blocks (never a TaskCreate)."""
    if not residue_rows:
        return ""
    parts = []
    for r in residue_rows:
        label = r.get("classification", "unresolved")
        gate = r.get("gate_name", "?")
        part = f"{gate} ({label})"
        reason = (r.get("block_reason_excerpt") or "")[:80]
        if reason:
            part += f": {reason}"
        parts.append(part)
    body = "; ".join(parts)
    return (
        f"[cc-lazy-closure-debt residue] {len(residue_rows)} unsettled "
        f"gate block{'s' if len(residue_rows) != 1 else ''}: {body}. "
        "No action needed for unresolved items."
    )


def _format_fp_directive(fp_rows: list[dict]) -> str:
    """TaskCreate directive for each confirmed_fp block not yet promoted.

    Each unique ledger_id gets one TaskCreate subject. Caller is responsible
    for filtering to unpromoted rows only.
    """
    if not fp_rows:
        return ""
    parts = []
    for r in fp_rows:
        gate = r.get("gate_name", "unknown_gate")
        artifact = r.get("artifact") or {}
        tool = artifact.get("tool", "")
        target = artifact.get("target", "")
        excerpt = (r.get("block_reason_excerpt") or "")[:120]
        parts.append(
            f"- Gate: {gate}" + (f" ({excerpt})" if excerpt else "")
            + f"\n  Refuted via: {tool} on {target}"
        )
    detail = "\n".join(parts)
    n = len(fp_rows)
    return (
        f"[cc-lazy-closure-debt FP] {n} likely false positive gate "
        f"block{'s' if n != 1 else ''} identified (artifact seen):\n"
        f"{detail}\n"
        f"On this turn, call TaskCreate {n} time{'s' if n != 1 else ''} — "
        f"one task per FP block, with subject='FP candidate: <gate_name>' for each."
    )


def run(data: dict) -> dict:
    """Main entry point.

    Returns a hookDecision dict with additionalContext when debt exists,
    or a no-op Continue-true when the store is empty.
    """
    terminal_id = _safe_id(_resolve_terminal_id(data))

    # --- Deferral context (unchanged) ---------------------------------------
    items = recent_deferrals(
        terminal_id=terminal_id,
        max_age_h=MAX_AGE_H,
        max_count=MAX_COUNT,
    )
    context_blocks: list[str] = []
    if items:
        review_context = _format_review_context(terminal_id, data, items)
        context_blocks.append("\n\n".join(
            block for block in (_format_context(items), review_context) if block
        ))

    # --- Gate-residue ingestion + classification (advisory, fail-open) ------
    try:
        new_blocks = ingest_new_blocks(terminal_id=terminal_id)
    except Exception:
        new_blocks = []  # fail-open
    if new_blocks:
        tools, turn_text = _read_post_block_turn(data)
        already_promoted = promoted_ledger_ids(terminal_id)
        fp_directive_rows: list[dict] = []
        residue_rows: list[dict] = []

        for block in new_blocks:
            try:
                cls, artifact = classify_block(block, tools, turn_text)
            except Exception:
                cls, artifact = "unresolved", None

            block["classification"] = cls
            block["artifact"] = artifact

            # Persist classification.
            try:
                record_classification(
                    terminal_id, block.get("ledger_id", ""), cls, artifact,
                )
            except Exception:
                pass

            lid = block.get("ledger_id", "")
            if cls == "confirmed_fp" and lid and lid not in already_promoted:
                fp_directive_rows.append(block)
            elif cls in ("unresolved", "disputed"):
                residue_rows.append(block)

        if fp_directive_rows:
            # Emit TaskCreate directives and mark promoted.
            context_blocks.append(_format_fp_directive(fp_directive_rows))
            for r in fp_directive_rows:
                try:
                    mark_promoted(terminal_id, r.get("ledger_id", ""))
                except Exception:
                    pass

        if residue_rows:
            context_blocks.append(_format_residue_context(residue_rows))

    if not context_blocks:
        return {"continue": True}

    return {
        "continue": True,
        "hookSpecificOutput": {
            "hookEventName": "UserPromptSubmit",
            "additionalContext": "\n\n---\n\n".join(context_blocks),
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
