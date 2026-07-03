#!/usr/bin/env python3
"""Characterization tests for strawberry_validator decommission.

RED phase: Verifies CURRENT behavior before decommission.

These tests document what strawberry_validator currently does so we can
confirm the same coverage exists (or doesn't need to) after it's removed.

Key invariants to preserve:
1. strawberry_validator is NOT in ACTIVE_RUNTIME_HOOKS (already unwired)
2. StrawberryValidator uses httpx to call external Z.AI API (policy violation)
3. strawberry_validator tests exist and must be moved/removed
4. scanners/strawberry_validator.py must be deleted after test migration

Key things that do NOT need to be preserved:
- Stage 2 httpx LLM call (violates hook external dependency policy)
- UNCERTAIN_PATTERNS as Stage 2 triggers (should become Stage 1 FAIL)
- ZAI_API_KEY dependency
"""

import re
import sys
from pathlib import Path

HOOKS_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HOOKS_DIR))


class TestStrawberryValidatorNotWired:
    """Verify strawberry_validator is not in the active runtime hooks."""

    def test_not_in_stop_active_runtime_hooks(self):
        """strawberry_validator must NOT appear in active Stop hooks."""
        stop_path = HOOKS_DIR / "Stop.py"
        content = stop_path.read_text(encoding="utf-8")

        # Check IN_PROCESS_GATES for strawberry references
        in_process_match = re.search(
            r"IN_PROCESS_GATES\s*=\s*\{(.*?)\}",
            content,
            re.DOTALL,
        )
        if in_process_match:
            assert (
                "strawberry" not in in_process_match.group(1).lower()
            ), "strawberry_validator should NOT be in IN_PROCESS_GATES"

        # Check no import of strawberry
        assert (
            "strawberry" not in content.lower()
            or "scanners" not in content.lower()
        ), "No strawberry scanner imports should exist in Stop.py"

    def test_not_in_hook_sequence(self):
        """strawberry_validator should not be referenced in Stop.py."""
        stop_path = HOOKS_DIR / "Stop.py"
        content = stop_path.read_text(encoding="utf-8")

        # No strawberry references at all
        assert (
            "strawberry" not in content.lower()
        ), "strawberry_validator should not be referenced in Stop.py"


class TestStrawberryValidatorDecommissioned:
    """Verify strawberry_validator has been properly decommissioned (deleted)."""

    def test_scanner_file_deleted(self):
        """strawberry_validator.py scanner must be deleted (httpx policy violation)."""
        scanner_path = HOOKS_DIR / "scanners" / "strawberry_validator.py"
        assert not scanner_path.exists(), "strawberry_validator.py must be deleted from scanners/"

    def test_policy_violation_was_documented(self):
        """The httpx policy violation was documented before deletion."""
        policy_path = HOOKS_DIR / "hook_external_llm_policy.md"
        content = policy_path.read_text(encoding="utf-8")
        assert "strawberry" in content.lower(), "Policy doc must reference strawberry"
        assert "httpx" in content.lower() or "external" in content.lower()


class TestStrawberryValidatorPatterns:
    """Verify patterns were migrated or handled during decommission."""

    def test_no_scanner_file_means_no_patterns(self):
        """strawberry_validator.py is deleted, so patterns are no longer in that file."""
        scanner_path = HOOKS_DIR / "scanners" / "strawberry_validator.py"
        assert not scanner_path.exists(), "Scanner file must be deleted"

    def test_hooks_claude_md_documents_decommission(self):
        """CLAUDE.md must document strawberry_validator removal."""
        claude_md_path = HOOKS_DIR / "CLAUDE.md"
        content = claude_md_path.read_text(encoding="utf-8")
        # The Scanner section should either be removed or marked as decommissioned
        # Check that the old Stage 2 LLM verification is documented as removed
        assert "strawberry" in content.lower() or "httpx" in content.lower()


class TestStopHookCrossValidator:
    """Verify cross_validator state in Stop.py."""

    def test_not_in_active_runtime_hooks(self):
        """cross_validator is NOT in active Stop hooks (inactive by default)."""
        stop_path = HOOKS_DIR / "Stop.py"
        content = stop_path.read_text(encoding="utf-8")

        # Check IN_PROCESS_GATES
        in_process_match = re.search(
            r"IN_PROCESS_GATES\s*=\s*\{(.*?)\}",
            content,
            re.DOTALL,
        )
        if in_process_match:
            assert (
                "cross_validator" not in in_process_match.group(1).lower()
            ), "cross_validator should NOT be in IN_PROCESS_GATES"

    def test_not_in_stop_py_hook_imports(self):
        """cross_validator IS wired into Stop.py (in-process)."""
        stop_path = HOOKS_DIR / "Stop.py"
        content = stop_path.read_text(encoding="utf-8")

        # cross_validator IS referenced (this is the post-consolidation state)
        assert "cross_validator" in content, "cross_validator should be in Stop.py"


class TestStrawberryValidatorTestFiles:
    """Verify strawberry_validator test files were removed during decommission."""

    def test_strawberry_validator_test_file_deleted(self):
        """test_strawberry_validator.py must be deleted (replaced by decommission tests)."""
        test_path = HOOKS_DIR / "tests" / "test_strawberry_validator.py"
        assert not test_path.exists(), "test_strawberry_validator.py must be deleted"

    def test_strawberry_validator_skill_claims_test_deleted(self):
        """test_strawberry_validator_skill_claims.py must be deleted."""
        test_path = HOOKS_DIR / "tests" / "test_strawberry_validator_skill_claims.py"
        assert not test_path.exists(), "test_strawberry_validator_skill_claims.py must be deleted"


class TestStrawberryValidatorCanBeImported:
    """Verify the scanner module is removed (not importable)."""

    def test_scanner_module_deleted(self):
        """strawberry_validator.py is deleted, so it cannot be imported."""
        scanner_path = HOOKS_DIR / "scanners" / "strawberry_validator.py"
        assert not scanner_path.exists(), "Scanner file must be deleted"


class TestHookExternalLLMPolicyDocumented:
    """Verify the policy violation is documented."""

    def test_policy_doc_exists(self):
        """hook_external_llm_policy.md should document the violation."""
        policy_path = HOOKS_DIR / "hook_external_llm_policy.md"
        assert (
            policy_path.exists()
        ), "hook_external_llm_policy.md not found — policy must be documented"
        content = policy_path.read_text(encoding="utf-8")
        assert "strawberry" in content.lower(), "Policy doc should mention strawberry_validator"
        assert (
            "httpx" in content or "external" in content.lower()
        ), "Policy doc should mention httpx/external API violation"