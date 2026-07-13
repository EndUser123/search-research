import test from "node:test";
import assert from "node:assert/strict";
import { EventEmitter } from "node:events";
import { PassThrough } from "node:stream";
import { mkdtemp, readFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { buildCommand, runPacket } from "../src/runner.mjs";

const basePacket = {
  schema_version: "1",
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
  const pi = buildCommand({ ...basePacket, worker: "pi", model: "minimax/MiniMax-M3" }, "do the task");
  assert.equal(pi.command, "pi.cmd");
  assert.ok(pi.args.includes("--tools"));
  assert.ok(pi.args.includes("read,grep,find,ls"));

  const opencode = buildCommand({ ...basePacket, worker: "opencode", model: "opencode-go/deepseek-v4-flash" }, "do the task");
  assert.equal(opencode.command, "opencode.cmd");
  assert.ok(opencode.args.includes("--format"));
  assert.ok(opencode.args.includes("json"));
  assert.ok(opencode.args.includes("external-readonly"));
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

test("classifies malformed successful output as protocol failure", async () => {
  const artifactDir = await mkdtemp(join(tmpdir(), "codex-delegation-test-"));
  const result = await runPacket(basePacket, {
    artifactDir,
    spawnImpl: fakeSpawn({ stdout: "worker prose without marker" }),
  });
  assert.equal(result.status, "failed");
  assert.equal(result.failure_class, "protocol_error");
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
