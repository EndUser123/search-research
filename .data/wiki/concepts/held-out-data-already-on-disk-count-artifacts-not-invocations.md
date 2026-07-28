---
title: "Held-out data already on disk: count artifacts not invocations"
created: 2026-07-28
source: session-019fa94a (/tp review of plan-writer skill improvements)
tags: [held-out-validation, skill-improvement, artifacts-vs-invocations, validation-corpus, false-zero-data]
summary: >
  When validating skill improvements via held-out testing (T23), the held-out
  data may already exist as artifacts on disk. Counting skill-brand invocations
  instead of artifacts produces a false "zero held-out sessions" conclusion.
  The plan-writer skill had 1 post-consolidation invocation but 24 plan files
  on disk — all valid held-out data because the planning logic was inherited
  wholesale from predecessor skills. Also documents the structure-vs-function
  conflation pattern: "the review loop exists" was treated as "the review loop
  checks for over-engineering," causing the highest-leverage improvement to be
  incorrectly marked "already applied."
agent: grok
host: grok
cognitive_load: 2
verification: observed
sources:
  - session-019fa94a transcript (/tp review with glm-5-2 subagent)
relations:
  - target: wiki/concepts/skill-development-portfolio.md
    type: refines
  - target: wiki/concepts/spec-driven-development-tools-and-planning-workflows.md
    type: extends
  - target: wiki/concepts/maker-checker-required-for-enforcement-work.md
    type: related
  - target: wiki/concepts/scope-matching-verification-discipline.md
    type: related
---

# Held-out data already on disk: count artifacts not invocations

## Decision context

**Why this was needed:** a `/tp` review of the plan-writer skill improvements
handoff concluded "zero held-out sessions exist" — both the cross-family
subagent (glm-5-2) and the orchestrator confirmed this. The conclusion was
**wrong**. The operator asked "can't we test this idea on our transcripts?"
and a 30-line Python script scanning `docs/superpowers/plans/` revealed 24
plan files on disk, 23 of which were valid held-out data for the planning
logic being improved.

The root cause: we counted **plan-writer-brand invocations** (1 post-consolidation)
instead of counting **plan artifacts** (24 on disk). Because plan-writer was
consolidated from `/plan` + `writing-plans` and inherited their logic wholesale,
the pre-consolidation plans are valid held-out data for evaluating improvements
to that logic.

## The pattern

When asked "do we have data to validate this skill improvement?", the wrong
question is "how many times has this skill been invoked?" The right question
is "what artifacts has this skill (or its predecessors) produced?"

**Failure mode:** a skill is consolidated or renamed. The new skill has N=1
invocations. The improvement proposal says "zero held-out sessions exist."
But the predecessor skill produced dozens of artifacts that implement
substantially the same logic. Those artifacts ARE held-out data.

**Correct framing:** count artifacts (plans, designs, handoffs, wiki entries,
code reviews — whatever the skill produces), not invocations (how many times
the skill was called by name). Artifacts persist on disk; invocations don't.
The artifact is the evidence; the invocation is the label.

## Evidence from this session

| What was counted | Count | Conclusion |
|---|---|---|
| plan-writer-brand invocations post-consolidation | 1 | "zero held-out sessions" |
| Plan files in `docs/superpowers/plans/` | 24 | 23 valid held-out data points |
| Plans matching AGENTS.md violation patterns (destructive git, full-file write) | **0 of 24** | Imp 5 addresses a failure mode that never occurred |
| Plans with traceability markers | **0 of 24** | Imp 6 addresses a failure mode with no local evidence |

The held-out data was **already on disk** and already answered the validation
questions. The "zero held-out sessions" claim in both the subagent critique and
the orchestrator synthesis was wrong — and would have led to deferring
improvements that the existing data could have validated immediately.

## Structure-vs-function conflation (companion finding)

The handoff marked wiki improvement #6 ("simplicity check in review loop") as
"already applied" because the mandatory review loop **structure** existed
(the loop spawns a fresh subagent, has round limits, tracks findings). But the
loop's reviewer prompt had **zero over-engineering dimensions** — its 7 attack
dimensions were all bug-focused. The loop existed as a mechanism but did not
carry the dimension it was supposed to carry.

This is a generalizable conflation: **confusing the existence of a mechanism
with the presence of the function that mechanism was supposed to deliver.**

| Structure (exists) | Function (missing) |
|---|---|
| Review loop spawns a subagent | Subagent checks for over-engineering |
| Hook is registered in settings.json | Hook catches the intended failure class |
| Validator script exists | Validator's regex matches the real pattern |
| Test file exists | Test covers the actual behavior, not the contract surface |

This connects to [[scope-matching-verification-discipline]]: the same blind
spot class that lets enforcement code pass its own tests while having
exploitable bypasses. Here, the "test" (the handoff's "already applied"
claim) passed because it checked for structure existence, not function
presence. It also connects to [[maker-checker-required-for-enforcement-work]]:
the agent that marked improvement #6 "already applied" was the same agent
that wrote the review loop — it shared the blind spot of what the loop
actually checked for.

## What this means for our workspace

1. **Before claiming "no held-out data exists," grep the artifact directory.**
   If the skill produces files (plans, designs, reviews, wiki entries), those
   files are held-out data. A 30-line Python script will answer most validation
   questions faster than waiting for future invocations.

2. **When a skill is consolidated or renamed, the predecessor's artifacts
   remain valid held-out data** for the inherited logic. The skill name
   changed; the planning logic (triggers, completeness checks, TDD format)
   did not.

3. **When marking an improvement "already applied," verify the FUNCTION not
   just the STRUCTURE.** The decomposition checkpoint (structure: a section
   in the skill) was genuinely applied. The review loop (structure: the loop
   mechanism) was genuinely applied. But the simplicity dimension (function:
   the reviewer prompt asking about over-engineering) was NOT applied — it
   was conflated with the loop's existence.

4. **T23 (held-out validation) should be refined:** before deferring an
   improvement for lack of held-out data, scan the artifact directory. The
   held-out data may already exist. This refines
   [[skill-development-portfolio]] technique 15 (held-out validation): the
   test set is not "future sessions" — it's "existing artifacts produced
   by this skill or its predecessors."

## The Verschlimmbesserung irony

The 4 proposed improvements were designed to prevent over-engineering. Adding
4 checks to a 639-line skill IS the accretion pattern — the skill that prevents
bloat was itself bloating. Böckeler's warning applies to skill improvement
itself: elaborate workflows amplify existing challenges rather than solving them.
This is the same closure-pressure-accretion pattern documented in
[[reactive-pattern-matching-and-closure-pressure]] — the model adds
defense-in-depth under pressure because adding feels safer than dropping.

The resolution: the highest-leverage improvement (adding 1 line — dimension 8
to the reviewer prompt) was the one most directly connected to the root cause.
The 4 more peripheral improvements (problem-size gate, length budget, AGENTS.md
check, traceability matrix) were accretion. The held-out data confirmed this:
the failure modes they addressed had zero observed instances across 24 plans.

## Falsifier

This finding would be wrong if: (a) the pre-consolidation artifacts use
substantially different logic than the consolidated skill (making them invalid
held-out data) — but plan-writer inherited `/plan`'s triggers and completeness
checks verbatim; (b) the artifact scan missed relevant patterns — possible
but the key finding (zero AGENTS.md violations) is a negative result that
doesn't depend on pattern completeness; (c) future sessions show the dropped
improvements would have caught real failures — falsifiable by tracking whether
AGENTS.md violations or traceability gaps emerge in future plans.

## Receipts

- **24 plan files analyzed:** `python P:/tmp/plan_analysis.py` scanned all files in `P:/docs/superpowers/plans/`. Zero matches for destructive git, full-file write, or AGENTS.md violation patterns across all 24.
- **Reviewer prompt had zero over-engineering dimensions:** `C:/Users/brsth/.grok/skills/plan-writer/SKILL.md` lines 510-520 (pre-edit). Verified by grep and read_file. Dimension 8 added in commit `0af0b5a`.
- **Handoff's "zero held-out sessions" claim:** `P:/docs/handoffs/plan-writer-skill-improvements-20260728/HANDOFF.md` lines 128, 167.
- **Subagent confirmed "zero held-out":** glm-5-2 subagent grep for post-consolidation plans returned only the training session. The subagent counted invocations, not artifacts — same error as the orchestrator.
