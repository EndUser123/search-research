#!/usr/bin/env python3
"""
Fake done detector for Stop hook.

Detects when the model claims completion ("Implementation complete.", "Done.")
without showing any evidence (code blocks, diffs, file paths, test results).

This is a Phase 2 hook — advisory on first occurrence, blocks on repeat.
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




# --- plugin bootstrap ---
import sys
from pathlib import Path

_lib = Path(__file__).resolve().parent.parent.parent / "__lib"
if str(_lib) not in sys.path:
    sys.path.insert(0, str(_lib))
from _bootstrap import bootstrap
_hooks_dir = bootstrap(__file__)
# --- end bootstrap ---

def _normalize_stdout(data: dict) -> dict:
    """Normalize hook output to Claude Code Zod-valid schema."""
    if data.get('decision') == 'allow':
        return {'decision': 'approve'}
    if data.get('decision') == 'block':
        return {'decision': 'block', 'reason': data.get('reason', '')}
    if 'allow' in data:
        if data['allow'] is False:
            return {'decision': 'block', 'reason': data.get('reason', '')}
        return {'decision': 'approve'}
    if 'continue' in data:
        if data['continue'] is False:
            return {'decision': 'block', 'reason': data.get('reason', '')}
        return {'decision': 'approve'}
    if 'ok' in data:
        return {'decision': 'approve'}
    return data






import os
import sys
from pathlib import Path

_Hook_Dir = Path(__file__).parent.resolve()
sys.path.insert(0, str(_Hook_Dir))

from hook_state_manager import (
    check_fake_done,
    check_violation_repeated,
    get_violation_count,
    increment_violation_count,
)

# ---------------------------------------------------------------------------
# Gate registration
# ---------------------------------------------------------------------------

GATE_NAME = "fake_done"

# Phrases that claim completion without evidence
_DONE_CLAIM_PHRASES = (
    "implementation complete",
    "done.",
    "fixed.",
    "complete.",
    "all files pass",
    "tests passed",
    "verified working",
    "code is ready",
    "the fix is complete",
)


def run_fake_done_detector(data: dict) -> dict | None:
    """
    Detect fake done claims without evidence.

    Returns None (pass) or a warning/block dict.
    """
    terminal_id = data.get("terminal_id") or os.environ.get("TERMINAL_ID", "")
    session_id = data.get("session_id") or ""

    if not terminal_id:
        return None

    output_text = data.get("output_text", "")
    if not output_text:
        return None

    # Check if output claims completion without evidence
    workspace = Path(data.get("cwd") or os.getcwd())
    if not check_fake_done(output_text, workspace=workspace):
        return None

    # Fake done detected — check repetition count
    count = get_violation_count(terminal_id, session_id, "fake_done")
    is_repeated, _ = check_violation_repeated(terminal_id, session_id, "fake_done")

    if is_repeated and count >= 1:
        return {
            "type": "block",
            "severity": "block",
            "gate": GATE_NAME,
            "error": (
                "FAKE DONE DETECTED\n\n"
                "You claimed completion without showing evidence.\n"
                "Show the actual changes: diffs, file paths, test results.\n"
                "Don't just claim it's done."
            ),
            "violations": ["fake_done"],
        }

    # First occurrence — warning
    return {
        "type": "warning",
        "severity": "warning",
        "gate": GATE_NAME,
        "error": (
            "COMPLETION CLAIM WITHOUT EVIDENCE\n\n"
            "You claimed completion without showing actual changes.\n"
            "Show: code diffs, file paths modified, or test results.\n"
            "Evidence is required for completion claims."
        ),
        "violations": ["fake_done"],
    }


def on_load() -> None:
    """Smoke test on import."""
    from hook_state_manager import check_fake_done
    assert callable(check_fake_done)


if __name__ == "__main__":
    import sys

    print("Running Stop_fake_done_detector.py self-test...", file=sys.stderr)

    from hook_state_manager import (
        clear_state, set_last_violations,
        get_violation_count, increment_violation_count
    )

    tid = "test_terminal_fake"
    sid = "test_session_fake"

    # Test 1: done-claim with a REAL file on disk → pass (grounded evidence).
    # A bare code-block diff no longer counts — the model can fabricate those.
    import tempfile
    from pathlib import Path
    with tempfile.TemporaryDirectory() as td:
        (Path(td) / "engine.py").write_text("x=1\n", encoding="utf-8")
        data = {
            "terminal_id": tid,
            "session_id": sid,
            "cwd": td,
            "output_text": "Implementation complete. Wrote engine.py",
            "all_violations": [],
        }
        result = run_fake_done_detector(data)
        assert result is None, f"Expected None with grounded evidence, got {result}"

        # Test 1b: done-claim referencing a MISSING file → fake (transcript case)
        clear_state(tid, "last_violations.json")
        clear_state(tid, "fake_done_count.json")
        data = {
            "terminal_id": tid,
            "session_id": sid,
            "cwd": td,
            "output_text": "Implementation complete. Wrote council_core/engine/council.py",
            "all_violations": [],
        }
        result = run_fake_done_detector(data)
        assert result is not None, "Expected warning on fabricated-evidence done claim"
        assert result["severity"] == "warning"

    # Test 2: Fake done without evidence → WARNING
    clear_state(tid, "last_violations.json")
    clear_state(tid, "fake_done_count.json")

    data = {
        "terminal_id": tid,
        "session_id": sid,
        "output_text": "Implementation complete.",
        "all_violations": [],
    }
    result = run_fake_done_detector(data)
    assert result is not None, "Expected warning on first fake done"
    assert result["severity"] == "warning"

    # Test 3: Repeated fake done → BLOCK
    increment_violation_count(tid, sid, "fake_done")  # count becomes 1
    set_last_violations(tid, sid, turn_number=2, violations=["fake_done"],
                        user_corrected=False, acknowledged=False)

    data = {
        "terminal_id": tid,
        "session_id": sid,
        "output_text": "Implementation complete. All files are updated.",
        "all_violations": [],
    }
    result = run_fake_done_detector(data)
    assert result is not None, "Expected block on repeated fake done"
    assert result["severity"] == "block"

    # Clean up
    clear_state(tid, "last_violations.json")
    clear_state(tid, "fake_done_count.json")

    print("All Stop_fake_done_detector.py self-tests passed.", file=sys.stderr)
