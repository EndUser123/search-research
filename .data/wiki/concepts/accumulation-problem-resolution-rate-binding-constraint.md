---
title: "Accumulation Problem — Resolution Rate Is the Binding Constraint"
created: 2026-08-01
source: session-2026-08-01
tags: [harvest, handoffs, obligations, discovery-vs-resolution, fleet-health, binding-constraint]
summary: >
  The fleet's bottleneck is not discovery (it excels at finding problems, writing wiki
  concepts, and creating handoffs) — it is resolution. The system produces obligations
  10x faster than it closes them. Evidence: 85% harvest open rate, 213 open handoffs
  (137 from last 7 days). The fix is a burn-down session and a discovery-to-resolution
  ratio target, not more investigation.
agent: grok
host: grok
cognitive_load: 2
verification: local-only
tier: warm
---

# Accumulation Problem — Resolution Rate Is the Binding Constraint

## The finding

Three independent scans from session 019f9a89 (2026-08-01) converged on the same signal:

| Metric | Value | Source |
|--------|-------|--------|
| Harvest open rate | 29 OPEN / 34 total = **85%** | `harvest.py doctor` |
| Open handoffs | **213** (137 from last 7 days = 64%) | `coverage_scan.py` |
| Discovery-to-resolution ratio | ~**10:1** (estimated) | Derived from open:closed ratios |
| Wiki concepts per session | ~10+ | `/capture` scan |

The fleet discovers problems, documents them, and creates obligations at a rate
far exceeding its closure rate. This is not a stale-tail problem — 64% of open
handoffs are from the last 7 days, meaning the current trajectory is the problem.

## Why this matters

Each unclosed obligation has a cost:
- **Triage cost**: every future session must scan past stale items to find actionable work
- **Misrouting cost**: stale handoffs referencing moved/deleted files misroute fresh sessions
- **Cognitive load**: 213 open handoffs is beyond human triage capacity
- **Investigation-theater risk**: the pattern of producing durable artifacts (wiki concepts, handoffs) as a substitute for structural fixes. Already documented in `[[analysis-over-action-pattern-knowledge-capture-without-application]]`.

## The /tp critique that surfaced it

A fresh-subagent /tp critique of the session's proposed next steps challenged the
recommendation to "investigate rule-firing compliance first":

> "91% harvest open rate — the system produces obligations 10x faster than it closes
> them. Investigating rule-firing continues an investigation-theater pattern. Ship a
> fix, don't write another wiki concept."

The critique forced a plan revision: from investigation-first to triage-first.

## Structural fix: discovery-to-resolution ratio

**Proposal:** adopt a soft guideline (not yet an AGENTS.md rule) of **1:1
discovery-to-resolution** — for every new handoff opened, close one existing one.

This is distinct from:
- **Throughput optimization** (making the fleet faster at discovery) — that's the wrong direction
- **Quality reduction** (fewer handoffs) — the discovery is valuable; the problem is resolution
- **Forced closure** (closing items without verification) — that violates the receipt rule

## Related concepts

- [[analysis-over-action-pattern-knowledge-capture-without-application]] — the behavioral pattern this finding names at the system level
- [[mechanical-enforcement-over-behavioral-reminder]] — structural fixes over prose
- [[harvest]] — the obligation tracking system whose data surfaced this finding

## Falsifier

This finding is wrong if:
- The 213 open handoffs are mostly still valid and actionable (not stale)
- The harvest open rate self-corrects as the fleet matures (no evidence of this yet)
- The operator's actual priority is discovery, not resolution (then accumulation is acceptable)

If a burn-down session closes 50+ items easily, the problem was backlog, not throughput.
If a burn-down session closes <5 items because each requires substantial work, the problem
is genuinely a throughput mismatch and the ratio target is the correct structural fix.
