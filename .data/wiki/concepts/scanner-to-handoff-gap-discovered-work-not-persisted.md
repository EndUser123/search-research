---
title: "Scanner-to-Handoff Gap: Discovered Work Not Persisted"
created: 2026-08-05
source: session-20260805
tags: [architecture-decision, scanner, handoff, persistence, todo, dream, cross-session, fleet-ops, gap]
summary: >
  The /todo scanner discovers 16 source types but its output is ephemeral — it
  dies when the session ends. Handoffs are the only cross-session persistence on
  Grok Build. Five categories of open work (script defects, stale handoffs,
  review findings, harvest obligations, dream proposals) were discovered by the
  scanner but never persisted to handoffs. Root cause: skills produce open items
  in skill-local stores (harvest JSON, FINDINGS.md, script scan output) but no
  bridge converts these to handoffs. The /dream skill creates handoffs from its
  corpus, but its corpus doesn't include the scanner sources. Structural fix:
  widen the dream's Step 1 corpus to include scanner sources, so the existing
  Step 6 handoff routing handles them automatically.
agent: grok
host: grok
cognitive_load: 3
verification: observed
relations:
  - target: wiki/concepts/dream-evidence-density-promotion-path.md
    type: related
  - target: wiki/concepts/epistemic-knowledge-system-design-2026.md
    type: related
  - target: wiki/concepts/complexity-magnet-subsystem-bug-accumulation.md
    type: related
---

# Scanner-to-Handoff Gap: Discovered Work Not Persisted

## Decision context

**Why this finding matters:** during session 2026-08-05, the operator asked "are those open items captured?" after the `/todo` scanner surfaced 11 action items. The honest answer was: they're in `/todo`'s ephemeral output and mentioned in one handoff line, but they have no dedicated handoffs. On Grok Build, handoffs are the only cross-session persistence mechanism. If nobody runs `/todo` or reads the session handoff, the items are invisible to future sessions.

**What failed:** the `/todo` scanner reads 16 sources and produces a prioritized RNS list. But that list is ephemeral — it exists only in the session transcript. Five categories of open work were discovered but never persisted:

| Category | Scanner source | Skill-local store | Has handoff bridge? |
|----------|---------------|-------------------|---------------------|
| Script defects (121) | `skill_scripts` | scan output only | ❌ |
| Stale handoffs (188) | `handoffs` | handoff files themselves | ❌ (meta: they ARE handoffs, but stale) |
| Review findings (12) | `review` | `.artifacts/FINDINGS.md` | ❌ |
| Harvest obligations (2) | `harvest` | `.data/harvest/pending/*.json` | ❌ |
| Dream proposals (7) | `dreams` | `P:/docs/dreams/*.md` | ✅ (dream Step 6 creates handoffs) |

Only the dream has a handoff bridge — its Step 6 post-output routing creates dedicated handoffs for unresolved proposals. The other four categories have no equivalent.

## The root cause chain

1. `/todo` discovers open items from 16 sources → produces ephemeral RNS list → session ends → list gone
2. `/dream` creates handoffs from its 6-source corpus → but its corpus doesn't include scanner sources (harvest, FINDINGS.md, script scan)
3. `/handoff` auto-update mode scans the session transcript → but scanner output is in tool calls, not the session's work streams
4. Skills that produce open items (`/review`, `/harvest`, `script_scan`) have no "create handoff" step

The gap: **skills discover or produce open work items but don't auto-create handoffs for them.** The pipeline has a missing stage. This is the same class of gap documented in [[epistemic-knowledge-system-design-2026]] — the system discovers knowledge but doesn't always persist it at the point of discovery.

```
scanner/skill discovers open item
    ↓
item exists in skill-local store (harvest JSON, FINDINGS.md, dream output)
    ↓
???  ← no skill converts these to handoffs
    ↓
item invisible to sessions that only read handoffs
```

## Why the dream → handoff chain almost worked

The existing chain is: work → `/wiki` → recommends `/dream` → dream Step 6 creates handoffs. This chain **did work** for dream items — it created `dream-2026-08-04-external-synthesis/HANDOFF.md`. But:

1. The dream's Step 1 corpus reads: handoffs, AARs, www-ledger, wiki concepts, ADRs, prior dreams. It does NOT read: harvest pending, review FINDINGS, script scan output.
2. So the dream literally cannot see 4 of the 5 open-item categories.
3. The `/todo` scanner CAN see all 16 sources, but `/todo` is ephemeral.

The dream persists → it doesn't discover the right sources. The scanner discovers → it doesn't persist.

## What this means for our workspace

1. **On Grok Build, handoffs are the ONLY cross-session persistence.** The `/tasks` skill (Claude Code's task store at `~/.claude/tasks/`) has been disabled as not applicable. There is no task store, no issue tracker, no external backlog. If it's not in a handoff, it doesn't survive the session.

2. **The immediate fix (applied this session):** manually write dedicated handoffs for each backlog category. Four handoffs were created: `skill-script-defects-cleanup-20260805`, `stale-handoff-cleanup-20260805`, `review-findings-cleanup-20260805`, `harvest-obligations-20260805`. This is a manual bridge — it works but requires an agent to notice the gap and act.

3. **The structural fix (proposed, not yet implemented):** widen the dream's Step 1 corpus to include the scanner sources. Then the dream's existing Step 6 handoff routing creates handoffs for items discovered across all scanner sources. No scheduled job needed — the dream already fires after `/wiki`, which fires after `/www`. The trigger chain exists; the input just needs widening. This connects to [[dream-evidence-density-promotion-path]] — both are improvements to the dream's input/promotion pipeline.

   Sources to add to dream Step 1:
   - `P:/.data/harvest/pending/*.json` (harvest obligations)
   - `P:/.artifacts/*/FINDINGS.md` (review findings >24h old)
   - Script scan output (run `script_scan.py` inline during dream Step 1)
   - Stale handoff detection (handoffs >7 days old with status=open)

4. **The `/todo` scanner could also gain a "write handoffs for deferred items" mode.** When the operator picks "0 - Do all" and the agent decides an item is better deferred, `/todo` writes a handoff instead of dropping it. This is the `/todo`-side bridge.

## Steelman (rejected alternative)

**Make `/todo` persistent — write its RNS list to a file.** Simpler than widening the dream's corpus. `/todo` already runs the scanner; just persist the output. **Why rejected:** a persistent RNS list is not a handoff. It doesn't have the 17 mandatory fields, acceptance criteria, task packets, or resumption protocol. Future sessions would need to parse the RNS format and re-evaluate each item. The handoff format exists precisely for this — it's structured for cold-start pickup. Persisting the scanner output in a different format creates a parallel persistence path that doesn't compose with the existing handoff infrastructure.

## Falsifier

This analysis is wrong if:
- The dream's corpus is already wide enough and the items were missed for a different reason (e.g., the dream didn't run, or it ran but skipped certain source types)
- Manual handoff creation is sufficient and the structural fix (widening the dream corpus) adds complexity without value
- The operator prefers ephemeral `/todo` lists and intentionally doesn't want every scanner finding persisted as a handoff (handoff accumulation concern — 188 stale handoffs is already a problem, see [[complexity-magnet-subsystem-bug-accumulation]] for how subsystems accrete without cleanup)

## Receipts

- `/todo` scanner: `~/.grok/skills/todo/__lib/scan_functions.py` — scans 16 sources (verified by reading SKILL.md source list)
- Dream Step 1 corpus: `~/.grok/skills/dream/SKILL.md` lines 176-189 — reads 6 sources (handoffs, AARs, www-ledger, wiki concepts, ADRs, prior dreams)
- Dream Step 6 handoff routing: `~/.grok/skills/dream/SKILL.md` lines 540-560 — creates handoffs for unresolved proposals
- `/tasks` skill disabled: `~/.grok/skills/tasks/SKILL.md` — frontmatter now `host: claude`, `user-invocable: false`
- Session 2026-08-05: operator asked "are those open items captured?" — the answer was "partially, but not in dedicated handoffs"

## Sources

- Session 2026-08-05 operator feedback ("are those open items captured?" → "What tasks skill are you talking about?")
- `/todo` scanner source list (16 sources, SKILL.md)
- `/dream` Step 1 corpus (6 sources, SKILL.md)
- `/handoff` auto-update mode (scans session transcript, not scanner outputs)

## Auto-related

- [[skill-graph]]
- [[close-scanner-unavailable-fallback-session-observations-handoff]]
- [[optimal-cross-session-chain-traversal-aar-handoff-grok]]
- [[llm-handoff-best-practices]]
- [[handoff-fragmentation-under-recurrence]]

