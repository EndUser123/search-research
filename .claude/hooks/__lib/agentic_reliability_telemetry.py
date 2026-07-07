"""Agentic-reliability telemetry — lightweight structured logging.

Observability for deterministic reliability gates (read-before-edit,
search-before-create, structural-claim evidence, validation-claim evidence).
These gates run telemetry-only by default; this sink is how we measure their
signal before promoting any of them to blocking.

Design imitates stop_gate_telemetry.py but is gate-agnostic: any gate calls
log_event(category, event, ...). Failures are silent — logging never disrupts
the hook. State lives outside the code tree (see memory: plugin_state_log_contract).

Log format (one JSON object per line):
    {"ts","category","event","gate","session_id","terminal_id","decision","extra"}

Enable: AGENTIC_RELIABILITY_TELEMETRY=1 (default off, like STOP_TELEMETRY).

Category vocabulary (CATEGORIES is the canonical set — producers should pass one
of these; the sink itself is untyped, the constant is for discoverability/tests):
    read_before_edit        — existence_gate: did the model read before editing?
    search_before_create    — search_before_create: did it search before creating?
    dispatch_decision       — a router/dispatcher chose a target. event in
                              {routed, delegated, blocked_dispatch, fallback};
                              extra: {source, target, worker_scope?}.
                              Producers: go_delegation_enforce_PreToolUse,
                              skill_pattern_gate (enforcement tier), model_router.
    complexity_model_source — complexity tier + which model handled it. event in
                              {classified, model_selected, tier_overridden};
                              extra: {tier, complexity_score?, model, model_source}.
                              Producers: classify_complexity, pi/local dispatch.
    self_check              — module self-roundtrip (see __main__).
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_ENABLED = os.environ.get("AGENTIC_RELIABILITY_TELEMETRY", "0") not in {
    "0",
    "false",
    "no",
    "off",
}

# Canonical category vocabulary. The sink is untyped (category is a free-form
# str at the log_event boundary); this constant exists for discoverability and
# so the self-check can assert every declared category round-trips.
CATEGORIES = frozenset({
    "read_before_edit",
    "search_before_create",
    "dispatch_decision",
    "complexity_model_source",
    "self_check",
})


def _resolve_state_dir() -> Path:
    try:
        from state_paths import SHARED_DIR  # type: ignore[import-not-found]

        return SHARED_DIR
    except Exception:
        return Path(__file__).resolve().parent.parent / ".state"


_STATE_DIR = _resolve_state_dir()
_LOG_FILE = _STATE_DIR / "agentic_reliability_telemetry.jsonl"

_ROTATION_MAX_BYTES = 50 * 1024
_ROTATION_MAX_FILES = 3


def _maybe_rotate() -> None:
    """Rotate the log file if it exceeds the size threshold. Fail-open."""
    try:
        if not _LOG_FILE.exists() or _LOG_FILE.stat().st_size < _ROTATION_MAX_BYTES:
            return
        _LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        oldest = _LOG_FILE.parent / f"{_LOG_FILE.name}.{_ROTATION_MAX_FILES}"
        if oldest.exists():
            oldest.unlink(missing_ok=True)
        for i in range(_ROTATION_MAX_FILES - 1, 0, -1):
            prev = _LOG_FILE.parent / f"{_LOG_FILE.name}.{i}"
            nxt = _LOG_FILE.parent / f"{_LOG_FILE.name}.{i + 1}"
            if prev.exists():
                prev.replace(nxt)
        dest = _LOG_FILE.parent / f"{_LOG_FILE.name}.1"
        if not dest.exists():
            _LOG_FILE.replace(dest)
        _LOG_FILE.touch()
    except Exception:
        pass


def log_event(
    category: str,
    event: str,
    gate: str | None = None,
    session_id: str | None = None,
    terminal_id: str | None = None,
    decision: str | None = None,
    extra: dict[str, Any] | None = None,
) -> None:
    """Log one reliability event. Never raises.

    Args:
        category: gate family (e.g. "read_before_edit", "search_before_create").
        event: what happened (e.g. "missing_read", "allow", "sidecar_write").
        gate: specific gate name (e.g. "existence_gate").
        decision: "block" | "allow" | "telemetry" — what the gate did.
    """
    if not _ENABLED:
        return
    record: dict[str, Any] = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "category": category,
        "event": event,
    }
    if gate:
        record["gate"] = gate
    if session_id:
        record["session_id"] = session_id
    if terminal_id:
        record["terminal_id"] = terminal_id
    if decision:
        record["decision"] = decision
    if extra:
        record["extra"] = extra
    try:
        _STATE_DIR.mkdir(parents=True, exist_ok=True)
        _maybe_rotate()
        from file_lock import append_jsonl_safe
        append_jsonl_safe(_LOG_FILE, record)
    except OSError:
        pass


def is_enabled() -> bool:
    return _ENABLED


def read_events() -> list[dict[str, Any]]:
    """Read all events (base + rotated). Test helper."""
    files = [_LOG_FILE] + [_LOG_FILE.parent / f"{_LOG_FILE.name}.{i}" for i in range(1, _ROTATION_MAX_FILES)]
    records: list[dict[str, Any]] = []
    for path in files:
        if not path.exists():
            continue
        try:
            for line in path.read_text(encoding="utf-8").splitlines():
                if line.strip():
                    records.append(json.loads(line))
        except Exception:
            pass
    return records


def clear_test_log() -> None:
    """Remove the log + rotated files. Test helper."""
    try:
        _LOG_FILE.unlink(missing_ok=True)
        for i in range(1, _ROTATION_MAX_FILES):
            (_LOG_FILE.parent / f"{_LOG_FILE.name}.{i}").unlink(missing_ok=True)
    except Exception:
        pass


if __name__ == "__main__":
    # ponytail self-check: round-trip one record per declared category when
    # enabled. Proves every entry in CATEGORIES is writable+readable, so adding
    # a category without wiring it still fails loudly here.
    os.environ["AGENTIC_RELIABILITY_TELEMETRY"] = "1"
    globals()["_ENABLED"] = True
    before = len(read_events())
    for cat in CATEGORIES:
        log_event(cat, "self_roundtrip", gate="self", session_id="self")
    after = len(read_events())
    added = after - before
    assert added == len(CATEGORIES), (
        f"round-trip failed: expected {len(CATEGORIES)} records, wrote {added}")
    print(f"agentic_reliability_telemetry: round-trip OK ({added}/{len(CATEGORIES)} categories)")
