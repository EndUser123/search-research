---
title: "AAR Always-Deep Mode — Operator Directive"
created: 2026-08-01
source: session-019fbf02
tags: ['aar', 'operator-directive', 'skill-design', 'mode-selection']
summary: >
  The operator directed that AAR always runs in Deep mode — no mode
  selection, no question to the operator. Light and Standard modes were
  removed entirely from the AAR skill.
agent: grok
cognitive_load: 2
verification: single-source-verified
host: grok
---

## Decision

**AAR always runs in Deep mode.** There is no mode selection and no
question to the operator. Every invocation uses full references +
cross-model audit + double-loop analysis. The `--deep` flag is accepted
for compatibility but is a no-op — Deep is the only mode.

## Rationale

The operator stated (2026-08-01): "AAR is always supposed to be D, there's
not supposed to be any other choice." The adaptive mode table (Light ≤20
turns, Standard 21-100, Deep >100) was inherited from the /debrief
absorption (2026-08-01) but never reflected the operator's actual
preference — they always want maximum rigor.

Offering a mode choice created a friction point: the agent asked the
operator to pick a mode, which wasted a turn and sometimes resulted in
a non-Deep mode being selected against the operator's intent.

## What changed

- `argument-hint`: removed `--lite` and `--standard`
- Mode section: replaced adaptive mode table with unconditional Deep directive
- Phase 6/7: "simple AAR" conditional language → "Always on (Deep mode)"
- Cross-model audit trigger: removed `--lite` skip clause
- §ten-questions: "default simple AAR" → "Deep AAR"
- Examples table: removed `--lite`/`--deep` as distinct modes
- `/debrief` now routes to `/aar` (not `/aar --lite`)

Commit: `f0979f1` in `~/.grok`

## Falsifier

If the operator ever explicitly requests a lighter mode ("just a quick
scan"), this directive should be revisited — the operator may want
flexibility they haven't expressed yet.

## Related

- [[agent-failure-modes-2026]] — "Ugly wish-granting" mode: agent grants
  literal request rather than understanding intent. The mode-selection
  question was itself an instance of this — the operator never wanted
  anything except Deep.
