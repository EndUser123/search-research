---
title: "Testing plan: resolve K3 and Ultra spawn_subagent failures"
created: 2026-07-26
source: session-2026-07-26 (direct API tests proved both models work; failure is in Grok Build dispatch)
tags: [testing-plan, spawn-subagent, serde-error, kimi-k3, nemotron-ultra, grok-build-bug, root-cause-investigation]
agent: grok
host: grok
cognitive_load: 3
verification: local-only
summary: >
  Both K3 and Ultra return valid responses via direct API (with `id` fields
  and `reasoning_content`). Both fail via Grok Build's spawn_subagent dispatch.
  The failure is in the deserializer, not the models or providers. This plan
  isolates the root cause through 7 tests across 3 dispatch paths, then
  determines whether the fix is upstream (Grok Build patch) or local (config
  workaround). The leading hypothesis: Grok Build's serde can't handle the
  `reasoning_content` field that both models return.
relations:
  - target: wiki/concepts/model-tool-calling-capability-matrix
    type: refines
  - target: wiki/concepts/model-fleet-provider-pools
    type: related
---

# Testing plan: resolve K3 and Ultra spawn_subagent failures

## Decision context

**Why this plan exists:** for three sessions we documented these models as "broken" and worked around them. Direct API tests this session proved both return valid responses. The failure is in Grok Build's spawn_subagent deserializer. We need to isolate the exact trigger and determine the fix path.

**What we already know (verified this session):**
- K3 direct API: ✅ 200 OK, `id` present (`chatcmpl-6a65990accb8fb5670505e54`), returns `reasoning_content`
- Ultra direct API at 6.6k chars: ✅ 200 OK, `id` present, returns `content` + `reasoning_content`
- K3 spawn_subagent: ❌ `missing field 'id'` (148s) — but the `id` IS in the response
- Ultra spawn_subagent at 98k tokens: ❌ `null, expected u32` (47s)

**Leading hypothesis:** Grok Build's serde deserializer doesn't handle the `reasoning_content` field. Both K3 and Ultra return it. The deserializer encounters it, fails to parse (because it expects a specific schema without `reasoning_content`), and produces a misleading error about a different field (`id` or `u32`).

## Phase 0: Discriminate the hypothesis (run FIRST — zero-cost, can kill the hypothesis)

The leading hypothesis is "`reasoning_content` breaks the deserializer." But `go-mimo-v2-5` and `glm-5-2` both work via spawn_subagent. If THEY also return `reasoning_content`, the hypothesis is dead.

### T0: Do known-working models return `reasoning_content`?

| # | Model | Dispatch path | Returns `reasoning_content`? | Works via spawn? | Implication |
|---|---|---|---|---|---|
| T0a | go-mimo-v2-5 | Direct API | ❓ CHECK | ✅ Yes | If yes → `reasoning_content` is NOT the trigger |
| T0b | glm-5-2 | Direct API | ❓ CHECK | ✅ Yes | If yes → `reasoning_content` is NOT the trigger |
| T0c | minimax-m3 | Direct API | ❓ CHECK | ✅ Yes | If yes → `reasoning_content` is NOT the trigger |

**If ALL known-working models also return `reasoning_content`:** the hypothesis is refuted. Pivot to alternative hypotheses:
- H2: The OpenCode Zen proxy (`opencode.ai/zen/go/v1`) strips or transforms fields under certain conditions
- H3: The response size triggers a buffer limit in the deserializer (Ultra at 98k, K3 at any size with thinking tokens inflating the response)
- H4: A specific field VALUE (not field NAME) triggers the parser — e.g., `null` in a nested field

**If known-working models do NOT return `reasoning_content`:** hypothesis survives, proceed to Phase 1.

**Why this matters:** this is a 3-line Python script per model (send a prompt, check response JSON for the key). Total cost: ~30 seconds. It can save hours of investigation by killing the hypothesis immediately.

## Phase 1: Isolate the trigger (per-model — K3 and Ultra may have different root causes)

**Important correction from /tp review:** K3 routes through OpenCode's Zen Go proxy (`opencode.ai/zen/go/v1`). Ultra routes directly to NVIDIA NIM (`integrate.api.nvidia.com/v1`). These are different providers with different response formats and different error messages. They should be investigated as potentially separate problems.

### K3 investigation track

| # | Test | Dispatch | What it proves |
|---|---|---|---|
| T_K3_1 | K3 via OpenCode Zen proxy — direct API (already done) | Direct API | ✅ Works, `id` present, `reasoning_content` present |
| T_K3_2 | K3 via spawn_subagent (already done) | spawn | ❌ Fails: `missing field 'id'` after 148s |
| T_K3_3 | **K3 via Moonshot direct API** (bypass OpenCode proxy) | Direct API | Does Moonshot's own API work? If yes → OpenCode proxy is the problem |
| T_K3_4 | Check whether OpenCode proxy transforms the response differently for Grok Build's User-Agent vs our direct API calls | Direct API | Is the proxy stripping `id` under certain conditions? |

### Ultra investigation track

| # | Test | Dispatch | Prompt size | What it proves |
|---|---|---|---|---|
| T_U_1 | Ultra direct API (already done) | Direct API | ~1.6k tokens | ✅ Works, `id` present |
| T_U_2 | Ultra spawn_subagent small (already done) | spawn | ~200 tokens | ✅ Works (19s) |
| T_U_3 | **Ultra spawn_subagent at 5k tokens** | spawn | ~5k tokens | **Key test**: does Ultra fail at medium scale? |
| T_U_4 | Ultra spawn_subagent at 50k tokens | spawn | ~50k tokens | Narrow the threshold |
| T_U_5 | Ultra direct API at 50k tokens | Direct API | ~50k tokens | Does direct API also fail at scale? (rules out spawn as the cause) |

## Phase 2: Test the workaround (if Phase 1 confirms the trigger)

### T8: K3 with reasoning disabled

If the provider supports disabling reasoning tokens:
```
# Try sending "reasoning_effort": "none" or "thinking": false in the request
spawn_subagent(model="go-kimi-k3", prompt="...", ...)
```
If this works, the workaround is a request parameter. Document in config.toml as a required parameter for K3.

### T9: Ultra with reasoning disabled

Same test for Ultra. NVIDIA NIM may support a parameter to suppress `reasoning_content`.

### T10: Config-based workaround

If the provider doesn't support disabling reasoning, check whether Grok Build's config.toml supports response field filtering (strip `reasoning_content` before parsing). This may require a Grok Build feature request.

## Phase 3: Report upstream (ONLY after root cause is confirmed — not after hypothesis testing)

**Correction from /tp review:** the original plan jumped to filing bug reports after Phase 1+2, but Phase 1 hasn't isolated the root cause yet. Report upstream only after we can say "here is the exact field/response that triggers the deserializer failure" — not "we think it might be `reasoning_content`."

### Bug report (template — fill after Phase 1+2 confirm the root cause)

For each confirmed bug:
- **Model + dispatch path:** e.g., "K3 via OpenCode Zen Go proxy + spawn_subagent"
- **Exact error:** the serde error string
- **Evidence:** direct API returns valid response with `id` field present; spawn_subagent fails to parse
- **Root cause (confirmed):** the specific field or condition that triggers the failure
- **Reproduction:** minimal spawn_subagent call that reproduces the error
- **Proposed fix:** if known (e.g., "handle `reasoning_content` field in deserializer")

## Acceptance criteria

The plan is complete when:
1. T0 discriminates the `reasoning_content` hypothesis (kill or confirm)
2. If confirmed: T_K3/T_U tests isolate the per-model trigger
3. If refuted: alternative hypotheses (H2-H4) are tested
4. Root cause is confirmed with evidence (not just hypothesis)
5. If workaround exists: document in config.toml + tool-fallbacks.md + wiki matrix
6. If no workaround: bug reports filed with confirmed root cause + reproduction
7. Wiki concept `model-tool-calling-capability-matrix.md` updated with root cause (replacing `[UNKNOWN]`)

## Falsifier

This plan is wrong if:
- T0 shows known-working models also return `reasoning_content` → pivot to H2-H4
- The models work via a different dispatch path (PI/OpenCode harness) → the fix is "use a different harness," not "fix Grok Build"
- The issue is in OpenCode's Zen proxy, not Grok Build → report to OpenCode instead
- K3 and Ultra have completely different root causes → split into separate investigations

## Out of scope

- Building a custom proxy to strip fields (premature — confirm root cause first)
- Testing other models with `reasoning_content` (validate the hypothesis first via T0, then expand)
- Performance optimization of K3/Ultra (they work fine via direct API; the issue is dispatch-only)

## What to run first (priority order — revised from /tp review)

1. **T0** (check whether known-working models return `reasoning_content`) — 30 seconds, can kill the hypothesis immediately
2. **T_U_3** (Ultra at 5k tokens via spawn_subagent) — narrows Ultra's scale threshold
3. **T_K3_3** (K3 via Moonshot direct API, bypassing OpenCode proxy) — determines if the proxy is the problem for K3
4. **T8/T9** (disable reasoning via request param) — if hypothesis survives T0, test the workaround
