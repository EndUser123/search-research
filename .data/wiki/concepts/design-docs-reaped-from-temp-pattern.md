---
title: "Design Docs in Temp Get Reaped by OS — Second Confirmed Loss"
slug: design-docs-reaped-from-temp-pattern
date: 2026-08-01
session: 019fbf26-08f9-7f12-ace1-15ce7541c140
source_sessions: [019f902a-621d-7711-9436-7c6003c57793]
tags: [design, temp-files, durability, data-loss, pattern]
host: grok
---

# Design Docs in Temp Get Reaped by OS

## Pattern

The `/design` skill writes its output (design doc, review file, summary) to
`%TEMP%\grok-design-<id>\`. The OS reaps temp directories on reboot. Design
docs that aren't manually copied to `P:/docs/design/` are permanently lost.

## Evidence

**Instance 1 (session `019f902a`, 2026-07-23):** A 109KB, 16-section design doc
for the `/tp` Thinking Hats enhancement (Hat Selection Gate mechanism) was
written to `C:\Users\brsth\AppData\Local\Temp\grok-design-fe4bd161\`. By
2026-08-01, `Test-Path` returned False — the directory was reaped. Only the
wiki concept `tp-hat-selection-gate-content-driven-hat-choice.md` survived
with the core decision.

**Instance 2 (prior):** An earlier design doc loss was noted in session
observations but not formally tracked.

## Root cause

`/design` uses `tempfile.gettempdir()` as the default base for its scratch
directory. The skill's output instructs the operator to "copy it now to
`P:/docs/design/`" — but this is a behavioral reminder, not a structural
guarantee. When the session ends or the terminal closes, the reminder is lost.

## Impact

- Multi-hour `/design` loops (4-9 writer/reviewer rounds) produce 50-109KB
  design docs that represent significant invested work
- Loss is silent — the operator discovers it days later when trying to
  reference the doc
- The wiki concept captures the *decision* but not the *full specification*
  (implementation details, PR breakdowns, acceptance criteria)

## Structural fix

**`/design` should auto-persist to `P:/docs/design/` on completion.** The
temp directory can remain for scratch, but when the design loop reaches
0 open issues, the final doc should be copied to:
```
P:/docs/design/<YYYY-MM-DD>-<topic-slug>.md
```

This is the same pattern `/close-check` uses when it writes its report to
`scratch/pre-close-report.md` — but `/close-check` runs within the session
directory (durable), while `/design` writes to OS temp (ephemeral).

## Alternative: GROK_DESIGN_SCRATCH_DIR

The `/design` skill already supports `GROK_DESIGN_SCRATCH_DIR` env var to
override the base directory. Setting this to `P:/docs/design/` globally
would prevent all future losses. But env vars are session-scoped and easy
to forget.

## Recommendation

1. **Auto-copy on completion** (structural fix): when `/design` reaches
   0 open issues, copy the final doc + review to `P:/docs/design/`
2. **Set `GROK_DESIGN_SCRATCH_DIR`** globally in the Grok Build config
3. **Warn at session end**: if a design doc exists in temp and wasn't
   copied, surface it in `/close-check` as an AT RISK item

## Related

- [[skill-catalog-scope-inconsistency-causes-cascading-read-failures]] —
  same class of problem (stale reference, discovered late)
- [[narrative-as-signal]] — the "copy it now" reminder is a narrative
  that doesn't enforce itself
