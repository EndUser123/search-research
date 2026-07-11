"""cc-lazy-closure-debt Stop hook — records deferral phrases to JSONL debt store.

When the assistant's response contains an untracked deferral pattern
("I'll leave that for now", "we can address that later", etc.), this hook:

1. Detects the deferral via cc-aca-epistemic.lazy_closure_detector
2. Appends a JSONL line to the per-terminal debt store
3. Returns continue=true (does NOT block — the existing detector already
   provides the user-facing message in the response)

The companion /debt skill lists, clears, and (on user opt-in) formalizes
these items as tasks via TaskCreate.
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

# Make the cc-aca-epistemic plugin __lib__ importable so we can use the
# canonical deferral detector (no pattern duplication). Walk up from this
# hook file to find the marketplace root (it lives at
# <marketplace>/plugins/cc-aca-epistemic/__lib/).
def _find_epistemic_lib() -> Path | None:
    here = Path(__file__).resolve()
    for parent in here.parents:
        candidate = parent / "cc-aca-epistemic" / "__lib"
        if candidate.is_dir():
            return candidate
    return None

_EPIS_LIB = _find_epistemic_lib()
if _EPIS_LIB is not None and str(_EPIS_LIB) not in sys.path:
    sys.path.insert(0, str(_EPIS_LIB))

try:
    from anti_sycophancy.lazy_closure_detector import detect_lazy_closure
except Exception as _exc:  # pragma: no cover - import-failure path
    detect_lazy_closure = None
    _IMPORT_ERR = repr(_exc)
else:
    _IMPORT_ERR = None

# Local helper module for the debt store
from debt_store import append_deferral  # noqa: E402


def _resolve_session_id(data: dict) -> str:
    """Resolve session_id from Stop hook data."""
    session_obj = data.get("session") or {}
    if isinstance(session_obj, dict):
        sid = session_obj.get("session_id") or session_obj.get("sessionId")
        if sid:
            return str(sid)
    sid = data.get("session_id") or data.get("sessionId")
    if sid:
        return str(sid)
    return os.environ.get("CLAUDE_SESSION_ID", "")


def _safe_id(value: str | None) -> str:
    if not value:
        return "unknown"
    return re.sub(r"[^a-zA-Z0-9_.-]+", "_", value)


def _resolve_terminal_id(data: dict) -> str:
    """Resolve terminal_id from Stop hook data, with env-var fallback."""
    session_obj = data.get("session") or {}
    if isinstance(session_obj, dict):
        tid = session_obj.get("terminal_id") or session_obj.get("terminalId")
        if tid:
            return str(tid)
    tid = data.get("terminal_id") or data.get("terminalId")
    if tid:
        return str(tid)
    return os.environ.get("CLAUDE_TERMINAL_ID", "default")


def _extract_response_text(data: dict) -> str:
    """Best-effort extraction of the assistant response text."""
    # The Stop hook payload varies by version; try common keys first.
    for key in ("response", "transcript_excerpt", "last_assistant_message"):
        val = data.get(key)
        if isinstance(val, str) and val.strip():
            return val
    # Fall back to transcript_path if present (do a tail read)
    tp = data.get("transcript_path")
    if tp and Path(tp).exists():
        try:
            with open(tp, "r", encoding="utf-8") as f:
                # Read last ~16KB; cheap and avoids loading huge files
                f.seek(0, 2)
                size = f.tell()
                f.seek(max(0, size - 16384))
                tail = f.read()
            # Pull the last assistant message text
            last_text = None
            for line in tail.splitlines():
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if obj.get("role") == "assistant":
                    content = obj.get("content")
                    if isinstance(content, list):
                        for part in content:
                            if isinstance(part, dict) and part.get("type") == "text":
                                last_text = part.get("text", "")
                    elif isinstance(content, str):
                        last_text = content
            if last_text:
                return last_text
        except OSError:
            pass
    return ""


def run(data: dict) -> dict:
    """Main entry point.

    Returns a Continue-true dict; never blocks. Appends to the debt store
    when a deferral pattern is detected in the response.
    """
    if detect_lazy_closure is None:
        # Detector unavailable — fail open and log to stderr
        print(
            f"[cc-lazy-closure-debt] detector import failed: {_IMPORT_ERR}",
            file=sys.stderr,
        )
        return {"continue": True}

    response = _extract_response_text(data)
    if not response:
        return {"continue": True}

    match = detect_lazy_closure(response)
    if match is None or match.pattern_type != "deferral":
        return {"continue": True}

    terminal_id = _safe_id(_resolve_terminal_id(data))
    session_id = _resolve_session_id(data)
    excerpt = response[:200]

    try:
        append_deferral(
            terminal_id=terminal_id,
            session_id=session_id,
            phrase=match.matched,
            transcript_excerpt=excerpt,
        )
    except OSError as exc:
        print(
            f"[cc-lazy-closure-debt] append failed: {exc}",
            file=sys.stderr,
        )

    return {"continue": True}


if __name__ == "__main__":
    raw = sys.stdin.read()
    try:
        data = json.loads(raw) if raw.strip() else {}
    except json.JSONDecodeError:
        data = {}
    result = run(data)
    print(json.dumps(result))
    sys.exit(0)
