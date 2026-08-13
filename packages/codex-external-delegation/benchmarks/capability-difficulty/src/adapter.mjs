import { readFile, writeFile } from "node:fs/promises";
import { join } from "node:path";
import { checkCase, CHECKER_ID } from "./checkers.mjs";
import { BENCHMARK_MANIFEST } from "./manifest.mjs";

async function readJson(path) {
  return JSON.parse(await readFile(path, "utf8"));
}

function sameBinding(packet, binding) {
  return packet?.orchestrator === binding?.orchestrator
    && packet?.invocation_method === binding?.invocation_method
    && packet?.requested_provider === binding?.provider
    && packet?.model === binding?.model
    && packet?.requested_worker === "pi";
}

function benchmarkCaseId(packet, entry) {
  if (typeof packet?.benchmark_case_id === "string" && packet.benchmark_case_id.trim()) {
    return packet.benchmark_case_id;
  }
  const source = `${packet?.objective || ""}\n${entry?.source_task_id || ""}`;
  return source.match(/\b((?:capability|code_pool)\.[a-z0-9_]+(?:\.[a-z0-9_]+){2,})\b/i)?.[1] || null;
}

function attemptId(runId, entry, caseId) {
  return `${runId}-${entry?.task_id || caseId}`;
}

function baseCase(definition, runId, entry, packet, result, binding) {
  const attempt = result?.attempt ?? null;
  const artifactDir = entry?.artifact_dir || null;
  const provider = binding?.provider || packet?.requested_provider || result?.provider || null;
  const model = binding?.model || packet?.model || result?.model || null;
  return {
    case_id: definition.case_id,
    attempt_id: attemptId(runId, entry, definition.case_id),
    execution_status: "not_run",
    verification_state: "not_run",
    failure_class: "not_run",
    artifact_dir: artifactDir,
    result_path: entry?.result_path || null,
    packet_path: entry?.packet_path || null,
    raw_attempt_path: artifactDir && Number.isInteger(Number(attempt)) && Number(attempt) > 0
      ? join(artifactDir, `attempt-${Number(attempt)}.json`)
      : null,
    raw_stdout_path: entry?.stdout_path || null,
    raw_stderr_path: entry?.stderr_path || null,
    orchestrator: binding?.orchestrator || packet?.orchestrator || result?.orchestrator || null,
    worker: binding?.worker || packet?.requested_worker || result?.worker || null,
    invocation_method: binding?.invocation_method || packet?.invocation_method || result?.invocation_method || null,
    route: binding?.route || packet?.dispatch_path || packet?.route || null,
    verifier: binding?.verifier || CHECKER_ID,
    provider,
    model,
    quota_pool: binding?.quota_pool || packet?.model_selection?.quota_pool || null,
    provider_account: binding?.provider_account || packet?.provider_account || null,
    provider_scope: binding?.provider_scope || packet?.provider_scope || null,
    isolated_cwd: result?.isolated_cwd || packet?.isolated_cwd || null,
    latency_ms: Number.isFinite(Number(entry?.elapsed_ms))
      ? Number(entry.elapsed_ms)
      : Number.isFinite(Number(result?.elapsed_ms)) ? Number(result.elapsed_ms) : null,
    token_usage: result?.token_usage || result?.usage || result?.result_payload?.token_usage || result?.result_payload?.usage || null,
    tool_trace: result?.tool_trace || result?.tool_trace_events || result?.result_payload?.tool_trace || null,
  };
}

export async function collectCapabilityRun({
  batchSummary,
  binding,
  runId,
  manifest = BENCHMARK_MANIFEST,
  checker = checkCase,
} = {}) {
  if (!batchSummary || typeof batchSummary !== "object") throw new Error("batch_summary_missing");
  if (!binding || typeof binding !== "object") throw new Error("binding_missing");
  if (typeof runId !== "string" || !runId.trim()) throw new Error("run_id_missing");
  const entries = Array.isArray(batchSummary.entries) ? batchSummary.entries : [];
  const cases = [];

  for (const definition of manifest.cases) {
    const matching = [];
    for (const entry of entries) {
      if (!entry?.packet_path || !entry?.result_path) continue;
      try {
        const packet = await readJson(entry.packet_path);
        if (benchmarkCaseId(packet, entry) === definition.case_id && sameBinding(packet, binding)) matching.push({ entry, packet });
      } catch { /* malformed batch artifacts are represented as not_run below */ }
    }

    if (matching.length !== 1) {
      const value = baseCase(definition, runId, matching[0]?.entry, matching[0]?.packet, null, binding);
      value.failure_class = matching.length > 1 ? "harness_duplicate_case" : "missing_observation";
      cases.push(value);
      continue;
    }

    const { entry, packet } = matching[0];
    let result;
    try { result = await readJson(entry.result_path); } catch (error) {
      const value = baseCase(definition, runId, entry, packet, null, binding);
      value.execution_status = "failed";
      value.failure_class = "harness";
      value.message = error.message;
      cases.push(value);
      continue;
    }

    const value = baseCase(definition, runId, entry, packet, result, binding);
    value.worker_status = result.status || null;
    value.worker_failure_class = result.failure_class || null;
    value.attempt = result.attempt ?? null;
    value.worktree_lifecycle = result.worktree_lifecycle || null;
    value.retry_after = result.retry_after || result.retry_after_ms || null;
    value.reset_at = result.reset_at || result.quota_reset_at || null;
    value.reprobe_at = result.reprobe_at || null;
    if (result.status === "blocked") {
      value.execution_status = "blocked";
      value.failure_class = result.failure_class || "blocked";
      cases.push(value);
      continue;
    }
    if (result.status !== "ok") {
      value.execution_status = "failed";
      value.failure_class = result.failure_class || "execution_failed";
      cases.push(value);
      continue;
    }

    let checkerResult;
    try {
      checkerResult = await checker({
        caseId: definition.case_id,
        payload: result.result_payload || {},
        worktreePath: result.isolated_cwd || packet.isolated_cwd || null,
      });
    } catch (error) {
      value.execution_status = "blocked";
      value.verification_state = "not_run";
      value.failure_class = "harness";
      value.message = error.message;
      cases.push(value);
      continue;
    }
    value.execution_status = checkerResult.status === "verification_blocked" ? "blocked" : "completed";
    value.verification_state = checkerResult.status === "verification_passed" ? "verification_passed" : value.execution_status === "blocked" ? "not_run" : "verification_failed";
    value.failure_class = value.execution_status === "blocked" ? checkerResult.failure_class || "harness" : undefined;
    value.checks = Array.isArray(checkerResult.checks) ? checkerResult.checks : [];
    value.checker = checkerResult.checker || CHECKER_ID;
    value.checker_receipt = checkerResult;
    value.response = result.result_payload?.response ?? null;
    value.observations = result.result_payload?.observations ?? [];
    cases.push(value);
  }

  return {
    schema_version: "capability-difficulty-run.v1",
    run_id: runId,
    manifest_id: manifest.manifest_id,
    manifest_sha256: manifest.manifest_sha256,
    binding,
    source_batch_id: batchSummary.batch_id || null,
    checker: CHECKER_ID,
    cases,
  };
}

export async function writeCapabilityRun(path, options) {
  const run = await collectCapabilityRun(options);
  await writeFile(path, `${JSON.stringify(run, null, 2)}\n`, "utf8");
  return run;
}
