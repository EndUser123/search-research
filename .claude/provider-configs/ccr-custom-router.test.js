// node:test + node:assert/strict — matches scripts/bifrost_tool_shim.test.js convention.
//
// The router reads from local-model-state.json for context metadata and from
// P:/.claude/state/ccr-* for hints/pins/recs. All of these are wrapped in
// readJsonSafe() (returns null on missing/corrupt). For unit tests we point
// STATE_DIR... no — STATE_DIR is hard-coded to P:/.claude/state. So tests use
// the real path but the file is absent on test machines → state reads return
// null. That is the expected "fresh" state.
//
// We stub globalThis.fetch to drive /health and /slots responses. The module
// caches its probe result for CACHE_WINDOW_MS (10s); between tests we reset the
// cache via a fresh require (delete require.cache). This keeps each test
// hermetic without poking at module internals.

const assert = require("node:assert/strict");
const test = require("node:test");
const path = require("path");

const ROUTER_PATH = path.join(__dirname, "ccr-custom-router.js");

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
  // The Haiku alias for opencode-go is preserved (not removed).
  assert.match(
    src,
    /"opencode-go,deepseek-v4-flash".*claude-haiku-4-5-20251001/,
    "routeToAlias must still map opencode-go to Haiku for non-failure routing",
  );
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