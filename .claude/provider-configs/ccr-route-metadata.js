// ccr-route-metadata.js — canonical route-metadata source consumed by both
// ccr-custom-router.js and ccr-admission-proxy.js.
//
// AUTHORITY: this module IS the single source of truth for context limits.
// Edit it when adding/removing routes or updating verified limits. Do NOT
// maintain duplicate tables in individual consumer files.
const ROUTE_METADATA = Object.freeze([
  { route: 'zai,glm-5.2', limit: 1_000_000, source: 'zai-docs', confidence: 'verified', observedAt: '2026-07-10' },
  { route: 'opencode-go,deepseek-v4-flash', limit: 1_000_000, source: 'deepseek-specs', confidence: 'verified', observedAt: '2026-07-10' },
  { route: 'opencode-go,mimo-v2.5', limit: 1_000_000, source: 'opencode-go-specs', confidence: 'verified', observedAt: '2026-07-10' },
  { route: 'minimax,MiniMax-M3[1m]', limit: 1_000_000, source: 'minimax-docs-[1m]', confidence: 'verified', observedAt: '2026-07-10' },
  { route: 'nvidia-free,nvidia/nemotron-3-ultra-550b-a55b', limit: 1_000_000, source: 'nvidia-ultra-technical-report', confidence: 'verified', observedAt: '2026-07-15' },
  { route: 'nvidia-free,nvidia/nemotron-3-super-120b-a12b', limit: 1_000_000, source: 'nvidia-super-technical-report', confidence: 'verified', observedAt: '2026-07-15' },
  { route: 'opencode-zen-free,opencode/minimax-m3-free', limit: 1_000_000, source: 'opencode-zen-free-tier', confidence: 'verified', observedAt: '2026-07-10' },
]);
const ROUTES_HANDLED_OUTSIDE_CLOUD_PROXY = Object.freeze(new Set(['llama-cpp,ornith-1.0-9b']));
const GLOBAL_CONTEXT_LIMIT = Math.min(...ROUTE_METADATA.map(r => r.limit));
const OUTPUT_RESERVE = 16_384;
const CONTEXT_LIMITS = Object.fromEntries(ROUTE_METADATA.map(r => [r.route, r.limit]));
const ROUTE_INDEX = Object.fromEntries(ROUTE_METADATA.map(r => [r.route, r]));
const CHAR_PER_TOKEN = 3;
function getContextLimit(route) { const m = ROUTE_INDEX[route]; return m ? m.limit : GLOBAL_CONTEXT_LIMIT; }
function getMinimumLimit() { return GLOBAL_CONTEXT_LIMIT; }
function getRouteMetadata(route) { return ROUTE_INDEX[route] || null; }
function getAllRoutes() { return ROUTE_METADATA; }
function getProvenance(route) { const m = ROUTE_INDEX[route]; return m ? m.confidence : 'unknown'; }
function isProvisional(route) { return getProvenance(route) === 'provisional'; }
module.exports = {
  ROUTE_METADATA, CONTEXT_LIMITS, ROUTES_HANDLED_OUTSIDE_CLOUD_PROXY,
  GLOBAL_CONTEXT_LIMIT, OUTPUT_RESERVE, CHAR_PER_TOKEN,
  getContextLimit, getMinimumLimit, getRouteMetadata, getAllRoutes,
  getProvenance, isProvisional,
};
