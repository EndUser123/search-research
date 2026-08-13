import test from "node:test";
import assert from "node:assert/strict";
import { mkdtemp, mkdir, rm, writeFile } from "node:fs/promises";
import { join } from "node:path";
import { tmpdir } from "node:os";
import { collectCapabilityRun } from "../benchmarks/capability-difficulty/src/adapter.mjs";
import { BENCHMARK_MANIFEST } from "../benchmarks/capability-difficulty/src/manifest.mjs";

const binding = {
  orchestrator: "codex",
  invocation_method: "pi",
  provider: "nvidia-nim",
  model: "deepseek-ai/deepseek-v4-flash",
  route: "pi",
  verifier: "capability-difficulty-verifier@1",
  quota_pool: "nvidia-nim",
  provider_account: "fixture-account",
  provider_scope: "dedicated-account",
};

test("adapter collects a Pi result into a binding-scoped capability run", async () => {
  const root = await mkdtemp(join(tmpdir(), "codex-pi-adapter-test-"));
  try {
    const artifact = join(root, "tasks", "one");
    await mkdir(artifact, { recursive: true });
    const packetPath = join(artifact, "packet.json");
    const resultPath = join(artifact, "result.json");
    await writeFile(packetPath, JSON.stringify({
      orchestrator: "codex",
      invocation_method: "pi",
      requested_worker: "pi",
      requested_provider: binding.provider,
      model: binding.model,
      provider_account: binding.provider_account,
      provider_scope: binding.provider_scope,
      model_selection: { quota_pool: binding.quota_pool },
      benchmark_case_id: "capability.contract_following.easy.001",
      isolated_cwd: null,
    }), "utf8");
    await writeFile(resultPath, JSON.stringify({
      status: "ok",
      attempt: 1,
      elapsed_ms: 12,
      token_usage: { input: 11, output: 7 },
      tool_trace: [{ name: "read_file", status: "ok" }],
      result_payload: { response: JSON.stringify({ answer: 7, confidence: "high" }) },
    }), "utf8");
    await writeFile(join(artifact, "attempt-1.json"), JSON.stringify({ exitCode: 0 }), "utf8");
    const run = await collectCapabilityRun({
      batchSummary: {
        batch_id: "batch-one",
        entries: [{ task_id: "task-one", artifact_dir: artifact, packet_path: packetPath, result_path: resultPath, stdout_path: join(artifact, "stdout.log"), stderr_path: join(artifact, "stderr.log"), elapsed_ms: 12 }],
      },
      binding,
      runId: "run-one",
      manifest: BENCHMARK_MANIFEST,
    });
    assert.equal(run.schema_version, "capability-difficulty-run.v1");
    assert.equal(run.cases.find((value) => value.case_id === "capability.contract_following.easy.001").verification_state, "verification_passed");
    assert.equal(run.cases.filter((value) => value.execution_status === "not_run").length, 15);
    assert.equal(run.cases[0].checker, "capability-difficulty-verifier@1");
    const observation = run.cases.find((value) => value.case_id === "capability.contract_following.easy.001");
    assert.equal(observation.quota_pool, binding.quota_pool);
    assert.equal(observation.provider_account, binding.provider_account);
    assert.equal(observation.provider_scope, binding.provider_scope);
    assert.equal(observation.route, binding.route);
    assert.equal(observation.raw_attempt_path, join(artifact, "attempt-1.json"));
    assert.deepEqual(observation.token_usage, { input: 11, output: 7 });
    assert.deepEqual(observation.tool_trace, [{ name: "read_file", status: "ok" }]);
  } finally {
    await rm(root, { recursive: true, force: true });
  }
});

test("adapter derives case identity from live batch packet objective when explicit case metadata is absent", async () => {
  const root = await mkdtemp(join(tmpdir(), "codex-pi-adapter-live-packet-"));
  try {
    const artifact = join(root, "tasks", "one");
    await mkdir(artifact, { recursive: true });
    const packetPath = join(artifact, "packet.json");
    const resultPath = join(artifact, "result.json");
    await writeFile(packetPath, JSON.stringify({
      orchestrator: binding.orchestrator,
      invocation_method: binding.invocation_method,
      requested_worker: "pi",
      requested_provider: binding.provider,
      model: binding.model,
      objective: "Execute immutable benchmark case capability.contract_following.easy.001. Return the required payload.",
    }), "utf8");
    await writeFile(resultPath, JSON.stringify({
      status: "ok",
      attempt: 1,
      result_payload: { response: JSON.stringify({ answer: 7, confidence: "high" }) },
    }), "utf8");
    const run = await collectCapabilityRun({
      batchSummary: {
        batch_id: "batch-live-packet",
        entries: [{
          source_task_id: "nvidia-nim-deepseek-ai-deepseek-v4-flash--capability.contract_following.easy.001",
          task_id: "task-live-packet",
          artifact_dir: artifact,
          packet_path: packetPath,
          result_path: resultPath,
        }],
      },
      binding,
      runId: "run-live-packet",
      manifest: BENCHMARK_MANIFEST,
    });
    const observation = run.cases.find((value) => value.case_id === "capability.contract_following.easy.001");
    assert.equal(observation.execution_status, "completed");
    assert.equal(observation.verification_state, "verification_passed");
  } finally {
    await rm(root, { recursive: true, force: true });
  }
});

test("adapter preserves provider blocks as excluded health evidence", async () => {
  const root = await mkdtemp(join(tmpdir(), "codex-pi-adapter-blocked-"));
  try {
    const artifact = join(root, "tasks", "blocked");
    await mkdir(artifact, { recursive: true });
    const packetPath = join(artifact, "packet.json");
    const resultPath = join(artifact, "result.json");
    await writeFile(packetPath, JSON.stringify({
      orchestrator: "codex", invocation_method: "pi", requested_worker: "pi",
      requested_provider: binding.provider, model: binding.model,
      benchmark_case_id: "capability.contract_following.easy.001",
    }), "utf8");
    await writeFile(resultPath, JSON.stringify({
      status: "blocked",
      failure_class: "quota_temporary",
      attempt: 0,
      retry_after: "2026-08-09T10:00:00.000Z",
      reset_at: "2026-08-09T10:00:00.000Z",
      reprobe_at: "next fresh quota snapshot",
    }), "utf8");
    const run = await collectCapabilityRun({
      batchSummary: { batch_id: "batch-blocked", entries: [{ task_id: "task-blocked", artifact_dir: artifact, packet_path: packetPath, result_path: resultPath }] },
      binding,
      runId: "run-blocked",
    });
    const observation = run.cases.find((value) => value.case_id === "capability.contract_following.easy.001");
    assert.equal(observation.execution_status, "blocked");
    assert.equal(observation.failure_class, "quota_temporary");
    assert.equal(observation.verification_state, "not_run");
    assert.equal(observation.retry_after, "2026-08-09T10:00:00.000Z");
    assert.equal(observation.reset_at, "2026-08-09T10:00:00.000Z");
    assert.equal(observation.reprobe_at, "next fresh quota snapshot");
  } finally {
    await rm(root, { recursive: true, force: true });
  }
});

test("adapter preserves coding worktree identity and classifies checker exceptions as harness blocks", async () => {
  const root = await mkdtemp(join(tmpdir(), "codex-pi-adapter-coding-"));
  try {
    const artifact = join(root, "tasks", "coding");
    await mkdir(artifact, { recursive: true });
    const packetPath = join(artifact, "packet.json");
    const resultPath = join(artifact, "result.json");
    await writeFile(packetPath, JSON.stringify({
      orchestrator: binding.orchestrator,
      invocation_method: binding.invocation_method,
      requested_worker: "pi",
      requested_provider: binding.provider,
      model: binding.model,
      benchmark_case_id: "code_pool.localized_patch.easy.001",
      isolated_cwd: null,
    }), "utf8");
    await writeFile(resultPath, JSON.stringify({
      status: "ok",
      attempt: 1,
      isolated_cwd: "P:/tmp/codex-pi-coding-worktree",
      result_payload: { response: "{}", observations: [] },
    }), "utf8");
    let checkerPath = null;
    const run = await collectCapabilityRun({
      batchSummary: { batch_id: "batch-coding", entries: [{ task_id: "task-coding", artifact_dir: artifact, packet_path: packetPath, result_path: resultPath }] },
      binding,
      runId: "run-coding",
      checker: async ({ worktreePath }) => {
        checkerPath = worktreePath;
        throw new Error("fixture worktree unavailable");
      },
    });
    const observation = run.cases.find((value) => value.case_id === "code_pool.localized_patch.easy.001");
    assert.equal(checkerPath, "P:/tmp/codex-pi-coding-worktree");
    assert.equal(observation.isolated_cwd, "P:/tmp/codex-pi-coding-worktree");
    assert.equal(observation.execution_status, "blocked");
    assert.equal(observation.verification_state, "not_run");
    assert.equal(observation.failure_class, "harness");
  } finally {
    await rm(root, { recursive: true, force: true });
  }
});
