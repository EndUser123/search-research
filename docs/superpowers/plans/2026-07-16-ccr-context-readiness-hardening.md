# CCR Context and Readiness Hardening Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Preserve the best role model for as long as possible without false universal-token rejection, semantic context loss, or false infrastructure readiness.

**Architecture:** Keep the canonical edge proxy on `127.0.0.1:3456` and CCR internal on `127.0.0.1:3457`. The edge proxy authenticates, performs only exact-duplicate compaction, records redacted size telemetry, and exposes separate liveness/readiness contracts. A cheap size estimate is only a prefilter; above the common cloud ceiling the proxy asks CCR's local `count_tokens` endpoint and rejects a confirmed oversize request before routing. CCR remains the sole model-routing authority; provider-error fallback still requires proof of failed-route exclusion and retry semantics.

**Tech Stack:** PowerShell 7/Pester, Node.js CommonJS and `node:test`, CCR 2.x configuration.

**Outcome (2026-07-16):** Tasks 1-4 and the safe portions of Task 6 were
implemented, tested, restarted, and live-verified. The live gate also found and
fixed two state-leak bugs: hints are now deleted when consumed, and an unhinted
request cannot borrow another session's model recommendation. Task 5
is intentionally deferred because CCR 2.0.0 did not prove explicit context-error
classification, failed-route exclusion, and a one-retry cap. No speculative
retry loop was added.

**Follow-up outcome (2026-07-16):** A live failure proved the missing boundary:
the proxy forwarded a request it estimated at 1,569,286 total tokens; CCR counted
1,108,432 input tokens and routed the over-local-context coding request to
DeepSeek Flash, which returned a generic upstream 400. Exact-on-threshold edge
admission is now implemented and tested. This does not claim provider-specific
tokenizer equivalence and does not enable CCR's unproven provider fallback loop.

## Global Constraints

- Preserve all unrelated dirty workspace changes.
- Do not stage, commit, push, or edit secrets.
- Do not use the chars-per-token estimate as a cloud authorization gate. CCR's
  local count may enforce only the common configured ceiling; it is not evidence
  that every provider tokenizer has identical counts.
- Ornith is eligible only for affirmatively classified coding or explicit user selection.
- MiniMax M3 uses the user-preferred, proven `MiniMax-M3[1m]` route identifier.
- Run test-first for each behavior slice and restart only exact verified process owners.

---

### Task 1: Make context shaping semantics safe

**Files:**
- Modify: `P:/.claude/provider-configs/ccr-context-shaper.test.js`
- Modify: `P:/.claude/provider-configs/ccr-context-shaper.js`

**Interfaces:**
- `shapeAnthropicRequest(body, options?) -> { body, changed, telemetry }`
- `telemetry.compacted_resources[] -> { resource_hash, retained_tool_use_id, replaced }`

- [ ] Add a failing test where two reads of one path have different content and prove both remain verbatim.
- [ ] Add a failing test where identical repeated results compact only the earlier content.
- [ ] Add a failing test proving telemetry does not contain the path, query, or command.
- [ ] Compare serialized tool-result content before replacement and compact only exact equality.
- [ ] Hash resource identity with SHA-256 and emit only a short hash plus opaque tool-use ID.
- [ ] Run `node --test P:/.claude/provider-configs/ccr-context-shaper.test.js` and expect all tests to pass.

### Task 2: Separate proxy liveness from readiness

**Files:**
- Modify: `P:/.claude/provider-configs/ccr-admission-proxy.integration.test.js`
- Modify: `P:/.claude/provider-configs/ccr-admission-proxy.js`
- Modify: `P:/.claude/provider-configs/cc-ccr.Tests.ps1`
- Modify: `P:/.claude/provider-configs/cc-ccr.ps1`

**Interfaces:**
- `GET /__ccr_admission_health` proves process identity only.
- `GET /__ccr_admission_ready` proves separated credentials and authenticated CCR reachability without inference.

- [ ] Add failing tests for healthy-but-upstream-dead and upstream-auth-rejected states.
- [ ] Implement a bounded readiness probe through CCR using the upstream credential and a non-inference endpoint.
- [ ] Make launcher reuse/start decisions require readiness, not liveness alone.
- [ ] Replace the synthetic missing-key fallback with an explicit fail-closed launcher result.
- [ ] Run Node integration tests and Pester; expect readiness failures to prevent `Available=true`.

### Task 3: Bound proxy lifecycle and make logs usable

**Files:**
- Modify: `P:/.claude/provider-configs/ccr-admission-proxy.integration.test.js`
- Modify: `P:/.claude/provider-configs/ccr-admission-proxy.js`
- Modify: `P:/.claude/provider-configs/cc-ccr.ps1`

**Interfaces:**
- `CCR_PROXY_MAX_BODY_BYTES` defaults to the explicitly documented transport ceiling.
- `CCR_PROXY_UPSTREAM_TIMEOUT_MS` bounds connect/response lifetime.

- [ ] Add failing tests for body overflow, stalled upstream, client abort, and partial upstream failure.
- [ ] Reject transport overflow while reading instead of after buffering the entire body.
- [ ] Propagate client abort to the upstream request and destroy incomplete responses.
- [ ] Set an upstream timeout and return a distinct 504 error before headers are sent.
- [ ] Launch Node directly with separate redirected stdout/stderr files instead of a buffering PowerShell pipeline.
- [ ] Run integration tests and verify startup logs are non-empty while the process is alive.

### Task 4: Restore the explicit routing contract

**Files:**
- Modify: `P:/.claude/provider-configs/ccr-custom-router.test.js`
- Modify: `P:/.claude/provider-configs/ccr-custom-router.js`
- Modify: `P:/.claude/provider-configs/ccr-route-metadata.js`
- Modify: `C:/Users/brsth/.claude-code-router/config.json`

**Interfaces:**
- Unknown/unclassified work routes to the role-appropriate cloud default.
- Ornith routes only for `coding`, `trivial-coding`, `local-coding`, or explicit `claude-local-ornith`.
- Canonical M3 route is `minimax,MiniMax-M3[1m]`.

- [ ] Add failing tests proving prose/unknown work does not reach Ornith.
- [ ] Add failing tests proving affirmative coding still reaches idle Ornith.
- [ ] Change the fallback classifier default from `coding` to `general` and route general work to M3.
- [ ] Remove Ornith from `fallback.background`.
- [x] Keep every active M3 route/model identifier and metadata key on the proven `[1m]` form.
- [ ] Parse config JSON and run all router tests.

### Task 5: Prove the context-error fallback boundary

**Files:**
- Inspect: installed CCR distribution under `C:/Users/brsth/AppData/Roaming/npm/node_modules/@musistudio/claude-code-router/dist/`
- Modify only if proven: `C:/Users/brsth/.claude-code-router/config.json`

**Interfaces:**
- Context fallback occurs only on an explicit pre-generation context rejection.
- The failed route is excluded from the single retry.

- [ ] Trace CCR error classification, fallback selection, and failed-route exclusion in the installed runtime.
- [ ] Add or reuse a fake-provider integration test that returns an explicit context error before generation.
- [ ] If exclusion and one-retry semantics are proven, configure the role-specific long-context fallback order.
- [ ] If either property is unproven, make no retry code/config change and document the boundary as blocked.

### Task 6: Cut over, verify, and update authority documents

**Files:**
- Modify: `P:/.claude/provider-configs/README.md`
- Modify: `P:/docs/ccr-model-routing-optimization-handoff.md`
- Modify: `P:/docs/superpowers/plans/2026-07-12-ccr-task-context-shaper.md`

- [ ] Run all Node and Pester suites, syntax checks, JSON parsing, and `git diff --check`.
- [ ] Verify exact owners of ports 3456 and 3457, then restart only the proxy unless CCR source/config changes require CCR restart.
- [ ] Verify liveness and readiness separately through the live endpoint.
- [ ] Send one bounded real request through canonical port 3456 and inspect correlated proxy/route evidence.
- [ ] Update stale hard-gate and unsafe-supersession documentation.
- [ ] Re-run source-authority discovery and report remaining untested provider behavior.
