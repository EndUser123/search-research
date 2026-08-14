---
title: "with perplexity pro, how much free api use do I get?"
date: "2025-12-07"
mode: "COPILOT"
uuid: "2ba38867-5155-42e7-b9ca-b9a9692c21c5"
entry_count: 6
---

## Human

with perplexity pro, how much free api use do I get?

## Assistant

**Perplexity Pro subscribers receive $5 in monthly credits for API usage on the Sonar API (also referred to as pplx-api or Sonar models).**[1][2]

These credits appear automatically on the first day of each month in your account's API settings tab, where you can also generate keys and monitor usage.  New subscribers may need to wait 10-20 minutes after signup for credits to activate, and manually adding credits incurs a separate $5 charge.[3][2]

Free plan users can access the API but do not receive these monthly credits; additional usage requires purchasing credits via the settings page.  Pro's API credits apply specifically to embedding AI-powered search with citations into projects, distinct from Pro's other unlimited features like searches or file uploads.[4][2][1]

## Human

what is the fee schedule for api use?

## Assistant

## Perplexity API Pricing Overview

Perplexity's Sonar API uses a token-based pricing model charged per million tokens for input and output, with rates varying by model.  Pro subscribers receive $5 monthly credits applicable to this usage.[1]

## Sonar Model Rates

| Model                | Input ($/M tokens) | Output ($/M tokens) | Additional Notes                  |
|----------------------|--------------------|---------------------|-----------------------------------|
| Sonar Pro           | 3                  | 15                  | Suitable for detailed answers [1] |
| Sonar Reasoning     | 1                  | 5                   | Standard reasoning tasks [1] |
| Sonar Reasoning Pro | 2                  | 8                   | Enhanced reasoning [1]      |
| Sonar Deep Research | 2 (input), 2 (reasoning) | 8            | Includes $3/M reasoning; exhaustive research [1] |

Some models add flat fees, such as $5 per 1,000 searches for base Sonar alongside token costs.  Check the official docs.perplexity.ai/pricing for latest rates, as they may update.  Usage is pay-as-you-go after credits, monitored in API settings.[2][3][1]

## Human

does the api tell me how much credit I have left?

## Assistant

**Perplexity's API dashboard displays your remaining credits and usage, but no public API endpoint exists for programmatic balance queries.**[1]

Access this via Settings > "</> API" tab, where credits (like Pro's $5 monthly allowance) and consumption patterns appear directly.  API responses include per-request `usage` details (e.g., `prompt_tokens`, `completion_tokens`), allowing client-side tracking of token spend against known rates.[2][1]

For precise monitoring, view the dashboard regularly or integrate usage logging in code, as programmatic credit checks are unavailable.[3][1]

## Human

Seriously, there's no way to programatically query how much I've used in a month??

## Assistant

**No, Perplexity's Sonar API lacks a programmatic endpoint to query monthly usage or remaining credits.**[1]

Monitor credits and consumption manually through the Settings > "</> API" tab dashboard, which shows usage patterns and balances.  Per-request responses provide token counts (`prompt_tokens`, `completion_tokens`) for client-side cost estimation against known rates, but aggregate monthly totals require dashboard checks.[1]

For programmatic tracking, implement local logging of API responses and calculate spend, as no billing/usage API exists.[1]

## Human

Users haven't found a way to track usage?  Or at least to know when they have gone beyond their $5?

## Assistant

## Current Tracking Limitations

Perplexity users rely on the web dashboard (Settings > "</> API" tab) for viewing usage, credits, and overages beyond the $5 Pro monthly allowance—no programmatic API endpoint exists.  Developers report challenges with manual logging or email alerts for thresholds, as dashboard-only access hinders automation.[1][2][3]

## User Workarounds

- **Client-side logging**: Track per-response token usage (`prompt_tokens`, `completion_tokens`) and estimate costs locally against rates.[4]
- **Billing dashboard**: Monitor invoices, API key-specific spend (e.g., via last 4 chars like "pro (743S)"), and set budget alerts (50%, 75%, 90%).[5][6]
- **Feature requests**: Open GitHub issue #266 seeks a usage/billing endpoint like OpenAI's, highlighting the gap.[2]

## Overage Handling

Exceeding $5 triggers pay-as-you-go charges if a payment method is added; auto-top-up prevents interruptions but requires setup.  Users hover over dashboard dates (e.g., July 4) for breakdowns confirming overages.  Contact api@perplexity.ai for enterprise options or feedback.[6][7][1][5]

## Human

How to set billing alerts for Perplexity API usage

## Assistant

**Perplexity API does not offer automated billing alerts or notifications for usage thresholds like the $5 Pro credits.**[1]

Monitor usage manually via Settings > "</> API" tab, which displays credits, consumption patterns, and per-key breakdowns (e.g., "pro (743S)").  No setup for email/push alerts on overages exists; users track via dashboard or local token logging from API responses.[2][1]

Feature requests for alerts appear in community discussions, but official docs confirm dashboard-only monitoring.  Contact api@perplexity.ai for enterprise billing options or feedback.[1][2]
