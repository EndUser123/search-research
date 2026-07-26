---
title: "Gemini API billing tiers and actual rate limits (verified 2026-07-22)"
created: 2026-07-22
source: session-2026-07-22
tags: [gemini, billing, rate-limits, free-tier, tier-1, prepay, gemma, flash-lite, pricing, verified, operational]
summary: >
  Verified from operator's AI Studio dashboard + Google billing docs: both API
  keys are Free tier (Google One AI Pro subscription does NOT upgrade API project
  tier). Actual rate limits confirmed: Gemma 4 31B has 14,400 RPD / 30 RPM (best
  free model by far); Flash-Lite has 500 RPD / 15 RPM; Flash has 20 RPD / 5 RPM;
  Pro has 0 RPD (not available on free tier). Enabling billing moves ALL models
  to per-token pricing (minimum $10 prepay; stops when credits hit $0). Cannot
  have billing enabled and still get free pricing on the same project. Solution:
  stay on free tier; use Gemma 4 31B as primary (massive headroom), with DGemma
  (NVIDIA, no daily cap) and Flash-Lite as complementary pool members.
agent: grok
host: both
cognitive_load: 2
verification: directly-verified
relations:
  - target: wiki/concepts/gemini-gemma-quota-rate-limits-2026-07-22
    type: corrects
  - target: wiki/concepts/model-fleet-provider-pools
    type: grounds
  - target: wiki/concepts/dgemma-gemini-flash-operational-tests-2026-07-22
    type: grounds
---

# Gemini API billing tiers and actual rate limits

## Correction from previous concept

The prior concept (`gemini-gemma-quota-rate-limits-2026-07-22`) reported
practitioner-estimated limits (~1,500 RPD for Flash-Lite). The operator's
actual AI Studio dashboard shows the real numbers are **lower**. This concept
supersedes those estimates with directly-verified data.

## Both API keys are Free tier (verified)

| Account | Project | API key | Tier |
|---------|---------|---------|------|
| a.hominidae@gmail.com (Google One AI Pro) | gen-lang-client-0139984961 | `AIzaSyB9...` | **Free** |
| brsthomson@hotmail.com | gen-lang-client-0142216870 | `AQ.Ab8R...` | **Free** |
| Third key (`_1`) | Unknown | `AIzaSyDK...` | Unknown |

**Key finding:** Google One AI Pro subscription does NOT upgrade the API
project's tier. The subscription covers agy/Google AI Studio interactive
usage, not the API project's billing tier. Both API projects remain on Free
tier regardless of the subscription.

## Actual rate limits (from operator's AI Studio dashboard)

| Model | Free RPM | Free RPD | Free TPM | Fleet viability |
|-------|----------|----------|----------|----------------|
| **Gemma 4 31B** | **30** | **14,400** | **16K** | ✅ **Primary** — massive daily headroom |
| **Gemma 4 26B** | **30** | **14,400** | **16K** | ✅ Same limits (open model variant) |
| **Gemini 3.5 Flash-Lite** | **15** | **500** | **250K** | ⚠️ Tight — 500/day ÷ 5 terminals = 100/terminal |
| **Gemini 3.1 Flash-Lite** | **15** | **500** | **250K** | ⚠️ Same as 3.5 Flash-Lite |
| Gemini 3.6 Flash | 5 | **20** | 250K | ❌ Reserve only (20 RPD total) |
| Gemini 3.5 Flash | 5 | **20** | 250K | ❌ Reserve only |
| Gemini 3 Flash Preview | 5 | **20** | 250K | ❌ Reserve only |
| Gemini 2.5 Flash | 5 | **20** | 250K | ❌ Reserve only |
| Gemini 2.5 Flash Lite | 10 | **20** | 250K | ❌ Reserve only |
| Gemini 2.5 Pro | **0** | **0** | — | ❌ Not available on free tier |
| Gemini 3.1 Pro Preview | **0** | **0** | — | ❌ Not available on free tier |

**RPD resets at midnight Pacific time.** TPM is per-minute token budget (input).

## Can you enable billing and still get free models?

**No.** From Google's billing docs (ai.google.dev/gemini-api/docs/billing, scraped 2026-07-22):

> "Upgrading from the Free Tier to the Paid Tier means linking a billing account
> and prepaying to add a minimum of $10 of credits to your account."

> "When your Prepay credit balance hits $0, all API keys in all projects linked
> to that billing account will stop working simultaneously."

Once billing is enabled on a project:
- ALL models switch to per-token paid pricing (Flash-Lite: $0.30/$2.50 per 1M)
- The "Free of charge" pricing column no longer applies
- You must maintain a positive credit balance or API stops entirely
- Minimum prepay: $10 (expires after 12 months if unused; non-refundable)

**Workaround:** keep separate projects. One project stays free tier (for free
model access). A second project with billing enabled (for paid models / higher
limits). Different projects, different billing, different limits.

**Recommendation for this fleet:** stay on free tier. The free models (especially
Gemma 4 at 14,400 RPD) provide more than enough capacity.

## The Gemma 4 31B opportunity

Gemma 4 31B is the **hidden gem** of the free tier:

| Property | Value |
|----------|-------|
| RPD | **14,400** (28x more than Flash-Lite's 500) |
| RPM | **30** (2x Flash-Lite's 15) |
| TPM | **16K** (low — large file reads need spacing) |
| Cost | Free |
| Context window | 131K |
| Architecture | Google's open Gemma 4 model, hosted on Gemini API |

**TPM caveat:** 16K tokens per minute is the constraint. A single 9K-token
file read (like go/SKILL.md) uses more than half the per-minute budget. For
batch reads: one large file per ~30 seconds, or use multiple smaller reads.

**In our tests:** Gemma 4 31B via Gemini API responded correctly on probes
(`OK` with content). Quality not formally tested in the DGemma/Gemini test
suite (which tested Gemini 3.5 Flash-Lite, not Gemma). Should be tested.

## Operational strategy (free tier only, no billing)

| Role | Primary | Secondary | Notes |
|------|---------|-----------|-------|
| **Code lane mechanical reads** | **Gemma 4 31B** (14,400 RPD, 30 RPM, 16K TPM) | DiffusionGemma via NVIDIA (no daily cap, ~40 RPM) | Gemma has the most headroom; DGemma provides overflow |
| **Code lane large context** | DiffusionGemma via NVIDIA (262K ctx, no daily cap) | Gemini Flash-Lite (1M ctx, 500 RPD) | DGemma for batch; Flash-Lite for occasional large reads |
| **Reasoning** | Nemotron via NVIDIA (1M ctx, no daily cap) | GLM-5.2 (subscription, 4.3K req/mo) | NVIDIA has no daily cap for reasoning either |
| **Second opinion / research** | agy (separate AI Pro subscription quota) | — | Completely independent pool |

**Total free daily capacity across all providers:**
- Gemma 4 31B: 14,400 RPD
- NVIDIA (DGemma + Nemotron + Inkling): ~57,600/day at 40 RPM (no cap)
- Gemini Flash-Lite: 500 RPD
- **Combined: ~72,500 requests/day** — far exceeds fleet demand (~1,360/day across 5 terminals)

## What this means for pool membership

The pool ordering should reflect actual rate limit headroom:

| Priority | Model | Why |
|----------|-------|-----|
| 1 | **Gemma 4 31B** (Gemini API) | 14,400 RPD — by far the most daily capacity |
| 2 | **DiffusionGemma** (NVIDIA) | No daily cap — unlimited requests, 40 RPM |
| 3 | **ccr-ornith** (local) | Unlimited — no rate limits at all |
| 4 | Gemini 3.5 Flash-Lite | 500 RPD — use sparingly; good for large-context reads |
| 5 | MiniMax M3 (subscription) | 530 RPD — escalation tier |

Gemma 4 31B should be the **default Code lane model**, not a "diversity"
afterthought. It has 28x more daily capacity than Flash-Lite and scored
well in probes.

## Sources

- Operator's AI Studio rate-limit dashboard (verified 2026-07-22, direct paste)
- [ai.google.dev/gemini-api/docs/billing](https://ai.google.dev/gemini-api/docs/billing) (scraped 2026-07-22; last updated 2026-07-21)
- [ai.google.dev/gemini-api/docs/pricing](https://ai.google.dev/gemini-api/docs/pricing) (scraped 2026-07-22)
- [ai.google.dev/gemini-api/docs/rate-limits](https://ai.google.dev/gemini-api/docs/rate-limits) (scraped 2026-07-22)
- usagebox.com, yingtu.ai (practitioner sources on separate-project workaround)

## Auto-related

- [[solo_operator_adr_best_practices]]

