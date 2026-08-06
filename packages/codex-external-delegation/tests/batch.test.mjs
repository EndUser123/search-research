import test from "node:test";
import assert from "node:assert/strict";
import { mkdtemp, readFile, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { validatePacket } from "../src/contract.mjs";
import {
  expandBatchManifest,
  routeBatch,
  runBatch,
  validateBatchManifest,
} from "../src/batch.mjs";

async function artifactRoot() {
  return mkdtemp(join(tmpdir(), "codex-batch-artifacts-"));
}

function inputFor(taskId, overrides = {}) {
  return {
    objective: `Inspect ${taskId}.`,
    cwd: "P:/packages/codex-external-delegation",
    mode: "read_only",
    allowed_paths: ["src/"],
    verification_commands: ["node --version"],
    output_schema: { required: ["observations"] },
    ...overrides,
  };
}

function explicitInput(taskId, provider = "minimax") {
  return inputFor(taskId, {
    requested_worker: "pi",
    requested_provider: provider,
    model: "MiniMax-M3",
  });
}

function fakeCompiler(calls = [], { provider = "minimax", blocked = false } = {}) {
  return (input) => {
    calls.push(input);
    const packet = {
      schema_version: "2",
      invocation_id: input.task_id,
      parent_run_id: input.parent_run_id,
      task_id: input.task_id,
      role: "BOUNDED_EXECUTION",
      selected_lane: "pi",
      requested_worker: "pi",
      requested_provider: input.requested_provider || provider,
      requested_model: input.model || "MiniMax-M3",
      worker: "pi",
      model: input.model || "MiniMax-M3",
      objective: input.objective,
      cwd: input.cwd,
      allowed_paths: input.allowed_paths,
      mode: input.mode,
      write_scope: input.write_scope || [],
      isolated_cwd: input.isolated_cwd || null,
      worktree_request: input.worktree_request || null,
      output_schema: input.output_schema,
      timeout_seconds: 30,
      timeout_ms: 30_000,
      containment: "read_only",
      verification: { commands: input.verification_commands },
      model_selection: blocked ? {
        status: "no_eligible_candidate",
        reason: "test blocked route",
      } : {
        status: "selected",
        candidate_id: `${input.requested_provider || provider}/test-model`,
        provider: input.requested_provider || provider,
        model: input.model || "MiniMax-M3",
        quota_pool: input.quota_pool || input.requested_provider || provider,
        confidence: "measured",
        reasons: ["test_selection"],
      },
    };
    return {
      classification: blocked
        ? { role: "BOUNDED_EXECUTION", lane: "pi", eligible: true, reason: "test" }
        : { role: "BOUNDED_EXECUTION", lane: "pi", eligible: true, reason: "test" },
      packet,
    };
  };
}

function manifest(root, tasks, overrides = {}) {
  return {
    schema_version: "batch.v1",
    batch_id: "batch-test",
    artifact_root: root,
    concurrency: { max_in_flight: 2, by_provider: {} },
    tasks,
    ...overrides,
  };
}

test("validates the batch.v1 envelope and rejects the old packet-shaped design", () => {
  assert.deepEqual(validateBatchManifest({ schema_version: "batch.v1" }).sort(), [
    "artifact_root: must be a non-empty path",
    "batch_id: must be a safe non-empty identifier",
    "concurrency: must be an object",
    "tasks: must be a non-empty array",
  ].sort());
  const errors = validateBatchManifest({
    schema_version: "batch.v1",
    batch_id: "batch",
    artifact_root: "P:/tmp/artifacts",
    concurrency: { max_in_flight: 1, by_provider: {} },
    tasks: [{ task_id: "t", repetitions: 1, candidate_mode: "automatic", packet: {} }],
  });
  assert.match(errors.join(";"), /input: must be an object/);
});

test("expands repetitions deterministically and derives isolated artifact paths", async () => {
  const root = await artifactRoot();
  const expanded = expandBatchManifest(manifest(root, [
    { task_id: "extract", repetitions: 2, candidate_mode: "automatic", input: inputFor("extract") },
    { task_id: "verify", repetitions: 1, candidate_mode: "explicit", input: explicitInput("verify", "zai") },
  ]));
  assert.deepEqual(expanded.map((entry) => entry.repetition_id), [
    "batch-test--extract--r001",
    "batch-test--extract--r002",
    "batch-test--verify--r001",
  ]);
  assert.equal(expanded[0].input.task_id, expanded[0].repetition_id);
  assert.equal(expanded[0].input.parent_run_id, "batch-test");
  assert.equal(expanded[2].candidate_mode, "explicit");
  assert.match(expanded[1].artifact_dir, /tasks[\\/]extract[\\/]rep-002$/);
});

test("routes automatic and explicit candidates without worker calls and redacts artifacts", async () => {
  const root = await artifactRoot();
  const calls = [];
  const result = await routeBatch(manifest(root, [
    { task_id: "automatic", repetitions: 2, candidate_mode: "automatic", input: inputFor("automatic", { api_key: "do-not-write" }) },
    { task_id: "explicit", repetitions: 1, candidate_mode: "explicit", input: explicitInput("explicit", "zai") },
  ]), {
    compile: fakeCompiler(calls),
    validate: validatePacket,
  });
  assert.equal(result.status, "ok");
  assert.deepEqual(result.counts, { total: 3, routed: 3, blocked: 0, succeeded: 0, failed: 0 });
  assert.equal(calls.length, 3);
  assert.ok(calls.every((input) => !Object.hasOwn(input, "model") || input.requested_provider));
  assert.equal(result.entries[2].selection.provider, "zai");
  const routeText = await readFile(result.route_path, "utf8");
  assert.doesNotMatch(routeText, /do-not-write/);
  const packetText = await readFile(result.entries[0].packet_path, "utf8");
  assert.doesNotMatch(packetText, /do-not-write/);
  const manifestText = await readFile(result.manifest_path, "utf8");
  assert.doesNotMatch(manifestText, /do-not-write/);
});

test("keeps a blocked route visible for that repetition without fallback", async () => {
  const root = await artifactRoot();
  const calls = [];
  const result = await routeBatch(manifest(root, [
    { task_id: "blocked", repetitions: 1, candidate_mode: "automatic", input: inputFor("blocked") },
    { task_id: "accepted", repetitions: 1, candidate_mode: "explicit", input: explicitInput("accepted") },
  ]), {
    compile: (input) => fakeCompiler(calls, { blocked: input.task_id.includes("blocked") })(input),
    validate: validatePacket,
  });
  assert.equal(result.status, "blocked");
  assert.equal(result.counts.blocked, 1);
  assert.equal(result.entries[0].failure_class, "no_eligible_external_candidate");
  assert.equal(result.entries[1].status, "ok");
  assert.equal(calls.length, 2);
});

test("preserves write scope and deferred worktree requirements for execution", async () => {
  const root = await artifactRoot();
  const result = await routeBatch(manifest(root, [{
    task_id: "writer",
    repetitions: 1,
    candidate_mode: "explicit",
    input: explicitInput("writer", "minimax"),
  }]), {
    compile: (input) => fakeCompiler([], { provider: "minimax" })({
      ...input,
      mode: "write",
      write_scope: ["src/batch.mjs"],
      worktree_request: { worktreeRoot: "P:/tmp/worktrees", intendedFiles: ["src/batch.mjs"] },
    }),
    validate: validatePacket,
  });
  assert.equal(result.status, "ok");
  assert.deepEqual(result.plans[0].packet.write_scope, ["src/batch.mjs"]);
  assert.equal(result.plans[0].packet.worktree_request.worktreeRoot, "P:/tmp/worktrees");
});

test("runs each routed repetition once, respects global/provider limits, and continues after failure", async () => {
  const root = await artifactRoot();
  const tasks = [
    { task_id: "alpha-1", repetitions: 1, candidate_mode: "explicit", input: explicitInput("alpha-1", "alpha") },
    { task_id: "beta-1", repetitions: 1, candidate_mode: "explicit", input: explicitInput("beta-1", "beta") },
    { task_id: "alpha-2", repetitions: 1, candidate_mode: "explicit", input: explicitInput("alpha-2", "alpha") },
    { task_id: "beta-2", repetitions: 1, candidate_mode: "explicit", input: explicitInput("beta-2", "beta") },
  ];
  const batch = manifest(root, tasks, {
    concurrency: { max_in_flight: 2, by_provider: { alpha: 1, beta: 2 } },
  });
  const calls = [];
  let active = 0;
  let maxActive = 0;
  let alphaActive = 0;
  let maxAlpha = 0;
  const result = await runBatch(batch, {
    compile: (input) => {
      const compiled = fakeCompiler([], { provider: input.requested_provider })(input);
      compiled.packet.model_selection.quota_pool = input.requested_provider;
      return compiled;
    },
    validate: validatePacket,
    run: async (packet) => {
      calls.push(packet.task_id);
      active += 1;
      maxActive = Math.max(maxActive, active);
      if (packet.requested_provider === "alpha") {
        alphaActive += 1;
        maxAlpha = Math.max(maxAlpha, alphaActive);
      }
      await new Promise((resolve) => setTimeout(resolve, packet.task_id.includes("alpha-1") ? 15 : 5));
      active -= 1;
      if (packet.requested_provider === "alpha") alphaActive -= 1;
      if (packet.task_id.includes("alpha-1")) throw new Error("intentional worker failure");
      return {
        schema_version: "2",
        task_id: packet.task_id,
        status: "ok",
        failure_class: "none",
        result_payload: { observations: packet.task_id },
        attempt: 1,
        exit_code: 0,
        timed_out: false,
        artifact_dir: null,
      };
    },
  });
  assert.equal(result.status, "failed");
  assert.deepEqual(result.counts, { total: 4, routed: 4, blocked: 0, succeeded: 3, failed: 1 });
  assert.equal(calls.length, 4);
  assert.equal(new Set(calls).size, 4);
  assert.ok(maxActive <= 2);
  assert.equal(maxAlpha, 1);
  assert.deepEqual(result.entries.map((entry) => entry.source_task_id), tasks.map((task) => task.task_id));
  assert.equal(result.entries[0].failure_class, "batch_runner_error");
  assert.equal(result.entries[3].status, "ok");
  const summaryText = await readFile(result.summary_path, "utf8");
  assert.match(summaryText, /batch-summary/);
});

test("dry-run routes but never invokes the worker", async () => {
  const root = await artifactRoot();
  let runCalls = 0;
  const result = await runBatch(manifest(root, [
    { task_id: "dry", repetitions: 1, candidate_mode: "explicit", input: explicitInput("dry") },
  ]), {
    compile: fakeCompiler(),
    validate: validatePacket,
    run: async () => { runCalls += 1; throw new Error("must not run"); },
    dryRun: true,
  });
  assert.equal(result.status, "dry_run");
  assert.equal(result.dry_run, true);
  assert.equal(runCalls, 0);
});

test("does not start workers when route artifact setup fails", async () => {
  const root = await artifactRoot();
  await writeFile(join(root, "broken-batch"), "not a directory", "utf8");
  let runCalls = 0;
  const result = await runBatch(manifest(root, [
    { task_id: "setup-failure", repetitions: 1, candidate_mode: "explicit", input: explicitInput("setup-failure") },
  ], { batch_id: "broken-batch" }), {
    compile: fakeCompiler(),
    validate: validatePacket,
    run: async () => { runCalls += 1; throw new Error("must not run"); },
  });
  assert.equal(result.failure_class, "artifact_error");
  assert.equal(runCalls, 0);
});
