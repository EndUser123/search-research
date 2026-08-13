import test from "node:test";
import assert from "node:assert/strict";
import { mkdtemp, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { spawnSync } from "node:child_process";
import { fileURLToPath } from "node:url";

const packageRoot = join(fileURLToPath(new URL(".", import.meta.url)), "..");
const cli = join(packageRoot, "bin", "external-delegation.mjs");

async function manifestFile(manifest) {
  const dir = await mkdtemp(join(tmpdir(), "codex-batch-cli-"));
  const path = join(dir, "manifest.json");
  await writeFile(path, JSON.stringify(manifest), "utf8");
  return { dir, path };
}

function explicitTask(taskId) {
  return {
    task_id: taskId,
    repetitions: 1,
    candidate_mode: "explicit",
    input: {
      requested_worker: "pi",
      requested_provider: "minimax",
      model: "MiniMax-M3",
      objective: "Return observations.",
      cwd: packageRoot,
      mode: "read_only",
      allowed_paths: ["src/"],
      verification_commands: ["node --version"],
      output_schema: { required: ["observations"] },
    },
  };
}

function manifest(artifactRoot) {
  return {
    schema_version: "batch.v1",
    batch_id: "cli-batch",
    artifact_root: artifactRoot,
    concurrency: { max_in_flight: 1, by_provider: { minimax: 1 } },
    tasks: [explicitTask("one")],
  };
}

test("batch route CLI emits structured output and does not spawn a worker", async () => {
  const artifactRoot = await mkdtemp(join(tmpdir(), "codex-batch-cli-artifacts-"));
  const file = await manifestFile(manifest(artifactRoot));
  const result = spawnSync(process.execPath, [cli, "batch", "route", "--manifest", file.path], { encoding: "utf8" });
  assert.equal(result.status, 0, result.stderr);
  const output = JSON.parse(result.stdout);
  assert.equal(output.status, "ok");
  assert.equal(output.counts.total, 1);
  assert.equal(output.entries[0].status, "ok");
});

test("batch run dry-run uses route semantics and returns before worker execution", async () => {
  const artifactRoot = await mkdtemp(join(tmpdir(), "codex-batch-cli-dry-artifacts-"));
  const file = await manifestFile(manifest(artifactRoot));
  const result = spawnSync(process.execPath, [cli, "batch", "run", "--manifest", file.path, "--dry-run"], { encoding: "utf8" });
  assert.equal(result.status, 0, result.stderr);
  const output = JSON.parse(result.stdout);
  assert.equal(output.status, "dry_run");
  assert.equal(output.dry_run, true);
  assert.equal(output.entries[0].status, "ok");
});

test("batch run dry-run reports expected preflight blocks without a failure exit", async () => {
  const artifactRoot = await mkdtemp(join(tmpdir(), "codex-batch-cli-blocked-dry-artifacts-"));
  const blockedManifest = manifest(artifactRoot);
  blockedManifest.tasks[0].input.benchmark_preflight = {
    status: "blocked",
    failure_class: "quota_or_rate_limit",
    reasons: ["test-only preflight block"],
  };
  const file = await manifestFile(blockedManifest);
  const result = spawnSync(process.execPath, [cli, "batch", "run", "--manifest", file.path, "--dry-run"], { encoding: "utf8" });
  assert.equal(result.status, 0, result.stderr);
  const output = JSON.parse(result.stdout);
  assert.equal(output.status, "blocked");
  assert.equal(output.dry_run, true);
  assert.equal(output.counts.blocked, 1);
  assert.equal(output.entries[0].failure_class, "quota_or_rate_limit");
});

test("benchmark CLI blocks before any provider worker without live approval", async () => {
  const artifactRoot = await mkdtemp(join(tmpdir(), "codex-batch-cli-approval-artifacts-"));
  const benchmarkManifest = manifest(artifactRoot);
  benchmarkManifest.batch_id = "benchmark-cli-approval";
  benchmarkManifest.tasks[0].input.benchmark_manifest_id = "capability-difficulty-test";
  benchmarkManifest.tasks[0].input.benchmark_manifest_sha256 = "manifest-hash-test";
  const file = await manifestFile(benchmarkManifest);
  const result = spawnSync(process.execPath, [cli, "batch", "run", "--manifest", file.path], { encoding: "utf8" });
  assert.equal(result.status, 20, result.stderr);
  const output = JSON.parse(result.stdout);
  assert.equal(output.failure_class, "benchmark_live_approval_required");
  assert.equal(output.benchmark_gate.status, "blocked");
  assert.equal(output.counts.blocked, 1);
});

test("batch CLI rejects an invalid manifest with setup exit code", async () => {
  const file = await manifestFile({ schema_version: "batch.v1" });
  const result = spawnSync(process.execPath, [cli, "batch", "route", "--manifest", file.path], { encoding: "utf8" });
  assert.equal(result.status, 30);
  assert.equal(JSON.parse(result.stdout).failure_class, "invalid_manifest");
});
