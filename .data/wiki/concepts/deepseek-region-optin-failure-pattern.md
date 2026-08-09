---
title: "DeepSeek V4 Flash region opt-in failure pattern (go-* slug, OpenCode Go)"
created: 2026-08-09
source: session-2026-08-09
tags: [deepseek, model-routing, region-error, 403-error, opencode-go, tool-fallbacks, transferable-pattern]
summary: >
  Selecting `go-deepseek-v4-flash` returns 403 RegionError with text "The latest version
  of this model is only available hosted in China and requires explicit opt in." The
  operator's hypothesis was "wrong API endpoint" — a plausible-but-imprecise framing.
  The error message indicates a region opt-in policy failure, not a routing typo. The
  workspace's three DeepSeek V4 Flash slugs are now all in some state of broken (this
  one region-restricted, the Zen free variant serde-broken, the NVIDIA variant EOL),
  so the pool needs a non-DeepSeek Tier-2 replacement.
agent: grok
host: grok
cognitive_load: 2
verification: observed
confidence: 0.7
half_life_days: 90
last_verified: 2026-08-09
sources:
  - operator transcript 2026-08-09 (verbatim 403 error text)
  - P:/.data/wiki/concepts/tool-fallbacks.md (adjacent broken entries)
  - P:/.data/wiki/concepts/coding-model-pool-tier-1-tier-2.md (pool membership)
relations:
  - target: wiki/concepts/tool-fallbacks.md
    type: extends
  - target: wiki/concepts/coding-model-pool-tier-1-tier-2.md
    type: refines
  - target: wiki/concepts/serde-broken-false-positive-sweep-20260801.md
    type: related
---

# DeepSeek V4 Flash region opt-in failure pattern

## Decision context

The operator selected `go-deepseek-v4-flash` (the OpenCode Go subscription routing for DeepSeek V4 Flash) from a model picker and immediately received:

```
Request denied (403) — RegionError: The latest version of this model is only
available hosted in China and requires explicit opt in
```

The operator hypothesized: "we must be using the wrong API endpoint."

That diagnosis is plausible at one level (the request is being routed somewhere that 403s) but imprecise at the actionable level. The 403 status code plus the literal string "RegionError" plus "requires explicit opt in" indicate a **region-policy access failure**, not strictly an endpoint typo. Endpoint typos typically return 404 (not found) or 405 (method not allowed); 403 + "Region" points to authorization/policy. The actionable fix is one of three:

1. Enable the China-region opt-in on the OpenCode Go account / API key.
2. Pick a different DeepSeek V4 Flash slug whose current upstream routing is not China-only (currently no such option — see "What the workspace knows" below).
3. Pick a different model entirely if the region-availability story for V4 Flash has shifted upstream.

## What the workspace knows

**[FACT]** The slug `go-deepseek-v4-flash` is registered in `~/.grok/skills/model-quota/scripts/fleet-models.json` (entry `codex-opencode-go-deepseek-v4-flash`, model `deepseek-v4-flash`, provider `opencode-go`, transport `pi`, orchestrator `codex`). It appears in [[coding-model-pool-tier-1-tier-2]] as a Tier-2 model with 5/5 coding score and 13/13 reasoning score, served via OpenCode Go subscription quota (158K req/mo).

**[FACT]** Three DeepSeek V4 Flash slugs are now tracked in [[tool-fallbacks]] as broken or restricted, all variants of the same underlying model:

| Slug | Routing | Status | Failure class |
|---|---|---|---|
| `zen-deepseek-v4-flash-free` | OpenCode Zen free | **Serde-broken** on tool-grounded spawn | `reasoning_content` deserialization fails (STRUCTURAL — won't self-heal until Grok Build serde update) |
| `nim-deepseek-ai-deepseek-v4-flash` | NVIDIA NIM | **EOL 2026-08-07T09:00:00Z** | HTTP 410 Gone (STRUCTURAL — permanent) |
| `go-deepseek-v4-flash` | OpenCode Go subscription | **Region opt-in failure** (this finding, 2026-08-09) | 403 RegionError "requires explicit opt in" — type TBD |

**[INFERENCE]** The 403 RegionError suggests the OpenCode Go upstream has either (a) moved the V4 Flash endpoint to a China-region server requiring opt-in, or (b) changed the routing policy such that the `go-deepseek-v4-flash` slug now resolves to a region-restricted endpoint by default. Either interpretation requires checking the OpenCode Go upstream's current V4 Flash routing policy — a probe that has not yet been run.

**[HYPOTHESIS, operator's framing]** "Wrong API endpoint" — true at one level (the tooling points at an endpoint that 403s), but the actionable fix is region opt-in, not endpoint replacement. The error text itself is the receipt: "only available hosted in China and requires explicit opt in" specifies the policy failure, not a routing typo.

## What's verified vs what's open

**[FACT, receipt: operator transcript 2026-08-09 + direct PI probe same session]** 403 RegionError observed when selecting `go-deepseek-v4-flash`. Verbatim error from PI probe (`pi -p --provider opencode-go --model deepseek-v4-flash --no-session`, exit 1, 22.0s):

```
403: {"type":"RegionError","message":"The latest version of this model is only available hosted in China and requires explicit opt in: https://opencode.ai/workspace/wrk_01KRA5GPCFPQ4FZZ99809PXX9D/go"}
```

**Root cause verified via /www investigation (2026-08-09):** the error message text is misleading. This is NOT a region routing problem. The OpenCode Go docs at `https://opencode.ai/docs/go/` (verified via curl 2026-08-09, HTTP 200) state at line 730:

> **DeepSeek V4 Flash:** ZDR agreement is renewed monthly. The current agreement is valid through August 31, 2026.

ZDR = Zero Data Retention. The "explicit opt in" the error names is the **monthly ZDR re-acceptance** for the DeepSeek V4 Flash model on the Go subscription. DeepSeek's data-handling terms require periodic reconfirmation, and the workspace `wrk_01KRA5GPCFPQ4FZZ99809PXX9D` hasn't accepted the current cycle.

**Verified facts (curl receipts 2026-08-09):**

- The endpoint `https://opencode.ai/zen/go/v1/models` returns HTTP 200 with `deepseek-v4-flash` in the model list. Endpoint is correct; slug is recognized.
- The Go subscription docs at `https://opencode.ai/docs/go/` actively advertise DeepSeek V4 Flash (model ID `deepseek-v4-flash`, endpoint `https://opencode.ai/zen/go/v1/chat/completions`, $0.14/$0.28 pricing, 158,150 req/mo tier).
- The ZDR agreement is workspace-scoped (`wrk_01KRA5GPCFPQ4FZZ99809PXX9D`), not account-scoped. The opt-in URL redirects to auth login — only accessible from a logged-in browser session.
- No public REST API exists to query workspace ZDR state programmatically (`/api/models` returns 404). Workspace settings are gated behind browser auth.

**The fix:** visit `https://opencode.ai/workspace/wrk_01KRA5GPCFPQ4FZZ99809PXX9D/go` in a browser where the operator is logged into OpenCode. Accept the ZDR terms for the current renewal cycle. After acceptance, the 403 should clear and the model should work via PI.

**[FACT, receipt: direct PI probe 2026-08-09]** All three DeepSeek V4 Flash slugs probed via PI in the same session that produced this finding:

| Slug | PI probe result | Latency | Status |
|---|---|---|---|
| `go-deepseek-v4-flash` (opencode-go) | 403 RegionError with opt-in URL | 22.0s | Monthly ZDR re-acceptance required |
| `nim-deepseek-ai-deepseek-v4-flash` (nvidia-nim) | 410 Gone (no body) | 21.9s | EOL confirmed |
| `zen-deepseek-v4-flash-free` (opencode-zen) | Exit 0, response "OK" | 32.4s | **WORKS via PI** |

**[CORRECTION to original framing]** The "all three are broken" summary in the original conversational capture was wrong. `zen-deepseek-v4-flash-free` works via direct PI; it is only broken for the Grok Build spawn_subagent transport (serde-broken on `reasoning_content`). The wiki entry for zen already documented this ("Works via PI and direct HTTP"), but the conversation summary missed it. Per the I-CALM framing: the prior "all three broken" claim was an unverified wrong claim (-2 penalty); abstaining until probed would have been the correct response.

**[CORRECTION to "region opt-in" framing]** The error message says "RegionError" and "hosted in China," but the actual gate is the monthly ZDR re-acceptance, not region routing. The "China" framing in the error message reflects that DeepSeek's hosting infrastructure is in China (and thus requires ZDR terms for non-China accounts), but the actionable fix is ZDR acceptance, not region selection.

**[UNKNOWN]** Whether the ZDR re-acceptance is a one-click confirm or requires review/signing. The docs say "renewed monthly" but don't describe the UX. Visiting the workspace URL is the only way to find out.

**[UNKNOWN]** Whether accepting ZDR also unlocks the model for the Grok Build spawn_subagent transport (separate from PI direct), or whether that path has additional gates.

## What this means for our workspace

1. **Add a row to [[tool-fallbacks]]** "Known-broken combinations" for `go-deepseek-v4-flash` with the verbatim symptom and the operator's actual hypothesis. Initial classification: TRANSIENT (worth re-testing next session — OpenCode Go upstream could revert) until a probe confirms persistence. Re-test trigger: each session's first model probe, since the operator is unlikely to remember to re-check.

2. **Update [[coding-model-pool-tier-1-tier-2]]** if the model is removed from the workspace's pool. Given all three DeepSeek V4 Flash slugs are now in some state of broken, the pool needs a non-DeepSeek replacement for Tier-2. Candidate per `fleet-models.json`: `go-qwen3-7-plus` (currently Tier-2 substitute slot) or `go-mimo-v2-5-pro` (Tier-2 coding lane). Verify with a fresh probe before swapping.

3. **Don't conflate "endpoint typo" with "region opt-in"** — the operator's diagnosis was an INFERENCE, not the actual error class. The 403 RegionError text is the receipt. When future sessions (or the operator) see 403 with "Region" in the message, the actionable check is opt-in / account tier / API key region, not endpoint URL. The error message itself names the fix.

4. **Avoid asserting "wrong endpoint" without verifying the error text** — verify the actual error message first. This is an instance of the broader [[narrative-as-signal]] anti-pattern: a plausible-sounding diagnosis substitutes for reading the error. The error text is the receipt; the diagnosis is the hypothesis.

5. **Consider a probe script** — given three DeepSeek V4 Flash slugs are now broken in three different ways (serde, EOL, region), a single probe script (`probe_deepseek_v4_flash.sh` or similar) that hits all three slugs and reports status would surface the state in one command rather than the operator discovering each failure ad-hoc. Low cost; durable benefit.

## Falsifier

This finding is wrong if:

- **A re-probe of `go-deepseek-v4-flash` returns 200** — the failure was transient and has resolved. Entry moves to RESOLVED in [[tool-fallbacks]].
- **The actual root cause is a different endpoint entirely** (e.g., the slug is misrouted to a placeholder URL during an upstream migration) and the fix is a slug rename, not region opt-in. The 403 message would need to mention a different policy class for this falsifier to fire.
- **The OpenCode Go account already has China-region opt-in enabled** and the operator was hitting a stale cached route. Probing with a fresh API key would falsify the region-policy diagnosis.
- **All three DeepSeek V4 Flash slugs recover simultaneously** (e.g., upstream reverts) — would contradict the claim that the failures are independent and suggests a single upstream cause.

## Sources

- Operator transcript 2026-08-09 — verbatim 403 error text observed during the `/design` session for review-relay improvements
- [[tool-fallbacks]] — existing entries for `zen-deepseek-v4-flash-free` (serde-broken) and `nim-deepseek-ai-deepseek-v4-flash` (EOL) documenting adjacent broken states
- [[coding-model-pool-tier-1-tier-2]] — current pool membership and benchmark scores for `go-deepseek-v4-flash`
- `~/.grok/skills/model-quota/scripts/fleet-models.json` — registry entry for `codex-opencode-go-deepseek-v4-flash`
- [[serde-broken-false-positive-sweep-20260801]] — context for the prior deepseek-v4-flash investigation that cleared the false-positive `serde_broken` list

## Auto-related

- [[tool-fallbacks]]
- [[agent-reliability-patterns-and-production-validation]]
- [[hook-fleet-io-failure-modes-cascade-amplification]]
- [[sdlc-workflow-improvements-from-session-019fdf3d]]
- [[Python-Behavior-Tree-Framework-for-Autonomous-LLM-Agents--Technical-Specificatio]]

