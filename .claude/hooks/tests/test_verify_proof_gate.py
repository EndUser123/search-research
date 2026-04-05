#!/usr/bin/env python3
"""Tests for TDD VERIFY execution proof enforcement."""

import re
import sys
from pathlib import Path

# Add hooks directory to path
hooks_dir = Path(__file__).resolve().parent.parent
if str(hooks_dir) not in sys.path:
    sys.path.insert(0, str(hooks_dir))


class TestVerifyProofGate:
    """Test suite for VERIFY phase execution proof enforcement."""

    # Dry-run patterns that indicate fake verification
    DRY_RUN_PATTERNS = [
        r"--dry-run",
        r"--dry\s+run",
        r"--check",
        r"--simulate",
        r"mock",
        r"stub\s+(?:test|verification)",
    ]

    # Verification claim patterns
    VERIFICATION_CLAIM_PATTERNS = [
        r"verified",
        r"checked",
        r"confirmed",
        r"working",
        r"passes?\s+(?:tests|validation)",
    ]

    # Tool output fingerprints
    TOOL_OUTPUT_FINGERPRINTS = {
        "ruff": r"ruff check|```\[\s\S\]*?ruff",
        "mypy": r"mypy|\"errors\":\s*\[\]",
        "bandit": r"bandit|severity",
        "pytest": r"pytest|PASSED|FAILED",
    }

    def test_verify_blocks_dry_run_claims(self):
        """VERIFY gate blocks when dry-run patterns detected without actual proof."""
        # Response with dry-run claim but no tool output
        response = "I verified the code with --dry-run and everything looks good."

        # Check for dry-run patterns
        has_dry_run = any(re.search(p, response, re.I) for p in self.DRY_RUN_PATTERNS)
        assert has_dry_run, "Should detect dry-run pattern"

        # Check for tool outputs
        tool_outputs_found = []
        for tool, pattern in self.TOOL_OUTPUT_FINGERPRINTS.items():
            if re.search(pattern, response, re.I | re.M):
                tool_outputs_found.append(tool)

        assert len(tool_outputs_found) < 2, "Should have insufficient tool outputs"

    def test_verify_blocks_claim_without_proof(self):
        """VERIFY gate blocks when 'verified' claimed without tool output."""
        # Response with verification claim but no proof
        response = "The code has been verified and is working correctly."

        # Check for verification claims
        has_claims = any(re.search(p, response, re.I) for p in self.VERIFICATION_CLAIM_PATTERNS)
        assert has_claims, "Should detect verification claim"

        # Check for tool outputs
        tool_outputs_found = []
        for tool, pattern in self.TOOL_OUTPUT_FINGERPRINTS.items():
            if re.search(pattern, response, re.I | re.M):
                tool_outputs_found.append(tool)

        assert len(tool_outputs_found) == 0, "Should have no tool outputs"

    def test_verify_allows_with_actual_tool_output(self):
        """VERIFY gate allows when actual tool output is present."""
        # Response with actual tool outputs
        response = """
I ran verification tools:
```bash
$ ruff check src/
All checks passed!
```
```bash
$ mypy src/
Success: no issues found in 5 source files
```
"""

        # Check for tool outputs
        tool_outputs_found = []
        for tool, pattern in self.TOOL_OUTPUT_FINGERPRINTS.items():
            if re.search(pattern, response, re.I | re.M):
                tool_outputs_found.append(tool)

        assert len(tool_outputs_found) >= 2, "Should have 2+ tool outputs"

    def test_verify_requires_minimum_two_tools(self):
        """VERIFY gate requires at least 2 different tool outputs."""
        # Response with only one tool output
        response = "$ pytest tests/\nPASSED"

        # Check for tool outputs
        tool_outputs_found = []
        for tool, pattern in self.TOOL_OUTPUT_FINGERPRINTS.items():
            if re.search(pattern, response, re.I | re.M):
                tool_outputs_found.append(tool)

        assert len(tool_outputs_found) == 1, "Should have only 1 tool output (insufficient)"
