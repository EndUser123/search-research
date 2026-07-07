#!/usr/bin/env python3
"""UserPromptSubmit hook: consume a classify recommendation and record it.

CCR is the sole routing authority.  The apply hook exists only to:
  - mark the recommendation as consumed (prevent double-fire)
  - append an audit row for offline analysis / telemetry

States:
  - no recommendation.json   -> no-op
  - recommendation expired   -> no-op
  - recommendation consumed  -> no-op
  - recommended == current   -> no-op
  - else                    -> consume + audit

Exit codes:
  0  always. We must NOT block the user prompt.
"""

import json
import os
import pathlib
import sys
from datetime import datetime, timezone

PLUGIN_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
if str(PLUGIN_ROOT / "__lib") not in sys.path:
    sys.path.insert(0, str(PLUGIN_ROOT / "__lib"))

from settings_writer import atomic_write_json  # type: ignore[import-not-found]  # noqa: E402

TTL_SECONDS = 300


def get_state_path(terminal_id: str, session_id: str) -> pathlib.Path:
    return (
        pathlib.Path(os.environ.get("CSF_STATE_DIR") or str(pathlib.Path("P:/") / ".claude" / "state"))
        / "model-router"
        / terminal_id
        / session_id
    )


def load_recommendation(state_path: pathlib.Path) -> dict | None:
    p = state_path / "recommendation.json"
    if not p.exists():
        return None
    try:
        with open(p, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def is_expired(rec: dict, ttl: int = TTL_SECONDS) -> bool:
    written = rec.get("written_at", "")
    if not written:
        return True
    try:
        written_dt = datetime.fromisoformat(written)
        # Mixed-tz safety: if the stored timestamp is naive (legacy rows written by
        # older classify hooks as local time), compare against naive local now —
        # the original same-machine behavior. If it's tz-aware (new UTC writes),
        # compare against aware UTC now. Never reinterpret naive as UTC: on a
        # non-UTC host that makes fresh rows look hours old and falsely expires them.
        if written_dt.tzinfo is None:
            now = datetime.now()
        else:
            now = datetime.now(timezone.utc)
        age = (now - written_dt).total_seconds()
    except Exception:
        return True
    return age > ttl


def mark_consumed(state_path: pathlib.Path) -> None:
    p = state_path / "recommendation.json"
    if not p.exists():
        return
    try:
        with open(p, encoding="utf-8") as f:
            data = json.load(f)
        data["consumed"] = True
        data["consumed_at"] = datetime.now(timezone.utc).isoformat()
        # Atomic write closes the read-modify-write race: two concurrent apply
        # calls can no longer both read consumed=False and double-apply.
        atomic_write_json(p, data)
    except Exception:
        pass


def append_audit(state_path: pathlib.Path, row: dict) -> None:
    audit = state_path.parent.parent / "apply_audit.jsonl"
    try:
        audit.parent.mkdir(parents=True, exist_ok=True)
        with open(audit, "a", encoding="utf-8") as f:
            f.write(json.dumps(row) + "\n")
    except Exception:
        pass


def main() -> None:
    try:
        data = json.load(sys.stdin)
    except Exception:
        sys.exit(0)

    terminal_id = data.get("terminal_id", "default")
    session_id = data.get("session_id", "default")
    state_path = get_state_path(terminal_id, session_id)

    rec = load_recommendation(state_path)
    if not rec:
        sys.exit(0)

    if is_expired(rec):
        sys.exit(0)

    if rec.get("consumed"):
        sys.exit(0)

    recommended = rec.get("recommended_model", "")
    current = rec.get("current_model", "")
    if not recommended or recommended == current:
        sys.exit(0)

    base_recommended = recommended.split("[")[0]
    base_current = current.split("[")[0]
    if base_recommended == base_current:
        sys.exit(0)

    ts = datetime.now().isoformat()

    mark_consumed(state_path)

    append_audit(
        state_path,
        {
            "ts": ts,
            "action_taken": "logging-only",
            "current_model": current,
            "new_model": recommended,
            "terminal_id": terminal_id,
            "session_id": session_id,
        },
    )

    print(
        f"[model-router-apply] model={current} -> {recommended} "
        f"(log-only, no settings.json write)",
        file=sys.stderr,
    )
    sys.exit(0)


if __name__ == "__main__":
    main()
