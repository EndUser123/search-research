import { createHash } from "node:crypto";

export const MANIFEST_SCHEMA_VERSION = "capability-difficulty-manifest.v1";

export const DEFAULT_POLICY = Object.freeze({
  min_observations_per_cell: 10,
  min_verified_successes_per_cell: 10,
  require_all_difficulty_tiers: true,
});

// The manifest is intentionally small enough to review as data. A live adapter
// may render these prompts, but it must not change IDs, difficulty, or checker
// contracts after the run starts.
const CASES = [
  {
    case_id: "capability.contract_following.easy.001",
    suite: "capability",
    lane: "mechanical",
    capability: "contract_following",
    difficulty: "easy",
    prompt: "Return JSON with exactly the keys answer and confidence. Set answer to 7 and confidence to high.",
    checker: { type: "structured_json", required_keys: ["answer", "confidence"], required_checks: ["keys_exact", "values_exact"], exact: { answer: 7, confidence: "high" } },
    budget: { max_output_tokens: 80, max_latency_ms: 15000 },
  },
  {
    case_id: "capability.contract_following.medium.001",
    suite: "capability",
    lane: "mechanical",
    capability: "contract_following",
    difficulty: "medium",
    prompt: "Return the requested fields in the supplied order, omit commentary, and mark the unavailable field as unknown rather than guessing.",
    checker: { type: "structured_json", required_keys: ["name", "version", "owner", "unknown_fields"], required_checks: ["keys_exact", "unknown_field_labeled"], exact: { unknown_fields: ["owner"] } },
    budget: { max_output_tokens: 160, max_latency_ms: 20000 },
  },
  {
    case_id: "capability.contract_following.hard.001",
    suite: "capability",
    lane: "mechanical",
    capability: "contract_following",
    difficulty: "hard",
    prompt: "Produce a schema-valid decision packet that separates verified facts, inferences, and hypotheses and includes a falsifier for every hypothesis.",
    checker: { type: "structured_json", required_keys: ["facts", "inferences", "hypotheses", "falsifiers"], required_checks: ["schema_valid", "hypotheses_falsifiable"], invariant: "every_hypothesis_has_falsifier" },
    budget: { max_output_tokens: 360, max_latency_ms: 30000 },
  },
  {
    case_id: "capability.contract_following.expert.001",
    suite: "capability",
    lane: "critic",
    capability: "contract_following",
    difficulty: "expert",
    prompt: "Return a red-team report using only the declared evidence scope; unsupported claims must be labeled and action-ineligible.",
    checker: { type: "structured_json", required_keys: ["findings", "claim_ledger", "scope"], required_checks: ["scope_respected", "unsupported_non_actionable"], invariant: "unsupported_claims_are_non_actionable" },
    budget: { max_output_tokens: 640, max_latency_ms: 45000 },
  },
  {
    case_id: "capability.context_retrieval.easy.001",
    suite: "capability",
    lane: "reasoning",
    capability: "context_retrieval",
    difficulty: "easy",
    prompt: "Answer the question using the one relevant record in the provided context and cite its record ID.",
    checker: { type: "evidence", required_checks: ["answer_matches_record", "record_id_cited"] },
    budget: { max_output_tokens: 160, max_latency_ms: 20000 },
  },
  {
    case_id: "capability.context_retrieval.medium.001",
    suite: "capability",
    lane: "reasoning",
    capability: "context_retrieval",
    difficulty: "medium",
    prompt: "Reconcile two records with different timestamps, prefer the authoritative source, and state the discarded conflict.",
    checker: { type: "evidence", required_checks: ["authoritative_source_selected", "timestamp_rule_applied", "conflict_disclosed"] },
    budget: { max_output_tokens: 260, max_latency_ms: 30000 },
  },
  {
    case_id: "capability.context_retrieval.hard.001",
    suite: "capability",
    lane: "reasoning",
    capability: "context_retrieval",
    difficulty: "hard",
    prompt: "Trace a decision across a policy, an implementation note, and a receipt; identify where the evidence chain breaks.",
    checker: { type: "evidence", required_checks: ["all_artifacts_traced", "authority_order_respected", "gap_identified"] },
    budget: { max_output_tokens: 420, max_latency_ms: 45000 },
  },
  {
    case_id: "capability.context_retrieval.expert.001",
    suite: "capability",
    lane: "reasoning",
    capability: "context_retrieval",
    difficulty: "expert",
    prompt: "Construct a bounded causal explanation from the supplied artifacts, distinguish observation from inference, and name the test that would disambiguate alternatives.",
    checker: { type: "evidence", required_checks: ["causal_claims_labeled", "alternative_explanation_present", "discriminating_test_present"] },
    budget: { max_output_tokens: 640, max_latency_ms: 60000 },
  },
  {
    case_id: "code_pool.localized_patch.easy.001",
    suite: "code_pool",
    lane: "coding",
    capability: "localized_patch",
    difficulty: "easy",
    prompt: "Patch the supplied function so an empty input returns an empty array while preserving the existing non-empty behavior.",
    checker: { type: "patch_contract", required_checks: ["empty_case_passes", "existing_case_passes", "scope_is_limited"] },
    budget: { max_output_tokens: 360, max_latency_ms: 45000 },
  },
  {
    case_id: "code_pool.syntax_contract.easy.001",
    suite: "code_pool",
    lane: "coding",
    capability: "syntax_contract",
    difficulty: "easy",
    prompt: "Complete the small typed helper without changing its public signature or introducing an implicit null/undefined conversion.",
    checker: { type: "test_contract", required_checks: ["type_check_passes", "signature_preserved", "boundary_cases_pass"] },
    budget: { max_output_tokens: 360, max_latency_ms: 45000 },
  },
  {
    case_id: "code_pool.test_authoring.medium.001",
    suite: "code_pool",
    lane: "coding",
    capability: "test_authoring",
    difficulty: "medium",
    prompt: "Add regression tests for the boundary cases in the supplied parser without changing production behavior.",
    checker: { type: "test_contract", required_checks: ["boundary_cases_covered", "tests_fail_before_fix", "tests_pass_after_fix", "scope_is_limited"] },
    budget: { max_output_tokens: 640, max_latency_ms: 60000 },
  },
  {
    case_id: "code_pool.debugging_and_edge_cases.hard.001",
    suite: "code_pool",
    lane: "coding",
    capability: "debugging_and_edge_cases",
    difficulty: "hard",
    prompt: "Diagnose the failing asynchronous cache test, fix the race without adding an unbounded retry, and preserve cancellation semantics.",
    checker: { type: "test_contract", required_checks: ["race_reproduced", "race_fixed", "cancellation_preserved", "retry_bounded", "tests_pass_after_fix"] },
    budget: { max_output_tokens: 900, max_latency_ms: 90000 },
  },
  {
    case_id: "code_pool.multi_file_invariant.hard.001",
    suite: "code_pool",
    lane: "coding",
    capability: "multi_file_invariant",
    difficulty: "hard",
    prompt: "Update the serializer and deserializer together so the new field round-trips while old records remain readable.",
    checker: { type: "patch_contract", required_checks: ["new_round_trip_passes", "old_record_compatible", "schema_version_handled", "scope_is_limited"] },
    budget: { max_output_tokens: 900, max_latency_ms: 90000 },
  },
  {
    case_id: "code_pool.api_compatibility.expert.001",
    suite: "code_pool",
    lane: "coding",
    capability: "api_compatibility",
    difficulty: "expert",
    prompt: "Add a backward-compatible API option with explicit validation, deterministic errors, and no silent behavior change for existing callers.",
    checker: { type: "patch_contract", required_checks: ["old_callers_unchanged", "new_option_validated", "errors_deterministic", "negative_cases_pass", "scope_is_limited"] },
    budget: { max_output_tokens: 1200, max_latency_ms: 120000 },
  },
  {
    case_id: "code_pool.security_edge_cases.expert.001",
    suite: "code_pool",
    lane: "coding",
    capability: "security_edge_cases",
    difficulty: "expert",
    prompt: "Harden the path-handling helper against traversal and symlink escapes while preserving valid nested paths and reporting rejection reasons.",
    checker: { type: "test_contract", required_checks: ["traversal_rejected", "symlink_escape_rejected", "valid_nested_path_passes", "reason_is_actionable", "tests_pass_after_fix"] },
    budget: { max_output_tokens: 1200, max_latency_ms: 120000 },
  },
  {
    case_id: "code_pool.regression_fix.expert.001",
    suite: "code_pool",
    lane: "coding",
    capability: "regression_fix",
    difficulty: "expert",
    prompt: "Repair a regression in the request lifecycle without masking provider errors, fabricating retries, or changing the public receipt contract.",
    checker: { type: "test_contract", required_checks: ["regression_reproduced", "provider_error_preserved", "retry_not_fabricated", "receipt_contract_preserved", "tests_pass_after_fix"] },
    budget: { max_output_tokens: 1400, max_latency_ms: 150000 },
  },
];

function sortObject(value) {
  if (Array.isArray(value)) return value.map(sortObject);
  if (!value || typeof value !== "object") return value;
  return Object.fromEntries(Object.keys(value).sort().map((key) => [key, sortObject(value[key])]));
}

export function canonicalJson(value) {
  return JSON.stringify(sortObject(value));
}

export function hashManifest(manifest) {
  const content = { ...manifest };
  delete content.manifest_sha256;
  return createHash("sha256").update(canonicalJson(content), "utf8").digest("hex");
}

const baseManifest = {
  schema_version: MANIFEST_SCHEMA_VERSION,
  manifest_id: "codex-capability-difficulty-2026-08-09",
  version: 1,
  suites: ["capability", "code_pool"],
  difficulty_tiers: ["easy", "medium", "hard", "expert"],
  policy: DEFAULT_POLICY,
  cases: CASES,
};

export const BENCHMARK_MANIFEST = Object.freeze({
  ...baseManifest,
  manifest_sha256: hashManifest(baseManifest),
});

export function cloneManifest(manifest = BENCHMARK_MANIFEST) {
  return JSON.parse(JSON.stringify(manifest));
}
