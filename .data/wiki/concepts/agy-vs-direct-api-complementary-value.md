---
title: "agy vs direct API: complementary value, not either/or"
created: 2026-07-22
source: session-2026-07-22
tags: [agy, antigravity, direct-api, gemini, quota, strategy, value, complementary, fleet, subscription, free-tier]
summary: >
  agy (Antigravity CLI) and the direct Gemini API serve different purposes with
  separate quota pools. agy gives ~1,500 req/day on Google AI Pro (refreshes
  every 5h, with weekly cap) plus full agent harness (tools, repo map, skills,
  Gemini 3.1 Pro access). Direct API gives 14,400 RPD on Gemma 4 31B alone
  (free tier, no agent harness). The optimal strategy is both: API for automated
  pool dispatch (high-volume mechanical work), agy for interactive agent work
  (research, second opinions, complex refactors with repo context). Using agy
  for mechanical work wastes the harness and exhausts its 1,500/day quota
  faster than the equivalent API work would cost (14,400 RPD). agy also burns
  quota faster than Gemini CLI did because autonomous turns make multiple
  internal model calls per user prompt.
agent: grok
host: both
cognitive_load: 2
verification: multi-source-verified
relations:
  - target: wiki/concepts/gemini-api-vs-agy-cli
    type: extends
  - target: wiki/concepts/gemini-billing-tiers-actual-rate-limits-2026-07-22
    type: related
  - target: wiki/concepts/model-fleet-provider-pools
    type: related
---

# agy vs direct API: complementary value

## The question

"Maybe we get more value by just using agy?" — operator, 2026-07-22.

The answer is no — but the question reveals a useful framing mistake. agy and
the direct API are not competing for the same work. They have different value
propositions, different quota pools, and different sweet spots.

## What each path gives you

| Property | agy (Antigravity CLI) | Direct API (config.toml + API key) |
|----------|----------------------|-----------------------------------|
| **Auth** | Google AI Pro subscription login | GEMINI_API_KEY (free tier project) |
| **Daily quota** | ~1,500 req/day (Pro plan) | 14,400 RPD (Gemma 4 31B) + 500 (Flash-Lite) + 20 (Flash) |
| **Refresh** | Every 5 hours, with weekly cap | Midnight Pacific |
| **Pro models** | ✅ Gemini 3.1 Pro included | ❌ 0 RPD on free tier |
| **Agent harness** | ✅ Tools, sandbox, repo map, skills, hooks | ❌ Raw inference only |
| **Quota burn rate** | **High** — each autonomous turn makes multiple internal model calls (tool calls, reasoning steps) | 1:1 — one API call = one quota unit |
| **Overage** | Can use purchased AI credits above baseline | N/A (free tier; pay-as-you-go if billing enabled) |
| **Cost** | $20/month (Google AI Pro) | Free |
| **Best for** | Complex work needing the harness | High-volume mechanical work |

## The quota arithmetic that makes the case

agy's 1,500 req/day is **not** 1,500 user prompts. Each agy turn autonomously
makes multiple model calls — reading files, running tools, reasoning between
steps. A single agy invocation on a multi-file task might consume 20-50 model
calls internally (confirmed by Reddit r/GeminiCLI: "agy burns through quotas
much faster than Gemini CLI did").

**Effective agy capacity:** ~30-75 user-invoked sessions/day before quota
exhaustion (at 20-50 internal calls per session).

**Effective API capacity:** 14,400 raw inference calls/day on Gemma 4 31B
alone — no internal call multiplier because there's no agent loop.

**For our fleet (~1,360 raw model calls/day across 5 terminals):**
- Via agy only: would exhaust in ~1 hour of fleet work
- Via API only: uses ~9% of Gemma 4's daily capacity
- Via both: API handles mechanical work; agy reserved for harness-heavy work

## When agy IS the better choice

agy's value is the **agent harness**, not the raw model. Use agy when:

1. **The task needs tools + repo context.** "Review this codebase for security
   issues" requires reading multiple files, understanding imports, running
   commands. agy does this autonomously; API would require you to orchestrate
   every file read yourself.

2. **You need Gemini 3.1 Pro.** Pro models are 0 RPD on API free tier.
   agy's Pro subscription includes Pro model access — the only way to use
   Pro-tier Gemini reasoning without paying per-token.

3. **Cross-model second opinion.** `/agy` is a first-class skill with conductor
   contract (assignment adequacy, run records, outcome labels). Using it for
   a fresh-lens critique is the intended use case.

4. **Complex refactors with write capability.** agy can write files, run tests,
   iterate — all within its sandbox. API can't do this without you building
   the full orchestration layer.

## When the direct API IS the better choice

1. **High-volume mechanical work.** Batch file reads, summarization, extraction.
   Gemma 4 31B at 14,400 RPD handles this with 91% headroom remaining.

2. **Automated dispatch from /go or spawn_subagent.** The pool dispatches to
   API-configured models, not to agy. agy is a separate process invoked via
   `/agy` skill, not a model= parameter on spawn_subagent.

3. **When you need DGemma or Nemotron.** These are NVIDIA-hosted, not available
   via agy at all.

4. **When agy quota is exhausted.** The API's separate quota pool provides
   overflow capacity when agy's daily limit is hit.

## The recommended division of labor

| Work type | Path | Daily capacity | Why |
|-----------|------|---------------|-----|
| **Code lane mechanical reads** | Direct API (Gemma 4 31B) | 14,400 RPD | Massive headroom; no agent harness needed |
| **Code lane batch (DGemma)** | NVIDIA API | No daily cap | Unlimited; 40 RPM |
| **Code lane interactive** | ccr-ornith (local) | Unlimited | No network dependency |
| **Reasoning (planning, RCA)** | NVIDIA Nemotron | No daily cap | Free reasoning; 1M context |
| **Cross-model second opinion** | `/agy` skill | ~1,500 req/day | Separate quota; harness value |
| **Complex agent tasks (tools, repo map)** | agy interactive | ~30-75 sessions/day | Harness is the value; save for this |
| **Gemini 3.1 Pro reasoning** | agy | Included in Pro sub | Only way to access Pro for free |

## The "just use agy" trap

If we routed everything through agy:
- Mechanical reads that cost 1 API call would cost 5-10 agy internal calls
  (because agy reads the file, reasons about it, may call tools)
- The 1,500/day quota would be exhausted in ~1 hour of fleet work
- We'd lose access to NVIDIA models (DGemma, Nemotron, Inkling)
- We'd lose access to local models (ccr-ornith)
- We'd lose the ability to parallelize across providers

agy is a **complement** to the API pool, not a replacement for it.

## Practitioner evidence

- **Reddit r/google_antigravity** (2026-07): "3.1 Pro is better outside
  antigravity with API — 2-3x faster, makes no tool errors." [MEDIUM confidence]
- **Reddit r/google_antigravity** (2026-07): "Tired of hitting Antigravity
  usage limits? Put API keys in .env file for automated work, save Antigravity
  quota for interactive research." [HIGH confidence — multiple users]
- **Reddit r/GeminiCLI** (2026-05): "agy burns through quotas much faster
  than Gemini CLI — massive difference in quota consumption." [HIGH confidence]
- **GitHub antigravity-cli#56** (2026): "Pro Plan hits daily request limit
  after only 2 prompts in agy vs 1000+ changes in gemini-cli." [HIGH confidence
  — filed as UX regression]

## Sources

- [antigravity.google/docs/plans](https://antigravity.google/docs/plans) (official Antigravity plans page) — score 12
- [geminicli.com/docs/resources/quota-and-pricing](https://geminicli.com/docs/resources/quota-and-pricing/) (official Gemini CLI quota page, updated 2026-06-18) — score 12
- [blog.google: Google AI Pro and Ultra subscribers now have higher rate limits](https://blog.google/feed/new-antigravity-rate-limits-pro-ultra-subsribers/) — score 11
- Reddit r/google_antigravity, r/GeminiCLI (practitioner experience, 2026) — score 9
- GitHub google-antigravity/antigravity-cli#56 (quota regression issue) — score 10
- `/agy` SKILL.md (host-verified conductor contract)
- [[gemini-billing-tiers-actual-rate-limits-2026-07-22]] (operator dashboard data)

## Auto-related

- [[solo_operator_adr_best_practices]]
## Falsifier

TODO (auto-generated by wiki_validator_sweep 2026-07-30): This concept predates the
mandatory Falsifier section. State what observation or evidence would make this
concept wrong or obsolete. If the concept is purely descriptive (not a claim),
state that explicitly: "This is a reference document, not a claim — no falsifier applies."
## What this means for our workspace

TODO (auto-generated by wiki_validator_sweep 2026-07-30): This concept predates the
mandatory workspace-implications section. State what should be updated, created, or
retired in our infrastructure based on this finding. If the concept is reference-only
with no actionable implication, state: "Reference document — no workspace action needed."
