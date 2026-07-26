---
title: "Offer, Don't Auto-Destroy — Irreversible Cleanup Convention"
created: 2026-07-24
source: session-2026-07-24
tags: [convention, cleanup, safety, skills, close, irreversible]
summary: >
  When a skill handles cleanup (temp files, old artifacts, stale caches),
  it must offer with a structured table showing what's there — never
  auto-delete. The operator decides based on blast-radius information,
  not a blanket trust-the-machine default.
agent: grok
host: grok
cognitive_load: 1
---

## Decision

**Never auto-delete. Always offer with a structured table.**

When `/close` (or any skill) encounters files eligible for cleanup, it must:
1. Group files by pattern (disposable, output capture, durable, uncertain)
2. Show count + total size per group
3. Preserve durable-value files first (Tier 1)
4. Emit one structured table with a one-word question
5. Operator scopes their own answer ("delete groups 1-2", "yes", "keep all")

## Rationale

The operator experienced a session where files were moved/copied/deleted
with no confirmation and no log — then couldn't reconstruct what happened.
Auto-deletion of temp files in `/close` reproduces that exact failure mode
at the session level: artifacts disappear with no trace, and if you later
realize you needed one (e.g., a preflight JSON proving a discovery was done),
it's gone.

This extends the AGENTS.md tier system: **Tier 3 (irreversible) requires
operator decision, always.** Deletion is Tier 3. No exceptions for "obvious"
patterns — the operator must see the table and confirm, even for disposable
scripts, because the cost of asking (3 seconds) is negligible compared to
the cost of losing something you didn't realize was there.

## Alternatives rejected

- **Auto-delete disposables, ask on uncertain** — rejected because it
  violates Tier 3 and reproduces the silent-deletion failure mode
- **Ask per-file** — rejected because it's too slow for 50+ temp files;
  the grouped table is faster and clearer

## Falsifier

If operators consistently say "just delete everything" and never look at
the table, the convention is ceremony and auto-delete-with-log would be
simpler. Track for 10 close cycles.

## Related

- [[advisory-vs-mandatory-triggers]]@related — same blast-radius principle
  applied to proactive triggers
