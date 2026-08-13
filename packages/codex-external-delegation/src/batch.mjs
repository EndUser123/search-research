import { access, mkdir, readFile, writeFile } from "node:fs/promises";
import { dirname, isAbsolute, join, relative, resolve } from "node:path";
import { compilePacket as defaultCompilePacket } from "./packet.mjs";
import { validatePacket as defaultValidatePacket, validateResult as defaultValidateResult } from "./contract.mjs";
import { runPacket as defaultRunPacket } from "./runner.mjs";

export const BATCH_SCHEMA_VERSION = "batch.v1";
export const BENCHMARK_APPROVAL_SCHEMA_VERSION = "codex-pi-benchmark-live-approval.v1";

const MAX_REPETITIONS = 5;
const MAX_CONCURRENCY = 256;
const ID_PATTERN = /^[A-Za-z0-9][A-Za-z0-9._-]*$/;
const REDACTED = "[REDACTED]";

function isObject(value) {
  return value !== null && typeof value === "object" && !Array.isArray(value);
}

function nonEmptyString(value) {
  return typeof value === "string" && value.trim().length > 0;
}

function safeId(value) {
  return nonEmptyString(value) && ID_PATTERN.test(value) && value !== "." && value !== "..";
}

function integerInRange(value, min, max) {
  return Number.isInteger(value) && value >= min && value <= max;
}

function own(value, key) {
  return Object.prototype.hasOwnProperty.call(value, key);
}

function pushError(errors, path, message) {
  errors.push(`${path}: ${message}`);
}

function validateConcurrency(concurrency, errors) {
  if (!isObject(concurrency)) {
    pushError(errors, "concurrency", "must be an object");
    return;
  }
  for (const key of Object.keys(concurrency)) {
    if (!["max_in_flight", "by_provider"].includes(key)) {
      pushError(errors, `concurrency.${key}`, "unknown field");
    }
  }
  if (!integerInRange(concurrency.max_in_flight, 1, MAX_CONCURRENCY)) {
    pushError(errors, "concurrency.max_in_flight", `must be an integer from 1 to ${MAX_CONCURRENCY}`);
  }
  if (!isObject(concurrency.by_provider)) {
    pushError(errors, "concurrency.by_provider", "must be an object");
    return;
  }
  for (const [provider, limit] of Object.entries(concurrency.by_provider)) {
    if (!nonEmptyString(provider)) pushError(errors, "concurrency.by_provider", "provider keys must be non-empty");
    if (!integerInRange(limit, 1, MAX_CONCURRENCY)) {
      pushError(errors, `concurrency.by_provider.${provider}`, `must be an integer from 1 to ${MAX_CONCURRENCY}`);
    }
  }
}

function validateTask(task, index, seen, errors) {
  const prefix = `tasks[${index}]`;
  if (!isObject(task)) {
    pushError(errors, prefix, "must be an object");
    return;
  }
  for (const key of Object.keys(task)) {
    if (!["task_id", "repetitions", "candidate_mode", "input"].includes(key)) {
      pushError(errors, `${prefix}.${key}`, "unknown field");
    }
  }
  if (!safeId(task.task_id)) pushError(errors, `${prefix}.task_id`, "must be a safe non-empty identifier");
  if (safeId(task.task_id)) {
    if (seen.has(task.task_id)) pushError(errors, `${prefix}.task_id`, "must be unique");
    seen.add(task.task_id);
  }
  if (!integerInRange(task.repetitions, 1, MAX_REPETITIONS)) {
    pushError(errors, `${prefix}.repetitions`, `must be an integer from 1 to ${MAX_REPETITIONS}`);
  }
  if (task.candidate_mode !== "automatic" && task.candidate_mode !== "explicit") {
    pushError(errors, `${prefix}.candidate_mode`, "must be automatic or explicit");
  }
  if (!isObject(task.input)) {
    pushError(errors, `${prefix}.input`, "must be an object compatible with compilePacket");
    return;
  }

  if (task.candidate_mode === "automatic") {
    if (own(task.input, "model") || own(task.input, "requested_model")) {
      pushError(errors, `${prefix}.input`, "automatic candidates must omit model and requested_model");
    }
  }
  if (task.candidate_mode === "explicit") {
    if (task.input.requested_worker !== "pi") {
      pushError(errors, `${prefix}.input.requested_worker`, "explicit candidates must request worker pi");
    }
    if (!nonEmptyString(task.input.requested_provider)) {
      pushError(errors, `${prefix}.input.requested_provider`, "is required for explicit candidates");
    }
    if (!nonEmptyString(task.input.model)) {
      pushError(errors, `${prefix}.input.model`, "is required for explicit candidates");
    }
  }
}

export function validateBatchManifest(manifest) {
  const errors = [];
  if (!isObject(manifest)) return ["manifest: must be an object"];
  for (const key of Object.keys(manifest)) {
    if (!["schema_version", "batch_id", "artifact_root", "concurrency", "tasks"].includes(key)) {
      pushError(errors, key, "unknown field");
    }
  }
  if (manifest.schema_version !== BATCH_SCHEMA_VERSION) {
    pushError(errors, "schema_version", `must equal ${BATCH_SCHEMA_VERSION}`);
  }
  if (!safeId(manifest.batch_id)) pushError(errors, "batch_id", "must be a safe non-empty identifier");
  if (!nonEmptyString(manifest.artifact_root)) pushError(errors, "artifact_root", "must be a non-empty path");
  validateConcurrency(manifest.concurrency, errors);
  if (!Array.isArray(manifest.tasks) || manifest.tasks.length === 0) {
    pushError(errors, "tasks", "must be a non-empty array");
  } else {
    const seen = new Set();
    manifest.tasks.forEach((task, index) => validateTask(task, index, seen, errors));
  }
  return errors;
}

function benchmarkManifestInfo(manifest) {
  const inputs = (manifest?.tasks || [])
    .map((task) => task?.input)
    .filter((input) => isObject(input) && nonEmptyString(input.benchmark_manifest_id));
  if (inputs.length === 0) return null;
  const manifestIds = [...new Set(inputs.map((input) => input.benchmark_manifest_id))];
  const manifestHashes = [...new Set(inputs.map((input) => input.benchmark_manifest_sha256).filter(nonEmptyString))];
  return {
    benchmark_manifest_ids: manifestIds,
    benchmark_manifest_hashes: manifestHashes,
    estimated_calls: (manifest.tasks || []).reduce((total, task) => total + (Number.isInteger(task?.repetitions) ? task.repetitions : 0), 0),
  };
}

function benchmarkApprovalErrors(manifest, approval, now = Date.now()) {
  const info = benchmarkManifestInfo(manifest);
  if (!info) return [];
  const errors = [];
  const requireString = (key) => {
    if (!nonEmptyString(approval?.[key])) errors.push(`benchmark approval ${key} is required`);
  };

  if (!isObject(approval)) {
    return ["benchmark live execution requires an approval receipt"];
  }
  if (approval.schema_version !== BENCHMARK_APPROVAL_SCHEMA_VERSION) {
    errors.push(`benchmark approval schema_version must equal ${BENCHMARK_APPROVAL_SCHEMA_VERSION}`);
  }
  if (approval.status !== "approved") errors.push("benchmark approval status must be approved");
  for (const key of ["authorization_id", "benchmark_manifest_id", "manifest_sha256", "batch_id", "scope", "orchestrator", "worker", "invocation_method", "fallback_policy", "approved_at", "expires_at"]) {
    requireString(key);
  }
  if (info.benchmark_manifest_ids.length !== 1 || approval.benchmark_manifest_id !== info.benchmark_manifest_ids[0]) {
    errors.push("benchmark approval manifest id does not match the batch");
  }
  if (info.benchmark_manifest_hashes.length !== 1 || approval.manifest_sha256 !== info.benchmark_manifest_hashes[0]) {
    errors.push("benchmark approval manifest hash does not match the batch");
  }
  if (approval.batch_id !== manifest.batch_id) errors.push("benchmark approval batch id does not match the batch");
  if (approval.scope !== "capability-difficulty") errors.push("benchmark approval scope must be capability-difficulty");
  if (approval.orchestrator !== "codex") errors.push("benchmark approval orchestrator must be codex");
  if (approval.worker !== "pi") errors.push("benchmark approval worker must be pi");
  if (approval.invocation_method !== "pi") errors.push("benchmark approval invocation_method must be pi");
  if (approval.fallback_policy !== "halt_no_automatic_fallback") errors.push("benchmark approval fallback policy must disable fallback");
  if (!Number.isInteger(approval.max_calls) || approval.max_calls < info.estimated_calls) {
    errors.push(`benchmark approval max_calls must be an integer at least ${info.estimated_calls}`);
  }

  const approvedAt = Date.parse(approval.approved_at);
  const expiresAt = Date.parse(approval.expires_at);
  if (!Number.isFinite(approvedAt)) errors.push("benchmark approval approved_at must be an ISO timestamp");
  if (!Number.isFinite(expiresAt)) errors.push("benchmark approval expires_at must be an ISO timestamp");
  if (Number.isFinite(approvedAt) && approvedAt > now) errors.push("benchmark approval is not yet valid");
  if (Number.isFinite(approvedAt) && Number.isFinite(expiresAt) && expiresAt <= approvedAt) {
    errors.push("benchmark approval expires_at must be after approved_at");
  }
  if (Number.isFinite(expiresAt) && expiresAt <= now) errors.push("benchmark approval has expired");
  return errors;
}

function assertValidManifest(manifest) {
  const errors = validateBatchManifest(manifest);
  if (errors.length) {
    const error = new Error("Invalid batch manifest");
    error.name = "BatchManifestError";
    error.errors = errors;
    throw error;
  }
}

function batchDirectory(manifest) {
  const artifactRoot = resolve(manifest.artifact_root);
  const batchDir = resolve(join(artifactRoot, manifest.batch_id));
  const escaped = relative(artifactRoot, batchDir);
  if (escaped === ".." || escaped.startsWith(`..${"/"}`) || escaped.startsWith(`..${"\\"}`) || isAbsolute(escaped)) {
    throw new Error("batch_id escapes artifact_root");
  }
  return { artifactRoot, batchDir };
}

function repetitionLabel(repetition) {
  return String(repetition).padStart(3, "0");
}

export function expandBatchManifest(manifest) {
  assertValidManifest(manifest);
  const { batchDir } = batchDirectory(manifest);
  const expanded = [];
  for (const task of manifest.tasks) {
    for (let repetition = 1; repetition <= task.repetitions; repetition += 1) {
      const label = repetitionLabel(repetition);
      const repetitionId = `${manifest.batch_id}--${task.task_id}--r${label}`;
      const artifactDir = join(batchDir, "tasks", task.task_id, `rep-${label}`);
      expanded.push({
        index: expanded.length,
        batch_id: manifest.batch_id,
        source_task_id: task.task_id,
        repetition,
        repetition_id: repetitionId,
        candidate_mode: task.candidate_mode,
        artifact_dir: artifactDir,
        input: {
          ...task.input,
          task_id: repetitionId,
          parent_run_id: manifest.batch_id,
        },
      });
    }
  }
  return expanded;
}

function redactString(value) {
  return String(value)
    .replace(/\bsk-[A-Za-z0-9_-]{16,}\b/g, REDACTED)
    .replace(/((?:api[_-]?key|access[_-]?token|secret|password)\s*[:=]\s*["']?)([^\s,;"'}]+)/gi, `$1${REDACTED}`)
    .replace(/((?:authorization)\s*[:=]\s*(?:bearer\s+)?)[^\s,;"'}]+/gi, `$1${REDACTED}`);
}

export function redactValue(value, key = "") {
  // Do not redact telemetry fields such as token_cap_flags_present merely
  // because their names contain "token". Credential fields are explicit.
  if (/^(?:api[_-]?key|access[_-]?token|refresh[_-]?token|token|password|secret|authorization)$/i.test(key)) return REDACTED;
  if (typeof value === "string") return redactString(value);
  if (Array.isArray(value)) return value.map((entry) => redactValue(entry));
  if (isObject(value)) {
    return Object.fromEntries(Object.entries(value).map(([entryKey, entryValue]) => [entryKey, redactValue(entryValue, entryKey)]));
  }
  return value;
}

function selectionSummary(packet) {
  const selection = packet?.model_selection || {};
  return {
    candidate_id: selection.candidate_id || null,
    worker: packet?.requested_worker || packet?.worker || selection.worker || null,
    provider: packet?.requested_provider || selection.provider || null,
    model: packet?.model || selection.model || null,
    quota_pool: selection.quota_pool || packet?.requested_provider || null,
    status: selection.status || (packet?.model ? "explicit" : null),
    confidence: selection.confidence || (packet?.model ? "explicit" : null),
    reasons: Array.isArray(selection.reasons) ? selection.reasons : [],
  };
}

function publicEntry(plan) {
  return {
    index: plan.index,
    task_id: plan.repetition_id,
    source_task_id: plan.source_task_id,
    repetition: plan.repetition,
    repetition_id: plan.repetition_id,
    candidate_mode: plan.candidate_mode,
    artifact_dir: plan.artifact_dir,
    packet_path: plan.packet_path,
    result_path: plan.result_path,
    stdout_path: plan.stdout_path,
    stderr_path: plan.stderr_path,
    status: plan.status,
    failure_class: plan.failure_class,
    selection: plan.selection || null,
    classification: plan.classification || null,
    errors: plan.errors || [],
  };
}

function routeFailure(plan, failureClass, errors, classification = null, packet = null) {
  plan.status = "blocked";
  plan.failure_class = failureClass;
  plan.errors = errors;
  plan.classification = classification;
  plan.packet = packet;
  plan.selection = packet ? selectionSummary(packet) : null;
  return plan;
}

function routeOne(plan, { compilePacket, validatePacket }) {
  let compiled;
  try {
    compiled = compilePacket(plan.input);
  } catch (error) {
    return routeFailure(plan, "route_error", [error.message], null);
  }
  const packet = compiled?.packet || compiled;
  const classification = compiled?.classification || null;
  plan.classification = classification;
  plan.packet = packet;
  plan.selection = selectionSummary(packet);

  if (plan.candidate_mode === "automatic" && classification && classification.eligible !== true) {
    return routeFailure(plan, "not_eligible_external_candidate", [classification.reason || "task is not eligible for automatic routing"], classification, packet);
  }
  if (packet?.model_selection?.status === "no_eligible_candidate") {
    return routeFailure(plan, "no_eligible_external_candidate", [packet.model_selection.reason || "no eligible candidate"], classification, packet);
  }
  if (packet?.model_selection?.confidence === "unverified") {
    return routeFailure(plan, "unverified_model_selection", ["model selection is unverified"], classification, packet);
  }

  const validation = validatePacket(packet, { allowWorktreeRequest: true });
  if (!validation.ok) {
    return routeFailure(plan, "contract_error", validation.errors, classification, packet);
  }
  const preflight = plan.input?.benchmark_preflight;
  if (preflight?.status === "blocked") {
    return routeFailure(
      plan,
      preflight.failure_class || "preflight_blocked",
      Array.isArray(preflight.reasons) && preflight.reasons.length ? preflight.reasons : ["benchmark_preflight_blocked"],
      classification,
      packet,
    );
  }
  plan.status = "ok";
  plan.failure_class = "none";
  plan.errors = [];
  return plan;
}

function planPaths(plan) {
  return {
    packet_path: join(plan.artifact_dir, "packet.json"),
    result_path: join(plan.artifact_dir, "result.json"),
    stdout_path: join(plan.artifact_dir, "stdout.log"),
    stderr_path: join(plan.artifact_dir, "stderr.log"),
  };
}

async function writeJson(path, value) {
  await mkdir(dirname(path), { recursive: true });
  await writeFile(path, `${JSON.stringify(value, null, 2)}\n`, "utf8");
}

async function writeIfMissing(path, content = "") {
  try {
    await access(path);
  } catch {
    await writeFile(path, content, "utf8");
  }
}

async function writeRouteArtifacts(manifest, route, plans) {
  const { batchDir } = batchDirectory(manifest);
  await mkdir(batchDir, { recursive: true });
  await writeJson(join(batchDir, "manifest.redacted.json"), redactValue(manifest));
  for (const plan of plans) {
    Object.assign(plan, planPaths(plan));
    if (plan.packet) {
      await writeJson(plan.packet_path, redactValue(plan.packet));
    }
  }
  route.artifact_dir = batchDir;
  route.manifest_path = join(batchDir, "manifest.redacted.json");
  route.route_path = join(batchDir, "route.json");
  route.entries = plans.map(publicEntry);
  await writeJson(route.route_path, route);
}

function countStatuses(plans) {
  return {
    total: plans.length,
    routed: plans.filter((plan) => plan.status === "ok").length,
    blocked: plans.filter((plan) => plan.status === "blocked").length,
    succeeded: 0,
    failed: 0,
  };
}

function routeEnvelope(manifest, plans) {
  const counts = countStatuses(plans);
  return {
    schema_version: BATCH_SCHEMA_VERSION,
    batch_id: manifest.batch_id,
    status: counts.blocked === 0 ? "ok" : "blocked",
    failure_class: counts.blocked === 0 ? "none" : "batch_route_blocked",
    counts,
    entries: plans.map(publicEntry),
  };
}

export async function routeBatch(manifest, {
  compile = defaultCompilePacket,
  validate = defaultValidatePacket,
  writeArtifacts = true,
} = {}) {
  const errors = validateBatchManifest(manifest);
  if (errors.length) {
    return {
      schema_version: BATCH_SCHEMA_VERSION,
      batch_id: manifest?.batch_id || null,
      status: "blocked",
      failure_class: "invalid_manifest",
      counts: { total: 0, routed: 0, blocked: 0, succeeded: 0, failed: 0 },
      errors,
      entries: [],
      plans: [],
    };
  }

  const expanded = expandBatchManifest(manifest);
  const plans = expanded.map((plan) => routeOne(plan, { compilePacket: compile, validatePacket: validate }));
  plans.forEach((plan) => Object.assign(plan, planPaths(plan)));
  const route = routeEnvelope(manifest, plans);
  if (writeArtifacts) {
    try {
      await writeRouteArtifacts(manifest, route, plans);
    } catch (error) {
      return {
        ...route,
        status: "blocked",
        failure_class: "artifact_error",
        errors: [error.message],
        entries: plans.map(publicEntry),
        plans,
      };
    }
  }
  return { ...route, plans };
}

function providerKey(packet) {
  return packet?.model_selection?.quota_pool || packet?.requested_provider || packet?.worker || "unknown";
}

function failureResult(plan, error) {
  return {
    schema_version: "2",
    task_id: plan.repetition_id,
    status: "failed",
    failure_class: "batch_runner_error",
    worker: plan.packet?.worker || null,
    provider: plan.packet?.requested_provider || null,
    model: plan.packet?.model || null,
    attempt: 0,
    exit_code: null,
    timed_out: false,
    result_payload: null,
    message: error.message,
    artifact_dir: plan.artifact_dir,
  };
}

function blockedResult(plan) {
  return {
    schema_version: "2",
    task_id: plan.repetition_id,
    status: "blocked",
    failure_class: plan.failure_class,
    worker: plan.packet?.worker || null,
    provider: plan.packet?.requested_provider || null,
    model: plan.packet?.model || null,
    attempt: 0,
    exit_code: null,
    timed_out: false,
    result_payload: null,
    contract_errors: plan.errors,
    artifact_dir: plan.artifact_dir,
  };
}

async function executePlans(plans, manifest, run, validateResult, clock) {
  const results = new Array(plans.length);
  const maxInFlight = manifest.concurrency.max_in_flight;
  const providerLimits = manifest.concurrency.by_provider;
  const pending = plans.filter((plan) => plan.status === "ok").map((plan) => plan.index);
  const totalEligible = pending.length;
  const activeByProvider = new Map();
  let active = 0;
  let completed = 0;

  for (const plan of plans) {
    if (plan.status !== "ok") {
      results[plan.index] = blockedResult(plan);
    }
  }

  await new Promise((resolveAll) => {
    const pump = () => {
      let launched = false;
      while (active < maxInFlight) {
        const position = pending.findIndex((index) => {
          const provider = providerKey(plans[index].packet);
          const limit = own(providerLimits, provider) ? providerLimits[provider] : maxInFlight;
          return (activeByProvider.get(provider) || 0) < limit;
        });
        if (position < 0) break;
        const index = pending.splice(position, 1)[0];
        const plan = plans[index];
        const provider = providerKey(plan.packet);
        active += 1;
        activeByProvider.set(provider, (activeByProvider.get(provider) || 0) + 1);
        launched = true;
        const started = clock();
        Promise.resolve()
          .then(() => run(plan.packet, { artifactDir: plan.artifact_dir }))
          .then((result) => {
            const validation = validateResult(result);
            if (!validation.ok) {
              results[index] = {
                ...failureResult(plan, new Error("worker returned an invalid result envelope")),
                failure_class: "contract_error",
                contract_errors: validation.errors,
                elapsed_ms: Math.max(0, clock() - started),
                selection: plan.selection,
              };
              return;
            }
            results[index] = { ...result, elapsed_ms: Math.max(0, clock() - started), selection: plan.selection, artifact_dir: plan.artifact_dir };
          })
          .catch((error) => {
            results[index] = { ...failureResult(plan, error), elapsed_ms: Math.max(0, clock() - started), selection: plan.selection };
          })
          .finally(() => {
            active -= 1;
            activeByProvider.set(provider, Math.max(0, (activeByProvider.get(provider) || 1) - 1));
            completed += 1;
            if (completed === totalEligible) {
              resolveAll();
            } else {
              pump();
            }
          });
      }
      if (!launched && active === 0 && pending.length === 0) resolveAll();
    };
    pump();
  });

  return results;
}

function summaryEntry(plan, result) {
  return {
    ...publicEntry(plan),
    status: result?.status || plan.status,
    failure_class: result?.failure_class || plan.failure_class,
    attempt: result?.attempt ?? 0,
    elapsed_ms: result?.elapsed_ms ?? 0,
    selection: plan.selection,
    failure_diagnostics: result?.failure_diagnostics || null,
  };
}

export async function runBatch(manifest, {
  compile = defaultCompilePacket,
  validate = defaultValidatePacket,
  validateResult = defaultValidateResult,
  run = defaultRunPacket,
  benchmarkApproval = null,
  clock = () => Date.now(),
  writeArtifacts = true,
  dryRun = false,
} = {}) {
  const started = clock();
  const route = await routeBatch(manifest, { compile, validate, writeArtifacts });
  if (!route.plans?.length && route.failure_class === "invalid_manifest") {
    return { ...route, dry_run: dryRun, elapsed_ms: Math.max(0, clock() - started), summary_path: null };
  }
  if (route.failure_class === "artifact_error") {
    return { ...route, dry_run: dryRun, elapsed_ms: Math.max(0, clock() - started), summary_path: null };
  }
  if (dryRun) {
    return { ...route, status: route.status === "ok" ? "dry_run" : route.status, dry_run: true, elapsed_ms: Math.max(0, clock() - started) };
  }

  const approvalErrors = benchmarkApprovalErrors(manifest, benchmarkApproval, clock());
  let preExecutionFailureClass = null;
  if (approvalErrors.length > 0) {
    preExecutionFailureClass = "benchmark_live_approval_required";
    for (const plan of route.plans) {
      if (plan.status === "ok") {
        routeFailure(plan, preExecutionFailureClass, approvalErrors, plan.classification, plan.packet);
      }
    }
    Object.assign(route, routeEnvelope(manifest, route.plans));
    if (writeArtifacts) {
      try {
        await writeRouteArtifacts(manifest, route, route.plans);
      } catch (error) {
        return {
          ...route,
          status: "failed",
          failure_class: "artifact_error",
          errors: [error.message],
          dry_run: false,
          elapsed_ms: Math.max(0, clock() - started),
          summary_path: null,
        };
      }
    }
  }

  const results = await executePlans(route.plans, manifest, run, validateResult, clock);
  const artifactErrors = [];
  for (const plan of route.plans) {
    const result = results[plan.index];
    if (result) {
      try {
        await writeJson(plan.result_path, redactValue(result));
        await writeIfMissing(plan.stdout_path);
        await writeIfMissing(plan.stderr_path);
      } catch (error) {
        artifactErrors.push({ task_id: plan.repetition_id, message: error.message });
        results[plan.index] = {
          ...result,
          status: "failed",
          failure_class: "artifact_error",
          artifact_errors: [error.message],
        };
      }
    }
  }
  const entries = route.plans.map((plan) => summaryEntry(plan, results[plan.index]));
  const routeBlocked = route.plans.filter((plan) => plan.status === "blocked").length;
  const executionBlocked = entries.filter((entry, index) => route.plans[index]?.status === "ok" && entry.status === "blocked").length;
  const workerBlocked = entries.filter((entry, index) => route.plans[index]?.status === "ok" && entry.failure_class === "worker_blocked").length;
  const counts = {
    total: entries.length,
    routed: route.plans.filter((plan) => plan.status === "ok").length,
    blocked: routeBlocked,
    execution_blocked: executionBlocked,
    worker_blocked: workerBlocked,
    succeeded: entries.filter((entry) => entry.status === "ok").length,
    failed: entries.filter((entry) => entry.status === "failed").length,
  };
  const failed = counts.blocked > 0 || counts.execution_blocked > 0 || counts.failed > 0 || artifactErrors.length > 0;
  const summary = {
    schema_version: BATCH_SCHEMA_VERSION,
    batch_id: manifest.batch_id,
    status: failed ? "failed" : "ok",
    failure_class: artifactErrors.length > 0 ? "artifact_error" : failed ? (preExecutionFailureClass || "batch_task_failed") : "none",
    counts,
    elapsed_ms: Math.max(0, clock() - started),
    entries,
  };
  if (approvalErrors.length > 0) {
    summary.benchmark_gate = {
      status: "blocked",
      failure_class: preExecutionFailureClass,
      errors: approvalErrors,
    };
  }
  if (artifactErrors.length > 0) summary.artifact_errors = artifactErrors;
  if (writeArtifacts) {
    try {
      const { batchDir } = batchDirectory(manifest);
      summary.summary_path = join(batchDir, "batch-summary.json");
      await writeJson(summary.summary_path, summary);
    } catch (error) {
      return {
        ...summary,
        status: "failed",
        failure_class: "artifact_error",
        artifact_errors: [...(summary.artifact_errors || []), { task_id: null, message: error.message }],
        summary_path: null,
        plans: route.plans,
        route_path: route.route_path || null,
        artifact_dir: route.artifact_dir || null,
      };
    }
  }
  return { ...summary, plans: route.plans, route_path: route.route_path || null, artifact_dir: route.artifact_dir || null };
}

export function batchExitCode(result) {
  if (result?.failure_class === "invalid_manifest" || result?.failure_class === "artifact_error") return 30;
  if (result?.dry_run === true) return 0;
  if (result?.status === "ok" || result?.status === "dry_run") return 0;
  return 20;
}
