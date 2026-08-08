import { readdirSync, readFileSync } from "node:fs";
import { homedir } from "node:os";
import { join } from "node:path";

const DEFAULT_FLEET_REGISTRY = join(homedir(), ".grok", "skills", "model-quota", "scripts", "fleet-models.json");
const DEFAULT_QUOTA_CACHE = join(homedir(), ".cache", "opencode", "fleet-quota-cache.json");
const DEFAULT_QUOTA_STATE = join(homedir(), ".cache", "opencode", "quota-provider-state");
const DEFAULT_PI_MODELS = join(homedir(), ".pi", "agent", "models.json");
const FLEET_REGISTRY_SCHEMA_VERSION = 5;
const CODEX_ORCHESTRATOR = "codex";
const PI_INVOCATION_METHOD = "pi";
const REGISTRY_PROVIDER_ALIASES = Object.freeze({
  "opencode-go": Object.freeze(["opencode-go"]),
  "opencode-zen": Object.freeze(["opencode-zen", "zen"]),
  "nvidia-nim": Object.freeze(["nvidia-nim", "nvidia", "nim"]),
  minimax: Object.freeze(["minimax"]),
  zai: Object.freeze(["zai"]),
});
const DEFAULT_CANDIDATES = [
  {
    id: "opencode-go/deepseek-v4-flash",
    registry_slug: "codex-opencode-go-deepseek-v4-flash",
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
    registry_slug: "codex-nvidia-nim-deepseek-ai-deepseek-v4-flash",
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
    registry_slug: "codex-nvidia-nemotron-3-ultra",
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
    registry_slug: "codex-minimax-m3",
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
    registry_slug: "codex-zai-glm-5-2",
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
    registry_slug: "codex-opencode-zen-deepseek-v4-flash-free",
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
const EXPECTED_PI_BASE_URLS = Object.freeze({
  "opencode-go": "https://opencode.ai/zen/go/v1",
  "opencode-zen": "https://opencode.ai/zen/v1",
  "nvidia-nim": "https://integrate.api.nvidia.com/v1",
  minimax: "https://api.minimax.io/anthropic",
  zai: "https://api.z.ai/api/coding/paas/v4",
});

export const MODEL_CANDIDATES = Object.freeze(DEFAULT_CANDIDATES.map((candidate) => Object.freeze({
  ...candidate,
  orchestrator: CODEX_ORCHESTRATOR,
  invocation_method: PI_INVOCATION_METHOD,
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

function latencyForRole(entry) {
  // The shared v5 registry may contain Grok/spawn evidence for the same
  // provider and model. That evidence is not Codex/Pi evidence and must not
  // influence this selector. Only an explicitly identity-bound Codex/Pi
  // evidence block is eligible for live latency ranking.
  const identity = entry?.evidence?.identity;
  if (identity?.orchestrator !== CODEX_ORCHESTRATOR || identity?.invocation_method !== PI_INVOCATION_METHOD) {
    return null;
  }
  const latency = entry.evidence?.latency;
  const p90 = Number(latency?.p90);
  return Number.isFinite(p90) ? p90 : null;
}

function registryProviderMatches(entry, candidate) {
  const allowed = REGISTRY_PROVIDER_ALIASES[candidate.provider] || [candidate.provider];
  return allowed.includes(entry?.provider);
}

function resolveFleetEntry(registry, candidate) {
  if (registry?.schema_version !== FLEET_REGISTRY_SCHEMA_VERSION || !Array.isArray(registry.candidates)) {
    return { error: "fleet_registry_schema_unsupported" };
  }
  const matches = registry.candidates.filter((value) => value?.id === candidate.registry_slug);
  if (!matches.length) return { error: "candidate_missing_from_fleet_registry" };
  const expectedOrchestrator = candidate.orchestrator || CODEX_ORCHESTRATOR;
  const entry = matches.find((value) => value?.orchestrator === expectedOrchestrator);
  if (!entry) {
    return { error: "candidate_orchestrator_binding_missing", entry: matches[0] };
  }
  if (!registryProviderMatches(entry, candidate)) {
    return { error: "registry_provider_mismatch", entry };
  }
  if (entry.model !== candidate.model) {
    return { error: "registry_model_binding_mismatch", entry };
  }
  const expectedTransport = candidate.invocation_method || PI_INVOCATION_METHOD;
  const registryTransport = entry.invocation_method || entry.transport || entry.dispatch_path || null;
  if (registryTransport !== expectedTransport
    || (entry.transport && entry.transport !== expectedTransport)
    || (entry.dispatch_path && entry.dispatch_path !== expectedTransport)) {
    return { error: "registry_transport_binding_mismatch", entry };
  }
  return { entry };
}

function piDispatchPaths(entry) {
  const paths = Array.isArray(entry?.dispatch_paths) ? [...entry.dispatch_paths] : [];
  if (entry?.dispatch_path) paths.push(entry.dispatch_path);
  return new Set(paths.map((path) => String(path).toLowerCase()));
}

function registryLatencyAllowed(registry) {
  // Quarantine the implicit-write format used by the old benchmark writer.
  // Its measurements remain historical evidence, but were copied across
  // role lanes and must not influence live routing.
  return registry.provenance?.reason !== "model-benchmark dispatch latency write-back";
}

function authoritativeHealth(candidate, input, role, { allowTestPaths = false } = {}) {
  const paths = fleetPaths(input, { allowTestPaths });
  const registry = readJson(paths.registry);
  const quotaCache = readJson(paths.quota) || {};
  const piModels = readJson(paths.piModels);
  const nowMs = input.now_ms || Date.now();
  if (!registry) return { available: false, health_source: "fleet_registry_missing", unverified: true };

  const resolved = resolveFleetEntry(registry, candidate);
  if (resolved.error) {
    return {
      available: false,
      health_source: "fleet_registry",
      registry_error: resolved.error,
      unverified: true,
    };
  }
  const entry = resolved.entry;

  if (!piDispatchPaths(entry).has(PI_INVOCATION_METHOD)) {
    return {
      available: false,
      health_source: "fleet_registry",
      registry_error: "pi_dispatch_unavailable",
      provider_unavailable: true,
    };
  }
  if (entry.lifecycle !== "active") {
    return {
      available: false,
      health_source: "fleet_registry",
      registry_error: `lifecycle_${entry.lifecycle || "missing"}`,
      provider_unavailable: true,
    };
  }
  if (entry.policy === "excluded") {
    return {
      available: false,
      health_source: "fleet_registry",
      registry_error: "registry_policy_excluded",
      provider_unavailable: true,
    };
  }

  // v5 stores transport availability as dispatch_paths. A legacy
  // pi_cli-status block is accepted only as an explicitly Pi-scoped detail;
  // top-level serde/spawn compatibility views are intentionally ignored.
  const transport = entry.transports?.pi_cli || entry.transport_status?.pi_cli || {};
  if (BROKEN_TRANSPORT_STATUSES.has(transport.status)) {
    return {
      available: false,
      health_source: "fleet_registry",
      registry_transport_status: transport.status,
      provider_unavailable: true,
    };
  }

  const piProvider = piModels?.providers?.[candidate.provider];
  const configuredModels = piProvider?.models || [];
  const configuredModel = configuredModels.find((model) => model?.id === candidate.model);
  const configured = Boolean(configuredModel);
  if (!configured) {
    return { available: false, health_source: "pi_model_registry", provider_unavailable: true, model_not_configured: true };
  }
  const expectedBaseUrl = EXPECTED_PI_BASE_URLS[candidate.provider];
  if (expectedBaseUrl && piProvider?.baseUrl && piProvider.baseUrl.replace(/\/$/, "") !== expectedBaseUrl) {
    return {
      available: false,
      health_source: "pi_model_registry",
      provider_unavailable: true,
      binding_mismatch: `baseUrl:${piProvider.baseUrl}`,
    };
  }
  const effectiveCompat = { ...(piProvider?.compat || {}), ...(configuredModel?.compat || {}) };
  if (candidate.provider === "opencode-go" && piProvider?.compat && effectiveCompat.supportsDeveloperRole !== false) {
    return {
      available: false,
      health_source: "pi_model_registry",
      provider_unavailable: true,
      binding_mismatch: "opencode-go requires supportsDeveloperRole=false",
    };
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
  const latencyMs = registryLatencyAllowed(registry) ? latencyForRole(entry, role) : null;
  return {
    available: quotaAssessment.quota_available,
    ...quotaAssessment,
    quota_class: entry.quota_class || candidate.quota_class,
    registry_schema_version: FLEET_REGISTRY_SCHEMA_VERSION,
    registry_transport_status: transport.status || "unknown",
    registry_transport_verified_at: transport.verified_at || null,
    configured_model: true,
    latency_ms: latencyMs === null ? null : latencyMs * 1000,
    evidence_count: latencyMs === null ? 0 : Object.keys(entry.evidence?.sample_counts || {}).length,
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
  if (health.registry_error) reasons.push(health.registry_error);
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
    orchestrator: candidate.orchestrator || CODEX_ORCHESTRATOR,
    invocation_method: candidate.invocation_method || PI_INVOCATION_METHOD,
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
