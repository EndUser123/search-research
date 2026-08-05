---
title: "Dedicated-quota-first dispatch routing for fleet models"
created: 2026-08-04
source: session-20260804
tags: [fleet, dispatch, quota, routing, architecture]
summary: >
  Fleet models with dedicated API keys (Cohere, Z.ai, MiniMax, NIM, Groq, Google,
  Mistral) should be dispatched through their dedicated provider first, falling
  back to shared/subscription pools (OpenCode Zen/Go, OpenRouter) only when
  dedicated quota is exhausted. This preserves shared pools for models that have
  no dedicated option and avoids burning paid credits on models available free
  via dedicated keys. Implemented as dispatch_paths list in fleet-models.json.
agent: grok
host: grok
cognitive_load: 2
verification: observed
relations:
  - target: wiki/concepts/model-pool-selection-policy-speed-quota-diversity.md
    type: refines
  - target: wiki/concepts/model-fleet-provider-pools.md
    type: extends
---

# Dedicated-quota-first dispatch routing

## Decision context

The fleet has models accessible through multiple providers — a dedicated API key
with its own quota pool, and shared subscription pools (OpenCode Go/Zen) or
pay-per-token services (OpenRouter). Without a priority rule, `pick_model.py`
recommended whichever provider appeared first in the registry, sometimes burning
OpenRouter paid credits for models available free via a dedicated key.

The decision: what order should dispatch paths be tried for each model?

## Selection criterion

**Quota independence first, cost second.** Dedicated keys have their own
rate-limit buckets that reset independently per provider. Using them first
means shared pools stay available for models that have no dedicated option.

## The routing rule

```
Dedicated providers (cohere, minimax, zai, nvidia-nim, groq, google, mistral):
  dispatch_paths = ["PI", "HTTP", "OC", "spawn"]

Shared/subscription (opencode-zen):
  dispatch_paths = ["spawn", "PI", "HTTP"]

Paid (openrouter):
  dispatch_paths = ["spawn", "PI", "HTTP"]
```

Dedicated providers lead with PI (lowest overhead, dedicated quota). Subscription
and paid providers lead with spawn (Grok's native dispatch, which works reliably
for these providers without needing PI/OC registration).

## Steelman: why not just use spawn for everything?

Spawn is the simplest dispatch path — no PI/OpenCode config needed, no API keys
to manage. It's the only path that supports tools (function calling). For models
that work reliably via spawn and don't have latency issues, spawn-first is correct.

The dedicated-first rule only applies when a model has a dedicated key AND spawn
has known issues (e.g., Cohere NMC spawn is 3-10x slower than PI). For models
that spawn handles well (most Zen/OpenRouter models), spawn-first remains correct.

## What this means for our workspace

`fleet-models.json` now has `dispatch_paths` lists per model entry. `pick_model.py`
returns the full chain. Callers iterate the list on failure — try `dispatch_paths[0]`,
on failure try `[1]`, etc.

The benchmark measures all paths; the routing rule decides priority. Both are
needed: the routing rule is a decision, not a measurement.

See [[model-pool-selection-policy-speed-quota-diversity]] for the broader
pool selection framework. See [[model-fleet-provider-pools]] for the fleet
inventory and provider definitions. See [[subprocess-run-timeout-deadlock-windows]]
for the subprocess fix that made reliable benchmarking possible.

## Transport-specific failures: metadata, not pool exclusion (2026-08-05)

A model can fail on one transport but work perfectly on others. The
`tool_grounded_spawn_broken` list in fleet-models.json tracks models that
pass trivial probes but fail on real tool-grounded spawn_subagent prompts
(serde error: `null, expected u32`). These same models work via PI, OpenCode,
and HTTP.

**Design principle:** transport-specific failure data should be **routing
metadata** (tells callers "skip spawn, try PI first"), not a **pool-exclusion
filter** (blocks the model entirely). The `dispatch_paths` chain already
exists for exactly this purpose. Blocking a model from pick_model entirely
when it works on 3 of 4 transports unnecessarily shrinks the pool.

The `spawn_limitation` field in pick_model output surfaces this to callers:
when set, the caller knows to skip `spawn` and start with the next
dispatch_path. This keeps all models available while routing around the
broken transport.

**Anti-pattern that prompted this:** adding a model to a "broken" list that
causes `is_available()` to return False, removing it from all lanes. The
operator caught this: "but we have PI, so why limit ourselves to spawn?"
The fix is to downgrade the hard exclusion to soft preference (rank
spawn-broken models lower when alternatives exist) or simply surface the
limitation as metadata for the caller.

**Generalization:** any per-transport failure classification (serde broken,
timeout-prone, rate-limited) should flow through `dispatch_paths` ordering
and `spawn_limitation` metadata — not through pool exclusion. Pool exclusion
is reserved for models that fail on ALL transports (genuinely broken).

## Falsifier

If a dedicated provider consistently has higher latency than the subscription
path for the same model, the dedicated-first rule should be relaxed to prefer
the faster path when the latency difference exceeds a threshold. Measure by
comparing `dispatch_latency[PI]` vs `dispatch_latency[spawn]` per model — if
dedicated PI is >2x slower than spawn, swap the order.

## Auto-related

- [[skill-graph]]
- [[model-quota-contention-coordination-fleet-rate-limiting]]
- [[model-pool-selection-policy-speed-quota-diversity]]
- [[model-fleet-provider-pools]]
- [[cohere-api-integration-rate-limit-tracking]]

