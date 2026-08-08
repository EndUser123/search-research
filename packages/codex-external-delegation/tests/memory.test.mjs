import test from "node:test";
import assert from "node:assert/strict";
import { EventEmitter } from "node:events";
import { mkdir, readdir, writeFile } from "node:fs/promises";
import { mkdtemp } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { buildHistoryEntry, readHistory, summarizeHistory, writeHistoryEntry } from "../src/memory.mjs";
import { runPacket } from "../src/runner.mjs";

const packet = {
  schema_version: "2",
  task_id: "memory-task",
  invocation_id: "memory-invocation",
  run_id: "memory-run",
  worker: "opencode",
  requested_provider: "opencode",
  model: "test-model",
  role: "mechanical",
  selected_lane: "opencode",
  task_type: "mechanical_edit",
  task_class: "read_only",
  objective: "Return a value.",
  cwd: "P:/repo",
  mode: "read_only",
  output_schema: { required: ["value"] },
  verification: { commands: ["node --version"] },
};

function fakeSpawn({ stdout = "", stderr = "", exitCode = 0, delay = 0 } = {}) {
  return () => {
    const child = new EventEmitter();
    child.stdin = new EventEmitter();
    child.stdout = new EventEmitter();
    child.stderr = new EventEmitter();
    child.stdin.end = () => {};
    setTimeout(() => {
      if (stdout) child.stdout.emit("data", Buffer.from(stdout));
      if (stderr) child.stderr.emit("data", Buffer.from(stderr));
      child.emit("close", exitCode, null);
    }, delay);
    return child;
  };
}

async function root() { return mkdtemp(join(tmpdir(), "codex-memory-test-")); }

test("successful live runner result writes one history entry with real identity", async () => {
  const dir = await root();
  const historyDir = join(dir, "history");
  const result = await runPacket(packet, {
    artifactDir: join(dir, "artifacts", "memory-task"),
    historyDir,
    spawnImpl: fakeSpawn({ stdout: '<external-delegation-result>{"status":"ok","result_payload":{"value":42,"verification":{"status":"pass"}}}</external-delegation-result>' }),
  });
  assert.equal(result.status, "ok");
  assert.equal(result.telemetry.status, "recorded");
  const history = await readHistory(historyDir);
  assert.equal(history.entries.length, 1);
  assert.equal(history.entries[0].task_type, "mechanical_edit");
  assert.equal(history.entries[0].model, "test-model");
  assert.equal(history.entries[0].timeout, false);
  assert.equal(history.entries[0].verification.status, "pass");
  assert.ok(history.entries[0].duration_ms >= 0);
});

test("history failure is surfaced without changing a successful worker result", async () => {
  const dir = await root();
  const result = await runPacket(packet, {
    artifactDir: join(dir, "artifacts"),
    memoryWriter: async () => { throw new Error("history volume unavailable"); },
    spawnImpl: fakeSpawn({ stdout: '<external-delegation-result>{"status":"ok","result_payload":{"value":42}}</external-delegation-result>' }),
  });
  assert.equal(result.status, "ok");
  assert.equal(result.telemetry.status, "failed");
  assert.equal(result.telemetry.failure_class, "telemetry_error");
});

test("failed worker and timeout entries preserve failure class without retry fabrication", async () => {
  const dir = await root();
  const historyDir = join(dir, "history");
  const failed = await runPacket(packet, {
    artifactDir: join(dir, "failed"), historyDir,
    spawnImpl: fakeSpawn({ stderr: "provider unavailable", exitCode: 1 }),
  });
  assert.equal(failed.status, "failed");
  assert.equal(failed.telemetry.status, "recorded");
  const timeout = buildHistoryEntry(packet, { ...failed, task_id: "timeout-task", status: "failed", failure_class: "timeout", timed_out: true }, { startedAt: Date.now() - 10, endedAt: Date.now(), artifactDir: join(dir, "timeout") });
  await writeHistoryEntry(timeout, historyDir);
  const entries = (await readHistory(historyDir)).entries;
  assert.equal(entries.length, 2);
  assert.equal(entries.find((entry) => entry.task_id === "timeout-task").timeout, true);
  assert.equal(Object.hasOwn(entries[0], "retry_count"), false);
});

test("malformed telemetry is ignored and never invents token or cost values", async () => {
  const dir = await root();
  const entry = buildHistoryEntry(packet, { task_id: packet.task_id, status: "ok", failure_class: "none", attempt: 1, timed_out: false, result_payload: { value: 1, usage: { total_tokens: "not-a-number", cost_usd: "unknown" } } }, { startedAt: 100, endedAt: 200, artifactDir: dir });
  await writeHistoryEntry(entry, join(dir, "history"));
  const stored = (await readHistory(join(dir, "history"))).entries[0];
  assert.equal(Object.hasOwn(stored, "reported_metrics"), false);
  assert.equal(Object.hasOwn(stored, "tokens"), false);
  assert.equal(Object.hasOwn(stored, "cost"), false);
});

test("history duration remains numeric when runner timestamps are ISO strings", () => {
  const entry = buildHistoryEntry(
    packet,
    { task_id: packet.task_id, status: "ok", failure_class: "none", result_payload: { value: 1 } },
    {
      startedAt: "2026-08-07T12:00:00.000Z",
      endedAt: "2026-08-07T12:00:01.250Z",
    },
  );
  assert.equal(entry.duration_ms, 1250);
  assert.equal(entry.started_at, "2026-08-07T12:00:00.000Z");
  assert.equal(entry.ended_at, "2026-08-07T12:00:01.250Z");
});

test("concurrent duplicate task IDs create distinct immutable entries", async () => {
  const dir = await root();
  const historyDir = join(dir, "history");
  const entries = [
    buildHistoryEntry(packet, { task_id: packet.task_id, run_id: "same-run", status: "ok", failure_class: "none", attempt: 1, timed_out: false, result_payload: { value: 1 } }, { startedAt: 100, endedAt: 200, artifactDir: dir }),
    buildHistoryEntry(packet, { task_id: packet.task_id, run_id: "same-run", status: "ok", failure_class: "none", attempt: 1, timed_out: false, result_payload: { value: 2 } }, { startedAt: 101, endedAt: 201, artifactDir: dir }),
  ];
  assert.notEqual(entries[0].entry_id, entries[1].entry_id);
  await Promise.all(entries.map((entry) => writeHistoryEntry(entry, historyDir)));
  const history = await readHistory(historyDir);
  assert.equal(history.entries.length, 2);
  assert.deepEqual(history.entries.map((entry) => entry.task_id), [packet.task_id, packet.task_id]);
  assert.equal((await readdir(join(historyDir, packet.task_id))).filter((name) => name.endsWith(".json")).length, 2);
});

test("reader recovers from partial temp files and reports malformed JSON", async () => {
  const dir = await root();
  const historyDir = join(dir, "history");
  const entry = buildHistoryEntry(packet, { status: "ok", failure_class: "none", attempt: 1, timed_out: false, result_payload: { value: 1 } }, { startedAt: 100, endedAt: 200, artifactDir: dir });
  await writeHistoryEntry(entry, historyDir);
  await mkdir(join(historyDir, "partial"), { recursive: true });
  await writeFile(join(historyDir, "partial", ".unfinished.tmp"), "{\"schema_version\":", "utf8");
  await writeFile(join(historyDir, "partial", "malformed.json"), "{not-json", "utf8");
  const result = await readHistory(historyDir);
  assert.equal(result.entries.length, 1);
  assert.equal(result.skipped.length, 1);
  assert.match(result.skipped[0].path, /malformed\.json/);
});

test("report summarizes real entries and leaves verification unknown when absent", async () => {
  const entries = [
    { task_type: "mechanical_edit", model: "test-model", status: "ok", timeout: false, duration_ms: 10 },
    { task_type: "mechanical_edit", model: "test-model", status: "failed", timeout: true, failure_class: "timeout", duration_ms: 30 },
  ];
  const report = summarizeHistory(entries);
  assert.deepEqual(report, [{ task_type: "mechanical_edit", model: "test-model", entries: 2, success_rate: 0.5, timeout_rate: 0.5, median_duration_ms: 20, verification_pass_rate: null }]);
});
