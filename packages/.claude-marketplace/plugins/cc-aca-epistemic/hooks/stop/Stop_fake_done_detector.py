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
    _extract_claimed_paths,
)

# CHANGE-007 read-side: optional dependency on the investigation-ledger.
# Fail-OPEN: if the ledger module is unavailable, Tier 1.5 is skipped entirely
# rather than warning on every verification claim. _hooks_dir is the global
# hooks dir (P:/.claude/hooks/) resolved by the plugin bootstrap.
_LEDGER_AVAILABLE = False
try:
    _IL_DIR = _hooks_dir / "investigation-ledger"
    if str(_IL_DIR) not in sys.path:
        sys.path.insert(0, str(_IL_DIR))
    from ledger import is_verified as _is_verified  # type: ignore[import-not-found]
    _LEDGER_AVAILABLE = True
except Exception:
    _is_verified = None  # type: ignore[assignment]

# Verification-specific claims (subset of _DONE_CLAIM_PHRASES). Generic
# "done"/"fixed" is NOT here — editing is not testing. This tier fires only
# when the model asserts verification that the ledger cannot corroborate.
_VERIFICATION_CLAIM_PHRASES = (
    "tests passed",
    "verified working",
    "all files pass",
    "test suite passes",
    "tests pass",
)


def _has_verification_claim(output_text: str) -> bool:
    lower = output_text.lower()
    return any(phrase in lower for phrase in _VERIFICATION_CLAIM_PHRASES)


def _exists(path_str: str, base: Path) -> bool:
    return Path(path_str).exists() or (base / path_str).exists()


def _resolve(path_str: str, base: Path) -> Path:
    """Absolute path for a claimed token: prefer base-relative when relative."""
    p = Path(path_str)
    if p.is_absolute():
        return p
    rel = base / p
    return rel if rel.exists() else p

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

# Ungrounded superlatives — strong un-hedged claims not backed by present evidence even
# when files exist. OQ-1 WARN tier: satisfied grounding + superlative -> warn (the claim
# overshoots what the evidence supports).
import re as _re
_SUPERLATIVE_RE = _re.compile(
    r"\b(?:flawless(?:ly)?|perfect(?:ly|ion)?|bulletproof|airtight|comprehensively|"
    r"production-ready|rock\s*solid|guaranteed|zero[- ]?defect|fully\s+fixed|"
    r"completely\s+fixed|100%|ironclad)\b",
    _re.IGNORECASE,
)


def _has_done_claim(output_text: str) -> bool:
    lower = output_text.lower()
    return any(phrase in lower for phrase in _DONE_CLAIM_PHRASES)


def run_fake_done_detector(data: dict) -> dict | None:
    """Detect fake done claims without evidence — block-first, narrow trigger (OQ-1).

    Posture (director decision 2026-06-27):
      - BLOCK on the first fabricated evidence-existence claim (a referenced file that
        does not exist, or a done-claim with no file referenced at all). Replaces the
        former advisory-first/block-on-repeat: a disposable coder that hallucinates a
        completion once never reaches a repeat counter.
      - WARN on ungrounded superlatives WITH satisfied file grounding (files exist, but
        the strong claim isn't backed by evidence).
      - PASS on satisfied grounding without a superlative issue.

    Returns None (pass) or a warning/block dict.
    """
    terminal_id = data.get("terminal_id") or os.environ.get("TERMINAL_ID", "")

    if not terminal_id:
        return None

    output_text = data.get("output_text", "")
    if not output_text:
        return None

    workspace = Path(data.get("cwd") or os.getcwd())

    # Tier 1 — fabricated evidence-existence / no-evidence claim: BLOCK (first occurrence).
    if check_fake_done(output_text, workspace=workspace):
        return {
            "type": "block",
            "severity": "block",
            "gate": GATE_NAME,
            "error": (
                "FAKE DONE — completion claimed without verifiable evidence.\n\n"
                "You asserted a done/fix/verification, but the referenced file does "
                "not exist (or no file was referenced). Show the actual change: a real "
                "file path you wrote, a diff, or test output.\n"
                "Block-first (OQ-1): a single fabricated completion claim blocks."
            ),
            "violations": ["fake_done"],
        }

    # Tier 1.5 — claimed verification the ledger cannot corroborate (CHANGE-007
    # read-side). Fires ONLY on verification claims ("tests passed", "verified
    # working"), not generic done/fixed, and only when a claimed file EXISTS
    # but is_verified() is False (no fresh verification record vs current
    # content). WARN ceiling: the write-side captures most runners but misses
    # bare scripts / already-committed code, so a False here can be a capture
    # gap. The CHANGE-003(b) tool-event rescue that would discriminate true
    # fake-done from capture gaps is deferred — see plan CHANGE-007.
    if _LEDGER_AVAILABLE and _is_verified is not None and _has_verification_claim(output_text):
        claimed = _extract_claimed_paths(output_text)
        existing = [p for p in claimed if _exists(p, workspace)]
        if existing:
            unverified = [p for p in existing if not _is_verified(str(_resolve(p, workspace)), mode="strict")]
            if unverified:
                shown = unverified[0] if len(unverified) == 1 else f"{len(unverified)} files"
                return {
                    "type": "warning",
                    "severity": "warning",
                    "gate": GATE_NAME,
                    "error": (
                        "UNVERIFIED COMPLETION — you claim tests/verification "
                        f"passed, but the ledger has no fresh verification record "
                        f"for {shown} against its current content. If you ran a "
                        "verifying command, name it; otherwise run it (pytest/"
                        "python -m pytest/etc.) so the record is captured."
                    ),
                    "violations": ["unverified_completion"],
                }

    # Tier 2 — ungrounded superlative with satisfied grounding: WARN.
    if _has_done_claim(output_text) and _SUPERLATIVE_RE.search(output_text):
        return {
            "type": "warning",
            "severity": "warning",
            "gate": GATE_NAME,
            "error": (
                "UNGROUNDED SUPERLATIVE — the completion claim uses an un-hedged "
                "superlative (flawless / perfect / bulletproof / production-ready / ...). "
                "Files exist, but the strong claim overshoots the evidence. Hedge it "
                "('should', 'appears to', scope the claim) or show the evidence that "
                "justifies the superlative."
            ),
            "violations": ["ungrounded_superlative"],
        }

    # Tier 3 — satisfied grounding, no superlative issue: PASS.
    return None


def on_load() -> None:
    """Smoke test on import."""
    from hook_state_manager import check_fake_done
    assert callable(check_fake_done)


if __name__ == "__main__":
    import sys

    print("Running Stop_fake_done_detector.py self-test...", file=sys.stderr)

    from hook_state_manager import clear_state

    tid = "test_terminal_fake"
    sid = "test_session_fake"

    # Test 1: done-claim with a REAL file on disk → PASS (grounded evidence).
    import tempfile
    from pathlib import Path
    with tempfile.TemporaryDirectory() as td:
        (Path(td) / "engine.py").write_text("x=1\n", encoding="utf-8")
        data = {
            "terminal_id": tid, "session_id": sid, "cwd": td,
            "output_text": "Implementation complete. Wrote engine.py",
            "all_violations": [],
        }
        assert run_fake_done_detector(data) is None, "grounded evidence must pass"

        # Test 1b: done-claim referencing a MISSING file → BLOCK (block-first, first occurrence).
        data = {
            "terminal_id": tid, "session_id": sid, "cwd": td,
            "output_text": "Implementation complete. Wrote council_core/engine/council.py",
            "all_violations": [],
        }
        result = run_fake_done_detector(data)
        assert result is not None and result["severity"] == "block", (
            f"block-first: fabricated evidence must BLOCK on first occurrence, got {result}"
        )

        # Test B: done-claim + real file + ungrounded superlative → WARN.
        data = {
            "terminal_id": tid, "session_id": sid, "cwd": td,
            "output_text": "Implementation complete. Flawless, bulletproof fix. Wrote engine.py",
            "all_violations": [],
        }
        result = run_fake_done_detector(data)
        assert result is not None and result["severity"] == "warning", (
            f"ungrounded superlative + satisfied grounding must WARN, got {result}"
        )

        # --- CHANGE-007 read-side (Tier 1.5) ---
        # Guard: only meaningful when the ledger dependency loaded.
        if _LEDGER_AVAILABLE:
            import ledger as _ledger
            from pathlib import Path as _P
            _ledger.reset_ledger()
            try:
                eng = _P(td) / "engine.py"

                # Test C: verification-claim + file exists + NOT verified → WARN.
                data = {
                    "terminal_id": tid, "session_id": sid, "cwd": td,
                    "output_text": "Tests passed. Wrote engine.py",
                    "all_violations": [],
                }
                result = run_fake_done_detector(data)
                assert result is not None and result["severity"] == "warning", (
                    f"unverified completion claim must WARN, got {result}"
                )

                # Test D: after record_verification, same claim → PASS (is_verified True).
                _ledger.record_verification(str(eng), mode="strict",
                                            command="pytest", exit_code=0)
                data = {
                    "terminal_id": tid, "session_id": sid, "cwd": td,
                    "output_text": "Tests passed. Wrote engine.py",
                    "all_violations": [],
                }
                assert run_fake_done_detector(data) is None, (
                    "verified completion claim must PASS"
                )
            finally:
                _ledger.reset_ledger()

    # Test 2: done-claim with NO evidence → BLOCK (block-first, first occurrence).
    data = {
        "terminal_id": tid, "session_id": sid,
        "output_text": "Implementation complete.",
        "all_violations": [],
    }
    result = run_fake_done_detector(data)
    assert result is not None and result["severity"] == "block", (
        f"block-first: no-evidence claim must BLOCK on first occurrence, got {result}"
    )

    # Clean up
    clear_state(tid, "last_violations.json")
    clear_state(tid, "fake_done_count.json")

    print("All Stop_fake_done_detector.py self-tests passed.", file=sys.stderr)
