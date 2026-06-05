"""Heuristic review helpers for cc-lazy-closure-debt.

The debt tracker should not just record repeated deferrals. It should also
surface whether the supervised workflow would benefit from:

- a local fix,
- a focused subagent,
- or an external LLM judge / reviewer.
"""
from __future__ import annotations

import json
import os
import re
import threading
import time
from pathlib import Path
from typing import Any

from debt_store import DEFAULT_STATE_ROOT, PLUGIN_NAME, _safe_id

_COMPARE_RE = re.compile(
    r"\b(best|better|optimal|recommend|recommendation|compare|comparison|"
    r"which\s+(?:option|approach|path|one)|should\s+we|trade[- ]?off|highest[- ]?roi)\b",
    re.IGNORECASE,
)
_SUBAGENT_RE = re.compile(
    r"\b(agent|subagent|delegate|delegation|parallel|multi[- ]file|multiple files?)\b",
    re.IGNORECASE,
)

_review_lock = threading.Lock()


def _resolve_terminal_id(data: dict[str, Any] | None) -> str:
    session = (data or {}).get("session") or {}
    if isinstance(session, dict):
        tid = session.get("terminal_id") or session.get("terminalId")
        if tid:
            return str(tid)
    tid = (data or {}).get("terminal_id") or (data or {}).get("terminalId")
    if tid:
        return str(tid)
    return os.environ.get("CLAUDE_TERMINAL_ID", "default")


def _review_state_dir(root: Path | None = None) -> Path:
    base = Path(root) if root is not None else DEFAULT_STATE_ROOT
    path = base / PLUGIN_NAME / "workflow-reviews"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _review_state_path(terminal_id: str, root: Path | None = None) -> Path:
    return _review_state_dir(root) / f"{_safe_id(terminal_id)}.jsonl"


def _tool_events(data: dict[str, Any] | None) -> list[dict[str, Any]]:
    events = (data or {}).get("tool_events", [])
    return events if isinstance(events, list) else []


def _file_op_count(data: dict[str, Any] | None) -> int:
    count = 0
    for event in _tool_events(data):
        if not isinstance(event, dict):
            continue
        name = str(event.get("name", "") or "")
        if name in ("Edit", "Write", "MultiEdit"):
            count += 1
    return count


def _agent_used(data: dict[str, Any] | None) -> bool:
    for event in _tool_events(data):
        if isinstance(event, dict) and event.get("name") == "Agent":
            return True
    return False


def _join_text(parts: list[str]) -> str:
    return " ".join(part.strip() for part in parts if part and part.strip())


def classify_workflow(
    data: dict[str, Any] | None,
    debt_items: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Classify whether the last supervised workflow should stay local, use a subagent,
    or benefit from an external LLM review.

    The function is deliberately heuristic and fail-open. It is intended to support
    operator judgment, not replace it.
    """
    items = debt_items or []
    prompt = _join_text(
        [
            str((data or {}).get("prompt", "") or ""),
            str((data or {}).get("user_prompt", "") or ""),
            str((data or {}).get("message", "") or ""),
            str((data or {}).get("response", "") or ""),
        ]
    )
    file_ops = _file_op_count(data)
    agent_used = _agent_used(data)
    max_occurrences = max((int(it.get("occurrences", 1) or 1) for it in items), default=1)
    unique_items = len(items)

    signals: list[str] = []
    if file_ops:
        signals.append(f"{file_ops} file ops")
    if agent_used:
        signals.append("Agent used")
    if unique_items:
        signals.append(f"{unique_items} unique debt item{'s' if unique_items != 1 else ''}")
    if max_occurrences > 1:
        signals.append(f"max occurrence count {max_occurrences}")

    if file_ops >= 3 and not agent_used:
        return {
            "recommendation": "subagent",
            "summary": (
                "The workflow touched multiple files without Agent delegation. "
                "A focused subagent can absorb the file-level analysis and keep the main "
                "context for synthesis."
            ),
            "signals": signals,
        }

    if unique_items == 1 and max_occurrences >= 2:
        return {
            "recommendation": "local",
            "summary": (
                "The same debt phrase repeated. Fix it once, mark it formalized, and avoid "
                "spawning another task for the same underlying issue."
            ),
            "signals": signals,
        }

    if _COMPARE_RE.search(prompt) and not _SUBAGENT_RE.search(prompt):
        return {
            "recommendation": "external_llm",
            "summary": (
                "This looks like a comparative or decision-heavy turn. An external LLM judge "
                "is useful when the question is about ranking options or checking rubric-like "
                "quality, not just editing local code."
            ),
            "signals": signals,
        }

    if unique_items >= 2 and not agent_used and file_ops >= 1:
        return {
            "recommendation": "subagent",
            "summary": (
                "Multiple debt items surfaced alongside local edits. A subagent can review "
                "the impacted surfaces independently and keep the main turn focused."
            ),
            "signals": signals,
        }

    return {
        "recommendation": "local",
        "summary": (
            "The workflow is bounded enough to keep local. Use the debt item as a reminder "
            "to close the loop directly before escalating."
        ),
        "signals": signals,
    }


def record_workflow_review(
    data: dict[str, Any] | None,
    review: dict[str, Any],
    state_root: Path | None = None,
) -> None:
    """Append one review decision to the production log.

    Logging is best-effort and must never interfere with the actual workflow.
    """
    try:
        terminal_id = _safe_id(_resolve_terminal_id(data))
        signals = review.get("signals", [])
        record = {
            "ts": int(time.time()),
            "terminal_id": terminal_id,
            "recommendation": str(review.get("recommendation", "local") or "local"),
            "signals": list(signals) if isinstance(signals, list) else [],
        }
        path = _review_state_path(terminal_id, state_root)
        with _review_lock:
            with open(path, "a", encoding="utf-8") as f:
                f.write(json.dumps(record, ensure_ascii=True))
                f.write("\n")
                f.flush()
                os.fsync(f.fileno())
    except Exception:
        return


def summarize_workflow_reviews(
    terminal_id: str,
    max_age_h: float = 24.0,
    state_root: Path | None = None,
) -> dict[str, Any]:
    """Summarize recent review recommendations for one terminal."""
    tid = _safe_id(terminal_id)
    path = _review_state_path(tid, state_root)
    if not path.exists():
        return {"terminal_id": tid, "total": 0, "counts": {}}

    cutoff = int(time.time()) - int(max_age_h * 3600)
    counts = {"local": 0, "subagent": 0, "external_llm": 0}
    total = 0
    last_ts = 0
    try:
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if not isinstance(obj, dict):
                    continue
                ts = int(obj.get("ts", 0))
                if ts < cutoff:
                    continue
                rec = str(obj.get("recommendation", "") or "")
                if rec in counts:
                    counts[rec] += 1
                    total += 1
                    last_ts = max(last_ts, ts)
    except OSError:
        return {"terminal_id": tid, "total": 0, "counts": {}}

    return {"terminal_id": tid, "total": total, "counts": counts, "last_ts": last_ts}


def format_workflow_review_stats(summary: dict[str, Any]) -> str:
    """Render a compact metrics line for prompt visibility."""
    total = int(summary.get("total", 0) or 0)
    counts = summary.get("counts", {})
    if total <= 0 or not isinstance(counts, dict):
        return ""
    local = int(counts.get("local", 0) or 0)
    subagent = int(counts.get("subagent", 0) or 0)
    external_llm = int(counts.get("external_llm", 0) or 0)
    return (
        "[cc-lazy-closure-debt stats] "
        f"last 24h: local={local}, subagent={subagent}, external_llm={external_llm}."
    )


def format_workflow_review(review: dict[str, Any]) -> str:
    """Render a compact review block for additionalContext."""
    recommendation = str(review.get("recommendation", "local"))
    summary = str(review.get("summary", "") or "")
    signals = review.get("signals", [])
    if isinstance(signals, list) and signals:
        signal_text = "; ".join(str(s) for s in signals if str(s).strip())
        if signal_text:
            return (
                f"[cc-lazy-closure-debt review] Suggested executor: {recommendation}. "
                f"{summary} Signals: {signal_text}."
            )
    return f"[cc-lazy-closure-debt review] Suggested executor: {recommendation}. {summary}"
