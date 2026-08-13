import { join } from "node:path";
import { fileURLToPath } from "node:url";

export const FIXTURE_SCHEMA_VERSION = "capability-difficulty-fixtures.v1";

const FIXTURE_ROOT = join(fileURLToPath(new URL("..", import.meta.url)), "fixtures");

const CASE_FIXTURES = {
  "code_pool.localized_patch.easy.001": {
    directory: "localized-patch",
    entrypoint: "normalize.mjs",
    allowed_paths: ["normalize.mjs"],
    instruction: "Edit fixtures/localized-patch/normalize.mjs. Export normalizeItems(values). The hidden parent checker calls it with [] and with [' a ', 'b']; preserve trimming for non-empty input and return [] for empty input.",
  },
  "code_pool.syntax_contract.easy.001": {
    directory: "syntax-contract",
    entrypoint: "label.mjs",
    allowed_paths: ["label.mjs"],
    instruction: "Edit fixtures/syntax-contract/label.mjs. Preserve the exported toLabel(value) signature. The explicit contract is: null and undefined become 'unknown', numbers stringify without implicit null conversion, and ordinary strings are returned unchanged.",
  },
  "code_pool.test_authoring.medium.001": {
    directory: "test-authoring",
    entrypoint: "parser.mjs",
    allowed_paths: ["parser.test.mjs"],
    instruction: "Add fixtures/test-authoring/parser.test.mjs without changing parser.mjs. Cover empty input, surrounding whitespace, and an escaped comma. The hidden parent checker independently verifies the parser behavior and that the added tests are real node:test tests.",
  },
  "code_pool.debugging_and_edge_cases.hard.001": {
    directory: "debugging-and-edge-cases",
    entrypoint: "cache.mjs",
    allowed_paths: ["cache.mjs"],
    instruction: "Edit fixtures/debugging-and-edge-cases/cache.mjs. AsyncCache.get(key, loader, options) must share an in-flight load for concurrent callers, cache only fulfilled values, and reject an aborted caller without caching a failed load.",
  },
  "code_pool.multi_file_invariant.hard.001": {
    directory: "multi-file-invariant",
    entrypoint: "serializer.mjs",
    allowed_paths: ["serializer.mjs", "deserializer.mjs"],
    instruction: "Edit fixtures/multi-file-invariant/serializer.mjs and deserializer.mjs together. Version 2 records must round-trip the priority field, while version 1 records remain readable with priority 0.",
  },
  "code_pool.api_compatibility.expert.001": {
    directory: "api-compatibility",
    entrypoint: "api.mjs",
    allowed_paths: ["api.mjs"],
    instruction: "Edit fixtures/api-compatibility/api.mjs. Preserve createRequest(path) for existing callers, add an optional timeoutMs option, reject invalid paths and timeoutMs values with deterministic error classes/messages, and do not silently coerce invalid input.",
  },
  "code_pool.security_edge_cases.expert.001": {
    directory: "security-edge-cases",
    entrypoint: "safe-path.mjs",
    allowed_paths: ["safe-path.mjs"],
    instruction: "Edit fixtures/security-edge-cases/safe-path.mjs. Export async resolveSafePath(root, requested). Permit valid nested paths, reject traversal, and reject a path whose real target escapes root through a symlink. Return actionable rejection reasons.",
  },
  "code_pool.regression_fix.expert.001": {
    directory: "regression-fix",
    entrypoint: "lifecycle.mjs",
    allowed_paths: ["lifecycle.mjs"],
    instruction: "Edit fixtures/regression-fix/lifecycle.mjs. Export async executeRequest(send). Preserve the success receipt shape, preserve provider error name/message/code on failure, report attempt 1, and never fabricate a retry.",
  },
};

const CASE_CONTEXT = {
  "capability.contract_following.medium.001": {
    input: {
      requested_order: ["name", "version", "owner", "unknown_fields"],
      record: { name: "relay", version: "2", owner: null },
    },
    expected: { name: "relay", version: "2", owner: null, unknown_fields: ["owner"] },
  },
  "capability.context_retrieval.easy.001": {
    records: [{ id: "record-001", answer: "the quota window is five hours", authority: "runbook" }],
    question: "What is the quota window?",
    expected_record_id: "record-001",
    expected_answer: "the quota window is five hours",
    response_contract: { required: ["answer", "record_id"], exact: { answer: "the quota window is five hours", record_id: "record-001" } },
  },
  "capability.context_retrieval.medium.001": {
    records: [
      { id: "status-older", timestamp: "2026-08-08T10:00:00Z", source: "mirror", value: "degraded" },
      { id: "status-authoritative", timestamp: "2026-08-08T09:00:00Z", source: "provider-status", value: "operational" },
    ],
    rule: "provider-status is authoritative over mirror, even when its timestamp is older",
    expected_source: "provider-status",
    expected_discarded_id: "status-older",
    response_contract: { required: ["selected_source", "discarded_record_id", "rule_applied", "conflict_disclosed"], exact: { selected_source: "provider-status", discarded_record_id: "status-older" } },
  },
  "capability.context_retrieval.hard.001": {
    artifacts: [
      { id: "policy-17", kind: "policy", authority: 1, says: "retry only after retry_after" },
      { id: "note-4", kind: "implementation_note", authority: 2, says: "runner records retry_after" },
      { id: "receipt-9", kind: "receipt", authority: 3, says: "retry_after is absent" },
    ],
    expected_gap: "receipt-9 does not prove that the runner emitted retry_after",
    response_contract: { required: ["trace", "gap"], trace_ids: ["policy-17", "note-4", "receipt-9"] },
  },
  "capability.context_retrieval.expert.001": {
    artifacts: [
      { id: "a", observation: "request returned 429" },
      { id: "b", observation: "provider reset is five hours away" },
    ],
    expected_alternatives: ["temporary quota", "route retirement"],
    expected_test: "reprobe after retry_after and inspect provider model availability",
    response_contract: { required: ["observations", "inference", "alternatives", "discriminating_test"], alternatives: ["temporary quota", "route retirement"] },
  },
};

export function fixtureForCase(caseId) {
  const value = CASE_FIXTURES[caseId];
  return value ? JSON.parse(JSON.stringify(value)) : null;
}

export function contextForCase(caseId) {
  const value = CASE_CONTEXT[caseId];
  return value ? JSON.parse(JSON.stringify(value)) : null;
}

export function fixtureRoot() {
  return FIXTURE_ROOT;
}

export function fixtureDirectory(caseId, root = FIXTURE_ROOT) {
  const value = CASE_FIXTURES[caseId];
  return value ? join(root, value.directory) : null;
}

export function allFixtureCaseIds() {
  return Object.keys(CASE_FIXTURES).sort();
}
