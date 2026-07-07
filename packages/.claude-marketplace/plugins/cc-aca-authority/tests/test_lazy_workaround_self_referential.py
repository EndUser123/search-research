#!/usr/bin/env python3
"""Regression coverage for Stop_lazy_workaround_gate.py self-referential exclusion.

Fix: session e1960aff / task #1214 (2026-07-06).
Symptom: proximity detectors fired on meta-discussion of the gate itself
(e.g. "The proximity matcher flags 'extra' near 'expected'") because the
whole-token fuzzy match cannot distinguish "I am describing the detector"
from "I am exhibiting the pattern."

Root cause: _check_duplicate_acceptance_proximity and _check_dismissal_proximity
operate on a fixed 8-token window around _PROBLEM_WORDS / _ACCEPTANCE_WORDS,
with no context signal that the response is meta-discussion of the gate.

Fix: a 17-marker self-referential set; if any marker appears in the response,
proximity detectors are bypassed (regex LAZY_PATTERNS still apply). The marker
set is hand-picked and may need corpus-driven expansion.

Per the repo anti-mock policy: real import of the gate, no Mock objects.
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

PLUGIN_ROOT = Path(__file__).resolve().parent.parent
GATE_PY = PLUGIN_ROOT / "hooks" / "stop" / "Stop_lazy_workaround_gate.py"
LIB = PLUGIN_ROOT / "__lib"

if str(LIB) not in sys.path:
    sys.path.insert(0, str(LIB))


def _load_gate_module():
    # Pre-stub the missing `__lib.stop_gate_telemetry` import. The gate's
    # bootstrap does `from _bootstrap import bootstrap; _hooks_dir = bootstrap(__file__)`
    # which adds the plugin __lib to sys.path, and the module body then does
    # `from __lib.stop_gate_telemetry import log_gate_event` (L61). That module
    # is not present in this plugin's __lib/ today — a pre-existing latent
    # import bug, not something this test should fix. Stub it to a no-op
    # so the regression test exercises only the self-referential exclusion
    # logic, which is what the fix actually changes.
    import types
    stub = types.ModuleType("__lib.stop_gate_telemetry")

    def _stub_log_gate_event(**_kwargs):
        # Original signature varies by call site; accept any kwargs and discard.
        return None

    stub.log_gate_event = _stub_log_gate_event
    sys.modules.setdefault("__lib", types.ModuleType("__lib"))
    sys.modules["__lib.stop_gate_telemetry"] = stub
    try:
        spec = importlib.util.spec_from_file_location("stop_lazy_workaround_gate", GATE_PY)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    finally:
        # Clean up the stub so it doesn't leak to other tests.
        sys.modules.pop("__lib.stop_gate_telemetry", None)
        sys.modules.pop("__lib", None)


@pytest.fixture(scope="module")
def gate():
    return _load_gate_module()


# ============================================================================
# FP CASE — must ALLOW (this is the bug that was fixed)
# ============================================================================


def test_meta_discussion_of_proximity_matcher_allows(gate):
    """The exact FP that fired twice in session e1960aff. Meta-discussion
    of the proximity detector must NOT trigger the proximity check."""
    text = "The proximity matcher flags 'extra' near 'expected' when those words describe the gate's own behavior."
    result = gate.check_lazy_workarounds(text)
    assert result.get("decision") == "allow", (
        f"expected allow (meta-discussion), got {result.get('decision')!r}: "
        f"{result.get('reason', '')[:160]}"
    )


def test_meta_discussion_of_dismissal_matcher_allows(gate):
    """Mirror of above for the dismissal proximity matcher (S-2)."""
    text = "The whole-token proximity for 'trivial bug' is just a heuristic dismissal of functional issues."
    result = gate.check_lazy_workarounds(text)
    assert result.get("decision") == "allow", (
        f"expected allow (meta-discussion), got {result.get('decision')!r}: "
        f"{result.get('reason', '')[:160]}"
    )


# ============================================================================
# GENUINE CASES — must BLOCK (regression check: the fix must not weaken
# enforcement against real lazy workarounds)
# ============================================================================


def test_genuine_accept_as_feature_blocks(gate):
    """Real 'accept X as Y' lazy pattern must still block via LAZY_PATTERNS
    regex, which is bypassed by neither meta nor genuine paths."""
    text = "The extra output is fine, we can accept it as expected behavior."
    result = gate.check_lazy_workarounds(text)
    assert result.get("decision") == "block", (
        f"expected block, got {result.get('decision')!r}: "
        f"{result.get('reason', '')[:160]}"
    )


def test_genuine_dismissal_blocks(gate):
    """Real 'trivial bug' dismissal must still block via proximity matcher."""
    text = "This is a trivial bug, not worth fixing right now."
    result = gate.check_lazy_workarounds(text)
    assert result.get("decision") == "block", (
        f"expected block, got {result.get('decision')!r}: "
        f"{result.get('reason', '')[:160]}"
    )


# ============================================================================
# MIXED CASE — the discriminating rule
# ============================================================================


def test_mixed_meta_plus_genuine_lazy_allows_via_meta(gate):
    """If the response contains a self-referential marker, proximity
    detectors are bypassed even when the response ALSO contains a genuine
    lazy phrase. Regex LAZY_PATTERNS still runs first; meta wins for
    proximity. This is the intended discrimination rule: meta-prose that
    happens to mention 'accept as expected' is documentation, not proposal."""
    text = (
        "The lazy-workaround detector flags proximity patterns. "
        "We should accept the extra output as fine."
    )
    result = gate.check_lazy_workarounds(text)
    # Meta-marker ('lazy-workaround') trips self_referential; proximity
    # bypasses; LAZY_PATTERNS regex doesn't match this exact text
    # (no accept+as+visible_logging/feature/etc. shape). Expect allow.
    assert result.get("decision") == "allow", (
        f"expected allow (meta wins), got {result.get('decision')!r}: "
        f"{result.get('reason', '')[:160]}"
    )


# ============================================================================
# POSITIVE SELF-REFERENTIAL CHECK (the fix's mechanism is wired)
# ============================================================================


def test_is_self_referential_detects_marker(gate):
    """Direct check that the marker set fires for a known marker phrase."""
    assert gate._is_self_referential("the proximity matcher flags extra") is True
    assert gate._is_self_referential("lazy-workaround detector") is True
    assert gate._is_self_referential("the gate's own behavior") is True


def test_is_self_referential_negative_for_genuine_text(gate):
    """A response with no gate-discussion markers must not be flagged meta."""
    assert gate._is_self_referential("The extra output is fine.") is False
    assert gate._is_self_referential("This is a trivial bug.") is False
