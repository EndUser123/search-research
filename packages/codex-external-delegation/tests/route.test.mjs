import test from "node:test";
import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import { mkdtemp, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { fileURLToPath } from "node:url";

const packageRoot = join(fileURLToPath(new URL(".", import.meta.url)), "..");
const cli = join(packageRoot, "bin", "external-delegation.mjs");
function fixtureEnv({ registry, quota, models }) {
  return {
    ...process.env,
    CODEX_PI_FLEET_REGISTRY: registry,
    CODEX_PI_QUOTA_CACHE: quota || "",
    CODEX_PI_MODELS: models,
  };
}

test("route emits a packet for bounded work and no packet for agy advisory review", async () => {
  const dir = await mkdtemp(join(tmpdir(), "codex-route-test-"));
  const boundedPath = join(dir, "bounded.json");
  const agyPath = join(dir, "agy.json");
  await writeFile(boundedPath, JSON.stringify({
    objective: "List callers of module X.",
    model: "opencode-go/deepseek-v4-flash",
    cwd: "P:/repo",
    allowed_paths: ["src/"],
    verification_commands: ["rg -n module src"],
  }));
  await writeFile(agyPath, JSON.stringify({ requested_role: "ADVISORY_REVIEW" }));

  const bounded = spawnSync(process.execPath, [cli, "route", "--input", boundedPath], { encoding: "utf8" });
  const boundedOutput = JSON.parse(bounded.stdout);
  assert.equal(bounded.status, 0);
  assert.equal(boundedOutput.classification.lane, "pi");
  assert.equal(boundedOutput.packet.failure_policy, "halt_no_automatic_fallback");
  assert.equal(boundedOutput.packet.worker, "pi");
  assert.equal(typeof boundedOutput.packet.packet_hash, "string");

  const agy = spawnSync(process.execPath, [cli, "route", "--input", agyPath], { encoding: "utf8" });
  const agyOutput = JSON.parse(agy.stdout);
  assert.equal(agy.status, 0);
  assert.equal(agyOutput.classification.lane, "agy");
  assert.equal(agyOutput.classification.eligible, false);
  assert.equal(agyOutput.lane.status, "advisory_manual_identity_unproven");
  assert.equal(agyOutput.packet, undefined);
});

test("route accepts bounded input from stdin", () => {
  const bounded = JSON.stringify({
    objective: "List callers of module X.",
    model: "minimax/MiniMax-M3",
    cwd: "P:/repo",
    allowed_paths: ["src/"],
    verification_commands: ["rg -n module src"],
  });
  const result = spawnSync(process.execPath, [cli, "route", "--input", "-"], {
    input: bounded,
    encoding: "utf8",
  });
  const output = JSON.parse(result.stdout);
  assert.equal(result.status, 0);
  assert.equal(output.packet.worker, "pi");
  assert.equal(output.packet.model, "minimax/MiniMax-M3");
});

test("route blocks when the authoritative registry says no candidate is eligible", async () => {
  const dir = await mkdtemp(join(tmpdir(), "codex-route-health-"));
  const registryPath = join(dir, "fleet-models.json");
  const quotaPath = join(dir, "quota.json");
  const modelsPath = join(dir, "models.json");
  await writeFile(registryPath, JSON.stringify({
    schema_version: 5,
    threshold_policy: {},
    candidates: [{
      id: "codex-zai-glm-5-2",
      model: "glm-5.2",
      provider: "zai",
      transport: "pi",
      orchestrator: "codex",
      lanes: ["reasoning"],
      capabilities: { context_window: 131072, tool_calling: true, structured_output: true, multimodal: false, reasoning: true },
      quota: { type: "flat_rate", monthly_estimated: 0, shared_with: [] },
      lifecycle: "active",
      policy: "excluded",
      dispatch_path: "pi",
      dispatch_paths: ["pi", "http", "opencode", "spawn"],
    }],
    serde_broken: [],
    tool_grounded_spawn_broken: [],
  }));
  await writeFile(quotaPath, JSON.stringify({ zai: { pct: 0, updated: Date.now() / 1000, source: "test" } }));
  await writeFile(modelsPath, JSON.stringify({ providers: { zai: { models: [{ id: "glm-5.2" }] } } }));
  const result = spawnSync(process.execPath, [cli, "route", "--input", "-"], {
    input: JSON.stringify({
      objective: "Read the repository.",
      cwd: "P:/repo",
      allowed_paths: ["src/"],
      verification_commands: ["rg -n . src"],
      task_domain: "reasoning",
    }),
    env: fixtureEnv({ registry: registryPath, quota: quotaPath, models: modelsPath }),
    encoding: "utf8",
  });
  const output = JSON.parse(result.stdout);
  assert.equal(result.status, 20);
  assert.equal(output.status, "blocked");
  assert.equal(output.failure_class, "no_eligible_external_candidate");
});

test("route permits a configured candidate with incomplete transport history as provisional", async () => {
  const dir = await mkdtemp(join(tmpdir(), "codex-route-provisional-"));
  const registryPath = join(dir, "fleet-models.json");
  const modelsPath = join(dir, "models.json");
  await writeFile(registryPath, JSON.stringify({
    schema_version: 5,
    threshold_policy: {},
    candidates: [{
      id: "codex-nvidia-nim-deepseek-ai-deepseek-v4-flash",
      model: "deepseek-ai/deepseek-v4-flash",
      provider: "nim",
      transport: "pi",
      orchestrator: "codex",
      lanes: ["mechanical"],
      capabilities: { context_window: 131072, tool_calling: true, structured_output: true, multimodal: false, reasoning: false },
      quota: { type: "flat_rate", monthly_estimated: 0, shared_with: [] },
      lifecycle: "active",
      policy: "use_freely",
      dispatch_path: "pi",
      dispatch_paths: ["spawn", "pi"],
    }],
    serde_broken: [],
    tool_grounded_spawn_broken: [],
  }));
  await writeFile(modelsPath, JSON.stringify({ providers: { "nvidia-nim": { models: [{ id: "deepseek-ai/deepseek-v4-flash" }] } } }));
  const result = spawnSync(process.execPath, [cli, "route", "--input", "-"], {
    input: JSON.stringify({
      objective: "Read the repository.",
      cwd: "P:/repo",
      allowed_paths: ["src/"],
      verification_commands: ["rg -n . src"],
      task_domain: "mechanical",
    }),
    env: fixtureEnv({ registry: registryPath, models: modelsPath }),
    encoding: "utf8",
  });
  const output = JSON.parse(result.stdout);
  assert.equal(result.status, 0);
  assert.equal(output.status, "ok");
  assert.equal(output.packet.model_selection.confidence, "provisional");
});
