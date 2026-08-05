export const ROLES = Object.freeze([
  "BOUNDED_EXECUTION",
  "SEARCH_DISCOVERY",
  "ADVISORY_REVIEW",
  "SPECIALIST_EXPLICIT",
  "CODEX_NATIVE",
]);

export const LANE_REGISTRY = Object.freeze({
  opencode: Object.freeze({
    role: "BOUNDED_EXECUTION",
    lane: "opencode",
    automatic_eligibility: "not_enabled",
    selection_mode: "explicit",
    identity_requirement: "requested_worker_model_agent_and_runtime_must_match",
    containment_requirement: "read_only_or_isolated_write_scope",
    failure_behavior: "halt_no_automatic_fallback",
    verification_requirement: "codex_independent_verification_required",
    capability_probe: "external-delegation check --worker opencode",
    adapter: "opencode",
    status: "available_explicit_alternative",
  }),
  mmx: Object.freeze({
    role: "SEARCH_DISCOVERY",
    lane: "mmx",
    automatic_eligibility: "not_enabled",
    selection_mode: "explicit",
    identity_requirement: "provider_and_model_must_be_recorded",
    containment_requirement: "read_only_external_retrieval",
    failure_behavior: "record_failure_require_fresh_routing_decision",
    verification_requirement: "source_and_provenance_validation",
    capability_probe: "not_implemented",
    adapter: null,
    status: "capability_only",
  }),
  agy: Object.freeze({
    role: "ADVISORY_REVIEW",
    lane: "agy",
    automatic_eligibility: "not_enabled",
    selection_mode: "explicit_advisory",
    identity_requirement: "actual_gemini_model_and_trajectory_binding_required",
    containment_requirement: "read_only_until_isolated_execution_proven",
    failure_behavior: "reviewer_unavailable_or_gate_incomplete_no_self_review_substitution",
    verification_requirement: "codex_must_validate_each_finding",
    capability_probe: "agy --version; agy models; authenticated read_only smoke",
    adapter: null,
    status: "advisory_manual_identity_unproven",
  }),
  pi: Object.freeze({
    role: "BOUNDED_EXECUTION",
    lane: "pi",
    automatic_eligibility: "candidate",
    selection_mode: "automatic",
    identity_requirement: "requested_worker_and_model_must_match",
    containment_requirement: "read_only_or_isolated_write_scope",
    failure_behavior: "halt_no_automatic_fallback",
    verification_requirement: "codex_independent_verification_required",
    capability_probe: "external-delegation check --worker pi",
    adapter: "pi",
    status: "available_candidate",
  }),
  codex_native: Object.freeze({
    role: "CODEX_NATIVE",
    lane: "codex_native",
    automatic_eligibility: "available",
    selection_mode: "native",
    identity_requirement: "codex_runtime_identity",
    containment_requirement: "parent_owned",
    failure_behavior: "parent_owned",
    verification_requirement: "parent_owned",
    capability_probe: "native_codex_runtime",
    adapter: null,
    status: "available",
  }),
});

export function getLane(lane) {
  return LANE_REGISTRY[lane] || null;
}

export function registrySnapshot() {
  return Object.fromEntries(Object.entries(LANE_REGISTRY).map(([key, value]) => [key, { ...value }]));
}
