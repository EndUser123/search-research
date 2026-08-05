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
  assert.match(await readFile(join(artifactDir, "stdout.log"), "utf8"), /result_payload/);
  assert.match(await readFile(join(artifactDir, "result.json"), "utf8"), /"status": "ok"/);
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
