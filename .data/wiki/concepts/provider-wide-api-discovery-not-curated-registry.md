---
title: "Provider-wide API discovery — query /v1/models instead of testing only curated registry entries"
created: 2026-08-11
source: session-019fdf47
tags: [model-discovery, provider-api, pool-test, registry, root-cause, testing-methodology]
summary: >
  The root cause of under-testing fleet models was treating the curated
  registry (fleet-models.json) as the universe of testable models, when each
  provider's /v1/models API exposes many more. NVIDIA has 101 models on API;
  the registry had 6. OpenRouter has 400; the registry had 2. The fix:
  --provider discovery mode queries the API, filters to chat models, and
  tests ALL of them.
agent: grok
host: grok
cognitive_load: 1
verification: observed
---

# Provider-wide API discovery

## Decision context

The fleet had 6 NVIDIA models in the registry and tested only those 6. When the operator asked "why only 6?", the answer was "that's what's in config.toml." But NVIDIA's API has 101 models. The operator's correction: "you have 80 models on their API and you're proposing 24. Why?"

The root cause: **treating the internal registry as the universe instead of the provider's API.** The registry is a curated subset. The API is the actual available surface.

## The pattern

```
WRONG:  for model in registry: test(model)           # tests only what you already know about
RIGHT:  models = GET /v1/models → test(each)          # tests everything available
```

The `--provider` mode in `pool_test.py` implements the right pattern:
1. Query `{base_url}/models` endpoint
2. Filter to chat models (exclude embeddings, audio, vision-only)
3. Probe each with a 5-token reachability check
4. Test all alive models

The `--free-only` flag further filters by API pricing field (`prompt == "0" && completion == "0"`), not by the `:free` label suffix — stealth and unlabeled $0 models are included.

## Empirical results

| Provider | In registry | On API | Chat models | Alive | Tested |
|----------|------------|--------|-------------|-------|--------|
| NVIDIA | 6 | 101 | 71 | 24 | 24 (all 3 capabilities) |
| ZAI | 1 | 8 | 8 | 8 | 8 (all 3 capabilities) |
| OpenRouter | 2 | 400 | 397 | 246 (318 probed) | 12 free-tier |
| Cohere | 3 | 31 | 17 | 0 (0% quota) | blocked |
| MiniMax | 1 | 8 | 8 | 8 | previously tested |

## What this means for our workspace

**Always discover from the API, not from the registry.** The registry is a routing tool (which models to pick), not a testing scope (which models to certify). New models appear on provider APIs without registry updates — the discovery mode catches them.

The discovery pipeline now feeds:
1. `pool_test.py --provider` → capability testing
2. `concurrency_probe.py --provider` → concurrency limits
3. `promote_models.py` → auto-promotion from evidence

When a provider adds new models, re-running `--provider` discovery automatically finds and tests them without registry changes.

## Falsifier

This approach is wrong if:
- Provider `/v1/models` endpoints are unreliable or return stale data. **Not observed** — all 4 providers returned accurate, current model lists.
- Testing all models wastes time on irrelevant ones (embeddings, audio). **Mitigated** by the `_NON_CHAT_PATTERNS` filter and the quick probe (5-token reachability check before full testing).
- The API model list diverges from what's actually dispatchable (model listed but 404 on call). **Observed for 2 models** (or-ling-3-flash-free, zen-deepseek-v4-flash-free) — the probe catches these.

## Receipts

- Discovery function: `pool_test.py:discover_provider_models()` (line 159)
- Free-tier filter: `pool_test.py` `--free-only` flag (pricing-based, commit `dd2ed37`)
- Operator correction: "you have 80 models on their API and you're proposing 24. Why?"
- Operator correction: "that's too broad" (on blanket exclusions — exclusions depend on provider)

Related: [[concurrency-discovery-proactive-provider-ceiling-mapping]], [[tool-evidence-gap-http-vs-agent-harness]], [[model-pool-selection-policy-speed-quota-diversity]], [[diagnostic-logging-by-default-in-fleet-tooling]]

## Auto-related

- [[skill-graph]]
- [[I'm-going-to-create-a-hook-to-enforce-discovery-be]]
- [[skill-catalog]]
- [[model-fleet-provider-pools]]
- [[pydantic-models-and-serialization]]

