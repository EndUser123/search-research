# HANDOFF: Requirements-validation lens — new skill (spike output)

**Created:** 2026-08-12
**Session:** 019ff685-ecb9-7193-9743-660be86de0fb
**Status:** OPEN — spike complete, build not started
**Chronicity:** chronic
**Assignee:** unassigned
**Related:** `P:/.data/wiki/concepts/great-adversarial-review-skill-design-patterns.md` (spike source)

## Problem

The workspace's adversarial-review stack (`/risk`, `/tp`, `/wargame`) challenges
risk, framing, and assumptions — but NO skill validates **requirements validity**:
whether a requirement/spec/decision-input is complete, clear, consistent, and
unambiguous BEFORE it drives work. Identified in session 019ff685 via a `/tp`
coverage audit (2026-08-12): "/redteam challenges risk, not requirements."

The gap's practical cost: vague requirements reach `/risk` (which assumes the
requirement is given) or reach implementation directly (where ambiguity
surfaces as rework).

## Spike output (this handoff's basis)

The spike researched the prior art and made a shape decision:

- **Shape decision: NEW lightweight skill** (working name `/req-check`), NOT a
  `/risk` phase. Rationale (design-choice audit):
  - **CONCEPT** — requirements-validation is a different judgment type
    (completeness/clarity/consistency of the requirement) than risk
    (probability/severity of failure). /risk's plan/spec scan checks
    feasibility/dependencies/missing-scope; it does not check whether the
    requirement is well-formed.
  - **SCOPE** — conditional: fires when requirements are defined/refined
    (session start, before implementation, at decision points), not always.
  - **FIT** — session-scoped, multi-terminal-isolated, same conventions as
    sibling review skills.
  - **ALTERNATIVES REJECTED** — (a) /risk plan/spec extension: conflates
    requirements-quality with risk, muddies /risk's escalation ladder;
    (b) adopt GitHub spec-kit wholesale: it's a full SDD pipeline
    (constitution/specify/plan/tasks/implement) — we only need the validation
    slice, and it requires the `specify` CLI + uv install.

- **Prior art to model on** (all read during the spike):
  - GitHub spec-kit `/speckit.checklist` — "unit tests for English":
    generates custom quality checklists validating requirements completeness,
    clarity, consistency.
  - GitHub spec-kit `/speckit.clarify` — actively questions underspecified
    areas (one-question-at-a-time, recommended before planning).
  - GitHub spec-kit `/speckit.analyze` — cross-artifact consistency.
  - Decision Quality Checks (Calypso) — meaning-checks before treating inputs
    as decision-grade ("did we change what these tags mean?", "did 'resolved'
    get redefined?").
  - Kamsties/Berry/Paech 2001 — ambiguity-inspection checklists catch
    linguistic ambiguities but NOT model-dependent ones (scope-boundary
    receipt for the skill's limits).
  - Ladder of Inference backward-walk — walk a conclusion back to the
    observation it rests on.
  - SAST / Assumption-Based Planning — load-bearing assumption extraction.

## Scope

Build a new skill at `~/.grok/skills/req-check/SKILL.md` (name confirmable):

1. **Input**: a requirement/spec/decision-input (pasted, file path, or the
   session's active task).
2. **Phase 1 — Requirement-quality checklist** (spec-kit pattern): generate
   a domain-appropriate checklist; label each requirement item against it:
   COMPLETE / INCOMPLETE / AMBIGUOUS / INCONSISTENT / UNVERIFIABLE, with the
   specific defect quoted.
3. **Phase 2 — Clarify** (spec-kit.clarify pattern): one-question-at-a-time
   on underspecified items, each with a recommended answer; loop until the
   requirement is decision-grade.
4. **Phase 3 — Meaning-checks** (Decision Quality Checks): before the
   requirement is accepted, check that terms/definitions/comparability
   haven't drifted ("what does 'done' mean here?", "is this comparable to
   what we measured before?").
5. **Phase 4 — Assumption walk-back** (Ladder of Inference): extract
   load-bearing assumptions; each must state what evidence would disconfirm it.
6. **Output**: verdict (READY / NEEDS_CLARIFICATION / REJECT) + the defect
   list + the clarified requirement. Reuses the wiki-grounded pattern from
   /risk (query wiki for known requirement-failure patterns before scanning).
7. **Integration**: suggested by `/go` before implementation waves and by
   `/risk` when a plan/spec target has unclear requirements; does NOT
   auto-fire (operator-invoked, like sibling review skills).

## Acceptance criteria

1. `/req-check` validates a requirement's completeness, clarity, consistency,
   verifiability — mechanically checkable labels per item, not prose vibes
2. Clarify loop is one-question-at-a-time with recommended answers (grill-me
   pattern) and terminates (bounded iterations)
3. Meaning-checks fire before a requirement can be accepted as decision-grade
4. Assumptions extracted with disconfirming evidence required
5. Output includes READY / NEEDS_CLARIFICATION / REJECT verdict
6. Respects host invariants: session-scoped state, no cross-terminal writes,
   no shared-state mutation
7. Skill passes `/skill-dev measure` (paths resolve, host conformance,
   frontmatter complete) and is test-fired once

## Why not DO_NOW

~1-2 hours: new skill authoring + skill-dev validation + test-fire + wiki
concept for the requirement-failure patterns found on first real use. The
shape decision is made (this handoff); the build is mechanical from here but
was deferred from the spike session per the /www recommendation contract.
