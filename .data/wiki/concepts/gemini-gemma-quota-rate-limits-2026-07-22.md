---
title: "Gemini + Gemma quota and rate limits (verified 2026-07-22)"
created: 2026-07-22
source: session-2026-07-22
tags: [gemini, gemma, quota, rate-limits, pricing, free-tier, paid-tier, agy, direct-api, nvidia, verified]
summary: >
  Official Google docs (scraped 2026-07-22) confirm: Gemini Flash and Flash-Lite
  models are FREE on the Free Tier (free input + output tokens). Pro models have
  free tier input/output but much lower RPD. Rate limits are per-project (not per-key),
  measured in RPM, TPM, and RPD. Free tier RPD resets at midnight Pacific. The
  specific RPM/RPD/TPM numbers are visible in AI Studio but not published on the
  public docs page — they require checking your project's dashboard. Practitioner
  sources report ~15 RPM / 1,500 RPD for Flash-Lite on free tier. agy (Antigravity CLI)
  uses Google AI Pro/Ultra subscription quota — a completely separate pool from the
  direct API key.
agent: grok
host: both
cognitive_load: 2
verification: superseded-by-dashboard-data
relations:
  - target: wiki/concepts/dgemma-gemini-flash-operational-tests-2026-07-22
    type: grounds
  - target: wiki/concepts/model-fleet-provider-pools
    type: grounds
  - target: wiki/concepts/gemini-google-api-models-2026-07
    type: extends
---

> **SUPERSEDED:** This concept used practitioner-estimated rate limits (~1,500 RPD for Flash-Lite). Actual limits verified from operator AI Studio dashboard are lower (500 RPD). See [[gemini-billing-tiers-actual-rate-limits-2026-07-22]] for verified data.

# Gemini + Gemma quota and rate limits

## What's free vs paid (from Google's official pricing page, scraped 2026-07-22)

**Source:** [ai.google.dev/gemini-api/docs/pricing](https://ai.google.dev/gemini-api/docs/pricing) — last updated 2026-07-21 UTC

### Free Tier (what our GEMINI_API_KEY uses)

| Model | Input | Output | Notes |
|-------|-------|--------|-------|
| **Gemini 3.6 Flash** | **Free** | **Free** | Free tier available |
| **Gemini 3.5 Flash** | **Free** | **Free** | Free tier available |
| **Gemini 3.5 Flash-Lite** | **Free** | **Free** | Free tier available; most cost-efficient GA model |
| **Gemini 3.1 Flash-Lite** | **Free** | **Free** | Free tier available |
| **Gemini 3 Flash Preview** | **Free** | **Free** | Preview model |
| **Gemini 2.5 Flash** | **Free** | **Free** | Free tier available |
| **Gemini 2.5 Flash-Lite** | **Free** | **Free** | Free tier available |
| **Gemini 2.5 Pro** | **Free** | **Free** | Free tier available |
| **Gemini 3.1 Pro Preview** | **Free** | **Free** | Preview model |
| **Gemma 4 (26B/31B)** | **Free** | **Free** | Open model hosted on Gemini API |

**All models we configured have free tier input + output.** The "quota exceeded, limit: 0" errors we hit earlier on Pro models were likely **daily RPD exhaustion** (we'd used that model's daily quota already), not a zero-free-tier policy.

### Free Tier caveat (important)

> "Content used to improve our products: **Yes**" (for Free Tier)

Free tier responses may be used by Google for product improvement. If the operator needs data privacy, upgrade to a paid tier ("Content **not** used to improve our products").

### Paid Tier pricing (for reference)

| Model | Input (per 1M tokens) | Output (per 1M tokens) |
|-------|----------------------|----------------------|
| Gemini 3.6 Flash | $1.50 | $7.50 |
| Gemini 3.5 Flash | $1.50 | $9.00 |
| **Gemini 3.5 Flash-Lite** | **$0.30** | **$2.50** |
| Gemini 3.1 Pro Preview | $2.70 | $13.50 |
| Gemini 2.5 Pro | $1.25-2.50 | $10.00-15.00 |

## Rate limits (how the free tier is throttled)

**Source:** [ai.google.dev/gemini-api/docs/rate-limits](https://ai.google.dev/gemini-api/docs/rate-limits) — last updated 2026-07-21 UTC

### Three dimensions

Rate limits are measured across:
1. **RPM** — Requests Per Minute
2. **TPM** — Tokens Per Minute (input)
3. **RPD** — Requests Per Day (resets at midnight Pacific time)

> "Your usage is evaluated against each limit, and exceeding any of them will trigger a rate limit error."

### Limits are per-project, not per-key

> "Rate limits are applied per project, not per API key."

We have 3 GEMINI_API_KEYs in `.env`. If they belong to the same Google Cloud project, they share one rate limit pool. If they belong to different projects, each has its own limits. **This is unverified for our keys.**

### The specific RPM/RPD/TPM numbers are NOT on the public docs page

Google's rate-limits page says: "View your active rate limits in AI Studio" and links to [aistudio.google.com/rate-limit](https://aistudio.google.com/rate-limit). The actual numbers are project-specific and visible only in the dashboard.

### Practitioner-reported free tier limits (from community sources)

**Source:** tokenmix.ai, yingtu.ai, pecollective.com (2026-07, scored 9-10)

| Model | Free tier RPM | Free tier RPD | Free tier TPM | Source confidence |
|-------|--------------|---------------|---------------|-----------------|
| Gemini 3.1 Flash-Lite | **~15 RPM** | **~1,500 RPD** | **~1M TPM** | `[MEDIUM]` — practitioner reports; Google doesn't publish these publicly |
| Gemini 2.5 Flash | ~10 RPM | ~500 RPD | ~1M TPM | `[MEDIUM]` |
| Gemini 2.5 Flash-Lite | ~15 RPM | ~1,500 RPD | ~1M TPM | `[MEDIUM]` |
| Gemini 2.5 Pro | ~5 RPM | ~50 RPD | ~250K TPM | `[MEDIUM]` — explains why we hit "limit: 0" after a few calls |
| Gemini 3.x Pro Preview | Lower than 2.5 Pro | Lower | Lower | `[INFERENCE]` — preview models are "more restricted" per docs |

**Note:** these are community-reported, not officially published. Google's docs say "Specified rate limits are not guaranteed and actual capacity may vary." The only way to verify our actual limits is to check [AI Studio](https://aistudio.google.com/rate-limit) with the project behind our key.

### What this means for our fleet usage

At ~170 calls/hour across 5 terminals:
- **15 RPM = 900/hour** — our usage is ~19% of the Flash-Lite ceiling. Comfortable.
- **1,500 RPD** — our daily usage across 5 terminals (~1,360) is ~91% of the daily cap. **This is tight.** Under heavy multi-terminal use, we could exhaust the daily quota.
- **50 RPD for Pro** — exhausted almost immediately. Pro models are for occasional reasoning tasks, not pool members.

**Operational implication:** Flash-Lite is safe for daily pool use. Flash models have slightly lower RPM but similar RPD. Pro models are reserve-only (few calls per day, not pool members).

## DiffusionGemma via NVIDIA (separate quota pool)

DGemma on NVIDIA's API is a **completely separate rate pool** from Google's Gemini API:
- NVIDIA: ~40 RPM, no daily cap (verified from NVIDIA forums)
- Google Gemini API: ~15 RPM, ~1,500 RPD (practitioner-reported)

Using DGemma via NVIDIA does NOT consume Gemini API quota. The two are independent providers with independent limits.

## Gemma 4 via Gemini API

`gemma-4-31b-it` is hosted on Google's API (`generativelanguage.googleapis.com`). It shares the Gemini API rate limit pool — same project, same RPM/TPM/RPD. It's a different model but the same provider.

## agy (Antigravity CLI) — completely separate quota

**Source:** Google Developers Blog (transitioning Gemini CLI to Antigravity CLI, 2026-05-19) + `/agy` SKILL.md

agy uses the **Google AI Pro/Ultra subscription** for authentication — not the GEMINI_API_KEY. This is a completely separate identity and quota pool:

| Access path | Auth | Quota pool | Limits |
|-------------|------|-----------|--------|
| **Direct API** (our config.toml) | `GEMINI_API_KEY` from `.env` | Google Cloud project free tier | ~15 RPM, ~1,500 RPD (practitioner-reported) |
| **agy CLI** | Google account login (AI Pro/Ultra subscription) | Subscription tier | Separate from API; subscription-defined |

**Key implication:** using the direct API does NOT consume agy's subscription quota, and vice versa. They are independent paths to the same models with independent limits.

**When to use which:**
- Direct API: for pool dispatch (spawn_subagent, scripts, automated calls)
- agy: for second opinions, research with agent harness, cross-model critique (per `/agy` SKILL.md)

See [[gemini-api-vs-agy-cli]] for the full decision matrix.

## How to verify our actual limits

1. Go to [AI Studio rate-limit page](https://aistudio.google.com/rate-limit?timeRange=last-28-days)
2. Log in with the Google account that owns the GEMINI_API_KEYs
3. View per-model RPM, RPD, TPM for the current project

This is the only authoritative source for our actual limits. The practitioner-reported numbers above are community observations, not guarantees.

## Summary for cold-start LLMs

| Question | Answer | Confidence |
|----------|--------|------------|
| Is Gemini Flash-Lite free? | **Yes** — free input + output tokens on Free Tier | `[HIGH]` — Google's official pricing page |
| What's the daily cap? | **~1,500 RPD** (practitioner-reported; verify in AI Studio) | `[MEDIUM]` |
| What's the per-minute cap? | **~15 RPM** (practitioner-reported) | `[MEDIUM]` |
| Does it share quota with DGemma on NVIDIA? | **No** — completely separate providers | `[HIGH]` |
| Does it share quota with agy? | **No** — agy uses subscription auth, API uses project key | `[HIGH]` |
| Does it share quota across multiple API keys? | **Depends** — if same project, yes; if different projects, no | `[UNVERIFIED]` for our keys |
| Why did Pro models return "limit: 0"? | **Daily RPD exhausted** (Pro has ~50 RPD on free tier) | `[INFERENCE]` |
| Is ~1,360 calls/day across 5 terminals safe? | **Tight for Flash-Lite** (~91% of RPD); safe for Flash; unsafe for Pro | `[MEDIUM]` |

## Sources

- https://ai.google.dev/gemini-api/docs/pricing (scraped 2026-07-22; last updated 2026-07-21 UTC) — score 12
- https://ai.google.dev/gemini-api/docs/rate-limits (scraped 2026-07-22; last updated 2026-07-21 UTC) — score 12
- https://tokenmix.ai/blog/gemini-api-free-tier-limits (2026) — score 9
- https://yingtu.ai/en/blog/gemini-api-free-tier (verified July 16, 2026) — score 10
- https://pecollective.com/tools/gemini-free-tier-guide/ (2026) — score 9
- `/agy` SKILL.md (host-verified conductor contract)

## Auto-related

- [[solo_operator_adr_best_practices]]
## Falsifier

TODO (auto-generated by wiki_validator_sweep 2026-07-30): This concept predates the
mandatory Falsifier section. State what observation or evidence would make this
concept wrong or obsolete. If the concept is purely descriptive (not a claim),
state that explicitly: "This is a reference document, not a claim — no falsifier applies."
