---
title: "for the kimi.com coding plan, what are the rate limits?"
date: "2026-04-22"
mode: "CONCISE"
uuid: "77213d7e-5a87-4973-87ee-f9c0340ab7f4"
entry_count: 5
---

## Human

for the kimi.com coding plan, what are the rate limits?

## Assistant

Based on the search results, **Kimi.com's coding plan (Kimi Code) uses a rolling 5-hour frequency window combined with a weekly quota system**.[1][2]

## Rate Limit Structure

**5-hour rolling window**: Even if you have sufficient total quota, too many requests in a short 5-hour period will trigger rate limiting, which automatically recovers as the window rolls forward.[2]

**Weekly quota**: The quota refreshes automatically every 7 days from your subscription date, with unused quota not carrying over. For the Moderato membership tier (~$19/month), this includes 2,048 Kimi Code requests per week.[3][2]

## Concurrency & Throughput

The standard tier supports a **maximum concurrency of 30 simultaneous requests**. For reference, if you're using the API via Kimi Code (separate from chat credits), the rate limits scale with recharge tier: Starter tier ($1–$9) allows ~3 RPM (requests per minute), while Tier 1 ($10+) allows 200 RPM with 50 concurrent connections.[4][1]

## Key Constraint

Kimi Code shares quota with your main Kimi membership plan—if your membership's monthly quota is exhausted, Kimi Code access freezes until reset or upgrade.[2]

Are you planning to use Kimi Code via CLI/API integration, or through the chat interface within a development tool?

## Human

See you later.

## Assistant

Answer skipped.

## Human

cli

## Assistant

For **Kimi CLI via the API platform**, the rate limits are multidimensional:[1]

## API Rate Limit Dimensions

- **Concurrency**: Maximum simultaneous requests at any given time[1]
- **RPM (Requests Per Minute)**: Request throughput cap[1]
- **TPM (Tokens Per Minute)**: Token consumption rate[1]
- **TPD (Tokens Per Day)**: Daily token budget[1]

The system hits whichever limit is breached first. For example, if you send 20 requests at 100 tokens each but your RPM is only 20, you'll hit the RPM limit even if token usage is far below your TPM ceiling.[1]

## Specific Tier Limits

The exact numbers scale with your **cumulative recharge amount**—the Kimi API Platform ties rate limits to total account spend rather than membership tier. You must recharge at least $1 to use the API, and hitting $5 cumulative gets you a $5 voucher.[2]

For practical reference, reports indicate **~1000 RPM** is a common ceiling for standard paid tiers, with concurrency around **50 parallel requests**.[3]

## Key Behaviors

- Rate limits are **user-level** (not per API key) and **shared across all models**[1]
- Responses include `X-RateLimit-Remaining` and `Retry-After` headers—respect these for backoff logic[3]
- The system uses `max_completion_tokens` in billing calculations, not actual output tokens[1]

For your exact limits, check the **Kimi API Platform dashboard** at `platform.kimi.ai/docs/pricing/limits`, or email `[email protected]` if you need higher enterprise quotas.[2]

## Human

So on their $19 a month plan, or $15 a month plan, you get 2,000 requests per week? That doesn't seem like very much.

## Assistant

You're right to be skeptical. **2,048 requests per week (~292 per day) on the $19 Moderato plan is quite constrained** compared to competing tools.[1]

## The Real Bottleneck

The **5-hour rolling window is the tighter constraint** than weekly quota. The $19 plan caps you at **200–300 requests per 5-hour window** with a max of 30 concurrent requests. That's the practical ceiling—you could theoretically use your entire weekly quota in 1-2 days if you wanted, but the 5-hour frequency window prevents sustained high-throughput automation.[2][3]

**Example**: If you're running parallel scraping agents or batch processing, you're limited to ~40–60 requests per hour on the $19 tier, even if you have weekly quota remaining.[3]

## Scaling Up

To compare: the **$60/month plan** gives you **1,350 requests per 5-hour window** (10x more). At that tier, you'd hit ~270 requests per hour—workable for sustained CLI automation. For heavy multi-agent orchestration (like 100 parallel agents), you're looking at **$15–$25 per session** on the $19 plan versus enterprise tiers.[4][2]

## Your Real Options

Given your use case (heavy YouTube data extraction + NotebookLM pipeline automation), the $19 plan isn't designed for what you're building. Either:

1. **Stay on $19** but architect for batch jobs within the 5-hour window (queue overnight runs, stagger requests)
2. **Jump to $60/month** for sustained automation workflows
3. **Use the API tier instead** and pay per token—this decouples request limits from memberships and might be cheaper for episodic workloads[1]

Does the 5-hour window constraint align with your actual usage pattern, or are you planning for always-on automation?

## Human

I only code 15 hours a day.

## Assistant

Then the 5‑hour window matters more than the weekly number.

On the **$15–$19 coding/membership tiers**, your practical situation looks roughly like this (based on current docs and third‑party breakdowns, which are not perfectly consistent, so treat as approximate, not exact FACT):[1][2][3]

- **Weekly quota**: ~2,000–2,048 “Kimi Code” requests/week on the mid tier.[2][3]
- **5‑hour rolling window**: a few hundred requests per 5‑hour block on that tier (reports cluster in the 200–300 / 5h range, but Kimi doesn’t publish a single clean number per plan).[3][1]
- **Concurrency**: around 30 concurrent requests for the coding agent in this band.[4][1]

Given **15 hours/day**:

- You effectively get **three 5‑hour windows per day**.  
- If each window is ~200–300 requests, you’re looking at **600–900 requests/day** ceiling from the frequency limit, *but* your **2k/week quota will probably run out first** if you hit that every day.  
- 2,000 / 7 ≈ **285 requests/day average** before weekly quota exhaustion, so sustained coding at your pace will feel cramped quickly.

So your intuition is right: **for a 15‑hours‑per‑day heavy dev workflow, that mid plan is under‑provisioned**; it’s tuned for “serious casual” rather than “I live in the CLI with an AI pair‑programmer”.

If you want to stay with Kimi, the more realistic options for your actual usage pattern are:

- **Higher membership tier (e.g., ~$60/mo)** – documented to raise per‑window limits by ~10x in some cases (into the ~1,000+ requests / 5h band), which fits 15‑hour days far better.[3]
- **Switch to / supplement with the API** – per‑token billing with higher RPM/concurrency ceilings tied to recharge level, which is often more economical for spiky or very heavy usage than “fixed weekly request” bundles.[5][6]

If you give me your *typical* interaction size (tokens per request) and how many calls/hour you actually want (e.g., 10/min single‑agent vs 50/min multi‑agent), I can ballpark:

- whether the **$60 plan** is enough, or  
- whether a **pure API + cheaper membership** strategy is better for you.
