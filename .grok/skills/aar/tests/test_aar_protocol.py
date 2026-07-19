"""Contract-presence tests for /aar skill (CONTRACT_TESTED).

Evidence classification: CONTRACT_TESTED

These tests verify that the AAR skill corpus (SKILL.md core plus the
conditionally-loaded references/*.md files) contains the required text,
phases, schemas, types, dispositions, and rules. They are structural
tests only.

They are NOT behavioral tests and do NOT prove that a live Grok LLM
follows the skill. "Behavioral test" (LIVE_BEHAVIOR_TESTED) requires an
actual Grok /aar invocation with generated output.

Phase 1 lean-hybrid architecture note:
  The skill is split into an always-loaded lean core (SKILL.md) and
  conditionally-loaded references/*.md files. Tests in this file check
  that required content exists SOMEWHERE in the combined corpus. Tests
  that assert content is in the default-loaded surface specifically use
  ``_skill_text()`` (core only); tests that assert the corpus defines a
  concept use ``_corpus_text()`` (core + references).

Taxonomy:
  CONTRACT_TESTED      — text/structure presence (this file)
  CONTRACT_MODEL_TESTED  — test-local executable model internally consistent
  LIVE_BEHAVIOR_TESTED   — actual Grok /aar invocation and generated artifact
"""

import json
import re
from pathlib import Path

import pytest

SKILL_PATH = Path(__file__).resolve().parent.parent / "SKILL.md"
REFERENCES_DIR = Path(__file__).resolve().parent.parent / "references"


def _skill_text() -> str:
    """Return ONLY the always-loaded SKILL.md core (the lean surface)."""
    return SKILL_PATH.read_text(encoding="utf-8")


def _corpus_text() -> str:
    """Return SKILL.md core PLUS all references/*.md content.

    Used for contract tests that verify a concept is defined SOMEWHERE
    in the skill corpus. The Phase 1 split moves conditional detail to
    references; the contract is still satisfied if the content lives in
    a reference file that loads on the appropriate trigger.
    """
    parts = [SKILL_PATH.read_text(encoding="utf-8")]
    if REFERENCES_DIR.is_dir():
        for ref in sorted(REFERENCES_DIR.glob("*.md")):
            parts.append(f"\n\n--- {ref.name} ---\n")
            parts.append(ref.read_text(encoding="utf-8"))
    return "".join(parts)


# ---------------------------------------------------------------------------
# Test 1: Complete vs partial source handling
# ---------------------------------------------------------------------------


def test_skill_defines_source_status_types():
    """SKILL.md must define SOURCE_COMPLETE, SOURCE_PARTIAL, SOURCE_UNVERIFIED."""
    text = _corpus_text()
    assert "SOURCE_COMPLETE" in text
    assert "SOURCE_PARTIAL" in text
    assert "SOURCE_UNVERIFIED" in text


def test_skill_requires_partial_source_flagged():
    """Partial sources must be flagged, not claimed as exhaustive."""
    text = _corpus_text()
    assert "must not claim" in text.lower() and "exhaustive" in text.lower()


# ---------------------------------------------------------------------------
# Test 2: Resolved incident does not become open task
# ---------------------------------------------------------------------------


def test_resolved_incident_not_auto_promoted():
    """SKILL.md must state resolved incidents are NOT automatically open actions."""
    text = _corpus_text()
    assert "resolved_incident" in text
    assert "do NOT automatically become open" in text or "not a pending task" in text.lower()


# ---------------------------------------------------------------------------
# Test 3: Pending decision distinguished from defect
# ---------------------------------------------------------------------------


def test_pending_decision_is_separate_type():
    """pending_decision must be a distinct episode type from open_defect."""
    text = _corpus_text()
    assert "pending_decision" in text
    assert "open_defect" in text
    # They must appear as separate table rows, not combined
    types_section = re.search(r"## Phase 2.*?## Phase 3", text, re.DOTALL)
    assert types_section
    assert "pending_decision" in types_section.group(0)
    assert "open_defect" in types_section.group(0)


# ---------------------------------------------------------------------------
# Test 4: Duplicate episodes clustered into one pattern
# ---------------------------------------------------------------------------


def test_pattern_synthesis_requires_clustering():
    """SKILL.md must require deduplication of episodes into patterns."""
    text = _corpus_text()
    assert "cluster" in text.lower() or "dedup" in text.lower()
    assert "shared_root_cause" in text


# ---------------------------------------------------------------------------
# Test 5: Validated success captured
# ---------------------------------------------------------------------------


def test_validated_success_is_required_phase():
    """SKILL.md must have Phase 5 for validated practices."""
    text = _corpus_text()
    assert "## Phase 5" in text
    assert "validated_success" in text
    assert "PRESERVE" in text
    assert "STANDARDIZE" in text


# ---------------------------------------------------------------------------
# Test 6: NO_CHANGE and PRESERVE as valid outcomes
# ---------------------------------------------------------------------------


VALID_DISPOSITIONS = {
    "ACT_NOW",
    "INVESTIGATE",
    "MONITOR",
    "PRESERVE",
    "DEFER",
    "BLOCKED",
    "NOT_WORTH_DOING",
    "NO_CHANGE",
}


def test_all_dispositions_defined():
    """All 8 dispositions must be present in the promotion challenge."""
    text = _corpus_text()
    for d in VALID_DISPOSITIONS:
        assert d in text, f"Disposition {d} missing from SKILL.md"


def test_no_change_explicitly_valid():
    """SKILL.md must state NO_CHANGE is valid and desirable."""
    text = _corpus_text()
    assert "NO_CHANGE" in text
    assert "valid" in text.lower() and "desirable" in text.lower()


# ---------------------------------------------------------------------------
# Test 7: Opportunity rejected when existing coverage sufficient
# ---------------------------------------------------------------------------


def test_promotion_challenge_includes_existing_coverage_check():
    """Promotion challenge must test 'is an existing mechanism already sufficient?'."""
    text = _corpus_text()
    assert "existing mechanism already sufficient" in text.lower()


def test_promotion_challenge_includes_smaller_intervention_check():
    """Promotion challenge must test 'is there a smaller intervention?'."""
    text = _corpus_text()
    assert "smaller" in text.lower() and "intervention" in text.lower()


# ---------------------------------------------------------------------------
# Test 8: Implementation not performed without authorization
# ---------------------------------------------------------------------------


def test_skill_forbids_silent_implementation():
    """SKILL.md must state AAR does not implement without authorization."""
    text = _corpus_text()
    assert "do not implement" in text.lower() or "must not silently implement" in text.lower()
    assert "explicit authorization" in text.lower() or "authorized" in text.lower()


def test_no_companion_skills_created():
    """SKILL.md must forbid creating aar-redteam, aar-implement, etc."""
    text = _corpus_text()
    assert "aar-redteam" in text
    assert "Do not create" in text or "do not create" in text


# ---------------------------------------------------------------------------
# Test 9: Foreign terminal state ignored
# ---------------------------------------------------------------------------


def test_foreign_terminal_state_excluded():
    """SKILL.md must require terminal isolation and foreign-state exclusion."""
    text = _corpus_text()
    assert "Never read another terminal" in text
    assert "foreign terminal state" in text.lower() or "foreign" in text.lower()


# ---------------------------------------------------------------------------
# Test 10: No /debrief alias (removed — AAR is standalone)
# ---------------------------------------------------------------------------


def test_no_debrief_alias_claim():
    """SKILL.md must NOT claim /debrief as an alias (standalone skill)."""
    text = _corpus_text()
    # The alias declaration was removed; verify it is gone
    assert "Alias:** `/debrief` routes here" not in text
    assert "do not maintain two implementations" not in text.lower()


# ---------------------------------------------------------------------------
# Test 11: Windows path and PowerShell invocation
# ---------------------------------------------------------------------------


def test_shell_detection_required():
    """SKILL.md must require reading $PSVersionTable."""
    text = _corpus_text()
    assert "PSVersionTable" in text


def test_powershell_7_preferred():
    """SKILL.md must say do not invoke powershell.exe 5.1 when session uses pwsh 7+."""
    text = _corpus_text()
    assert "pwsh" in text
    assert "5.1" in text


# ---------------------------------------------------------------------------
# Test 12: Output accounting reconciliation
# ---------------------------------------------------------------------------

ALL_TYPES = [
    "validated_success",
    "resolved_incident",
    "open_defect",
    "process_weakness",
    "pending_decision",
    "opportunity_candidate",
    "observation",
    "unknown",
]


def test_all_episode_types_defined():
    """All 8 episode types must be present in Phase 2."""
    text = _corpus_text()
    for t in ALL_TYPES:
        assert t in text, f"Episode type {t} missing from SKILL.md"


def test_accounting_reconciliation_formula():
    """SKILL.md must contain the accounting reconciliation formula."""
    text = _corpus_text()
    assert "total_episodes" in text
    assert "reconcile" in text.lower()
    # Every type must appear in the reconciliation context
    recon_section = re.search(r"### Accounting reconciliation.*?(?=###|\Z)", text, re.DOTALL)
    if recon_section:
        for t in ALL_TYPES:
            assert t in recon_section.group(0), f"Type {t} missing from reconciliation"


# ---------------------------------------------------------------------------
# Structural: skill discoverable and well-formed
# ---------------------------------------------------------------------------


def test_skill_file_exists():
    assert SKILL_PATH.exists(), f"SKILL.md not found at {SKILL_PATH}"


def test_skill_has_valid_frontmatter():
    """Frontmatter must have name, description, effort."""
    text = _corpus_text()
    assert text.startswith("---")
    header = text[: text.index("---", 3)]
    assert "name: aar" in header
    assert "description:" in header
    assert "effort:" in header


def test_skill_has_all_phases():
    """SKILL.md must have Phases 1-9."""
    text = _corpus_text()
    for i in range(1, 10):
        assert f"## Phase {i}" in text, f"Phase {i} missing"


def test_skill_has_rules_section():
    """SKILL.md must have a Rules section with ≥10 rules."""
    text = _corpus_text()
    assert "## Rules" in text or "## Rules" in text
    # Count numbered rules
    rules = re.findall(r"^\d+\.\s", text, re.MULTILINE)
    assert len(rules) >= 10, f"Expected ≥10 rules, found {len(rules)}"


# ---------------------------------------------------------------------------
# Lesson Calibration Gate (Phase 9 additions)
# ---------------------------------------------------------------------------


def test_lesson_calibration_gate_defined():
    """SKILL.md must define the Lesson Calibration Gate in Phase 9."""
    text = _corpus_text()
    assert "Lesson Calibration Gate" in text
    assert "Supporting episodes" in text
    assert "Direct observation" in text
    assert "Causal interpretation" in text
    assert "Competing explanations" in text


def test_lesson_calibration_comparison_status_values():
    """All 4 comparison-status values must be present."""
    text = _corpus_text()
    for v in ["NO_COMPARISON", "INFORMAL_COMPARISON", "CONTROLLED_COMPARISON", "EXTERNAL_EVIDENCE"]:
        assert v in text, f"Comparison status {v} missing"


def test_lesson_calibration_scope_values():
    """All 3 scope values must be present."""
    text = _corpus_text()
    for v in ["SESSION_SPECIFIC", "PROBLEM_CLASS", "GENERAL"]:
        assert v in text, f"Scope {v} missing"


def test_lesson_calibration_confidence_values():
    """All 3 confidence values must be present."""
    text = _corpus_text()
    for v in ["OBSERVED", "INFERRED", "SPECULATIVE"]:
        assert v in text, f"Confidence {v} missing"


def test_lesson_calibration_unsupported_extension_required():
    """Lesson gate must require stating what evidence does NOT establish."""
    text = _corpus_text()
    assert "Unsupported extension" in text
    assert "does NOT establish" in text or "does not establish" in text


def test_comparative_claim_rule_present():
    """SKILL.md must contain the comparative-claim rule."""
    text = _corpus_text()
    assert "Comparative-claim rule" in text
    assert "more reliable" in text
    assert "intervention class" in text


def test_comparative_claim_rule_examples():
    """The rule must include examples of overgeneralization."""
    text = _corpus_text()
    assert "rejected proposals do not establish" in text or "Specific rejected proposals do not establish" in text


def test_intervention_selection_sequence_present():
    """SKILL.md must define the intervention selection sequence."""
    text = _corpus_text()
    assert "Observed failure" in text
    assert "verified causal mechanism" in text
    assert "problem-class classification" in text
    assert "smallest sufficient intervention" in text
    assert "bounded lesson" in text


def test_intervention_classes_not_ranked():
    """The skill must not rank intervention classes before failure classification."""
    text = _corpus_text()
    assert "must not rank intervention classes" in text or "must not choose or rank" in text


# ---------------------------------------------------------------------------
# Epistemic calibration (Phase 9.5 additions)
# ---------------------------------------------------------------------------

CONFIDENCE_DIMENSIONS = ["evidence_confidence", "causal_confidence", "intervention_confidence", "scope_confidence"]
CONFIDENCE_LEVELS = ["VERY_HIGH", "HIGH", "MEDIUM", "LOW", "UNKNOWN"]
CAUSAL_LEVELS = ["ROOT_CAUSE", "CONTRIBUTING_FACTOR", "MANIFESTATION", "CONSEQUENCE"]
TEMPORAL_CATS = ["KNOWN_AT_THE_TIME", "DISCOVERABLE_AT_THE_TIME", "LEARNED_LATER", "NOT_REASONABLY_KNOWABLE"]
PREVENTION_LEVELS = ["DEMONSTRATED", "STRONGLY_SUPPORTED", "PLAUSIBLE", "SPECULATIVE", "NOT_SUPPORTED"]
WORKFLOW_CLASSIFICATIONS = ["PROVEN_VALUE", "LIKELY_VALUE", "UNCERTAIN_VALUE", "LOW_OBSERVED_VALUE", "REDUNDANT", "PROCESS_THEATER_CANDIDATE"]
QUALITY_DIMENSIONS = ["decision_quality", "execution_quality", "outcome_quality", "luck_or_external_effect"]
POLICY_LEVELS = ["SESSION_NOTE", "LOCAL_PRACTICE", "CANDIDATE_RULE", "DURABLE_POLICY"]


def test_multidimensional_confidence_defined():
    text = _corpus_text()
    for dim in CONFIDENCE_DIMENSIONS:
        assert dim in text, f"Confidence dimension {dim} missing"


def test_confidence_levels_defined():
    text = _corpus_text()
    for level in CONFIDENCE_LEVELS:
        assert level in text, f"Confidence level {level} missing"


def test_confidence_rationales_required():
    text = _corpus_text()
    assert "rationale" in text.lower() or "reason" in text.lower()
    assert "bare labels" in text.lower()


def test_causal_hierarchy_defined():
    text = _corpus_text()
    for level in CAUSAL_LEVELS:
        assert level in text, f"Causal level {level} missing"


def test_temporal_evidence_categories_defined():
    text = _corpus_text()
    for cat in TEMPORAL_CATS:
        assert cat in text, f"Temporal category {cat} missing"


def test_prevention_interception_fields_defined():
    text = _corpus_text()
    assert "Observed failure path" in text
    assert "Interception point" in text
    assert "Residual bypass" in text


def test_prevention_confidence_levels_defined():
    text = _corpus_text()
    for level in PREVENTION_LEVELS:
        assert level in text, f"Prevention level {level} missing"


def test_workflow_value_fields_defined():
    text = _corpus_text()
    assert "Unique output" in text
    assert "Rare-event value" in text


def test_workflow_classifications_defined():
    text = _corpus_text()
    for cls in WORKFLOW_CLASSIFICATIONS:
        assert cls in text, f"Workflow classification {cls} missing"


def test_decision_outcome_quality_separation():
    text = _corpus_text()
    for dim in QUALITY_DIMENSIONS:
        assert dim in text, f"Quality dimension {dim} missing"


def test_policy_promotion_levels_defined():
    text = _corpus_text()
    for level in POLICY_LEVELS:
        assert level in text, f"Policy level {level} missing"


def test_cross_field_invariants_present():
    text = _corpus_text()
    assert "Cross-field consistency invariants" in text
    assert "NO_COMPARISON" in text and "more reliable than" in text
    assert "SOURCE_PARTIAL" in text and "exhaustive" in text
    assert "accounting proves only" in text.lower()


def test_contradiction_audit_present():
    text = _corpus_text()
    assert "Final contradiction audit" in text
    assert "confidence upgrades" in text
    assert "scope upgrades" in text


def test_accounting_disclaimer_present():
    text = _corpus_text()
    assert "Accounting disclaimer" in text
    assert "arithmetic consistency" in text.lower()


def test_readability_scoping_present():
    text = _corpus_text()
    assert "minor observation" in text.lower() and "compact" in text.lower()
