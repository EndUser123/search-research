"""
Tests for overconfidence_detector module.

Covers:
- Causal assertion detection
- Catastrophizing detection
- Unverified attribution detection
- Structural assessment detection (new)
- Evidence marker allow-listing (quantified counts, compared across, etc.)
- Outcome attribution detection
"""

import sys
sys.path.insert(0, str(__file__).rsplit("tests", 1)[0])
from overconfidence_detector import (
    OverconfidenceMatch,
    detect_overconfidence,
    detect_all_overconfidence,
    _has_evidence_marker,
    _is_explanatory_prose,
    _infer_structural_subject,
)


class TestCausalAssertion:
    """Causal assertion phrase detection."""

    def test_detects_this_explains_why(self):
        assert detect_overconfidence("This explains why the tests failed") is not None

    def test_detects_which_explains(self):
        assert detect_overconfidence("The error, which explains the failure") is not None

    def test_detects_this_is_why(self):
        assert detect_overconfidence("This is why the API returns errors") is not None

    def test_detects_due_to_this(self):
        assert detect_overconfidence("Due to this, everything fails") is not None

    def test_causal_with_tier_is_allowed(self):
        assert detect_overconfidence("[Tier 1]: This explains the failure") is None

    def test_causal_with_verified_is_allowed(self):
        assert detect_overconfidence("Verified: The root cause is X") is None


class TestCatastrophizing:
    """Catastrophizing phrase detection."""

    def test_detects_is_broken(self):
        assert detect_overconfidence("The system is broken") is not None

    def test_detects_completely_fails(self):
        assert detect_overconfidence("The code completely fails under load") is not None

    def test_detects_cant_work(self):
        assert detect_overconfidence("This approach can't work") is not None

    def test_no_catastrophizing_passes(self):
        assert detect_overconfidence("The import statement is missing") is None


class TestUnverifiedAttribution:
    """Root cause attribution detection."""

    def test_detects_root_cause_is(self):
        assert detect_overconfidence("The root cause is the missing import") is not None

    def test_detects_underlying_issue(self):
        assert detect_overconfidence("The underlying issue is the config") is not None

    def test_attribution_with_logs_show_is_allowed(self):
        assert detect_overconfidence("Logs show: the root cause is X") is None


class TestStructuralAssessment:
    """Structural assessment detection — new for architecture/code review contexts."""

    def test_detects_optimal_structure_intentional_exception(self):
        result = detect_overconfidence("Optimal structure, one intentional exception.")
        assert result is not None
        assert result.pattern_type == "structural_assessment"
        assert result.severity == "flag"

    def test_detects_deliberate_pattern(self):
        assert detect_overconfidence("That's a deliberate pattern, not an error.") is not None

    def test_detects_intentional_design(self):
        assert detect_overconfidence("This is intentional design.") is not None

    def test_detects_correct_by_design(self):
        assert detect_overconfidence("Correct by design — it's optimal.") is not None

    def test_detects_proper_structure(self):
        assert detect_overconfidence("The proper structure is correct — here's why:") is not None

    def test_detects_optimal_architecture(self):
        assert detect_overconfidence("Optimal architecture — intentional exception.") is not None

    def test_tier_allows(self):
        assert detect_overconfidence("[Tier 1]: intentional exception per ADR-002") is None

    def test_compared_against_allows(self):
        assert detect_overconfidence("Compared against all 36 peers: optimal structure.") is None

    def test_compared_across_allows(self):
        assert detect_overconfidence("compared across all skills: optimal structure") is None

    def test_verified_across_allows(self):
        assert detect_overconfidence("verified across 37 packages: optimal structure") is None

    def test_reviewed_n_files_allows(self):
        assert detect_overconfidence("After reviewing 36 files: optimal structure.") is None

    def test_reviewed_n_skills_allows(self):
        """skills was missing from alternation — this was the original bug."""
        assert detect_overconfidence("I reviewed 37 skills — optimal structure.") is None

    def test_checked_n_instances_allows(self):
        assert detect_overconfidence("Checked 12 instances — intentional design.") is None

    def test_enumerated_all_skills_allows(self):
        assert detect_overconfidence("Enumerated all skills: deliberate exception here.") is None

    def test_examined_n_cases_allows(self):
        """cases was missing from alternation."""
        assert detect_overconfidence("Examined 24 cases: intentional pattern.") is None

    def test_after_reviewing_all_allows(self):
        assert detect_overconfidence("after reviewing all 36 peers") is None

    def test_i_dont_know_passes(self):
        """Non-claim uncertainty should not be flagged."""
        assert detect_overconfidence("I don't know if this is intentional.") is None

    def test_optimal_structure_without_evidence_detects(self):
        """Regression: 'optimal structure' alone was not caught before.

        Pattern matches "optimal structure" as a phrase, not "structure is optimal" (predicate).
        "The structure is optimal" = predicate → not caught
        "Optimal structure" = phrase → caught
        """
        result = detect_overconfidence("Optimal structure — one exception.")
        assert result is not None
        assert result.pattern_type == "structural_assessment"


class TestOutcomeAttribution:
    """Post-hoc causation attribution detection."""

    def test_detects_correctly_blocked(self):
        assert detect_overconfidence("The hook correctly blocked the command") is not None

    def test_detects_was_handled_by(self):
        assert detect_overconfidence("This was handled by the validator") is not None

    def test_detects_blocked_by(self):
        assert detect_overconfidence("blocked by the safety hook") is not None

    def test_logs_show_allows(self):
        assert detect_overconfidence("Logs show: The hook correctly blocked it") is None

    def test_tier_1_allows(self):
        assert detect_overconfidence("[Tier 1]: blocked by the safety hook") is None


class TestQuantifiedEvidenceMarker:
    """Specific patterns that must be allow-listed by quantified count regex."""

    def test_reviewed_n_skills(self):
        """Previously this was a false negative — skills not in alternation."""
        assert detect_overconfidence("I reviewed 37 skills, only one is nested.") is None

    def test_checked_n_cases(self):
        """cases not in alternation was another gap."""
        assert detect_overconfidence("Checked 18 cases — none match.") is None

    def test_compared_across_n(self):
        assert detect_overconfidence("Compared across 40 packages: all follow pattern.") is None

    def test_verified_against_n(self):
        assert detect_overconfidence("Verified against 25 skills: consistent.") is None


class TestDetectAllOverconfidence:
    """Full-spectrum detection (all pattern types at once)."""

    def test_multiple_matches_includes_structural(self):
        text = "This explains the error. The correct structure is optimal."
        results = detect_all_overconfidence(text)
        types = [r.pattern_type for r in results]
        assert "causal_assertion" in types
        # "The correct structure" contains "correct structure" phrase -> structural_assessment
        assert "structural_assessment" in types

    def test_structural_only(self):
        text = "Optimal structure — intentional exception."
        results = detect_all_overconfidence(text)
        # Multiple structural patterns can fire on a single phrase
        # (e.g. "optimal structure" + "intentional exception" + "structure — intentional exception")
        structural = [r for r in results if r.pattern_type == "structural_assessment"]
        assert len(structural) >= 2
        assert all(r.pattern_type == "structural_assessment" for r in results)


class TestHasEvidenceMarker:
    """Direct unit tests for _has_evidence_marker."""

    def test_tier_markers(self):
        assert _has_evidence_marker("[Tier 1]: the cause is X")
        assert _has_evidence_marker("tier 2: verified")

    def test_compared_markers(self):
        assert _has_evidence_marker("compared against 36 files")
        assert _has_evidence_marker("compared across all peers")

    def test_count_pattern(self):
        assert _has_evidence_marker("reviewed 36 files")
        assert _has_evidence_marker("checked 12 instances")
        assert _has_evidence_marker("enumerated all skills")

    def test_no_evidence_returns_false(self):
        assert not _has_evidence_marker("The structure is correct.")
        assert not _has_evidence_marker("This is intentional.")


class TestIsExplanatoryProse:
    """_is_explanatory_prose context filtering."""

    def test_why_question_with_data_allows_causal(self):
        response = "After reviewing 37 files, this explains why it fails."
        prompt = "Why does this fail?"
        assert _is_explanatory_prose(response, prompt) is True

    def test_why_question_without_data_rejects(self):
        response = "This explains why it fails."
        prompt = "Why does this fail?"
        assert _is_explanatory_prose(response, prompt) is False

    def test_non_why_prompt_returns_false(self):
        response = "After reviewing 36 files."
        prompt = "What files are affected?"
        assert _is_explanatory_prose(response, prompt) is False


class TestToolEventsEvidence:
    """Tool-events-based comparison evidence for structural claims."""

    def test_structural_block_no_tool_events(self):
        """Structural claim + empty tool_events -> BLOCK."""
        result = detect_overconfidence(
            "Optimal structure — one exception.",
            tool_events=[],
        )
        assert result is not None
        assert result.pattern_type == "structural_assessment"

    def test_structural_block_none_tool_events(self):
        """Structural claim + None tool_events -> BLOCK."""
        result = detect_overconfidence(
            "Correct by design — it's optimal.",
            tool_events=None,
        )
        assert result is not None
        assert result.pattern_type == "structural_assessment"

    def test_structural_block_enumeration_only(self):
        """Enumeration Bash commands without inspection -> BLOCK.

        'ls skills/*/' is enumeration but no Read events means we haven't
        actually inspected any peer structures.
        """
        events = [
            {"name": "Bash", "command": "ls skills/*/SKILL.md", "output_excerpt": ""},
            {"name": "Bash", "command": "ls packages/*/SKILL.md", "output_excerpt": ""},
        ]
        result = detect_overconfidence(
            "Optimal structure — one exception.",
            tool_events=events,
        )
        assert result is not None
        assert result.pattern_type == "structural_assessment"

    def test_structural_allow_with_enumeration_plus_inspection(self):
        """Structural claim + enumeration Bash + ≥2 distinct Read events -> ALLOW.

        'ls skills/*/' (enumeration) + inspection of 2 distinct sibling files
        satisfies the quality threshold.
        """
        events = [
            {"name": "Bash", "command": "ls skills/*/", "output_excerpt": ""},
            {"name": "Read", "command": {"file_path": "skills/foo/SKILL.md"}, "output_excerpt": ""},
            {"name": "Read", "command": {"file_path": "skills/bar/SKILL.md"}, "output_excerpt": ""},
        ]
        result = detect_overconfidence(
            "Optimal structure — one exception.",
            tool_events=events,
        )
        assert result is None

    def test_structural_block_same_file_repeated(self):
        """3 Read events all on the same file -> BLOCK.

        Normalization deduplicates reads of the same file.
        """
        events = [
            {"name": "Read", "command": {"file_path": "skills/code/SKILL.md"}, "output_excerpt": ""},
            {"name": "Read", "command": {"file_path": "skills/code/SKILL.md"}, "output_excerpt": ""},
            {"name": "Read", "command": {"file_path": "skills/code/SKILL.md"}, "output_excerpt": ""},
        ]
        result = detect_overconfidence(
            "Optimal structure — one exception.",
            tool_events=events,
        )
        assert result is not None
        assert result.pattern_type == "structural_assessment"

    def test_structural_allow_with_three_distinct_siblings(self):
        """Structural claim + 3 distinct sibling file reads (no enumeration) -> ALLOW.

        When we have 3+ distinct inspected peer targets without enumeration,
        that is sufficient comparison evidence.
        """
        events = [
            {"name": "Read", "command": {"file_path": "skills/foo/SKILL.md"}, "output_excerpt": ""},
            {"name": "Read", "command": {"file_path": "skills/bar/SKILL.md"}, "output_excerpt": ""},
            {"name": "Read", "command": {"file_path": "skills/baz/SKILL.md"}, "output_excerpt": ""},
        ]
        result = detect_overconfidence(
            "The proper structure is correct — here's why:",
            tool_events=events,
        )
        assert result is None

    def test_structural_block_bash_no_glob_no_reads(self):
        """'ls skills/' (no glob) + 1 Read -> BLOCK.

        Without glob/wildcard signals or find predicates, 'ls skills/' is a
        shallow listing, not enumeration. One distinct read is insufficient.
        """
        events = [
            {"name": "Bash", "command": "ls skills/", "output_excerpt": ""},
            {"name": "Read", "command": {"file_path": "skills/foo/SKILL.md"}, "output_excerpt": ""},
        ]
        result = detect_overconfidence(
            "Optimal architecture — intentional exception.",
            tool_events=events,
        )
        assert result is not None
        assert result.pattern_type == "structural_assessment"

    def test_structural_allow_with_find_enumeration_plus_inspection(self):
        """'find skills/ -name SKILL.md' + 2 distinct reads -> ALLOW."""
        events = [
            {"name": "Bash", "command": "find skills/ -name SKILL.md", "output_excerpt": ""},
            {"name": "Read", "command": {"file_path": "skills/a/SKILL.md"}, "output_excerpt": ""},
            {"name": "Read", "command": {"file_path": "skills/b/SKILL.md"}, "output_excerpt": ""},
        ]
        result = detect_overconfidence(
            "Optimal structure — one exception.",
            tool_events=events,
        )
        assert result is None

    def test_structural_allow_with_grep_enumeration_plus_inspection(self):
        """'grep -r pattern skills/' + 2 distinct reads -> ALLOW."""
        events = [
            {"name": "Bash", "command": 'grep -r "pattern" skills/', "output_excerpt": ""},
            {"name": "Read", "command": {"file_path": "skills/x/SKILL.md"}, "output_excerpt": ""},
            {"name": "Read", "command": {"file_path": "skills/y/SKILL.md"}, "output_excerpt": ""},
        ]
        result = detect_overconfidence(
            "Optimal structure — one exception.",
            tool_events=events,
        )
        assert result is None

    def test_structural_allow_src_modules(self):
        """Reads of 3 distinct src/* modules (generic sibling pattern) -> ALLOW."""
        events = [
            {"name": "Read", "command": {"file_path": "src/module_a.rs"}, "output_excerpt": ""},
            {"name": "Read", "command": {"file_path": "src/module_b.rs"}, "output_excerpt": ""},
            {"name": "Read", "command": {"file_path": "src/module_c.rs"}, "output_excerpt": ""},
        ]
        result = detect_overconfidence(
            "The correct structure is optimal — here's why:",
            tool_events=events,
        )
        assert result is None

    def test_structural_block_single_unrelated_bash(self):
        """Structural claim + single unrelated Bash -> still BLOCK."""
        events = [
            {"name": "Bash", "command": "pwd", "output_excerpt": ""},
        ]
        result = detect_overconfidence(
            "Optimal structure — one exception.",
            tool_events=events,
        )
        assert result is not None
        assert result.pattern_type == "structural_assessment"

    def test_structural_block_single_file_read(self):
        """Structural claim + single Read -> still BLOCK."""
        events = [
            {"name": "Read", "command": {"file_path": "skills/foo/SKILL.md"}, "output_excerpt": ""},
        ]
        result = detect_overconfidence(
            "Optimal structure — one exception.",
            tool_events=events,
        )
        assert result is not None
        assert result.pattern_type == "structural_assessment"

    def test_uncertainty_allows_regardless(self):
        """'I dont know' passes even with no tool_events."""
        result = detect_overconfidence(
            "I don't know if this is intentional.",
            tool_events=[],
        )
        assert result is None

    def test_detect_all_with_comparison_tool_events(self):
        """detect_all: structural claim + valid comparison events -> empty results.

        Requires enumeration Bash (glob/wildcard or find predicates) AND ≥2
        distinct Read targets. Plain 'ls dir/' is not enumeration.
        """
        events = [
            {"name": "Bash", "command": "ls skills/*/", "output_excerpt": ""},
            {"name": "Read", "command": {"file_path": "skills/code/SKILL.md"}, "output_excerpt": ""},
            {"name": "Read", "command": {"file_path": "skills/refactor/SKILL.md"}, "output_excerpt": ""},
        ]
        results = detect_all_overconfidence(
            "Optimal structure — intentional exception.",
            tool_events=events,
        )
        structural = [r for r in results if r.pattern_type == "structural_assessment"]
        assert len(structural) == 0

    def test_detect_all_without_comparison_tool_events(self):
        """detect_all: structural claim + no comparison -> structural result."""
        results = detect_all_overconfidence(
            "Optimal structure — one exception.",
            tool_events=[],
        )
        structural = [r for r in results if r.pattern_type == "structural_assessment"]
        assert len(structural) == 1

    def test_non_structural_pattern_not_affected(self):
        """Non-structural patterns still work regardless of tool_events."""
        # Causal assertion with no evidence
        result = detect_overconfidence(
            "This explains why the tests failed",
            tool_events=[],
        )
        assert result is not None
        assert result.pattern_type == "causal_assertion"

        # With comparison events but no evidence marker — still catches causal
        result2 = detect_overconfidence(
            "This explains why the tests failed",
            tool_events=[
                {"name": "Bash", "command": "ls skills/", "output_excerpt": ""},
                {"name": "Bash", "command": "ls packages/", "output_excerpt": ""},
            ],
        )
        # Causal assertion should still be flagged (comparison evidence != causal evidence)
        assert result2 is not None
        assert result2.pattern_type == "causal_assertion"


class TestInferStructuralSubject:
    """_infer_structural_subject extraction from structural claims."""

    def test_extracts_directory_prefix(self):
        assert _infer_structural_subject("refactor/ structure is optimal") == "refactor"
        assert _infer_structural_subject("skills/ pattern is correct") == "skills"
        assert _infer_structural_subject("plugin/ design is intentional") == "plugin"
        assert _infer_structural_subject("The hooks/ structure is correct") == "hooks"

    def test_extracts_nested_path(self):
        assert _infer_structural_subject("skills/code/ structure is optimal") == "skills"

    def test_bare_structural_no_dir_prefix(self):
        """No directory prefix -> returns None (triggers fallback)."""
        assert _infer_structural_subject("Optimal structure — one exception.") is None
        assert _infer_structural_subject("The correct structure is optimal") is None
        assert _infer_structural_subject("That's a deliberate pattern, not an error.") is None

    def test_empty_response(self):
        assert _infer_structural_subject("") is None
        assert _infer_structural_subject(None) is None

    def test_non_structural_response(self):
        """Non-structural text should return None."""
        assert _infer_structural_subject("This explains why the tests failed") is None
        assert _infer_structural_subject("The root cause is X") is None


class TestSubjectAwareEvidence:
    """Subject-aware comparison evidence for structural claims.

    Verifies that evidence targets match the subject of the claim.
    Uses phrasing that matches actual structural patterns:
      "refactor/ architecture is optimal"  (matches architecture is optimal)
      "refactor/ pattern is intentional"   (matches pattern is intentional)
      "refactor/ design is deliberate"     (matches design is deliberate)
    """

    # --- claim about refactor/ with evidence from skills/ ---

    def test_wrong_subject_block(self):
        """Claim about refactor/ + evidence from skills/ -> BLOCK."""
        # Matches \boptimal\s+architecture\b
        response = "refactor/ architecture is optimal"
        events = [
            {"name": "Bash", "command": "ls skills/*/", "output_excerpt": ""},
            {"name": "Read", "command": {"file_path": "skills/foo/SKILL.md"}, "output_excerpt": ""},
            {"name": "Read", "command": {"file_path": "skills/bar/SKILL.md"}, "output_excerpt": ""},
        ]
        result = detect_overconfidence(response, tool_events=events)
        assert result is not None
        assert result.pattern_type == "structural_assessment"

    def test_wrong_subject_block_no_enumeration(self):
        """Claim about refactor/ + 3 reads from skills/ -> BLOCK."""
        response = "refactor/ pattern is intentional"
        events = [
            {"name": "Read", "command": {"file_path": "skills/foo/SKILL.md"}, "output_excerpt": ""},
            {"name": "Read", "command": {"file_path": "skills/bar/SKILL.md"}, "output_excerpt": ""},
            {"name": "Read", "command": {"file_path": "skills/baz/SKILL.md"}, "output_excerpt": ""},
        ]
        result = detect_overconfidence(response, tool_events=events)
        assert result is not None
        assert result.pattern_type == "structural_assessment"

    # --- claim about refactor/ with evidence from refactor/ ---

    def test_correct_subject_allow_with_enumeration(self):
        """Claim about refactor/ + ls refactor/*/ + reads -> ALLOW."""
        response = "refactor/ architecture is optimal"
        events = [
            {"name": "Bash", "command": "ls refactor/*/", "output_excerpt": ""},
            {"name": "Read", "command": {"file_path": "refactor/foo/SKILL.md"}, "output_excerpt": ""},
            {"name": "Read", "command": {"file_path": "refactor/bar/SKILL.md"}, "output_excerpt": ""},
        ]
        result = detect_overconfidence(response, tool_events=events)
        assert result is None  # Allowed: evidence on correct subject

    def test_correct_subject_allow_no_enumeration(self):
        """Claim about refactor/ + 3 reads from refactor/ -> ALLOW."""
        response = "refactor/ pattern is intentional"
        events = [
            {"name": "Read", "command": {"file_path": "refactor/foo/SKILL.md"}, "output_excerpt": ""},
            {"name": "Read", "command": {"file_path": "refactor/bar/SKILL.md"}, "output_excerpt": ""},
            {"name": "Read", "command": {"file_path": "refactor/baz/SKILL.md"}, "output_excerpt": ""},
        ]
        result = detect_overconfidence(response, tool_events=events)
        assert result is None  # Allowed: 3 reads from same subject

    # --- bare structural claim (no subject) -> fallback to current logic ---

    def test_bare_claim_fallback_to_scope_check(self):
        """'Optimal structure' has no subject -> use normal scope check."""
        response = "Optimal structure — one exception."
        events = [
            {"name": "Bash", "command": "ls skills/*/", "output_excerpt": ""},
            {"name": "Read", "command": {"file_path": "skills/foo/SKILL.md"}, "output_excerpt": ""},
            {"name": "Read", "command": {"file_path": "skills/bar/SKILL.md"}, "output_excerpt": ""},
        ]
        # No subject -> falls back to checking same-scope, skills==skills -> ALLOW
        result = detect_overconfidence(response, tool_events=events)
        assert result is None

    # --- claim about plugins/ with packages/ context ---

    def test_plugin_claim_with_packages_context(self):
        """Claim about plugin/ design + enum on packages/ -> BLOCK (wrong subject)."""
        response = "plugin/ design is deliberate"
        events = [
            {"name": "Bash", "command": "ls packages/*/", "output_excerpt": ""},
            {"name": "Read", "command": {"file_path": "packages/foo/SKILL.md"}, "output_excerpt": ""},
            {"name": "Read", "command": {"file_path": "packages/bar/SKILL.md"}, "output_excerpt": ""},
        ]
        result = detect_overconfidence(response, tool_events=events)
        assert result is not None
        assert result.pattern_type == "structural_assessment"

    # --- uncertain response (no confident claim) ---

    def test_uncertainty_no_subject(self):
        """'I don't know' has no structural claim subject."""
        response = "I don't know if this is intentional."
        events = [
            {"name": "Bash", "command": "ls skills/*/", "output_excerpt": ""},
            {"name": "Read", "command": {"file_path": "skills/foo/SKILL.md"}, "output_excerpt": ""},
            {"name": "Read", "command": {"file_path": "skills/bar/SKILL.md"}, "output_excerpt": ""},
        ]
        result = detect_overconfidence(response, tool_events=events)
        assert result is None  # No structural claim detected

    # --- subject in enumeration roots (mixed roots, filter to subject) ---

    def test_mixed_roots_filtered_to_subject(self):
        """Enum targets both skills/ and refactor/, claim is refactor/ -> filter to refactor/."""
        response = "refactor/ architecture is optimal"
        events = [
            {"name": "Bash", "command": "ls skills/*/ refactor/*/", "output_excerpt": ""},
            {"name": "Read", "command": {"file_path": "refactor/foo/SKILL.md"}, "output_excerpt": ""},
            {"name": "Read", "command": {"file_path": "refactor/bar/SKILL.md"}, "output_excerpt": ""},
        ]
        result = detect_overconfidence(response, tool_events=events)
        assert result is None

    def test_mixed_roots_wrong_subject_blocked(self):
        """Enum targets both skills/ and refactor/, claim is skills/, evidence is refactor/ -> BLOCK."""
        response = "skills/ architecture is optimal"
        events = [
            {"name": "Bash", "command": "ls skills/*/ refactor/*/", "output_excerpt": ""},
            {"name": "Read", "command": {"file_path": "refactor/foo/SKILL.md"}, "output_excerpt": ""},
            {"name": "Read", "command": {"file_path": "refactor/bar/SKILL.md"}, "output_excerpt": ""},
        ]
        result = detect_overconfidence(response, tool_events=events)
        assert result is not None
        assert result.pattern_type == "structural_assessment"
