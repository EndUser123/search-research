from __future__ import annotations

import sys
from pathlib import Path
from datetime import datetime, timedelta, timezone

ROOT = Path(__file__).parents[2]
sys.path.insert(0, str(ROOT))

from research_runtime.router import (  # noqa: E402
    CLOSED,
    OPEN,
    RESTRICTED,
    CapabilityRecord,
    TaskSignals,
    default_capabilities,
    recommend,
)


def test_local_context_prefers_local_and_returns_one_lane() -> None:
    result = recommend(TaskSignals(needs_local_context=True), default_capabilities())

    assert [item.lane for item in result.recommendations] == ["local"]
    assert result.stop_reason == "single_best_eligible_lane"


def test_unready_provider_is_rejected_with_reason() -> None:
    result = recommend(TaskSignals(needs_deep_source_inspection=True, explicit_lane="notebooklm"), default_capabilities())

    notebook = next(item for item in result.rejected if item.lane == "notebooklm")
    assert "runtime_not_ready" in notebook.reasons
    assert "authentication_not_verified" in notebook.reasons


def test_agy_requires_explicit_advisory_role() -> None:
    result = recommend(TaskSignals(needs_adversarial_review=True), default_capabilities())

    agy = next(item for item in result.rejected if item.lane == "agy")
    assert "advisory_lane_requires_explicit_role" in agy.reasons
    assert "restricted_lane_requires_explicit_selection" in agy.reasons
    assert "runtime_not_ready" in agy.reasons


def test_agy_can_be_recommended_only_for_explicit_advisory_review() -> None:
    now = datetime.now(timezone.utc)
    agy = CapabilityRecord(
        "agy",
        "ADVISORY_REVIEW",
        "agy",
        frozenset({"adversarial_review"}),
        circuit=RESTRICTED,
        ready=True,
        readiness_observed_at=now.isoformat(),
        readiness_valid_until=(now + timedelta(hours=1)).isoformat(),
        observation_method="bounded-runtime-check",
        authenticated=True,
        accepted_roles=frozenset({"AGY_SEARCH_ADVERSARIAL"}),
    )
    result = recommend(
        TaskSignals(needs_adversarial_review=True, explicit_lane="agy", explicit_role="AGY_SEARCH_ADVERSARIAL"),
        (agy,),
    )

    assert [item.lane for item in result.recommendations] == ["agy"]
    assert result.recommendations[0].selection_mode == "role_restricted"


def test_open_circuit_and_low_quota_are_hard_rejections() -> None:
    capabilities = (
        CapabilityRecord("blocked", "SEARCH_DISCOVERY", "x", frozenset({"current_web"}), circuit=OPEN, ready=True, authenticated=True, automatic=True),
        CapabilityRecord("low_quota", "SEARCH_DISCOVERY", "y", frozenset({"current_web"}), ready=True, authenticated=True, automatic=True, quota_remaining_percent=5, quota_reserve_percent=10),
    )

    result = recommend(TaskSignals(needs_current_web=True), capabilities)

    assert not result.recommendations
    assert "circuit_open" in next(item for item in result.rejected if item.lane == "blocked").reasons
    assert "quota_below_reserve" in next(item for item in result.rejected if item.lane == "low_quota").reasons


def test_restricted_circuit_requires_probe_signal() -> None:
    capability = CapabilityRecord("probe", "SEARCH_DISCOVERY", "x", frozenset({"current_web"}), circuit=RESTRICTED, ready=True, authenticated=True, automatic=True)

    result = recommend(TaskSignals(needs_current_web=True), (capability,))

    assert not result.recommendations


def _healthy_mmx(**overrides: object) -> CapabilityRecord:
    now = datetime.now(timezone.utc)
    values: dict[str, object] = {
        "lane": "mmx",
        "role": "SEARCH_DISCOVERY",
        "independence_group": "external_search",
        "capabilities": frozenset({"external_discovery", "current_web", "independent_recall"}),
        "ready": True,
        "authenticated": True,
        "automatic": True,
        "observation_method": "bounded-runtime-check",
        "readiness_observed_at": now.isoformat(),
        "readiness_valid_until": (now + timedelta(hours=1)).isoformat(),
        "quota_remaining_percent": 80,
        "supported_roles": frozenset({
            "BROAD_EXTERNAL_DISCOVERY", "CONCEPTUAL_RECALL",
            "EXPLORATORY_RESEARCH", "CANDIDATE_GENERATION", "GENERAL_WEB_RESEARCH",
        }),
    }
    values.update(overrides)
    return CapabilityRecord(**values)


def test_healthy_mmx_is_automatically_eligible_for_independent_discovery() -> None:
    result = recommend(
        TaskSignals(needs_current_web=True, needs_independent_recall=True),
        (_healthy_mmx(),),
    )

    assert [item.lane for item in result.recommendations] == ["mmx"]
    assert result.recommendations[0].selection_mode == "automatic"


def _healthy_brave(**overrides: object) -> CapabilityRecord:
    now = datetime.now(timezone.utc)
    values: dict[str, object] = {
        "lane": "brave",
        "role": "SEARCH_DISCOVERY",
        "independence_group": "external_search",
        "capabilities": frozenset({
            "external_discovery", "current_web", "independent_recall",
            "implementation_discovery", "authority_candidate_discovery",
        }),
        "ready": True,
        "authenticated": True,
        "automatic": True,
        "observation_method": "bounded-runtime-check",
        "readiness_observed_at": now.isoformat(),
        "readiness_valid_until": (now + timedelta(hours=1)).isoformat(),
        "supported_roles": frozenset({"IMPLEMENTATION_DISCOVERY", "AUTHORITATIVE_SOURCE_DISCOVERY"}),
    }
    values.update(overrides)
    return CapabilityRecord(**values)


def _healthy_local() -> CapabilityRecord:
    return CapabilityRecord(
        "local", "LOCAL_INSPECTION", "local",
        frozenset({"local_context", "primary_source_verification"}),
        ready=True, authenticated=True, automatic=True, authority="local",
        observation_method="harness-local",
    )


def test_authority_selects_brave_for_candidate_discovery_and_defers_authority() -> None:
    result = recommend(
        TaskSignals(
            needs_current_web=True,
            needs_primary_source_verification=True,
            requested_roles=frozenset({"AUTHORITATIVE_SOURCE_DISCOVERY"}),
        ),
        (_healthy_brave(),),
    )

    assert [item.lane for item in result.recommendations] == ["brave"]
    assert "primary_source_verification" in result.required_capabilities
    assert result.capability_satisfaction["primary_source_verification"] == ()


def test_composition_selects_minimum_local_brave_mmx_set() -> None:
    mmx = _healthy_mmx(capabilities=frozenset({"external_discovery", "conceptual_discovery"}))
    brave = _healthy_brave()
    result = recommend(
        TaskSignals(
            needs_local_context=True,
            needs_current_web=True,
            needs_independent_recall=True,
            requested_roles=frozenset({"IMPLEMENTATION_DISCOVERY", "CONCEPTUAL_RECALL"}),
            allow_parallel=True,
            parallel_trigger="distinct_complementary_roles",
        ),
        (_healthy_local(), brave, mmx),
    )

    assert set(item.lane for item in result.recommendations) == {"local", "brave", "mmx"}
    assert result.stop_reason == "bounded_parallel_wave"
    assert result.capability_satisfaction["local_context"] == ("local",)
    assert result.capability_satisfaction["implementation_discovery"] == ("brave",)
    assert result.capability_satisfaction["conceptual_discovery"] == ("mmx",)


def test_stale_readiness_is_rejected_even_when_provider_is_otherwise_healthy() -> None:
    now = datetime.now(timezone.utc)
    result = recommend(
        TaskSignals(needs_current_web=True, as_of=now.isoformat()),
        (_healthy_mmx(readiness_valid_until=(now - timedelta(minutes=1)).isoformat()),),
    )

    assert not result.recommendations
    assert "readiness_stale" in result.rejected[0].reasons


def test_sufficient_evidence_stops_without_redundant_lane() -> None:
    result = recommend(
        TaskSignals(needs_current_web=True, evidence_sufficient=True),
        (_healthy_mmx(),),
    )

    assert not result.recommendations
    assert result.stop_reason == "evidence_already_sufficient"
    assert result.rejected[0].reasons == ("evidence_already_sufficient",)


def test_recorded_agy_role_does_not_require_per_call_lane_or_human_selection() -> None:
    now = datetime.now(timezone.utc)
    agy = CapabilityRecord(
        "agy",
        "ADVISORY_REVIEW",
        "agy",
        frozenset({"adversarial_review"}),
        circuit=RESTRICTED,
        ready=True,
        authenticated=True,
        readiness_observed_at=now.isoformat(),
        readiness_valid_until=(now + timedelta(hours=1)).isoformat(),
        observation_method="bounded-runtime-check",
        accepted_roles=frozenset({"AGY_SEARCH_ADVERSARIAL"}),
    )

    result = recommend(
        TaskSignals(needs_adversarial_review=True, recorded_role="AGY_SEARCH_ADVERSARIAL"),
        (agy,),
    )

    assert [item.lane for item in result.recommendations] == ["agy"]
    assert result.recommendations[0].selection_mode == "role_restricted"
    assert not result.human_escalation


def test_agy_cannot_cross_provenance_or_high_impact_authority_boundary() -> None:
    now = datetime.now(timezone.utc)
    agy = CapabilityRecord(
        "agy",
        "ADVISORY_REVIEW",
        "agy",
        frozenset({"adversarial_review"}),
        circuit=RESTRICTED,
        ready=True,
        authenticated=True,
        readiness_observed_at=now.isoformat(),
        readiness_valid_until=(now + timedelta(hours=1)).isoformat(),
        observation_method="bounded-runtime-check",
        accepted_roles=frozenset({"AGY_SEARCH_ADVERSARIAL"}),
    )

    result = recommend(
        TaskSignals(
            needs_adversarial_review=True,
            needs_provenance_binding=True,
            decision_impact="high",
            recorded_role="AGY_SEARCH_ADVERSARIAL",
        ),
        (agy,),
    )

    assert not result.recommendations
    reasons = result.rejected[0].reasons
    assert "provenance_binding_unproven" in reasons
    assert "advisory_authority_boundary" in reasons
    assert result.human_escalation
