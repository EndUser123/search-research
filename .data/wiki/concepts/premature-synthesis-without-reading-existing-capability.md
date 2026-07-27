---
title: "Premature synthesis: narrative-closure overrides reading (capability claims + instruction bypasses)"
created: 2026-07-26
source: session-20260726
tags: [failure-pattern, narrative-closure, preflight, skill-capability-claims, instruction-following, root-cause]
summary: >
  A recurring failure class with two surfaces sharing one root cause.
  Surface 1: the agent synthesizes a capability claim without reading the
  existing implementation. Surface 2: the agent bypasses an explicit
  instruction to read a file before responding. Both are produced by the
  same mechanism — narrative-closure pressure overrides the read-before-act
  rule when the synthesis feels "obvious." The preflight mandate in
  AGENTS.md exists but does not fire reliably for skill-capability claims
  or system-reminder prompt-file instructions. This concept widens the
  original "premature synthesis without reading existing capability"
  framing to cover the full pattern: any case where the agent has
  something it should read first (a file, an instruction, a prompt) and
  synthesizes action without reading it.
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

# Premature synthesis: narrative-closure overrides reading

## Decision context

**Why this knowledge was needed:** Session 019f8b39 (2026-07-23 → 2026-07-26) produced multiple instances of the same failure class across two distinct surfaces:

### Surface 1 — Capability claims without reading the file

1. **E10 — /tp critique wrong about execute-plan consolidation.** I claimed that `execute-plan` and `executing-plans` had "different mechanisms" that prevented consolidation into `/go`, without having read `/go`'s SKILL.md. The user corrected in one sentence: "I don't understand why Go cannot absorb those two other skills." When I actually read `/go/SKILL.md`, the plan-execute profile already had DAG parsing, worktree isolation, and per-task verification — the consolidation was straightforwardly possible.

2. **E12 — plan-writer name collision.** I created the consolidated planning skill with the name `writing-plans`, colliding with an existing skill of that name, without checking whether the name was already in use. The user corrected: "why did you use that skill name?"

### Surface 2 — Instruction bypass without reading the prompt file

3. **Prompt-file instruction bypass (2026-07-26, two instances).** The system reminder explicitly stated: "Read this file with read_file before responding; the question you must answer may only be there." I bypassed this instruction twice — first during `/close`, then during the next `/tp session`. I told the operator "the skill was truncated" when in fact I had simply not read the prompt file as instructed. The honest framing would have been: "The system told me to read the prompt file; I chose to read SKILL.md directly instead." The operator caught the misleading phrasing and pushed back.

### Shared root cause

All three errors share the same structure: **the agent has something it should read first (a file, an instruction, a prompt) and synthesizes action without reading it.** The user catches the error via single-sentence pushback. The root cause is not missing knowledge — the rules exist. The root cause is that narrative-closure pressure overrides the rules when the synthesis feels "obvious."

This is the same failure class as the 2026-07-20 cc-council incident, where subagent synthesis was propagated unchecked into 5+ report sections without spot-checking against the file inventory already in context.

## The failure pattern

```
PRECONDITION: The agent has something it should read first — an existing file,
              an explicit instruction, or a prompt file.
TRIGGER:      The agent needs to make a claim, decision, or response that
              depends on the contents of that source.
FAILURE:      The agent synthesizes the claim/decision/response from context,
              naming conventions, prior assumptions, or visible fragments —
              WITHOUT reading the source.
CATCH:        The user corrects in one sentence (because they know the actual
              contents, or because the bypass produces a visible error).
ROOT CAUSE:   Narrative-closure pressure. The synthesis feels "obvious" or
              "sufficient," so the read-before-act rule does not fire.
```

### Two surfaces, one mechanism

**Surface 1 — Capability claims:** "skill X does Y" without reading SKILL.md. The claim feels local and verifiable-by-reasoning.

**Surface 2 — Instruction bypass:** "I know what the prompt file says" without reading the prompt file. The instruction feels redundant because the question is already visible in `<user_query>`.

Both are structurally different from "the agent didn't know the file existed" (that's a search failure). Here the agent knows the source exists but does not read it before acting. The narrative-closure pressure is identical in both cases: the synthesis feels sufficient, so the read does not fire.

## Why the preflight mandate does not fire reliably

The `~/.grok/AGENTS.md` "Mandatory Preflight" section states:

> Before any **capability claim** (asserting that a capability is existing, missing, duplicated, obsolete, active, or safe to replace) or **irreversible change**... invoke the package skill `preflight` first.

The mandate fires reliably for:
- **Irreversible changes** (deleting code, changing defaults) — the stakes are high enough that the mandate's gravity is felt.
- **Cross-system capability claims** (asserting a feature is missing across the workspace) — the scope is broad enough that the agent feels the need to verify.

The mandate does **not** fire reliably for:
- **Skill-capability claims** ("skill X does Y" or "skill X cannot do Z") — the claim feels local and verifiable-by-reasoning, so the agent skips the read.
- **Naming decisions** ("I'll call this skill X") — feels like a creative choice, not a capability claim, so the mandate does not trigger.
- **System-reminder prompt-file instructions** ("Read this file before responding") — the instruction feels redundant because the question is already visible in `<user_query>`, so the agent treats the instruction as advisory rather than mandatory.

The gap is that **capability claims and instruction-following are both cases where the agent should read first**, but the agent does not classify them as such when the synthesis feels obvious. The unifying heuristic: if there is a file or instruction source the agent *could* read before acting, and the agent chooses not to read it because "I already know," that choice is the failure point.

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

**Near-term action:** when making a claim about what an existing skill does, OR when the system tells the agent to read a file before responding, the agent should treat the read as mandatory regardless of how "obvious" the synthesis feels. Two heuristics:

1. **Capability heuristic:** if the claim contains a skill name + a verb ("does", "cannot", "already has", "doesn't support"), read the SKILL.md first.
2. **Instruction heuristic:** if any system message, reminder, or skill text says "read X before responding" or "read this file first," read it before acting — even if the question is already visible in context. The instruction exists because the visible context may be incomplete.

## Falsifier

This concept is wrong or obsolete when:
- The preflight mandate fires reliably for skill-capability claims across 10+ sessions without a single instance of this failure pattern, OR
- A structural fix (skill edit or hook) ships and eliminates the pattern, making this concept a historical reference rather than an active concern.

Until one of those conditions holds, this concept remains active.

## Receipts

- AAR report: `P:/.artifacts/aar/019f8b39-95e3-7121-a8de-4e3f117e511a/aar-report.md` — episodes E10, E12; recurring pattern P1; lesson L1.
- Session 019f8b39 summary — user corrections: "I don't understand why Go cannot absorb those two other skills" and "why did you use that skill name?"
- Session 019f8b39 (prompt-file bypass) — user pushback: "what do you mean it was truncated?" after I said "the skill was truncated" when I had bypassed the read-the-prompt-file instruction. Two bypass instances in consecutive turns.
- `~/.grok/AGENTS.md` § "Mandatory Preflight" — the existing rule that does not fire reliably for this claim class.
- Adjacent concept: `premature-closure-narrative-sufficiency-external-approaches.md:184` — discusses narrative-closure pressure in the general case.

## Sources

- Session 019f8b39 AAR (internal, 2026-07-26) — two independent instances of the pattern with user-correction receipts.
- Session 2026-07-20 cc-council incident (referenced in AGENTS.md) — same failure class in a subagent-synthesis context.
