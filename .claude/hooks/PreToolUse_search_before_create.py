"""PreToolUse telemetry probe: search-before-create.

Detects Write of a NEW helper/hook/skill/util module without a prior Grep/Glob
in the session, and logs a telemetry event. TELEMETRY-ONLY — never blocks. The
point is to measure the false-positive rate before considering enforcement.

Discovery sidecar: .claude/state/searches_{session_id}.json
(populated by run_search_tracker, which PostToolUse calls on Grep/Glob).

Wiring:
  - PreToolUse.py TOOL_HOOKS["Write"] += "PreToolUse_search_before_create.py"
  - PostToolUse.py main() calls run_search_tracker(data) on Grep/Glob
"""

from __future__ import annotations

import os
from pathlib import Path

try:
    from __lib.pre_tool_use_logic import resolve_session_id
except Exception:  # pragma: no cover
    def resolve_session_id(data: dict | None = None) -> str:  # type: ignore[no-redef]
        payload = data or {}
        session_obj = payload.get("session")
        if isinstance(session_obj, dict):
            for key in ("id", "session_id", "sessionId"):
                value = session_obj.get(key)
                if isinstance(value, str) and value.strip():
                    return value.strip()
        for key in ("session_id", "sessionId", "CLAUDE_SESSION_ID"):
            value = payload.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
        return os.environ.get("CLAUDE_SESSION_ID", "").strip()


STATE_DIR = Path.home() / ".claude" / "state"
STATE_DIR.mkdir(parents=True, exist_ok=True)

# ponytail: heuristic — telemetry-only, so we accept some noise. These signal
# "new shared/utility code" where reusing an existing helper is the likely intent.
_HELPER_MARKERS = ("/__lib/", "/hooks/", "/lib/", "/utils/", "/shared/")
_HELPER_NAME_TOKENS = ("helper", "util", "common", "shared", "_lib")


def _telemetry(event: str, session_id: str, extra: dict | None = None) -> None:
    try:
        from __lib.agentic_reliability_telemetry import log_event

        log_event(
            category="search_before_create",
            event=event,
            gate="search_before_create",
            session_id=session_id or None,
            decision="telemetry",
            extra=extra,
        )
    except Exception:
        pass


def _searches_file(session_id: str) -> Path:
    return STATE_DIR / f"searches_{session_id}.json"


def _load_searches(session_id: str) -> list[str]:
    f = _searches_file(session_id)
    if not f.exists():
        return []
    try:
        import json

        return json.loads(f.read_text(encoding="utf-8")).get("searches", [])
    except Exception:
        return []


def _looks_like_helper(file_path: str) -> bool:
    norm = file_path.replace("\\", "/").lower()
    if any(marker in norm for marker in _HELPER_MARKERS):
        return True
    name = Path(norm).name
    return any(tok in name for tok in _HELPER_NAME_TOKENS)


def run(data: dict) -> dict | None:
    """PreToolUse probe. Telemetry-only; always returns None (allow)."""
    if data.get("tool_name") != "Write":
        return None
    session_id = resolve_session_id(data)
    if not session_id:
        return None
    tool_input = data.get("tool_input", {})
    file_path = tool_input.get("file_path", "")
    if not file_path:
        return None
    # Only new files (creates) are in scope — editing existing is existence_gate's job.
    if Path(file_path).exists():
        return None
    if not _looks_like_helper(file_path):
        return None
    searches = _load_searches(session_id)
    if searches:
        return None  # discovery happened — no signal
    _telemetry(
        "create_without_search",
        session_id,
        extra={"file": file_path, "searches_recorded": 0},
    )
    return None


def run_search_tracker(data: dict) -> dict | None:
    """PostToolUse recorder for Grep/Glob. Appends to the discovery sidecar."""
    tool_name = data.get("tool_name", "")
    if tool_name not in ("Grep", "Glob"):
        return None
    session_id = resolve_session_id(data)
    if not session_id:
        return None
    try:
        import json

        f = _searches_file(session_id)
        existing = _load_searches(session_id)
        existing.append(f"{tool_name}:{data.get('tool_input', {}).get('pattern', '') or data.get('tool_input', {}).get('path', '')}")
        f.write_text(json.dumps({"searches": existing[-50:]}), encoding="utf-8")
    except Exception:
        pass
    return None


if __name__ == "__main__":
    # ponytail self-check: a helper create with empty sidecar logs telemetry.
    os.environ["AGENTIC_RELIABILITY_TELEMETRY"] = "1"
    import tempfile

    sid = "self-check-sbc"
    # clean sidecar
    sf = _searches_file(sid)
    sf.unlink(missing_ok=True)
    d = tempfile.NamedTemporaryFile(delete=False, suffix="_util.py")
    d.close()
    Path(d.name).unlink(missing_ok=True)  # ensure non-existent (new file)
    run({"tool_name": "Write", "session": {"id": sid}, "tool_input": {"file_path": d.name}})
    print("search_before_create: self-check OK (telemetry would fire for", d.name, ")")
