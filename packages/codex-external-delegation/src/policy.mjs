import { getLane } from "./registry.mjs";

const NON_DELEGABLE_REASONS = Object.freeze({
  ambiguous: "objective_or_scope_ambiguous",
  architecture: "architectural_judgment_required",
  security: "security_judgment_required",
  missing_verification: "independent_verification_missing",
  missing_scope: "relevant_scope_missing",
});

export function classifyTask(input = {}) {
  const requestedRole = input.requested_role || null;
  if (requestedRole === "ADVISORY_REVIEW") {
    return { role: requestedRole, lane: "agy", eligible: false, selection_mode: "explicit_advisory", reason: "agy_advisory_not_automatic" };
  }
  if (requestedRole === "SEARCH_DISCOVERY") {
    return { role: requestedRole, lane: "mmx", eligible: false, selection_mode: "explicit", reason: "mmx_adapter_not_proven" };
  }
  if (requestedRole === "SPECIALIST_EXPLICIT") {
    return { role: requestedRole, lane: "pi", eligible: false, selection_mode: "explicit", reason: "pi_requires_explicit_selection" };
  }

  const checks = [
    [typeof input.objective === "string" && input.objective.trim().length > 0, NON_DELEGABLE_REASONS.missing_scope],
    [Array.isArray(input.allowed_paths) && input.allowed_paths.length > 0, NON_DELEGABLE_REASONS.missing_scope],
    [Array.isArray(input.verification_commands) && input.verification_commands.length > 0, NON_DELEGABLE_REASONS.missing_verification],
    [input.requested_worker ? (typeof (input.model || input.requested_model) === "string" && (input.model || input.requested_model).trim().length > 0) : true, "requested_worker_model_missing"],
    [input.ambiguity !== "high", NON_DELEGABLE_REASONS.ambiguous],
    [input.needs_architecture !== true, NON_DELEGABLE_REASONS.architecture],
    [input.needs_security_judgment !== true, NON_DELEGABLE_REASONS.security],
  ];
  const failed = checks.find(([ok]) => !ok);
  if (failed) {
    return { role: "CODEX_NATIVE", lane: "codex_native", eligible: false, selection_mode: "parent_owned", reason: failed[1] };
  }

  const lane = getLane("pi");
  return {
    role: "BOUNDED_EXECUTION",
    lane: "pi",
    eligible: lane.automatic_eligibility === "candidate",
    selection_mode: lane.selection_mode,
    reason: "bounded_low_ambiguity_task_with_deterministic_verification",
  };
}
