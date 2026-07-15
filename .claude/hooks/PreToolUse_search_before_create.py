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

import json
import os
import sys
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
# NOTE: the __lib__ marker uses double underscores to match the Python
# name-mangling convention used by `__pycache__`, `__init__.py`, etc.
_HELPER_MARKERS = ("/__lib__/", "/hooks/", "/lib/", "/utils/", "/shared/")
_HELPER_NAME_TOKENS = ("helper", "util", "common", "shared", "_lib")

# High-risk extension points. Creating a new one of these without prior search
# soft-blocks the edit. Promoted from telemetry-only 2026-07-02 in Phase 2
# of the /go reliability ladder.
# Lowercase — _is_high_risk_extension_point lowercases the path before matching.
_HIGH_RISK_PATH_FRAGMENTS = (
    "/pretooluse_", "/posttooluse_", "/stop_", "/sessionstart_",
    "/sessionend_", "/userpromptsubmit_", "/subagentstop_",
    "/skill.md", "/__lib__", "/__lib__/",
    "/plugin-audit", "/cache-mutation",
)


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


def _is_high_risk_extension_point(file_path: str) -> bool:
    # Normalize to lowercase so filesystem case-sensitivity doesn't defeat the
    # marker match. The markers themselves are already lowercase.
    norm = file_path.replace("\\", "/").lower()
    return any(frag in norm for frag in _HIGH_RISK_PATH_FRAGMENTS)


def run(data: dict) -> dict | None:
    """PreToolUse probe. Promoted from telemetry-only 2026-07-02:
    - High-risk extension points (PreToolUse_*, PostToolUse_*, Stop_*, etc.):
      soft-block with explicit bypass.
    - Normal helper/utility paths: warn with the existing message.
    - Trivial paths (no helper marker, no high-risk): allow.
    Bypass: --allow-no-search in the user message.
    """
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
    high_risk = _is_high_risk_extension_point(file_path)
    looks_like_helper = _looks_like_helper(file_path)
    if not (high_risk or looks_like_helper):
        return None
    searches = _load_searches(session_id)
    if searches:
        return None  # discovery happened — no signal
    # Bypass: explicit user opt-out.
    message = data.get("message", "")
    if "--allow-no-search" in message:
        _telemetry(
            "create_without_search_bypass",
            session_id,
            extra={"file": file_path, "high_risk": high_risk},
        )
        return None
    # Emit telemetry in all cases.
    _telemetry(
        "create_without_search",
        session_id,
        extra={"file": file_path, "high_risk": high_risk, "searches_recorded": 0},
    )
    if high_risk:
        return {
            "decision": "block",
            "reason": (
                f"New high-risk extension point {file_path} created without prior Grep/Glob. "
                "Search for existing equivalents first, or add --allow-no-search to bypass."
            ),
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "permissionDecisionReason": (
                    f"Search-before-create: {file_path} is a high-risk extension point. "
                    "Run a Grep/Glob to find existing equivalents first, "
                    "or add --allow-no-search to bypass."
                ),
            },
        }
    # Normal helper/utility path: warn, not block.
    return {
        "decision": "warn",
        "systemMessage": (
            f"Search-before-create: new helper/utility file {file_path} was created without "
            "a prior Grep/Glob in this session. Consider searching for existing equivalents first; "
            "add --allow-no-search to bypass."
        ),
    }


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


def main() -> int:
    """Run the hook through the JSON stdin/stdout PreToolUse contract."""
    raw = sys.stdin.read()
    if not raw.strip():
        return 0
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        print(json.dumps({"decision": "block", "reason": f"Invalid hook input: {exc}"}))
        return 2
    result = run(data if isinstance(data, dict) else {})
    print(json.dumps(result or {}))
    return 2 if result and result.get("decision") == "block" else 0


if __name__ == "__main__":
    raise SystemExit(main())
