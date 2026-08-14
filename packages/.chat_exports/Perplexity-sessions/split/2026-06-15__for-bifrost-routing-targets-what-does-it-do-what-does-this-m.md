---
title: "for bifrost routing targets, what does it do?  what does this mean?  Weights must sum to 1. Leave provider or model empt"
date: "2026-06-15"
mode: "COPILOT"
uuid: "b3c93c46-c056-44ed-b276-21248ab311a3"
entry_count: 3
---

## Human

for bifrost routing targets, what does it do?  what does this mean?  Weights must sum to 1. Leave provider or model empty to use the incoming request value.

## Assistant

In Bifrost routing targets, that line means each target is one possible destination for the request, and Bifrost picks among them probabilistically using the listed weights. The weights are relative probabilities and must add up to 1.0, while leaving `provider` or `model` blank tells Bifrost to keep the incoming request’s original value for that field.[1][2]

## What it does

A routing rule can define multiple targets, such as OpenAI 70% and Azure 30%, so matching requests are split across those destinations at request time. This is used for weighted load balancing, A/B testing, canaries, or cost distribution, and the selection happens before governance provider selection when a routing rule matches.[1]

## What “weights must sum to 1” means

If you define two targets with weights `0.7` and `0.3`, that is a valid split because the total is `1.0`. If the weights do not add to `1.0`, the config is invalid or at least not in the intended format described by the docs, because the weights represent probabilities rather than arbitrary scores.[1]

## What “leave provider or model empty” means

If you omit `provider`, Bifrost keeps the provider from the incoming request; if you omit `model`, Bifrost keeps the incoming model. That lets a rule change only one part of the destination, such as “same model, different provider” or “same provider, different model,” without rewriting the whole request.[1]

## Example

If the incoming request is `model=gpt-4o` and your targets are:

- `provider=openai, model empty, weight=0.7`
- `provider=azure, model empty, weight=0.3`

then Bifrost will send 70% of matching requests to OpenAI and 30% to Azure, while preserving the incoming model name in both cases. If instead you set `provider=openai, model=gpt-4o-mini`, then the rule can redirect only that matched traffic to a different model on OpenAI.[1]

## Practical reading

Think of the routing target as a patch, not a full replacement. Missing fields mean “inherit from the request,” and weights mean “how often should this patch win when multiple targets are available”.[1]

## Human

how long does the target last for?  will prompt caching work?

## Assistant

The target does not “last” across requests by itself; Bifrost evaluates the routing rule per request, then picks a target for that request based on the configured weights. So the practical lifetime is one request, unless the same request is retried through a fallback chain.[1]

## What that means

For weighted routing, each matching request is independently assigned to a target according to the weights, and the docs say weights are normalized to sum to 1.0 for the providers available to that model. That means the routing decision is probabilistic per request, not sticky or session-based.[1]

## Prompt caching

Yes, prompt caching can still work, but only if the underlying provider supports it and the routed request preserves the same cache-relevant prefix and parameters. Bifrost itself does not appear to create a special “target lifetime” that would preserve cache state; it forwards the request to the selected provider, so cache behavior depends on the provider-side caching mechanism and whether the routed request is byte-identical where required.[2][3][4]

## Practical implications

If Bifrost routes the same prompt to different providers, provider-side prompt caching will usually not be shared across providers, because each provider maintains its own cache semantics. If Bifrost keeps routing the same traffic to the same provider and the cache prefix is stable, caching should benefit as usual.[3][4][2]

## Safe assumption

Treat Bifrost routing as changing the destination per request, while prompt caching lives at the provider layer, not the routing-target layer. The main uncertainty is whether your specific provider and model support the exact caching mode you want, since cache rules differ by vendor and model family.[4][2][3][1]

## Human

how to implement sticky sessions for model routing targets

## Assistant

Bifrost does not provide native sticky sessions for routing targets in the docs I found; its weighted routing is explicitly per-request and non-sticky by default. So if you want a client to keep hitting the same model/provider target, you need to add stickiness **outside** Bifrost or via a custom routing layer in front of it.[1][2]

## Practical ways to do it

1. Use a client/session ID and store the chosen target in your own session map, then inject the resolved `provider/model` on subsequent requests. That is the most direct way to make routing deterministic per session, because Bifrost will otherwise re-pick on each request.[2][1]

2. Put sticky routing in a reverse proxy or load balancer in front of Bifrost using a cookie or header-based affinity rule. That is the common sticky-session pattern in load balancers: the proxy remembers the assignment and keeps sending the same client to the same upstream target.[3][4]

3. If you control the app, include a stable tenant/user/session key and hash it to a target deterministically. This gives you “sticky enough” behavior without server-side session state, but you must manage rebalancing and target failures yourself.

## What to implement

A simple design is:

- Generate or reuse a `session_id`.
- Hash `session_id` to one of your candidate targets.
- Persist `session_id -> target` in Redis, a DB, or an in-memory cache with TTL.
- On each request, resolve the stored target and send an explicit `provider/model` to Bifrost.
- If the target becomes unhealthy, invalidate the mapping and reassign.

That approach works well because Bifrost already accepts explicit `provider/model` routing, and its docs note that weighted routing is only used when a request is not already directed to a specific provider/model.[2]

## Prompt caching impact

Sticky sessions can improve cache hit rates if the cache is provider-specific and the same session keeps going to the same provider/model. But stickiness is not a guarantee of prompt-cache reuse, because cache keys still depend on the exact request shape, model, and provider behavior.[5][6][7]

## Recommended default

For most setups, use deterministic session-to-target mapping only for workloads that truly need affinity, such as long-running conversations or provider-specific context windows. For everything else, let Bifrost keep doing per-request weighted selection, because that preserves balancing and failover behavior.[1][2]
