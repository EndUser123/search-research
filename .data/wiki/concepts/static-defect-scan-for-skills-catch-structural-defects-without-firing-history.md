---
title: "Static defect scan for skills: catch structural defects without firing history"
created: 2026-08-06
source: session-019fc303
tags: [skill-lifecycle, static-analysis, defect-prevention, skill-dev, measurement, technique]
summary: >
  A 6-check static scan run during skill measurement that catches structural
  defects (broken paths, host-conformance violations, passthrough gaps, stale
  versions, incomplete frontmatter, bloat) without needing firing history.
  Added to /skill-dev as Step 1.5 after measuring /maintain scored "Insufficient
  Evidence" (0 firings) but a /tp review found 3 structural defects the
  measurement missed. The scan prevents the "Latent / Untested with Defects"
  outcome by catching defects at measurement time.
agent: grok
host: both
cognitive_load: 2
verification: empirically-tested
sources:
  - session-019fc303 (2026-08-02, /skill-dev measure /maintain + /tp review)
relations:
  - target: wiki/concepts/execution-receipts-for-executable-artifacts.md
    type: layer-1-of-2 — static checks form Layer 1 of the two-layer execution-receipt gate
  - target: wiki/concepts/skill-lean-code-context-efficiency.md
    type: check-6-implements — the leanness check operationalizes the leanness principle
---

# Static defect scan for skills: catch structural defects without firing history

## Decision context

`/skill-dev measure /maintain` scored "Insufficient Evidence" (0 firings, MEC
cannot be assessed). A subsequent `/tp` review found 3 structural defects the
measurement missed: a Claude-ism env var (`CLAUDE_TERMINAL_ID` instead of
`GROK_SESSION_ID`), a hardcoded placeholder (`my_term = "console_XXXX"` with
no passthrough), and a dead path (`D:\.code`). The skill couldn't have worked
if fired — but the measurement said "insufficient evidence" rather than
"broken."

**Root cause:** `/skill-dev` Mode 1 (measure) evaluated the skill from
firing evidence (AAR traces, tp critique logs, routing incidents) but never
inspected the SKILL.md body itself for structural soundness. A skill with
zero firings has no evidence to evaluate — but it can still have defects.

## The 6 checks

| # | Check | What it catches |
|---|-------|----------------|
| 1 | Path resolution | Script paths that don't resolve, wrong env vars |
| 2 | Host conformance | Claude-isms in a grok skill (CLAUDE_SESSION_ID, .claude paths) |
| 3 | Code-block passthrough | Hardcoded placeholders (XXXX, console_YYYY) with no passthrough |
| 4 | Version freshness | Stale `version:` field after known edits |
| 5 | Frontmatter completeness | Missing `techniques:`, `host:` fields |
| 6 | Leanness | In-file changelogs, redundant provenance, over-explanation |

## The "Latent / Untested with Defects" MEC outcome

Step 1.5 added a new MEC outcome: `<3 firings AND Step 1.5 found ≥1 blocking
defect`. The skill can't be assessed for contribution because it has
structural defects that would prevent it from working if fired. This is
distinct from "Insufficient Evidence" which has no defects found — "Latent
with Defects" means the skill needs repair before it can even be evaluated.

## Transferability

This technique applies beyond `/skill-dev`:
- Any skill measurement system that evaluates from firing history needs a
  static-check layer for zero-firing skills
- The 6 checks are domain-agnostic (paths, host, passthrough, version,
  frontmatter, leanness) and can be applied to any instruction document
- The technique composes with the execution-receipts two-layer gate: Step 1.5
  is Layer 1 (static), test-firing is Layer 2 (runtime)

## Falsifier

This technique is wrong if:
- The 6 checks consistently find zero defects across all measured skills
  (too strict — catching noise, not real defects)
- The checks find "defects" that don't affect runtime behavior (false positives)
- The "Latent with Defects" outcome never fires on real skills (the category
  is unused)

Empirical validation: first run found 6 defects in `/maintain` (all blocking).
Second run (batch scan) found 149 defects across 10 skills with `__lib/` scripts.

## Reference incident

Session 019fc303 (2026-08-02): `/maintain` went 5 days with 6 undetected
defects. The operator caught it only by manually asking "anything else to
consider before trying /maintain?" Step 1.5 is the structural fix — it would
have caught all 6 before the operator needed to ask.
