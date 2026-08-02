---
thread_id: harvest-burn-down-20260801
parent_handoff_path: none
current_session_id: 019f9a89-d902-7930-ad3a-bab7e682830b
current_terminal_id: console
produced_at: 2026-08-01T21:20:00Z
last_updated_by: 019f9a89-d902-7930-ad3a-bab7e682830b
last_updated_at: 2026-08-01T21:20:00Z
status: open
handoff_type: investigation
accurate_as_of_head: 18eace1f530464f868dfa5a5946e8b34851c334b
---

# Handoff: Harvest burn-down — close the 27 OPEN obligations

## Objective

Cluster the 27 OPEN harvest items by root cause, identify the top 5-10 that share a fix, and close them. Invert the fleet's accumulation trajectory (currently producing obligations 10x faster than closing them).

## Status

OPEN — ready for implementation. No investigation needed; this is a triage + closure session.

## Producing context

Produced 2026-08-01 by session 019f9a89 (terminal: console). Triggered by /tp critique finding: 85% harvest open rate (29 OPEN / 34 total) is the workspace's binding constraint.

## Read-first list

1. `~/.grok/skills/harvest/SKILL.md` — harvest lifecycle, operations, CLI
2. Run `harvest.py show` — current OPEN items with titles + hints
3. Run `harvest.py doctor` — pattern candidates, unarmed items, fold time
4. `P:/.data/wiki/concepts/analysis-over-action-pattern-knowledge-capture-without-application.md` — the investigation-theater pattern this burn-down addresses

## Verified facts

- [FACT] 29 OPEN harvest items, 5 COLLECTED, 0 REGRESSED, 0 RETIRE_CANDIDATE, 3 CLOSED (source: `harvest.py doctor` output, 2026-08-01)
- [FACT] 9 GENERALIZE items identified as pattern candidates by `harvest.py doctor` (source: same output)
- [FACT] 28 unarmed items (hint only, no verification test) (source: same)
- [FACT] 48 events total, 0 conflicts, fold time 0.9ms (source: same)
- [FACT] 213 open handoffs across all sessions, 137 from last 7 days (source: `coverage_scan.py`, 2026-08-01)
- [INFERENCE] The fleet is producing obligations 10x faster than closing them, based on the ratio of open to closed items

## Current state

The harvest system is healthy mechanically (0 conflicts, fast fold time). The problem is throughput: items accumulate because nobody closes them. The closure rate is 3/34 = 8.8%.

## Task packets

### BURN-01: Cluster OPEN items by root cause

- **Goal:** Identify which harvest items share a common root cause
- **In scope:** All 29 OPEN items
- **Out of scope:** COLLECTED items (already have evidence); CLOSED items
- **How:** Read each item's title + obligation + hint. Group by theme. Look for clusters of 3+ items sharing a root cause.
- **Acceptance:** A clustering table showing N groups, each with ≥1 item, the shared root cause, and the fix that would close all items in the group
- **Falsifier:** if every item is genuinely independent (no clusters ≥3), the burn-down is lower-leverage and individual closure is the only path

### BURN-02: Close the top cluster

- **Goal:** Fix the root cause of the largest cluster, then collect all items in it
- **In scope:** The largest cluster from BURN-01 (or top 2 clusters if both are fixable in one session)
- **Out of scope:** Items outside the cluster
- **How:** Implement the fix (code, config, or AGENTS.md rule). Then `harvest.py arm <id> --test "<verification>"` + `harvest.py collect <id>` for each item in the cluster.
- **Acceptance:** ≥5 items transitioned from OPEN to COLLECTED or CLOSED
- **Falsifier:** if the fix doesn't actually resolve the obligations (verification fails), the items stay OPEN
- **Verification level:** LIVE_BEHAVIOR — the fix must be verified against the real system

### BURN-03: Arm and verify individual items

- **Goal:** For items that are individually closeable (not part of a cluster), arm with verification tests and collect
- **In scope:** Items from BURN-01 that are individually closeable
- **Out of scope:** Items requiring design decisions or operator input
- **How:** For each item: `harvest.py arm <id> --test "<command>"` then `harvest.py collect <id>`
- **Acceptance:** ≥3 additional items collected
- **Falsifier:** if verification commands fail, the items stay OPEN (correct behavior)

## Open decisions

### D1: Should the 1:1 discovery-to-resolution policy be adopted?

- **Question:** For every new handoff opened, close one existing one. Should this become an AGENTS.md rule?
- **Options:**
  - A: Adopt as AGENTS.md rule (structural enforcement)
  - B: Adopt as soft guideline (behavioral, no hook)
  - C: Reject — the ratio will self-correct as the fleet matures
- **Selection criterion:** can the fleet sustain the ratio without it becoming a bottleneck itself?
- **Current lead:** B (soft guideline) — structural enforcement may cause agents to close items prematurely to satisfy the ratio

## Hard constraints

- **No premature closure.** Collecting an item without a passing verification is forbidden by harvest's own contract (`collect` refuses without `--assert-manual`). Don't bypass this with `--assert-manual` just to hit a target.
- **No deleting items to reduce the count.** If an item is genuinely obsolete, use `harvest.py mark-retire` → `harvest.py close` (proper lifecycle). Never delete event files directly.

## Cross-reference couplings

- `~/.grok/AGENTS.md` "Completion-claim discipline" → if items are collected prematurely, the completion claims are false. The receipt rule applies.
- `P:/.data/harvest/events/` → the immutable event store. This handoff reads it via `harvest.py show/doctor`.
- `P:/docs/handoffs/agentic-rules-not-firing-enforcement-investigation-20260726` → if rule-firing is the shared root cause of ≥5 harvest items, that investigation gets promoted to priority 1.

## Other outstanding streams

- **close-check-lifecycle-auto-chain-20260801** — concrete implementation, design ready. Open.
- **why-skill-adoption-gap-20260725** (Rev 1) — investigation open. Deprioritized.
- **agentic-rules-not-firing-enforcement-investigation-20260726** (Rev 1) — deferred until harvest backlog < 10 OPEN.
- **missed-decisions-wiki-capture-investigation-20260725** — investigation open. Unchanged.

## Explicit non-goals

- Do NOT add new harvest items during the burn-down session. The goal is closure, not discovery.
- Do NOT investigate rule-firing compliance during this session. That's deferred (see agentic-rules handoff Rev 1).
- Do NOT rewrite the harvest system. It's mechanically healthy (0 conflicts, fast fold). The problem is throughput, not architecture.

## Resumption protocol

1. `$env:HARVEST_HOME="P:/.data/harvest"; python ~/.grok/skills/harvest/scripts/harvest.py show`
2. Cluster the 27 items by reading titles + obligations
3. Identify the largest cluster with a shared root cause
4. Fix the root cause
5. Arm + collect each item in the cluster

## Suggested next invocation

```
Pick up the harvest burn-down handoff at P:/docs/handoffs/harvest-burn-down-20260801/HANDOFF.md.
Start by running harvest.py show, then cluster the 27 OPEN items by root cause.
Goal: close ≥5 items in one session.
```

## Last user message (verbatim)

"/tp update recommendations with info from todo and recap-grok" → (the /tp output recommended harvest burn-down as priority 1) → "/handoff"

## Epistemic labels

- [FACT] 27 OPEN / 34 total harvest items (harvest.py doctor output, updated 2026-08-02 after 2 collections)
- [FACT] 213 open handoffs (coverage_scan.py output)
- [INFERENCE] The fleet produces obligations 10x faster than it closes them (derived from open:closed ratio)
- [INFERENCE] Clustering will reveal shared root causes (based on the 9 GENERALIZE pattern candidates already identified by doctor)
- [UNKNOWN] Whether rule-firing is the shared root cause of ≥5 items (won't know until clustering is done)

## Changelog

| Date | Session | Action |
|------|---------|--------|
| 2026-08-01T21:20 | 019f9a89... | created |
| 2026-08-02T15:00 | 019f9a89... | updated — Rev 1: 2 items collected (29→27 OPEN), updated counts |

---

## Revision 1 — 2026-08-02T15:00:00Z (session 019f9a89-d902-7930-ad3a-bab7e682830b)

**Trigger:** auto-update — /go do now collected 2 harvest items.

**What changed since the original:**
- `01KYR4PMGM64JAXP9WWDX33KBH` (quality-gate timeout, leverage 40): COLLECTED. Root cause was dirty-tree inflation (not timeout value), fixed by session 019fb937. Timeout bump no longer needed. Evidence: handoff `hook-timeout-root-cause-and-deferred-work-20260801` line 40.
- `01KYQ3WN3DH7303ZPJD8DNY5YG` (narrative sufficiency, leverage 35): COLLECTED. Rule already present in AGENTS.md line 544 with comprehensive worked examples. Enforcement gap tracked separately by `agentic-rules-not-firing` investigation.
- Harvest state: 27 OPEN / 34 total (was 29 OPEN). 5 COLLECTED total (was 3).
- /tp do + /tp improve analysis surfaced 12 findings across 4 dimensions (efficiency, effectiveness, insightfulness, thought-partnership). All findings routed to existing handoffs or the DO_NOW list (3 items, all executed via /go).
- Top 3 ranked harvest items remaining: yt-is/nlm integration (45), verdict-integrity (35), nlm queue workers (35).

**Status update:** OPEN — scope reduced from 29→27 items. The highest-leverage remaining items are now yt-is integration (leverage 45) and nlm queue workers (leverage 35).
