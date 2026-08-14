---
title: "Mandatory Step Enforcement: Move Control Flow from Prose to Code"
created: 2026-07-20
source: session-2026-07-20 (/www research on structural enforcement)
tags: [enforcement, state-machine, harness-engineering, skill-execution, control-flow, close-skill, aar]
agent: grok
host: both
cognitive_load: 3
verification: multi-source-verified
summary: >
  When a skill step must not be skipped or downgraded, prose instruction is
  structurally insufficient. The only reliable enforcement is mechanical: the
  pipeline's control flow must make the step a precondition for the next step,
  not a suggestion the LLM can downgrade. Three implementation patterns:
  state-machine guarded transitions, scanner-side gates, and the linter-promotion
  pattern. All share one root insight: move enforcement from the LLM's context
  (advisory) to the pipeline's control flow (structural).
relations:
  - target: wiki/concepts/skill-enforcement-layers
    type: refines
  - target: wiki/concepts/skill-step-downgraded-from-action-to-note
    type: supports
  - target: wiki/concepts/skill-enforcement-deep-dive
    type: refines
---

## Summary

When a multi-step agent skill (like `/close`) requires that a particular step (like `/aar`) always execute before the pipeline completes, the instruction must live in the **control flow**, not in the **prose**. Prose instructions are advisory — they can be downgraded, softened, or skipped under context momentum. Code-enforced preconditions cannot.

This was demonstrated empirically in session 2026-07-20: the `/close` skill said "ask: Run /aar?" but the model wrote "recommend /aar" in a summary table and moved on. The step wasn't skipped — it was *downgraded* from an interactive action to a passive note. The root cause is structural: nothing in the close skill's machinery prevents emitting the summary without `/aar` having run.

## Key Findings

### 1. Prose enforcement fails under context momentum

The model's behavior at close-out time is dominated by momentum toward "fill the template and finish." Any step that breaks this momentum (asking the operator, running a sub-skill) competes with that momentum and loses. Stronger verbs ("run" vs "ask") help marginally but don't change the architecture — they're still prose, still advisory.

- EVIDENCE_GAP: no controlled experiment comparing strong-verb prose vs scanner-enforced gate on the same skill. The claim is inferred from the observed pattern + the 3-layer enforcement analysis.
- Assumption: context momentum is the dominant failure mode for skill-step downgrading, not capability gap or misunderstanding.

### 2. State machines enforce invariants; prose does not

Brightlume AI (April 2026) documents the principle directly:

> "The state machine enforces the invariant. These rules are enforced by the state machine, not by the LLM. If the agent is in the 'awaiting fraud check' state, it cannot transition to 'approved' without explicit fraud validation."

The architectural insight: the LLM is a component that produces output; the state machine is the controller that decides what happens based on that output. Don't let the LLM decide what happens next — constrain it to valid transitions.

For the `/close` case: the scanner (which already computes gate states) is the state machine. If it returns `loop.needed = true` with `retrospective` in `attention_gates` when friction is detected and no AAR artifact exists, the close summary cannot emit clean. The LLM literally cannot get a `loop.needed = false` until the AAR has run and produced an artifact.

### 3. The OpenAI harness-engineering principle: promote rules to code

OpenAI's harness-engineering team (February 2026) discovered the same pattern at scale:

> "When documentation falls short, we promote the rule into code."
> "Human taste is captured once, then enforced continuously on every line of code."
> "These constraints are enforced mechanically via custom linters."

Their approach: start with documentation (AGENTS.md). When the documentation is consistently ignored or downgraded, move the rule from documentation into mechanical enforcement (linters, CI gates, structural tests). The promotion is one-directional: code-enforced rules don't go back to prose.

### 4. Three implementation patterns, ordered by enforcement strength

| Pattern | Mechanism | Strength | Example in our environment |
|---|---|---|---|
| **State-machine guarded transitions** | Explicit states + entry/exit conditions; LLM cannot transition past the mandatory step without the precondition being met | Strongest | `close_accounting.py` returns `loop.needed = true` with `retrospective` in attention_gates |
| **Scanner-side gate** | The scanner blocks on a missing artifact; the LLM cannot produce a clean summary until the artifact exists | Strong | `close_accounting.py` checks for AAR artifact in session directory |
| **Summary template requires artifact path** | The template field requires a concrete path, not free text; empty or "skipped" is invalid | Medium | Template: `Retrospective: <aar-artifact-path or "no friction">` |
| **Prose instruction (strong verb)** | SKILL.md says "run /aar" with imperative language | Weak (advisory) | Current state of `/close` SKILL.md after this session's edit |

The first two are mechanical — they cannot be downgraded. The third is semi-mechanical (the LLM can lie, but the lie is visible). The fourth is what we have now, and what failed.

### 5. The promotion threshold

Not every prose rule should be promoted to code. OpenAI's heuristic: promote when the rule is consistently ignored or downgraded despite being clearly stated. The signal is observed failure, not hypothetical risk.

For `/close` + `/aar`: the signal is clear. One observed downgrade in one session is enough because the failure mode is structural (prose under momentum), not incidental (a one-off mistake).

## The Fix (Applied to `/close`)

The scanner (`close_accounting.py`) should:

1. Detect friction in the session (hard — requires either transcript analysis or an explicit friction flag set during the session)
2. Check for an AAR artifact in the session directory
3. If friction detected AND no AAR artifact: set `retrospective` gate to `needs_attention` (not `needs_llm_check`) and add it to `loop.attention_gates`
4. The loop fires: the LLM cannot get `loop.needed = false` until the AAR artifact exists
5. The close summary cannot be emitted clean

This moves the enforcement from prose ("run /aar") to code (the scanner blocks on the missing artifact). The LLM's only path to a clean close summary is to actually run `/aar`.

**Open question:** how to detect "friction" mechanically. Options:
- Explicit friction flag set by the model during the session (via a hook or skill)
- Transcript analysis for `/tp` invocations, error patterns, or operator corrections
- AAR-artifact-presence as the only signal (if no AAR was run this session, the gate fires unconditionally for sessions with substantive work)

## Related

- [[skill-enforcement-layers]] — the 3-layer model (PreToolUse 100% / UserPromptSubmit ~50% / Stop backstop); this page refines it with the state-machine and scanner-gate patterns
- [[skill-step-downgraded-from-action-to-note]] — the specific failure pattern this concept addresses
- [[skill-enforcement-deep-dive]] — the ~50% Layer 1 failure analysis; this page explains why Layer 1 (prose injection) can't reach 100%
- [[writing-discipline-not-enforced]] — same root pattern: prose rules treated as advisory

## Sources

- Brightlume AI, "Why Your AI Agent Needs a State Machine, Not a Prompt Chain" (April 2026) — https://brightlume.ai/blog/why-ai-agent-needs-state-machine-not-prompt-chain
- OpenAI, "Harness engineering: leveraging Codex in an agent-first world" (February 2026) — https://openai.com/index/harness-engineering/
- Session 2026-07-20: `/close` invocation where retrospective gate was downgraded from "ask" to "recommend"
- Existing wiki: `skill-enforcement-layers.md`, `skill-step-downgraded-from-action-to-note.md`

## Auto-related

- [[skill-enforcement-layers]]
- [[skill-enforcement-deep-dive]]
- [[handoff-pre-compact-problems]]
## Falsifier

TODO (auto-generated by wiki_validator_sweep 2026-07-30): This concept predates the
mandatory Falsifier section. State what observation or evidence would make this
concept wrong or obsolete. If the concept is purely descriptive (not a claim),
state that explicitly: "This is a reference document, not a claim — no falsifier applies."
## What this means for our workspace

TODO (auto-generated by wiki_validator_sweep 2026-07-30): This concept predates the
mandatory workspace-implications section. State what should be updated, created, or
retired in our infrastructure based on this finding. If the concept is reference-only
with no actionable implication, state: "Reference document — no workspace action needed."
