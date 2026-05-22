"""
Stop gate-level telemetry — lightweight structured logging.

EXPERIMENTAL: Provides visibility into which gates fire with what decisions.
wired: false (off by default)
review: TBD

Usage:
    STOP_TELEMETRY=1  # Enable telemetry to .state/stop_gate_telemetry.jsonl

Log format (one JSON object per line):
    {
        "ts": "<ISO8601>",
        "gate": "<gate_name>",
        "class": "policy|quality",
        "profile": "<critic_profile or context>",
        "decision": "block|warn|allow",
        "session_id": "...",
        "terminal_id": "...",
        "skip_reason": "...",        # Phase 2: why gate was skipped
        "turn_kind": "...",          # Phase 2: classified turn kind
        "claim_kind": "...",        # Phase 2: detected claim kind
        "artifact_classes": [...],  # Phase 2: detected artifact classes
        "artifact_class_required": "...",  # Phase 3: artifact class required by gate
        "artifact_class_observed": "...",  # Phase 3: artifact class actually observed
        "rollout_mode": "...",      # Phase 2: active rollout mode (block/advisory/shadow/disabled)
        "visible": true,             # Phase 2: whether gate output was visible to user
    }

Failures are silent — logging errors never propagate.
"""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_TELEMETRY_ENABLED = os.environ.get("STOP_TELEMETRY", "0") not in {"0", "false", "no", "off"}
_STATE_DIR = Path(__file__).resolve().parent.parent / ".state"
_LOG_FILE = _STATE_DIR / "stop_gate_telemetry.jsonl"

# Rotation defaults
_ROTATION_MAX_BYTES = 50 * 1024  # 50 KB
_ROTATION_MAX_FILES = 3  # keep .1, .2, .3


def log_gate_event(
    gate_name: str,
    classification: str,
    profile: str | None,
    decision: str,
    session_id: str | None = None,
    terminal_id: str | None = None,
    extra: dict[str, Any] | None = None,
    # Phase 2 fields
    skip_reason: str | None = None,
    turn_kind: str | None = None,
    claim_kind: str | None = None,
    artifact_classes: list[str] | None = None,
    rollout_mode: str | None = None,
    visible: bool | None = None,
    # Phase 3: runtime claim artifact enrichment
    artifact_class_required: str | None = None,
    artifact_class_observed: str | None = None,
) -> None:
    """Log a single gate invocation. Never raises."""
    if not _TELEMETRY_ENABLED:
        return

    record: dict[str, Any] = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "gate": gate_name,
        "class": classification,
        "profile": profile,
        "decision": decision,
    }
    if session_id:
        record["session_id"] = session_id
    if terminal_id:
        record["terminal_id"] = terminal_id
    # Phase 2 enriched fields
    if skip_reason:
        record["skip_reason"] = skip_reason
    if turn_kind:
        record["turn_kind"] = turn_kind
    if claim_kind:
        record["claim_kind"] = claim_kind
    if artifact_classes:
        record["artifact_classes"] = artifact_classes
    if rollout_mode:
        record["rollout_mode"] = rollout_mode
    if visible is not None:
        record["visible"] = visible
    # Phase 3 runtime claim artifact enrichment
    if artifact_class_required:
        record["artifact_class_required"] = artifact_class_required
    if artifact_class_observed:
        record["artifact_class_observed"] = artifact_class_observed
    if extra:
        record["extra"] = extra

    try:
        _STATE_DIR.mkdir(parents=True, exist_ok=True)
        maybe_rotate_telemetry_file()  # rotate if over threshold before writing
        with open(_LOG_FILE, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(record, separators=(",", ":")) + "\n")
    except Exception:
        pass  # Fail silent — telemetry errors must not disrupt Stop


def clear_test_telemetry() -> None:
    """Remove telemetry log. For use in tests only."""
    try:
        if _LOG_FILE.exists():
            _LOG_FILE.unlink()
    except Exception:
        pass


def read_telemetry() -> list[dict[str, Any]]:
    """Read all telemetry records. For use in tests only."""
    try:
        if not _LOG_FILE.exists():
            return []
        return [json.loads(line) for line in _LOG_FILE.read_text(encoding="utf-8").splitlines() if line.strip()]
    except Exception:
        return []


# ---------------------------------------------------------------------------
# Phase 5: Health summary helpers
# ---------------------------------------------------------------------------


def _is_recent(record: dict[str, Any], hours: int) -> bool:
    """Return True if record is within the last `hours` hours."""
    try:
        ts = datetime.fromisoformat(record.get("ts", ""))
        delta = datetime.now(timezone.utc) - ts.replace(tzinfo=timezone.utc)
        return delta.total_seconds() <= hours * 3600
    except Exception:
        return False


def get_recent_gate_summary(
    records: list[dict[str, Any]] | None = None,
    hours: int = 24,
    top_n: int = 5,
) -> dict[str, int]:
    """Return top non-allow gate decisions in the recent window.

    Args:
        records: telemetry records (reads from file if None)
        hours: time window in hours (default 24)
        top_n: maximum gates to return (default 5)

    Returns:
        dict of gate_name → count, sorted descending, for block/warn only.
        Empty dict when no non-allow events.
    """
    if records is None:
        records = read_telemetry()
    recent = [r for r in records if _is_recent(r, hours)]
    non_allow = [r for r in recent if r.get("decision") in ("block", "warn")]
    counts: dict[str, int] = {}
    for r in non_allow:
        gate = r.get("gate", "?")
        counts[gate] = counts.get(gate, 0) + 1
    return dict(sorted(counts.items(), key=lambda x: -x[1])[:top_n])


def get_runtime_claim_summary(
    records: list[dict[str, Any]] | None = None,
    hours: int = 24,
) -> dict[str, int]:
    """Return runtime claim enforcement outcome counts.

    Looks for records from gates that have `artifact_class_required` and
    counts outcomes by `artifact_class_observed`.

    Returns:
        dict with keys: matched, artifact_missing, no_match, other.
    """
    if records is None:
        records = read_telemetry()
    recent = [r for r in records if _is_recent(r, hours)]
    runtime = [r for r in recent if r.get("artifact_class_required")]
    counts = {"matched": 0, "artifact_missing": 0, "no_match": 0, "other": 0}
    for r in runtime:
        observed = r.get("artifact_class_observed") or "none"
        if observed == "none" or not observed:
            counts["no_match"] += 1
        elif observed == "artifact_missing":
            counts["artifact_missing"] += 1
        elif observed == observed:  # has a value
            counts["matched"] += 1
        else:
            counts["other"] += 1
    return counts


def get_rollout_summary(
    records: list[dict[str, Any]] | None = None,
    hours: int = 24,
) -> dict[str, int]:
    """Return non-default rollout mode counts.

    Default rollout is "block". Any gate with a different rollout_mode
    indicates a non-default override.

    Returns:
        dict of rollout_mode → count, excluding "block".
    """
    if records is None:
        records = read_telemetry()
    recent = [r for r in records if _is_recent(r, hours)]
    counts: dict[str, int] = {}
    for r in recent:
        mode = r.get("rollout_mode")
        if mode and mode != "block":
            counts[mode] = counts.get(mode, 0) + 1
    return counts


def render_mode_status(session_mode: str) -> str:
    """Render a compact one-line mode status with behavioral note if non-NORMAL."""
    if session_mode == "debug_gates":
        return "Session Mode: DEBUG_GATES  (quality gates suppressed)"
    if session_mode == "audit":
        return "Session Mode: AUDIT  (format-only friction softened on audit-report turns)"
    return "Session Mode: NORMAL"


def render_attention_lines(
    gate_summary: dict[str, int],
    claim_summary: dict[str, int],
    rollout_summary: dict[str, int],
    session_mode: str,
) -> list[str]:
    """Build compact attention lines from summary data.

    Returns a list of short, actionable one-liners.
    Empty list when nothing actionable is present.
    """
    lines: list[str] = []

    if session_mode == "debug_gates":
        lines.append("Mode is DEBUG_GATES — quality gates suppressed for gate-debug conversation")

    total_runtime = sum(claim_summary.values())
    if total_runtime >= 3:
        pct_missing = claim_summary.get("artifact_missing", 0) / total_runtime
        if pct_missing >= 0.5:
            lines.append(
                f"Runtime claim enforcement: {claim_summary['artifact_missing']}/{total_runtime} "
                f"failed — artifact_missing dominates ({int(pct_missing*100)}%)"
            )

    if rollout_summary:
        top_rollout = max(rollout_summary, key=lambda k: rollout_summary[k])
        lines.append(
            f"Rollout override active: {top_rollout} on "
            f"{rollout_summary[top_rollout]} event(s)"
        )

    return lines


def render_compact_health(
    session_mode: str,
    gate_summary: dict[str, int],
    claim_summary: dict[str, int],
    rollout_summary: dict[str, int],
    hours: int = 24,
) -> str:
    """Render a full compact health snapshot as a multi-line string.

    Output is intentionally terse — fits in ~10 lines.
    """
    lines: list[str] = []
    lines.append(f"━━ Gate Health (last {hours}h) ━━")
    lines.append(render_mode_status(session_mode))

    total_gates = sum(gate_summary.values())
    if total_gates == 0:
        lines.append("  No non-allow gate events")
    else:
        for gate, count in sorted(gate_summary.items(), key=lambda x: -x[1]):
            lines.append(f"  {gate}: {count}")
        lines.append(f"  total: {total_gates}")

    attention = render_attention_lines(gate_summary, claim_summary, rollout_summary, session_mode)
    for line in attention:
        lines.append(f"  ⚑ {line}")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Rotation helpers
# ---------------------------------------------------------------------------

def _iter_telemetry_files(
    base: Path | None = None,
    max_files: int = _ROTATION_MAX_FILES,
) -> list[Path]:
    """Yield base file + up to max_files-1 rotated files, newest first.

    Files are expected at: stop_gate_telemetry.jsonl,
    stop_gate_telemetry.jsonl.1, .2, ... .N.
    Only returns existing files. Empty list if nothing exists.
    """
    if base is None:
        base = _LOG_FILE

    candidates: list[Path] = [base]
    for i in range(1, max_files):
        candidates.append(Path(str(base) + f".{i}"))

    return [f for f in candidates if f.exists()]


def maybe_rotate_telemetry_file(
    base: Path | None = None,
    max_bytes: int = _ROTATION_MAX_BYTES,
    max_files: int = _ROTATION_MAX_FILES,
) -> None:
    """Rotate telemetry file if it exceeds max_bytes.

    Rotation is safe: renames current → .1, shifts .N → .N+1, prunes oldest
    beyond max_files, then re-creates the base file empty. Fails open — any
    exception is swallowed so rotation errors never disrupt Stop hooks.
    """
    if base is None:
        base = _LOG_FILE

    try:
        if not base.exists():
            return

        if base.stat().st_size < max_bytes:
            return

        # Ensure parent dir exists
        base.parent.mkdir(parents=True, exist_ok=True)

        # Step 1: delete oldest beyond max_files
        oldest = base.parent / f"{base.name}.{max_files}"
        if oldest.exists():
            try:
                oldest.unlink()
            except Exception:
                pass

        # Step 2: shift .N → .N+1 for N = max_files-1 down to 1
        for i in range(max_files - 1, 0, -1):
            prev = base.parent / f"{base.name}.{i}"
            nxt = base.parent / f"{base.name}.{i + 1}"
            if prev.exists():
                try:
                    prev.replace(nxt)  # atomic overwrite on Windows
                except Exception:
                    pass

        # Step 3: rename base → .1
        dest = base.parent / f"{base.name}.1"
        if not dest.exists():
            try:
                base.replace(dest)  # atomic overwrite on Windows
            except Exception:
                pass

        # Step 4: re-create base empty
        base.touch()

    except Exception:
        pass  # Fail open — rotation errors must not block telemetry writes


def _read_telemetry_multi(
    base: Path | None = None,
    max_files: int = _ROTATION_MAX_FILES,
) -> list[dict[str, Any]]:
    """Read telemetry from base file + rotated files, newest-first order.

    Returns all records from all files, in chronological order.
    Missing or unparseable files are skipped silently.
    """
    if base is None:
        base = _LOG_FILE

    files = _iter_telemetry_files(base, max_files)
    if not files:
        return []

    records: list[dict[str, Any]] = []
    for path in files:
        try:
            records.extend(
                json.loads(line)
                for line in path.read_text(encoding="utf-8").splitlines()
                if line.strip()
            )
        except Exception:
            pass

    return records


# ---------------------------------------------------------------------------
# Override read_telemetry to use multi-file reader (for callers that pass None)
# ---------------------------------------------------------------------------

def read_telemetry() -> list[dict[str, Any]]:
    """Read all telemetry records from base + rotated files."""
    return _read_telemetry_multi()