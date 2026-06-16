#!/usr/bin/env python3
"""
Automated tests for debugRCA protocol compliance.

Verifies that required sections and content exist in debugRCA SKILL.md
to ensure investigation protocols are properly documented.
"""

import re
from pathlib import Path

import pytest

# Path to debugRCA SKILL.md
SKILL_MD_PATH = Path("P:/.claude/skills/debugRCA/SKILL.md")


def load_skill_md():
    """Load debugRCA SKILL.md content."""
    if not SKILL_MD_PATH.exists():
        pytest.skip(f"SKILL.md not found at {SKILL_MD_PATH}")
    return SKILL_MD_PATH.read_text()


class TestObservableDefinition:
    """Tests for Gate 1A: Observable Definition protocol."""

    def test_observable_definition_section_exists(self):
        """Verify Investigation Verification Gates section exists."""
        content = load_skill_md()
        assert "## Investigation Verification Gates" in content, \
            "Missing 'Investigation Verification Gates' section"

    def test_observable_definition_template_exists(self):
        """Verify Observable Definition template is present."""
        content = load_skill_md()
        assert "Gate 1: Pre-Investigation" in content, \
            "Missing 'Gate 1: Pre-Investigation'"
        assert "Observable Definition" in content, \
            "Missing 'Observable Definition'"

    def test_observable_definition_has_checklist(self):
        """Verify Observable Definition has required checklist items."""
        content = load_skill_md()
        # Check for the three required checklist items
        assert "Expected observable defined" in content, \
            "Missing 'Expected observable defined' checklist item"
        assert "Non-equivalent proxies listed" in content, \
            "Missing 'Non-equivalent proxies listed' checklist item"
        assert "Exact success evidence specified" in content, \
            "Missing 'Exact success evidence specified' checklist item"

    def test_observable_definition_has_examples(self):
        """Verify Observable Definition includes examples from skill-guard bug."""
        content = load_skill_md()
        # Should reference the skill-guard bug example
        assert "Skill('gto')" in content or "skill-guard" in content, \
            "Missing examples from skill-guard bug"

    def test_observable_definition_has_red_flags(self):
        """Verify Observable Definition includes red flag phrases."""
        content = load_skill_md()
        assert "Red Flag Phrases" in content, \
            "Missing 'Red Flag Phrases' section"
        assert "Tests pass" in content or "Directive was injected" in content, \
            "Missing red flag examples"

    def test_ambiguity_resolution_gate_exists(self):
        """Verify Gate 1B: Ambiguity Resolution exists."""
        content = load_skill_md()
        assert "Gate 1B: Ambiguity Resolution" in content or \
               "CONDITIONAL GATES" in content, \
            "Missing Gate 1B: Ambiguity Resolution"

    def test_ambiguity_protocol_has_clarification_questions(self):
        """Verify Ambiguity Resolution includes clarification protocol."""
        content = load_skill_md()
        assert "Clarification Protocol" in content or \
               "clarification questions" in content, \
            "Missing clarification protocol for ambiguous reports"


class TestUserReportDisproof:
    """Tests for User Report Disproof Protocol."""

    def test_disproof_protocol_section_exists(self):
        """Verify User Report Disproof Protocol section exists."""
        content = load_skill_md()
        assert "User Report Disproof Protocol" in content, \
            "Missing 'User Report Disproof Protocol' section"

    def test_disproof_protocol_in_synthesis_checkpoint(self):
        """Verify Disproof Protocol is in Synthesis Checkpoint section."""
        content = load_skill_md()
        # Find "## Synthesis Checkpoint" and check if Disproof Protocol appears after it
        synthesis_idx = content.find("## Synthesis Checkpoint")
        assert synthesis_idx != -1, "Synthesis Checkpoint section not found"

        # Check if Disproof Protocol appears after Synthesis Checkpoint header
        content_after_synthesis = content[synthesis_idx:]
        assert "User Report Disproof Protocol" in content_after_synthesis, \
            "Disproof Protocol not in Synthesis Checkpoint"

    def test_disproof_protocol_has_wrong_correct_examples(self):
        """Verify Disproof Protocol includes WRONG vs CORRECT examples."""
        content = load_skill_md()
        # Check for example comparison
        assert "WRONG" in content and "CORRECT" in content, \
            "Missing WRONG vs CORRECT examples"

    def test_disproof_protocol_has_evidence_requirements(self):
        """Verify Disproof Protocol specifies evidence requirements."""
        content = load_skill_md()
        assert "Disproof Evidence Requirements" in content or \
               "evidence requirements" in content, \
            "Missing disproof evidence requirements"

    def test_disproof_protocol_has_enforcement_checklist(self):
        """Verify Disproof Protocol includes enforcement gate checklist."""
        content = load_skill_md()
        assert "Enforcement Gate Checklist" in content or \
               "enforcement checklist" in content, \
            "Missing enforcement gate checklist"


class TestPreResponseChecklist:
    """Tests for Pre-Response Checklist (Investigation Complete Gate)."""

    def test_complete_gate_section_exists(self):
        """Verify Investigation Complete Gate section exists."""
        content = load_skill_md()
        assert "Investigation Complete Gate" in content, \
            "Missing 'Investigation Complete Gate' section"

    def test_complete_gate_has_4_questions(self):
        """Verify Pre-Response Checklist has all 4 required questions."""
        content = load_skill_md()
        # Should have 4 questions (Q1-Q4)
        assert "Q1:" in content or "Question 1" in content, \
            "Missing Q1 in checklist"
        assert "Q2:" in content or "Question 2" in content, \
            "Missing Q2 in checklist"
        assert "Q3:" in content or "Question 3" in content, \
            "Missing Q3 in checklist"
        assert "Q4:" in content or "Question 4" in content, \
            "Missing Q4 in checklist"

    def test_complete_gate_has_evidence_template(self):
        """Verify Complete Gate includes evidence collection template."""
        content = load_skill_md()
        assert "Evidence Template" in content or \
               "Investigation Evidence Summary" in content, \
            "Missing evidence template"

    def test_complete_gate_requires_all_yes(self):
        """Verify Complete Gate requires all YES answers."""
        content = load_skill_md()
        assert "ALL 4 questions answered YES" in content or \
               "all 4 questions" in content, \
            "Missing requirement for all YES answers"

    def test_complete_gate_has_status_example(self):
        """Verify Complete Gate includes status example."""
        content = load_skill_md()
        assert "Status:" in content or "Investigation ongoing" in content, \
            "Missing status example showing in-progress investigation"


class TestRuntimeStateInspection:
    """Tests for Runtime State Inspection protocol."""

    def test_runtime_state_inspection_section_exists(self):
        """Verify Runtime State Inspection step exists."""
        content = load_skill_md()
        assert "Step 1.65: Runtime State Inspection" in content, \
            "Missing 'Step 1.65: Runtime State Inspection'"

    def test_runtime_state_inspection_has_trigger_conditions(self):
        """Verify Runtime State Inspection specifies trigger conditions."""
        content = load_skill_md()
        assert "Trigger Conditions" in content or \
               "no visible error" in content, \
            "Missing trigger conditions for silent failures"

    def test_runtime_state_inspection_references_tool(self):
        """Verify Runtime State Inspection references Python tool."""
        content = load_skill_md()
        assert "inspect_runtime_state.py" in content, \
            "Missing reference to inspect_runtime_state.py tool"

    def test_runtime_state_inspection_has_error_handling(self):
        """Verify Runtime State Inspection includes error handling."""
        content = load_skill_md()
        assert "error handling" in content or \
               "Missing files" in content or \
               "graceful degradation" in content, \
            "Missing error handling for missing/corrupted files"

    def test_runtime_state_inspection_has_analysis_patterns(self):
        """Verify Runtime State Inspection includes state analysis patterns."""
        content = load_skill_md()
        assert "Pattern" in content or \
               "Terminal ID" in content or \
               "Stale state" in content, \
            "Missing state analysis patterns"


class TestTripleCollectionFramework:
    """Tests for Triple-Collection Framework (Action Graph enhancement)."""

    def test_triple_collection_section_exists(self):
        """Verify Triple-Collection Framework section exists."""
        content = load_skill_md()
        assert "Triple-Collection Framework" in content, \
            "Missing 'Triple-Collection Framework'"

    def test_triple_collection_has_3_buckets(self):
        """Verify Triple-Collection Framework specifies 3 buckets."""
        content = load_skill_md()
        # Check for 3 buckets: Mechanism, State, Outcome
        assert "Bucket 1" in content and "Mechanism" in content, \
            "Missing Bucket 1: Mechanism"
        assert "Bucket 2" in content and "State" in content, \
            "Missing Bucket 2: State"
        assert "Bucket 3" in content and "Outcome" in content, \
            "Missing Bucket 3: Outcome"

    def test_triple_collection_has_bucket_mapping_table(self):
        """Verify Triple-Collection Framework includes bucket mapping table."""
        content = load_skill_md()
        assert "bucket mapping" in content or \
               "Bucket Mapping" in content, \
            "Missing bucket mapping table"

    def test_triple_collection_has_empty_bucket_protocol(self):
        """Verify Triple-Collection Framework includes empty bucket protocol."""
        content = load_skill_md()
        assert "Empty Bucket Protocol" in content or \
               "empty bucket" in content, \
            "Missing empty bucket protocol"

    def test_triple_collection_has_confidence_penalty(self):
        """Verify Triple-Collection Framework includes confidence penalty."""
        content = load_skill_md()
        assert "confidence penalty" in content or \
               "60%" in content or \
               "40%" in content, \
            "Missing confidence penalty for empty buckets"


class TestExtendedEvidenceTiers:
    """Tests for Extended Evidence Tier System."""

    def test_tier_0_added(self):
        """Verify Tier 0 (Intuition) was added."""
        content = load_skill_md()
        # Check either SKILL.md or verification_tiers.md
        assert "Tier 0" in content or \
               "Intuition" in content, \
            "Missing Tier 0 (Intuition)"

    def test_tier_4_added(self):
        """Verify Tier 4 (User Observable) was added."""
        content = load_skill_md()
        # Check either SKILL.md or verification_tiers.md
        assert "Tier 4" in content or \
               "User Observable" in content, \
            "Missing Tier 4 (User Observable)"

    def test_existing_tier_names_preserved(self):
        """Verify existing Tier 1-3 names were preserved."""
        content = load_skill_md()
        # Should still have Component/Integration/Runtime names
        assert "Component" in content, \
            "Missing Tier 1: Component"
        assert "Integration" in content, \
            "Missing Tier 2: Integration"
        assert "Runtime" in content, \
            "Missing Tier 3: Runtime"

    def test_confidence_ceiling_enforcement(self):
        """Verify confidence ceiling enforcement rules documented."""
        content = load_skill_md()
        assert "confidence ceiling" in content or \
               "Confidence Ceiling" in content, \
            "Missing confidence ceiling enforcement"

    def test_skill_md_references_verification_tiers(self):
        """Verify SKILL.md references verification_tiers.md."""
        content = load_skill_md()
        assert "verification_tiers.md" in content, \
            "SKILL.md should reference verification_tiers.md"


class TestMarkdownSyntax:
    """Tests for markdown syntax validity."""

    def test_no_broken_markdown_links(self):
        """Verify no broken markdown section links."""
        content = load_skill_md()

        # Find all section references like {#section-name}
        section_refs = re.findall(r'\{#([a-z0-9-]+)\}', content)

        # Find all section headers
        section_defs = re.findall(r'^#+\s+(.+)\s*\{#([a-z0-9-]+)\}', content, re.MULTILINE)

        # Extract section IDs from definitions
        defined_ids = {match[1] for match in section_defs}

        # Check if all references have definitions
        broken_refs = set(section_refs) - defined_ids

        if broken_refs:
            pytest.fail(
                f"Broken markdown section references: {', '.join(broken_refs)}"
            )

    def test_markdown_headers_format(self):
        """Verify markdown headers use correct format."""
        content = load_skill_md()
        lines = content.split('\n')

        for i, line in enumerate(lines, 1):
            # Check for headers (lines starting with #)
            if line.startswith('#'):
                # Should have space after # symbols
                if re.match(r'^#+[^#\s]', line):
                    pytest.fail(f"Line {i}: Malformed header (missing space after #): {line}")

    def test_code_blocks_closed(self):
        """Verify all code blocks are properly closed."""
        content = load_skill_md()
        lines = content.split('\n')

        in_code_block = False
        for i, line in enumerate(lines, 1):
            if line.strip().startswith('```'):
                # In standard markdown, ``` closes any code block
                in_code_block = not in_code_block

        # After processing all lines, should not be in a code block
        if in_code_block:
            pytest.fail("Unclosed code block detected (odd number of ``` fences)")


class TestToolFileExists:
    """Tests for runtime state inspection tool file."""

    def test_inspect_runtime_state_tool_exists(self):
        """Verify inspect_runtime_state.py tool file exists."""
        tool_path = Path("P:/.claude/skills/debugRCA/tools/inspect_runtime_state.py")
        assert tool_path.exists(), \
            f"Tool file not found: {tool_path}"

    def test_inspect_runtime_state_importable(self):
        """Verify inspect_runtime_state.py can be imported."""
        tool_path = Path("P:/.claude/skills/debugRCA/tools/inspect_runtime_state.py")
        if not tool_path.exists():
            pytest.skip("Tool file does not exist")

        # Try to import the module
        import sys
        sys.path.insert(0, str(tool_path.parent))

        try:
            import inspect_runtime_state
            assert hasattr(inspect_runtime_state, 'inspect_runtime_state'), \
                "Missing inspect_runtime_state() function"
        except ImportError as e:
            pytest.fail(f"Failed to import inspect_runtime_state: {e}")

    def test_inspect_runtime_state_has_main(self):
        """Verify inspect_runtime_state.py has main() entry point."""
        tool_path = Path("P:/.claude/skills/debugRCA/tools/inspect_runtime_state.py")
        if not tool_path.exists():
            pytest.skip("Tool file does not exist")

        content = tool_path.read_text()

        assert "def main()" in content, \
            "Missing main() function in inspect_runtime_state.py"
        assert 'if __name__ == "__main__"' in content, \
            "Missing main entry point guard"


class TestConfidenceTagRequirements:
    """Tests for v2.6 confidence tag requirement."""

    def test_confidence_tag_section_exists(self):
        """Verify confidence tag requirement section exists."""
        content = load_skill_md()
        assert "Confidence Tag Requirement (MANDATORY in v2.6)" in content, \
            "Missing 'Confidence Tag Requirement (MANDATORY in v2.6)' section"

    def test_confidence_tag_format_defined(self):
        """Verify confidence tag format is defined."""
        content = load_skill_md()
        assert "(Tier [0-4], [0-100]%)" in content, \
            "Missing confidence tag format specification"
        assert "Tier 0" in content and "Tier 4" in content, \
            "Missing tier definitions (0-4)"

    def test_confidence_tier_limits_defined(self):
        """Verify tier confidence limits are documented."""
        content = load_skill_md()
        # Check for tier ceiling rules
        assert "max 50% confidence" in content or "Tier 0" in content, \
            "Missing Tier 0 confidence limit"
        assert "max 95% confidence" in content or "Tier 4" in content, \
            "Missing Tier 4 confidence limit"

    def test_hypothesis_ranking_requires_confidence(self):
        """Verify hypothesis ranking template includes confidence column."""
        content = load_skill_md()
        # Check for updated hypothesis ranking template with confidence
        assert "Confidence" in content, \
            "Missing 'Confidence' column in hypothesis ranking template"
        assert "(Tier [0-4], [0-100]%)" in content, \
            "Missing confidence tag format in hypothesis template"

    def test_output_format_requires_confidence(self):
        """Verify output format requires confidence tags."""
        content = load_skill_md()
        # Check for confidence requirements in output format
        assert "All hypothesis statements, conclusions, and claims MUST include confidence tags" in content, \
            "Missing confidence tag requirement in output format"
        assert 'No "root cause identified" below Tier 3' in content, \
            "Missing Tier 3 requirement for root cause claims"
        assert 'No "fixed/works" below Tier 4' in content, \
            "Missing Tier 4 requirement for fixed/working claims"


class TestDisconfirmationStepFormat:
    """Tests for v2.6 disconfirmation step format."""

    def test_disconfirmation_step_section_exists(self):
        """Verify disconfirmation step section exists."""
        content = load_skill_md()
        assert "Disconfirmation Step Format (REQUIRED in v2.6)" in content, \
            "Missing 'Disconfirmation Step Format (REQUIRED in v2.6)' section"

    def test_disconfirmation_template_exists(self):
        """Verify disconfirmation template is provided."""
        content = load_skill_md()
        assert "Disconfirming Evidence" in content, \
            "Missing 'Disconfirming Evidence' template"
        assert "Disconfirmation Check" in content, \
            "Missing 'Disconfirmation Check' template"
        assert "If this hypothesis were false, I would see" in content, \
            "Missing disconfirmation evidence format"
        assert "I checked" in content and "found" in content, \
            "Missing disconfirmation check format"

    def test_disconfirmation_result_format(self):
        """Verify disconfirmation result format is defined."""
        content = load_skill_md()
        assert "SUPPORTED / REFUTED / INCONCLUSIVE" in content, \
            "Missing disconfirmation result format"

    def test_disconfirmation_prevents_lock_in(self):
        """Verify disconfirmation purpose is documented."""
        content = load_skill_md()
        assert "Prevents lock-in" in content or "plausible-sounding but unverified" in content, \
            "Missing disconnection step purpose documentation"

    def test_disconfirmation_in_output_format(self):
        """Verify disconnection steps are required in output format."""
        content = load_skill_md()
        # Check for disconfirmation section in output format
        assert "Disconfirmation Steps (REQUIRED in v2.6)" in content, \
            "Missing disconfirmation steps in output format section"


class TestSpecVsObservedSeparation:
    """Tests for v2.6 Spec vs Observed two-column requirement."""

    def test_spec_vs_observed_section_exists(self):
        """Verify Spec vs Observed separation section exists."""
        content = load_skill_md()
        assert "Spec vs Observed Separation (REQUIRED in v2.6)" in content, \
            "Missing 'Spec vs Observed Separation (REQUIRED in v2.6)' section"

    def test_two_column_format_exists(self):
        """Verify two-column format is defined."""
        content = load_skill_md()
        assert "Column A: Intended Architecture" in content, \
            "Missing 'Column A: Intended Architecture'"
        assert "Column B: Observed Behavior" in content, \
            "Missing 'Column B: Observed Behavior'"

    def test_source_separation_defined(self):
        """Verify source separation is documented."""
        content = load_skill_md()
        assert "docs, comments, design notes" in content, \
            "Missing Intended Architecture sources"
        assert "logs, state files, transcripts, tests" in content, \
            "Missing Observed Behavior sources"

    def test_docstring_driven_prevention(self):
        """Verify prevention of docstring-driven development is documented."""
        content = load_skill_md()
        assert "docstring-driven development" in content, \
            "Missing 'docstring-driven development' prevention"
        assert "Guards against assuming docstrings/comments reflect reality" in content, \
            "Missing purpose documentation"

    def test_forbidden_root_claims_from_spec_only(self):
        """Verify forbidden claims from spec-only are documented."""
        content = load_skill_md()
        assert "FORBIDDEN" in content and "citing ONLY Column A" in content, \
            "Missing forbidden rule for spec-only claims"
        assert "Column B evidence" in content and "behavioral claims" in content, \
            "Missing requirement for observed behavior evidence"

    def test_spec_vs_observed_example(self):
        """Verify example of Spec vs Observed separation is provided."""
        content = load_skill_md()
        assert "skill-guard bug" in content or "example" in content.lower(), \
            "Missing example of Spec vs Observed application"
        # Check for table structure
        assert "|" in content, \
            "Missing table format for Spec vs Observed example"


class TestSkillInvocationLogger:
    """Tests for Phase 2: Skill invocation logger and show_skill_invocations tool."""

    def test_skill_invocation_logger_hook_exists(self):
        """Verify skill invocation logger hook file exists."""
        hook_path = Path("P:/.claude/hooks/posttooluse/skill_invocation_logger_hook.py")
        assert hook_path.exists(), \
            "Missing skill_invocation_logger_hook.py"
        assert hook_path.is_file(), \
            "skill_invocation_logger_hook.py should be a file"

    def test_skill_invocation_logger_importable(self):
        """Verify skill invocation logger can be imported."""
        try:
            import sys
            hooks_dir = "P:/.claude/hooks"
            if hooks_dir not in sys.path:
                sys.path.insert(0, hooks_dir)

            from posttooluse.skill_invocation_logger_hook import SkillInvocationLoggerHook
            assert SkillInvocationLoggerHook is not None, \
                "Failed to import SkillInvocationLoggerHook"
        except ImportError as e:
            pytest.fail(f"Failed to import skill_invocation_logger_hook: {e}")

    def test_skill_invocation_logger_registered(self):
        """Verify skill invocation logger is registered in posttooluse package."""
        try:
            import sys
            hooks_dir = "P:/.claude/hooks/posttooluse"
            if hooks_dir not in sys.path:
                sys.path.insert(0, hooks_dir)

            # Check the __init__.py imports the hook
            init_path = Path("P:/.claude/hooks/posttooluse/__init__.py")
            init_content = init_path.read_text()
            assert "skill_invocation_logger_hook" in init_content, \
                "skill_invocation_logger_hook not imported in __init__.py"
            assert "SkillInvocationLoggerHook" in init_content, \
                "SkillInvocationLoggerHook not imported in __init__.py"

            # Check the hook is registered in create_registry()
            assert '"skill_invocation_logger"' in init_content, \
                "skill_invocation_logger not registered in create_registry()"
        except Exception as e:
            pytest.fail(f"Failed to verify hook registration: {e}")

    def test_skill_invocation_logger_has_tool_matcher(self):
        """Verify skill invocation logger only triggers on Skill tool."""
        try:
            import sys
            hooks_dir = "P:/.claude/hooks"
            if hooks_dir not in sys.path:
                sys.path.insert(0, hooks_dir)

            from posttooluse.skill_invocation_logger_hook import SkillInvocationLoggerHook

            hook = SkillInvocationLoggerHook()
            assert hook.tool_matcher == {"Skill"}, \
                "SkillInvocationLoggerHook should only match Skill tool"
        except ImportError as e:
            pytest.fail(f"Failed to import hook: {e}")

    def test_show_skill_invocations_tool_exists(self):
        """Verify show_skill_invocations tool file exists."""
        tool_path = Path("P:/.claude/skills/debugRCA/tools/show_skill_invocations.py")
        assert tool_path.exists(), \
            "Missing show_skill_invocations.py tool"
        assert tool_path.is_file(), \
            "show_skill_invocations.py should be a file"

    def test_show_skill_invocations_importable(self):
        """Verify show_skill_invocations tool can be imported."""
        try:
            import sys
            tools_dir = "P:/.claude/skills/debugRCA/tools"
            if tools_dir not in sys.path:
                sys.path.insert(0, tools_dir)

            from show_skill_invocations import main, show_recent_invocations
            assert callable(show_recent_invocations), \
                "show_recent_invocations should be callable"
            assert callable(main), \
                "main should be callable"
        except ImportError as e:
            pytest.fail(f"Failed to import show_skill_invocations: {e}")

    def test_show_skill_invocations_has_main_function(self):
        """Verify show_skill_invocations tool has main() function."""
        tool_path = Path("P:/.claude/skills/debugRCA/tools/show_skill_invocations.py")
        content = tool_path.read_text()

        assert "def main()" in content, \
            "Missing main() function in show_skill_invocations.py"
        assert 'if __name__ == "__main__"' in content, \
            "Missing main entry point guard"

    def test_show_skill_invocations_documented_in_skill(self):
        """Verify show_skill_invocations is documented in debugRCA SKILL.md."""
        content = load_skill_md()

        assert "show_skill_invocations" in content, \
            "show_skill_invocations not documented in SKILL.md"
        assert "Skill Invocation Verification" in content, \
            "Skill Invocation Verification section missing from SKILL.md"


class TestTier3SplitAndMaxClaimTable:
    """Tests for Phase 3: Tier 3a/3b split and max claim table."""

    def test_tier_3a_definition_exists(self):
        """Verify Tier 3a (runtime state only) is defined."""
        content = load_skill_md()
        assert "Tier 3a" in content, \
            "Missing Tier 3a definition"
        assert "Runtime state only" in content, \
            "Missing Tier 3a description (runtime state only)"

    def test_tier_3b_definition_exists(self):
        """Verify Tier 3b (runtime state + hook logs) is defined."""
        content = load_skill_md()
        assert "Tier 3b" in content, \
            "Missing Tier 3b definition"
        assert "hook logs" in content, \
            "Missing Tier 3b description (hook logs / tool-pipeline logs)"

    def test_max_claim_table_exists(self):
        """Verify max claim allowed per tier table exists."""
        content = load_skill_md()
        assert "Max Claim Allowed Per Tier" in content, \
            "Missing max claim table section"
        assert "Max Claim Allowed" in content, \
            "Missing max claim column in table"

    def test_tier_3a_confidence_ceiling(self):
        """Verify Tier 3a has 80% confidence ceiling."""
        content = load_skill_md()
        assert "Tier 3a" in content and "80%" in content, \
            "Tier 3a should have 80% confidence ceiling"

    def test_tier_3b_confidence_ceiling(self):
        """Verify Tier 3b has 85% confidence ceiling."""
        content = load_skill_md()
        assert "Tier 3b" in content and "85%" in content, \
            "Tier 3b should have 85% confidence ceiling"

    def test_tier_3a_vs_3b_distinction(self):
        """Verify Tier 3a and 3b are clearly distinguished."""
        content = load_skill_md()
        # Both should be mentioned with their distinctions
        assert "Tier 3a" in content and "Tier 3b" in content, \
            "Both Tier 3a and 3b should be defined"
        # Should have different confidence levels
        assert "Tier 3a" in content and "Tier 3b" in content, \
            "Tier 3a and 3b should have distinct definitions"

    def test_version_updated_to_2_9(self):
        """Verify version updated to v2.9.0 for Phase 3 changes."""
        content = load_skill_md()
        assert "v2.9.0" in content or "version: 2.9.0" in content, \
            "Version should be updated to v2.9.0 for Phase 3"

    def test_explicit_tier_3a_3b_requirement(self):
        """Verify requirement to explicitly state Tier 3a vs 3b."""
        content = load_skill_md()
        # Should mention the need to explicitly state 3a vs 3b
        assert "Tier 3a" in content or "Tier 3b" in content, \
            "Should require explicit Tier 3a vs 3b distinction"
        # Should warn about using the correct tier designation
        assert "Tier 3" in content, \
            "Should mention Tier 3a/3b when using runtime evidence"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
