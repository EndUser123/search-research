#!/usr/bin/env python3
"""Unit tests for Stop hook verification enforcement gate."""

import os
import sys
from pathlib import Path
from unittest.mock import patch

# Add hooks directory to path
HOOKS_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HOOKS_DIR))


def test_verification_enforcement_disabled_by_default():
    """Test that verification enforcement is disabled by default."""
    # Ensure env var is not set
    os.environ.pop("VERIFICATION_ENFORCEMENT_ENABLED", None)

    from Stop import _run_verification_enforcement

    data = {"response": "Test response"}
    result = _run_verification_enforcement(data)

    # Should return None (allow) when disabled
    assert result is None, "Verification enforcement should be disabled by default"


def test_verification_enforcement_enabled_no_trails():
    """Test that verification enforcement allows when no breadcrumb trails exist."""
    os.environ["VERIFICATION_ENFORCEMENT_ENABLED"] = "true"

    from Stop import _run_verification_enforcement

    # Mock get_active_breadcrumb_trails to return empty list
    with patch("skill_guard.breadcrumb.tracker.get_active_breadcrumb_trails", return_value=[]):
        data = {"response": "Test response"}
        result = _run_verification_enforcement(data)

    # Should return None (allow) when no trails
    assert result is None, "Should allow when no breadcrumb trails exist"

    # Clean up
    os.environ.pop("VERIFICATION_ENFORCEMENT_ENABLED", None)


def test_verification_enforcement_with_pending_steps():
    """Test that verification enforcement blocks when pending steps exist."""
    os.environ["VERIFICATION_ENFORCEMENT_ENABLED"] = "true"

    from Stop import _run_verification_enforcement

    # Mock trail with pending verification step
    mock_trail = {
        "skill": "test-skill",
        "workflow_steps": [
            {"id": "step1", "kind": "execution"},
            {"id": "verify_checklist", "kind": "verification"},
        ],
        "completed_steps": ["step1"],  # Missing verify_checklist
    }

    with patch("skill_guard.breadcrumb.tracker.get_active_breadcrumb_trails", return_value=[mock_trail]):
        data = {"response": "Test response"}
        result = _run_verification_enforcement(data)

    # Should block with pending verification
    assert result is not None, "Should block with pending verification steps"
    assert result.get("decision") == "block", "Should have block decision"
    assert "test-skill:verify_checklist" in result.get("reason", ""), \
        "Should mention missing verification step"

    # Clean up
    os.environ.pop("VERIFICATION_ENFORCEMENT_ENABLED", None)


def test_verification_enforcement_all_steps_complete():
    """Test that verification enforcement allows when all steps are complete."""
    os.environ["VERIFICATION_ENFORCEMENT_ENABLED"] = "true"

    from Stop import _run_verification_enforcement

    # Mock trail with all steps complete
    mock_trail = {
        "skill": "test-skill",
        "workflow_steps": [
            {"id": "step1", "kind": "execution"},
            {"id": "verify_checklist", "kind": "verification"},
        ],
        "completed_steps": ["step1", "verify_checklist"],  # All complete
    }

    with patch("skill_guard.breadcrumb.tracker.get_active_breadcrumb_trails", return_value=[mock_trail]):
        data = {"response": "Test response"}
        result = _run_verification_enforcement(data)

    # Should allow when all verification steps complete
    assert result is None, "Should allow when all verification steps are complete"

    # Clean up
    os.environ.pop("VERIFICATION_ENFORCEMENT_ENABLED", None)


def test_verification_enforcement_bypass_flag():
    """Test that --skip-verification flag bypasses enforcement."""
    os.environ["VERIFICATION_ENFORCEMENT_ENABLED"] = "true"

    from Stop import _run_verification_enforcement

    # Mock trail with pending verification step
    mock_trail = {
        "skill": "test-skill",
        "workflow_steps": [
            {"id": "verify_checklist", "kind": "verification"},
        ],
        "completed_steps": [],  # Pending
    }

    with patch("skill_guard.breadcrumb.tracker.get_active_breadcrumb_trails", return_value=[mock_trail]):
        data = {
            "response": "Test response",
            "userMessage": "This message has --skip-verification flag",
        }
        result = _run_verification_enforcement(data)

    # Should allow when bypass flag is present
    assert result is None, "Should allow with --skip-verification flag"

    # Clean up
    os.environ.pop("VERIFICATION_ENFORCEMENT_ENABLED", None)


def test_verification_enforcement_multiple_pending_steps():
    """Test that verification enforcement reports all pending steps."""
    os.environ["VERIFICATION_ENFORCEMENT_ENABLED"] = "true"

    from Stop import _run_verification_enforcement

    # Mock trail with multiple pending verification steps
    mock_trail = {
        "skill": "test-skill",
        "workflow_steps": [
            {"id": "verify_checklist", "kind": "verification"},
            {"id": "verify_quality", "kind": "verification"},
        ],
        "completed_steps": [],  # Both pending
    }

    with patch("skill_guard.breadcrumb.tracker.get_active_breadcrumb_trails", return_value=[mock_trail]):
        data = {"response": "Test response"}
        result = _run_verification_enforcement(data)

    # Should block and mention both pending steps
    assert result is not None, "Should block with pending verification steps"
    reason = result.get("reason", "")
    assert "test-skill:verify_checklist" in reason, "Should mention first pending step"
    assert "test-skill:verify_quality" in reason, "Should mention second pending step"

    # Clean up
    os.environ.pop("VERIFICATION_ENFORCEMENT_ENABLED", None)


def test_verification_enforcement_mixed_step_formats():
    """Test that verification enforcement handles mixed string/dict workflow_steps."""
    os.environ["VERIFICATION_ENFORCEMENT_ENABLED"] = "true"

    from Stop import _run_verification_enforcement

    # Mock trail with mixed formats (string and dict)
    mock_trail = {
        "skill": "test-skill",
        "workflow_steps": [
            "step1",  # String format (no kind)
            {"id": "verify_checklist", "kind": "verification"},
        ],
        "completed_steps": ["step1"],
    }

    with patch("skill_guard.breadcrumb.tracker.get_active_breadcrumb_trails", return_value=[mock_trail]):
        data = {"response": "Test response"}
        result = _run_verification_enforcement(data)

    # Should only block on verification steps, not string steps
    assert result is not None, "Should block with pending verification step"
    assert "test-skill:verify_checklist" in result.get("reason", ""), \
        "Should mention missing verification step"
    # Should not mention step1 (it's not a verification step)
    assert "step1" not in result.get("reason", ""), \
        "Should not mention non-verification steps"

    # Clean up
    os.environ.pop("VERIFICATION_ENFORCEMENT_ENABLED", None)


def test_verification_enforcement_graceful_failure():
    """Test that verification enforcement fails open on errors."""
    os.environ["VERIFICATION_ENFORCEMENT_ENABLED"] = "true"

    from Stop import _run_verification_enforcement

    # Mock get_active_breadcrumb_trails to raise exception
    with patch("skill_guard.breadcrumb.tracker.get_active_breadcrumb_trails", side_effect=Exception("Test error")):
        data = {"response": "Test response"}
        result = _run_verification_enforcement(data)

    # Should fail open (allow) on error
    assert result is None, "Should fail open and allow on exception"

    # Clean up
    os.environ.pop("VERIFICATION_ENFORCEMENT_ENABLED", None)


if __name__ == "__main__":
    import pytest

    # Run tests
    pytest.main([__file__, "-v"])
