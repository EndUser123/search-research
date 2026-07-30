---
title: "Prompt preflight: session-context completeness check before dispatching subagent prompts"
created: 2026-07-30
source: session-019fb189
tags: [prompt-engineering, context-completeness, procedural-verification, reusable-pattern, skill-design, seed]
summary: >
  Before a skill dispatches a subagent prompt (e.g., /design writer, /go
  implementer, /plan planner), check the prompt against the session transcript
  for missing load-bearing information. This is NOT epistemic reflection ("is
  this prompt good?") — which fails per Huang et al. ICLR 2024. It IS procedural
  verification ("what session facts are NOT in the prompt?") — which works
  because it checks against an external reference (the transcript). The pattern
  is reusable across /design, /plan, /go, /handoff, /refine. Implementation:
  a shared utility that extracts load-bearing facts from session context,
  checks each against the prompt, and proposes additions for missing items.
agent: grok
host: grok
cognitive_load: 2
verification: inferred
relations:
  - target: wiki/concepts/self-reflection-in-llms-fails-without-external-evidence.md
    type: related — the distinction between epistemic reflection (fails) and procedural verification (works) is why this pattern works
  - target: wiki/concepts/prompting-patterns-for-ai-agent-control.md
    type: extends — adds a new pattern to the catalog
---

# Prompt preflight: session-context completeness check

## Decision context

**Why this was needed:** during session 019fb189's /design run, the operator noticed the firewall subagent prompt was high-quality and asked "did you use /refine?" The answer: the prompt was good because the *operator's* scoping was good — not because the agent did any prompt-quality checking. The operator proposed: "Can /design do a self-reflection step to see if it can make the prompt better before doing design?"

The session's own research ([[self-reflection-in-llms-fails-without-external-evidence]]) says intrinsic self-reflection fails. But the operator's proposal is NOT intrinsic reflection — it's procedural verification against session context. That distinction is exactly what the research says works. The pattern is generalizable: any skill that dispatches a subagent could benefit from checking whether the dispatch prompt contains all load-bearing facts from the session. The cost is low (one grep/scan of the transcript) and the value is high (a subagent that lacks context produces lower-quality output that requires more revision rounds).

## The pattern

```
prompt_preflight(session_context, current_prompt) → enhanced_prompt | original_prompt

1. Extract load-bearing facts from session_context:
   - Decisions made (with rationale)
   - Constraints stated by the operator
   - Evidence gathered (with receipts)
   - Rejected alternatives
   - Open questions

2. Check each fact against current_prompt (semantic match)

3. For each missing load-bearing fact, propose adding it

4. Present: "Original vs Enhanced. <N> session facts missing from prompt. Use enhanced?"
```

## Why it works (per session research)

- Epistemic reflection ("is this prompt good?") → FAILS (Huang et al. ICLR 2024). The model has no reliable signal that it missed something. "Silent divergence" — the model doesn't know it's wrong.
- Procedural verification ("what session facts are NOT in the prompt?") → WORKS. This is the Chain-of-Verification pattern (Dhuliawala et al. 2024): check against an external reference, not against the model's own judgment.
- The session transcript is an external reference; the model's opinion about prompt quality is not.
- This connects to [[convergence-gap-rca-symptom-restatement-toulmin-enforcement]]: the Toulmin COUNTEREXAMPLE field is the same pattern applied to RCA claims — force an external check rather than trusting internal assessment.
- The workspace's evidence-tier system ([[self-reflection-in-llms-fails-without-external-evidence]]) is the same principle applied to causal claims — require external receipts, not self-assessment.
- [[problem-first-systems-decomposition]] is related: understand the full context before generating solutions; the preflight ensures the prompt contains the full context.

## Where it applies

- /design — before spawning the writer
- /plan — before writing the plan from a spec
- /go — before dispatching implementation subagents
- /handoff — before writing the handoff
- /refine — literally IS this pattern already

## Worked example (session 019fb189)

The operator invoked `/design` to restructure /why Steps 9, 11, 12, 14, 16. The dispatch prompt to the firewall subagent included the step numbers, the changes, and the constraint. But it was missing:
- The Hermes benchmark finding (tight feedback loop + Rule of Three)
- The pressure-test results (MECHANISM field is fakeable)
- The research-applicability check pattern (Round 3.25)

These were load-bearing facts from the session that the writer needed. A prompt preflight would have caught them. The prompt was still good (the operator's scoping was excellent), but the writer would have benefited from the full session context — especially the pressure-test failure modes that constrain the design (e.g., "don't rely on MECHANISM field alone; COUNTEREXAMPLE and EVIDENCE are the load-bearing fields").

## Receipts

- Session 019fb189 operator observation: "Did you use /refine or something else to help with it?" — the prompt was good because the operator's scoping was good, not because of a preflight step
- Huang et al. ICLR 2024 (arXiv:2310.01798): intrinsic self-correction fails; the model has no signal that its reasoning drifted
- Chain-of-Verification (Dhuliawala et al. 2024, arXiv:2309.11495): procedural verification works when the check is against an external reference
- Session 019fb189 wiki concept [[self-reflection-in-llms-fails-without-external-evidence]]: documents the reflection-vs-verification distinction with ablation evidence

## Falsifier

If the preflight consistently finds zero missing facts across 10+ real skill dispatches, it's not earning its cost and should be removed. But the cost is so low (~5-10 seconds, a few thousand tokens) that there's no reason to gate it behind a trigger condition — always run it. The cost of a missing fact (a revision round, 5-10 minutes) dwarfs the cost of the check.

## Implementation seed

[INFERENCE] Shared utility at `P:/.agents/scripts/prompt_preflight.py` that skills call before dispatching. Returns JSON: `{missing_facts: [...], enhanced_prompt: "...", original_prompt: "..."}`. Skills present the choice; the operator decides. Not yet implemented — this is a design seed from session 019fb189.

## How it differs from /refine

`/refine` takes a rough task and tightens it by inspecting the codebase. This pattern takes a *complete-looking* task and checks it against *session context* — not the codebase. The difference: /refine adds missing scope from the external system; prompt preflight adds missing context from the conversation. Both are procedural verification (external reference check), not epistemic reflection (internal quality assessment).

## What this means for our workspace

1. This is a cross-cutting concern — applies to any skill that dispatches subagent prompts
2. **Always run** — the cost (~5-10 seconds) is negligible; the cost of a missing fact (a revision round, 5-10 minutes) dwarfs it. No gate condition needed.
3. The operator decides whether to use the enhanced prompt — the check suggests, doesn't override
4. The pattern is a structural instance of the procedural-verification principle documented across three session wiki concepts — same underlying mechanism, different application domain
