---
title: "Research-to-execution ratio — the self-reinforcing substrate-accumulation pattern"
created: 2026-07-27
source: session-019fa48a (/tp critique of /www 6-track investigation)
tags: [research-to-execution-ratio, analysis-paralysis, substrate-accumulation, meta-pattern, workflow, self-reinforcing, handoff-backlog, execution-gap]
summary: >
  The workspace accumulates research artifacts (wiki concepts, handoffs, AAR
  artifacts) faster than it executes them. The pattern is self-reinforcing:
  more research produces more substrate, which provides more material to
  synthesize, which generates more research. The /tp opportunity scan
  exacerbates this by treating execution-ready work (handoffs with directions)
  as research opportunities. Detection signal: when a /www or /tp cycle
  "confirms" directions that already had handoffs, the research-to-execution
  ratio is off. The fix is structural, not behavioral: gate research on whether
  a handoff already contains the direction.
cognitive_load: 2
verification: operator-confirmed
host: both
agent: grok
sources:
  - "session-019fa48a /tp critique (glm-5-2 fresh subagent, 7 tool calls, 141.8s)"
  - "P:/docs/handoffs/ inventory (169 directories as of 2026-07-27)"
  - "wiki/concepts/research-vs-design-vs-architect-skills-and-www-self-assessment.md (2026-07-26, one day prior)"
relations:
  - target: wiki/concepts/research-vs-design-vs-architect-skills-and-www-self-assessment.md
    type: extends
  - target: wiki/concepts/mechanical-enforcement-over-behavioral-reminder.md
    type: related
  - target: wiki/concepts/decision-and-fix-documentation-rule.md
    type: related
---

# Research-to-execution ratio

## Decision context

**The problem:** a `/tp` critique of a `/www` investigation found that 5 of 6
"opportunity tracks" already had handoffs with directions and acceptance
criteria before the research ran. The /www confirmed them with external
citations rather than discovering new directions. The operator's response —
"I'm a little bit confused. Is there opportunity here?" — was the correct
instinctive signal that the research-to-execution ratio was off.

**The underlying pattern:** the workspace has 169 handoff directories. This
session alone produced 8 wiki concepts and 10+ handoffs. The research
artifact accumulation rate exceeds the execution rate. The workspace's own
meta-assessment ([[research-vs-design-vs-architect-skills-and-www-self-
assessment]], 2026-07-26) said "pare ceremony" — and the next day, more
ceremony was produced. The pattern is self-reinforcing.

## The self-reinforcing loop

```
Research produces artifacts (concepts, handoffs)
  → more substrate exists to synthesize
    → synthesis produces more research artifacts
      → more substrate exists...
```

The loop has no natural termination. Each research cycle adds to the
substrate that justifies the next research cycle. Execution — actually
building the thing the handoff describes — is the only exit.

## Detection signal

A /www or /tp cycle that "confirms" directions that already had handoffs.
If the output says "confirmed" or "validated" rather than "discovered" or
"changed," the research-to-execution ratio is likely off. The operator's
confusion ("Is there opportunity here?") after receiving confirmatory
research is the human-side detection signal — research that produced genuine
discovery does not produce confusion.

**Analyst-exhibits-pattern-being-analyzed:** this session's /www output is
itself an instance of the pattern. The /www investigated 6 tracks, found that
5 already had handoffs, and produced a 500-line confirmatory concept anyway.
The act of researching the pattern is the pattern. The cross-cutting finding
("thin layer over existing substrate") was undercut by the act of producing
it — a 500-line concept is not a thin layer over 5 existing handoffs; it's a
6th integration artifact. See [[reactive-pattern-matching-and-closure-pressure]]
for the underlying mechanism: the model's closure pressure drives it to
produce *something*, and the available action (research) is easier than the
needed action (execution).

## Why the /tp opportunity scan exacerbates it

The /tp opportunity scan treats "has an open handoff with a direction" as
equivalent to "is an open opportunity." It is not. An open handoff with
acceptance criteria is **execution-ready work**, not a **research opportunity**.
Surfacing it as an opportunity routes it to /www instead of to /go or
implementation.

## What this means for our workspace

The fix is structural, not behavioral. A behavioral rule ("do less research")
doesn't fire under closure pressure — same failure class as every other
behavioral rule ([[mechanical-enforcement-over-behavioral-reminder]]).

**Structural gate:** before /www or /tp explore runs on a /tp-surfaced track,
check whether a handoff already contains a direction + acceptance criteria.
If yes, the track's disposition is **execute or defer**, not **research**.
/www runs only on tracks with genuinely open uncertainties. This is the same
principle as [[mechanical-enforcement-over-behavioral-reminder]] — a behavioral
rule ("remember to check for existing handoffs before researching") won't fire
under closure pressure, but a structural gate in the /tp opportunity scan
(check handoff existence before surfacing as opportunity) will.

**Execution-first bias:** when the operator asks "is there opportunity here?"
after research, the default disposition should be "execute one thing" —
not "research more." The research already produced the directions; the
opportunity is in building. This connects to [[decision-and-fix-documentation-
rule]]: the rule says "if you just shipped something, stop and ask: did I
document the decision?" The complementary question this pattern surfaces is:
"if you just documented something, stop and ask: should I be executing
instead of documenting more?"

**Substrate-volume awareness:** the workspace's search infrastructure (qmd,
Track D's FTS5 target) is itself degraded by substrate volume. More concepts
and handoffs mean more noise in search results, which makes it harder to find
the relevant prior work — which in turn leads to re-researching what's already
documented. The substrate-accumulation loop doesn't just waste time; it
actively degrades the system's ability to find its own knowledge.

## Structural fix — implemented (2026-07-29)

The structural gate described above was implemented in session 019fa276:

1. **`workspace_opportunity_scan.py`** gained `scan_open_handoffs()` — scans
   `P:/docs/handoffs/` for OPEN handoffs, parses frontmatter status, checks
   for acceptance criteria sections, and separates results into two groups:
   `EXECUTE_OR_DEFER` (has acceptance criteria) vs `RESEARCH` (no criteria).
   Receipt: `P:/.agents/scripts/workspace_opportunity_scan.py` lines 80-130,
   commit `a63a785`.

2. **`/tp` SKILL.md** `/tp explore` section gained the "Opportunity scan gate"
   instruction: before tagging any opportunity as `RESEARCH`, cross-reference
   against the open handoffs from the scan output. Tracks with acceptance
   criteria get `EXECUTE_OR_DEFER` and are NOT routed to `/www`. Receipt:
   `C:/Users/brsth/.grok/skills/tp/SKILL.md` lines 530-548, commit `66f37fc`.

The gate has an explicit exception: if context has materially changed since
the handoff was written, the track can be tagged `RESEARCH — context shift`
with a one-sentence justification. This prevents the gate from blocking
legitimate re-investigation while making the override auditable.

**What this does NOT close:** the behavioral layer. The gate is a prompt
instruction in SKILL.md, not a mechanical hook. It fires when /tp explore
runs and the agent follows the instruction, but it does not fire under
closure pressure the way a hook would. A future session may build a
mechanical equivalent (e.g., a /tp pre-flight script that blocks RESEARCH
tags on tracks matching open handoffs). The prompt layer is the first
structural step; the mechanical layer is the second.

## Falsifier

This pattern is wrong if:
- The 169 handoffs are mostly closed/executed (not open) → the ratio is fine
- Future /www cycles consistently discover NEW directions (not confirm existing
  ones) → the research is genuinely productive, not self-reinforcing
- The operator never expresses confusion after receiving research output →
  the detection signal doesn't fire because it doesn't need to
- **The structural gate (2026-07-29) prevents the pattern from recurring** →
  if future /tp explore runs correctly separate EXECUTE_OR_DEFER from
  RESEARCH, the gate worked. If /tp explore still routes execution-ready
  tracks to /www, the prompt-layer gate was insufficient and the mechanical
  layer is needed.

## Receipts

- **Handoff count:** `Get-ChildItem -Path "P:/docs/handoffs/" -Directory`
  returned 169 directories (this session, 2026-07-27)
- **/tp critique:** fresh subagent (glm-5-2, 7 tool calls) found 5 of 6
  tracks already had handoffs; cross-verified by reading qmd-fts5 and
  agents-md-refactor handoffs (both dated 2026-07-27, same day as the /www)
- **Prior meta-assessment:** [[research-vs-design-vs-architect-skills-and-www-
  self-assessment]] (2026-07-26) recommended paring /www ceremony one day
  before this session produced a 500-line confirmatory /www concept
