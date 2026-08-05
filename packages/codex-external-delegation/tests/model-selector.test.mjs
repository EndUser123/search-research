import test from "node:test";
import assert from "node:assert/strict";
import { mkdir, mkdtemp, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { DEFAULT_QUOTA_MAX_AGE_MS, selectModel } from "../src/model-selector.mjs";

const fixtureCandidates = [
  {
    id: "opencode-go/deepseek-v4-flash",
    registry_slug: "go-deepseek-v4-flash",
    worker: "pi",
    provider: "opencode-go",
    model: "deepseek-v4-flash",
    quota_provider: "opencode-go",
    roles: { mechanical: 96 },
    capabilities: { tools: true, structured_output: true, reasoning: true, images: false },
    context_window: 131072,
    quota_pool: "opencode-go",
    quota_class: "shared_subscription",
    priority: 100,
  },
  {
    id: "nvidia-nim/deepseek-ai/deepseek-v4-flash",
    registry_slug: "nim-deepseek-ai-deepseek-v4-flash",
    worker: "pi",
    provider: "nvidia-nim",
    model: "deepseek-ai/deepseek-v4-flash",
    quota_provider: "nvidia",
    roles: { mechanical: 94 },
    capabilities: { tools: true, structured_output: true, reasoning: true, images: false },
    context_window: 131072,
    quota_pool: "nvidia-nim",
    quota_class: "unlimited_with_rate_limit",
    priority: 95,
  },
];

async function createQuotaFixture({ providerId, pct, timestamp }) {
  const dir = await mkdtemp(join(tmpdir(), "codex-selector-quota-"));
  const stateDir = join(dir, "quota-provider-state");
  const registryPath = join(dir, "fleet-models.json");
  const quotaPath = join(dir, "fleet-quota-cache.json");
  const modelsPath = join(dir, "models.json");
  await mkdir(stateDir);
  await writeFile(registryPath, JSON.stringify({
    models: {
      "go-deepseek-v4-flash": { provider: "opencode-go", transports: { pi_cli: { status: "unknown" } } },
      "nim-deepseek-ai-deepseek-v4-flash": { provider: "nim", transports: { pi_cli: { status: "unknown" } } },
    },
    lanes: {},
  }));
  await writeFile(quotaPath, JSON.stringify({}));
  await writeFile(modelsPath, JSON.stringify({ providers: {
    "opencode-go": { models: [{ id: "deepseek-v4-flash" }] },
    "nvidia-nim": { models: [{ id: "deepseek-ai/deepseek-v4-flash" }] },
  } }));
  if (providerId) {
    await writeFile(join(stateDir, `${providerId}-fixture.json`), JSON.stringify({
      providerId,
      timestamp,
      result: { attempted: true, entries: [{ name: "monthly", percentRemaining: pct }] },
    }));
  }
  return { registryPath, quotaPath, stateDir, modelsPath };
}

function withSelectorEnv(paths, callback) {
  const names = {
    CODEX_PI_FLEET_REGISTRY: paths.registryPath,
    CODEX_PI_QUOTA_CACHE: paths.quotaPath,
    CODEX_PI_QUOTA_STATE: paths.stateDir,
    CODEX_PI_MODELS: paths.modelsPath,
  };
  const previous = Object.fromEntries(Object.keys(names).map((name) => [name, process.env[name]]));
  Object.assign(process.env, names);
  try {
    return callback();
  } finally {
    for (const name of Object.keys(names)) {
      if (previous[name] === undefined) delete process.env[name];
      else process.env[name] = previous[name];
    }
  }
}

test("excludes OpenCode Go when its fresh provider state has an exhausted monthly window", async () => {
  const now = Date.now();
  const paths = await createQuotaFixture({ providerId: "opencode-go", pct: 0, timestamp: now });
  const result = withSelectorEnv(paths, () => selectModel({
    task_domain: "mechanical",
    now_ms: now,
    model_candidates: fixtureCandidates,
  }));
  assert.equal(result.status, "selected");
  assert.equal(result.provider, "nvidia-nim");
  assert.match(result.reasons.join(" "), /quota_status:static_unlimited_rate_limited/);
});

test("does not treat a stale shared quota snapshot as available", async () => {
  const now = Date.now();
  const paths = await createQuotaFixture({
    providerId: "opencode-go",
    pct: 100,
    timestamp: now - DEFAULT_QUOTA_MAX_AGE_MS - 1,
  });
  const result = withSelectorEnv(paths, () => selectModel({
    task_domain: "mechanical",
    now_ms: now,
    model_candidates: [fixtureCandidates[0]],
  }));
  assert.equal(result.status, "no_eligible_candidate");
  assert.match(result.candidates_considered[0].rejected.join(" "), /provider_quota_snapshot_unavailable/);
});

test("keeps NVIDIA eligible without a quota API snapshot", async () => {
  const now = Date.now();
  const paths = await createQuotaFixture({});
  const result = withSelectorEnv(paths, () => selectModel({
    task_domain: "mechanical",
    now_ms: now,
    model_candidates: [fixtureCandidates[1]],
  }));
  assert.equal(result.status, "selected");
  assert.equal(result.provider, "nvidia-nim");
  assert.match(result.reasons.join(" "), /quota_status:static_unlimited_rate_limited/);
});

test("selects the best available provider for mechanical work", () => {
  const result = selectModel({
    task_domain: "mechanical",
    provider_health: {
      "opencode-go": { available: true, quota_class: "shared_subscription", quota_available: true, reliability: 0.98, p90_latency_ms: 4000, evidence_count: 20 },
      "nvidia-nim": { available: true, quota_class: "unlimited_with_rate_limit", rate_limit_available: true, reliability: 0.98, p90_latency_ms: 2500, evidence_count: 20 },
    },
  }, { allowUntrustedHealth: true });
  assert.equal(result.status, "selected");
  assert.equal(result.provider, "nvidia-nim");
  assert.equal(result.model, "deepseek-ai/deepseek-v4-flash");
  assert.match(result.reasons.join(" "), /quota_class:unlimited_with_rate_limit/);
  assert.equal(result.confidence, "measured");
});

test("includes the Pi-verified Nemotron reasoning candidate", () => {
  const result = selectModel({
    task_domain: "reasoning",
    provider_health: {
      "nvidia-nim": { available: true, quota_available: true, quota_class: "unlimited_with_rate_limit", reliability: 0.99, p90_latency_ms: 2500, evidence_count: 20 },
    },
  }, { allowUntrustedHealth: true });
  assert.equal(result.status, "selected");
  assert.equal(result.provider, "nvidia-nim");
  assert.equal(result.model, "nvidia/nemotron-3-ultra-550b-a55b");
  assert.equal(result.confidence, "measured");
});

test("uses the dedicated MiniMax provider when coding is the best fit", () => {
  const result = selectModel({
    task_domain: "coding",
    provider_health: {
      minimax: { available: true, quota_available: true, quota_headroom: 0.9, reliability: 0.99, p90_latency_ms: 9000, evidence_count: 12 },
      "opencode-go": { available: true, quota_available: true, quota_headroom: 0.9, reliability: 0.99, p90_latency_ms: 3000, evidence_count: 12 },
    },
  }, { allowUntrustedHealth: true });
  assert.equal(result.provider, "minimax");
  assert.equal(result.model, "MiniMax-M3");
  assert.match(result.reasons.join(" "), /quota_pool:minimax-dedicated/);
});

test("uses Go when it is measurably faster despite NVIDIA capacity", () => {
  const result = selectModel({
    task_domain: "mechanical",
    provider_health: {
      "opencode-go": { available: true, quota_class: "shared_subscription", quota_available: true, reliability: 0.98, p90_latency_ms: 1800, evidence_count: 20 },
      "nvidia-nim": { available: true, quota_class: "unlimited_with_rate_limit", rate_limit_available: true, reliability: 0.98, p90_latency_ms: 2500, evidence_count: 20 },
    },
  }, { allowUntrustedHealth: true });
  assert.equal(result.provider, "opencode-go");
});

test("removes unavailable providers before ranking", () => {
  const result = selectModel({
    task_domain: "coding",
    provider_health: {
      minimax: { available: false },
      "opencode-go": { available: true, quota_available: true, reliability: 0.95, evidence_count: 8 },
    },
  }, { allowUntrustedHealth: true });
  assert.equal(result.provider, "opencode-go");
  assert.equal(result.alternatives.includes("minimax/MiniMax-M3"), false);
});

test("reports no eligible candidate when quota and capability gates fail", () => {
  const result = selectModel({
    task_domain: "reasoning",
    requires_images: true,
    provider_health: {
      zai: { quota_available: false },
      minimax: { quota_available: false },
    },
  }, { allowUntrustedHealth: true });
  assert.equal(result.status, "no_eligible_candidate");
  assert.equal(result.reason, "no_external_candidate_cleared_capability_quota_and_health_gates");
});

test("rejects a candidate when the requested context exceeds its limit", () => {
  const result = selectModel({ task_domain: "mechanical", context_tokens: 200000 }, { allowUntrustedHealth: true });
  assert.equal(result.status, "selected");
  assert.notEqual(result.provider, "opencode-go");
  assert.notEqual(result.provider, "nvidia-nim");
  assert.notEqual(result.provider, "opencode-zen");
});

test("ignores stale provider health instead of treating it as current truth", () => {
  const result = selectModel({
    task_domain: "mechanical",
    now_ms: Date.parse("2026-08-05T12:00:00Z"),
    provider_health: {
      "opencode-go": {
        observed_at: "2026-08-05T10:00:00Z",
        available: false,
        quota_available: false,
        reliability: 0,
        p90_latency_ms: 999999,
        evidence_count: 100,
      },
    },
  }, { allowUntrustedHealth: true });
  assert.equal(result.status, "selected");
  assert.match(result.reasons.join(" "), /health_snapshot_stale_ignored/);
  assert.equal(result.confidence, "unverified");
});
