#!/usr/bin/env python3
"""
Tests for Reflexion Validator - Evidence Type Tracking

Tests that claims are only allowed when the cached evidence TYPE supports
the claim TYPE, not just file hash matching.
"""

# Import the module to test
import sys
import tempfile
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import StopHook_reflexion_validator as validator


class TestObservationTypeMapping:
    """Test observation type detection from tool usage."""

    def test_read_tool_returns_read_type(self):
        """Read tool maps to 'read' observation type."""
        obs_type = validator._get_observation_type("Read", {"file_path": "/tmp/test.py"})
        assert obs_type == "read"

    def test_bash_pytest_returns_test_type(self):
        """Bash with pytest command maps to 'bash_test' observation type."""
        obs_type = validator._get_observation_type("Bash", {"command": "pytest tests/test.py"})
        assert obs_type == "bash_test"

    def test_bash_lint_returns_lint_type(self):
        """Bash with ruff/lint command maps to 'bash_lint' observation type."""
        obs_type = validator._get_observation_type("Bash", {"command": "ruff check file.py"})
        assert obs_type == "bash_lint"

    def test_bash_generic_returns_bash_type(self):
        """Generic bash command maps to 'bash' observation type."""
        obs_type = validator._get_observation_type("Bash", {"command": "ls -la"})
        assert obs_type == "bash"

    def test_grep_returns_grep_type(self):
        """Grep tool maps to 'grep' observation type."""
        obs_type = validator._get_observation_type("Grep", {"pattern": "test"})
        assert obs_type == "grep"

    def test_web_search_returns_web_type(self):
        """Web search tools map to 'web' observation type."""
        obs_type = validator._get_observation_type("WebSearch", {"query": "test"})
        assert obs_type == "web"


class TestClaimEvidenceTypeMatching:
    """Test that claims require matching evidence types."""

    def test_read_evidence_does_not_support_test_claims(self):
        """
        Reading a file should NOT support claims about tests passing.

        Scenario:
        1. Read test_file.py (observation type: "read")
        2. Claim "The tests pass" (claim type: test execution)
        3. Should BLOCK - read doesn't prove tests pass
        """
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("def test_something():\n    assert True\n")
            test_file = f.name

        try:
            # Simulate: Turn 1 - Read the test file
            tools_used_read = [
                {"tool": "Read", "arguments": {"file_path": test_file}}
            ]

            # Update cache with read observation
            validator._update_hash_cache(tools_used_read)

            # Simulate: Turn 2 - Claim "tests pass" without fresh tools
            claim = "The tests pass"
            tools_used_claim = [
                {"tool": "Read", "arguments": {"file_path": test_file}}
            ]

            # Should NOT be supported (read != bash_test)
            assert not validator._is_claim_supported_by_evidence(claim, tools_used_claim)

        finally:
            Path(test_file).unlink()
            # Clear cache
            cache_file = validator._get_hash_cache_file()
            if cache_file.exists():
                cache_file.unlink()

    def test_bash_test_evidence_supports_test_claims(self):
        """
        Running pytest SHOULD support claims about tests passing.

        Scenario:
        1. Run pytest (observation type: "bash_test")
        2. Claim "The tests pass" (claim type: test execution)
        3. Should ALLOW - bash_test proves tests pass
        """
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("def test_something():\n    assert True\n")
            test_file = f.name

        try:
            # Simulate: Turn 1 - Run pytest (Bash tool)
            # Note: Bash doesn't extract file paths, so we manually add cache entry
            cache_file = validator._get_hash_cache_file()
            if cache_file.exists():
                cache_file.unlink()

            cache = validator._load_hash_cache()
            file_hash = validator._compute_file_hash(test_file)
            cache[test_file] = {
                "hash": file_hash,
                "observation_type": "bash_test"
            }
            validator._save_hash_cache(cache)

            # Simulate: Turn 2 - Claim "tests pass" without fresh tools
            claim = "The tests pass"
            tools_used_claim = [
                {"tool": "Read", "arguments": {"file_path": test_file}}
            ]

            # Should be supported (bash_test supports test claims)
            assert validator._is_claim_supported_by_evidence(claim, tools_used_claim)

        finally:
            Path(test_file).unlink()
            if cache_file.exists():
                cache_file.unlink()

    def test_read_evidence_supports_structure_claims(self):
        """
        Reading a file SHOULD support claims about file structure.

        Scenario:
        1. Read file.py (observation type: "read")
        2. Claim "The file contains a function named foo" (claim type: structure)
        3. Should ALLOW - read proves file structure
        """
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("def foo():\n    pass\n")
            test_file = f.name

        try:
            # Simulate: Turn 1 - Read the file
            tools_used_read = [
                {"tool": "Read", "arguments": {"file_path": test_file}}
            ]

            validator._update_hash_cache(tools_used_read)

            # Simulate: Turn 2 - Claim about structure
            claim = "The file contains a function named foo"
            tools_used_claim = [
                {"tool": "Read", "arguments": {"file_path": test_file}}
            ]

            # Should be supported (read supports structure claims)
            assert validator._is_claim_supported_by_evidence(claim, tools_used_claim)

        finally:
            Path(test_file).unlink()
            cache_file = validator._get_hash_cache_file()
            if cache_file.exists():
                cache_file.unlink()


class TestEvidenceTypeStorage:
    """Test that observation type is stored in cache."""

    def test_cache_stores_observation_type(self):
        """Cache entry should include 'observation_type' field."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("# test file\n")
            test_file = f.name

        try:
            tools_used = [
                {"tool": "Read", "arguments": {"file_path": test_file}}
            ]

            # Clear cache first
            cache_file = validator._get_hash_cache_file()
            if cache_file.exists():
                cache_file.unlink()

            # Update cache
            validator._update_hash_cache(tools_used)

            # Load and verify structure
            cache = validator._load_hash_cache()

            # Verify the entry exists with correct structure
            assert test_file in cache
            assert isinstance(cache[test_file], dict)
            assert "hash" in cache[test_file]
            assert "observation_type" in cache[test_file]
            assert cache[test_file]["observation_type"] == "read"

        finally:
            Path(test_file).unlink()
            if cache_file.exists():
                cache_file.unlink()


class TestClaimTypeDetection:
    """Test claim type detection from response text."""

    def test_detect_test_claim_type(self):
        """Claims about tests should map to 'test' claim type."""
        test_claims = [
            "The tests pass",
            "All tests passed",
            "pytest shows 5 passed",
        ]
        for claim in test_claims:
            claim_type = validator._get_claim_type(claim)
            assert claim_type == "test", f"Claim '{claim}' should be 'test' type, got '{claim_type}'"

    def test_detect_structure_claim_type(self):
        """Claims about file structure should map to 'structure' claim type."""
        structure_claims = [
            "The file contains a function",
            "There's a class named Foo",
            "The import is at the top",
        ]
        for claim in structure_claims:
            claim_type = validator._get_claim_type(claim)
            assert claim_type == "structure", f"Claim '{claim}' should be 'structure' type, got '{claim_type}'"

    def test_detect_works_claim_type(self):
        """Claims about 'works' should map to 'execution' claim type."""
        works_claims = [
            "The function works",
            "It works correctly",
            "This is working",
        ]
        for claim in works_claims:
            claim_type = validator._get_claim_type(claim)
            assert claim_type == "execution", f"Claim '{claim}' should be 'execution' type, got '{claim_type}'"


class TestBackwardCompatibility:
    """Ensure implementation doesn't break existing behavior."""

    def test_claim_without_tools_is_blocked(self):
        """Claims without any tools should still be blocked."""
        response = "The function works"
        tools_used = []

        # Has claims, no observation tools - should require verification
        assert validator.has_claims(response)
        assert not validator.has_observation_tools(tools_used)

    def test_claim_with_observation_tools_is_allowed(self):
        """Claims with observation tools should be allowed."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("# test\n")
            test_file = f.name

        try:
            response = "The function works correctly"  # Actual claim pattern
            # Note: has_observation_tools expects list of tool names (strings), not dict objects
            tools_used = ["Read"]

            # Has claims AND observation tools - should be allowed
            assert validator.has_claims(response)
            assert validator.has_observation_tools(tools_used)

        finally:
            Path(test_file).unlink()

    def test_exempt_response_passes(self):
        """Exempt responses should pass without verification."""
        exempt_responses = [
            "Should I run the test?",
            "Acknowledged",
            "Let me check the file",
            "TODO: fix this later [UNVERIFIED]",
        ]

        for response in exempt_responses:
            assert validator.is_exempt(response), f"Response '{response}' should be exempt"

    def test_claims_are_detected(self):
        """Claim patterns should be detected."""
        claim_responses = [
            "The function works",
            "This is fixed",
            "The file is located at /tmp",
            "The error is a timeout",
        ]

        for response in claim_responses:
            assert validator.has_claims(response), f"Response '{response}' should contain claims"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
