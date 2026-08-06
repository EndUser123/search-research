---
title: "close-check workflow bundles lifecycle skills (sessions don't run them)"
created: 2026-08-05
source: session-019fc927
tags: [close-check, workflow, lifecycle-skills, harvest, friction, aar, handoff, wiki, capture, mechanism]
summary: >
  The /close-check workflow (defined at ~/.grok/workflows/close-check.rhai) is
  the mechanism that runs lifecycle skills like /harvest, /friction, /aar,
  /wiki, /handoff, /capture, /slc, /behave, /trace. They run in the workflow's
  Remediate phase, NOT during the session itself. Sessions that skip
  /close-check miss all of these. The judgment agent's lifecycle-skill-coverage
  check (CHECK 3) reports what *should have* run vs what *did* run, but only
  in the workflow's own report. The session transcript itself shows zero
  lifecycle-skill invocations — which is normal and correct, not a gap.
agent: grok
host: grok
cognitive_load: 3
verification: single-source-verified
sources:
  - "~/.grok/workflows/close-check.rhai (Sweep/Synthesize/Remediate/Finalize phases, judgment agent CHECK 3 lifecycle-skill-coverage)"
  - "~/.grok/commands/close-check.md (command wrapper description, replaced /close)"
  - "session-019fc927 transcript (only /close-check invocation, no individual lifecycle skills)"
relations:
  - target: wiki/concepts/replacement-before-investigation-pattern.md
    type: related
  - target: wiki/concepts/session-completeness-audit-2026-08-02.md
    type: complements
---

# close-check workflow bundles lifecycle skills (sessions don't run them)

## Decision context

**Why this knowledge was needed:** session 019fc927's
`lifecycle-skill-coverage` check (judgment agent CHECK 3, from the
close-check workflow) reported that NO lifecycle skills were invoked during
the session itself — no /harvest, /capture, /friction, /aar, /wiki, /slc,
/behave, or /trace. Naive reading: "session failed to run required skills."
Correct reading: lifecycle skills are not supposed to be invoked by the
session — they're invoked by the workflow's Remediate phase after the
sweep completes. The workflow IS the mechanism; the session running it
once at the end is correct.

This distinction matters because:
1. Sessions that judge themselves on "did I run /wiki this session?" will
   falsely believe they failed when the workflow actually handled it.
2. Sessions that DON'T run /close-check at all genuinely miss the bundled
   lifecycle coverage (those are real gaps).
3. Operators reading transcript grep for lifecycle skill calls will see
   zero hits even for well-run sessions — false alarm if they don't know
   the architecture.

## How the workflow bundles lifecycle skills (verified receipts)

The close-check workflow (`~/.grok/workflows/close-check.rhai`) defines 4
phases:

1. **Sweep** — 3 parallel agents run checks (mechanical, fmea, judgment).
2. **Synthesize** — classify findings, populate raw_evidence, build readiness report.
3. **Remediate** — **THIS IS WHERE LIFECYCLE SKILLS RUN.** Per the workflow
   metadata (lines 5-8):
   ```
   phases: [
     { title: "Sweep", ... },
     { title: "Synthesize", ... },
     { title: "Remediate",
       detail: "Wave 1: read-only skills (/trace, /friction) parallel.
                Wave 2: write-capable skills (/capture, /handoff, /wiki)
                serialized with safe-git + stale-read immunity." },
     { title: "Finalize", ... },
   ],
   ```
4. **Finalize** — commit workflow artifacts, clean temp files, refresh skill index.

The judgment agent's CHECK 3 (lifecycle-skill-coverage) reads the session
transcript and reports which skills *should have* run based on session
content (e.g., "drift detected → /slc should run"; "critical code written
→ /trace should run"). The Remediate phase then actually runs them — the
report from CHECK 3 feeds the remediation orchestration.

**The pattern is "session produces signals, workflow produces skills."**
This decouples skill execution from session runtime, which means a session
can be terminated mid-flow and the close-check workflow still produces the
required artifacts.

## What the session transcript shows vs what was actually done

Session 019fc927 transcript evidence:

- **Transcript grep for lifecycle skills:** `/tp` (mid-session for "what
  should we do next"), `/close-check` (terminal invocation). Zero
  `/harvest`, `/capture`, `/friction`, `/aar`, `/wiki`, `/handoff`, `/slc`,
  `/behave`, `/trace` calls.
- **Workflow state file:** `wf_019fd51057257e32af792cd6a0792bac` — this
  IS the mechanism that runs them in the Remediate phase.
- **Work completed:** Phase 2 tree-sitter scope (commit 4025d04),
  AGENTS.md /research alias documentation (commit 517c185), handoff
  CLOSED (commit 75b5970), codegraph measurement (`P:/tmp/codegraph_scope_measure.py`,
  exit 0 in 61.59s). All delivered; lifecycle skill capture happens after
  via the workflow.

A naive lifecycle-skill-coverage audit that says "no /wiki was called →
session failed to capture knowledge" is wrong here. The /wiki call
happens in the workflow's Remediate phase, not in the session.

## What this means for our workspace

**Action 1 — Update lifecycle-skill-coverage checks to recognize the
workflow pattern.** See the underlying gate contractfor the
underlying gate contract. The judgment agent's CHECK 3 should distinguish:
- "Session invoked /close-check at the end" → expect workflow Remediate
  to run lifecycle skills. Transcript grep should report this as PASS
  with a note: "lifecycle coverage delegated to /close-check Remediate."
- "Session terminated without /close-check" → flag as fail.

Currently the check may report "0 lifecycle skills ran" without
distinguishing "because the workflow handles it" from "because the
session ended without coverage." Reading the transcript for the
/close-check invocation (one grep) disambiguates.

**Action 2 — Don't recommend running lifecycle skills mid-session as a
fix.** If an operator sees "lifecycle-skill-coverage = fail" in a
workflow report and runs /wiki manually during the session, that
duplicates work the workflow would have done. The fix is to ensure
/close-check is invoked, not to manually invoke /wiki.

**Action 3 — The mechanism is durable, the SKILL.md is not.** `/close`
was replaced by `/close-check` per `~/.grok/commands/close-check.md`
("Replaces `/close`"). Any session that runs `/close` directly will
not get the bundled lifecycle coverage. This is a routing rule that
should live in AGENTS.md or in the `/close` skill's SKILL.md (mark
deprecated → use /close-check).

**Action 4 — When debugging "why didn't X get captured?", check the
workflow state file first.** If a handoff was supposed to be written
and wasn't, the cause is usually "the workflow's Wave 2 didn't reach
the handoff skill" or "the Wave 2 ran but the write failed silently."
The workflow state file (`P:/tmp/wf_*.json`) tracks phase
progress; the agent shouldn't just grep the session transcript for
/handoff and conclude "not invoked."

## Falsifier

This entry is wrong if:

- **Lifecycle skills ARE expected to be invoked mid-session.** If a
  future change moves /wiki, /handoff, /friction out of the workflow's
  Remediate phase and into session flow (e.g., to reduce workflow
  runtime), the "sessions don't run them" claim becomes stale.
  Verification: re-read `~/.grok/workflows/close-check.rhai` phases
  array; if Remediate no longer lists those skills, retire this concept.
- **The close-check workflow itself becomes deprecated.** If a future
  iteration replaces /close-check with another mechanism, the bundled-
  coverage architecture may not transfer. Verification: check the
  `~/.grok/commands/` directory and the AGENTS.md routing table for
  current close-time workflow.
- **The judgment agent's CHECK 3 already distinguishes workflow-run from
  session-run.** If the check has been updated since 2026-08-05 to
  recognize /close-check as a coverage signal, this entry is redundant.
  Verification: `rg "close.check\|Remediate" ~/.grok/workflows/close-check.rhai`
  returning a check that greps for the invocation.

## Receipts

The workflow and command files were inspected directly via `Get-Content` on
2026-08-05; the line ranges and quoted code are verified in the current
working tree:

| File | Lines / Section | Content | Verification |
|------|-----------------|---------|--------------|
| `~/.grok/workflows/close-check.rhai` | 5-8 (phases array) | Metadata listing 4 phases including "Remediate: Wave 1: read-only skills (/trace, /friction) parallel. Wave 2: write-capable skills (/capture, /handoff, /wiki) serialized..." | `Get-Content` returns the phases block as quoted |
| `~/.grok/workflows/close-check.rhai` | judgment agent prompt, CHECK 3 | "lifecycle-skill-coverage" check enumerates /harvest, /capture, /friction, /aar, /wiki, /handoff, /slc, /behave, /trace with applicability rules | grep verified block present |
| `~/.grok/commands/close-check.md` | lines 1-12 | Header: "Launch the close-check workflow - the session readiness gate. Replaces /close." + session-completeness audit + propagation check + ranked harvest additions dated 2026-08-02 | file present in `~/.grok/commands/` |

Session transcript evidence:

- **Workflow invocation id:** `call_b9a399398fb2471d8d3d9424` (single
  terminal /close-check invocation in session 019fc927)
- **Workflow state file id:** `wf_019fd51057257e32af792cd6a0792bac`
  (per raw evidence packet)
- **Transcript lifecycle-skill grep:** zero hits for /harvest,
  /capture, /friction, /aar, /wiki, /handoff, /slc, /behave, /trace
  (verified via session summary line "Lifecycle skills observed: only
  the /close-check workflow invocation at the end of the session")
- **Other session invocations:** /tp used mid-session ("what should
  we do next") — this is a discussion skill, not a lifecycle skill

The mechanism claim ("lifecycle skills run in the workflow's Remediate
phase, not the session") is verified by reading the workflow phases
metadata directly. It is not inferred from the absence of skill calls.

## Sources

- `~/.grok/workflows/close-check.rhai` lines 5-8 (phases metadata
  including "Remediate: Wave 1: read-only skills (/trace, /friction)
  parallel. Wave 2: write-capable skills (/capture, /handoff, /wiki)
  serialized with safe-git + stale-read immunity.")
- `~/.grok/workflows/close-check.rhai` judgment agent prompt
  (CHECK 3 lifecycle-skill-coverage — lists which skills are checked
  and their applicability rules)
- `~/.grok/commands/close-check.md` lines 1-12 ("Replaces `/close`"
  statement, session-completeness audit addition 2026-08-02,
  propagation check addition 2026-08-02, ranked harvest in report)
- Session 019fc927 transcript — confirmed /close-check invocation at
  end (call_b9a399398fb2471d8d3d9424); no individual lifecycle skill
  calls; workflow id wf_019fd51057257e32af792cd6a0792bac
- [[replacement-before-investigation-pattern]] — sessions replacing
  workflow coverage with manual invocation duplicates work
- the meta-checkpoint ritual — meta-checkpoint at
  /close is implemented as the workflow's Remediate phase, not as
  a session-end ritual

## Auto-related

- [[skill-catalog]]
- [[skill-graph]]
- [[agent-config-directory-taxonomy]]
- [[claude-code-cli-agent-configuration-and-workflow-patterns]]
- [[close-runner-verdict-staleness-across-phases]]

