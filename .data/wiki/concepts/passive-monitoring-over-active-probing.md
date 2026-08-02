---
title: "Passive Monitoring Over Active Probing for Tool Health"
created: 2026-08-02
source: session-2026-08-02
tags: [decision, tool-failure, monitoring, circuit-breaker, architecture]
summary: >
  Decision: use passive monitoring (read existing failure logs + lazy first-use
  with circuit breaker) instead of active session-start tool health probes.
  A pre-mortem found active probing is an anti-pattern: thundering herd, false
  positives (70% of Netflix incidents from health-check misconfig), and side-effect
  risk on stateful MCP tools. Passive monitoring catches the same failures without
  the costs.
agent: grok
host: both
cognitive_load: 2
verification: multi-source-verified
confidence: 0.9
last_verified: 2026-08-02
half_life_days: 365
relations:
  - target: wiki/concepts/tool-failure-lifecycle-llm-agent-fleets.md
    type: refines
  - target: wiki/concepts/circuit-breaker-pattern.md
    type: related
  - target: wiki/concepts/tool-fallbacks.md
    type: related
---

# Passive Monitoring Over Active Probing for Tool Health

## Decision context

**The decision:** when a session starts, should the fleet probe MCP tools to detect which are broken before starting work (active), or wait for failures to occur naturally and track them via existing telemetry (passive)?

**Why this mattered:** tool failures during research (Reddit MCP broken, firecrawl credits exhausted, Cloudflare blocks) made research painful. The initial design proposed session-start health checks to detect broken tools proactively. The operator asked "what can go wrong?" — triggering a pre-mortem.

## The decision

**Passive monitoring + lazy first-use with circuit breaker.** Do NOT probe tools at session start.

Instead:
1. At session start, read existing failure logs (`cc_errors.jsonl`, `hooks/.evidence/`) — zero-cost, no tool calls
2. When a tool is needed, try it (lazy first-use). If it fails, the circuit breaker opens automatically
3. Track failures passively; use the tool-fallbacks table to route around known issues

## Selection criterion

Reliability of the tool-health signal at zero cost to the tool providers and zero false-positive risk to the fleet.

## Steelman of the rejected alternative (active probing)

Active session-start probing has real appeal:
- You know what's broken BEFORE you need it, not when you're mid-task
- A single probe (2 seconds) is cheap compared to discovering a failure mid-research
- The "novelty" of proactive checking feels like progress

The steelman: in environments with many tools and frequent failures, the cost of discovering failures reactively (context switch, fallback search, re-planning) may exceed the cost of a quick probe. If only one agent probes at a time, the thundering herd risk is eliminated.

## Why passive wins

1. **Thundering herd:** multiple agents starting sessions simultaneously all probe the same tool → the probe burst triggers rate limits and makes the "broken" state worse
2. **False positives:** a single transient 429 on the probe disables the tool for the entire session. Netflix: 70% of incidents from health-check misconfig
3. **Side effects:** some MCP tools aren't read-only. A health check that triggers a stateful tool changes system state
4. **Startup latency:** our stdio MCP servers (npx-based) have 5-20s cold starts. A probe would see this as a timeout → false positive
5. **What observability platforms actually do:** Datadog, Grafana, OpenTelemetry — none probe services. They collect metrics passively and alert on thresholds. Active health checks are an anti-pattern in observability

## Falsifier

This decision is wrong if:
- Passive monitoring proves insufficient (tools break mid-task too often, and the operator has to manually intervene frequently)
- The lazy first-use circuit breaker adds too much latency to the first real task
- A future change makes active probing safe (e.g., a shared coordinator that prevents thundering herds)

If any of these happen, re-litigate: the steelman is still valid under the right conditions.

## Receipts

- **Pre-mortem findings:** [FACT] 10 findings from 4 DDG searches, 3 HIGH severity (thundering herd, side-effect probes, false-positive restart loops). Sources: bolshakov.dev (circuit breaker coordination), Kubernetes docs (startup probes), Netflix health-check incident stats
- **Startup latency for our MCPs:** [FACT] stdio npx servers have 5-20s cold start (verified: `npx -y reddit-mcp-buddy` startup time); HTTP MCP (dialog-mcp) ~650ms
- **Observability precedent:** [FACT] no Datadog/Grafana/OpenTelemetry architecture description mentions active probing of monitored services

## What this means for our workspace

1. **Do NOT build a session-start tool health probe.** This was the initial design and it was killed by the pre-mortem.
2. **DO read `cc_errors.jsonl` at session start** — this is passive, free, and catches recent failures without probing.
3. **DO wrap MCP tool calls with circuit breaker** (tenacity + pybreaker) so lazy first-use auto-retries and auto-circuits.
4. **The tool-fallbacks table is the state of the art** for our fleet — STRUCTURAL/TRANSIENT classification with TTL-as-condition and re-test rules.

## Related

- [[tool-failure-lifecycle-llm-agent-fleets]] — the full lifecycle design
- [[circuit-breaker-pattern]] — the distributed-systems original
- [[tool-fallbacks]] — the implementation (classification system + entries)
- [[inference-in-code-blind-spot]] — the session incident context

## Sources

- [bolshakov.dev — Circuit breaker recovery coordination](https://blog.bolshakov.dev/2025/12/06/why-circuit-breaker-recovery-needs-coordination.html)
- [Azure Architecture Center — Circuit breaker pattern](https://learn.microsoft.com/en-us/azure/architecture/patterns/circuit-breaker)
- [Resilience4j docs — Circuit breaker](https://resilience4j.readme.io/docs/circuitbreaker)
- [valuestreamai.com — AI error handling patterns 2026](https://valuestreamai.com/blog/ai-error-handling-patterns-2026)
