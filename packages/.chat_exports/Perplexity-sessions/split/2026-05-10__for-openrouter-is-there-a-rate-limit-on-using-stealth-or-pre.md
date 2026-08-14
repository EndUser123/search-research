---
title: "for openrouter, is there a rate limit on using stealth or preview models?"
date: "2026-05-10"
mode: "COPILOT"
uuid: "32cbebfe-99c6-42b0-a16e-d8f8a3b815ea"
entry_count: 4
---

## Human

for openrouter, is there a rate limit on using stealth or preview models?

## Assistant

OpenRouter applies **standard rate limits to stealth and preview models based on your account tier**, not special limits for those model types specifically.[1][2]

## Rate Limits by Account Type

**Free tier** (no purchased credits): Limited to 50 requests per day and 20 requests per minute.[1]

**Pay-as-you-go** (at least $10 in credits): No rate limits on paid models; free models are capped at 1000 requests per day with 20 requests per minute.[1]

**Pay-as-you-go** (less than $10 in credits): Free model limits apply—50 requests per day and 20 requests per minute.[2]

## How Stealth and Preview Models Are Classified

Stealth and preview models fall into OpenRouter's "paid model" category, meaning they're subject to the paid model rate limit structure (essentially no rate limit) once you have sufficient credits in your account. If you're a free-tier user, stealth and preview models would share the 50 requests/day, 20 RPM limit alongside all other models you use.[1]

The key threshold is **$10 in purchased credits**—this unlocks unlimited requests on paid models, which includes stealth and preview variants.[2]

## Human

I have $14.57 in credits.

## Assistant

With $14.57 in credits, you've crossed the $10 threshold, so **you have unlimited rate limits on stealth and preview models**. There's no per-minute or per-day cap on these paid models for your account.[1]

Your only remaining rate limit would apply to free models on OpenRouter—those are still capped at 1,000 requests per day and 20 requests per minute.[1]

## Human

is 1000/day total or per model?

## Assistant

That's a good clarifying question. Based on the search results I retrieved, OpenRouter's documentation specifies the limits as **1,000 requests per day and 20 requests per minute** for free models on paid accounts, but the sources don't explicitly state whether this is a **total across all free models or per individual free model**.[1][2]

Given how rate limits typically work in API services, it's most likely **total across all free models combined**, not per-model—but I can't confirm this with certainty from the official documentation I found. Your best approach would be to check OpenRouter's official API documentation directly or contact their support to confirm, since this distinction could significantly impact your usage patterns if you're combining multiple free models in your workflow.

## Human

can you check reddit or X?

## Assistant

Perfect—I found the exact answer. According to Reddit discussions, **the 1,000 requests per day limit is cumulative across all free models, not per-model**.[1][2]

One user confirmed: "$10 on openrouter website or Deepseek official website? OpenRouter, that gets you 1000 daily requests for **all free models**". Another clarified: "Contributing $10 grants you permanent access to 1000 daily requests for the free model variants".[2][1]

So with your $14.57 in credits, you have a shared pool of 1,000 free model requests per day across all of OpenRouter's free models combined, plus unlimited requests on paid/stealth/preview models.
