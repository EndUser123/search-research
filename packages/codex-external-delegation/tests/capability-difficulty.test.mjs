import test from "node:test";
import assert from "node:assert/strict";
import { BENCHMARK_MANIFEST, hashManifest } from "../benchmarks/capability-difficulty/src/manifest.mjs";
import { aggregateRuns, evaluateRun } from "../benchmarks/capability-difficulty/src/evaluate.mjs";

const binding = {
  orchestrator: "codex",
  invocation_method: "pi",
  provider: "nvidia-nim",
  model: "deepseek-ai/deepseek-v4-flash",
  route: "pi",
  verifier: "code-pool-verifier@1",
  quota_pool: "nvidia-nim",
  provider_account: "fixture-account",
  provider_scope: "dedicated-account",
};

function passingRun(runId, mutate = () => {}) {
  const run = {
    schema_version: "capability-difficulty-run.v1",
    run_id: runId,
    manifest_id: BENCHMARK_MANIFEST.manifest_id,
    manifest_sha256: BENCHMARK_MANIFEST.manifest_sha256,
    binding,
    cases: BENCHMARK_MANIFEST.cases.map((definition, index) => ({
      case_id: definition.case_id,
      attempt_id: `${runId}-case-${index + 1}`,
      execution_status: "completed",
      verification_state: "verification_passed",
      latency_ms: 100 + index,
      checks: (definition.checker.required_checks || ["objective_checker"]).map((name) => ({ name, passed: true })),
    })),
  };
  mutate(run);
  return run;
}

test("manifest has two suites, four difficulty tiers, stable IDs, and a stable hash", () => {
  assert.deepEqual(BENCHMARK_MANIFEST.suites, ["capability", "code_pool"]);
  assert.deepEqual(BENCHMARK_MANIFEST.difficulty_tiers, ["easy", "medium", "hard", "expert"]);
  assert.equal(new Set(BENCHMARK_MANIFEST.cases.map((value) => value.case_id)).size, BENCHMARK_MANIFEST.cases.length);
  assert.equal(hashManifest(BENCHMARK_MANIFEST), BENCHMARK_MANIFEST.manifest_sha256);
  assert.equal(BENCHMARK_MANIFEST.cases.length, 16);
});

test("a complete run reports quality and coverage but is not promotion evidence", () => {
  const result = evaluateRun({ run: passingRun("run-one") });
  assert.equal(result.status, "run_complete");
  assert.equal(result.overall.pass, 16);
  assert.equal(result.overall.quality_rate, 1);
  assert.equal(result.coverage.all_cases_observed, true);
  assert.equal(result.promotion.eligible, false);
});

test("ten repeated verified runs can meet the per-cell promotion floor", () => {
  const result = aggregateRuns({ runs: Array.from({ length: 10 }, (_, index) => passingRun(`run-${index + 1}`)) });
  assert.equal(result.status, "aggregate_complete");
  assert.equal(result.promotion.eligible, true);
  assert.equal(result.by_cell["code_pool|localized_patch|easy"].pass, 10);
  assert.equal(result.by_cell["capability|context_retrieval|expert"].observed, 10);
});

test("quota and transport blocks remain visible but do not become model failures", () => {
  const result = evaluateRun({
    run: passingRun("run-blocked", (run) => {
      const quotaCase = run.cases.find((value) => value.case_id.endsWith("localized_patch.easy.001"));
      quotaCase.execution_status = "failed";
      quotaCase.verification_state = "not_run";
      quotaCase.failure_class = "quota_temporary";
      const transportCase = run.cases.find((value) => value.case_id.endsWith("contract_following.easy.001"));
      transportCase.execution_status = "blocked";
      transportCase.verification_state = "not_run";
      transportCase.failure_class = "transport";
    }),
  });
  assert.equal(result.overall.pass, 14);
  assert.equal(result.overall.fail, 0);
  assert.equal(result.overall.blocked, 2);
  assert.equal(result.overall.quality_denominator, 14);
});

test("missing binding and wrong manifest hash fail closed", () => {
  const run = passingRun("run-invalid");
  run.binding = { ...binding, quota_pool: "" };
  run.manifest_sha256 = "wrong";
  const result = evaluateRun({ run });
  assert.equal(result.status, "invalid");
  assert.ok(result.errors.includes("run_manifest_hash_mismatch"));
  assert.ok(result.errors.includes("binding_quota_pool_missing"));
});

test("duplicate or unknown observations are invalid instead of silently replacing a case", () => {
  const run = passingRun("run-duplicate");
  run.cases.push({ ...run.cases[0], attempt_id: "duplicate" });
  run.cases.push({ ...run.cases[0], case_id: "not-in-manifest", attempt_id: "unknown" });
  const result = evaluateRun({ run });
  assert.equal(result.status, "partial");
  assert.equal(result.overall.invalid, 2);
  assert.equal(result.coverage.no_invalid_observations, false);
  assert.equal(result.promotion.eligible, false);
});

test("unverified completed output is excluded from quality rather than treated as pass", () => {
  const result = evaluateRun({
    run: passingRun("run-unverified", (run) => {
      const value = run.cases[0];
      value.verification_state = "not_verified";
    }),
  });
  assert.equal(result.overall.unverified, 1);
  assert.equal(result.overall.pass, 15);
  assert.equal(result.overall.quality_denominator, 15);
});

test("aggregation rejects mixing provider, method, or orchestrator evidence", () => {
  const first = passingRun("run-binding-one");
  const second = passingRun("run-binding-two", (run) => {
    run.binding = { ...run.binding, invocation_method: "http" };
  });
  const result = aggregateRuns({ runs: [first, second] });
  assert.equal(result.status, "invalid");
  assert.deepEqual(result.errors, ["mixed_binding_scope"]);
});

test("the evaluator rejects a success receipt that omits required objective checks", () => {
  const run = passingRun("run-missing-check", (value) => {
    value.cases[0].checks = [{ name: "objective_checker", passed: true }];
  });
  const result = evaluateRun({ run });
  assert.equal(result.status, "partial");
  assert.equal(result.observations[0].outcome, "invalid");
  assert.ok(result.observations[0].errors.includes("required_check_missing:keys_exact"));
  assert.equal(result.promotion.eligible, false);
});

test("malformed external manifests fail closed as structured invalid results", () => {
  const manifest = { ...BENCHMARK_MANIFEST, cases: { not: "an array" }, manifest_sha256: undefined };
  const result = evaluateRun({ manifest, run: passingRun("run-malformed-manifest") });
  assert.equal(result.status, "invalid");
  assert.ok(result.errors.includes("manifest_cases_missing"));
});
