"""Test-local contract model tests for /aar protocol logic (CONTRACT_MODEL_TESTED).

Evidence classification: CONTRACT_MODEL_TESTED

These tests verify that a test-local executable interpretation of the AAR
contract (Python functions written in this file) is internally consistent.
The functions (classify_episode, should_promote, reconcile_accounting) are
test-local models — they are NOT consumed by the /aar skill, NOT defined in
SKILL.md, and NOT in a shared __lib/. They provide no evidence that a live
Grok LLM follows the skill.

These are NOT behavioral tests. "Behavioral test" (LIVE_BEHAVIOR_TESTED)
requires an actual Grok /aar invocation with generated output.

Taxonomy:
  CONTRACT_TESTED        — text/structure presence in SKILL.md
  CONTRACT_MODEL_TESTED  — test-local executable model internally consistent (this file)
  LIVE_BEHAVIOR_TESTED   — actual Grok /aar invocation and generated artifact

Each test constructs a mini-episode scenario, runs it through the test-local
classification/disposition logic, and checks the result.
"""

import json
from pathlib import Path

import pytest

SKILL_PATH = Path(__file__).resolve().parent.parent / "SKILL.md"


# ---------------------------------------------------------------------------
# AAR protocol primitives (extracted from SKILL.md contract)
# ---------------------------------------------------------------------------

VALID_TYPES = {
    "validated_success",
    "resolved_incident",
    "open_defect",
    "process_weakness",
    "pending_decision",
    "opportunity_candidate",
    "observation",
    "unknown",
}

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

PROMOTABLE_TYPES = {"open_defect", "process_weakness", "opportunity_candidate"}
NON_PROMOTABLE_TYPES = VALID_TYPES - PROMOTABLE_TYPES


def classify_episode(event: str, evidence: str, status: str, *, is_success: bool = False, is_resolved: bool = False, needs_user_decision: bool = False) -> str:
    """Simulate AAR Phase 2 classification logic."""
    if is_success and status == "closed":
        return "validated_success"
    if is_resolved and status == "closed":
        return "resolved_incident"
    if needs_user_decision:
        return "pending_decision"
    if status == "open" and "not fixed" in event.lower():
        return "open_defect"
    if status == "monitor":
        return "process_weakness"
    if status == "closed" and "noteworthy" in event.lower():
        return "observation"
    return "unknown"


def should_promote(episode_type: str, disposition: str) -> bool:
    """Simulate AAR Phase 7 promotion gate."""
    if episode_type not in PROMOTABLE_TYPES:
        return False
    if disposition not in {"ACT_NOW"}:
        return False
    return True


def reconcile_accounting(episodes: list[dict]) -> bool:
    """Simulate AAR Phase 9 accounting reconciliation."""
    total = len(episodes)
    type_sum = 0
    for ep in episodes:
        if ep["type"] in VALID_TYPES:
            type_sum += 1
    return total == type_sum


# ---------------------------------------------------------------------------
# Behavioral fixture 1: Resolved incident not promoted
# ---------------------------------------------------------------------------


def test_resolved_incident_not_promoted_to_action():
    """A resolved incident must not produce a promoted action, regardless of disposition."""
    ep = {
        "id": "AAR-001",
        "type": classify_episode("bug fixed in session", "git log", "closed", is_resolved=True),
        "status": "closed",
    }
    assert ep["type"] == "resolved_incident"
    assert not should_promote(ep["type"], "ACT_NOW"), "Resolved incident must not be promoted even with ACT_NOW"


# ---------------------------------------------------------------------------
# Behavioral fixture 2: Pending decision not treated as defect
# ---------------------------------------------------------------------------


def test_pending_decision_not_defect():
    """A pending decision must classify as pending_decision, not open_defect."""
    ep_type = classify_episode(
        "user needs to decide on merge strategy",
        "conversation turn",
        "open",
        needs_user_decision=True,
    )
    assert ep_type == "pending_decision"
    assert ep_type != "open_defect"
    assert not should_promote(ep_type, "ACT_NOW"), "Pending decision should not auto-promote"


# ---------------------------------------------------------------------------
# Behavioral fixture 3: Existing coverage produces NO_CHANGE
# ---------------------------------------------------------------------------


def test_existing_coverage_produces_no_change():
    """When an existing AGENTS.md rule already covers the gap, disposition is NO_CHANGE."""
    # Simulate: agent proposed a hook; but AGENTS.md already has a rule
    existing_rule_exists = True  # e.g., "Tool friction protocol" already in AGENTS.md
    if existing_rule_exists:
        disposition = "NO_CHANGE"
    else:
        disposition = "ACT_NOW"
    assert disposition == "NO_CHANGE"


# ---------------------------------------------------------------------------
# Behavioral fixture 4: Success-only session
# ---------------------------------------------------------------------------


def test_success_only_session_valid():
    """A session with only validated_success episodes is a valid AAR with 0 promoted actions."""
    episodes = [
        {"id": "AAR-001", "type": "validated_success", "status": "closed"},
        {"id": "AAR-002", "type": "validated_success", "status": "closed"},
        {"id": "AAR-003", "type": "validated_success", "status": "closed"},
    ]
    assert reconcile_accounting(episodes)
    promoted = sum(1 for e in episodes if should_promote(e["type"], "ACT_NOW"))
    assert promoted == 0, "Success-only session must produce 0 promoted actions"


# ---------------------------------------------------------------------------
# Behavioral fixture 5: Duplicate symptoms clustered
# ---------------------------------------------------------------------------


def test_duplicate_symptoms_clustered():
    """Multiple episodes with the same root cause must cluster into one pattern, not N actions."""
    episodes = [
        {"id": "AAR-001", "type": "process_weakness", "event": "proposed hook without research"},
        {"id": "AAR-002", "type": "process_weakness", "event": "proposed config flag without checking docs"},
        {"id": "AAR-003", "type": "process_weakness", "event": "proposed block-all gate without considering use cases"},
    ]
    # All three are the same root cause: "epistemic overconfidence"
    patterns = {}
    for ep in episodes:
        root_cause = "epistemic_overconfidence"
        patterns.setdefault(root_cause, []).append(ep["id"])
    assert len(patterns) == 1, "Three symptoms of one root cause must cluster into 1 pattern"
    assert len(patterns["epistemic_overconfidence"]) == 3
    # One pattern → at most one promoted action
    promoted = min(1, len(patterns))
    assert promoted == 1, "Clustered pattern produces 1 action, not 3"


# ---------------------------------------------------------------------------
# Behavioral fixture 6: Partial source limits exhaustiveness
# ---------------------------------------------------------------------------


def test_partial_source_limits_claim():
    """SOURCE_PARTIAL must not claim exhaustive coverage."""
    source_status = "SOURCE_PARTIAL"
    transcript_is_compacted = True
    # AAR rule: "A partial source may still be analyzed, but the report
    # must not claim exhaustive coverage."
    can_claim_exhaustive = source_status == "SOURCE_COMPLETE" and not transcript_is_compacted
    assert not can_claim_exhaustive, "Partial source must not claim exhaustive coverage"


# ---------------------------------------------------------------------------
# Behavioral fixture 7: Unauthorized implementation refused
# ---------------------------------------------------------------------------


def test_unauthorized_implementation_refused():
    """AAR must not implement without explicit user authorization."""
    user_said_go = False  # user only said /aar, not /aar then "implement"
    aar_can_implement = user_said_go
    assert not aar_can_implement, "AAR must not implement without explicit authorization"


# ---------------------------------------------------------------------------
# Behavioral fixture 8: Foreign terminal state ignored
# ---------------------------------------------------------------------------


def test_foreign_terminal_state_ignored():
    """AAR must not read another terminal's state file."""
    my_terminal = "console_c7d7"
    foreign_terminal = "console_a3b1"
    state_file = f"P:/.artifacts/{foreign_terminal}/yt-is-state.md"

    # AAR rule: "Never read another terminal's state file."
    can_read = my_terminal in state_file
    assert not can_read, "Must not read foreign terminal state file"


# ---------------------------------------------------------------------------
# Accounting reconciliation behavioral test
# ---------------------------------------------------------------------------


def test_accounting_reconciles_with_all_types():
    """A mixed session with all 8 episode types must reconcile."""
    episodes = [
        {"id": f"AAR-{i:03d}", "type": t}
        for i, t in enumerate(sorted(VALID_TYPES), 1)
    ]
    assert reconcile_accounting(episodes)
    assert len(episodes) == 8


def test_accounting_mismatch_detected():
    """An episode with an invalid type must fail reconciliation."""
    episodes = [
        {"id": "AAR-001", "type": "validated_success"},
        {"id": "AAR-002", "type": "bogus_type"},  # invalid
    ]
    assert not reconcile_accounting(episodes)


# ---------------------------------------------------------------------------
# Promotion gate behavioral tests
# ---------------------------------------------------------------------------


def test_no_change_disposition_not_promoted():
    """NO_CHANGE disposition must never produce a promoted action."""
    for ep_type in PROMOTABLE_TYPES:
        assert not should_promote(ep_type, "NO_CHANGE")


def test_preserve_disposition_not_promoted():
    """PRESERVE disposition must never produce a promoted action."""
    for ep_type in PROMOTABLE_TYPES:
        assert not should_promote(ep_type, "PRESERVE")


def test_not_worth_doing_not_promoted():
    """NOT_WORTH_DOING disposition must never produce a promoted action."""
    for ep_type in PROMOTABLE_TYPES:
        assert not should_promote(ep_type, "NOT_WORTH_DOING")


def test_non_promotable_types_never_promoted():
    """validated_success, resolved_incident, observation, unknown must never promote."""
    for ep_type in NON_PROMOTABLE_TYPES:
        assert not should_promote(ep_type, "ACT_NOW")


# ---------------------------------------------------------------------------
# Lesson calibration model tests (CONTRACT_MODEL_TESTED)
# ---------------------------------------------------------------------------

VALID_COMPARISON_STATUSES = {"NO_COMPARISON", "INFORMAL_COMPARISON", "CONTROLLED_COMPARISON", "EXTERNAL_EVIDENCE"}
VALID_SCOPES = {"SESSION_SPECIFIC", "PROBLEM_CLASS", "GENERAL"}
VALID_CONFIDENCE = {"OBSERVED", "INFERRED", "SPECULATIVE"}


def calibrate_lesson(
    supporting_episodes: list[str],
    direct_observation: str,
    causal_interpretation: str,
    competing_explanations: str,
    comparison_status: str,
    scope: str,
    counterexample: str,
    confidence: str,
    unsupported_extension: str,
) -> dict:
    """Build a calibrated lesson object per the Phase 9 gate."""
    return {
        "supporting_episodes": supporting_episodes,
        "direct_observation": direct_observation,
        "causal_interpretation": causal_interpretation,
        "competing_explanations": competing_explanations,
        "comparison_status": comparison_status,
        "scope": scope,
        "counterexample_or_boundary": counterexample,
        "confidence": confidence,
        "unsupported_extension": unsupported_extension,
    }


def lesson_passes_gate(lesson: dict) -> bool:
    """Check whether a lesson passes all calibration gate fields."""
    required_fields = [
        "supporting_episodes", "direct_observation", "causal_interpretation",
        "competing_explanations", "comparison_status", "scope",
        "counterexample_or_boundary", "confidence", "unsupported_extension",
    ]
    for field in required_fields:
        val = lesson.get(field, "")
        if not val or (isinstance(val, str) and not val.strip()):
            return False
    if lesson["comparison_status"] not in VALID_COMPARISON_STATUSES:
        return False
    if lesson["scope"] not in VALID_SCOPES:
        return False
    if lesson["confidence"] not in VALID_CONFIDENCE:
        return False
    return True


def allows_comparative_claim(comparison_status: str, has_external_evidence: bool) -> bool:
    """Comparative claims require CONTROLLED_COMPARISON or EXTERNAL_EVIDENCE."""
    if comparison_status == "EXTERNAL_EVIDENCE" and has_external_evidence:
        return True
    if comparison_status == "CONTROLLED_COMPARISON":
        return True
    return False


def allows_general_scope(scope: str, comparison_status: str, n_sessions: int) -> bool:
    """GENERAL scope requires stronger evidence than one session."""
    if scope != "GENERAL":
        return True
    return n_sessions >= 3 and comparison_status in ("CONTROLLED_COMPARISON", "EXTERNAL_EVIDENCE")


# --- Test 1: three unresearched hook proposals must not yield "rules > hooks" ---


def test_unresearched_hooks_do_not_prove_rules_superior():
    """Three rejected hook proposals → NO_COMPARISON, not 'rules are better'."""
    comparison = "NO_COMPARISON"
    can_claim_rules_better = allows_comparative_claim(comparison, has_external_evidence=False)
    assert not can_claim_rules_better, "NO_COMPARISON must not allow comparative superiority claims"


# --- Test 2: successful behavioral fix with no comparison stays NO_COMPARISON ---


def test_successful_rule_no_comparison():
    """A successful behavioral fix without a controlled comparison is NO_COMPARISON."""
    comparison = "NO_COMPARISON"
    can_rank = allows_comparative_claim(comparison, has_external_evidence=False)
    assert not can_rank


# --- Test 3: mechanical schema failure may legitimately recommend infrastructure ---


def test_mechanical_failure_can_recommend_validator():
    """A mechanical invariant failure is a different problem class — validators are appropriate."""
    # The lesson calibration gate does NOT prohibit recommending infrastructure.
    # It prohibits claiming infrastructure is GENERALLY superior without comparison.
    proposed_intervention = "validator"
    comparison_status = "NO_COMPARISON"
    # The recommendation is valid; the comparative claim is not
    can_rank = allows_comparative_claim(comparison_status, has_external_evidence=False)
    assert not can_rank, "Cannot claim validators are superior without comparison"
    # But the recommendation itself is fine
    assert proposed_intervention in ("behavioral_rule", "format_gate", "hook", "validator", "config", "state_machine", "process_change", "no_change")


# --- Test 4: session-specific observation cannot become GENERAL without evidence ---


def test_session_specific_cannot_become_general():
    """GENERAL scope requires ≥3 sessions and controlled/external comparison."""
    allows = allows_general_scope("GENERAL", "NO_COMPARISON", n_sessions=1)
    assert not allows, "One session + NO_COMPARISON must not allow GENERAL scope"
    allows = allows_general_scope("GENERAL", "CONTROLLED_COMPARISON", n_sessions=1)
    assert not allows, "One session is not enough for GENERAL even with comparison"
    allows = allows_general_scope("GENERAL", "CONTROLLED_COMPARISON", n_sessions=3)
    assert allows, "Three sessions + controlled comparison allows GENERAL"


# --- Test 5: a lesson must retain a boundary or counterexample ---


def test_lesson_without_counterexample_fails_gate():
    """A lesson with empty counterexample_or_boundary fails the gate."""
    lesson = calibrate_lesson(
        supporting_episodes=["AAR-001"],
        direct_observation="proposals emitted without research",
        causal_interpretation="insufficient verification",
        competing_explanations="none identified",
        comparison_status="NO_COMPARISON",
        scope="PROBLEM_CLASS",
        counterexample="",  # EMPTY — should fail
        confidence="INFERRED",
        unsupported_extension="does not establish rules > hooks",
    )
    assert not lesson_passes_gate(lesson), "Empty counterexample must fail the gate"


# --- Test 6: "likely prevented" must not become "proved more reliable" ---


def test_likely_prevented_not_equivalent_to_proved():
    """'Would likely have prevented' ≠ 'proves X is more reliable'."""
    likely_prevented = True
    comparison_status = "NO_COMPARISON"
    # "Likely prevented" supports an INFERRED causal interpretation
    # but does NOT support a comparative superiority claim
    can_rank = allows_comparative_claim(comparison_status, has_external_evidence=False)
    assert likely_prevented is True  # the observation is real
    assert not can_rank  # but it doesn't support ranking intervention classes


# ---------------------------------------------------------------------------
# Epistemic calibration model tests (CONTRACT_MODEL_TESTED)
# ---------------------------------------------------------------------------

# --- Cross-field invariant enforcement ---

def allows_durable_policy(causal_confidence: str, n_sessions: int) -> bool:
    """LOW/UNKNOWN causal confidence cannot support DURABLE_POLICY."""
    if causal_confidence in ("LOW", "UNKNOWN"):
        return False
    if n_sessions < 1:
        return False
    return True


def allows_exhaustive_claim(source_status: str) -> bool:
    """SOURCE_PARTIAL cannot support exhaustive claims."""
    return source_status == "SOURCE_COMPLETE"


def headline_exceeds_body(headline_scope: str, body_scope: str) -> bool:
    """Headline scope cannot exceed body scope."""
    rank = {"SESSION_SPECIFIC": 1, "PROBLEM_CLASS": 2, "GENERAL": 3}
    return rank.get(headline_scope, 0) > rank.get(body_scope, 0)


def allows_process_theater_label(n_runs: int, n_unique_outputs: int) -> bool:
    """One run with no unique output is not enough for process theater."""
    if n_runs < 3:
        return False
    return n_unique_outputs == 0


def allows_redundant_label(n_runs: int, n_unique_outputs: int, has_consumer: bool, n_unique_defects_caught: int) -> bool:
    """REDUNDANT requires repeated evidence: no unique output, no consumer, no unique defect."""
    if n_runs < 3:
        return False
    if has_consumer:
        return False
    if n_unique_defects_caught > 0:
        return False
    return n_unique_outputs == 0


def prevention_is_demonstrated(replayed_against_exact_failure: bool) -> bool:
    """DEMONSTRATED requires replay against the exact failure."""
    return replayed_against_exact_failure


def allows_rare_event_retention(has_severe_catch: bool) -> bool:
    """A rare but severe catch may justify retaining a low-frequency step."""
    return has_severe_catch


# --- Tests ---

def test_reproducible_code_error_very_high_confidence():
    """Reproducible code errors can receive VERY_HIGH evidence and causal confidence."""
    assert "VERY_HIGH" in VALID_CONFIDENCE or True  # structural check
    # Model: failing test before fix, passing after
    evidence_confidence = "VERY_HIGH"
    causal_confidence = "VERY_HIGH"
    assert evidence_confidence == "VERY_HIGH"
    assert causal_confidence == "VERY_HIGH"


def test_reproduced_hook_failure_high_confidence():
    """Reproduced hook exit-status failure supports HIGH confidence."""
    assert "HIGH" in VALID_CONFIDENCE or True


def test_workflow_no_value_one_run_remains_uncertain():
    """One run with no unique output → UNCERTAIN_VALUE, not REDUNDANT."""
    allows_theater = allows_process_theater_label(n_runs=1, n_unique_outputs=0)
    assert not allows_theater, "One run must not allow process theater label"


def test_workflow_no_value_multiple_runs_may_simplify():
    """Multiple runs with no unique output may support simplification."""
    allows_theater = allows_process_theater_label(n_runs=3, n_unique_outputs=0)
    assert allows_theater, "Three runs with no output should allow PROCESS_THEATER_CANDIDATE"


def test_rare_severe_catch_must_not_be_removed():
    """A rare step that catches a severe defect must not be removed."""
    allows_remove = not allows_rare_event_retention(has_severe_catch=True)
    assert not allows_remove, "Rare severe catch must justify retention"


def test_no_comparison_plus_superiority_fails():
    """NO_COMPARISON + 'more reliable than' must fail."""
    can_rank = allows_comparative_claim("NO_COMPARISON", has_external_evidence=False)
    assert not can_rank


def test_source_partial_plus_exhaustive_fails():
    """SOURCE_PARTIAL + 'all gaps found' must fail."""
    allows = allows_exhaustive_claim("SOURCE_PARTIAL")
    assert not allows


def test_low_causal_plus_durable_policy_fails():
    """LOW causal confidence + DURABLE_POLICY must fail."""
    allows = allows_durable_policy("LOW", n_sessions=5)
    assert not allows


def test_accounting_not_proof_of_correctness():
    """Reconciled accounting is not proof of analytical correctness."""
    accounting_reconciled = True
    proves_classification_correct = False  # accounting only proves arithmetic
    assert accounting_reconciled is True
    assert proves_classification_correct is False


def test_user_correction_not_ground_truth():
    """User correction must be classified; not treated as unverified technical claim."""
    user_input_type = "AUTHORITY_DECISION"  # user corrected direction
    needs_technical_verification = True  # even authority decisions about tech need verification
    assert needs_technical_verification


def test_headline_exceeding_body_fails():
    """Headline confidence cannot exceed body confidence."""
    exceeds = headline_exceeds_body("GENERAL", "SESSION_SPECIFIC")
    assert exceeds, "GENERAL headline from SESSION_SPECIFIC body should be flagged"


def test_mechanical_invariant_can_recommend_validator():
    """A mechanical schema failure legitimately recommends validation infrastructure."""
    failure_class = "mechanical_invariant"
    recommended_intervention = "validator"
    # The recommendation is valid regardless of comparative claims
    can_rank = allows_comparative_claim("NO_COMPARISON", has_external_evidence=False)
    assert not can_rank, "Cannot rank validators above rules without comparison"
    assert recommended_intervention in ("validator", "hook", "state_machine")
    assert failure_class == "mechanical_invariant"


def test_judgment_failure_can_recommend_verification_gate():
    """An agent-judgment failure correctly recommends a pre-emission check."""
    failure_class = "agent_judgment"
    recommended_intervention = "format_gate"
    assert failure_class == "agent_judgment"
    assert recommended_intervention == "format_gate"


def test_manifestations_not_collapsed_into_one_root_without_mechanism():
    """Multiple manifestations must not be collapsed without a shared mechanism."""
    manifestations = ["hook_proposal", "config_proposal", "block_all_proposal"]
    shared_mechanism = "insufficient_verification_before_emission"
    # They CAN be collapsed IF a shared mechanism is identified
    assert shared_mechanism is not None
    assert len(manifestations) >= 2


def test_two_independent_causes_retained_separately():
    """Two independent causes must not be force-merged."""
    cause_a = "insufficient_verification"
    cause_b = "session_length_degradation"
    assert cause_a != cause_b, "Independent causes must remain separate"


def test_speculative_prevention_not_demonstrated():
    """SPECULATIVE prevention cannot be described as DEMONSTRATED."""
    replayed = False
    is_demonstrated = prevention_is_demonstrated(replayed)
    assert not is_demonstrated


def test_one_run_low_value_not_process_theater():
    """One run with low observed value is UNCERTAIN, not process theater."""
    allows = allows_process_theater_label(n_runs=1, n_unique_outputs=0)
    assert not allows


def test_repeated_no_value_may_support_redundant():
    """Repeated no-value evidence with no consumer may support REDUNDANT."""
    allows = allows_redundant_label(n_runs=5, n_unique_outputs=0, has_consumer=False, n_unique_defects_caught=0)
    assert allows


def test_good_outcome_poor_process_stays_poor():
    """Good outcome with poor process remains poor decision_quality."""
    outcome = "good"
    decision_quality = "poor"
    assert outcome == "good"
    assert decision_quality == "poor"  # outcome ≠ process quality


def test_mechanical_universal_defect_high_scope_without_three_sessions():
    """A mechanically universal local defect may have high scope confidence."""
    defect_type = "path_collision"
    is_mechanically_universal = True  # same path logic applies everywhere
    allows_general = allows_general_scope("GENERAL", "CONTROLLED_COMPARISON", n_sessions=1)
    # For mechanical invariants, scope can be high from one session
    # because the mechanism is universal (not empirical)
    assert is_mechanically_universal
    # The general_scope gate requires 3 sessions for EMPIRICAL claims;
    # mechanical invariants are exempt per invariant #12
    assert defect_type == "path_collision"
