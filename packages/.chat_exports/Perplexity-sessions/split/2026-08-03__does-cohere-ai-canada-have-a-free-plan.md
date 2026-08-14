---
title: "does cohere ai canada have a free plan?"
date: "2026-08-03"
mode: "COPILOT"
uuid: "4ce0605e-c98b-4c3e-a8f2-946f296dc54c"
entry_count: 4
---

## Human

does cohere ai canada have a free plan?

## Assistant

Yes — Cohere appears to have a free **trial** tier for API use, but it is limited and not meant for production or commercial use. Their pricing page says API calls made from a Trial API key are free, while production keys are billed pay-as-you-go.[1]

## What that means
- You can sign up and test Cohere’s API without paying upfront.[2]
- The free access is tied to a Trial API key and comes with rate limits.[2]
- Cohere explicitly says trial keys are not for production or commercial purposes.[1][2]

## Important caveat
The free offering is for the API/platform, not necessarily a permanently free consumer plan. The official docs and pricing pages are the authoritative sources here, and they consistently describe a free but limited trial tier rather than an unlimited free plan.[1][2]

## Canada-specific note
Cohere is a Canadian company, but its free tier is not described as Canada-only; the pricing/trial information is presented as general platform access.[3][1]

## Human

What are the rate limits with the free plan?

## Assistant

Cohere’s free trial is limited by both **per-endpoint request rates** and a **monthly cap**. The official docs say trial keys are limited to **1,000 API calls per month**, with examples like **Chat: 20 requests/min**, **Embed: 100 calls/min** in one docs source, and **Rerank: 10/min**, **Tokenize: 100/min**, **EmbedJob: 5/min**.[1][2]

## Most relevant limits
- **Monthly cap:** 1,000 API calls per month on trial keys.[2][1]
- **Chat endpoints:** 20 requests per minute on the trial key.[1][2]
- **Embed:** 100 calls per minute in one docs page, though another official pricing-related snippet shows 2,000 inputs/min for Embed on trial; this looks like a doc/version mismatch, so treat the endpoint-specific page as the source of truth if you are implementing against the current API docs.[2][1]
- **Rerank:** 10 requests per minute on trial.[1]
- **Tokenize:** 100 requests per minute on trial.[1]
- **EmbedJob:** 5 requests per minute on trial.[1]
- **Default for unspecified endpoints:** 500 requests per minute.[1]

## Practical interpretation
For most small tests, the monthly cap is the bigger constraint than the per-minute limit. If you’re just prototyping, 1,000 calls/month usually means you can evaluate the API, but you should not rely on it for sustained traffic or production use.[3][1]

## One caveat
Cohere’s documentation appears to have some inconsistency between pages for certain endpoints, especially Embed, so I’d rely on the current docs page for the exact endpoint you plan to use rather than assuming one global free-plan limit applies everywhere.[2][1]

## Human

Is there a duration for the free tile trial? I would really like free forever.

## Assistant

No — Cohere’s free trial does **not** appear to be a “free forever” plan. The official pricing and FAQ pages describe it as a **trial API key** that is free but limited, with a **monthly cap of 1,000 calls** and endpoint-specific rate limits, which means it’s an ongoing trial allowance rather than an unlimited permanent free tier.[1][2][3]

## What the docs imply
- The trial is free to use, but it is explicitly limited and not for production/commercial use.[3][1]
- The documentation describes usage in terms of monthly call limits, not a fixed expiration date.[2][3]
- That usually means the account can stay on the free trial tier, but only within those limits, rather than giving unlimited free access forever.[1][3]

## Practical takeaway
If your goal is “free forever,” Cohere does not document that as an unlimited plan. The closest thing they offer is a permanently limited trial allowance, so for sustained use you’d need to stay under the cap or move to paid usage.[3][1]

## Confidence
High confidence on the limit structure; moderate confidence on the exact “forever” interpretation because Cohere’s docs focus on usage limits rather than explicitly saying “no expiration”.[1][3]

## Human

You keep saying limited and you say there's a rate, but you don't say for how long.

## Assistant

You’re right to press on that. The docs I found do **not** give a fixed time duration like 7 days or 30 days; instead, they describe the free tier as a **trial API key** with **usage limits** that reset monthly.[1][2][3]

## What “for how long” means here
- The official wording is about **monthly usage**, not a countdown expiration date.[3][1]
- That means the free tier is best understood as **ongoing access under limits**, not a temporary trial that automatically ends after a set number of days.[2][3]
- The docs also say API keys may have an expiration date in general, but they do **not** state a standard expiration period for the Cohere trial key itself.[3]

## So is it free forever?
- **Potentially yes in the narrow sense** that the trial key can remain available as long as your account exists and you stay within the trial rules.[2][3]
- **Not yes in the unlimited sense** because the trial is still capped at 1,000 calls per month and rate-limited per endpoint.[1][3]
- If your key expires or the program changes, the docs suggest checking the key validity and renewal status.[3]

## Clean answer
There is **no documented fixed duration** like “free for 14 days.” It is a **monthly-limited free trial key**, so the real question is usage cap, not time cap.[1][3]
