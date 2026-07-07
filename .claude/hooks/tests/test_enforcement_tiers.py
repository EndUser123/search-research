#!/usr/bin/env python3
"""
Tests for Enforcement Tier System

Validates:
1. Advisory hooks return warnings, not blocks
2. Strict hooks return blocks on violations
3. Telemetry logging works correctly
4. Warning fatigue detection works
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

# Add hooks directory to path
# __file__ is in .claude/hooks/tests/, so parent.parent is .claude/hooks/
HOOKS_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HOOKS_DIR))

from __lib.enforcement_telemetry import (  # noqa: E402
    detect_warning_fatigue,
    get_advisory_compliance_rate,
    log_enforcement_event,
    reset_db_path,
)


@pytest.fixture(autouse=True)
def reset_database_path() -> None:
    """
    Reset the cached database path before each test.

    This ensures test isolation by clearing the global _db_path
    singleton in enforcement_telemetry.py.
    """
    reset_db_path()
    yield
    reset_db_path()


class TestEnforcementTelemetry:
    """Test enforcement telemetry functions."""

    def test_log_advisory_event(self, tmp_path: Path) -> None:
        """Test logging an advisory event."""
        os.environ["CSF_DIAGNOSTICS_DIR"] = str(tmp_path)

        result = log_enforcement_event(
            session_id="test_session_1",
            skill_name="test_skill",
            tier="advisory",
            outcome="warned",
            behavior_changed=False,
            trigger_context="test_trigger",
        )

        assert result is True

    def test_log_strict_event(self, tmp_path: Path) -> None:
        """Test logging a strict event."""
        os.environ["CSF_DIAGNOSTICS_DIR"] = str(tmp_path)

        result = log_enforcement_event(
            session_id="test_session_1",
            skill_name="test_skill",
            tier="strict",
            outcome="blocked",
            behavior_changed=True,
            trigger_context="missing_skill_call",
        )

        assert result is True

    def test_invalid_tier_rejected(self, tmp_path: Path) -> None:
        """Test that invalid tiers are rejected."""
        os.environ["CSF_DIAGNOSTICS_DIR"] = str(tmp_path)

        result = log_enforcement_event(
            session_id="test_session_1",
            skill_name="test_skill",
            tier="invalid_tier",
            outcome="allowed",
        )

        assert result is False

    def test_invalid_outcome_rejected(self, tmp_path: Path) -> None:
        """Test that invalid outcomes are rejected."""
        os.environ["CSF_DIAGNOSTICS_DIR"] = str(tmp_path)

        result = log_enforcement_event(
            session_id="test_session_1",
            skill_name="test_skill",
            tier="advisory",
            outcome="invalid_outcome",
        )

        assert result is False

    def test_compliance_rate_empty(self, tmp_path: Path) -> None:
        """Test compliance rate with no events."""
        os.environ["CSF_DIAGNOSTICS_DIR"] = str(tmp_path)

        rate = get_advisory_compliance_rate()

        assert rate["rate"] == 0
        assert rate["total_warnings"] == 0

    def test_compliance_rate_with_events(self, tmp_path: Path) -> None:
        """Test compliance rate calculation."""
        os.environ["CSF_DIAGNOSTICS_DIR"] = str(tmp_path)

        # Log 4 advisory events: 2 with behavior change, 2 without
        for _ in range(2):
            log_enforcement_event(
                session_id="test_session",
                skill_name="skill_a",
                tier="advisory",
                outcome="warned",
                behavior_changed=True,
            )
        for _ in range(2):
            log_enforcement_event(
                session_id="test_session",
                skill_name="skill_a",
                tier="advisory",
                outcome="warned",
                behavior_changed=False,
            )

        rate = get_advisory_compliance_rate()

        assert rate["rate"] == 50.0  # 2 out of 4 changed behavior
        assert rate["total_warnings"] == 4

    def test_warning_fatigue_detection(self, tmp_path: Path) -> None:
        """Test warning fatigue detection."""
        os.environ["CSF_DIAGNOSTICS_DIR"] = str(tmp_path)

        # Log 5 warnings for same skill without behavior change
        for _ in range(5):
            log_enforcement_event(
                session_id="test_session",
                skill_name="fatigued_skill",
                tier="advisory",
                outcome="warned",
                behavior_changed=False,
            )

        fatigue = detect_warning_fatigue("test_session", threshold=3)

        assert len(fatigue) == 1
        assert fatigue[0]["skill_name"] == "fatigued_skill"
        assert fatigue[0]["warning_count"] >= 3

    def test_no_fatigue_below_threshold(self, tmp_path: Path) -> None:
        """Test no fatigue detected when below threshold."""
        os.environ["CSF_DIAGNOSTICS_DIR"] = str(tmp_path)

        # Log only 2 warnings (below threshold of 3)
        for _ in range(2):
            log_enforcement_event(
                session_id="test_session",
                skill_name="not_fatigued_skill",
                tier="advisory",
                outcome="warned",
                behavior_changed=False,
            )

        fatigue = detect_warning_fatigue("test_session", threshold=3)

        assert len(fatigue) == 0  # Only fatigued_skill from previous test


class TestEnforcementTierValidator:
    """Test frontmatter validation in SKILL.md files.

    enforcement field removed 2026-07-07 (dead concept per user directive —
    all manually-invoked skills are enforced). Only workflow_steps is validated.
    """

    @pytest.fixture
    def validator(self):
        from posttooluse.enforcement_tier_validator import validate_enforcement_tier

        return validate_enforcement_tier

    def test_enforcement_not_required(self, validator) -> None:
        """Regression: enforcement field is NOT required (dead concept).

        A SKILL.md with workflow_steps but NO enforcement field must pass
        validation. This is the user's directive: "I REALLY don't want
        enforcement in the skills frontmatter."
        """
        content = """---
name: test-skill
workflow_steps:
  - step_one: Description
---
# Content
"""
        result = validator("test/SKILL.md", content)

        assert result["valid"] is True
        assert result["tier"] is None

    def test_missing_workflow_steps_field(self, validator) -> None:
        """Test missing workflow_steps field."""
        content = """---
name: test-skill
---
# Content
"""
        result = validator("test/SKILL.md", content)

        assert result["valid"] is False
        assert "workflow_steps" in result["warning"].lower()

    def test_workflow_steps_present_empty_inline(self, validator) -> None:
        """Regression: `workflow_steps: []` is present, NOT missing.

        Previous regex `^workflow_steps:\\s*$` only matched the empty-value
        form, so `workflow_steps: []` was wrongly flagged missing. Empty list
        is valid — it means "no workflow to enforce".
        """
        content = """---
name: test-skill
workflow_steps: []
---
# Content
"""
        result = validator("test/SKILL.md", content)

        assert result["valid"] is True

    def test_workflow_steps_present_empty_block(self, validator) -> None:
        """`workflow_steps:` with no value (block empty) is also present."""
        content = """---
name: test-skill
workflow_steps:
---
# Content
"""
        result = validator("test/SKILL.md", content)

        assert result["valid"] is True

    def test_workflow_steps_present_non_empty_inline(self, validator) -> None:
        """`workflow_steps: [a, b]` inline non-empty list is present."""
        content = """---
name: test-skill
workflow_steps: [analyze, execute, verify]
---
# Content
"""
        result = validator("test/SKILL.md", content)

        assert result["valid"] is True


class TestAdvisoryVsStrictBehavior:
    """Test that advisory returns warnings, strict returns blocks."""

    def test_advisory_hook_returns_warning(self) -> None:
        """Verify advisory enforcement returns warning, not block."""
        # This is a documentation test - actual behavior tested via integration
        # Advisory should return {"ok": true, "warning": "..."} not {"ok": false}
        advisory_response = {"ok": True, "warning": "ADVISORY: Step missing - use /task list"}
        assert advisory_response["ok"] is True
        assert "warning" in advisory_response

    def test_strict_hook_returns_block(self) -> None:
        """Verify strict enforcement returns block on violation."""
        # Strict should return {"ok": false} on violation
        strict_response = {"ok": False, "reason": "Skill workflow not followed"}
        assert strict_response["ok"] is False


class TestEnforcementRateLimiter:
    """Test enforcement rate limiting for advisory warnings."""

    def test_first_warning_shows(self, tmp_path: Path) -> None:
        """Test first warning for a skill should be shown."""
        os.environ["CSF_STATE_DIR"] = str(tmp_path)
        os.environ["CLAUDE_SESSION_ID"] = "rate_test_session_1"

        # Import after setting env vars
        from __lib.enforcement_rate_limiter import (
            clear_warning_history,
            should_show_warning,
        )

        # Clear any existing state
        clear_warning_history()

        result = should_show_warning("test_skill")
        assert result is True

    def test_second_warning_rate_limited(self, tmp_path: Path) -> None:
        """Test second warning for same skill is rate limited."""
        os.environ["CSF_STATE_DIR"] = str(tmp_path)
        os.environ["CLAUDE_SESSION_ID"] = "rate_test_session_2"

        from __lib.enforcement_rate_limiter import (
            clear_warning_history,
            record_warning_shown,
            should_show_warning,
        )

        clear_warning_history()

        # First warning should show
        assert should_show_warning("test_skill") is True

        # Record warning shown
        record_warning_shown("test_skill", warning_content="Test warning")

        # Second warning should be rate limited
        assert should_show_warning("test_skill") is False

    def test_different_skills_both_show(self, tmp_path: Path) -> None:
        """Test different skills each get their own warning."""
        os.environ["CSF_STATE_DIR"] = str(tmp_path)
        os.environ["CLAUDE_SESSION_ID"] = "rate_test_session_3"

        from __lib.enforcement_rate_limiter import (
            clear_warning_history,
            record_warning_shown,
            should_show_warning,
        )

        clear_warning_history()

        # First skill
        assert should_show_warning("skill_a") is True
        record_warning_shown("skill_a")

        # Second skill should still show
        assert should_show_warning("skill_b") is True

    def test_terminal_scoped_warnings(self, tmp_path: Path) -> None:
        """Test terminal-scoped warnings are independent."""
        os.environ["CSF_STATE_DIR"] = str(tmp_path)
        os.environ["CLAUDE_SESSION_ID"] = "rate_test_session_4"

        from __lib.enforcement_rate_limiter import (
            clear_warning_history,
            record_warning_shown,
            should_show_warning,
        )

        clear_warning_history()

        # Warning for terminal_1
        assert should_show_warning("skill_x", terminal_id="terminal_1") is True
        record_warning_shown("skill_x", terminal_id="terminal_1")

        # Same skill, different terminal should still show
        assert should_show_warning("skill_x", terminal_id="terminal_2") is True

    def test_clear_history_resets_warnings(self, tmp_path: Path) -> None:
        """Test clearing history allows warnings to show again."""
        os.environ["CSF_STATE_DIR"] = str(tmp_path)
        os.environ["CLAUDE_SESSION_ID"] = "rate_test_session_5"

        from __lib.enforcement_rate_limiter import (
            clear_warning_history,
            record_warning_shown,
            should_show_warning,
        )

        clear_warning_history()

        # Show and record warning
        assert should_show_warning("reset_skill") is True
        record_warning_shown("reset_skill")

        # Verify rate limited
        assert should_show_warning("reset_skill") is False

        # Clear history
        cleared = clear_warning_history()
        assert cleared >= 1

        # Should show again after clear
        assert should_show_warning("reset_skill") is True

    def test_session_stats(self, tmp_path: Path) -> None:
        """Test session statistics tracking."""
        os.environ["CSF_STATE_DIR"] = str(tmp_path)
        os.environ["CLAUDE_SESSION_ID"] = "rate_test_session_6"

        from __lib.enforcement_rate_limiter import (
            clear_warning_history,
            get_session_stats,
            record_warning_shown,
        )

        clear_warning_history()

        # Record multiple warnings
        record_warning_shown("skill_1")
        record_warning_shown("skill_2")
        record_warning_shown("skill_3")

        stats = get_session_stats()
        assert stats["total_warnings"] == 3
        assert stats["unique_skills"] == 3
        assert stats["session_created"] is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
