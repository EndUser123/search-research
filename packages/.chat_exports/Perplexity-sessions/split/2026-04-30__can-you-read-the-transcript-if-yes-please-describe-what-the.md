---
title: "can you read the transcript?  if yes please describe what the subscription plan he used is."
date: "2026-04-30"
mode: "COPILOT"
uuid: "05ae8579-7aa3-47e8-9ae5-7eba80dd1b48"
entry_count: 4
---

## Human

can you read the transcript?  if yes please describe what the subscription plan he used is.

## Assistant

**Yes**, I read the full transcript from the currently open YouTube page.[1]

## Primary Access
He used DeepSeek's direct API access via deepseek.com: log in, add funds (prepay balance), generate an API key, and integrate it into tools like his Alef Agent or OpenCode IDE—no named "subscription plan," but pay-per-use with cash pricing (~$0.175/M input tokens for V4 Flash, <$0.30/M output; even lower with cache) totaling <$1 for a full day of heavy agentic workflows (newsroom automation, multi-tool tasks).[1, {ts:437}][1, {ts:421}][1, {ts:204}]

## OpenCode Integration
Via free OpenCode IDE (open-source VS Code alternative), he pasted the DeepSeek API key to select V4 Flash/Pro models directly; OpenCode itself has optional paid plans (e.g., $5 first month/$10 after for Zen tier with model quotas including DeepSeek V4 Pro and Kimi K2), but he implies using the free tier + his DeepSeek API key (not a distinct subscription).[1, {ts:496}][1, {ts:473}][1, {ts:451}]

## Human

what's the url to learn more about the opencode sub plan?  do I have to use it with opencode?

## Assistant

From the video transcript, the creator does not give a direct URL for the OpenCode subscription/plan page, only a rough verbal description of pricing and features.[1]

## What he actually says about the plan

From the “Setting Up With Open Code” and “Open Code Deep Dive” segments, he describes OpenCode’s paid options like this:[1]

- There are **two plans**: “the Zen one” and “the Go, the cheaper one.”[1]
- Zen: “gives you access to multiple optimized models for development and coding.”[1]
- Go: “the cheaper one which gives you access to models.”[1]
- Pricing: “start $5 for the first month and after that it’s $10 afterwards.”[1]
- Benefits he calls out: access to Kimi K2 and newly added DeepSeek V4 Pro, plus a “really good quota” including the Flash model used as a coding assistant.[1]

But he never reads out or shows a specific marketing URL like `opencode.com/pricing` in the transcript.[1]

## Do you have to use DeepSeek with OpenCode?

No. Based on his own workflow description:[1]

- He first shows using DeepSeek directly via **DeepSeek’s own site and API keys**, funded with a prepaid balance; that is completely independent of OpenCode.[1]
- OpenCode is just one of “various platforms” where you can paste that API key to use DeepSeek as a provider (alongside NVIDIA and some built‑in free models).[1]
- He explicitly says OpenCode also has its **own plans** (Zen/Go) that bundle access to models like Kimi K2 and DeepSeek V4 Pro, but those are optional.[1]

So:

- To use DeepSeek: you can use their web chat or API directly; OpenCode is not required.[1]
- To use the **OpenCode subscription** he mentions: you’d need to sign up through OpenCode’s own site or app UI, but the exact URL is not given in this transcript.[1]

If you’d like, I can help you infer the likely URL pattern and suggest a quick way to confirm it safely in your browser without chasing the wrong “OpenCode” product.

## Human

can you search the web for the url?

## Assistant

Yes. The official pages for the OpenCode plans he mentions are:

- **OpenCode Go** (the $5 first month, then $10/month plan): [https://opencode.ai/docs/go/][1]
- **OpenCode Zen** (pay‑per‑use gateway with multiple premium models): [https://opencode.ai/zen] and its detailed docs at [https://opencode.ai/docs/zen/][2][3]

From OpenCode’s own docs, **Go** is a low‑cost monthly subscription that gives you reliable access to a curated set of coding models, currently described as “$5 for your first month, then $10/month.” **Zen** is a separate pay‑as‑you‑go product where you prepay balance and are billed per model token usage (including models like Kimi K2.x, GLM 5.x, Qwen, etc.).[3][4][2][1]

You **do not have to use DeepSeek via OpenCode** at all:  
- DeepSeek itself exposes a direct API and web UI that you can hit with your own keys, completely independent of OpenCode.[5]
- OpenCode Go/Zen are just **one** way to access DeepSeek (and other models) from within their coding agent/IDE; they bundle routing, auth, and quotas but are optional.[6][3][1]

If your main goal is “DeepSeek for agents and coding,” are you leaning toward (a) centralizing everything through OpenCode’s gateway, or (b) keeping separate direct API keys per provider and wiring them into your own orchestrator?

## Human

but can I use 'go' or 'zen' without opencode?

## Assistant

Yes, you can use both **Go** and **Zen** outside of the OpenCode app/CLI.

## Go

From the official Go page:[1][2]

- Go is a **subscription**: “$5 for your first month, then $10/month.”[2][1]
- It gives you an **API key** plus OpenAI‑compatible / Anthropic‑compatible endpoints like `https://opencode.ai/zen/go/v1/chat/completions` and `.../v1/messages`.[1]
- The marketing page explicitly says: “You can use it **with OpenCode or any agent**.”[2]

So you can plug the Go API key into:

- Your own Node/Python agents (anything that speaks OpenAI/Anthropic style APIs).  
- Other tools like Claude Code, custom backends, etc.[3][1]

You do **not** have to run the OpenCode client to benefit from Go; OpenCode is just one recommended integration.[2]

## Zen

From the Zen docs and landing page:[4][5][6]

- Zen is an **AI gateway** with a curated list of tested models and its own API key.  
- Docs describe it as “works like any other provider in OpenCode” but also clarify it is just a standard HTTP API.[5][4]
- The Zen landing page: “While we suggest you use Zen with OpenCode, you can use Zen with **any agent**.”[6]

You:

1. Sign up at Zen, add balance/billing, and create an API key.[4][6]
2. Call its REST endpoints from any app, or wire it through routers like Mastra, LLM Gateway, etc.[7][5][6]

So again, OpenCode is **not required**; it is their first‑party client, but Zen is just a general‑purpose gateway.

## Practical takeaway

- **Go**: cheap fixed‑price bundle of specific coding models, usable anywhere via standard API key.[1][2]
- **Zen**: pay‑per‑use gateway with a broader curated model list, again usable anywhere.[6][4]
- **OpenCode client**: optional; helpful UX, but not technically necessary to consume either product.

Given your stack, the key design question is whether you’d rather integrate a single OpenCode key into your orchestrator as a “meta‑provider,” or keep providers (DeepSeek, Kimi, etc.) separate. Are you currently routing models through a central gateway (e.g., OpenRouter, custom proxy), or calling each provider directly from your agents?  
