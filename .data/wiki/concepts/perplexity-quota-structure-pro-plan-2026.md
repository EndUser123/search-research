---
title: "Perplexity Quota Structure (Pro Plan, 2026)"
created: 2026-08-02
source: session-2026-08-02
tags: [perplexity, quota, reference, fleet-infrastructure]
summary: >
  Perplexity Pro plan quota structure verified Aug 2026 via official help-center
  comparison table, practitioner API captures of the hidden rate-limit endpoint,
  and annual-plan user reports. Key finding: "Unlimited Pro Search" is marketing
  language with a hidden fair-use cap that was reduced from 600/day (Feb 2026)
  to 200 rolling drip-refill after a May 2026 silent quota cut.
agent: grok
host: both
cognitive_load: 2
verification: multi-source-verified
relations:
  - target: wiki/concepts/private-uncensored-text-to-speech.md
    type: related
  - target: wiki/concepts/tool-fallbacks.md
    type: related
---

# Perplexity Quota Structure (Pro Plan, 2026)

## Decision context

**Why this research was needed:** the fleet quota dashboard (`fleet_quota.py`) added Perplexity as a provider but used guessed pool sizes and reset schedules. The operator noticed the output looked wrong (Browser Agent at 0 for 14+ hours, fake percentages). This research verified the actual numbers.

**What alternatives were explored:** three rounds of research — (1) pricing blogs and comparison articles, (2) Reddit r/perplexity_ai practitioner threads with full comment scraping, (3) official help-center comparison table via web_fetch + a practitioner's capture of the hidden `perplexity.ai/rest/rate-limit/all` API endpoint.

**What the research changed:** corrected all pool sizes, reset schedules, and the Browser Agent feature description in the fleet quota code. Changed Pro Search from "weekly" to "rolling", Browser Agent from "weekly" to "monthly", and Browser Agent from "Max-only" to "available on Pro with undisclosed pool."

## Verified quota structure (Pro plan, $20/mo or $200/yr)

| Quota | Pool | Reset | Source |
|---|---|---|---|
| **Pro Search** | 200 | Rolling drip-refill (~1 per 7 min) | wellstsai.com + pwm CLI + sifuyik.substack.com + practitioner API capture |
| **Deep Research** | 20 | Monthly | Official help-center table + practitioner capture + pwm matches |
| **Create Files & Apps** | 25 | Monthly | Practitioner API capture + pwm matches |
| **Browser Agent** | Undisclosed ("monthly limits, average use") | Monthly | Official help-center comparison table |

### The hidden "Advanced AI models" sub-quota

Within the 200 Pro Search total, there is a SEPARATE quota for premium models (Claude Sonnet, GPT-5.4, etc.): approximately **5 per week**. After exhausting this, queries fall back to the Sonar model. This was NOT documented in official Perplexity materials — only surfaced via practitioner reports.

**Source:** Reddit r/perplexity_ai, u/Metsatronic (Jul 2026): "they have reclassified the mid tier models like Sonnet and GPT-5.4 as 'Advanced' and giving us 5 requests per week." Corroborated by u/goranstoja: "In that 100 you got 10 search with advanced LLM models."

## The "Unlimited Pro Search" contradiction

Perplexity's marketing says "Unlimited Pro Search." This is misleading:

| Date | Actual Pro Search pool | Source |
|---|---|---|
| Early 2024 | ~600/day | Reddit r/perplexity_ai |
| Aug 2025 | "Over 300/day" | datastudios.org |
| Feb 2026 | 600 (per hidden API) | Practitioner API capture (u/Azek_Tge) |
| May 15, 2026 | **Silent reduction** | piunikaweb.com: "Perplexity quietly reduced usage limits" |
| Jul 2026 | 200 rolling | wellstsai.com + pwm CLI output |

**Resolution:** "Unlimited" means "no hard daily cap that returns an error." Instead, there's a rolling drip-refill budget (200 searches replenished at ~1 per 7 minutes). This is effectively unlimited for light users but throttles heavy users — and Perplexity can (and did) reduce the pool silently without changing the marketing language.

## What Browser Agent actually does

Per the official Comet resource article ("Comet Assistant vs. Comet Agent", Jul 28, 2026):

- **Comet Assistant** (passive, sidebar): summarizes pages, answers questions, has tab awareness
- **Comet Agent** (active, task-doing): clicks buttons, fills forms, navigates websites autonomously, books flights, schedules meetings, sends emails, makes purchases, manages multi-step workflows

The quota "Browser Agent" refers to the Agent (active) queries, not the Assistant (passive) ones. Free users can use the browser and the Assistant; the Agent requires Pro+.

## The hidden API endpoint

`https://www.perplexity.ai/rest/rate-limit/all` — returns JSON with keys including `remaining_pro`, `remaining_research`, `remaining_agentic_research`, `remaining_labs`, `free_queries`, and `sources` (per-source monthly limits). Requires authentication to return real numbers; unauthenticated calls return zeros/null.

The `pwm usage` CLI appears to read from this endpoint.

## Enterprise tier reference numbers

For comparison (from the official comparison table):

| Feature | Enterprise Pro ($40/seat) | Enterprise Max ($325/seat) |
|---|---|---|
| Pro Search | Unlimited | Unlimited |
| Deep Research | 500/day | Near Unlimited |
| Browser Agent | 80/month | 800/month |
| Create Files & Apps | Extended | Near Unlimited |

These are the only published numeric Browser Agent quotas. Individual Pro/Max get only qualitative descriptions.

## Receipts

- **Pro Search = 200 rolling:** [FACT] wellstsai.com 2026 update ("200 Pro searches per week") + pwm CLI shows 200 remaining on fresh account + sifuyik.substack.com ("200 searches spread across 24 hours... 1 every ~7 minutes") + Reddit u/Metsatronic ("It's rolling")
- **Deep Research = 20 monthly:** [FACT] Official help-center comparison table + practitioner API capture (Feb 2026) + wellstsai.com ("20 Deep Research queries per month") + pwm matches
- **Create Files = 25 monthly:** [FACT] Practitioner API capture (Feb 2026) + pwm matches
- **Browser Agent on Pro:** [FACT] Official help-center comparison table: Pro = "Monthly limits (average use)"
- **Browser Agent pool undisclosed:** [FACT] No published number for Pro/Max. Enterprise Pro = 80/month, Enterprise Max = 800/month.
- **Browser Agent reset = monthly:** [FACT] Comparison table column header. Note: Max help-center article says "weekly" — contradicts the comparison table. Comparison table is authoritative.
- **Silent May 2026 reduction:** [FACT] piunikaweb.com (May 15, 2026) + Reddit thread "the pro plan has much lower weekly limits now"
- **Advanced AI models sub-quota (~5/week):** [PRACTITIONER] u/Metsatronic + u/goranstoja on Reddit. Not in official docs.

## Falsifier

This page is wrong if:
- Perplexity publishes exact Browser Agent pool sizes for individual Pro/Max tiers
- The quota structure changes again (it has changed at least 3 times in 2025-2026)
- The hidden API endpoint is removed or restructured

Re-research if: >3 months old, or after any Perplexity pricing/plan announcement.

## What this means for our workspace

1. **`fleet_quota.py` now shows verified Perplexity data.** Pool sizes and reset schedules are no longer guesses. Pro Search = 200 rolling, Deep Research = 20 monthly, Create Files = 25 monthly, Browser Agent = undisclosed (monthly). The code handles the unknown Browser Agent pool by showing "0 remaining (pool unknown)" with a red bar.

2. **The `pwm` CLI is the authoritative source for this operator's yearly plan.** The numbers (200 Pro Search, 20 Deep Research, 25 Create Files) match exactly between pwm output and the verified pool sizes. When pwm shows a different number than the pool, it means quota has been consumed.

3. **Browser Agent at 0 is expected for a fresh/reset month or after exhaustion.** The pool size is undisclosed for Pro. If it's still 0 at the start of a new billing month, the yearly plan may have a very small pool (or 0). Next step: observe on the next monthly reset date.

4. **The hidden "Advanced AI models" sub-quota (~5/week) is not tracked by pwm or the dashboard.** This means the fleet could silently fall back to Sonar model after 5 premium-model queries without the dashboard showing it. No fix planned — this is a Perplexity-side opacity problem.

5. **Perplexity silently reduced quotas in May 2026.** If further reductions happen, the pool sizes in the code will become wrong. The `pwm usage` CLI always shows real remaining counts, so the raw numbers stay accurate even if the pool-size assumptions drift.

## Related

- [[tool-fallbacks]] — Tool Fallbacks (pwm as Perplexity CLI)
- [[private-uncensored-text-to-speech]] — TTS research (uses fleet quota for model dispatch)
- [[model-pool-selection-policy-speed-quota-diversity]] — Model pool selection
