---
title: "Multi-agent and fleet coordination: domain overview"
created: 2026-08-02
source: session-2026-08-02-wiki
tags: [multi-agent, fleet, coordination, domain-overview]
summary: >
  Index of 55 wiki concepts related to multi-agent coordination, fleet
  management, isolation, and concurrency. Grouped into 5 sub-themes:
  Fleet Architecture, Isolation & Concurrency, Failure Modes, MCP & Tool
  Sharing, and Coordination Patterns. The strongest external validation
  comes from the MAST taxonomy (NeurIPS 2025) and practitioner reports.
agent: grok
host: grok
cognitive_load: 2
verification: local-only
---

# Multi-agent and fleet coordination: domain overview

## Decision context

This workspace operates a fleet of concurrent LLM agents on a shared Windows
filesystem. The wiki accumulated 55 concepts tagged `multi-agent`, `fleet`,
or `coordination` — this overview makes the domain navigable.

## Sub-theme 1: Fleet Architecture (model pools, routing, coordination)

| Concept | One-line summary |
|---|---|
| [[solo-director-ai-fleet-coordination-isolation-best-practices]] | Core isolation patterns: worktrees, surgical git add, per-session state |
| [[agent-skills-fleet-patterns-solo-director-2026]] | 2026 fleet architecture patterns researched from external sources |
| [[model-fleet-provider-pools]] | Provider pools, access tiers, and selection flow |
| [[model-pool-not-chain]] | Qualified-pool routing vs linear fallback |
| [[model-lanes-vs-roles]] | 2-lane routing framework (mechanical vs reasoning) |
| [[execution-path-based-model-routing-grok-build]] | Quota-aware model routing |
| [[model-picker-as-failover-not-router]] | Model picker as failover, not primary router |
| [[model-quota-contention-coordination-fleet-rate-limiting]] | Proactive rate-limit avoidance |
| [[fleet-benchmark-results-2026-07-29]] | Coding/reasoning/streaming benchmark matrix |
| [[model-role-assignment-public-vs-custom-benchmarks]] | Public vs custom benchmarks for fleet ranking |
| [[llm-council-and-model-fusion]] | MoA, OpenRouter, Karpathy fusion patterns |

## Sub-theme 2: Isolation & Concurrency (worktrees, file editing, shared state)

| Concept | One-line summary |
|---|---|
| [[git-worktree-multi-terminal-best-prategies]] | Worktree isolation for concurrent agents |
| [[file-edit-failures-two-classes]] | Class A (persistence) vs Class B (collision) failures |
| [[invariants-beat-environment-comfort]] | Host invariants override generic best practices |
| [[multi-terminal-shared-state-contamination-transport-mismatch]] | Concurrent session cleared serde_broken list |
| [[concurrent-cdp-auth-contention]] | CDP session invalidation across terminals |
| [[mcp-server-sharing-multi-terminal]] | MCP server sharing patterns on Windows |
| [[grok-permission-deny-rules-cross-host-protection]] | Permission deny rules as cross-host protection |
| [[external-silent-edit-and-shell-quoting-reports]] | Class C quoting failures |
| [[git-mv-search-replace-capture-bug]] | Git mv + search_replace content loss |

## Sub-theme 3: Failure Modes (cascading errors, destructive operations, races)

| Concept | One-line summary |
|---|---|
| [[multi-agent-coordination-failure-modes-practitioner-and-research-2026]] | **NEW** — MAST taxonomy (79% spec+coordination), practitioner "keep it simple" |
| [[multi-agent-system-failure-modes]] | Academic overview of 7 failure modes |
| [[multi-agent-correlated-errors]] | Attack correlated errors, not persona diversity |
| [[multi-agent-destructive-git]] | Force-push/reset categorically wrong on shared repos |
| [[multi-agent-transcript-race-condition-check-preprocessor]] | Race condition in /check preprocessor |
| [[accumulation-problem-resolution-rate-binding-constraint]] | Resolution rate is the binding constraint |
| [[handoff-fragmentation-under-recurrence]] | Single-writer produces N authoritative files |
| [[hook-fleet-io-failure-modes-cascade-amplification]] | Cascade amplification in verification gates |

## Sub-theme 4: Coordination Patterns (handoffs, delegation, parallel execution)

| Concept | One-line summary |
|---|---|
| [[llm-handoff-best-practices]] | Typed ownership field on multi-agent handoffs |
| [[delegation-optimization-chunking-output-backend-discipline]] | Chunking, routing, cascading, coordination cost |
| [[parallelizing-design-doc-generation-what-works]] | Map-reduce, multi-agent, multi-candidate |
| [[tp-parallel-improvement-solution-space]] | Parallel /tp improvement design paths |
| [[improvement-surfacing-fleet-fragmentation-routing-and-meta-improvement]] | Fragmentation, routing, meta-improvement layer |

## Sub-theme 5: Fleet Management & Maintenance

| Concept | One-line summary |
|---|---|
| [[fleet-maintenance-skill-design]] | What a fleet maintenance skill should look like |
| [[fleet-wide-friction-taxonomy-20260728]] | Recurring friction patterns from AAR/handoff corpora |
| [[fleet-quota-api-discovery-2026]] | All provider quota API endpoints |
| [[perplexity-quota-structure-pro-plan-2026]] | Verified Perplexity quota pools |
| [[enforcement-vs-fleet-hygiene-attestation-deferred]] | Why attestation was deferred from close-authority |
| [[silently-dead-hooks-pgm-payload-bug-fleet-monitoring-gap]] | Dead hooks went undetected for weeks |
| [[serde-broken-false-positive-sweep-20260801]] | Model health registry was 100% false positives |
| [[test-design-falsification-of-production-components]] | Flawed test flagged working model as broken |

## What this means for our workspace

The multi-agent domain is the wiki's largest operational domain (55 concepts). The highest-value external validation is the MAST taxonomy finding that 79% of failures come from specification ambiguity and coordination breakdowns — directly validating our handoff format and isolation model. The practitioner signal ("keep it offensively simple") validates the single-writer-per-worktree pattern.

## Evidence

This is a reference/index document — no mechanism claims about local code.
Concept counts derived from tag scan (`P:/tmp/concept_enumerate.py`, 2026-08-02).
External validation cited from MAST taxonomy (NeurIPS 2025) and Reddit
practitioner reports linked in [[multi-agent-coordination-failure-modes-practitioner-and-research-2026]].

## Falsifier

This overview is stale when new multi-agent concepts are added without updating it. Run `/wiki multi-agent-domain-overview` to regenerate.

## Related

- [[design-patterns-domain-overview]] — the companion enforcement/trigger domain overview
- [[prose-rules-vs-structural-enforcement-research-2026]] — the governance layer

## Auto-related

- [[skill-graph]]
- [[portable-ai-brain-pattern]]
- [[skill-catalog]]
- [[solo-director-ai-fleet-coordination-isolation-best-practices]]
- [[multi-agent-system-failure-modes]]

