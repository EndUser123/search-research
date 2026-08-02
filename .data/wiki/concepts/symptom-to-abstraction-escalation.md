---
title: "Symptom-to-abstraction escalation: generalize session-specific fixes to workspace-level abstractions"
created: 2026-08-02
source: session-019fc318 (/tp on operator's "symptomatic focused" question)
tags: [generalization, iceberg-model, session-quality, mechanical-enforcement, decision, retrieval-gate, anchor-preservation]
summary: >
  Before shipping a session-specific finding or fix, ask what class of problem it
  belongs to and whether a workspace-level abstraction (skill, rule, script, config,
  hook, or wiki concept) would fix the whole class. Implement the generalizable fix
  instead of — or in addition to — the symptomatic fix. This is the Iceberg Model
  applied to agent output: Events (session-specific finding) → Patterns (class of
  issue) → Structures (workspace gap) → Mental Models (belief keeping the gap).
  The concept was previously institutionalized as an AGENTS.md rule + /close gate
  (2026-07-31) but the rule was accidentally deleted in a full-file rewrite
  (2026-08-01). The /close mechanical gate survived. This concept unifies the 10+
  scattered expressions of the same move into a single canonical home.
agent: grok
host: grok
cognitive_load: 3
verification: multi-source-verified
sources:
  - "session-019fc318 (/tp two-lens critique — fresh subagent found the deleted rule)"
  - "commit a446b72 (2026-07-31): original meta-checkpoint rule added to AGENTS.md"
  - "commit 01366cc (2026-07-31): meta_checkpoint gate added to close_accounting.py"
  - "commit e7da24f (2026-08-01): full-file AGENTS.md rewrite accidentally deleted the rule"
relations:
  - target: wiki/concepts/mechanical-enforcement-over-behavioral-reminder.md
    type: foundation — this concept is enforced by mechanical gates, not behavioral rules
  - target: wiki/concepts/extract-moves-not-conditions-tp-enhancements.md
    type: related — reproducibility of quality moves; generalization is a move, not a condition
  - target: wiki/concepts/analysis-over-action-knowledge-capture-without-application.md
    type: related — the analysis-action gap; escalation bridges it
  - target: wiki/concepts/convergence-gap-rca-symptom-restatement-toulmin-enforcement.md
    type: related — symptom-restatement in RCA; same failure mode in a different skill
  - target: wiki/concepts/problem-first-systems-decomposition.md
    type: related — decomposition before solution; escalation after solution
  - target: wiki/concepts/implement-now-vs-handoff-standing-question.md
    type: complements — disposition for every finding; escalation determines which disposition
---

# Symptom-to-abstraction escalation

## The move

Before shipping a session-specific finding or fix, ask what class of problem it
belongs to and whether a workspace-level abstraction (skill, rule, script, config,
hook, or wiki concept) would fix the whole class. Implement the generalizable fix
instead of — or in addition to — the symptomatic fix.

**Trigger question (operator phrasing):** "Is there an abstraction we should consider
that results in a more generally applicable fix?"

## The escalation ladder (Iceberg Model)

Applied from systems thinking (Meadows/Senge) — each rung is harder to change but
more durable. The move is to climb the ladder before settling for the Event-level fix.

| Rung | Level | Question | Fix target |
|------|-------|----------|------------|
| 1 | **Events** | What happened this session? | Session-specific fix |
| 2 | **Patterns** | Does this recur, or could it? | Generalization is mandatory if yes |
| 3 | **Structures** | What workspace element produces the pattern? | Skill, rule, script, config, hook, or wiki concept |
| 4 | **Mental models** | What belief keeps the structure in place? | Paradigm shift (rare; only when structure fix stalls) |

**Decision protocol:**
1. State the Event-level finding (one sentence).
2. Pattern test: does this recur, or could it? If yes, escalation is mandatory.
3. Structure test: what workspace element produces the pattern? The fix lives there.
4. Ship the highest-rung fix that is practical. If you ship Event-level only, state why.

## Why this is hard for LLMs specifically

The same closure pressure documented in [[reactive-pattern-matching-and-closure-pressure]]
pushes the agent toward the Event-level fix: it's fast, visible, and resolves the
immediate problem. The operator's question ("is there an abstraction?") is the
external nudge that counteracts this pressure. Without it, the agent ships the
symptomatic fix and moves on.

This is the same failure class as [[convergence-gap-rca-symptom-restatement-toulmin-enforcement]]:
LLMs produce symptom-restatements dressed as root causes because the convergence
question (what single mechanism unifies these causes?) is a behavioral prompt that
gets answered performatively. The escalation question has the same risk — without
mechanical enforcement, it gets answered performatively too.

## Enforcement (mechanical, not behavioral)

Per [[mechanical-enforcement-over-behavioral-reminder]]: behavioral rules in
AGENTS.md don't fire under session pressure. The fix is mechanical enforcement.

| Enforcement surface | Mechanism | Status |
|---------------------|-----------|--------|
| `/close` meta_checkpoint gate Q1 | Blocks CLOSE COMPLETE until generalization question answered | **ALIVE** (close_accounting.py:2558-2589, close_runner.py:57) |
| AGENTS.md retrieval gate | One-line gate: "before shipping a fix, ask if there's an abstraction" | **RESTORED** (this session, was accidentally deleted in e7da24f) |
| `/tp session` standing question | "What patterns generalize beyond this session?" | **UPGRADED** (broadened from skills-only to all workspace abstractions) |
| AGENTS.md anchor-preservation check | close_accounting.py validates required anchor sections exist | **NEW** (this session — prevents the loss that generated this concept) |
| close-check.rhai classification gap | Workflow Agent A must treat GATES_REQUIRING_RESOLUTION violations as fail | **FIXED** (this session) |

## History (the failure that motivates the protocol)

The meta-checkpoint rule ("Did I generalize the lesson?") was added to AGENTS.md on
2026-07-31 (commit a446b72) with a mechanical twin in close_accounting.py
(commit 01366cc). On 2026-08-01, a full-file AGENTS.md rewrite (commit e7da24f)
accidentally deleted the rule. The /close gate survived because it was in a
Python file, not a prose file.

This loss is itself an instance of the Iceberg Model:
- **Event:** the generalization rule was deleted in a rewrite.
- **Pattern:** full-file AGENTS.md rewrites silently delete sections; nothing
  verifies section-preservation.
- **Structure:** AGENTS.md has no anchor-preservation check — a full-file replace
  can drop any mandatory section without detection.
- **Mental model:** "It's in AGENTS.md so it's enforced" — the wiki concept and
  handoff still claimed the rule was live after it was deleted.

The concept was destroyed by the very failure mode it was designed to catch.

## What this means for our workspace

1. **The wiki concept is the canonical home.** When a future session produces a
   symptomatic fix, the retrieval gate in AGENTS.md points here. The concept
   unifies 10+ scattered expressions (see "Existing expressions unified here"
   below).

2. **The anchor-preservation check is the root-cause fix** for the loss class.
   It prevents ANY future full-file AGENTS.md rewrite from silently deleting a
   mandatory section.

3. **The /close gate Q1 wording matters.** "Did I generalize the lesson?" conflates
   capture (writing a wiki concept) with escalation (implementing the abstraction).
   The reworded Q1 asks about the abstraction itself, not just documentation.

## Existing expressions unified here

This concept was scattered across the workspace without a single canonical home.
These expressions remain valid in their contexts; this concept cross-links them:

- `/tp explore` Directives 8 (Iceberg Model) and 9 (Leverage Points) — fullest
  conceptual treatment. Fire only when `/tp explore` is invoked.
- `/tp session` standing generalization question — procedural home. Fires at
  session end.
- AGENTS.md "Optimal long-term solution", "Problem-first decomposition",
  "Root-cause clustering" — fix-selection principles for the current problem.
  Adjacent (choosing the general solution for THIS problem), not identical
  (escalating from THIS problem to the CLASS).
- [[extract-moves-not-conditions-tp-enhancements]] — reproducibility of quality
  moves. Generalization is a move, not a condition.
- [[analysis-over-action-knowledge-capture-without-application]] — the gap between
  analysis and action. Escalation bridges it.
- [[convergence-gap-rca-symptom-restatement-toulmin-enforcement]] — symptom-vs-cause
  in RCA. Same failure mode in a different skill.
- [[problem-first-systems-decomposition]] — decomposition before solution.
  Escalation after solution.
- [[mechanical-enforcement-over-behavioral-reminder]] — why this is enforced by
  gates, not prose.

## Falsifier

This concept is wrong if, within 6 months:
- The anchor-preservation check produces false positives (flags sections that
  were intentionally renamed or restructured) — would indicate the anchor list
  is too brittle.
- The escalation question in /close Q1 is answered performatively (model writes
  "generalized to wiki concept X" but X doesn't actually exist) — would indicate
  the gate needs an existence check, not just a text answer.
- Sessions consistently produce session-specific fixes that genuinely shouldn't
  be generalized — would indicate escalation is over-applied.
