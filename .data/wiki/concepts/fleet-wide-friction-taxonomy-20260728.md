---
title: "Fleet-wide friction taxonomy: recurring patterns across AAR and handoff corpora"
created: 2026-07-28
source: session-019fa94a (corpus mining)
tags: [friction-patterns, fleet-management, aar-mining, handoff-mining, artifacts-not-invocations, cross-session]
summary: >
  Mechanical scan of 20 AAR reports and 193 handoff files for recurring friction
  patterns. Surfaces the top 10 friction classes by frequency across the corpus,
  with file counts and hit totals. The dominant pattern by far is closure-pressure
  (118 hits / 43 files), followed by gitignore-related issues (56 hits / 14 files)
  and deferred-persistence (29 hits / 15 files). This taxonomy is the input for
  prioritizing which friction classes deserve structural fixes vs which are
  already adequately addressed.
agent: grok
host: grok
cognitive_load: 2
verification: observed
relations:
  - target: wiki/concepts/reactive-pattern-matching-and-closure-pressure.md
    type: quantifies
  - target: wiki/concepts/held-out-data-already-on-disk-count-artifacts-not-invocations.md
    type: extends
  - target: wiki/concepts/deferred-skill-improvements-registry.md
    type: related
---

# Fleet-wide friction taxonomy: recurring patterns across AAR and handoff corpora

## Decision context

**Why this was needed:** the artifacts-not-invocations pattern (discovered this
session) revealed that held-out validation data is already on disk. This scan
applies that pattern to the AAR (20 reports) and handoff (193 files) corpora to
identify which friction classes are recurring across sessions and deserve
structural attention vs which are one-offs already addressed.

No prior scan has aggregated friction patterns across the full corpus. Individual
AARs and session observations capture per-session friction; this is the first
cross-corpus aggregation.

## Methodology

Mechanical regex scan of all AAR reports (`P:/.artifacts/grok-aar/`) and all
handoff files (`P:/docs/handoffs/*/HANDOFF.md`) for 12 friction keyword patterns.
The patterns are derived from known failure modes documented in AGENTS.md and
prior wiki concepts. This is a frequency count, not a severity assessment —
severity requires reading the context, which this scan does not do.

## Results: friction pattern ranking

| Rank | Pattern | Total hits | Files affected | Already in wiki? |
|---|---|---|---|---|
| 1 | **closure-pressure** | 118 | 43 | ✅ [[reactive-pattern-matching-and-closure-pressure]] |
| 2 | **gitignore** (grep false negatives, path issues) | 56 | 14 | ✅ this session's AGENTS.md fix |
| 3 | **deferred-persistence** | 29 | 15 | ✅ no-deferred-persistence (AGENTS.md rule) |
| 4 | **stale-read** (reading outdated file state) | 24 | 14 | ✅ file-editing-protocol |
| 5 | **hook-timeout** | 19 | 10 | ⚠️ partially — documented per-hook, no fleet pattern |
| 6 | **shell-quoting** | 17 | 10 | ✅ Class C in AGENTS.md file-editing-protocol |
| 7 | **narrative-sufficiency** (plausible story as fact) | 17 | 10 | ✅ claims-require-receipts |
| 8 | **python-c** (inline Python with nested quotes) | 12 | 10 | ✅ Class C in AGENTS.md |
| 9 | **concurrent-edit** (multi-agent collision) | 12 | 11 | ✅ file-editing-protocol |
| 10 | **model-serde** (serialization failures) | 8 | 4 | ✅ [[model-tool-calling-capability-matrix]] |

**Key observation:** 9 of the top 10 friction classes already have wiki concepts
or AGENTS.md rules. The friction is still recurring despite documentation — which
means documentation alone is insufficient for these classes. The question is
whether the existing rules need structural enforcement (hooks) or whether the
recurrence rate is acceptable (rules reduce but don't eliminate).

## Corpus statistics

### AAR reports (20 reports)

| Metric | Value |
|---|---|
| Finding severity distribution | 6 CRITICAL, 19 HIGH, 19 MEDIUM, 11 LOW |
| Total headline lessons | 40 |
| Reports with open/actionable items | 19 of 20 |
| Opportunity dispositions | 33 ACT_NOW, 31 INVESTIGATE, 12 MONITOR, 7 BOUNDED_EXPERIMENT |

**Observation:** nearly every AAR has open/actionable items. The AAR process
is producing findings faster than they're being resolved. This is the
"finding velocity vs resolution velocity" gap.

### Handoffs (193 files)

| Status | Count |
|---|---|
| open | 154 (80%) |
| closed/resolved/complete | 20 (10%) |
| unknown/other | 19 (10%) |

**Observation:** 80% of handoffs are open. This is either high work-in-progress
(a real signal of unfinished work) or a failure to close handoffs when work
completes (a process gap). The `/close` skill checks for open handoffs, but
closing handoffs is operator-invoked (Rung 4).

### Design docs (6 files)

All 6 design docs have implementation references but none have a status field.
The check-orchestrator design (1428 lines, approved) has been referenced in 3
handoffs but remains unimplemented.

## What this means for our workspace

1. **The closure-pressure pattern dominates** (118 hits / 43 files — 3x the next
   pattern). It's already documented in
   [[reactive-pattern-matching-and-closure-pressure]] and has driven multiple
   structural fixes (mandatory review loops, close-accountity state machine).
   The recurrence rate suggests the pattern is inherent to the LLM-agent
   substrate, not a fixable defect — the structural fixes reduce its surface
   area rather than eliminating it.

2. **The gitignore friction** (56 hits / 14 files) was addressed this session
   with the catalog-not-grep rule. Prior to this fix, it was the #2 friction
   pattern without a dedicated wiki concept. The fix should reduce its
   recurrence in future sessions.

3. **The finding velocity vs resolution velocity gap** is the most actionable
   structural finding: 19 of 20 AARs have open items, 33 ACT_NOW dispositions
   across the corpus. The `/close` continuation_coverage scanner surfaces
   uncovered items, but the volume suggests the fleet is producing more
   findings than sessions can resolve. This is a scaling problem that will
   worsen as the fleet grows.

4. **80% handoff open-rate** is a hygiene signal. Either handoffs aren't being
   closed when work completes (process gap — `/close` doesn't auto-close
   handoffs), or the fleet genuinely has 150+ open work streams. The truth is
   likely a mix. A handoff-closure sweep (marking completed work as closed)
   would improve signal-to-noise for future sessions.

## Falsifier

This taxonomy would be wrong if: (a) the regex patterns produce false positives
(matching unrelated text) — mitigated by the patterns being specific (e.g.,
`closure.pressure` not just `pressure`); (b) the corpus is not representative
(AAR reports skew toward sessions with problems) — true, but the handoff corpus
is more representative; (c) the friction classes overlap (a single incident
counted under multiple patterns) — likely true for closure-pressure +
narrative-sufficiency, which often co-occur.

## Receipts

- **Scan script:** `P:/tmp/mine_corpora.py` — mechanical regex scan, not
  semantic analysis. Patterns derived from AGENTS.md known failure modes.
- **AAR corpus:** 20 reports at `P:/.artifacts/grok-aar/console_console_f8a6c949-f70c-4451-9f31-6295/`
- **Handoff corpus:** 193 files at `P:/docs/handoffs/*/HANDOFF.md`
- **Design corpus:** 6 files at `P:/docs/designs/*.md`
- **All counts are from the scan output,** verified by re-running the script.
