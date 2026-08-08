import test from "node:test";
import assert from "node:assert/strict";
import { mkdir, mkdtemp, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { classifyTask } from "../src/policy.mjs";
import { compilePacket, hashPacket } from "../src/packet.mjs";

const selectorFixtureCandidates = [
  {
    id: "opencode-go/deepseek-v4-flash",
    registry_slug: "codex-opencode-go-deepseek-v4-flash",
    worker: "pi",
    provider: "opencode-go",
    model: "deepseek-v4-flash",
    quota_provider: "opencode-go",
    roles: { mechanical: 96 },
    capabilities: { tools: true, structured_output: true, reasoning: true, images: false },
    context_window: 131072,
    max_output_tokens: 32768,
    quota_pool: "opencode-go",
    quota_class: "shared_subscription",
    priority: 100,
  },
  {
    id: "nvidia-nim/deepseek-ai/deepseek-v4-flash",
    registry_slug: "codex-nvidia-nim-deepseek-ai-deepseek-v4-flash",
    worker: "pi",
    provider: "nvidia-nim",
    model: "deepseek-ai/deepseek-v4-flash",
    quota_provider: "nvidia",
    roles: { mechanical: 94 },
    capabilities: { tools: true, structured_output: true, reasoning: true, images: false },
    context_window: 131072,
    max_output_tokens: 32768,
    quota_pool: "nvidia-nim",
    quota_class: "unlimited_with_rate_limit",
    priority: 95,
  },
];

async function createSelectorFixture(now) {
  const root = await mkdtemp(join(tmpdir(), "codex-policy-selector-"));
  const stateDir = join(root, "quota-provider-state");
  const registryPath = join(root, "fleet-models.json");
  const quotaPath = join(root, "fleet-quota-cache.json");
  const modelsPath = join(root, "models.json");
  await mkdir(stateDir);
  await writeFile(registryPath, JSON.stringify({
    schema_version: 5,
    threshold_policy: {},
    candidates: [
      {
        id: "codex-opencode-go-deepseek-v4-flash",
        model: "deepseek-v4-flash",
        provider: "opencode-go",
        transport: "pi",
        orchestrator: "codex",
        lanes: ["mechanical"],
        capabilities: { context_window: 131072, tool_calling: true, structured_output: true, multimodal: false, reasoning: false },
        quota: { type: "flat_rate", monthly_estimated: 0, shared_with: [] },
        lifecycle: "active",
        policy: "use_freely",
        dispatch_path: "pi",
        dispatch_paths: ["spawn", "pi"],
      },
      {
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
      },
    ],
    serde_broken: [],
    tool_grounded_spawn_broken: [],
  }));
  await writeFile(quotaPath, JSON.stringify({}));
  await writeFile(modelsPath, JSON.stringify({ providers: {
    "opencode-go": { models: [{ id: "deepseek-v4-flash" }] },
    "nvidia-nim": { models: [{ id: "deepseek-ai/deepseek-v4-flash" }] },
  } }));
  await writeFile(join(stateDir, "opencode-go-fixture.json"), JSON.stringify({
    providerId: "opencode-go",
    timestamp: now,
    result: { attempted: true, entries: [{ name: "monthly", percentRemaining: 0 }] },
  }));
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

const bounded = {
  objective: "List callers of module X.",
  model: "minimax/MiniMax-M3",
  cwd: "P:/repo",
  allowed_paths: ["src/", "tests/"],
  verification_commands: ["rg -n module src tests"],
};

test("classifies a bounded mechanical task for automatic Pi execution", () => {
  const result = classifyTask(bounded);
  assert.deepEqual(result, {
    role: "BOUNDED_EXECUTION",
    lane: "pi",
    eligible: true,
    selection_mode: "automatic",
    reason: "bounded_low_ambiguity_task_with_deterministic_verification",
  });
});

test("keeps ambiguous and judgment-heavy tasks with Codex", () => {
  assert.equal(classifyTask({ ...bounded, ambiguity: "high" }).lane, "codex_native");
  assert.equal(classifyTask({ ...bounded, needs_architecture: true }).lane, "codex_native");
  assert.equal(classifyTask({ ...bounded, verification_commands: [] }).reason, "independent_verification_missing");
});

test("represents agy, MMX, and explicit specialist work as non-automatic roles", () => {
  assert.equal(classifyTask({ requested_role: "ADVISORY_REVIEW" }).lane, "agy");
  assert.equal(classifyTask({ requested_role: "SEARCH_DISCOVERY" }).lane, "mmx");
  assert.equal(classifyTask({ requested_role: "SPECIALIST_EXPLICIT" }).lane, "pi");
  assert.equal(classifyTask({ requested_role: "ADVISORY_REVIEW" }).eligible, false);
});

test("compiles a complete versioned packet and hashes authoritative inputs", () => {
  const { packet } = compilePacket({ ...bounded, task_id: "packet-001", invocation_id: "invoke-001" });
  assert.equal(packet.schema_version, "2");
  assert.equal(packet.role, "BOUNDED_EXECUTION");
  assert.equal(packet.selected_lane, "pi");
  assert.equal(packet.mode, "read_only");
  assert.equal(packet.requested_agent, null);
  assert.equal(packet.agent, null);
  assert.equal(packet.failure_policy, "halt_no_automatic_fallback");
  assert.equal(packet.packet_hash, hashPacket(packet));
  const changed = { ...packet, objective: "List exports of module X." };
  assert.notEqual(packet.packet_hash, hashPacket(changed));
});

test("infers write mode from declared write intent while honoring explicit mode", () => {
  const { packet } = compilePacket({
    ...bounded,
    task_id: "write-intent-001",
    write_scope: ["src/example.mjs"],
    worktree_request: { worktreeRoot: "P:/tmp/worktrees", intendedFiles: ["src/example.mjs"] },
  });
  assert.equal(packet.mode, "write");
  assert.equal(packet.containment, "isolated_worktree_required");

  const explicitlyReadOnly = compilePacket({
    ...bounded,
    task_id: "write-intent-002",
    mode: "read_only",
    write_scope: ["src/example.mjs"],
  });
  assert.equal(explicitlyReadOnly.packet.mode, "read_only");
  assert.equal(explicitlyReadOnly.packet.containment, "read_only");
});

test("uses authoritative provider state when the caller leaves model selection open", async () => {
  const now = Date.now();
  const paths = await createSelectorFixture(now);
  const { packet } = withSelectorEnv(paths, () => compilePacket({
    objective: "Read the package manifest and report its name.",
    cwd: "P:/repo",
    allowed_paths: ["package.json"],
    verification_commands: ["node -e \"JSON.parse(require('fs').readFileSync('package.json'))\""],
    task_domain: "mechanical",
    now_ms: now,
    model_candidates: selectorFixtureCandidates,
    provider_health: {
      "opencode-go": { available: true, quota_available: true, reliability: 0.99, p90_latency_ms: 4000, evidence_count: 8 },
    },
  }));
  assert.equal(packet.worker, "pi");
  assert.equal(packet.requested_provider, "nvidia-nim");
  assert.equal(packet.model, "deepseek-ai/deepseek-v4-flash");
  assert.equal(packet.model_selection.status, "selected");
  assert.equal(packet.model_selection.health_source, "fleet_registry_and_quota_cache");
  assert.match(packet.model_selection.reasons.join(" "), /quota_status:static_unlimited_rate_limited/);
});

test("preserves explicit OpenCode identity when a caller selects that lane", () => {
  const { packet } = compilePacket({
    ...bounded,
    task_id: "packet-opencode-001",
    requested_worker: "opencode",
    requested_provider: "opencode",
    classification: {
      role: "BOUNDED_EXECUTION",
      lane: "opencode",
      eligible: false,
      selection_mode: "explicit",
      reason: "explicit_alternative",
    },
  });
  assert.equal(packet.selected_lane, "opencode");
  assert.equal(packet.worker, "opencode");
  assert.equal(packet.requested_agent, "external-readonly-primary");
});
