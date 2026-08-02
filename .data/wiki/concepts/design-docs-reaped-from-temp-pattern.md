---
title: "Design Docs in Temp Get Reaped by OS — Structural Durability Gap"
created: 2026-08-01
source: session-20260801
tags: [design, temp-files, durability, data-loss, pattern, structural-fix]
summary: >
  The /design skill writes multi-hour output (50-109KB design docs from 4-9
  writer/reviewer rounds) to OS temp (%TEMP%), which gets reaped on reboot.
  Two confirmed losses. The "copy it now" behavioral reminder doesn't enforce
  itself. Structural fix: auto-persist to P:/docs/design/ on completion.
agent: grok
host: grok
cognitive_load: 2
verification: observed
relations:
  - target: wiki/concepts/external-improvement-ideas-for-design-skill.md
    type: related
  - target: wiki/concepts/narrative-as-signal.md
    type: related
  - target: wiki/concepts/skill-catalog-scope-inconsistency-causes-cascading-read-failures.md
    type: related
---

# Design Docs in Temp Get Reaped by OS

## Decision context

The `/design` skill runs multi-hour writer/reviewer/critical-friend loops that
produce 50-109KB design documents — the most invested-work-per-artifact in the
workspace. These docs land in `%TEMP%\grok-design-<id>\`, which the OS reaps on
reboot. The skill tells the operator to "copy it now," but that's a behavioral
reminder, not a structural guarantee. After two confirmed losses, the question
is: should `/design` auto-persist its output, and if so, where?

## Evidence

**Instance 1 (session `019f902a`, 2026-07-23):** A 109KB, 16-section design doc
for the `/tp` Thinking Hats enhancement (Hat Selection Gate mechanism) was
written to `C:\Users\brsth\AppData\Local\Temp\grok-design-fe4bd161\`. By
2026-08-01, `Test-Path` returned False — the directory was reaped. Only the
wiki concept `tp-hat-selection-gate-content-driven-hat-choice.md` survived
with the core decision. The 16-section specification (PR breakdowns,
acceptance criteria, worked examples) is permanently lost.

**Instance 2 (prior):** `stop-hook-scope-binding-fix-design-decisions.md`
frontmatter references `C:\Users\brsth\AppData\Local\Temp\grok-design-4e4629f7\`
with the note "(design doc, temp — will be reaped)." The design doc itself
is gone; only the wiki concept referencing it survives.

**Pattern noted in 3 other concepts:** `external-improvement-ideas-for-design-skill.md`
line 102 ("design doc goes from draft → review → final → (dies in temp)"),
`design-graphs-solution-graphs-value-for-ai-agent-fleet.md` line 217 ("die
with temp files"), and `spec-driven-development-harness-engineering-ecosystem.md`
line 139 ("design docs are temp scaffolding by design"). The problem is
acknowledged but never fixed.

## Root cause

`/design` uses `tempfile.gettempdir()` as the default base for its scratch
directory. The skill's output instructs the operator to "copy it now to
`P:/docs/design/`" — but this is advisory prose, not structural enforcement.
When the session ends or the terminal closes, the reminder is lost. This is
the same [[narrative-as-signal]] pattern: a plausible instruction that doesn't
enforce itself, repeated across sessions without becoming structural.

## What this means for our workspace

**`/design` should auto-persist to `P:/docs/design/` on completion.** The
temp directory can remain for scratch, but when the design loop reaches
0 open issues, the final doc should be copied to:
```
P:/docs/design/<YYYY-MM-DD>-<topic-slug>.md
```

This is the same pattern `/close-check` uses when it writes its report to
`scratch/pre-close-report.md` — but `/close-check` runs within the session
directory (durable), while `/design` writes to OS temp (ephemeral).

**Three remediation options, ranked:**

1. **Auto-copy on completion** (structural fix): when `/design` reaches
   0 open issues, copy the final doc + review to `P:/docs/design/`. Best
   option — enforcement is in the skill, not the operator.
2. **Set `GROK_DESIGN_SCRATCH_DIR` globally** in the Grok Build config.
   The skill already supports this env var. But env vars are easy to forget
   and may not persist across Grok updates.
3. **Warn at session end**: if a design doc exists in temp and wasn't
   copied, surface it in `/close-check` as an AT RISK item. Reactive, not
   proactive — catches loss after the session but before the reboot.

The [[external-improvement-ideas-for-design-skill]] concept already proposed
adding an "archive" state to the design lifecycle. This concept provides the
specific mechanism: auto-copy to `P:/docs/design/` is the archive transition.

## Falsifier

This concept is wrong if `/design` already auto-persists (it doesn't — verified
by reading the skill's Step 0 scratch directory setup which uses
`tempfile.gettempdir()`), or if the operator prefers ephemeral design docs
(intentional disposability). If future Grok Build versions persist session
temp directories across reboots, the problem evaporates.

## Receipts

- Session `019fbf26` `Test-Path` on `grok-design-fe4bd161\grok-design-doc-fe4bd161.md` returned False (2026-08-01)
- [[stop-hook-scope-binding-fix-design-decisions]] frontmatter references temp design doc path with "(will be reaped)" note
- [[external-improvement-ideas-for-design-skill]] line 102: "design doc goes from draft → review → final → (dies in temp)"
- [[tp-hat-selection-gate-content-driven-hat-choice]] lines 114, 122 reference the lost 109KB design doc path

## Related

- [[external-improvement-ideas-for-design-skill]] — proposed "archive" lifecycle state for design docs
- [[narrative-as-signal]] — the "copy it now" reminder is advisory prose that doesn't enforce itself
- [[skill-catalog-scope-inconsistency-causes-cascading-read-failures]] — same class: stale reference discovered late
- [[spec-driven-development-harness-engineering-ecosystem]] — notes design docs are "temp scaffolding by design"
- [[design-graphs-solution-graphs-value-for-ai-agent-fleet]] — notes matrices in design docs "die with temp files"

## Auto-related

- [[skill-graph]]
- [[claude-code-cli-agent-configuration-and-workflow-patterns]]
- [[claude-code-external-tool-integration-via-mcp]]
- [[claude-code-hooks]]
- [[skill-catalog]]

