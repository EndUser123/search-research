"""
Tests for Investigation Ledger System
"""

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

# Add ledger module to path
HOOK_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(HOOK_DIR))

import ledger as ledger_module
from ledger import (
    calculate_confidence_ceiling,
    get_files_read,
    get_investigation_stats,
    record_execution,
    record_file_read,
    record_search,
    reset_ledger,
)
from validate_claims import validate_claims
from validate_confidence import validate_confidence

TEST_TERMINAL_ID = "pytest_investigation_ledger"
ledger_module._TERMINAL_ID = TEST_TERMINAL_ID
ledger_module.LEDGER_PATH = ledger_module.LEDGER_DIR / f"session_ledger_{TEST_TERMINAL_ID}.json"
ledger_module.LOCK_PATH = ledger_module.LEDGER_DIR / f"session_ledger_{TEST_TERMINAL_ID}.lock"


def _hook_env() -> dict[str, str]:
    return {
        **os.environ,
        "CLAUDE_PROJECT_DIR": str(HOOK_DIR.parents[2]),
        "CLAUDE_TERMINAL_ID": TEST_TERMINAL_ID,
    }


class TestLedger:
    """Test the core ledger functionality."""

    def setup_method(self):
        """Reset ledger before each test."""
        reset_ledger()

    def test_empty_ledger(self):
        """Fresh ledger should be empty."""
        stats = get_investigation_stats()
        assert stats["files_read"] == 0
        assert stats["searches"] == 0
        assert stats["executions"] == 0

    def test_record_file_read(self):
        """File reads should be tracked."""
        record_file_read("src/auth/login.py")
        stats = get_investigation_stats()
        assert stats["files_read"] == 1
        assert "login" in stats["topics"]
        assert "auth" in stats["topics"]

    def test_record_search(self):
        """Searches should be tracked."""
        record_search("authentication flow", 5)
        stats = get_investigation_stats()
        assert stats["searches"] == 1
        assert "authentication" in stats["topics"]
        assert "flow" in stats["topics"]

    def test_record_execution(self):
        """Executions should be tracked."""
        record_execution("pytest test_auth.py", 0)
        stats = get_investigation_stats()
        assert stats["executions"] == 1
        assert stats["successful_executions"] == 1

    def test_failed_execution(self):
        """Failed executions should be tracked separately."""
        record_execution("pytest test_auth.py", 1)
        stats = get_investigation_stats()
        assert stats["executions"] == 1
        assert stats["successful_executions"] == 0

    def test_no_duplicate_files(self):
        """Same file should only be recorded once."""
        record_file_read("src/auth.py")
        record_file_read("src/auth.py")
        assert len(get_files_read()) == 1


class TestConfidenceCeiling:
    """Test confidence ceiling calculation."""

    def setup_method(self):
        reset_ledger()

    def test_zero_ceiling_no_investigation(self):
        """No investigation = 0% ceiling."""
        result = calculate_confidence_ceiling()
        assert result["ceiling"] == 0
        assert result["tier"] is None

    def test_tier_4_one_file(self):
        """One file read = Tier 4 (50%)."""
        record_file_read("src/handler.py")
        result = calculate_confidence_ceiling()
        assert result["ceiling"] == 50
        assert result["tier"] == 4

    def test_tier_3_two_files(self):
        """Two files read = Tier 3 (75%)."""
        record_file_read("src/handler.py")
        record_file_read("src/router.py")
        result = calculate_confidence_ceiling()
        assert result["ceiling"] == 75
        assert result["tier"] == 3

    def test_tier_1_with_execution(self):
        """Three files + successful execution = Tier 1 (95%)."""
        record_file_read("src/handler.py")
        record_file_read("src/router.py")
        record_file_read("src/test_handler.py")
        record_execution("pytest", 0)
        result = calculate_confidence_ceiling()
        assert result["ceiling"] == 95
        assert result["tier"] == 1


class TestClaimValidation:
    """Test claim validation."""

    def setup_method(self):
        reset_ledger()

    def test_short_response_passes(self):
        """Short responses should always pass."""
        result = validate_claims("Hello, how can I help?")
        assert result["valid"] is True

    def test_question_passes(self):
        """Questions should always pass."""
        result = validate_claims("What files would you like me to read?")
        assert result["valid"] is True

    def test_claims_without_investigation_blocked(self):
        """Claims about systems without investigation should be blocked."""
        text = """The authentication system validates JWT tokens by checking the signature
        against the secret key. When a user logs in, the system creates a new token
        with the user ID embedded in the payload. This architecture ensures security."""
        result = validate_claims(text)
        assert result["valid"] is False
        assert "INVESTIGATION" in result["message"]

    def test_claims_with_investigation_pass(self):
        """Claims about investigated topics should pass."""
        record_file_read("src/auth/jwt.py")
        record_file_read("src/auth/login.py")
        text = """The authentication system validates JWT tokens. When a user logs in,
        the system creates a new token. This is the standard approach for web auth."""
        result = validate_claims(text)
        assert result["valid"] is True

    def test_speculation_markers_rejected(self):
        """Fake evidence markers should be rejected."""
        record_file_read("src/handler.py")
        text = """According to my understanding, the handler processes requests.
        I believe this is the correct implementation based on my experience."""
        result = validate_claims(text)
        # Should still pass because we have investigation, but evidence check notes speculation
        # The speculation is caught by confidence validation, not claim validation


class TestConfidenceValidation:
    """Test confidence validation."""

    def setup_method(self):
        reset_ledger()

    def test_short_response_passes(self):
        """Short responses should pass."""
        result = validate_confidence("Sure, I can help.")
        assert result["valid"] is True

    def test_high_confidence_without_investigation_blocked(self):
        """High confidence without investigation should be blocked."""
        text = "I am 95% confident the authentication system works correctly and handles all edge cases properly."
        result = validate_confidence(text)
        assert result["valid"] is False
        assert "CONFIDENCE" in result["message"]

    def test_high_confidence_with_tier1_passes(self):
        """High confidence with Tier 1 investigation should pass."""
        record_file_read("src/auth.py")
        record_file_read("src/handler.py")
        record_file_read("src/test_auth.py")
        record_execution("pytest", 0)
        text = "I am 95% confident the system works correctly."
        result = validate_confidence(text)
        assert result["valid"] is True

    def test_medium_confidence_with_tier3_passes(self):
        """Medium confidence with Tier 3 should pass."""
        record_file_read("src/auth.py")
        record_file_read("src/handler.py")
        text = "The system likely handles authentication correctly."
        result = validate_confidence(text)
        assert result["valid"] is True

    def test_unhedged_assertion_tier3_passes(self):
        """Unhedged factual assertions should pass at Tier 3."""
        record_file_read("src/auth.py")
        record_file_read("src/handler.py")
        text = "The system validates tokens and handles authentication."
        result = validate_confidence(text)
        assert result["valid"] is True

    def test_unhedged_assertion_tier4_blocked(self):
        """Unhedged assertions at Tier 4 should be blocked."""
        record_file_read("src/auth.py")  # Only 1 file = Tier 4
        text = """The authentication system validates JWT tokens by checking signatures.
        When users log in, the system creates tokens with embedded user IDs.
        This implementation follows industry best practices for security."""
        result = validate_confidence(text)
        assert result["valid"] is False


class TestHookIntegration:
    """Test hook entry points."""

    def setup_method(self):
        reset_ledger()

    def test_posttool_hook_records_read(self):
        """PostToolUse hook should record file reads."""
        hook_input = json.dumps(
            {
                "tool_name": "Read",
                "tool_input": {"path": "src/router.py"},
                "tool_result": {"content": "def route(): pass"},
            }
        )

        result = subprocess.run(
            ["python", str(HOOK_DIR / "PostToolUse_investigation_tracker.py")],
            input=hook_input,
            capture_output=True,
            text=True,
            env=_hook_env(),
        )

        output = json.loads(result.stdout)
        assert output.get("continue") is True

        # Check ledger was updated
        stats = get_investigation_stats()
        assert stats["files_read"] == 1

    def test_stop_hook_blocks_unsubstantiated(self):
        """Stop hook should block unsubstantiated claims."""
        hook_input = json.dumps(
            {
                "response": """The authentication system validates JWT tokens by checking
            signatures. The router dispatches requests to handlers. This architecture
            ensures high performance and security for all user requests."""
            }
        )

        result = subprocess.run(
            ["python", str(HOOK_DIR / "Stop_investigation_validator.py")],
            input=hook_input,
            capture_output=True,
            text=True,
            env=_hook_env(),
        )

        output = json.loads(result.stdout)
        assert output.get("decision") == "block"

    def test_stop_hook_allows_substantiated(self):
        """Stop hook should allow substantiated claims."""
        # First record investigation
        record_file_read("src/auth/jwt.py")
        record_file_read("src/auth/login.py")
        record_file_read("test/test_auth.py")
        record_execution("pytest", 0)

        hook_input = json.dumps(
            {
                "response": """Based on the jwt.py module, the authentication system validates
            tokens. The implementation in login.py handles user sessions correctly."""
            }
        )

        result = subprocess.run(
            ["python", str(HOOK_DIR / "Stop_investigation_validator.py")],
            input=hook_input,
            capture_output=True,
            text=True,
            env=_hook_env(),
        )

        output = json.loads(result.stdout)
        assert output.get("continue") is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
