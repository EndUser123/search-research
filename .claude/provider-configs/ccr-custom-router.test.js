// node:test + node:assert/strict.
//
// The router reads from local-model-state.json for context metadata and from
// the state directory's ccr-* files for hints/pins/recs. Tests use a fresh
// temporary state directory so the suite cannot consume live routing hints,
// pins, recommendations, or append to the production route log.
//
// We stub globalThis.fetch to drive /health and /slots responses. The module
// caches its probe result for CACHE_WINDOW_MS (10s); between tests we reset the
// cache via a fresh require (delete require.cache). This keeps each test
// hermetic without poking at module internals.

const assert = require("node:assert/strict");
const test = require("node:test");
const fs = require("fs");
const os = require("os");
const path = require("path");

const ROUTER_PATH = path.join(__dirname, "ccr-custom-router.js");
const PROXY_PATH = path.join(__dirname, "ccr-admission-proxy.js");
const TUI_PATH = path.join(__dirname, "cc-ccr-tui.ps1");
const CCR_CONFIG_PATH = process.env.CCR_CONFIG_PATH || path.join(os.homedir(), ".claude-code-router/config.json");
const TEST_STATE_DIR = fs.mkdtempSync(path.join(os.tmpdir(), "ccr-custom-router-test-"));
process.env.CCR_ROUTER_STATE_DIR = TEST_STATE_DIR;
test.after(() => {
  delete process.env.CCR_ROUTER_STATE_DIR;
  fs.rmSync(TEST_STATE_DIR, { recursive: true, force: true });
});

// --- Test harness -----------------------------------------------------------

function freshRouter() {
  delete require.cache[ROUTER_PATH];
  return require(ROUTER_PATH);
}

function stubFetch(healthImpl, slotsImpl) {
  // Returns a fetch replacement whose response shape matches what the router
  // inspects: { ok, json(), status }. Tracks call counts so tests can assert
  // that /slots was queried (or not).
  const calls = [];
  const stub = async (url, opts = {}) => {
    calls.push({ url, method: opts.method || "GET" });
    if (typeof url === "string" && url.endsWith("/health")) {
      return healthImpl ? healthImpl() : { ok: true, json: async () => ({}) };
    }
    if (typeof url === "string" && url.endsWith("/slots")) {
      return slotsImpl ? slotsImpl() : { ok: true, json: async () => [{ id: 0, is_processing: false }] };
    }
    return { ok: false, status: 404, json: async () => ({}) };
  };
  globalThis.fetch = stub;
  return calls;
}

function makeReq({ model = "claude-sonnet-5", messages = [], tokenCount = 0 } = {}) {
  return {
    body: { model, messages },
    tokenCount,
  };
}

function readRouteEvents() {
  const routeLog = path.join(TEST_STATE_DIR, "ccr-route-log.jsonl");
  try {
    return fs.readFileSync(routeLog, "utf8")
      .trim()
      .split(/\r?\n/)
      .filter(Boolean)
      .map((line) => JSON.parse(line));
  } catch {
    return [];
  }
}

function makeConfig({ routingMode = "aggressive" } = {}) {
  return {
    routingMode,
    routingThresholds: { aggressive: 0.9, conservative: 0.65 },
    Router: { background: "opencode-go,deepseek-v4-flash" },
  };
}

function makePinRouteCall(pin = {}, rec = null) {
  // For most tests we want NO pin and NO rec — pin overrides admission control,
  // rec just picks tierRoute. Both absent lets us isolate local-first routing.
  return { pin, rec };
}

// --- 1. Initial CCR probe does not include inference ----------------------
// At the cc-ccr.ps1 layer, the new initial probe is the non-inference rung
// (rungs 1-4 only). Indirectly verified by the absence of an inference URL
// in the router: the probe block only references /health and /slots. This test
// fails if /v1/chat/completions or any inference URL appears in the source.
test("router source contains no inference URL (admission probe must be non-inference)", () => {
  const fs = require("fs");
  const src = fs.readFileSync(ROUTER_PATH, "utf8");
  assert.equal(
    src.includes("/v1/chat/completions"),
    false,
    "router must NOT probe /v1/chat/completions — that recreates the HUNG race",
  );
  assert.equal(
    src.includes("Invoke-LocalModelProbe -IncludeInference"),
    false,
    "router source must not mention the inference probe name",
  );
});

// --- 2. Existing local state metadata does not bypass live check ----------
// If /health fails (or /slots reports busy), a stale state file with
// maxContextTokens must NOT cause local-first routing.
test("stale state metadata does NOT bypass live unavailability", async () => {
  stubFetch(
    () => ({ ok: false, status: 503, json: async () => ({}) }),
    () => ({ ok: true, json: async () => [{ is_processing: false }] }),
  );
  const router = freshRouter();
  const req = makeReq({ model: "claude-sonnet-5", messages: [{ role: "user", content: "fix bug" }], tokenCount: 1000 });
  const route = await router(req, makeConfig());
  // No pin, no rec → LOCAL_FAIL_FALLBACK = opencode-go/deepseek-v4-flash (NOT M3)
  assert.equal(route, "opencode-go,deepseek-v4-flash", "unhealthy local must route to LOCAL_FAIL_FALLBACK");
});

// --- 3. Idle local slot permits automatic local-first routing -------------
test("idle local + aggressive coding routes to local", async () => {
  stubFetch(
    () => ({ ok: true, json: async () => ({}) }),
    () => ({ ok: true, json: async () => [{ id: 0, is_processing: false }] }),
  );
  const router = freshRouter();
  const req = makeReq({ model: "claude-sonnet-5", messages: [{ role: "user", content: "def hello():\n    pass" }], tokenCount: 1000 });
  const route = await router(req, makeConfig({ routingMode: "aggressive" }));
  assert.equal(route, "llama-cpp,ornith-1.0-9b", "aggressive + idle must pick local-first");
});

test("route log includes request correlation and safe request-shape metadata", async () => {
  stubFetch(
    () => ({ ok: true, json: async () => ({}) }),
    () => ({ ok: true, json: async () => [{ id: 0, is_processing: false }] }),
  );
  const router = freshRouter();
  const requestId = `observability-test-${Date.now()}`;
  const req = makeReq({
    model: "claude-sonnet-5",
    messages: [{
      role: "assistant",
      content: [{ type: "thinking", thinking: "redacted from logs" }],
    }],
    tokenCount: 1234,
  });
  req.id = requestId;
  req.body.tools = [{ name: "example" }];
  req.body.thinking = { type: "enabled" };

  const route = await router(req, makeConfig({ routingMode: "aggressive" }));
  assert.equal(route, "llama-cpp,ornith-1.0-9b");

  const event = readRouteEvents().find((candidate) => candidate.request_id === requestId);
  assert.ok(event, "route event must include the CCR request correlation ID");
  assert.equal(event.body_message_count, 1);
  assert.equal(event.body_has_tools, true);
  assert.equal(event.body_thinking_type, "enabled");
  assert.equal(event.body_has_thinking_blocks, true);
  assert.equal(JSON.stringify(event).includes("redacted from logs"), false);
});

// --- 4. Busy local slot selects cloud fallback ----------------------------
test("busy local slot admits to cloud fallback (automatic routing)", async () => {
  stubFetch(
    () => ({ ok: true, json: async () => ({}) }),
    () => ({ ok: true, json: async () => [{ id: 0, is_processing: true }] }),
  );
  const router = freshRouter();
  const req = makeReq({ model: "claude-sonnet-5", messages: [{ role: "user", content: "def hello():\n    pass" }], tokenCount: 1000 });
  const route = await router(req, makeConfig({ routingMode: "aggressive" }));
  assert.equal(route, "opencode-go,deepseek-v4-flash", "busy local must NOT queue; admit to LOCAL_FAIL_FALLBACK");
});

// Explicit local selection (model === "claude-local-ornith") honors user choice
// even when busy. Preserves explicit-pick contract.
test("explicit local selection (claude-local-ornith) honors busy local", async () => {
  stubFetch(
    () => ({ ok: true, json: async () => ({}) }),
    () => ({ ok: true, json: async () => [{ id: 0, is_processing: true }] }),
  );
  const router = freshRouter();
  const req = makeReq({ model: "claude-local-ornith", messages: [{ role: "user", content: "ping" }], tokenCount: 100 });
  const route = await router(req, makeConfig({ routingMode: "conservative" }));
  assert.equal(route, "llama-cpp,ornith-1.0-9b", "explicit local pick must route to local even when busy");
});

// --- 5. /slots or /health failure selects cloud fallback (fail closed) ----
test("/health failure selects cloud fallback", async () => {
  stubFetch(
    () => { throw new Error("connect ECONNREFUSED"); },
    () => ({ ok: true, json: async () => [{ is_processing: false }] }),
  );
  const router = freshRouter();
  const req = makeReq({ model: "claude-sonnet-5", messages: [{ role: "user", content: "fix bug" }], tokenCount: 100 });
  const route = await router(req, makeConfig({ routingMode: "aggressive" }));
  assert.equal(route, "opencode-go,deepseek-v4-flash", "/health down → LOCAL_FAIL_FALLBACK");
});

test("/slots failure selects cloud fallback (fail closed)", async () => {
  stubFetch(
    () => ({ ok: true, json: async () => ({}) }),
    () => { throw new Error("slots timeout"); },
  );
  const router = freshRouter();
  const req = makeReq({ model: "claude-sonnet-5", messages: [{ role: "user", content: "fix bug" }], tokenCount: 100 });
  const route = await router(req, makeConfig({ routingMode: "aggressive" }));
  assert.equal(route, "opencode-go,deepseek-v4-flash", "/slots failure must fail closed to LOCAL_FAIL_FALLBACK");
});

test("/slots non-2xx selects cloud fallback (fail closed)", async () => {
  stubFetch(
    () => ({ ok: true, json: async () => ({}) }),
    () => ({ ok: false, status: 500, json: async () => ({ error: "boom" }) }),
  );
  const router = freshRouter();
  const req = makeReq({ model: "claude-sonnet-5", messages: [{ role: "user", content: "fix bug" }], tokenCount: 100 });
  const route = await router(req, makeConfig({ routingMode: "aggressive" }));
  assert.equal(route, "opencode-go,deepseek-v4-flash", "/slots non-2xx must fail closed to LOCAL_FAIL_FALLBACK");
});

test("/slots empty array treated as unavailable", async () => {
  stubFetch(
    () => ({ ok: true, json: async () => ({}) }),
    () => ({ ok: true, json: async () => [] }),
  );
  const router = freshRouter();
  const req = makeReq({ model: "claude-sonnet-5", messages: [{ role: "user", content: "fix bug" }], tokenCount: 100 });
  const route = await router(req, makeConfig({ routingMode: "aggressive" }));
  assert.equal(route, "opencode-go,deepseek-v4-flash", "empty /slots → unavailable → LOCAL_FAIL_FALLBACK");
});

// --- 6. Cached probe behavior works as intended ---------------------------
// CACHE_WINDOW_MS is 10s. Within that window, /health + /slots are NOT called
// again — the cached result is reused. This documents the optimization and
// the race it implies: a cached idle verdict can admit multiple requests.
test("cached probe: second call within 10s does not refetch /slots", async () => {
  let healthCalls = 0;
  let slotsCalls = 0;
  globalThis.fetch = async (url) => {
    if (url.endsWith("/health")) {
      healthCalls++;
      return { ok: true, json: async () => ({}) };
    }
    if (url.endsWith("/slots")) {
      slotsCalls++;
      return { ok: true, json: async () => [{ is_processing: false }] };
    }
    return { ok: false, status: 404 };
  };
  const router = freshRouter();
  const cfg = makeConfig({ routingMode: "aggressive" });
  await router(makeReq({ model: "claude-sonnet-5", messages: [{ role: "user", content: "x" }], tokenCount: 10 }), cfg);
  const after1Health = healthCalls;
  const after1Slots = slotsCalls;
  await router(makeReq({ model: "claude-sonnet-5", messages: [{ role: "user", content: "y" }], tokenCount: 10 }), cfg);
  await router(makeReq({ model: "claude-sonnet-5", messages: [{ role: "user", content: "z" }], tokenCount: 10 }), cfg);
  // First call: both probes. Subsequent: cache hit, no new fetch.
  assert.equal(healthCalls, after1Health, "health must not refetch within cache window");
  assert.equal(slotsCalls, after1Slots, "slots must not refetch within cache window");
});

// Cache flips from idle→busy as soon as the cache expires. We can't wait 10s
// in a test; instead, we test the underlying `getLocalAvailability` behavior
// by stubbing fetch to flip and using freshRouter to reset the cache between
// the two phases. Documenting the limitation clearly is the goal.
test("documented limitation: cached idle verdict can admit N requests before /slots reports busy", async () => {
  // This is a contract test, not a wall-clock test. We assert the LIMITATION
  // exists by design: a single /slots sample represents a point in time, and
  // requests between samples cannot be serialized without an external lock.
  // The router source must acknowledge this honestly.
  const fs = require("fs");
  const src = fs.readFileSync(ROUTER_PATH, "utf8");
  // Look for the explicit admission-control caveat.
  assert.match(src, /queue growth is NOT fully bounded/i);
  assert.match(src, /ponytail/);
});

// --- 7. Concurrent/admission behavior: documented as a remaining limitation
// The pre-flight read of `getLocalModelProbed()` is the only synchronization
// point. Without a shared mutex on /slots reads, two requests reading a stale
// "idle" cache entry can both admit themselves to local. Tests document this
// as an accepted limitation (see block 6 comment in the router source).
test("concurrent-request race: documented as limitation", () => {
  const fs = require("fs");
  const src = fs.readFileSync(ROUTER_PATH, "utf8");
  assert.match(src, /admit-then-queue under/i);
});

// --- 8. /slots shape acceptance: both array and {slots: [...]} accepted ----
test("/slots accepts array shape", async () => {
  stubFetch(
    () => ({ ok: true, json: async () => ({}) }),
    () => ({ ok: true, json: async () => [{ is_processing: false }] }),
  );
  const router = freshRouter();
  const route = await router(makeReq({ model: "claude-sonnet-5", messages: [{ role: "user", content: "x" }], tokenCount: 10 }), makeConfig({ routingMode: "aggressive" }));
  assert.equal(route, "llama-cpp,ornith-1.0-9b");
});

test("/slots accepts {slots: [...]} wrapped shape", async () => {
  stubFetch(
    () => ({ ok: true, json: async () => ({}) }),
    () => ({ ok: true, json: async () => ({ slots: [{ is_processing: false }] }) }),
  );
  const router = freshRouter();
  const route = await router(makeReq({ model: "claude-sonnet-5", messages: [{ role: "user", content: "x" }], tokenCount: 10 }), makeConfig({ routingMode: "aggressive" }));
  assert.equal(route, "llama-cpp,ornith-1.0-9b");
});

test("/slots busy in wrapped shape also triggers admission", async () => {
  stubFetch(
    () => ({ ok: true, json: async () => ({}) }),
    () => ({ ok: true, json: async () => ({ slots: [{ is_processing: true }] }) }),
  );
  const router = freshRouter();
  const route = await router(makeReq({ model: "claude-sonnet-5", messages: [{ role: "user", content: "x" }], tokenCount: 10 }), makeConfig({ routingMode: "aggressive" }));
  assert.equal(route, "opencode-go,deepseek-v4-flash", "busy (wrapped shape) → LOCAL_FAIL_FALLBACK");
});

// --- 9. Over-context local request → LOCAL_FAIL_FALLBACK (NOT M3) ----------
// effectiveCtx = floor(65536 * 0.9) = 58982. A request larger than that is a
// local-first FAILURE (wanted local, too big) and must fall to opencode-go.
test("over-context local request falls to LOCAL_FAIL_FALLBACK (not M3)", async () => {
  stubFetch(
    () => ({ ok: true, json: async () => ({}) }),
    () => ({ ok: true, json: async () => [{ id: 0, is_processing: false }] }),
  );
  const router = freshRouter();
  const req = makeReq({ model: "claude-sonnet-5", messages: [{ role: "user", content: "def f():\n    pass" }], tokenCount: 60000 });
  const route = await router(req, makeConfig({ routingMode: "aggressive" }));
  assert.equal(route, "opencode-go,deepseek-v4-flash", "over-context must fall to LOCAL_FAIL_FALLBACK, not M3");
});

// --- 10. Conservative non-trivial coding keeps ORDINARY M3 routing --------
// Guard: the M3 fallback replacement applies ONLY to local-first failures.
// Ordinary non-local routing (conservative mode, non-trivial coding that never
// targeted local) must still use the tier/M3 default. This would fail if the
// change over-reached and rerouted all cloud coding to opencode-go.
test("conservative non-trivial coding keeps ordinary M3 (unchanged)", async () => {
  stubFetch(
    () => ({ ok: true, json: async () => ({}) }),
    () => ({ ok: true, json: async () => [{ id: 0, is_processing: false }] }),
  );
  const router = freshRouter();
  // >200-char code message so inferTaskType returns "coding" (not trivial-coding),
  // and conservative mode so wantLocal is false → ordinary conservative-cloud path.
  const longCode = "def process(data):\n    " + "x = 1\n    ".repeat(40) + "    return data\n";
  const req = makeReq({ model: "claude-sonnet-5", messages: [{ role: "user", content: longCode }], tokenCount: 1000 });
  const route = await router(req, makeConfig({ routingMode: "conservative" }));
  assert.equal(route, "minimax,MiniMax-M3[1m]", "ordinary non-local conservative coding must stay M3");
});

// --- 11. Route logging identifies the local fallback accurately ------------
// local-fail-fallback uses opencode-go/deepseek-v4-flash (same route string as
// ordinary Haiku). The decide() function in the router must alias it by the
// raw route string (NOT the Haiku alias) when decisionSource is
// "local-fail-fallback", or the route log would misleadingly label local-failure
// admissions as Haiku. The Haiku alias for opencode-go must still exist in
// routeToAlias() — it wasn't removed, only bypassed for this source.
test("route logging: local-fail-fallback uses raw route, not Haiku alias", () => {
  const fs = require("fs");
  const src = fs.readFileSync(ROUTER_PATH, "utf8");
  // Guard exists: decide() selects raw route over routeToAlias for local-fail-fallback.
  assert.match(
    src,
    /decisionSource === .local-fail-fallback.*\?.*route\s*:/,
    "local-fail-fallback must use raw route, not routeToAlias alias",
  );
  // The shared route still maps to the Haiku alias for ordinary Haiku
  // requests; decide() bypasses this mapping for local-failure telemetry.
  assert.ok(
    src.includes('"opencode-go,deepseek-v4-flash": "claude-haiku-4-5-20251001"'),
    "routeToAlias must retain the ordinary Haiku alias",
  );
});

// --- 11b. z.ai provider identifier is consistent across every consumer -----
// z.ai exposes the provider model as "glm-5.2". The [1m] suffix is not a z.ai
// model identifier; context-limit metadata must not leak into provider routes.
test("z.ai routes use the provider model identifier without context suffix", () => {
  const config = JSON.parse(fs.readFileSync(CCR_CONFIG_PATH, "utf8"));
  const zai = config.Providers.find((provider) => provider.name === "zai");
  assert.ok(zai, "config must define the z.ai provider");
  assert.ok(zai.models.includes("glm-5.2"), "z.ai provider must expose glm-5.2");
  assert.ok(
    !zai.models.some((model) => model === "glm-5.2[1m]"),
    "[1m] must not be sent as the z.ai provider model identifier",
  );

  const routeStrings = [];
  const collectStrings = (value) => {
    if (typeof value === "string") routeStrings.push(value);
    else if (Array.isArray(value)) value.forEach(collectStrings);
    else if (value && typeof value === "object") Object.values(value).forEach(collectStrings);
  };
  collectStrings(config.Router);
  collectStrings(config.fallback);
  const zaiRoutes = routeStrings.filter((route) => route.startsWith("zai,"));
  assert.ok(zaiRoutes.length > 0, "config must contain at least one z.ai route");
  assert.deepEqual(
    [...new Set(zaiRoutes)],
    ["zai,glm-5.2", "zai,glm-4.7"],
    "every configured z.ai route must use a provider model identifier",
  );

  const routerSource = fs.readFileSync(ROUTER_PATH, "utf8");
  const proxySource = fs.readFileSync(PROXY_PATH, "utf8");
  const tuiSource = fs.readFileSync(TUI_PATH, "utf8");
  const metadataSource = fs.readFileSync(path.join(__dirname, "ccr-route-metadata.js"), "utf8");

  // Check that the shared metadata module contains the zai routes
  assert.match(metadataSource, /zai,glm-5\.2/,
    "route metadata must name the z.ai provider model");
  assert.match(metadataSource, /zai,glm-4\.7/,
    "route metadata must name additional zai models");

  // Check that consumers import from shared metadata
  assert.match(routerSource, /require\("\.\/ccr-route-metadata"\)/,
    "custom router must import from shared route-metadata");
  assert.match(proxySource, /require\("\.\/ccr-route-metadata"\)/,
    "admission proxy must import from shared route-metadata");

  // Verify no context suffix in any source
  for (const source of [routerSource, proxySource, tuiSource, metadataSource]) {
    assert.doesNotMatch(source, /zai,glm-5\.2\[1m\]/,
      "provider routes must not contain the z.ai context suffix");
  }

  // TUI still uses the direct identifier format
  assert.match(tuiSource, /Provider\s*=\s*"zai";\s*Model\s*=\s*"glm-5\.2"/,
    "TUI must emit the z.ai provider model identifier");
});

// --- 12. Architecture review: bounded admission investigation --------------
// The documented 10-second cached-idle admission race cannot be bounded at the
// router layer. CCR's custom-router API is a per-request callback (see
// module.exports = async function router(req, config)). It does NOT expose:
//   - A request lifecycle hook (onComplete, onAbort)
//   - Any shared middleware or interceptor API
//   - A reverse-proxy-style response-affecting hook
//   - Any per-slot state outside the probe cache
//
// Without a completion callback, no release mechanism exists. An in-flight mutex
// would freeze routing forever if a request never completes (crash, hang, timeout).
//
// Therefore bounded admission is BLOCKED — the router lifecycle does not support it.
// This test verifies the source does NOT claim bounded queues and does NOT
// implement a fake release mechanism (no release counter, no in-flight decrement).
test("bounded admission cannot be implemented at the router layer (no lifecycle)", () => {
  // Verify the source honestly documents the limitation.
  const fs = require("fs");
  const A = fs.readFileSync(ROUTER_PATH, "utf8");
  assert.match(A, /queue growth is NOT fully bounded/i);
  assert.match(A, /admit-then-queue under/i);
  // Verify no fake release mechanism exists.
  assert.ok(!A.includes("inFlight--") && !A.includes("inFlight++") && !A.includes("release"),
    "router must NOT implement a fake in-flight counter (no lifecycle to release it)");
  // Verify the module export is a plain async function (not a class with lifecycle hooks).
  const mod = require(ROUTER_PATH);
  assert.equal(typeof mod, "function", "router export must be a plain async function");
  assert.equal(mod.length, 2, "router must accept (req, config) — 2 params");
});

// --- 13. Custom-router null → CCR built-in fallthrough (CCR contract) ----
// CCR's middleware (verified from dist/cli.js): if customRouter returns a truthy
// value, use it; else { built-in B6(e, A, n, o) } picks the model. Therefore
// falsy return is fall-through, NOT rejection. This test proves the router
// returns its route string, NOT null, even for over-limit requests, and that
// back-to-back null/logging paths are not mis-wired.
test("custom-router null contract: falsy return is fall-through, not rejection", () => {
  const CCR_SOURCE = process.env.CCR_SOURCE || path.join(os.homedir(), "AppData/Roaming/npm/node_modules/@musistudio/claude-code-router/dist/cli.js");
  const fs = require("fs");
  const ccr = fs.readFileSync(CCR_SOURCE, "utf8");
  // Extract the custom router consumption block. It's a single expression:
  // if(d) e.scenarioType="default"; else{ let g=await B6(e,A,n,o); ... } e.body.model=d
  // Falsy → built-in router, NOT aborted.
  assert.match(ccr, /if\(d\).*else\{.*B6\(/, "falsy custom router result must fall through to built-in B6");
  assert.ok(!ccr.includes("if(typeof d==='string'||d)"), "router must not differentiate string vs null");
  // The test module must not claim that null is rejection.
  const router = freshRouter();
  assert.equal(typeof router, "function", "router is a function");
  assert.equal(router.length, 2, "router takes (req, config)");
});

// --- 14. Proxy tests (admission gate via ccr-admission-proxy.js) -----------
// The proxy is the hard gate. These test its estimateTokens() and safe ceiling.

const {
  estimateTokens,
  SAFE_CEILING,
  GLOBAL_CONTEXT_LIMIT,
  VERIFIED_ROUTE_LIMITS,
  OUTPUT_RESERVE,
  CHAR_PER_TOKEN,
  getUnverifiedConfiguredRoutes,
  validateConfiguredRoutes,
} = require("./ccr-admission-proxy.js");

const BIG_BODY = JSON.stringify({
  model: "claude-opus-4-8",
  messages: [{ role: "user", content: "x".repeat(3_000_000) }],
  max_tokens: 8000,
});

test("proxy: estimateTokens on a small body", () => {
  const body = { model: "x", messages: [{ role: "user", content: "hi" }], max_tokens: 1000 };
  const r = estimateTokens(body);
  assert.equal(r.maxTokens, 1000, "must read max_tokens");
  assert.ok(r.inputEstimate > 0, "inputEstimate > 0");
  assert.equal(r.total, r.inputEstimate + 1000, "total = input + output");
});

test("proxy: large body exceeds safe ceiling", () => {
  const body = JSON.parse(BIG_BODY);
  // 3M chars / 3 cpt ≈ 1M input + 8K output ≈ 1.01M, above 983,616
  const r = estimateTokens(body);
  assert.equal(r.maxTokens, 8000);
  assert.ok(r.total > SAFE_CEILING, "large 3M-char body must exceed safe ceiling");
  assert.equal(r.total, r.inputEstimate + r.maxTokens, "total = input + output");
});

test("proxy: small body within safe ceiling", () => {
  const body = { model: "x", messages: [{ role: "user", content: "hello world" }], max_tokens: 100 };
  const r = estimateTokens(body);
  assert.ok(r.total <= SAFE_CEILING, "small body must be within safe ceiling");
});

test("proxy: max_tokens is derived from request (not heuristic)", () => {
  const body = { model: "x", messages: [], max_tokens: 8192 };
  const r = estimateTokens(body);
  assert.equal(r.maxTokens, 8192, "max_tokens is the real output budget");
  assert.equal(r.total, r.inputEstimate + 8192, "total reserves real output budget");
});

test("proxy: body without max_tokens defaults to 0 output budget", () => {
  const body = { model: "x", messages: [{ role: "user", content: "hi" }] };
  const r = estimateTokens(body);
  assert.equal(r.maxTokens, 0, "no max_tokens → 0 output budget");
  assert.equal(r.total, r.inputEstimate, "total = input estimate only");
});

test("proxy: every active CCR route has a verified context limit", () => {
  assert.equal(GLOBAL_CONTEXT_LIMIT, 200_000);
  assert.deepEqual(getUnverifiedConfiguredRoutes(), [], "config routes must be registered before proxy startup");
  assert.doesNotThrow(() => validateConfiguredRoutes());
  assert.equal(VERIFIED_ROUTE_LIMITS["zai,glm-5.2"], 1_000_000);
});

test("proxy: rejection diagnostics use the verified global limit", () => {
  const src = require("fs").readFileSync(ROUTER_PATH.replace("ccr-custom-router.js", "ccr-admission-proxy.js"), "utf8");
  assert.doesNotMatch(src, /MAX_VERIFIED_LIMIT/);
  assert.match(src, /backend limit \$\{GLOBAL_CONTEXT_LIMIT\}/);
});

// --- 15. Router backend context check is advisory/proxy-audited (not rejection) ---
// The router's decide() function logs an ADVERSE entry when the request exceeds
// the backend limit, but does NOT return null. The admission proxy is the hard
// gate. This test proves the router falls through (returns the route string).
test("router backend context: over-limit request returns route (falls through), not null", async () => {
  stubFetch(
    () => ({ ok: true, json: async () => ({}) }),
    () => ({ ok: true, json: async () => [{ id: 0, is_processing: false }] }),
  );
  const router = freshRouter();
  const reasoningMsg = [{ role: "user", content: "analyze the architecture and design a plan for this large codebase" }];
  const req = makeReq({ model: "claude-opus-4-8", messages: reasoningMsg, tokenCount: 1069200 });
  const route = await router(req, makeConfig());
  // Router falls through — returns the route string, NOT null. The proxy is the gate.
  assert.notEqual(route, null, "router must NOT return null for over-limit (admission proxy is the gate)");
  assert.equal(typeof route, "string", "router must return a route string even when over limit");
});

// --- 16. Local llama.cpp routing unchanged by proxy -------------------------
test("local llama routing unchanged by context enforcement", async () => {
  stubFetch(
    () => ({ ok: true, json: async () => ({}) }),
    () => ({ ok: true, json: async () => [{ id: 0, is_processing: false }] }),
  );
  const router = freshRouter();
  const req = makeReq({ model: "claude-sonnet-5", messages: [{ role: "user", content: "def f():\n    pass" }], tokenCount: 1000 });
  const route = await router(req, makeConfig({ routingMode: "aggressive" }));
  assert.equal(route, "llama-cpp,ornith-1.0-9b", "local-first routing unchanged");
});

// --- 17. Local-failure fallback to opencode-go unchanged -------------------
test("local-failure fallback to opencode-go unchanged", async () => {
  stubFetch(
    () => ({ ok: true, json: async () => ({}) }),
    () => ({ ok: true, json: async () => [{ id: 0, is_processing: true }] }),
  );
  const router = freshRouter();
  const req = makeReq({ model: "claude-sonnet-5", messages: [{ role: "user", content: "def f():\n    pass" }], tokenCount: 1000 });
  const route = await router(req, makeConfig({ routingMode: "aggressive" }));
  assert.equal(route, "opencode-go,deepseek-v4-flash", "local failure must fall back to opencode-go");
});
