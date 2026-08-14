---
title: "Z.ai GLM Coding Plan: rate limits, credit metering, and model cards (2026-08)"
id: zai-glm-coding-plan-rate-limits-and-model-cards
created: 2026-08-14
updated: 2026-08-14
verified_against:
  - https://docs.z.ai/devpack/usage-policy (fetched 2026-08-14)
  - https://docs.z.ai/devpack/overview (fetched 2026-08-14)
  - https://docs.z.ai/devpack/faq (fetched 2026-08-14)
  - https://docs.z.ai/guides/overview/concept-param (fetched 2026-08-14)
  - https://docs.z.ai/guides/llm/glm-5.2 (fetched 2026-08-14)
  - https://docs.z.ai/guides/llm/glm-5.3 (fetched 2026-08-14)
verification: primary-source (official docs read this session)
falsifier: docs.z.ai pages above changing, or a 413/TPM-style rejection appearing in telemetry for z.ai calls
---

# Z.ai GLM Coding Plan — rate limits, credit metering, model cards

## Why this research was needed

The fleet runs 9 GLM models against `api.z.ai/api/coding/paas/v4` (the GLM
Coding Plan endpoint). Two questions were open:

1. **Token-budget policy:** does setting a high `max_completion_tokens`
   consume quota or get requests rejected (like Groq's TPM wall)?
   Previously labeled [INFERENCE] from absence of token-limit failures
   across 854 telemetry calls.
2. **Model cards:** are the configured slugs current, and what are the
   official context/output limits?

## Finding 1: metering is credits from ACTUAL tokens — no reserved-budget wall

[FACT] (source: devpack/overview, "Credit Calculation") Credit usage =
`(Input tokens × Input multiplier + Cached Input tokens × Cached multiplier +
Output tokens × Output multiplier) / 10,000`.

**Implication:** `max_completion_tokens` does NOT pre-consume credits and no
request-size wall exists for the coding plan. Credits are charged on tokens
actually used. This upgrades the prior [INFERENCE] ("ZAI limits
requests/actual tokens, not reserved output") to primary-source-verified for
the Coding Plan endpoint.

**BUT — output budget still matters for GLM, differently:** GLM reasoning
(chain-of-thought) tokens are output tokens (multiplier 24 for GLM-5.3).
`reasoning_effort` defaults to `max` on GLM-5.2+ (concept-param). So the
*reasoning setting* burns credits; the *cap* is free. A generous cap only
matters for (a) truncation detection (`finish_reason=length`) and (b) staying
under the context window.

## Finding 2: rate limits = concurrency + 5h/weekly credits, tier-based

[FACT] (source: devpack/usage-policy + overview):

| Limit | Value |
|---|---|
| RPM/TPM numeric cap | **None published.** Rate limits are **concurrency** limits, tier-based, dynamically adjusted (Max > Pro > Lite), higher off-peak |
| Recommended concurrent projects | Lite: 1 · Pro: 1–2 · Max: 2+ |
| 5-hour credits | Lite 2,000 · Pro 12,000 · Max 28,000 (reset 5h after consumption) |
| Weekly credits | Lite 10,000 · Pro 60,000 · Max 140,000 (7-day cycle) |
| Off-peak discount | 50% of standard credit rate; peak = Mon–Fri 14:00–18:00 UTC+8 (Singapore) |

Credit multipliers (per model):

| Product | Input | Cached input | Output |
|---|---|---|---|
| GLM-5.3 | 6.9 | 1.7 | 24 |
| GLM-5-Turbo | 5.7 | 1.5 | 21 |
| GLM-4.7 | 4.6 | 1.2 | 16 |
| GLM-4.6V (Vision MCP) | 1.2 | 0.3 | 2.7 |

Estimated weekly token allowance at 90.9% cache hit (official): Lite 43–87M,
Pro 263–526M, Max 613–1226M.

**This explains our telemetry:** the `429 code 1302 "Rate limit reached for
requests"` failures are the concurrency limiter (2 observed); `429 code 1311
"plan does not yet include access"` are model-support failures (34 observed,
2026-08-11); zero token-limit failures across 854 calls is exactly what
credit metering predicts.

[PRACTITIONER, single-source] GitHub anomalyco/opencode#8618: Pro subscriber
reports effective concurrency ~1 ("Too much concurrency" errors, ~4% of 5h
quota usable). Reddit r/ZaiGLM: GLM-4.7 heavy rate-limiting complaints on Max
plan. Directionally consistent with tight dynamic concurrency.

## Finding 3: the Coding Plan supports only THREE models

[FACT] (source: devpack/overview + faq): All plans support **GLM-5.3,
GLM-5-Turbo, GLM-4.7**. Requests for GLM-5.2/GLM-5.1 are **auto-routed to
GLM-5.3**. Older models are not listed as supported.

**Workspace impact:** of our 9 configured GLM entries
(glm-4-5, glm-4-5-air, glm-4-6, glm-4-7, glm-5, glm-5-1, glm-5-2, glm-5-3,
glm-5-turbo), only glm-4-7, glm-5-3, glm-5-turbo are plan-supported.
glm-5-1/glm-5-2 silently route to GLM-5.3 (label drift: telemetry records
the requested slug, not the serving model). The remaining five (4.5, 4.5-air,
4.6, 5, and pre-routing 5.2) fail with 1311.

[UNRESOLVED] Our 2026-08-11 telemetry shows 1311 on z.ai calls; docs say
5.2/5.1 auto-route. Either the 1311s were for non-routed models (4.5/4.6/5)
or the routing postdates that date. Check `model` column on those rows to
resolve.

## Finding 4: official model cards

[FACT] (source: concept-param table + model card pages):

| Model | Context | Default max_tokens | Max max_tokens | Card notes |
|---|---|---|---|---|
| glm-5.3 | 1M | 65536 | 131072 | Coding-plan only (API "coming soon"); same base as 5.2, post-trained; +50% coding vs 5.2 |
| glm-5.2 | 1M | 65536 | 131072 | |
| glm-5.1 | — | 65536 | 131072 | |
| glm-5-turbo | — | 65536 | 131072 | plan-supported |
| glm-5 | — | 65536 | 131072 | |
| glm-4.7 | — | 65536 | 131072 | plan-supported; forced thinking (thinking.type enabled is mandatory) |
| glm-4.6 | 200K (from 128K) | 65536 | 131072 | |
| glm-4.5 / -air / -x / -flash | 128K | 65536 | 98304 | |

Also: `thinking` defaults to enabled on GLM-4.5+ (auto on most; forced on
4.7); `reasoning_effort` values max/xhigh/high/medium/low/minimal/none, default
`max`, GLM-5.2+ only; low/medium map to high, none/minimal skip thinking.
This is the official explanation for the wiki quirk "GLM-5.2 used 1064
reasoning tokens on a trivial prompt" ([[model-benchmark-testing-quirks]]).

Error `1113 Insufficient Balance` on the coding plan = wrong base URL or
unsupported model (FAQ), not actual balance exhaustion.

## Operator tier: Max (recorded 2026-08-14)

[FACT] Operator is on the **Max** plan: 28,000 credits / 5h, 140,000 / weekly.
[FACT] Host timezone: Mountain (UTC-6 DST; receipt: `tzutil /g`, 2026-08-14).
Peak window (Mon–Fri 14:00–18:00 SGT) = **midnight–4:00 AM local** → the
operator's entire working day is **off-peak → 50% credit rate** → effective
quota sits at the top of the official 613–1,226M tokens/week band.

Effective budgets (all-off-peak, GLM-5.3 at 6.9/1.7/24):
- Coding-agent call (50K ctx: 45K cached, 5K fresh, 2K out) = 7.95 credits
  → ~3,500 such calls per 5h window; ~17,600/week.
- Benchmark-style call (~300 in / 400 out) ≈ 0.6 credits → ~47K/5h.
- [FACT] Observed usage: 854 z.ai calls total across 3 weeks of telemetry —
  credits are a non-issue for this fleet; the binding constraints are
  concurrency and policy (below).

[1311 resolved] All 68 `1311` errors in telemetry were `glm-5` (a
non-supported, non-routed model — now removed from config). Both `1302`
concurrency errors were `glm-4.5`/`glm-4.5-air` (also removed). Auto-routing
of 5.2/5.1 is consistent with telemetry (zero 1311s on them). The 2026-08-14
config cleanup therefore eliminates 100% of observed ZAI error classes.

Cost ordering on-plan (per-token credits): GLM-4.7 (4.6/1.2/16) < GLM-5-Turbo
(5.7/1.5/21) < GLM-5.3 (6.9/1.7/24). GLM-4.7 has **forced thinking** (cannot
disable); GLM-5-Turbo supports `thinking: disabled` → cheapest plan-supported
lane for mechanical/high-volume sweeps.

[RISK, Max-specific] Usage policy limits the plan to "officially supported
tools"; violations → rate limiting / account freezing; >3 violations → ban
(usage-policy page). Whether this host's direct-HTTP benchmark scripts and
PI/Grok dispatch count as supported tools is [UNKNOWN] — the supported-tools
list was not fetched. On Max the stakes are account-level, not per-call.



## Recommendations for this workspace

1. **Budget policy (GLM):** set `max_completion_tokens` to 131072 for
   plan-supported models (or omit and rely on provider default 65536 —
   better than our benchmark.py 4096 fallback). No TPM-style wall exists;
   the cap costs nothing until used.
2. **Config cleanup — DONE 2026-08-14:** the 6 non-supported GLM entries
   (4.5, 4.5-air, 4.6, 5, 5.1, 5.2) removed from config.toml. Kept
   glm-5-3, glm-5-turbo, glm-4-7. Legacy refs remain in fleet-models.json
   (owned by fleet-database-migration Phase 3) and ~/.pi/agent/models.json.
3. **Concurrency:** on Max, docs publish no numeric concurrency (tier-based,
   dynamic, higher off-peak; "2+ concurrent projects" recommended).
   Observed: only 2 code-1302 errors ever — both from now-removed models;
   concurrency has never actually bound on this fleet. Keep the
   concurrency-limits.json ZAI ceiling modest (≤4) and watch 1302s in
   telemetry rather than assuming the Pro-tier ~1 horror story applies.
4. **Cost control lever:** for benchmark sweeps where GLM quality floors
   don't matter, `thinking: disabled` or `reasoning_effort: none` cuts
   output-credit burn ~24x on the reasoning share.

## Peak-window picker analysis (2026-08-14)

[FACT] Peak = Mon–Fri 14:00–18:00 SGT (devpack/overview) = **Mon–Fri
midnight–4:00 AM Mountain** (host tz receipt: `tzutil /g`). Measured
exposure: 10 of 1,068 z.ai/GLM calls (0.9%) fell in the peak window, and
all 10 were failures (the glm-5 1311 batch) — **0 output tokens ever
billed at peak rate**. Credits non-binding at Max even at 2×.

**Picker conclusion:** no time-aware gate justified (grep: no peak/hour
modeling exists in model-quota scripts; adding it for 0.9% exposure is
over-engineering — if ever needed, `threshold_policy` table in the
fleet-database migration is the home). The live concurrency ceiling is 4
(measured by concurrency_probe 2026-08-10, first failure at 5 — the
SKILL.md table's "ZAI: 7" is stale). Strategy inputs:

- Off-peak = raised concurrency → ZAI is MORE available during the
  operator's daytime and all weekends.
- Overnight weekday sessions crossing local midnight–4AM pay 2× credits
  and get tighter concurrency → run ZAI-heavy parallel benchmark waves in
  local daytime or weekends; route overnight waves to other providers.
- Interactive work needs no change at any hour.

## Falsifier

- A 413/TPM-style rejection appearing in telemetry for z.ai calls would
  refute "no reserved-budget wall."
- docs.z.ai devpack pages changing tier tables/model lists.
- A 1311 on glm-5-3/glm-5-turbo/glm-4-7 would refute the supported-model
  list as applied to our account tier.

## Related

- [[model-benchmark-testing-quirks]] — GLM reasoning-token verbosity (now
  explained by default reasoning_effort=max)
- [[groq-free-tier-tpm-limit-6000]] — the contrasting provider where the
  budget wall IS real
- [[tool-fallbacks]] — ZAI provider quirks
- [[model-pool-selection-policy-speed-quota-diversity]] — token verbosity
  note for GLM-5.2
