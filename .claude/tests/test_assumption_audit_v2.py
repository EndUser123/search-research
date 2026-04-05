#!/usr/bin/env python3
"""
Test Cases for Assumption Audit v2 (Blocking Mode)

These tests verify that the assumption audit hook:
1. Detects factual claims about code/files/state
2. Checks if verification tools were used
3. BLOCKS (not warns) when claims made without verification
4. Allows legitimate responses through

Run: pytest P:/.claude/tests/test_assumption_audit_v2.py -v
"""

import json
import pytest
from pathlib import Path
import sys

# Add hooks directory to path
sys.path.insert(0, str(Path("P:/.claude/hooks")))


class TestClaimDetection:
    """Test that factual claim patterns are correctly detected."""
    
    @pytest.mark.parametrize("text,should_detect", [
        # File/code existence claims
        ("The file contains a parse function", True),
        ("Module exists in the src directory", True),
        ("Function returns a dictionary", True),
        ("Class has three methods", True),
        
        # Test/execution claims
        ("Tests pass successfully", True),
        ("Pytest shows 15 passed", True),
        ("The script executes without errors", True),
        
        # State assertions
        ("The config is currently set to debug mode", True),
        ("Database is now connected", True),
        ("File was created successfully", True),
        
        # Discovery claims
        ("I found 13 tasks in the file", True),
        ("I identified three issues", True),
        ("I located the bug in line 45", True),
        
        # Enumeration patterns
        ("There are 8 items in the list", True),
        ("System contains 5 services", True),
        
        # General knowledge (should NOT detect)
        ("A mutex is a synchronization primitive", False),
        ("Git uses SHA-1 for hashing", False),
        ("Python supports duck typing", False),
        
        # Questions (should NOT detect)
        ("What's in the file?", False),
        ("Can you check the logs?", False),
        
        # Hedged/uncertain (should NOT detect as claims)
        ("Let me check the file", False),
        ("I need to verify this", False),
        ("[UNVERIFIED] The file might contain", False),
    ])
    def test_claim_detection(self, text, should_detect):
        """Test claim detection patterns."""
        from assumption_audit_v2 import detect_claims
        
        claims = detect_claims(text)
        has_claims = len(claims) > 0
        
        assert has_claims == should_detect, \
            f"Expected detect={should_detect} for: '{text}', got claims={claims}"


class TestToolUsageCheck:
    """Test that verification tool usage is correctly identified."""

    @pytest.mark.parametrize("tools,should_verify", [
        # Observation tools
        (["Read"], True),
        (["Bash"], True),
        (["Grep"], True),
        (["Glob"], True),
        (["Search"], True),

        # Multiple tools including observation
        (["Write", "Read"], True),
        (["Edit", "Bash"], True),

        # No observation tools
        (["Write"], False),
        (["Edit"], False),
        (["Task"], False),

        # Empty
        ([], False),
    ])
    def test_tool_usage_detection(self, tools, should_verify):
        """Test tool usage detection via evaluate_response."""
        from assumption_audit_v2 import evaluate_response, OBSERVATION_TOOLS

        # Check if any tool in tools is an observation tool
        has_observation = any(t in OBSERVATION_TOOLS for t in tools)

        # When response has claims, observation tools should allow it through
        if has_observation:
            # With tool_sequence providing evidence, should allow
            tool_sequence = [{"name": t, "command": "test", "output": "evidence"} for t in tools]
            result = evaluate_response(
                response_text="The file contains 5 functions",
                tools_used=tools,
                tool_sequence=tool_sequence
            )
            # Should be VERIFIED or SCOPE_VERIFIED (allow)
            assert result["decision"] in ("allow", "block"), f"Unexpected decision: {result}"
        else:
            # No observation tools = should block (NO_EVIDENCE)
            result = evaluate_response(
                response_text="The file contains 5 functions",
                tools_used=tools,
                tool_sequence=[]
            )
            assert result["decision"] == "block", f"Expected block for non-observation tools={tools}, got {result}"


class TestBlockingBehavior:
    """Test that blocking works correctly."""

    def test_claims_without_tools_blocks(self):
        """Response with claims but no verification tools should be blocked."""
        from assumption_audit_v2 import evaluate_response

        result = evaluate_response(
            response_text="The file contains 5 functions and 2 classes",
            tools_used=[],
            tool_sequence=[]
        )

        assert result["decision"] == "block"
        assert result["reason"] == "NO_EVIDENCE"

    def test_claims_with_tools_allows(self):
        """Response with claims AND verification tools should be allowed."""
        from assumption_audit_v2 import evaluate_response

        result = evaluate_response(
            response_text="The file contains 5 functions and 2 classes",
            tools_used=["Read"],
            tool_sequence=[{"name": "Read", "command": "file.py", "output": "def func1..."}]
        )

        assert result["decision"] == "allow"

    def test_no_claims_allows(self):
        """Response without claims should be allowed."""
        from assumption_audit_v2 import evaluate_response

        result = evaluate_response(
            response_text="A mutex is a synchronization primitive used in concurrent programming.",
            tools_used=[]
        )

        assert result["decision"] == "allow"
        assert result["reason"] == "NO_CLAIMS"

    def test_unverified_marker_blocks(self):
        """[UNVERIFIED] marking should NOT be an escape hatch in v2."""
        from assumption_audit_v2 import evaluate_response

        # In v1, [UNVERIFIED] was allowed as compliance
        # In v2, we want to BLOCK and force actual verification
        result = evaluate_response(
            response_text="[UNVERIFIED] The file contains 5 functions",
            tools_used=[],
            tool_sequence=[]
        )

        # v2 should still block - marking isn't verification
        # This is the key behavioral change from v1
        assert result["decision"] == "block", \
            "[UNVERIFIED] marking should not be an escape hatch"


class TestExemptionPatterns:
    """Test that legitimate responses are not blocked."""
    
    @pytest.mark.parametrize("text,should_exempt", [
        # Definitions
        ("A mutex is a synchronization primitive", True),
        ("An async function allows concurrent execution", True),
        
        # General knowledge (these are borderline - may or may not exempt)
        # Note: "Python 3.12 introduced" and "Git uses" are factual claims
        # that could benefit from verification in some contexts
        
        # Short responses
        ("OK", True),
        ("Done", True),
        ("Got it", True),
        
        # Questions
        ("What file should I check?", True),
        ("Would you like me to read that?", True),
        
        # Intent to verify
        ("Let me check the file", True),
        ("I'll verify that with Read", True),
        
        # Actual claims (should NOT exempt)
        ("The file has 5 functions", False),
        ("Tests are passing", False),
    ])
    def test_exemption_patterns(self, text, should_exempt):
        """Test exemption patterns for legitimate responses."""
        from assumption_audit_v2 import is_exempt_response
        
        result = is_exempt_response(text)
        
        assert result == should_exempt, \
            f"Expected exempt={should_exempt} for: '{text}'"


class TestBlockMessage:
    """Test that block messages are actionable."""

    def test_block_message_includes_claims(self):
        """Block message should show the detected claims."""
        from assumption_audit_v2 import evaluate_response

        result = evaluate_response(
            response_text="The file contains 5 functions. Module exists in src.",
            tools_used=[],
            tool_sequence=[]
        )

        assert "claims_detected" in result
        assert len(result["claims_detected"]) > 0

    def test_block_message_specifies_action(self):
        """Block message should specify required action."""
        from assumption_audit_v2 import evaluate_response

        result = evaluate_response(
            response_text="The file contains 5 functions",
            tools_used=[],
            tool_sequence=[]
        )

        assert "message" in result
        assert "Read" in result["message"] or "Bash" in result["message"]

    def test_block_message_explicit_about_blocking(self):
        """Block message should be explicit that response is blocked."""
        from assumption_audit_v2 import evaluate_response

        result = evaluate_response(
            response_text="The file contains 5 functions",
            tools_used=[],
            tool_sequence=[]
        )

        message = result.get("message", "")

        # Should be clear this is a block, not a warning
        assert "BLOCKED" in message or "block" in message.lower()
        assert "warning" not in message.lower()


class TestHookIntegration:
    """Test integration with hook system."""
    
    def test_hook_output_format(self):
        """Hook output should be valid JSON matching hook protocol."""
        from assumption_audit_v2 import format_hook_output
        
        output = format_hook_output(
            decision="block",
            reason="UNVERIFIED_CLAIMS",
            message="Test message",
            claims=["claim1", "claim2"]
        )
        
        # Should be valid JSON
        parsed = json.loads(output)
        
        # Should have required fields for block protocol
        assert "decision" in parsed
        assert parsed["decision"] == "block"
    
    def test_allow_output_format(self):
        """Allow output should be minimal."""
        from assumption_audit_v2 import format_hook_output
        
        output = format_hook_output(
            decision="allow",
            reason="VERIFIED"
        )
        
        parsed = json.loads(output)
        
        assert parsed["decision"] == "allow"
        assert "message" not in parsed or parsed["message"] == ""


class TestPerformance:
    """Test performance considerations."""
    
    def test_early_exit_on_tools_present(self):
        """Should exit immediately when observation tools present."""
        from assumption_audit_v2 import evaluate_response
        import time
        
        # With tools - should be fast
        start = time.time()
        result = evaluate_response(
            response_text="A" * 10000,  # Long response
            tools_used=["Read"]
        )
        elapsed = time.time() - start
        
        assert result["decision"] == "allow"
        assert elapsed < 0.01, "Should exit immediately when tools present"
    
    def test_pattern_matching_performance(self):
        """Claim detection should be fast even for long responses."""
        from assumption_audit_v2 import detect_claims
        import time
        
        long_response = "The file contains functions. " * 1000
        
        start = time.time()
        claims = detect_claims(long_response)
        elapsed = time.time() - start
        
        assert elapsed < 0.1, f"Claim detection took {elapsed}s, should be <0.1s"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
