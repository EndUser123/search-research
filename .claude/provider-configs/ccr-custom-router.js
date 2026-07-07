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

function emitRouteChange(newRoute, reason) {
  const prev = readJsonSafe(ROUTE_STATE_FILE);
  if (prev && prev.route === newRoute) return; // No change, no emission

  const state = {
    route: newRoute,
    reason,
    ts: new Date().toISOString(),
  };
  writeJsonSafe(ROUTE_STATE_FILE, state);

  // Emit system message via CCR's systemMessage injection (best effort)
  // The systemMessage field on the request body is what CCR forwards
  // to the LLM as a system-level annotation.
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

  // --- Pin override check ---
  const pin = getPinState();
  if (pin && pin.model) {
    // Pin is active — route to the pinned model, ignoring automatic logic
    const pinRoute = resolveModelToRoute(pin.model);
    if (pinRoute) {
      emitRouteChange(pinRoute, `pin: ${pin.model}`);
      return pinRoute;
    }
  }

  // --- Get routing hints ---
  const hint = getRoutingHint();
  const taskType = hint?.taskType || inferTaskType(model, messages);

  // --- Background tasks: fall through to CCR Router.background ---
  if (taskType === "background") {
    emitRouteChange(null, "background — fall through to CCR Router.background");
    return null; // CCR's default Router handles background slot
  }

  // --- Reasoning/planning: GLM-5.2 ---
  if (taskType === "reasoning") {
    const route = "zai,glm-5.2";
    emitRouteChange(route, "reasoning — GLM-5.2");
    return route;
  }

  // --- Coding tasks: local-first (aggressive) or M3-first (conservative) ---
  const localModel = getLocalModelState();
  const mode = getRoutingMode(config);
  const threshold = getThreshold(config, mode);

  if (localModel && localModel.maxContextTokens) {
    const effectiveCtx = Math.floor(localModel.maxContextTokens * threshold);

    // Local-first in aggressive mode (or if CC already targets local)
    if (mode === "aggressive" || model === "claude-local-ornith") {
      if (tokenCount <= effectiveCtx) {
        const route = `llama-cpp,${localModel.id}`;
        emitRouteChange(route, `local-first (${taskType}, ${tokenCount} tokens <= ${effectiveCtx} effective ctx)`);
        return route;
      }
      // Over threshold — escalate to M3
      const route = "minimax,MiniMax-M3[1m]";
      emitRouteChange(route, `escalated: ${tokenCount} tokens > ${effectiveCtx} local ctx (aggressive)`);
      return route;
    }

    // Conservative mode: M3-first, local only for very small tasks
    if (taskType === "trivial-coding" && tokenCount <= effectiveCtx) {
      const route = `llama-cpp,${localModel.id}`;
      emitRouteChange(route, `conservative-local (${taskType}, ${tokenCount} tokens <= ${effectiveCtx})`);
      return route;
    }

    // Conservative coding: M3
    const route = "minimax,MiniMax-M3[1m]";
    emitRouteChange(route, `conservative-cloud (${taskType}, ${tokenCount} tokens)`);
    return route;
  }

  // --- No local model available: M3 for coding ---
  const route = "minimax,MiniMax-M3[1m]";
  emitRouteChange(route, `no-local-model (${taskType})`);
  return route;
};

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
