"""Deterministic, provider-neutral research-lane recommendations.

This module only recommends lanes. It never probes, invokes, authenticates, or
falls back between providers. Readiness, quota, and circuit state are explicit
inputs supplied by the current harness.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Iterable


CLOSED = "CLOSED"
RESTRICTED = "RESTRICTED"
OPEN = "OPEN"
PROBE = "PROBE"
VALID_CIRCUITS = {CLOSED, RESTRICTED, OPEN, PROBE}

ROLE_BROAD_DISCOVERY = "BROAD_EXTERNAL_DISCOVERY"
ROLE_CONCEPTUAL_RECALL = "CONCEPTUAL_RECALL"
ROLE_EXPLORATORY_RESEARCH = "EXPLORATORY_RESEARCH"
ROLE_CANDIDATE_GENERATION = "CANDIDATE_GENERATION"
ROLE_GENERAL_WEB = "GENERAL_WEB_RESEARCH"
ROLE_IMPLEMENTATION = "IMPLEMENTATION_DISCOVERY"
ROLE_AUTHORITY = "AUTHORITATIVE_SOURCE_DISCOVERY"
ROLE_REPOSITORY = "REPOSITORY_PROJECT_DISCOVERY"
ROLE_MAINTENANCE = "MAINTENANCE_STATUS"
ROLE_COMPATIBILITY = "COMPATIBILITY_RESEARCH"
ROLE_OMISSION = "OMISSION_SENSITIVE_DISCOVERY"
ROLE_LOCAL = "LOCAL_CONTEXT"
ROLE_SEMANTIC = "SEMANTIC_EXTERNAL_DISCOVERY"
ROLE_INDEPENDENT_INDEX = "INDEPENDENT_INDEX_DISCOVERY"
PARALLEL_TRIGGERS = frozenset({
    "distinct_complementary_roles", "omission_risk", "consequential_decision",
    "independent_index_coverage", "supporting_and_limiting_evidence",
})

ROLE_CAPABILITIES = {
    ROLE_BROAD_DISCOVERY: "broad_discovery",
    ROLE_CONCEPTUAL_RECALL: "conceptual_discovery",
    ROLE_EXPLORATORY_RESEARCH: "conceptual_discovery",
    ROLE_CANDIDATE_GENERATION: "candidate_generation",
    ROLE_GENERAL_WEB: "external_discovery",
    ROLE_IMPLEMENTATION: "implementation_discovery",
    ROLE_AUTHORITY: "authority_candidate_discovery",
    ROLE_REPOSITORY: "repository_discovery",
    ROLE_MAINTENANCE: "maintenance_discovery",
    ROLE_COMPATIBILITY: "compatibility_discovery",
    ROLE_OMISSION: "omission_sensitive_discovery",
    ROLE_SEMANTIC: "semantic_external_discovery",
    ROLE_INDEPENDENT_INDEX: "independent_index_discovery",
}


@dataclass(frozen=True)
class CapabilityRecord:
    lane: str
    role: str
    independence_group: str
    capabilities: frozenset[str]
    circuit: str = CLOSED
    ready: bool = False
    authenticated: bool = False
    automatic: bool = False
    authority: str = "advisory"
    quota_remaining_percent: float | None = None
    quota_reserve_percent: float = 10.0
    readiness_observed_at: str | None = None
    readiness_valid_until: str | None = None
    observation_method: str | None = None
    recent_anomaly: bool = False
    recent_verified_value: str | None = None
    integrity: str = "unknown"
    accepted_roles: frozenset[str] = frozenset()
    supported_roles: frozenset[str] = frozenset()


@dataclass(frozen=True)
class TaskSignals:
    needs_local_context: bool = False
    needs_current_web: bool = False
    needs_primary_source_verification: bool = False
    needs_independent_recall: bool = False
    needs_adversarial_review: bool = False
    needs_deep_source_inspection: bool = False
    needs_extraction: bool = False
    needs_fixed_corpus_synthesis: bool = False
    decision_impact: str = "low"
    sensitivity: str = "normal"
    reversibility: str = "reversible"
    authorization_level: str = "none"
    explicit_lane: str | None = None
    explicit_role: str | None = None
    recorded_role: str | None = None
    agent_selected: bool = False
    human_authorized: bool = False
    evidence_sufficient: bool = False
    attempted_lanes: frozenset[str] = frozenset()
    failed_lanes: frozenset[str] = frozenset()
    needs_provenance_binding: bool = False
    broad_or_long_context: bool = False
    high_cost_model: bool = False
    circuit_override: bool = False
    as_of: str | None = None
    probe: bool = False
    requested_roles: frozenset[str] = frozenset()
    allow_parallel: bool = False
    parallel_trigger: str | None = None
    conditional_lane_trigger: str | None = None


@dataclass(frozen=True)
class LaneDecision:
    lane: str
    eligible: bool
    score: int
    reasons: tuple[str, ...]
    selection_mode: str
    satisfies: frozenset[str] = frozenset()


@dataclass(frozen=True)
class RoutingRecommendation:
    recommendations: tuple[LaneDecision, ...]
    rejected: tuple[LaneDecision, ...]
    stop_reason: str
    human_escalation: bool = False
    escalation_reasons: tuple[str, ...] = ()
    required_capabilities: tuple[str, ...] = ()
    capability_satisfaction: dict[str, tuple[str, ...]] | None = None


def _requested_capabilities(signals: TaskSignals) -> set[str]:
    requested: set[str] = set()
    if signals.needs_local_context:
        requested.add("local_context")
    if signals.needs_current_web:
        requested.add("external_discovery")
    if signals.needs_independent_recall:
        requested.add("independent_recall")
    if signals.needs_adversarial_review:
        requested.add("adversarial_review")
    if signals.needs_deep_source_inspection:
        requested.add("deep_source_inspection")
    if signals.needs_extraction:
        requested.add("extraction")
    if signals.needs_fixed_corpus_synthesis:
        requested.add("fixed_corpus_synthesis")
    requested.update(
        ROLE_CAPABILITIES[role]
        for role in signals.requested_roles
        if role in ROLE_CAPABILITIES
    )
    return requested


def required_capabilities(signals: TaskSignals) -> tuple[str, ...]:
    """Return the full evidence requirements, including post-open authority."""

    required = _requested_capabilities(signals)
    if signals.needs_primary_source_verification:
        required.add("primary_source_verification")
    required.update({"source_opening", "evidence_assessment"})
    return tuple(sorted(required))


def _parse_time(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)
    except ValueError:
        return None


def _readiness_reason(capability: CapabilityRecord, signals: TaskSignals) -> str | None:
    if not capability.ready:
        return "runtime_not_ready"
    if not capability.observation_method:
        return "readiness_observation_missing"
    observed = _parse_time(capability.readiness_observed_at)
    valid_until = _parse_time(capability.readiness_valid_until)
    if capability.lane not in {"local", "native_web"} and observed is None:
        return "readiness_observation_missing"
    if capability.readiness_valid_until and valid_until is None:
        return "readiness_expiry_invalid"
    as_of = _parse_time(signals.as_of) or datetime.now(timezone.utc)
    if valid_until and as_of >= valid_until:
        return "readiness_stale"
    return None


def _decision(capability: CapabilityRecord, signals: TaskSignals) -> LaneDecision:
    reasons: list[str] = []
    requested = _requested_capabilities(signals)
    ddg_conditional = capability.lane == "duckduckgo" and signals.conditional_lane_trigger in {
        "conflicting_sources", "omission_risk", "high_consequence", "insufficient_after_primary",
    }
    selection_mode = "conditional" if ddg_conditional else "automatic" if capability.automatic else "explicit"
    if capability.role == "ADVISORY_REVIEW":
        selection_mode = "role_restricted"

    if capability.circuit not in VALID_CIRCUITS:
        reasons.append("invalid_circuit_state")
    elif capability.circuit == OPEN:
        reasons.append("circuit_open")
    elif capability.circuit == PROBE and not signals.probe:
        reasons.append("probe_only_without_probe_signal")
    elif capability.circuit == RESTRICTED and signals.explicit_lane != capability.lane and not ddg_conditional:
        role = signals.recorded_role or signals.explicit_role
        role_recorded = capability.role == "ADVISORY_REVIEW" and role in capability.accepted_roles
        if not role_recorded:
            reasons.append("restricted_lane_requires_explicit_selection")
    readiness_reason = _readiness_reason(capability, signals)
    if readiness_reason:
        reasons.append(readiness_reason)
    if not capability.authenticated:
        reasons.append("authentication_not_verified")
    if capability.recent_anomaly:
        reasons.append("recent_runtime_anomaly")
    if capability.quota_remaining_percent is not None and capability.quota_remaining_percent < capability.quota_reserve_percent:
        reasons.append("quota_below_reserve")
    if signals.sensitivity in {"sensitive", "credentialed"} and capability.authority != "local":
        reasons.append("sensitive_task_requires_local_lane")
    if signals.authorization_level in {"pilot", "production", "implementation"}:
        reasons.append("routing_only_supports_evidence_gathering")
    if capability.lane in signals.attempted_lanes:
        reasons.append("lane_already_attempted")
    if capability.lane in signals.failed_lanes:
        reasons.append("prior_lane_failure_remains_visible")
    if capability.role == "ADVISORY_REVIEW":
        role = signals.recorded_role or signals.explicit_role
        if role not in capability.accepted_roles:
            reasons.append("advisory_lane_requires_explicit_role")
        if signals.needs_provenance_binding:
            reasons.append("provenance_binding_unproven")
        if signals.decision_impact in {"high", "critical"}:
            reasons.append("advisory_authority_boundary")
    if signals.requested_roles:
        if not capability.supported_roles.intersection(signals.requested_roles):
            if capability.lane != "local":
                reasons.append("missing_requested_role")
    elif capability.lane == "brave":
        reasons.append("role_signal_required")
    if not capability.automatic and capability.role != "ADVISORY_REVIEW" and not signals.agent_selected and signals.explicit_lane != capability.lane and not ddg_conditional:
        reasons.append("lane_requires_explicit_selection")
    # Capability gaps are resolved by composition in recommend(). They are
    # retained in satisfies metadata instead of rejecting a complementary lane.
    satisfies = frozenset(requested & capability.capabilities)

    eligible = not reasons
    score = len(satisfies) * 10
    if signals.needs_local_context and capability.lane == "local":
        score += 100
    if signals.needs_current_web and capability.lane == "native_web":
        score += 100
    if signals.needs_primary_source_verification and "primary_source_verification" in capability.capabilities:
        score += 40
    if signals.needs_independent_recall and "independent_recall" in capability.capabilities:
        score += 30
    if signals.needs_adversarial_review and capability.role == "ADVISORY_REVIEW":
        score += 30
    if signals.needs_fixed_corpus_synthesis and capability.lane == "notebooklm":
        score += 100
    if capability.authority == "authoritative":
        score += 10
    return LaneDecision(capability.lane, eligible, score, tuple(reasons), selection_mode, satisfies)


def recommend(signals: TaskSignals, capabilities: Iterable[CapabilityRecord]) -> RoutingRecommendation:
    """Return stable recommendations and explicit rejection reasons.

    The first recommendation is the default. A second lane is returned only
    for an explicit deterministic parallel trigger and two eligible roles.
    """

    decisions = [_decision(capability, signals) for capability in capabilities]
    required = _requested_capabilities(signals)
    escalation_reasons: list[str] = []
    if signals.evidence_sufficient:
        decisions = [LaneDecision(item.lane, False, item.score, ("evidence_already_sufficient",), item.selection_mode, item.satisfies) for item in decisions]
    if not signals.human_authorized:
        if signals.sensitivity in {"sensitive", "credentialed", "write"}:
            escalation_reasons.append("sensitive_or_write_boundary")
        if signals.high_cost_model:
            escalation_reasons.append("high_cost_model")
        if signals.broad_or_long_context:
            escalation_reasons.append("broad_or_long_context")
        if signals.circuit_override:
            escalation_reasons.append("circuit_override")
        if signals.decision_impact in {"high", "critical"} and (signals.needs_adversarial_review or signals.needs_provenance_binding):
            escalation_reasons.append("authority_bearing_advisory_reliance")
    eligible = sorted((item for item in decisions if item.eligible), key=lambda item: (-item.score, item.lane))
    if signals.explicit_lane:
        # An explicit provider/lane is a hard boundary.  Never broaden to a
        # different provider merely because the requested role is unsupported.
        eligible = [item for item in eligible if item.lane == signals.explicit_lane]
    selected: list[LaneDecision] = []
    covered: set[str] = set()
    for item in eligible:
        contribution = set(item.satisfies) - covered
        if contribution:
            selected.append(item)
            covered.update(contribution)
        if covered >= required:
            break
    if signals.explicit_lane and covered < required:
        # An explicit lane request must not silently broaden into a partial
        # composition when that lane cannot satisfy the requested envelope.
        selected = []
    parallel_requested = signals.allow_parallel and signals.parallel_trigger in PARALLEL_TRIGGERS
    if len(selected) > 1 and not parallel_requested:
        # Composition is bounded: without an existing parallel trigger, keep
        # the historical single-lane behavior and leave the remainder
        # unresolved rather than invoking extra providers.
        selected = selected[:1]
    if not required:
        selected = []
    elif covered < required:
        # A lane plan that leaves a required capability uncovered is not a
        # minimum-sufficient plan. Preserve the gap instead of executing a
        # misleading partial wave.
        selected = []
    recommendations = tuple(selected)
    selected_lanes = {item.lane for item in recommendations}
    rejected_items: list[LaneDecision] = []
    for item in decisions:
        if not item.eligible:
            rejected_items.append(item)
        elif item.lane not in selected_lanes:
            rejected_items.append(LaneDecision(item.lane, False, item.score, ("no_missing_capability",), item.selection_mode, item.satisfies))
    rejected = tuple(sorted(rejected_items, key=lambda item: item.lane))
    parallel_allowed = parallel_requested and len(recommendations) >= 2
    if not recommendations and any("quota_below_reserve" in item.reasons for item in decisions):
        escalation_reasons.append("quota_below_reserve")
    if signals.evidence_sufficient:
        stop_reason = "evidence_already_sufficient"
    else:
        if not recommendations:
            stop_reason = "no_eligible_lane"
        elif parallel_allowed:
            stop_reason = "bounded_parallel_wave"
        else:
            stop_reason = "single_best_eligible_lane"
    satisfaction = {
        capability: (
            ("phase1",)
            if capability in {"source_opening", "evidence_assessment"}
            else tuple(item.lane for item in recommendations if capability in item.satisfies)
        )
        for capability in required_capabilities(signals)
    }
    return RoutingRecommendation(
        recommendations,
        rejected,
        stop_reason,
        bool(escalation_reasons),
        tuple(escalation_reasons),
        required_capabilities(signals),
        satisfaction,
    )


def default_capabilities() -> tuple[CapabilityRecord, ...]:
    """Return conservative records without performing live capability probes."""

    return (
        CapabilityRecord("local", "LOCAL_INSPECTION", "local", frozenset({"local_context", "primary_source_verification", "deep_source_inspection", "extraction"}), ready=True, authenticated=True, automatic=True, authority="local", observation_method="harness-local", supported_roles=frozenset({ROLE_LOCAL})),
        CapabilityRecord("native_web", "SEARCH_DISCOVERY", "native_web", frozenset({"external_discovery", "current_web", "primary_source_verification", "independent_recall", "deep_source_inspection"}), ready=True, authenticated=True, automatic=True, authority="authoritative", observation_method="harness-native"),
        CapabilityRecord("mmx", "SEARCH_DISCOVERY", "external_search", frozenset({"external_discovery", "current_web", "independent_recall", "broad_discovery", "conceptual_discovery", "candidate_generation"}), ready=False, authenticated=False, automatic=True, authority="advisory", observation_method="not-observed", supported_roles=frozenset({ROLE_BROAD_DISCOVERY, ROLE_CONCEPTUAL_RECALL, ROLE_EXPLORATORY_RESEARCH, ROLE_CANDIDATE_GENERATION, ROLE_GENERAL_WEB})),
        CapabilityRecord("brave", "SEARCH_DISCOVERY", "external_search", frozenset({"external_discovery", "current_web", "independent_recall", "implementation_discovery", "repository_discovery", "maintenance_discovery", "compatibility_discovery", "authority_candidate_discovery", "omission_sensitive_discovery"}), ready=False, authenticated=False, automatic=True, authority="advisory", observation_method="not-observed", supported_roles=frozenset({ROLE_IMPLEMENTATION, ROLE_AUTHORITY, ROLE_REPOSITORY, ROLE_MAINTENANCE, ROLE_COMPATIBILITY, ROLE_OMISSION})),
        CapabilityRecord("notebooklm", "DEEP_SOURCE_INSPECTION", "source_grounded", frozenset({"deep_source_inspection", "extraction", "primary_source_verification", "fixed_corpus_synthesis"}), ready=False, authenticated=False, authority="advisory", observation_method="not-observed"),
        CapabilityRecord("agy", "ADVISORY_REVIEW", "agy", frozenset({"independent_recall", "deep_source_inspection", "adversarial_review"}), circuit=RESTRICTED, ready=False, authenticated=False, authority="advisory", observation_method="not-observed", accepted_roles=frozenset({"AGY_SEARCH_INDEPENDENT", "AGY_SEARCH_DEEP", "AGY_SEARCH_ADVERSARIAL"})),
        CapabilityRecord("exa", "SEARCH_DISCOVERY", "exa", frozenset({"external_discovery", "semantic_external_discovery", "conceptual_discovery"}), circuit=CLOSED, ready=False, authenticated=False, automatic=True, authority="advisory", observation_method="not-observed", supported_roles=frozenset({ROLE_SEMANTIC, ROLE_CONCEPTUAL_RECALL, ROLE_EXPLORATORY_RESEARCH})),
        CapabilityRecord("duckduckgo", "SEARCH_DISCOVERY", "duckduckgo", frozenset({"external_discovery", "independent_index_discovery", "independent_recall", "broad_discovery"}), circuit=RESTRICTED, ready=False, authenticated=False, authority="advisory", observation_method="not-observed", supported_roles=frozenset({ROLE_INDEPENDENT_INDEX, ROLE_BROAD_DISCOVERY, ROLE_GENERAL_WEB})),
    )
