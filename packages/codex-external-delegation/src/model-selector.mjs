import { readdirSync, readFileSync } from "node:fs";
import { homedir } from "node:os";
import { join } from "node:path";

const DEFAULT_FLEET_REGISTRY = join(homedir(), ".grok", "skills", "model-quota", "scripts", "fleet-models.json");
const DEFAULT_QUOTA_CACHE = join(homedir(), ".cache", "opencode", "fleet-quota-cache.json");
const DEFAULT_QUOTA_STATE = join(homedir(), ".cache", "opencode", "quota-provider-state");
const DEFAULT_PI_MODELS = join(homedir(), ".pi", "agent", "models.json");
const DEFAULT_CANDIDATES = [
  {
    id: "opencode-go/deepseek-v4-flash",
    registry_slug: "go-deepseek-v4-flash",
    worker: "pi",
    provider: "opencode-go",
    model: "deepseek-v4-flash",
    quota_provider: "opencode-go",
    roles: { mechanical: 96, extraction: 96, verification: 92, coding: 88, structured_output: 90 },
    capabilities: { tools: true, structured_output: true, reasoning: true, images: false },
    context_window: 131072,
    max_output_tokens: 32768,
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
    roles: { mechanical: 94, extraction: 94, verification: 90, coding: 86, structured_output: 86 },
    capabilities: { tools: true, structured_output: true, reasoning: true, images: false },
    context_window: 131072,
    max_output_tokens: 32768,
    quota_pool: "nvidia-nim",
    quota_class: "unlimited_with_rate_limit",
    priority: 95,
  },
  {
    id: "nvidia-nim/nvidia/nemotron-3-ultra-550b-a55b",
    registry_slug: "nvidia-nemotron-3-ultra",
    worker: "pi",
    provider: "nvidia-nim",
    model: "nvidia/nemotron-3-ultra-550b-a55b",
    quota_provider: "nvidia",
    roles: { reasoning: 98 },
    capabilities: { tools: true, structured_output: true, reasoning: true, images: false },
    context_window: 131072,
    max_output_tokens: 32768,
    quota_pool: "nvidia-nim",
    quota_class: "unlimited_with_rate_limit",
    priority: 98,
  },
  {
    id: "minimax/MiniMax-M3",
    registry_slug: "minimax-m3",
    worker: "pi",
    provider: "minimax",
    model: "MiniMax-M3",
    quota_provider: "minimax",
    roles: { mechanical: 76, extraction: 82, verification: 84, coding: 98, structured_output: 100, multimodal: 96 },
    capabilities: { tools: true, structured_output: true, reasoning: true, images: true },
    context_window: 1048576,
    max_output_tokens: 512000,
    quota_pool: "minimax-dedicated",
    quota_class: "dedicated_regenerating",
    priority: 90,
  },
  {
    id: "zai/glm-5.2",
    registry_slug: "glm-5-2",
    worker: "pi",
    provider: "zai",
    model: "glm-5.2",
    quota_provider: "zai",
    roles: { mechanical: 70, extraction: 72, verification: 90, coding: 86, structured_output: 86, reasoning: 100 },
    capabilities: { tools: true, structured_output: true, reasoning: true, images: false },
    context_window: 1000000,
    max_output_tokens: 32768,
    quota_pool: "zai-dedicated",
    quota_class: "dedicated_regenerating",
    priority: 90,
  },
  {
    id: "opencode-zen/deepseek-v4-flash-free",
    registry_slug: "zen-deepseek-v4-flash-free",
    worker: "pi",
    provider: "opencode-zen",
    model: "deepseek-v4-flash-free",
    quota_provider: "zen",
    roles: { mechanical: 88, extraction: 88, verification: 84, coding: 82, structured_output: 82 },
    capabilities: { tools: true, structured_output: true, reasoning: true, images: false },
    context_window: 131072,
    max_output_tokens: 32768,
    quota_pool: "opencode-zen-shared",
    quota_class: "rate_limited_free",
    priority: 80,
  },
];

const DEFAULT_HEALTH_MAX_AGE_MS = 15 * 60 * 1000;
export const DEFAULT_QUOTA_MAX_AGE_MS = 30 * 60 * 1000;
const QUOTA_STATE_PROVIDER_IDS = Object.freeze({
  minimax: "minimax-coding-plan",
  "opencode-go": "opencode-go",
  zai: "zai",
});
const BROKEN_TRANSPORT_STATUSES = new Set([
  "serde_broken",
  "context_overrun",
  "spawn_broken",
  "unsupported",
  "disabled",
  "blocked",
]);

export const MODEL_CANDIDATES = Object.freeze(DEFAULT_CANDIDATES.map((candidate) => Object.freeze({
  ...candidate,
  roles: Object.freeze({ ...candidate.roles }),
  capabilities: Object.freeze({ ...candidate.capabilities }),
})));

function taskRole(input = {}) {
  if (input.task_domain) return input.task_domain;
  if (input.requires_images) return "multimodal";
  if (input.requires_reasoning || input.needs_planning) return "reasoning";
  if (input.requires_structured_output || input.output_schema) return "structured_output";
  if (input.task_type === "coding" || input.write_scope || input.mode === "write") return "coding";
  if (input.task_type === "verification") return "verification";
  if (input.task_type === "extraction") return "extraction";
  return "mechanical";
}

function readJson(path) {
  try {
    return JSON.parse(readFileSync(path, "utf8"));
  } catch {
    return null;
  }
}

function fleetPaths(input, { allowTestPaths = false } = {}) {
  return {
    registry: (allowTestPaths && input.fleet_registry_path) || process.env.CODEX_PI_FLEET_REGISTRY || DEFAULT_FLEET_REGISTRY,
    quota: (allowTestPaths && input.quota_cache_path) || process.env.CODEX_PI_QUOTA_CACHE || DEFAULT_QUOTA_CACHE,
    quotaState: (allowTestPaths && input.quota_state_path) || process.env.CODEX_PI_QUOTA_STATE || DEFAULT_QUOTA_STATE,
    piModels: (allowTestPaths && input.pi_models_path) || process.env.CODEX_PI_MODELS || DEFAULT_PI_MODELS,
  };
}

function asPercent(value) {
  const number = Number(value);
  return Number.isFinite(number) && number >= 0 && number <= 100 ? number : null;
}

function asEpochMs(value) {
  const number = Number(value);
  if (!Number.isFinite(number) || number <= 0) return null;
  return number > 10_000_000_000 ? number : number * 1000;
}

function cacheQuotaSnapshot(quotaCache, provider) {
  const raw = quotaCache?.[provider];
  if (!raw || typeof raw !== "object") return null;
  const pct = asPercent(raw.pct);
  if (pct === null) return null;
  return {
    pct,
    updated_ms: asEpochMs(raw.updated),
    source: raw.source || "fleet_quota_cache",
    reset_ts: raw.reset_ts || null,
  };
}

function providerStateSnapshot(stateDir, provider) {
  const providerId = QUOTA_STATE_PROVIDER_IDS[provider];
  if (!providerId) return null;
  let names;
  try {
    names = readdirSync(stateDir).filter((name) => name.startsWith(`${providerId}-`) && name.endsWith(".json"));
  } catch {
    return null;
  }

  let newest = null;
  for (const name of names) {
    const state = readJson(join(stateDir, name));
    const entries = state?.providerId === providerId && state.result?.attempted !== false && Array.isArray(state.result?.entries)
      ? state.result.entries
      : [];
    const windows = entries
      .map((entry) => ({
        name: entry.name || null,
        window: entry.window || entry.label || null,
        pct: asPercent(entry.percentRemaining ?? entry.pct),
        reset_ts: entry.resetTimeIso ? Date.parse(entry.resetTimeIso) / 1000 : null,
      }))
      .filter((entry) => entry.pct !== null);
    if (!windows.length) continue;
    const snapshot = {
      pct: Math.min(...windows.map((entry) => entry.pct)),
      updated_ms: asEpochMs(state.timestamp),
      source: "opencode_quota_provider_state",
      reset_ts: windows.map((entry) => entry.reset_ts).filter(Number.isFinite).sort((a, b) => a - b)[0] || null,
      windows,
    };
    if (!newest || (snapshot.updated_ms || 0) > (newest.updated_ms || 0)) newest = snapshot;
  }
  return newest;
}

function quotaSnapshot(quotaCache, stateDir, provider) {
  return [cacheQuotaSnapshot(quotaCache, provider), providerStateSnapshot(stateDir, provider)]
    .filter(Boolean)
    .sort((left, right) => (right.updated_ms || 0) - (left.updated_ms || 0))[0] || null;
}

function assessQuota(candidate, entry, snapshot, nowMs, maxAgeMs) {
  const quotaClass = entry.quota_class || candidate.quota_class;
  const isUnlimitedRateLimited = quotaClass === "unlimited_with_rate_limit";
  const pct = snapshot?.pct ?? null;
  const ageMs = snapshot?.updated_ms === null || snapshot?.updated_ms === undefined
    ? null
    : nowMs - snapshot.updated_ms;
  const fresh = Boolean(snapshot && snapshot.updated_ms && ageMs >= -2 * 60 * 1000 && ageMs <= maxAgeMs);
  const defaultHeadroom = {
    unlimited_with_rate_limit: 1,
    dedicated_regenerating: 0.5,
    rate_limited_free: 0.25,
    shared_subscription: 0,
  }[quotaClass] ?? 0.5;

  let available = true;
  let status = "untracked";
  if (isUnlimitedRateLimited) {
    status = "static_unlimited_rate_limited";
  } else if (fresh && pct !== null && pct <= 0) {
    available = false;
    status = "exhausted";
  } else if (quotaClass === "shared_subscription" && (!fresh || pct === null)) {
    available = false;
    status = "stale_or_missing";
  } else if (!snapshot) {
    status = quotaClass === "rate_limited_free" ? "untracked_rate_limited_free" : "untracked_dedicated";
  } else if (!fresh) {
    status = "stale_snapshot_allowed_by_class";
  } else {
    status = "current";
  }

  return {
    quota_available: available,
    quota_headroom: fresh && pct !== null ? pct / 100 : defaultHeadroom,
    quota_status: status,
    quota_snapshot_fresh: fresh,
    quota_age_ms: ageMs,
    quota_source: snapshot?.source || (isUnlimitedRateLimited ? "static_registry" : null),
    quota_observed_at: snapshot?.updated_ms ? new Date(snapshot.updated_ms).toISOString() : null,
    quota_windows: snapshot?.windows || undefined,
  };
}

function latencyForRole(entry, role) {
  const latency = entry?.dispatch_latency?.PI || entry?.dispatch_latency?.pi_cli;
  if (!latency || typeof latency !== "object") return null;
  const keys = {
    mechanical: ["probe", "structured"],
    extraction: ["probe", "structured"],
    verification: ["reasoning", "structured"],
    coding: ["code-gen", "multi-step"],
    structured_output: ["structured"],
    reasoning: ["reasoning", "multi-step"],
    multimodal: [],
  }[role] || [];
  const values = keys.map((key) => Number(latency[key])).filter(Number.isFinite);
  return values.length ? values.reduce((sum, value) => sum + value, 0) / values.length : null;
}

function findFleetEntry(registry, candidate) {
  const direct = registry.models?.[candidate.registry_slug];
  if (direct) {
    const laneEntry = Object.values(registry.lanes || {})
      .flatMap((lane) => ["tier1", "tier2"].flatMap((tier) => lane?.[tier] || []))
      .find((value) => value?.slug === candidate.registry_slug);
    return laneEntry ? { ...direct, ...laneEntry, transports: direct.transports } : direct;
  }
  return Object.values(registry.models || {}).find((value) => value?.provider === candidate.provider && value?.model === candidate.model)
    || Object.values(registry.lanes || {})
      .flatMap((lane) => ["tier1", "tier2"].flatMap((tier) => lane?.[tier] || []))
      .find((value) => value?.slug === candidate.registry_slug);
}

function authoritativeHealth(candidate, input, role, { allowTestPaths = false } = {}) {
  const paths = fleetPaths(input, { allowTestPaths });
  const registry = readJson(paths.registry);
  const quotaCache = readJson(paths.quota) || {};
  const piModels = readJson(paths.piModels);
  const nowMs = input.now_ms || Date.now();
  if (!registry) return { available: false, health_source: "fleet_registry_missing", unverified: true };

  const entry = findFleetEntry(registry, candidate);
  if (!entry) return { available: false, health_source: "candidate_missing_from_fleet_registry", unverified: true };

  const transport = entry.transports?.pi_cli || {};
  if (BROKEN_TRANSPORT_STATUSES.has(transport.status)) {
    return {
      available: false,
      health_source: "fleet_registry",
      registry_transport_status: transport.status,
      provider_unavailable: true,
    };
  }

  const configuredModels = piModels?.providers?.[candidate.provider]?.models || [];
  const configured = configuredModels.some((model) => model?.id === candidate.model);
  if (!configured) {
    return { available: false, health_source: "pi_model_registry", provider_unavailable: true, model_not_configured: true };
  }

  const quotaProvider = candidate.quota_provider || candidate.provider;
  const quota = quotaSnapshot(quotaCache, paths.quotaState, quotaProvider);
  const quotaAssessment = assessQuota(
    candidate,
    entry,
    quota,
    nowMs,
    input.quota_max_age_ms ?? DEFAULT_QUOTA_MAX_AGE_MS,
  );
  const latencyMs = latencyForRole(entry, role);
  return {
    available: quotaAssessment.quota_available,
    ...quotaAssessment,
    quota_class: entry.quota_class || candidate.quota_class,
    registry_transport_status: transport.status || "unknown",
    registry_transport_verified_at: transport.verified_at || null,
    configured_model: true,
    latency_ms: latencyMs === null ? null : latencyMs * 1000,
    evidence_count: latencyMs === null ? 0 : Object.keys(entry.dispatch_latency?.PI || {}).length,
    health_source: "fleet_registry_and_quota_cache",
  };
}

function healthFor(candidate, input, role, { allowUntrustedHealth = false } = {}) {
  if (allowUntrustedHealth) {
    const raw = input.provider_health?.[candidate.provider]
      || input.provider_health?.[candidate.quota_pool];
    if (raw) {
      if (!raw.observed_at) return { ...raw, health_source: "test_override" };
      const observedAt = Date.parse(raw.observed_at);
      const now = input.now_ms || Date.now();
      const maxAge = input.health_max_age_ms ?? DEFAULT_HEALTH_MAX_AGE_MS;
      return Number.isFinite(observedAt) && now - observedAt <= maxAge
        ? { ...raw, health_source: "test_override" }
        : { stale: true, health_source: "test_override" };
    }
    return { health_source: "test_static" };
  }
  return authoritativeHealth(candidate, input, role, { allowTestPaths: allowUntrustedHealth });
}

function rejectReasons(candidate, input, health) {
  const reasons = [];
  const requiredContext = Number(input.context_tokens || 0);
  if (requiredContext > 0 && candidate.context_window && requiredContext > candidate.context_window) {
    reasons.push("context_window_insufficient");
  }
  if (input.requires_tools && !candidate.capabilities.tools) reasons.push("tool_use_unsupported");
  if (input.requires_images && !candidate.capabilities.images) reasons.push("image_input_unsupported");
  if (input.requires_reasoning && !candidate.capabilities.reasoning) reasons.push("reasoning_unsupported");
  if (input.requires_structured_output && !candidate.capabilities.structured_output) reasons.push("structured_output_unsupported");
  if (health.available === false) reasons.push("provider_unavailable");
  if (health.quota_status === "stale_or_missing") reasons.push("provider_quota_snapshot_unavailable");
  if (health.quota_available === false && health.quota_class !== "unlimited_with_rate_limit") reasons.push("provider_quota_unavailable");
  if (health.rate_limit_available === false) reasons.push("provider_rate_limit_unavailable");
  if (health.concurrency_available === false) reasons.push("provider_concurrency_unavailable");
  if (health.reliability !== undefined && health.reliability < (input.reliability_floor ?? 0.8)) {
    reasons.push("provider_reliability_below_floor");
  }
  return reasons;
}

function rank(candidate, health) {
  const reliability = health.reliability ?? 0.5;
  const quotaClass = health.quota_class || candidate.quota_class;
  const scarcityPreference = {
    unlimited_with_rate_limit: 4,
    dedicated_regenerating: 3,
    shared_subscription: 2,
    rate_limited_free: 1,
  }[quotaClass] || 0;
  const quota = health.quota_headroom ?? (quotaClass === "unlimited_with_rate_limit" ? 1 : 0.5);
  const latency = health.p90_latency_ms ?? health.latency_ms ?? Number.MAX_SAFE_INTEGER;
  const measured = !health.stale && (health.p90_latency_ms !== undefined || health.latency_ms !== undefined);
  const latencyPreference = measured ? -latency : 0;
  return [
    reliability,
    measured ? 1 : 0,
    latencyPreference,
    measured ? scarcityPreference : 0,
    measured ? quota : 0,
    candidate.priority,
  ];
}

function compareRanks(a, b) {
  for (let index = 0; index < a.length; index += 1) {
    if (a[index] !== b[index]) return b[index] - a[index];
  }
  return 0;
}

export function selectModel(input = {}, { allowUntrustedHealth = false } = {}) {
  const candidates = input.model_candidates || MODEL_CANDIDATES;
  const role = taskRole(input);
  const evaluated = candidates.map((candidate) => {
    const health = healthFor(candidate, input, role, { allowUntrustedHealth });
    const rejected = rejectReasons(candidate, input, health);
    return { candidate, health, rejected, roleFit: candidate.roles[role] || 0, rank: rejected.length === 0 ? rank(candidate, health) : null };
  });
  const eligible = evaluated.filter((entry) => entry.rejected.length === 0 && (entry.candidate.roles[role] || 0) > 0);
  if (eligible.length === 0) {
    return {
      status: "no_eligible_candidate",
      role,
      candidates_considered: evaluated.map(({ candidate, rejected }) => ({ id: candidate.id, rejected })),
      reason: "no_external_candidate_cleared_capability_quota_and_health_gates",
    };
  }

  const bestRoleFit = Math.max(...eligible.map((entry) => entry.roleFit));
  const roleFitMargin = input.role_fit_margin ?? 8;
  const qualityQualified = eligible.filter((entry) => entry.roleFit >= bestRoleFit - roleFitMargin);
  qualityQualified.sort((a, b) => compareRanks(a.rank, b.rank));
  const selected = qualityQualified[0];
  const { candidate, health } = selected;
  const reasons = [`best_role_fit:${role}`, `quota_pool:${candidate.quota_pool}`, `quota_class:${health.quota_class || candidate.quota_class}`];
  if (health.quota_status) reasons.push(`quota_status:${health.quota_status}`);
  if (health.quota_source) reasons.push(`quota_source:${health.quota_source}`);
  if (health.stale) reasons.push("health_snapshot_stale_ignored");
  if (health.p90_latency_ms !== undefined) reasons.push(`p90_latency_ms:${health.p90_latency_ms}`);
  if (health.latency_ms !== undefined) reasons.push(`dispatch_latency_ms:${health.latency_ms}`);
  if (health.quota_headroom !== undefined) reasons.push(`quota_headroom:${health.quota_headroom}`);
  if (health.reliability !== undefined) reasons.push(`reliability:${health.reliability}`);

  return {
    status: "selected",
    candidate_id: candidate.id,
    worker: candidate.worker,
    provider: candidate.provider,
    model: candidate.model,
    role,
    quota_pool: candidate.quota_pool,
    confidence: health.health_source === "test_override"
      ? (health.evidence_count >= 5 && health.reliability !== undefined ? "measured" : "unverified")
      : health.health_source === "fleet_registry_and_quota_cache" && health.available === true
        ? (health.registry_transport_status === "working" ? "measured" : "provisional")
        : "unverified",
    health_source: health.health_source || null,
    reasons,
    alternatives: qualityQualified.slice(1).map(({ candidate: alternative }) => alternative.id),
  };
}
