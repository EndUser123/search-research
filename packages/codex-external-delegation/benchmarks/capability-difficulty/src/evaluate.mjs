import { BENCHMARK_MANIFEST, DEFAULT_POLICY, MANIFEST_SCHEMA_VERSION, hashManifest } from "./manifest.mjs";

const REQUIRED_BINDING_FIELDS = [
  "orchestrator",
  "invocation_method",
  "provider",
  "model",
  "route",
  "verifier",
  "quota_pool",
  "provider_account",
  "provider_scope",
];

const EXECUTION_STATUSES = new Set(["completed", "failed", "blocked", "not_run"]);
const VERIFICATION_STATES = new Set(["verification_passed", "verification_failed", "not_verified", "not_run"]);

function finiteNonNegative(value) {
  return Number.isFinite(Number(value)) && Number(value) >= 0;
}

function bindingErrors(binding) {
  if (!binding || typeof binding !== "object") return ["binding_missing"];
  return REQUIRED_BINDING_FIELDS
    .filter((field) => typeof binding[field] !== "string" || binding[field].trim() === "")
    .map((field) => `binding_${field}_missing`);
}

function sameBinding(left, right) {
  return REQUIRED_BINDING_FIELDS.every((field) => left?.[field] === right?.[field]);
}

function cellKey(caseDefinition) {
  return `${caseDefinition.suite}|${caseDefinition.capability}|${caseDefinition.difficulty}`;
}

function emptyCounts() {
  return {
    total: 0,
    observed: 0,
    pass: 0,
    fail: 0,
    unverified: 0,
    blocked: 0,
    not_run: 0,
    invalid: 0,
    quality_denominator: 0,
    quality_rate: null,
    wilson_lower_bound_95: null,
  };
}

function wilsonLowerBound(successes, trials, z = 1.645) {
  if (!Number.isInteger(successes) || !Number.isInteger(trials) || trials <= 0) return null;
  const phat = successes / trials;
  const z2 = z * z;
  const denominator = 1 + z2 / trials;
  const center = phat + z2 / (2 * trials);
  const spread = z * Math.sqrt((phat * (1 - phat) / trials) + (z2 / (4 * trials * trials)));
  return Math.max(0, (center - spread) / denominator);
}

function summarize(observations, definitions) {
  const summary = emptyCounts();
  summary.total = definitions.length;
  for (const observation of observations) {
    summary.observed += 1;
    summary[observation.outcome] += 1;
    if (observation.outcome === "pass" || observation.outcome === "fail") summary.quality_denominator += 1;
  }
  if (summary.quality_denominator > 0) {
    summary.quality_rate = summary.pass / summary.quality_denominator;
    summary.wilson_lower_bound_95 = wilsonLowerBound(summary.pass, summary.quality_denominator);
  }
  return summary;
}

function groupSummary(definitions, observations, groupBy) {
  const definitionsByGroup = new Map();
  const observationsByGroup = new Map();
  for (const definition of definitions) {
    const key = groupBy(definition);
    if (!definitionsByGroup.has(key)) definitionsByGroup.set(key, []);
    definitionsByGroup.get(key).push(definition);
  }
  for (const observation of observations) {
    const definition = definitions.find((candidate) => candidate.case_id === observation.case_id);
    if (!definition) continue;
    const key = groupBy(definition);
    if (!observationsByGroup.has(key)) observationsByGroup.set(key, []);
    observationsByGroup.get(key).push(observation);
  }
  return Object.fromEntries([...definitionsByGroup.entries()].sort(([a], [b]) => a.localeCompare(b)).map(([key, groupDefinitions]) => [
    key,
    summarize(observationsByGroup.get(key) || [], groupDefinitions),
  ]));
}

function validateChecks(raw, definition) {
  if (!Array.isArray(raw.checks) || raw.checks.length === 0) return ["checks_missing"];
  const errors = raw.checks.flatMap((check, index) => {
    if (!check || typeof check !== "object" || typeof check.name !== "string" || typeof check.passed !== "boolean") {
      return [`check_${index}_malformed`];
    }
    return [];
  });
  const names = new Set(raw.checks.filter((check) => check && typeof check.name === "string").map((check) => check.name));
  for (const required of definition.checker?.required_checks || []) {
    if (!names.has(required)) errors.push(`required_check_missing:${required}`);
  }
  return errors;
}

export function evaluateObservation(raw, definition) {
  const errors = [];
  if (!raw || typeof raw !== "object") return { case_id: definition.case_id, outcome: "invalid", errors: ["observation_missing"] };
  if (raw.case_id !== definition.case_id) errors.push("case_id_mismatch");
  if (!EXECUTION_STATUSES.has(raw.execution_status)) errors.push("execution_status_invalid");
  if (!VERIFICATION_STATES.has(raw.verification_state)) errors.push("verification_state_invalid");
  if (typeof raw.attempt_id !== "string" || raw.attempt_id.trim() === "") errors.push("attempt_id_missing");
  if (raw.latency_ms !== undefined && !finiteNonNegative(raw.latency_ms)) errors.push("latency_invalid");
  if (raw.input_tokens !== undefined && !finiteNonNegative(raw.input_tokens)) errors.push("input_tokens_invalid");
  if (raw.output_tokens !== undefined && !finiteNonNegative(raw.output_tokens)) errors.push("output_tokens_invalid");

  const checkErrors = validateChecks(raw, definition);
  const requiresChecks = raw.execution_status === "completed";
  if (requiresChecks) errors.push(...checkErrors);
  if (errors.length) return { case_id: definition.case_id, outcome: "invalid", errors };

  if (raw.execution_status === "not_run") return { case_id: definition.case_id, outcome: "not_run", exclusion_reason: "not_run" };
  if (raw.execution_status === "blocked") return { case_id: definition.case_id, outcome: "blocked", exclusion_reason: raw.failure_class || "blocked" };
  if (raw.execution_status === "failed") return { case_id: definition.case_id, outcome: "blocked", exclusion_reason: raw.failure_class || "execution_failed" };

  const allChecksPassed = raw.checks.every((check) => check.passed === true);
  if (raw.verification_state === "verification_passed" && allChecksPassed) return { case_id: definition.case_id, outcome: "pass" };
  if (raw.verification_state === "verification_failed" || !allChecksPassed) return { case_id: definition.case_id, outcome: "fail" };
  return { case_id: definition.case_id, outcome: "unverified", exclusion_reason: "verification_not_passed" };
}

function manifestErrors(manifest) {
  const errors = [];
  if (!manifest || typeof manifest !== "object") return ["manifest_missing"];
  if (manifest.schema_version !== MANIFEST_SCHEMA_VERSION) errors.push("manifest_schema_unsupported");
  if (typeof manifest.manifest_id !== "string" || manifest.manifest_id.trim() === "") errors.push("manifest_id_missing");
  if (!Array.isArray(manifest.cases) || manifest.cases.length === 0) errors.push("manifest_cases_missing");
  const seenCaseIds = new Set();
  const definitions = Array.isArray(manifest.cases) ? manifest.cases : [];
  for (const definition of definitions) {
    for (const field of ["case_id", "suite", "lane", "capability", "difficulty"]) {
      if (typeof definition?.[field] !== "string" || definition[field].trim() === "") errors.push(`case_${field}_missing`);
    }
    if (definition?.case_id && seenCaseIds.has(definition.case_id)) errors.push(`duplicate_manifest_case:${definition.case_id}`);
    if (definition?.case_id) seenCaseIds.add(definition.case_id);
    if (!definition?.checker || typeof definition.checker.type !== "string") errors.push(`checker_missing:${definition?.case_id || "unknown"}`);
  }
  if (manifest.manifest_sha256 && hashManifest(manifest) !== manifest.manifest_sha256) errors.push("manifest_hash_mismatch");
  return errors;
}

export function evaluateRun({ manifest = BENCHMARK_MANIFEST, run }) {
  const errors = manifestErrors(manifest);
  if (!run || typeof run !== "object") return { status: "invalid", errors: [...errors, "run_missing"] };
  const expectedManifestHash = manifest.manifest_sha256 || hashManifest(manifest);
  if (run.schema_version !== "capability-difficulty-run.v1") errors.push("run_schema_unsupported");
  if (typeof run.run_id !== "string" || run.run_id.trim() === "") errors.push("run_id_missing");
  if (run.manifest_id !== manifest.manifest_id) errors.push("run_manifest_id_mismatch");
  if (run.manifest_sha256 !== expectedManifestHash) errors.push("run_manifest_hash_mismatch");
  errors.push(...bindingErrors(run.binding));
  if (!Array.isArray(run.cases)) errors.push("run_cases_missing");
  if (errors.length) return { status: "invalid", errors, manifest_sha256: manifest.manifest_sha256 || hashManifest(manifest) };

  const definitionsById = new Map(manifest.cases.map((definition) => [definition.case_id, definition]));
  const seen = new Set();
  const attempts = new Set();
  const observations = [];
  for (const raw of run.cases) {
    const definition = definitionsById.get(raw?.case_id);
    if (!definition) {
      observations.push({ case_id: raw?.case_id || "unknown", outcome: "invalid", errors: ["case_unknown"] });
      continue;
    }
    if (seen.has(definition.case_id)) {
      observations.push({ case_id: definition.case_id, outcome: "invalid", errors: ["duplicate_case_observation"] });
      continue;
    }
    seen.add(definition.case_id);
    if (typeof raw.attempt_id === "string" && attempts.has(raw.attempt_id)) {
      observations.push({ case_id: definition.case_id, outcome: "invalid", errors: ["duplicate_attempt_id"] });
      continue;
    }
    if (typeof raw.attempt_id === "string") attempts.add(raw.attempt_id);
    observations.push(evaluateObservation(raw, definition));
  }
  for (const definition of manifest.cases) {
    if (!seen.has(definition.case_id)) observations.push({ case_id: definition.case_id, outcome: "not_run", exclusion_reason: "missing_observation" });
  }

  const overall = summarize(observations, manifest.cases);
  const bySuite = groupSummary(manifest.cases, observations, (definition) => definition.suite);
  const byCapability = groupSummary(manifest.cases, observations, (definition) => definition.capability);
  const byDifficulty = groupSummary(manifest.cases, observations, (definition) => definition.difficulty);
  const byCell = groupSummary(manifest.cases, observations, cellKey);
  const allCasesObserved = overall.observed === overall.total;
  const noInvalid = overall.invalid === 0;
  const runStatus = allCasesObserved && noInvalid ? "run_complete" : "partial";
  const policy = { ...DEFAULT_POLICY, ...(manifest.policy || {}) };
  const promotionEligible = Object.values(byCell).every((cell) => (
    cell.observed >= policy.min_observations_per_cell
    && cell.pass >= policy.min_verified_successes_per_cell
  ));

  return {
    status: runStatus,
    errors: [],
    manifest_sha256: manifest.manifest_sha256 || hashManifest(manifest),
    run_id: run.run_id,
    binding: run.binding,
    overall,
    by_suite: bySuite,
    by_capability: byCapability,
    by_difficulty: byDifficulty,
    by_cell: byCell,
    coverage: { all_cases_observed: allCasesObserved, no_invalid_observations: noInvalid },
    promotion: {
      eligible: promotionEligible,
      reason: promotionEligible ? "policy_thresholds_met" : "insufficient_repeated_verified_evidence",
      policy,
    },
    observations,
  };
}

export function aggregateRuns({ manifest = BENCHMARK_MANIFEST, runs }) {
  if (!Array.isArray(runs) || runs.length === 0) return { status: "invalid", errors: ["runs_missing"] };
  const evaluations = runs.map((run) => evaluateRun({ manifest, run }));
  const invalid = evaluations.filter((evaluation) => evaluation.status === "invalid");
  if (invalid.length) return { status: "invalid", errors: invalid.flatMap((evaluation) => evaluation.errors || []) };
  if (runs.some((run) => !sameBinding(run.binding, runs[0].binding))) {
    return { status: "invalid", errors: ["mixed_binding_scope"] };
  }

  const definitionsById = new Map(manifest.cases.map((definition) => [definition.case_id, definition]));
  const observations = [];
  for (const evaluation of evaluations) {
    for (const observation of evaluation.observations) {
      if (definitionsById.has(observation.case_id)) observations.push(observation);
    }
  }
  const policy = { ...DEFAULT_POLICY, ...(manifest.policy || {}) };
  const definitionsByCell = new Map();
  for (const definition of manifest.cases) {
    const key = cellKey(definition);
    if (!definitionsByCell.has(key)) definitionsByCell.set(key, []);
    definitionsByCell.get(key).push(definition);
  }
  const byCell = {};
  for (const [key, definitions] of definitionsByCell.entries()) {
    const definitionIds = new Set(definitions.map((definition) => definition.case_id));
    const values = observations.filter((observation) => definitionIds.has(observation.case_id));
    byCell[key] = summarize(values, definitions.flatMap((definition) => runs.map(() => definition)));
  }
  const overall = summarize(observations, manifest.cases.flatMap((definition) => runs.map(() => definition)));
  const promotionEligible = Object.values(byCell).every((cell) => (
    cell.observed >= policy.min_observations_per_cell
    && cell.pass >= policy.min_verified_successes_per_cell
  ));
  return {
    status: "aggregate_complete",
    manifest_sha256: manifest.manifest_sha256 || hashManifest(manifest),
    run_count: runs.length,
    binding: runs[0].binding,
    overall,
    by_cell: byCell,
    promotion: {
      eligible: promotionEligible,
      reason: promotionEligible ? "policy_thresholds_met" : "insufficient_repeated_verified_evidence",
      policy,
    },
    run_statuses: evaluations.map((evaluation) => ({ run_id: evaluation.run_id, status: evaluation.status })),
  };
}
