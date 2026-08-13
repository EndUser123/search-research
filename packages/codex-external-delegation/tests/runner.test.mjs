import test from "node:test";
import assert from "node:assert/strict";
import { EventEmitter } from "node:events";
import { PassThrough } from "node:stream";
import { mkdtemp, readFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { dirname, join } from "node:path";
import { buildCommand, redactText, runPacket, spawnSpec, workerEnvironment } from "../src/runner.mjs";

const basePacket = {
  schema_version: "2",
  task_id: "runner-test-001",
  worker: "opencode",
  model: "opencode-go/deepseek-v4-flash",
  objective: "Return a small structured result.",
  cwd: "P:/repo",
  mode: "read_only",
  allowed_paths: ["src/"],
  forbidden_actions: ["edit files"],
  output_schema: { required: ["value"] },
  verification: { commands: ["node --version"] },
};

function fakeSpawn({ stdout = "", stderr = "", exitCode = 0, delayMs = 0 } = {}) {
  return (_command, _args, _options) => {
    const child = new EventEmitter();
    child.stdin = new PassThrough();
    child.stdout = new PassThrough();
    child.stderr = new PassThrough();
    child.killed = false;
    child.kill = () => {
      child.killed = true;
      child.stdout.end();
      child.stderr.end();
      child.emit("close", null, "SIGTERM");
    };
    setTimeout(() => {
      if (child.killed) return;
      child.stdout.end(stdout);
      child.stderr.end(stderr);
      child.emit("close", exitCode, null);
    }, delayMs);
    return child;
  };
}

test("builds safe read-only commands for PI and OpenCode", () => {
  const pi = buildCommand({ ...basePacket, worker: "pi", model: "deepseek-v4-flash", requested_provider: "opencode-go" }, "do the task");
  assert.equal(pi.command, "pi.cmd");
  assert.equal(pi.args[pi.args.indexOf("--provider") + 1], "opencode-go");
  assert.ok(pi.args.includes("--no-context-files"));
  assert.ok(pi.args.includes("--no-extensions"));
  assert.ok(pi.args.includes("--no-skills"));
  assert.ok(pi.args.includes("--no-approve"));
  assert.ok(pi.args.includes("--tools"));
  assert.ok(pi.args.includes("read,grep,find,ls"));

  const piWriter = buildCommand({ ...basePacket, worker: "pi", model: "MiniMax-M3", requested_provider: "minimax", mode: "write" }, "do the task");
  assert.equal(piWriter.args[piWriter.args.indexOf("--tools") + 1], "read,grep,find,ls,edit,write");
  assert.equal(piWriter.args.includes("bash"), false);

  const opencode = buildCommand({ ...basePacket, worker: "opencode", model: "opencode-go/deepseek-v4-flash" }, "do the task");
  assert.equal(opencode.command, "opencode.cmd");
  assert.ok(opencode.args.includes("--format"));
  assert.ok(opencode.args.includes("json"));
  assert.ok(opencode.args.includes("external-readonly-primary"));
  assert.equal(opencode.args.includes("do the task"), false);
  assert.match(opencode.stdin, /do the task/);

  const qualified = buildCommand({
    ...basePacket,
    worker: "opencode",
    model: "deepseek-ai/deepseek-v4-pro",
    requested_provider: "nvidia-nim",
  }, "do the task");
  assert.equal(qualified.args[qualified.args.indexOf("--model") + 1], "nvidia-nim/deepseek-ai/deepseek-v4-pro");
  assert.equal(pi.stdin, "do the task");
});

test("keeps read-only tools while enabling thinking for reasoning tasks", () => {
  const mechanical = buildCommand({
    ...basePacket,
    worker: "pi",
    model: "inclusionai/ling-3.0-flash:free",
    requested_provider: "openrouter",
    task_type: "mechanical",
  }, "do the task");
  assert.equal(mechanical.args[mechanical.args.indexOf("--thinking") + 1], "off");

  const reasoning = buildCommand({
    ...basePacket,
    worker: "pi",
    model: "arcee-ai/trinity-large-thinking",
    requested_provider: "openrouter",
    task_type: "reasoning",
  }, "do the task");
  assert.equal(reasoning.args[reasoning.args.indexOf("--thinking") + 1], "low");
  assert.equal(reasoning.args[reasoning.args.indexOf("--tools") + 1], "read,grep,find,ls");

  const explicit = buildCommand({
    ...basePacket,
    worker: "pi",
    model: "arcee-ai/trinity-large-thinking",
    requested_provider: "openrouter",
    task_type: "reasoning",
    thinking: "high",
  }, "do the task");
  assert.equal(explicit.args[explicit.args.indexOf("--thinking") + 1], "high");

  const benchmark = buildCommand({
    ...basePacket,
    worker: "pi",
    model: "nvidia/nemotron-3-ultra-550b-a55b",
    requested_provider: "nvidia-nim",
    task_type: "BOUNDED_EXECUTION",
    task_class: "pi",
    requested_effort: "high",
  }, "do the task");
  assert.equal(benchmark.args[benchmark.args.indexOf("--thinking") + 1], "high");
});

test("wraps Windows command files through cmd.exe without enabling a shell", () => {
  const launch = spawnSpec("opencode.cmd", ["--version"], { platform: "win32", comspec: "C:\\Windows\\System32\\cmd.exe" });
  assert.equal(launch.command, "C:\\Windows\\System32\\cmd.exe");
  assert.deepEqual(launch.args, ["/d", "/s", "/c", "call opencode.cmd --version"]);
});

test("redacts quoted and unquoted credential fields", () => {
  const output = redactText('{"apiKey":"SECRET_A","authorization":"Bearer SECRET_B"} api_key=SECRET_C');
  assert.doesNotMatch(output, /SECRET_[A-C]/);
});

test("makes the bridge Node runtime visible to Windows worker wrappers", () => {
  const env = workerEnvironment({ worker: "pi" });
  const pathKey = Object.keys(env).find((key) => key.toLowerCase() === "path");
  assert.ok(pathKey);
  assert.ok(env[pathKey].split(";")[0].toLowerCase() === dirname(process.execPath).toLowerCase());

  const opencodeEnv = workerEnvironment({ worker: "opencode" });
  const opencodePathKey = Object.keys(opencodeEnv).find((key) => key.toLowerCase() === "path");
  assert.ok(opencodePathKey);
  assert.ok(opencodeEnv[opencodePathKey].split(";")[0].toLowerCase() === dirname(process.execPath).toLowerCase());

  const untrustedEnv = workerEnvironment({ worker: "pi", env: { NODE_OPTIONS: "--require=untrusted.js", CODEX_PI_TEST_INJECT: "1" } });
  assert.notEqual(untrustedEnv.CODEX_PI_TEST_INJECT, "1");
});

test("normalizes a successful worker response and preserves artifacts", async () => {
  const artifactDir = await mkdtemp(join(tmpdir(), "codex-delegation-test-"));
  const result = await runPacket(basePacket, {
    artifactDir,
    spawnImpl: fakeSpawn({ stdout: '<external-delegation-result>{"status":"ok","result_payload":{"value":42}}</external-delegation-result>' }),
  });

  assert.equal(result.status, "ok");
  assert.equal(result.result_payload.value, 42);
  assert.equal(result.failure_class, "none");
  assert.equal(result.effort_receipt.effort_support, "not_requested");
  assert.equal(result.command_receipt.token_cap_flags_present, false);
  assert.match(await readFile(join(artifactDir, "stdout.log"), "utf8"), /result_payload/);
  assert.match(await readFile(join(artifactDir, "result.json"), "utf8"), /"status": "ok"/);
});

test("records benchmark identity, requested effort, usage, and command evidence", async () => {
  const artifactDir = await mkdtemp(join(tmpdir(), "codex-delegation-benchmark-receipt-"));
  const result = await runPacket({
    ...basePacket,
    worker: "pi",
    requested_worker: "pi",
    requested_provider: "zai",
    model: "glm-5.2",
    invocation_method: "pi",
    task_domain: "reasoning",
    benchmark_role: "reasoning",
    benchmark_lane: "reasoning",
    benchmark_case_id: "reasoning.standard.001",
    benchmark_binding_id: "zai/glm-5.2",
    benchmark_manifest_id: "manifest-1",
    benchmark_manifest_sha256: "hash-1",
    quota_pool: "zai",
    provider_account: "account-1",
    provider_scope: "shared_subscription",
    requested_effort: "high",
  }, {
    artifactDir,
    spawnImpl: fakeSpawn({
      stdout: '{"type":"message_start","message":{"provider":"zai","model":"glm-5.2","usage":{"input":12,"output":8,"reasoning":4,"totalTokens":20}}}\n<external-delegation-result>{"status":"ok","result_payload":{"value":42}}</external-delegation-result>',
    }),
  });

  assert.equal(result.status, "ok");
  assert.equal(result.benchmark_identity.benchmark_case_id, "reasoning.standard.001");
  assert.equal(result.effort_receipt.requested_effort, "high");
  assert.equal(result.effort_receipt.native_effort, "high");
  assert.equal(result.effort_receipt.effective_effort, null);
  assert.equal(result.usage_receipt.observed, true);
  assert.equal(result.usage_receipt.final.reasoning, 4);
  assert.equal(result.command_receipt.token_cap_flags_present, false);
  assert.match(await readFile(join(artifactDir, "attempt-1.json"), "utf8"), /token_cap_flags_present/);
});

test("records bounded recovery diagnostics for quota and rate-limit failures", async () => {
  const artifactDir = await mkdtemp(join(tmpdir(), "codex-delegation-recovery-diagnostics-"));
  const result = await runPacket({
    ...basePacket,
    worker: "pi",
    requested_worker: "pi",
    requested_provider: "minimax",
    model: "MiniMax-M3",
    invocation_method: "pi",
  }, {
    artifactDir,
    spawnImpl: fakeSpawn({
      stdout: [
        '{"type":"auto_retry_start","attempt":1,"delayMs":2000}',
        '{"message":{"error":{"type":"rate_limit_error"}}}',
        "429 rate limit: token plan usage limit reached; retry after 5 hours; request_id=req-123",
      ].join("\n"),
    }),
  });

  assert.equal(result.failure_class, "auth_or_quota");
  assert.deepEqual(result.failure_diagnostics.signals, ["quota_exhausted", "rate_limit"]);
  assert.deepEqual(result.failure_diagnostics.provider_error_types, ["rate_limit_error"]);
  assert.equal(result.failure_diagnostics.retryable, true);
  assert.equal(result.failure_diagnostics.retry_after_ms, 5 * 60 * 60 * 1000);
  assert.equal(result.failure_diagnostics.internal_retry_count, 1);
  assert.equal(result.failure_diagnostics.recovery_state, "defer_until_provider_reset_or_capacity");
});

test("blocks benchmark worktree provisioning when the scratch-capacity guard is not met", async () => {
  const artifactDir = await mkdtemp(join(tmpdir(), "codex-delegation-capacity-preflight-"));
  let spawnCalls = 0;
  const minimumFreeBytes = Number.MAX_SAFE_INTEGER;
  const result = await runPacket({
    ...basePacket,
    task_id: "benchmark-capacity-preflight",
    worker: "pi",
    requested_worker: "pi",
    requested_provider: "zai",
    model: "glm-5.2",
    invocation_method: "pi",
    mode: "write",
    write_scope: ["src/example.mjs"],
    benchmark_manifest_id: "capability-difficulty-test",
    benchmark_min_free_bytes: minimumFreeBytes,
    worktree_request: { worktreeRoot: artifactDir, intendedFiles: ["src/example.mjs"] },
  }, {
    artifactDir,
    spawnImpl: (...args) => {
      spawnCalls += 1;
      return fakeSpawn({})(...args);
    },
  });

  assert.equal(result.status, "blocked");
  assert.equal(result.failure_class, "worktree_capacity");
  assert.equal(result.benchmark_capacity_preflight.status, "blocked");
  assert.ok(result.benchmark_capacity_preflight.free_bytes < minimumFreeBytes);
  assert.equal(result.failure_diagnostics.retryable, true);
  assert.equal(result.failure_diagnostics.recovery_state, "free_scratch_then_retry");
  assert.equal(spawnCalls, 0);
});

test("preserves isolated worktree identity in the result receipt", async () => {
  const artifactDir = await mkdtemp(join(tmpdir(), "codex-delegation-worktree-receipt-"));
  const result = await runPacket({
    ...basePacket,
    worker: "pi",
    requested_worker: "pi",
    requested_provider: "minimax",
    model: "MiniMax-M3",
    invocation_method: "pi",
    isolated_cwd: "P:/tmp/codex-pi-worktree",
    worktree: { worktree_path: "P:/tmp/codex-pi-worktree" },
  }, {
    artifactDir,
    spawnImpl: fakeSpawn({
      stdout: '{"type":"message_start","message":{"provider":"minimax","model":"MiniMax-M3"}}\n<external-delegation-result>{"status":"ok","result_payload":{"value":42}}</external-delegation-result>',
    }),
  });
  assert.equal(result.status, "ok");
  assert.equal(result.isolated_cwd, "P:/tmp/codex-pi-worktree");
  assert.equal(result.worktree_path, "P:/tmp/codex-pi-worktree");
});

test("uses the final valid marker when the worker echoes a placeholder marker", async () => {
  const artifactDir = await mkdtemp(join(tmpdir(), "codex-delegation-test-"));
  const result = await runPacket(basePacket, {
    artifactDir,
    spawnImpl: fakeSpawn({
      stdout: '<external-delegation-result>{"status":"ok","result_payload":{"value":null}}</external-delegation-result>\nworker stream\n<external-delegation-result>{"status":"ok","result_payload":{"value":42}}</external-delegation-result>',
    }),
  });
  assert.equal(result.status, "ok");
  assert.equal(result.failure_class, "none");
  assert.equal(result.result_payload.value, 42);
});

test("classifies malformed successful output as protocol failure", async () => {
  const artifactDir = await mkdtemp(join(tmpdir(), "codex-delegation-test-"));
  const result = await runPacket(basePacket, {
    artifactDir,
    spawnImpl: fakeSpawn({ stdout: "worker prose without marker" }),
  });
  assert.equal(result.status, "failed");
  assert.equal(result.failure_class, "protocol_error");
});

test("rejects a marker that omits required output fields", async () => {
  const artifactDir = await mkdtemp(join(tmpdir(), "codex-delegation-test-"));
  const result = await runPacket(basePacket, {
    artifactDir,
    spawnImpl: fakeSpawn({ stdout: '<external-delegation-result>{"status":"ok","result_payload":{}}</external-delegation-result>' }),
  });
  assert.equal(result.status, "failed");
  assert.equal(result.failure_class, "contract_error");
  assert.deepEqual(result.missing_result_fields, ["value"]);
});

test("kills timed-out workers and records timeout", async () => {
  const artifactDir = await mkdtemp(join(tmpdir(), "codex-delegation-test-"));
  const result = await runPacket({ ...basePacket, timeout_ms: 15 }, {
    artifactDir,
    spawnImpl: fakeSpawn({ delayMs: 100 }),
  });
  assert.equal(result.status, "failed");
  assert.equal(result.failure_class, "timeout");
  assert.equal(result.timed_out, true);
});

test("halts after an OpenCode failure even when legacy fallback fields are present", async () => {
  const artifactDir = await mkdtemp(join(tmpdir(), "codex-delegation-test-"));
  let spawnCount = 0;
  const result = await runPacket({
    ...basePacket,
    fallback_worker: "pi",
    fallback_model: "minimax/MiniMax-M3",
  }, {
    artifactDir,
    spawnImpl: (...args) => {
      spawnCount += 1;
      return fakeSpawn({ exitCode: 1, stderr: "connection refused" })(...args);
    },
  });
  assert.equal(result.status, "failed");
  assert.equal(result.failure_class, "provider_unavailable");
  assert.equal(result.attempt, 1);
  assert.equal(spawnCount, 1);
});

test("halts after a Pi failure without trying another worker", async () => {
  const artifactDir = await mkdtemp(join(tmpdir(), "codex-delegation-test-"));
  let spawnCount = 0;
  const result = await runPacket({
    ...basePacket,
    worker: "pi",
    requested_worker: "pi",
    requested_provider: "pi",
    requested_agent: null,
    agent: null,
    fallback_worker: "opencode",
    fallback_model: "minimax/MiniMax-M3",
  }, {
    artifactDir,
    spawnImpl: (...args) => {
      spawnCount += 1;
      return fakeSpawn({ exitCode: 1, stderr: "connection refused" })(...args);
    },
  });
  assert.equal(result.status, "failed");
  assert.equal(result.failure_class, "provider_unavailable");
  assert.equal(result.attempt, 1);
  assert.equal(spawnCount, 1);
});

test("does not accept a valid payload when OpenCode substituted the requested agent", async () => {
  const artifactDir = await mkdtemp(join(tmpdir(), "codex-delegation-test-"));
  const result = await runPacket(basePacket, {
    artifactDir,
    spawnImpl: fakeSpawn({
      stderr: 'agent "external-readonly" is a subagent, not a primary agent. Falling back to default agent',
      stdout: '{"type":"text","part":{"text":"<external-delegation-result>{\\"status\\":\\"ok\\",\\"result_payload\\":{\\"value\\":42}}</external-delegation-result>"}}',
    }),
  });
  assert.equal(result.status, "failed");
  assert.equal(result.failure_class, "identity_mismatch");
  assert.equal(result.result_payload, null);
});

test("rejects a successful Pi payload when runtime identity differs", async () => {
  const artifactDir = await mkdtemp(join(tmpdir(), "codex-delegation-test-"));
  const result = await runPacket({
    ...basePacket,
    worker: "pi",
    requested_worker: "pi",
    requested_provider: "opencode-go",
    model: "deepseek-v4-flash",
  }, {
    artifactDir,
    spawnImpl: fakeSpawn({
      stdout: '{"type":"message_start","message":{"provider":"minimax","model":"MiniMax-M3"}}\n<external-delegation-result>{"status":"ok","result_payload":{"value":42}}</external-delegation-result>',
    }),
  });
  assert.equal(result.status, "failed");
  assert.equal(result.failure_class, "identity_mismatch");
  assert.equal(result.result_payload, null);
});

test("accepts a provider-qualified packet model when Pi reports its canonical model ID", async () => {
  const artifactDir = await mkdtemp(join(tmpdir(), "codex-delegation-test-"));
  const result = await runPacket({
    ...basePacket,
    worker: "pi",
    requested_worker: "pi",
    requested_provider: "minimax",
    model: "minimax/MiniMax-M3",
  }, {
    artifactDir,
    spawnImpl: fakeSpawn({
      stdout: '{"type":"message_start","message":{"provider":"minimax","model":"MiniMax-M3"}}\n<external-delegation-result>{"status":"ok","result_payload":{"value":42}}</external-delegation-result>',
    }),
  });
  assert.equal(result.status, "ok");
  assert.equal(result.failure_class, "none");
  assert.equal(result.result_payload.value, 42);
});

test("does not classify task content mentioning quota as a provider failure", async () => {
  const artifactDir = await mkdtemp(join(tmpdir(), "codex-delegation-test-"));
  const result = await runPacket({
    ...basePacket,
    worker: "pi",
    requested_worker: "pi",
    requested_provider: "nvidia-nim",
    model: "deepseek-ai/deepseek-v4-flash",
  }, {
    artifactDir,
    spawnImpl: fakeSpawn({
      stdout: '{"type":"message_start","message":{"provider":"nvidia-nim","model":"deepseek-ai/deepseek-v4-flash"}}\nThe inspected source documents quota and rate limits.\n<external-delegation-result>{"status":"ok","result_payload":{"value":"quota terminology is source content"}}</external-delegation-result>',
    }),
  });
  assert.equal(result.status, "ok");
  assert.equal(result.failure_class, "none");
  assert.equal(result.provider, "nvidia-nim");
  assert.equal(result.result_payload.value, "quota terminology is source content");
});

test("blocks malformed packets before spawning a worker", async () => {
  const artifactDir = await mkdtemp(join(tmpdir(), "codex-delegation-test-"));
  let spawned = false;
  const result = await runPacket({ task_id: "invalid" }, {
    artifactDir,
    spawnImpl: () => { spawned = true; throw new Error("must not spawn"); },
  });
  assert.equal(result.status, "blocked");
  assert.equal(result.failure_class, "contract_error");
  assert.equal(spawned, false);
});

test("classifies a missing worker command without retrying", async () => {
  const artifactDir = await mkdtemp(join(tmpdir(), "codex-delegation-test-"));
  let spawnCount = 0;
  const result = await runPacket(basePacket, {
    artifactDir,
    spawnImpl: () => {
      spawnCount += 1;
      const child = new EventEmitter();
      child.stdin = new PassThrough();
      child.stdout = new PassThrough();
      child.stderr = new PassThrough();
      queueMicrotask(() => child.emit("error", Object.assign(new Error("missing worker"), { code: "ENOENT" })));
      return child;
    },
  });
  assert.equal(result.status, "failed");
  assert.equal(result.failure_class, "command_missing");
  assert.equal(result.attempt, 1);
  assert.equal(spawnCount, 1);
});

// --- Result-contract classification regressions (task spec §2) -------------------

// A policy-enforced worker refusal (e.g. read-only worker declining to mutate)
// must be classified as `worker_blocked`, NOT `none`, with the worker's
// blocked_reason preserved in the envelope. A correct policy refusal is
// neither a generic failure nor a contract error.
test("classifies worker policy refusal as worker_blocked with preserved reason", async () => {
  const artifactDir = await mkdtemp(join(tmpdir(), "codex-delegation-test-"));
  const result = await runPacket(basePacket, {
    artifactDir,
    spawnImpl: fakeSpawn({
      stdout: '<external-delegation-result>{"status":"blocked","result_payload":{"observations":"Cannot mutate: read-only profile","blocked_reason":"Read-only worker cannot perform write/create file operations. The task objective requests file creation which violates the read-only constraint."}}</external-delegation-result>',
    }),
  });
  assert.equal(result.status, "blocked");
  assert.equal(result.failure_class, "worker_blocked");
  assert.ok(result.result_payload, "blocked reason payload must be preserved");
  assert.match(String(result.result_payload.blocked_reason), /read-only/i);
  assert.match(await readFile(join(artifactDir, "stdout.log"), "utf8"), /result_payload/);
});

// A blocked status without a `blocked_reason` is still `worker_blocked`,
// but the envelope records that the reason was missing for diagnostics.
test("classifies blocked-without-reason as worker_blocked", async () => {
  const artifactDir = await mkdtemp(join(tmpdir(), "codex-delegation-test-"));
  const result = await runPacket(basePacket, {
    artifactDir,
    spawnImpl: fakeSpawn({
      stdout: '<external-delegation-result>{"status":"blocked","result_payload":{"observations":"blocked but no reason supplied"}}</external-delegation-result>',
    }),
  });
  assert.equal(result.status, "blocked");
  assert.equal(result.failure_class, "worker_blocked");
  assert.ok(result.result_payload);
});

// A successful result preserves the required field and reports failure_class = "none".
test("classifies successful result as ok with failure_class none", async () => {
  const artifactDir = await mkdtemp(join(tmpdir(), "codex-delegation-test-"));
  const result = await runPacket(basePacket, {
    artifactDir,
    spawnImpl: fakeSpawn({
      stdout: '<external-delegation-result>{"status":"ok","result_payload":{"value":"src/SAMPLE.txt contains 1 file"}}</external-delegation-result>',
    }),
  });
  assert.equal(result.status, "ok");
  assert.equal(result.failure_class, "none");
  assert.equal(result.result_payload.value, "src/SAMPLE.txt contains 1 file");
});

// A worker failure (e.g. crash, non-zero exit, garbage stream without a
// `blocked` marker) must be classified as `failed` with the worker-class
// failure class — NOT `blocked` and NOT `ok`.
test("classifies worker failure as failed with failure class", async () => {
  const artifactDir = await mkdtemp(join(tmpdir(), "codex-delegation-test-"));
  const result = await runPacket(basePacket, {
    artifactDir,
    spawnImpl: fakeSpawn({ exitCode: 1, stderr: "provider_unavailable" }),
  });
  assert.equal(result.status, "failed");
  assert.notEqual(result.failure_class, "none");
  assert.notEqual(result.failure_class, "worker_blocked");
  assert.notEqual(result.failure_class, "contract_error");
});

// A contract failure (invalid packet) produces failure_class = contract_error,
// distinct from worker_blocked. This guards against the regression where a
// `worker_blocked` envelope could mask a real contract violation.
test("distinguishes contract_error from worker_blocked", async () => {
  const artifactDir = await mkdtemp(join(tmpdir(), "codex-delegation-test-"));
  const result = await runPacket({ task_id: "minimal-invalid" }, {
    artifactDir,
    spawnImpl: () => { throw new Error("must not spawn"); },
  });
  assert.equal(result.status, "blocked");
  assert.equal(result.failure_class, "contract_error");
  assert.notEqual(result.failure_class, "worker_blocked");
});

// --- Optional typed output_schema.properties (backward-compatible) ------------
//
// When a packet declares output_schema.properties, every declared property
// whose name is present in result_payload must have a value matching the
// declared type. Arrays and null are distinguished from objects. A mismatch
// becomes status=failed with failure_class=contract_error and the
// result_payload is cleared; diagnostics name field, expected_type, and
// observed_type. Blocked payloads and existing failure classes are preserved.

const typedSchemaPacket = {
  ...basePacket,
  output_schema: {
    required: ["observations"],
    properties: {
      observations: { type: "array" },
    },
  },
};

// A successful run whose payload matches the typed schema must pass with
// status=ok and failure_class=none; the typed observations are preserved.
test("accepts a result whose payload matches the typed output_schema", async () => {
  const artifactDir = await mkdtemp(join(tmpdir(), "codex-delegation-test-"));
  const result = await runPacket(typedSchemaPacket, {
    artifactDir,
    spawnImpl: fakeSpawn({
      stdout: '<external-delegation-result>{"status":"ok","result_payload":{"observations":["a","b"]}}</external-delegation-result>',
    }),
  });
  assert.equal(result.status, "ok");
  assert.equal(result.failure_class, "none");
  assert.deepEqual(result.result_payload.observations, ["a", "b"]);
});

// A successful run whose payload declares `observations` as a string while
// the schema requires `array` must fail with contract_error, a cleared
// result_payload, and deterministic diagnostics naming field, expected_type,
// observed_type.
test("rejects a result whose declared present property has the wrong type", async () => {
  const artifactDir = await mkdtemp(join(tmpdir(), "codex-delegation-test-"));
  const result = await runPacket(typedSchemaPacket, {
    artifactDir,
    spawnImpl: fakeSpawn({
      stdout: '<external-delegation-result>{"status":"ok","result_payload":{"observations":"not an array"}}</external-delegation-result>',
    }),
  });
  assert.equal(result.status, "failed");
  assert.equal(result.failure_class, "contract_error");
  assert.equal(result.result_payload, null);
  assert.ok(Array.isArray(result.schema_errors));
  assert.equal(result.schema_errors.length, 1);
  const first = result.schema_errors[0];
  assert.equal(first.field, "observations");
  assert.equal(first.expected_type, "array");
  assert.equal(first.observed_type, "string");
  assert.deepEqual(result.contract_errors, ["result_payload_schema_mismatch"]);
});

// Arrays are distinguished from objects (typeof === "object") and null is
// treated separately: a payload value of null must match a declared
// `null` type, and an array must not satisfy a declared `object` type.
test("distinguishes arrays from objects and treats null separately", async () => {
  const artifactDir = await mkdtemp(join(tmpdir(), "codex-delegation-test-"));
  const arrayAsObject = await runPacket(typedSchemaPacket, {
    artifactDir,
    spawnImpl: fakeSpawn({
      stdout: '<external-delegation-result>{"status":"ok","result_payload":{"observations":{}}}</external-delegation-result>',
    }),
  });
  assert.equal(arrayAsObject.status, "failed");
  assert.equal(arrayAsObject.failure_class, "contract_error");
  assert.equal(arrayAsObject.schema_errors[0].field, "observations");
  assert.equal(arrayAsObject.schema_errors[0].expected_type, "array");
  assert.equal(arrayAsObject.schema_errors[0].observed_type, "object");

  const artifactDir2 = await mkdtemp(join(tmpdir(), "codex-delegation-test-"));
  const objectAsArray = await runPacket({
    ...basePacket,
    output_schema: {
      required: ["meta"],
      properties: { meta: { type: "object" } },
    },
  }, {
    artifactDir: artifactDir2,
    spawnImpl: fakeSpawn({
      stdout: '<external-delegation-result>{"status":"ok","result_payload":{"meta":[1,2,3]}}</external-delegation-result>',
    }),
  });
  assert.equal(objectAsArray.status, "failed");
  assert.equal(objectAsArray.failure_class, "contract_error");
  assert.equal(objectAsArray.schema_errors[0].expected_type, "object");
  assert.equal(objectAsArray.schema_errors[0].observed_type, "array");

  const artifactDir3 = await mkdtemp(join(tmpdir(), "codex-delegation-test-"));
  const nullOk = await runPacket({
    ...basePacket,
    output_schema: {
      required: ["maybe"],
      properties: { maybe: { type: "null" } },
    },
  }, {
    artifactDir: artifactDir3,
    spawnImpl: fakeSpawn({
      stdout: '<external-delegation-result>{"status":"ok","result_payload":{"maybe":null}}</external-delegation-result>',
    }),
  });
  assert.equal(nullOk.status, "ok");
  assert.equal(nullOk.failure_class, "none");
  assert.equal(nullOk.result_payload.maybe, null);

  const artifactDir4 = await mkdtemp(join(tmpdir(), "codex-delegation-test-"));
  const nullWrong = await runPacket({
    ...basePacket,
    output_schema: {
      required: ["maybe"],
      properties: { maybe: { type: "null" } },
    },
  }, {
    artifactDir: artifactDir4,
    spawnImpl: fakeSpawn({
      stdout: '<external-delegation-result>{"status":"ok","result_payload":{"maybe":{}}}</external-delegation-result>',
    }),
  });
  assert.equal(nullWrong.status, "failed");
  assert.equal(nullWrong.failure_class, "contract_error");
  assert.equal(nullWrong.schema_errors[0].expected_type, "null");
  assert.equal(nullWrong.schema_errors[0].observed_type, "object");
});

// Missing-required-field behavior must run before the typed-property check,
// so a payload missing the required field is reported as missing rather
// than being misclassified by the type validator.
test("reports missing required fields before validating declared properties", async () => {
  const artifactDir = await mkdtemp(join(tmpdir(), "codex-delegation-test-"));
  const result = await runPacket(typedSchemaPacket, {
    artifactDir,
    spawnImpl: fakeSpawn({
      stdout: '<external-delegation-result>{"status":"ok","result_payload":{}}</external-delegation-result>',
    }),
  });
  assert.equal(result.status, "failed");
  assert.equal(result.failure_class, "contract_error");
  assert.deepEqual(result.missing_result_fields, ["observations"]);
  assert.equal(result.result_payload, null);
});

// Blocked results must keep their payloads intact even when the schema
// would otherwise mismatch. Existing failure classes (worker_blocked)
// must not be overwritten by the typed-property validator.
test("preserves blocked payloads and existing failure classes", async () => {
  const artifactDir = await mkdtemp(join(tmpdir(), "codex-delegation-test-"));
  const result = await runPacket(typedSchemaPacket, {
    artifactDir,
    spawnImpl: fakeSpawn({
      stdout: '<external-delegation-result>{"status":"blocked","result_payload":{"observations":"not an array","blocked_reason":"policy refusal"}}</external-delegation-result>',
    }),
  });
  assert.equal(result.status, "blocked");
  assert.equal(result.failure_class, "worker_blocked");
  assert.ok(result.result_payload);
  assert.match(String(result.result_payload.blocked_reason), /policy refusal/);
});

// Legacy packets without output_schema.properties must behave exactly as
// before: a successful payload whose required field has any shape is
// accepted without schema-mismatch errors.
test("preserves legacy required-only behavior when no properties are declared", async () => {
  const artifactDir = await mkdtemp(join(tmpdir(), "codex-delegation-test-"));
  const result = await runPacket({
    ...basePacket,
    output_schema: { required: ["value"] },
  }, {
    artifactDir,
    spawnImpl: fakeSpawn({
      stdout: '<external-delegation-result>{"status":"ok","result_payload":{"value":{"any":"shape"},"extra":"ignored"}}</external-delegation-result>',
    }),
  });
  assert.equal(result.status, "ok");
  assert.equal(result.failure_class, "none");
  assert.equal(result.result_payload.value.any, "shape");
});
