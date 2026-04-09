"""Tests for evidence_grounding_reminder.py"""

import os
import sys
import pytest

sys.path.insert(0, "P:/.claude/hooks")
from UserPromptSubmit_modules.base import HookContext

# Set env before importing the module
os.environ["EVIDENCE_GROUNDING_ENABLED"] = "true"
os.environ["EVIDENCE_GROUNDING_FREQUENCY"] = "3"

from UserPromptSubmit_modules.evidence_grounding_reminder import (
    evidence_grounding_reminder,
    _counters,
    VARIANTS,
)


def _make_context(session_id="test-session"):
    return HookContext(
        prompt="test prompt",
        session_id=session_id,
        terminal_id="test-terminal",
        data={},
    )


class TestConditionalFiring:
    """Every 3rd turn fires, others skip."""

    def test_turn_1_skips(self):
        _counters.clear()
        ctx = _make_context("s1")
        result = evidence_grounding_reminder(ctx)
        assert result.context is None

    def test_turn_3_fires(self):
        _counters.clear()
        ctx = _make_context("s1")
        evidence_grounding_reminder(ctx)  # t1
        evidence_grounding_reminder(ctx)  # t2
        result = evidence_grounding_reminder(ctx)  # t3 → fires
        assert result.context is not None
        assert result.context in VARIANTS

    def test_turn_3_fires(self):
        _counters.clear()
        ctx = _make_context("s1")
        evidence_grounding_reminder(ctx)  # t1
        evidence_grounding_reminder(ctx)  # t2
        result = evidence_grounding_reminder(ctx)  # t3
        assert result.context is not None
        assert result.context in VARIANTS

    def test_turn_6_fires(self):
        _counters.clear()
        ctx = _make_context("s1")
        for _ in range(5):
            evidence_grounding_reminder(ctx)
        result = evidence_grounding_reminder(ctx)  # t6
        assert result.context is not None
        assert result.context in VARIANTS


class TestRotation:
    """Variants rotate every 3 turns."""

    def test_variant_0_then_1(self):
        _counters.clear()
        ctx = _make_context("s2")
        # turns 1,2 skip; turn 3 fires with variant index (3//3)%4 = 1
        evidence_grounding_reminder(ctx)
        evidence_grounding_reminder(ctx)
        r1 = evidence_grounding_reminder(ctx)
        # turns 4,5 skip; turn 6 fires with variant index (6//3)%4 = 2
        evidence_grounding_reminder(ctx)
        evidence_grounding_reminder(ctx)
        r2 = evidence_grounding_reminder(ctx)
        assert r1.context == VARIANTS[1]
        assert r2.context == VARIANTS[2]


class TestSessionIsolation:
    """Different sessions have independent counters."""

    def test_session_a_and_b_independent(self):
        _counters.clear()
        ctx_a = _make_context("session-a")
        ctx_b = _make_context("session-b")
        # Fire session-a to turn 3
        for _ in range(3):
            evidence_grounding_reminder(ctx_a)
        # Session-b should still be on turn 1
        result = evidence_grounding_reminder(ctx_b)
        assert result.context is None


class TestDisabled:
    """When env is false, hook does nothing."""

    def test_disabled(self):
        os.environ["EVIDENCE_GROUNDING_ENABLED"] = "false"
        _counters.clear()
        ctx = _make_context("s-disabled")
        result = evidence_grounding_reminder(ctx)
        os.environ["EVIDENCE_GROUNDING_ENABLED"] = "true"
        assert result.context is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
