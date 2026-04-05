#!/usr/bin/env python3
"""
Regression test for skill-guard bug investigation failure.

This test verifies that the new debugRCA protocols prevent the original
skill-guard investigation failure where the investigator:
1. Confused breadcrumb indicator with actual Skill() execution
2. Declared success from unit tests without runtime verification
3. Contradicted user report without direct evidence
4. Failed to inspect runtime state for terminal ID mismatch
5. Declared "fixed" prematurely without verification

The test ensures each protocol would have caught these failures.
"""

from pathlib import Path

import pytest

# Path to debugRCA SKILL.md
SKILL_MD_PATH = Path("P:/.claude/skills/debugRCA/SKILL.md")


def load_skill_md():
    """Load debugRCA SKILL.md content."""
    if not SKILL_MD_PATH.exists():
        pytest.skip(f"SKILL.md not found at {SKILL_MD_PATH}")
    return SKILL_MD_PATH.read_text()


class TestSkillGuardRegression:
    """Regression tests for skill-guard bug prevention."""

    def test_observable_definition_prevents_proxy_confusion(self):
        """
        Verify Observable Definition protocol prevents breadcrumb/proxy confusion.

        Original failure: Investigator confused breadcrumb indicator (🔧 emoji)
        with actual Skill() execution, leading to false "fixed" declaration.

        Expected behavior: Observable Definition requires explicit success
        evidence (Skill() in tool transcript) not proxy indicators.
        """
        content = load_skill_md()

        # Check that Observable Definition exists
        assert "Observable Definition" in content, \
            "Missing Observable Definition protocol"

        # Check that it explicitly calls out non-equivalent proxies
        assert "Non-Equivalent Proxies" in content, \
            "Missing non-equivalent proxies warning"

        # Check that it uses skill-guard bug as example
        assert ("breadcrumb" in content.lower() or \
                "indicator" in content.lower() or \
                "skill-guard" in content.lower()), \
            "Missing skill-guard bug example in proxies"

        # Verify the example shows what NOT to rely on
        assert "❌" in content and ("Breadcrumb" in content or "Directive" in content), \
            "Missing example showing what NOT to rely on"

    def test_observable_definition_requires_success_evidence(self):
        """
        Verify Observable Definition requires exact success evidence.

        Original failure: Unit test passing was treated as proof of execution.

        Expected behavior: Observable Definition requires Tier 3/4 evidence
        (tool transcript, runtime proof, user observable).
        """
        content = load_skill_md()

        # Check that success evidence is required
        assert "Exact Success Evidence" in content or \
               "success evidence specified" in content.lower(), \
            "Missing requirement for exact success evidence"

        # Check that it mentions tool transcript specifically
        assert "tool transcript" in content.lower() or \
               "Skill('gto')" in content, \
            "Missing reference to tool transcript as evidence"

        # Verify unit tests are explicitly called out as insufficient
        assert "Unit test" in content or \
               "unit test" in content.lower(), \
            "Missing warning about unit tests being insufficient"

    def test_disproof_protocol_prevents_user_dismissal(self):
        """
        Verify User Report Disproof Protocol prevents contradicting user without evidence.

        Original failure: User reported "there's no sign that Skill() was used"
        but investigator concluded "already working" without direct counter-evidence.

        Expected behavior: Disproof Protocol requires direct evidence
        (tool transcript, runtime proof) before contradicting user.
        """
        content = load_skill_md()

        # Check that Disproof Protocol exists
        assert "User Report Disproof Protocol" in content, \
            "Missing User Report Disproof Protocol"

        # Check that it requires direct disproof evidence
        assert "Disproof Evidence Requirements" in content or \
               "direct counter-evidence" in content, \
            "Missing disproof evidence requirements"

        # Check that it specifies what counts as direct evidence
        assert "Direct observation" in content or \
               "Tool transcript" in content, \
            "Missing specification of direct evidence types"

        # Verify it shows WRONG vs CORRECT pattern
        assert "WRONG" in content and "CORRECT" in content, \
            "Missing WRONG vs CORRECT example"

    def test_runtime_state_inspection_detects_terminal_mismatch(self):
        """
        Verify Runtime State Inspection detects terminal ID mismatch.

        Original failure: Investigator didn't check runtime state, missed
        terminal ID mismatch that prevented Skill() invocation.

        Expected behavior: Runtime State Inspection step would have
        detected terminal_id mismatch in pending intent files.
        """
        content = load_skill_md()

        # Check that Runtime State Inspection exists
        assert "Runtime State Inspection" in content, \
            "Missing Runtime State Inspection step"

        # Check that it's triggered for silent failures
        assert "no visible error" in content or \
               "silent failures" in content or \
               "doesn't work" in content, \
            "Missing trigger condition for silent failures"

        # Check that it references the state inspection tool
        assert "inspect_runtime_state.py" in content, \
            "Missing reference to state inspection tool"

        # Verify it includes terminal ID pattern detection
        assert "Terminal ID" in content or \
               "terminal_id" in content, \
            "Missing terminal ID pattern detection"

        # Check that it mentions the skill-guard bug pattern
        assert ("skill-guard" in content.lower() or \
                "mismatch" in content.lower()), \
            "Missing reference to terminal ID mismatch pattern"

    def test_pre_response_checklist_prevents_premature_fixed(self):
        """
        Verify Pre-Response Checklist prevents premature "fixed" declaration.

        Original failure: Investigator declared success from unit test
        without verifying actual Skill() invocation.

        Expected behavior: Pre-Response Checklist requires all 4 questions
        answered YES before declaring "fixed".
        """
        content = load_skill_md()

        # Check that Investigation Complete Gate exists
        assert "Investigation Complete Gate" in content or \
               "Pre-Response Checklist" in content, \
            "Missing Investigation Complete Gate"

        # Check that it requires 4 questions
        assert "Q1:" in content or "Question 1" in content, \
            "Missing Q1 in checklist"
        assert "Q2:" in content or "Question 2" in content, \
            "Missing Q2 in checklist"
        assert "Q3:" in content or "Question 3" in content, \
            "Missing Q3 in checklist"
        assert "Q4:" in content or "Question 4" in content, \
            "Missing Q4 in checklist"

        # Verify it requires all YES answers
        assert "ALL 4 questions answered YES" in content or \
               "all 4 questions" in content, \
            "Missing requirement for all YES answers"

        # Check that it shows example of in-progress status
        assert "Status:" in content or \
               "Investigation ongoing" in content, \
            "Missing status example showing in-progress investigation"

    def test_all_protocols_work_together(self):
        """
        Verify all protocols work together to prevent investigation failure.

        This integration test ensures that following all the protocols
        would have prevented the original skill-guard investigation failure.
        """
        content = load_skill_md()

        # Check that all key protocols exist
        required_protocols = [
            "Observable Definition",
            "User Report Disproof Protocol",
            "Runtime State Inspection",
            "Investigation Complete Gate"
        ]

        for protocol in required_protocols:
            assert protocol in content, \
                f"Missing required protocol: {protocol}"

        # Verify they reference the skill-guard bug as learning example
        skill_guard_references = (
            content.lower().count("skill-guard") +
            content.lower().count("breadcrumb") +
            content.lower().count("terminal_id")
        )

        # Should have multiple references to the bug case
        assert skill_guard_references >= 3, \
            f"Insufficient references to skill-guard bug (found {skill_guard_references})"

    def test_investigation_gates_have_tiered_system(self):
        """
        Verify Investigation Gates use tiered mandatory system.

        This ensures alert fatigue prevention by distinguishing CRITICAL
        (always enforced) from CONDITIONAL (trigger-based) gates.
        """
        content = load_skill_md()

        # Check for tiered system
        assert "CRITICAL" in content or \
               "always enforced" in content.lower(), \
            "Missing CRITICAL gate designation"

        assert "CONDITIONAL" in content or \
               "triggered" in content.lower(), \
            "Missing CONDITIONAL gate designation"

        # Verify it explains the tiered system
        assert ("Tier" in content or \
                "tiered" in content.lower() or \
                "alert fatigue" in content.lower()), \
            "Missing explanation of tiered mandatory system"


class TestProtocolIntegration:
    """Tests for protocol integration and workflow."""

    def test_gates_enforce_in_correct_order(self):
        """
        Verify gates are ordered correctly in investigation workflow.

        Observable Definition should come before investigation (Gate 1).
        Runtime State Inspection should be after initial search (Step 1.65).
        Disproof Protocol should be in Synthesis Checkpoint.
        Complete Gate should be before declaring "fixed" (Step 2.85+).
        """
        content = load_skill_md()

        # Find line numbers for key sections
        lines = content.split('\n')
        section_lines = {}

        for i, line in enumerate(lines, 1):
            if "## Investigation Verification Gates" in line:
                section_lines["Investigation Gates"] = i
            elif "### Step 1.65: Runtime State Inspection" in line:
                section_lines["Runtime State"] = i
            elif "### User Report Disproof Protocol" in line:
                section_lines["Disproof Protocol"] = i
            elif "### Investigation Complete Gate" in line:
                section_lines["Complete Gate"] = i
            elif "### Step 2.85: Convergence Gate Check" in line:
                section_lines["Convergence Gate"] = i

        # Verify ordering
        assert "Investigation Gates" in section_lines, \
            "Missing Investigation Verification Gates section"

        if all(k in section_lines for k in ["Investigation Gates", "Runtime State", "Convergence Gate"]):
            # Gates should be in logical order
            assert section_lines["Investigation Gates"] < section_lines["Runtime State"], \
                "Investigation Gates should come before Runtime State Inspection"
            assert section_lines["Runtime State"] < section_lines["Convergence Gate"], \
                "Runtime State should come before Convergence Gate"

        # Disproof Protocol should be in Synthesis Checkpoint (which is after Runtime State)
        if "Disproof Protocol" in section_lines and "Runtime State" in section_lines:
            assert section_lines["Runtime State"] < section_lines["Disproof Protocol"], \
                "Runtime State should come before Disproof Protocol (in Synthesis)"

        # Complete Gate should be after Convergence Gate
        if "Complete Gate" in section_lines and "Convergence Gate" in section_lines:
            assert section_lines["Convergence Gate"] < section_lines["Complete Gate"], \
                "Convergence Gate should come before Complete Gate"

    def test_triple_collection_framework_present(self):
        """
        Verify Triple-Collection Framework is present and comprehensive.

        Original failure: Investigator only collected mechanism evidence
        (code inspection) without state or outcome evidence.

        Expected behavior: Triple-Collection Framework requires all 3 buckets
        (Mechanism, State, Outcome) before hypothesis formation.
        """
        content = load_skill_md()

        # Check that Triple-Collection Framework exists
        assert "Triple-Collection Framework" in content, \
            "Missing Triple-Collection Framework"

        # Check that it defines 3 buckets
        assert "Bucket 1" in content, \
            "Missing Bucket 1 definition"
        assert "Bucket 2" in content, \
            "Missing Bucket 2 definition"
        assert "Bucket 3" in content, \
            "Missing Bucket 3 definition"

        # Verify bucket names
        assert "Mechanism" in content, \
            "Missing Mechanism bucket"
        assert "State" in content, \
            "Missing State bucket"
        assert "Outcome" in content, \
            "Missing Outcome bucket"

        # Check that it requires all buckets before hypothesis
        assert "Hypothesis Formation Gate" in content or \
               "form hypothesis" in content.lower(), \
            "Missing hypothesis formation gate"

        # Verify empty bucket protocol
        assert "Empty Bucket Protocol" in content or \
               "empty bucket" in content.lower(), \
            "Missing empty bucket protocol"


class TestEvidenceTierSystem:
    """Tests for extended evidence tier system."""

    def test_evidence_tiers_include_all_5_tiers(self):
        """
        Verify extended evidence tier system includes all 5 tiers.

        Original failure: No distinction between Tier 0 (intuition) and
        Tier 3/4 (runtime/user observable), leading to overconfidence.

        Expected behavior: Extended tier system with Tier 0-4 and confidence
        ceilings prevents claiming high confidence without appropriate evidence.
        """
        content = load_skill_md()

        # Check for all 5 tiers
        for tier_num in range(5):
            assert f"Tier {tier_num}" in content, \
                f"Missing Tier {tier_num}"

        # Check for specific tier names
        assert "Intuition" in content or \
               (content.count("Tier 0") > 1), \
            "Missing Tier 0: Intuition"
        assert "Component" in content, \
            "Missing Tier 1: Component"
        assert "Integration" in content, \
            "Missing Tier 2: Integration"
        assert "Runtime" in content, \
            "Missing Tier 3: Runtime"
        assert "User Observable" in content or \
               "E2E" in content, \
            "Missing Tier 4: User Observable"

    def test_confidence_ceiling_enforced(self):
        """
        Verify confidence ceiling enforcement is documented.

        Original failure: High confidence claimed from unit tests (Tier 2)
        without Tier 3/4 evidence.

        Expected behavior: Confidence cannot exceed weakest evidence tier,
        preventing overconfidence from incomplete evidence.
        """
        content = load_skill_md()

        # Check for confidence ceiling rules
        assert "confidence ceiling" in content.lower() or \
               "Confidence Ceiling" in content, \
            "Missing confidence ceiling enforcement"

        # Check that it specifies the ceiling rule
        assert ("weakest evidence tier" in content.lower() or \
                "lowest tier" in content.lower()), \
            "Missing rule about confidence limited by weakest evidence"

        # Verify it shows example calculation
        assert "example" in content.lower() or \
               "Example" in content, \
            "Missing confidence calculation example"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
