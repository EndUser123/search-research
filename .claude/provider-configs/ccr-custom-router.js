// ponytail: per-request CCR custom router for local-first coding delegation.
//
// AUTHORITY SPLIT (stable mental model — read before editing):
// - CC reads settings.json["model"] ONCE at session start (documented hot-reload
//   exception) and sends it as req.body.model — a LABEL, not the final route.
//   Mid-session switching is via /model + ANTHROPIC_MODEL, not the file.
// - CCR is the per-request routing authority. This function is the consumption
//   point that actually chooses the backend per outbound request.
// - Hooks (cc-model-router) can only write hints/config — they do NOT override
//   CCR. Any same-turn autoswitch MUST live here (request time), not in a
//   settings.json write. Full contract + falsification tests:
//   packages/.claude-marketplace/plugins/cc-model-router/SKILL.md ("Routing contract").
//
// ROUTING POLICY:
//   - Coding tasks: local llama.cpp first (aggressive), then M3, then GLM-5.2.
//   - Reasoning/planning: GLM-5.2.
//   - Background: haiku/background tier (fall through to CCR Router.background).
//   - Pin state overrides automatic routing until cleared.
//
// TOKEN ESTIMATION:
//   CCR pre-computes req.tokenCount before calling this function. Use it directly.
//   Compared against local model's maxContextTokens * threshold fraction.
//   Safety margin: aggressive=0.90, conservative=0.65 of maxContextTokens.
//
// STATE FILES (read per request):
//   - P:/.claude/state/local-model-state.json   → local model context window
//   - P:/.claude/state/ccr-routing-hint.json     → task-type hint from hooks
//   - P:/.claude/state/ccr-pin-state.json        → explicit /model pin state
//   - P:/.claude/state/ccr-route-state.json      → last route (written on change)
//
// RESTART REQUIRED AFTER EDIT: CCR loads this module via require() at startup
// and Node caches it — config.json is hot-reloaded, but this file is NOT.
// Editing it without restarting CCR leaves the old routing in memory.
const fs = require("fs");
const path = require("path");

const STATE_DIR = "P:/.claude/state";
const LOCAL_MODEL_STATE = path.join(STATE_DIR, "local-model-state.json");
const HINT_FILE = path.join(STATE_DIR, "ccr-routing-hint.json");
const PIN_FILE = path.join(STATE_DIR, "ccr-pin-state.json");
const ROUTE_STATE_FILE = path.join(STATE_DIR, "ccr-route-state.json");
const ROUTING_LOG_FILE = path.join(STATE_DIR, "ccr-route-log.jsonl");
const ROUTING_POLICY_FILE = path.join(STATE_DIR, "routing-policy.json");

// cc-model-router writes recommendation.json per (terminal, session).
const MODEL_ROUTER_STATE_DIR = path.join(STATE_DIR, "model-router");
const RECOMMENDATION_TTL_MS = 300000; // 5 min — stale recs must not leak across tasks

// --- Helpers ---

function readJsonSafe(filePath) {
  try {
    return JSON.parse(fs.readFileSync(filePath, "utf-8"));
  } catch {
    return null;
  }
}

function writeJsonSafe(filePath, data) {
  try {
    fs.mkdirSync(path.dirname(filePath), { recursive: true });
    fs.writeFileSync(filePath, JSON.stringify(data, null, 2), "utf-8");
  } catch {
    // Best effort — route state write failure should not block routing
  }
}

function getLocalModelState() {
  const state = readJsonSafe(LOCAL_MODEL_STATE);
  if (!state || !state.active_model || !state.models?.length) return null;
  const active = state.models.find((m) => m.id === state.active_model);
  return active || null;
}

function getRoutingPolicy() {
  return readJsonSafe(ROUTING_POLICY_FILE);
}

// --- Local model availability probe (live > state file) ---
// The state file written by run-ornith-server.ps1 persists across server restarts
// and can be stale if the server was started independently. A live HTTP probe is
// authoritative: CC-ccr.ps1 uses /health; this mirrors that check with a cache
// so we don't probe on every request.
const LOCAL_HEALTH_URL = "http://127.0.0.1:8010/health";
const LOCAL_INFERENCE_URL = "http://127.0.0.1:8010/v1/chat/completions";
const PROBE_TIMEOUT_MS = 1500;
const CACHE_WINDOW_MS = 10000;
const DEFAULT_LOCAL_CTX = 65536; // matches llama.cpp -c flag in run-ornith-server.ps1

let _probeCache = { lastCheckedAt: 0, available: false, reason: null };

async function isLocalModelAvailable() {
  const now = Date.now();
  if (now - _probeCache.lastCheckedAt < CACHE_WINDOW_MS) {
    if (_probeCache.available) {
      try { process.stderr.write("[CCR-route] local probe cache hit (available)\n"); } catch {}
    }
    return _probeCache.available;
  }

  // Primary: /health endpoint (same check as cc-ccr.ps1)
  try {
    const ac = new AbortController();
    const t = setTimeout(() => ac.abort(), PROBE_TIMEOUT_MS);
    const resp = await fetch(LOCAL_HEALTH_URL, { signal: ac.signal });
    clearTimeout(t);
    if (resp.ok) {
      _probeCache = { lastCheckedAt: Date.now(), available: true, reason: null };
      try { process.stderr.write("[CCR-route] /health OK — local available\n"); } catch {}
      return true;
    }
  } catch { /* fall through */ }

  // Fallback: minimal inference probe (tiny prompt, no quota cost)
  try {
    const body = JSON.stringify({
      model: "ornith-1.0-9b",
      messages: [{ role: "user", content: "hi" }],
      max_tokens: 1,
    });
    const ac = new AbortController();
    const t = setTimeout(() => ac.abort(), PROBE_TIMEOUT_MS);
    const resp = await fetch(LOCAL_INFERENCE_URL, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body,
      signal: ac.signal,
    });
    clearTimeout(t);
    if (resp.ok) {
      _probeCache = { lastCheckedAt: Date.now(), available: true, reason: null };
      try { process.stderr.write("[CCR-route] inference probe OK — local available\n"); } catch {}
      return true;
    }
  } catch (e) {
    _probeCache = { lastCheckedAt: Date.now(), available: false, reason: e.message };
  }

  try { process.stderr.write("[CCR-route] local unavailable — both probes failed\n"); } catch {}
  return false;
}

async function getLocalModelProbed() {
  const fromFile = getLocalModelState();
  if (fromFile && fromFile.maxContextTokens) return fromFile;

  // State file missing or stale — live probe is authoritative
  const live = await isLocalModelAvailable();
  if (live) {
    try {
      process.stderr.write(
        "[CCR-route] state file missing/stale — using live-probe default ctx (" + DEFAULT_LOCAL_CTX + ")\n"
      );
    } catch {}
    return { id: "ornith-1.0-9b", maxContextTokens: DEFAULT_LOCAL_CTX };
  }
  return null;
}

function logRoutingEvent(entry) {
  try {
    fs.mkdirSync(path.dirname(ROUTING_LOG_FILE), { recursive: true });
    fs.appendFileSync(ROUTING_LOG_FILE, JSON.stringify(entry) + "\n");
  } catch {}
}

function getRoutingHint() {
  const hint = readJsonSafe(HINT_FILE);
  if (!hint) return null;
  // Expire hints after 60s (one prompt should produce one hint, consumed once)
  const age = Date.now() - new Date(hint.ts).getTime();
  if (age > 60000) return null;
  return hint;
}

function getPinState() {
  return readJsonSafe(PIN_FILE);
}

function getRoutingMode(config) {
  return config.routingMode || "aggressive";
}

function getThreshold(config, mode) {
  const thresholds = config.routingThresholds || {};
  return thresholds[mode] || (mode === "aggressive" ? 0.90 : 0.65);
}

function getTokenBudget(config, route) {
  // Per-model token budget (approx). Defined in config.tokenBudgets.
  // Falls back to defaultFallback if no per-route budget configured.
  if (!config || !config.tokenBudgets) return null;
  const budgets = config.tokenBudgets;
  return budgets[route] ?? budgets.defaultFallback ?? null;
}

function emitRouteChange(newRoute, reason, req, extras) {
  const prev = readJsonSafe(ROUTE_STATE_FILE);
  if (prev && prev.route === newRoute) return; // No change, no emission

  const state = {
    route: newRoute,
    reason,
    ts: new Date().toISOString(),
    ...(extras || {}),
  };
  writeJsonSafe(ROUTE_STATE_FILE, state);

  // CCR does not expose a UI-channel for proxy-injected messages, so the most
  // truthful "system message on route change" is to annotate req.body.system
  // (the model sees it; the user sees it indirectly via the model's response).
  // The annotation is also surfaced to stderr so the user can tail the CCR
  // log and observe routing in real time.
  const notice = `[CCR-route] ${newRoute ?? "fall-through"} — ${reason}`;
  if (req) injectSystemMessage(req, notice);
  try {
    process.stderr.write(`[CCR-route] ${notice}\n`);
  } catch {}
}

// Append a text block to req.body.system (string-or-array form per Anthropic
// API). Idempotent w.r.t. existing entries: only adds if not already present.
function injectSystemMessage(req, text) {
  if (!req || !req.body) return;
  const annot = { type: "text", text };
  if (req.body.system === undefined || req.body.system === null) {
    req.body.system = [annot];
  } else if (typeof req.body.system === "string") {
    req.body.system = [
      { type: "text", text: req.body.system },
      annot,
    ];
  } else if (Array.isArray(req.body.system)) {
    // Dedupe: if the most recent entry already contains this notice, skip.
    const last = req.body.system[req.body.system.length - 1];
    if (last && last.type === "text" && last.text === text) return;
    req.body.system.push(annot);
  } else {
    req.body.system = [annot]; // unknown shape — fall back
  }
}

// --- Recommendation (cc-model-router) consumption ---
// CCR is process-scoped (one CCR instance per terminal via cc-ccr.ps1), so the
// freshest non-consumed, non-expired recommendation.json across the
// (terminal, session) tree is the right per-request signal. recommendation.json
// is the source of truth; the ccr-routing-hint.json file is a secondary task-type
// hint. TTL + consumed guard prevent stale recs from leaking into new tasks.
function getRecommendation() {
  let terminals = [];
  try { terminals = fs.readdirSync(MODEL_ROUTER_STATE_DIR); } catch { return null; }
  const now = Date.now();
  let best = null;
  let bestTs = 0;
  for (const terminal of terminals) {
    let sessions = [];
    try { sessions = fs.readdirSync(path.join(MODEL_ROUTER_STATE_DIR, terminal)); } catch { continue; }
    for (const session of sessions) {
      const p = path.join(MODEL_ROUTER_STATE_DIR, terminal, session, "recommendation.json");
      let rec;
      try { rec = JSON.parse(fs.readFileSync(p, "utf-8")); } catch { continue; }
      if (rec.consumed) continue;
      const written = Date.parse(rec.written_at || "");
      if (!written) continue;
      if (now - written > RECOMMENDATION_TTL_MS) continue;
      if (written > bestTs) { bestTs = written; best = rec; }
    }
  }
  return best;
}

// task-type bucket → pin key (spec: coding_pin / thinking_pin / background_pin)
function pinKeyForTask(taskType) {
  if (taskType === "reasoning") return "thinking_pin";
  if (taskType === "background") return "background_pin";
  return "coding_pin"; // coding | trivial-coding | local-coding
}

// Reverse-map a CCR route string to a CC alias for logging.
function routeToAlias(route, fallback) {
  if (!route) return fallback || null;
  const m = {
    "zai,glm-5.2": "claude-opus-4-8",
    "minimax,MiniMax-M3[1m]": "claude-sonnet-5",
    "opencode-go,deepseek-v4-flash": "claude-haiku-4-5-20251001",
  };
  if (m[route]) return m[route];
  if (route.startsWith("llama-cpp,")) return "claude-local-ornith";
  return route;
}

// "minimax,MiniMax-M3[1m]" -> { provider: "minimax", model: "MiniMax-M3[1m]" }
function splitRoute(route) {
  if (!route) return { provider: null, model: null };
  const i = route.indexOf(",");
  return i < 0 ? { provider: route, model: null } : { provider: route.slice(0, i), model: route.slice(i + 1) };
}

function describePins(pin) {
  if (!pin) return "none";
  const parts = [];
  for (const k of ["coding_pin", "thinking_pin", "background_pin"]) if (pin[k]) parts.push(`${k}=${pin[k]}`);
  if (pin.model) parts.push(`global=${pin.model}`); // legacy wildcard
  return parts.length ? parts.join(",") : "none";
}

// tier → default cloud route (used when local unavailable / over budget)
function routeByTier(tier) {
  if (tier === "haiku") return "opencode-go,deepseek-v4-flash";
  if (tier === "opus") return "zai,glm-5.2";
  return "minimax,MiniMax-M3[1m]"; // sonnet / unknown
}

// --- Routing logic ---

// Map CC model labels to task-type heuristics when no hook hint is available.
// This is the fallback when ccr-routing-hint.json doesn't exist.
function inferTaskType(model, messages) {
  if (model === "claude-local-ornith") return "local-coding";
  if (model === "claude-haiku-4-5" || model === "claude-haiku-4-5-20251001") return "background";

  // Heuristic: short user messages with code-like content = coding
  const lastUser = [...(messages || [])].reverse().find((m) => m.role === "user");
  if (lastUser) {
    const content = typeof lastUser.content === "string" ? lastUser.content : "";
    const hasCode = /```|def |class |function |import |from |const |let |var |fn |pub |#include/.test(content);
    const hasReasoningWords = /architecture|design|plan|tradeoff|approach|compare|analyze|explain the|deep dive|strategy/i.test(content);
    if (hasReasoningWords) return "reasoning";
    if (hasCode) return "coding";
    if (content.length < 200) return "trivial-coding";
  }
  return "coding"; // Default: assume coding for Claude Code
}

module.exports = async function router(req, config) {
  const model = req?.body?.model;
  const messages = req?.body?.messages || [];
  const tokenCount = req?.tokenCount || 0;

  // Decision order: pin (per task type) → local-first → classifier rec → default.
  const hint = getRoutingHint();
  const taskType = hint?.taskType || inferTaskType(model, messages);
  const pin = getPinState() || {};
  const rec = getRecommendation();

  // decide(): log the full effective-route field set, emit route change, return route.
  const decide = (route, reason, decisionSource, guardrailOverride = false) => {
    const backend = splitRoute(route);
    logRoutingEvent({
      ts: new Date().toISOString(),
      terminal_id: rec?.terminal_id || "unknown",
      session_id: rec?.session_id || hint?.sessionId || "unknown",
      task_type: taskType,
      session_model_alias: model || null,
      pin_state: describePins(pin),
      recommended_tier: rec?.recommended_tier || null,
      recommended_model: rec?.recommended_model || null,
      effective_route_alias: routeToAlias(route, model),
      backend_provider: backend.provider,
      backend_model: backend.model,
      local_used: backend.provider === "llama-cpp",
      decision_source: decisionSource,
      guardrail_override: guardrailOverride,
      token_count: tokenCount,
      reason,
    });
    // Strip Anthropic extended-thinking on the opencode-go path BEFORE the
    // CCR openai transformer adds the rejected `r.reasoning` field. Single
    // insertion covers every decision path (pin / background / reasoning /
    // coding / no-local). Idempotent on the body. Stderr-annotated for
    // CCR log tailers.
    if (route) stripThinkingForOpencodeGo(req, backend.provider);
    emitRouteChange(route, reason, req);
    return route;
  };

  // --- 1. Pin override (per task type; legacy global `model` pin = wildcard) ---
  const pinKey = pinKeyForTask(taskType);
  const pinnedAlias = pin[pinKey] || pin.model;
  if (pinnedAlias) {
    const pinRoute = resolveModelToRoute(pinnedAlias);
    if (pinRoute) {
      return decide(pinRoute, `pin ${pin[pinKey] ? pinKey : "global"}: ${pinnedAlias}`, "pin");
    }
  }

  // --- 2. Background: classifier haiku rec if present, else fall through ---
  if (taskType === "background") {
    if (rec?.recommended_tier === "haiku" && rec.recommended_model) {
      const r = resolveModelToRoute(rec.recommended_model);
      if (r) return decide(r, "background — classifier haiku rec", "classifier");
    }
    return decide(null, "background — fall through to CCR Router.background", "default");
  }

  // --- 3. Reasoning: classifier opus rec, else default GLM-5.2 (token-budget gated) ---
  if (taskType === "reasoning") {
    let route = "zai,glm-5.2";
    let source = "default";
    if (rec?.recommended_tier === "opus" && rec.recommended_model) {
      const r = resolveModelToRoute(rec.recommended_model);
      if (r) { route = r; source = "classifier"; }
    }
    const budget = getTokenBudget(config, route);
    if (budget && tokenCount > budget) {
      return decide("minimax,MiniMax-M3[1m]", `token-budget: ${tokenCount} > ${budget} for ${route}, fell back to M3`, source);
    }
    return decide(route, `reasoning — ${route} (tokenCount=${tokenCount}, budget=${budget})`, source);
  }

  // --- 4. Coding: local-first → classifier tier fallback → default M3 ---
  const localModel = await getLocalModelProbed();
  const mode = getRoutingMode(config);
  const threshold = getThreshold(config, mode);
  const tierRoute = rec?.recommended_tier ? routeByTier(rec.recommended_tier) : "minimax,MiniMax-M3[1m]";
  const tierSource = rec?.recommended_tier ? "classifier" : "default";

  if (localModel && localModel.maxContextTokens) {
    const effectiveCtx = Math.floor(localModel.maxContextTokens * threshold);
    const wantLocal = mode === "aggressive" || model === "claude-local-ornith" || taskType === "trivial-coding";

    if (wantLocal && tokenCount <= effectiveCtx) {
      return decide(`llama-cpp,${localModel.id}`, `local-first (${taskType}, ${tokenCount} <= ${effectiveCtx})`, "local-first");
    }
    if (wantLocal) {
      // Over local ctx — escalate by classifier tier (or M3 default)
      return decide(tierRoute, `escalated: ${tokenCount} > ${effectiveCtx} local ctx; tier=${rec?.recommended_tier || "none"}`, tierSource);
    }
    // Conservative non-trivial coding: tier/M3
    return decide(tierRoute, `conservative-cloud (${taskType}, ${tokenCount}); tier=${rec?.recommended_tier || "none"}`, tierSource);
  }

  // --- No local model: classifier tier or M3 ---
  return decide(tierRoute, `no-local-model (${taskType}); tier=${rec?.recommended_tier || "none"}`, tierSource);
};

// Pre-transform body patch: when the route is opencode-go AND the request
// carries Anthropic extended-thinking AND non-empty tools, strip thinking before
// the CCR openai transformer runs. Without this, the transformer emits
// `r.reasoning = { effort, enabled }` (dist/cli.js openai transform), which
// opencode-go's Console Go upstream rejects with 400 invalid_request_error on
// the {reasoning-model, tools, thinking} triple (musistudio issue #1378:
// "DeepSeek V4 Pro + thinking mode + tool calls: 400, no working workaround").
// Tool reinjection is NOT the bug here (the transformer handles it correctly);
// the rejected field is `reasoning`. Stripping thinking fixes the 400;
// tools continue to pass through the transform normally.
function stripThinkingForOpencodeGo(req, backendProvider) {
  if (backendProvider !== "opencode-go") return false;
  const body = req?.body;
  if (!body) return false;
  const thinking = body.thinking;
  const thinkingOn = thinking && thinking.type === "enabled";
  const hasTools = Array.isArray(body.tools) && body.tools.length > 0;
  if (!thinkingOn || !hasTools) return false;
  // Drop top-level thinking field; transform will skip the r.reasoning line.
  delete body.thinking;
  // Strip any thinking/redacted_thinking content blocks already in messages,
  // so they don't reach the upstream as malformed shapes.
  if (Array.isArray(body.messages)) {
    for (const m of body.messages) {
      if (!Array.isArray(m?.content)) continue;
      m.content = m.content.filter((b) => b && b.type !== "thinking" && b.type !== "redacted_thinking");
    }
  }
  try {
    process.stderr.write("[CCR-route] stripped thinking for opencode-go (tools=" +
      (body.tools?.length ?? 0) + ") — see #1378\n");
  } catch {}
  return true;
}

// --- Model name to CCR route resolution ---

function resolveModelToRoute(modelName) {
  if (!modelName) return null;

  // Direct route strings
  if (modelName.includes(",")) return modelName;

  // CC model label → CCR route mapping (matches config.json Router keys).
  // CANONICAL primary key is claude-sonnet-5; claude-sonnet-4-6 retained
  // for backward compat only (do NOT add new mainline route expansions on 4-6).
  const routeMap = {
    "claude-opus-4-8": "zai,glm-5.2",
    "claude-sonnet-5": "minimax,MiniMax-M3[1m]",   // CANONICAL primary
    "claude-sonnet-4-6": "minimax,MiniMax-M3[1m]", // BACKWARD COMPAT ONLY
    "claude-haiku-4-5": "opencode-go,deepseek-v4-flash",
    "claude-haiku-4-5-20251001": "opencode-go,deepseek-v4-flash",
    "claude-local-ornith": "llama-cpp,ornith-1.0-9b",
  };

  return routeMap[modelName] || null;
}
