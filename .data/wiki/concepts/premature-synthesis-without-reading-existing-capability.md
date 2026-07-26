---
title: "Premature synthesis without reading existing capability"
created: 2026-07-26
source: session-20260726
tags: [failure-pattern, narrative-closure, preflight, skill-capability-claims, root-cause]
summary: >
  A recurring failure class where the agent synthesizes a recommendation or
  capability claim without first reading the existing implementation. The
  narrative-closure pressure that produces confident-sounding output overrides
  the read-before-claim rule when the synthesis feels "obvious." The preflight
  mandate in AGENTS.md exists but does not fire reliably for skill-capability
  claims (claims about what an existing skill can or cannot do). This concept
  distinguishes itself from adjacent narrative-closure concepts by focusing on
  the specific pattern: skill exists → claim what it does without reading it →
  user catches the error in one sentence.
agent: grok
host: grok
cognitive_load: 2
verification: multi-source-verified
relations:
  - target: wiki/concepts/premature-closure-narrative-sufficiency-external-approaches.md
    type: refines
  - target: wiki/concepts/subagent-synthesis-report-gate.md
    type: complements
  - target: wiki/concepts/documented-deferral-substitutes-for-action.md
    type: related
---

# Premature synthesis without reading existing capability

## Decision context

**Why this knowledge was needed:** Session 019f8b39 (2026-07-23 → 2026-07-26) produced two independent instances of the same failure class:

1. **E10 — /tp critique wrong about execute-plan consolidation.** I claimed that `execute-plan` and `executing-plans` had "different mechanisms" that prevented consolidation into `/go`, without having read `/go`'s SKILL.md. The user corrected in one sentence: "I don't understand why Go cannot absorb those two other skills." When I actually read `/go/SKILL.md`, the plan-execute profile already had DAG parsing, worktree isolation, and per-task verification — the consolidation was straightforwardly possible.

2. **E12 — plan-writer name collision.** I created the consolidated planning skill with the name `writing-plans`, colliding with an existing skill of that name, without checking whether the name was already in use. The user corrected: "why did you use that skill name?"

Both errors share the same structure: **the agent synthesized a confident claim about an existing capability without reading the file that defines it.** The user caught both via single-sentence pushback. The root cause is not missing knowledge — the preflight mandate exists in `~/.grok/AGENTS.md`. The root cause is that narrative-closure pressure overrides the mandate when the synthesis feels "obvious."

This is the same failure class as the 2026-07-20 cc-council incident, where subagent synthesis was propagated unchecked into 5+ report sections without spot-checking against the file inventory already in context.

## The failure pattern

```
PRECONDITION: An existing skill/file/capability is relevant to the current task.
TRIGGER:      The agent needs to make a claim about what that capability does,
              or a decision that depends on its behavior.
FAILURE:      The agent synthesizes the claim/decision from context, naming
              conventions, or prior assumptions — WITHOUT reading the file.
CATCH:        The user corrects in one sentence (because they know the file's
              actual contents).
ROOT CAUSE:   Narrative-closure pressure. The synthesis feels "obvious" or
              "sufficient," so the read-before-claim rule does not fire.
```

This is structurally different from "the agent didn't know the file existed" (that's a search failure). Here the agent knows the file exists but does not read it before claiming what it does.

## Why the preflight mandate does not fire reliably

The `~/.grok/AGENTS.md` "Mandatory Preflight" section states:

> Before any **capability claim** (asserting that a capability is existing, missing, duplicated, obsolete, active, or safe to replace) or **irreversible change**... invoke the package skill `preflight` first.

The mandate fires reliably for:
- **Irreversible changes** (deleting code, changing defaults) — the stakes are high enough that the mandate's gravity is felt.
- **Cross-system capability claims** (asserting a feature is missing across the workspace) — the scope is broad enough that the agent feels the need to verify.

The mandate does **not** fire reliably for:
- **Skill-capability claims** ("skill X does Y" or "skill X cannot do Z") — the claim feels local and verifiable-by-reasoning, so the agent skips the read.
- **Naming decisions** ("I'll call this skill X") — feels like a creative choice, not a capability claim, so the mandate does not trigger.

The gap is that **skill-capability claims are capability claims** (they assert what an existing skill does), but the agent does not classify them as such when the claim feels obvious.

## Distinguishing from adjacent concepts

- **[[premature-closure-narrative-sufficiency-external-approaches]]** covers the general pattern of narrative-closure pressure producing premature conclusions. This concept **refines** that one for the specific sub-pattern: the closure pressure is about an existing capability, and the fix is reading the file (not external verification).

- **[[subagent-synthesis-report-gate]]** covers the specific instance where a subagent's synthesis is propagated by the orchestrator without spot-checking. This concept **complements** that one: the same closure pressure operates even without a subagent in the loop — the agent's own synthesis is sufficient to produce the error.

- **[[documented-deferral-substitutes-for-action]]** covers the pattern where documenting an action substitutes for taking it. This is **related** — the agent "documents" what a skill does (synthesizes a claim) instead of "taking the action" (reading the file).

## What this means for our workspace

The intervention tier (from AGENTS.md § "Minimal sufficient intervention") is:

1. **AGENTS.md rule** (exists) — the preflight mandate covers capability claims.
2. **Skill edit** (candidate) — a `/tp` or `/go` sub-step that explicitly checks "did you read the SKILL.md of the skill you're making a claim about?"
3. **Hook** (heavier) — a PreToolUse or Stop hook that detects capability-claim language ("skill X does Y", "X cannot do Z") without a corresponding file read in the recent tool-call window.

The current state is tier 1 (rule exists, fires unreliably). The session 019f8b39 AAR's `intervention_confidence: MEDIUM` reflects this: the rule is on the books but the structural fix (tier 2 or 3) has not shipped.

**Near-term action:** when making a claim about what an existing skill does, the agent should treat the claim as a capability claim (triggering the preflight mandate) regardless of how "obvious" the claim feels. The heuristic: if the claim contains a skill name + a verb ("does", "cannot", "already has", "doesn't support"), read the SKILL.md first.

## Falsifier

This concept is wrong or obsolete when:
- The preflight mandate fires reliably for skill-capability claims across 10+ sessions without a single instance of this failure pattern, OR
- A structural fix (skill edit or hook) ships and eliminates the pattern, making this concept a historical reference rather than an active concern.

Until one of those conditions holds, this concept remains active.

## Receipts

- AAR report: `P:/.artifacts/aar/019f8b39-95e3-7121-a8de-4e3f117e511a/aar-report.md` — episodes E10, E12; recurring pattern P1; lesson L1.
- Session 019f8b39 summary — user corrections: "I don't understand why Go cannot absorb those two other skills" and "why did you use that skill name?"
- `~/.grok/AGENTS.md` § "Mandatory Preflight" — the existing rule that does not fire reliably for this claim class.
- Adjacent concept: `premature-closure-narrative-sufficiency-external-approaches.md:184` — discusses narrative-closure pressure in the general case.

## Sources

- Session 019f8b39 AAR (internal, 2026-07-26) — two independent instances of the pattern with user-correction receipts.
- Session 2026-07-20 cc-council incident (referenced in AGENTS.md) — same failure class in a subagent-synthesis context.
