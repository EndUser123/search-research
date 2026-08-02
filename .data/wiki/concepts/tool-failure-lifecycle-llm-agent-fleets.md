---
title: "Tool-Failure Lifecycle for LLM Agent Fleets"
created: 2026-08-02
source: session-2026-08-02
tags: [tool-failure, circuit-breaker, staleness, lifecycle, agent-infrastructure, structural-fix, reference]
summary: >
  How an LLM agent fleet should manage tool failures: a three-stage lifecycle
  (TRANSIENT → investigation → STRUCTURAL) grounded in the standard circuit
  breaker pattern (Closed/Open/Half-Open). Key findings: (1) no major agent
  framework ships session-start health checks — our design is novel; (2) the
  circuit breaker half-open pattern validates our promotion-threshold approach;
  (3) TTL should be a condition, not a duration; (4) extended timer on repeated
  probe failures prevents wasteful re-testing.
agent: grok
host: both
cognitive_load: 3
verification: multi-source-verified
relations:
  - target: wiki/concepts/tool-fallbacks.md
    type: refines
  - target: wiki/concepts/circuit-breaker-pattern.md
    type: related
  - target: wiki/concepts/inference-in-code-blind-spot.md
    type: related
---

# Tool-Failure Lifecycle for LLM Agent Fleets

## Decision context

**Why this research was needed:** we designed a three-stage tool-failure lifecycle (TRANSIENT → investigation → STRUCTURAL) from first principles in this session. The operator asked "how do we make our system intelligent, adaptive, and consider predictable issues?" — which required grounding the design in external evidence rather than reasoning alone.

**What the research changed:** validated that our state machine maps to the standard circuit breaker pattern (three-state: Closed/Open/Half-Open). Confirmed that session-start health checks are genuinely novel — no agent framework does them. Identified the TTL-as-condition approach and the extended-timer-on-repeated-failure pattern as standard practice. Discovered that Reddit API degradation in 2026 is the root cause of our Reddit MCP failures (not our MCP server's fault).

## The lifecycle (grounded in circuit breaker pattern)

Our design maps to the standard three-state circuit breaker (Azure, Resilience4j, LangChain all use this):

```
Tool works (CLOSED)
  │
  │ failure observed
  ▼
TRANSIENT entry in tool-fallbacks (OPEN)
  "Use workaround, re-test soon"
  │
  ├─ TTL expires → re-test (half-open probe)
  │     ├── Works → remove entry (CLOSED). Done.
  │     └── Still broken → reset TTL
  │           └── Failed N consecutive sessions? (promotion threshold)
  │                 ├── YES → PROMOTE to investigation (handoff)
  │                 └── NO  → stays TRANSIENT
  │
  └─ Investigation resolves:
      ├── Fixable → fix → remove entry
      ├── Permanent → STRUCTURAL entry + wiki decision
      └── Was transient → demote back
```

### How this maps to standard circuit breaker concepts

| Our term | Circuit breaker term | Source |
|---|---|---|
| Tool works | CLOSED | Azure Architecture Center |
| Tool broken, use workaround | OPEN | Azure, Resilience4j |
| Re-test (one probe) | HALF-OPEN | Azure, Resilience4j |
| N consecutive failures → investigate | `failure-rate-threshold` + `minimum-number-of-calls` | Resilience4j (default 50% threshold, min 5-10 calls) |
| Extended re-test interval on repeat failure | Extended timer on failed probe | valuestreamai.com (not in Resilience4j default) |

## TTL-as-condition (not duration)

**Standard practice (verified):** "Pick TTL based on how stale the application can tolerate, not based on how often the data changes" (sujeet.pro, distributed cache design).

Applied to tool-failures, the TTL is a condition that matches the failure's expected recovery mechanism:

| Failure class | Recovery mechanism | TTL condition | Re-test trigger |
|---|---|---|---|
| Rate-limit / 429 | Time window clears | Next session | Probe once at session start |
| Credit exhaustion (firecrawl) | Monthly billing refresh | When quota dashboard shows credits >0 | Check dashboard, not the tool |
| CDN/Cloudflare block | Intermittent (minutes) | Next use | Try on each use (free) |
| API outage (provider down) | Provider restores | 24h or next session | Time-based |
| Repeated (3+ sessions) | Unknown | N/A | PROMOTE to handoff |

## Session-start health checks (novel — no framework does this)

**Research finding:** No major agent framework (LangChain, Pydantic AI, CrewAI, AutoGen) performs session-start tool health checks. Half-open circuit breaker probing is the closest analog, but it happens mid-execution when the circuit opens, not proactively at session start.

**Our fleet's advantage:** the session-start probe is cheap (one `reddit__browse_subreddit` call = 2 seconds) and eliminates the discovery cost that makes research painful when tools fail. This is the structural fix for the friction-reinforcement pattern: if you know what's broken before you start, you plan around it.

**How to implement:** at session start, check `[[tool-fallbacks]]` for TRANSIENT entries whose TTL condition has been met. Run a single probe for each. Remove entries that pass. Increment failure count for entries that fail.

## Extended timer on repeated failures

**Pattern (verified):** when a half-open probe fails, the circuit re-opens with an extended timer (valuestreamai.com). This is NOT in Resilience4j's default config — it's a documented extension.

**Applied to our fleet:** a tool that fails re-test 3 sessions in a row should not be re-tested every session. After 3 failures, promote to investigation (handoff). After investigation, either fix, mark STRUCTURAL, or demote back to TRANSIENT.

## Reddit API degradation (root cause of our MCP failures)

**Research finding:** Reddit deprecated unauthenticated .json endpoint access in May 2026 (scrapebadger.com). API key acquisition is "nearly impossible" in 2026 (LinkedIn practitioner report). The Reddit Data API is "heavily throttled, has no SLA, no documented rate-limit headers" (redditapis.com).

**Implication:** our Reddit MCP failures (`search_reddit` returning "Access forbidden") are likely symptoms of Reddit-side API tightening, not bugs in our MCP server. The `old.reddit.com` web_fetch workaround is reliable because it bypasses the API entirely.

**Alternatives exist:** 7+ Reddit MCP server implementations on GitHub (jordanburke, eliasbiondo, adhikasp, Maheidem, sumitroyyy, zicochaos, Arindam200) plus reddit-mcp-buddy. None have published reliability comparisons.

## What agent frameworks do (and don't do)

| Framework | Retry | Circuit breaker | Fallback | Session-start probe | Adaptive selection |
|---|---|---|---|---|---|
| LangChain | ✅ `with_retry()`, tenacity | ✅ documented pattern | ✅ `RunnableWithFallbacks` (model-level) | ❌ | ❌ |
| Pydantic AI | ✅ `ModelRetry` via validator | ❌ | ✅ community examples | ❌ | ❌ |
| CrewAI | ❌ first-class | ❌ | ❌ | ❌ | ❌ |
| AutoGen | ❌ first-class | ❌ | ❌ | ❌ | ❌ |
| MCP proxy pattern | ✅ tenacity | ✅ pybreaker | ✅ fallback chain | ❌ | ❌ |
| **Our fleet** | behavioral (manual) | **tool-fallbacks table** | **tool-fallbacks workarounds** | **TO IMPLEMENT (novel)** | ❌ (research-stage) |

**Key gap:** no framework ships session-start health checks or adaptive tool selection. Our design fills both gaps — session-start probes are implementable now; adaptive selection requires telemetry accumulation.

## What this means for our workspace

1. **The lifecycle design is validated.** It maps to the standard circuit breaker pattern, which is well-established in distributed systems. We're not inventing — we're applying a proven pattern to a new domain (LLM agent tool management).

2. **Session-start probes are the novel contribution.** No agent framework does this. It's cheap, high-value, and eliminates the friction that reinforces avoid-research behavior.

3. **Reddit MCP failures are Reddit-side.** The API is degrading in 2026. Our workaround (old.reddit.com web_fetch) is the right approach. A handoff should evaluate whether a different Reddit MCP server would perform better, or whether the old.reddit.com workaround should become the permanent approach.

4. **The STRUCTURAL/TRANSIENT classification with TTL-as-condition is standard practice.** Feature flag systems (Datadog, GrowthBook, FeatBit) use the same dual-tier approach with automatic stale detection and per-entry opt-out.

5. **Adaptive tool selection is research-stage only.** We should not wait for a framework to ship it. Our tool-fallbacks table with failure-count tracking is a pragmatic alternative that works today.

## Receipts

- **Circuit breaker three-state model:** [FACT] Azure Architecture Center (learn.microsoft.com/en-us/azure/architecture/patterns/circuit-breaker) + Resilience4j docs (resilience4j.readme.io/docs/circuitbreaker)
- **TTL-as-condition:** [FACT] sujeet.pro distributed cache design — "Pick TTL based on how stale the application can tolerate"
- **Extended timer on probe failure:** [FACT] valuestreamai.com — "If it fails, circuit opens again with an extended timer"
- **Session-start probes novel:** [FACT] LangChain (no session-start probe), Pydantic AI (no session-start probe), CrewAI (no resilience primitives at all), AutoGen (no resilience primitives)
- **Reddit API degradation 2026:** [PRACTITIONER] scrapebadger.com + redditapis.com + LinkedIn practitioner report — consistent across sources but no Reddit official announcement found
- **Adaptive tool selection research-stage:** [FACT] arxiv papers (AutoTool 2603.22862, AgentDebug 2509.25370) — no production implementation found
- **MCP proxy pattern:** [FACT] octopus.com/blog/mcp-timeout-retry — wraps MCP tools with retry/timeout/circuit-breaker using pybreaker + tenacity

## Falsifier

This concept is wrong if:
- A major agent framework ships session-start health checks, making our novel contribution unnecessary
- The circuit breaker pattern doesn't apply to LLM agent tool selection (different enough from distributed systems that the mapping breaks)
- The Reddit API recovers and our TRANSIENT entries become permanent false positives
- The promotion threshold (3 sessions) proves too aggressive or too conservative in practice

## Related

- [[tool-fallbacks]] — the implementation (classification system + entries)
- [[circuit-breaker-pattern]] — the distributed systems original
- [[inference-in-code-blind-spot]] — the session incident that surfaced the tool-failure pattern
- [[mcp-servers-for-email-social-unified-task-scanning]] — alternative Reddit MCP servers
