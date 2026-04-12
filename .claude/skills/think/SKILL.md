---
name: think
description: Adaptive reasoning gate for SDLC work - choose the right depth and evidence posture
version: "2.2.0"
status: stable
category: meta
triggers:
  - /think
aliases:
  - /think

suggest:
  - /truth
  - /decision-tree
  - /sequential-thinking
  - /analyze
---

# /think

Use `/think` when a prompt needs better judgment, not more output.

## Core Goal

Pick the reasoning depth that best fits the risk, uncertainty, and blast radius of the problem, then return a distilled recommendation.

## Depth Ladder

Choose the depth that matches the problem, and escalate if the first pass still leaves meaningful uncertainty:

1. `/truth` if the question is about evidence, existence, behavior, implementation status, or "what actually happened."
2. Evidence-audit mode if you want the answer challenged, cross-checked, or auto-verified before it is trusted. This subsumes the old `/truth-av` behavior.
3. `/decision-tree` if the question is about options, lifecycle, state transitions, phases, or resource management. Use the explicit 5-dimensional scaffold below.
4. `/sequential-thinking` if the question needs multiple hypotheses, root-cause analysis, or uncertainty reduction.
5. `/think` if the prompt is straightforward enough that a concise recommendation is better than a framework dump.

If the prompt is broad, ambiguous, high-stakes, or cross-cutting, prefer deeper analysis over the first adequate tier.

## Evidence-Audit Mode

Use evidence-audit mode when the user wants verification, skepticism, or a direct assessment backed by proof.

- Treat claims as hypotheses until the relevant files, commands, or tests have been checked.
- Prefer actual evidence over confidence language.
- For advisory questions, answer directly with tradeoffs and sources instead of deferring back to the user.
- Cite the proof, not the vibe.

## Decision-Tree Mode

Use this when the problem has real options, state changes, timing, or lifecycle impact.

Apply the full 5-dimensional scaffold in order:

1. Name the decision and the concrete options.
2. Map the state transition for each option.
3. Analyze lifecycle impact: persistent, ephemeral, or mixed.
4. Check the phases that matter: before, during, after, or never.
5. Clarify the purpose and constraints, then recommend one path.

If evidence is also uncertain, verify the facts first, then apply the decision tree.

## Output Contract

Return:

1. The problem in one sentence.
2. The chosen depth tier.
3. The best recommendation.
4. The top tradeoffs or risks.
5. The evidence or verification step that would change the answer. In evidence-audit mode, include the verdict and proof for each material claim.
6. A rollback or reversibility note when relevant.

## Operating Rules

- Do not print the full internal scaffold.
- Do not collapse every prompt into the smallest reasoning mode. If the prompt is ambiguous, risky, or cross-cutting, let the depth grow.
- Be decisive when evidence is sufficient.
- If a claim depends on repo state, runtime behavior, or missing functionality, verify it before stating it.
- If the task is trivial or purely informational, answer directly and skip the framework.
- If one blocking unknown remains, ask at most one question; otherwise proceed with the best assumption.
- If the problem belongs in decision-tree mode, do not stop at "there are options." Walk the 5 dimensions and then recommend.

## Hook Alignment

The hook stack already provides the supporting machinery. Use it as an additive stack, not a reason to stop at the first answer:

- evidence-first claim routing
- reasoning-mode selection
- sequential hypothesis analysis
- anti-sycophancy and verification reminders

Do not restate that machinery. Use it, then give the user the shortest answer that is still safe.

## Compatibility

- `/truth-av` is deprecated and kept only for backward compatibility.
- Its behavior now lives in `/think` under evidence-audit mode.
- Use `/truth` for direct manual verification and `/think` for adaptive reasoning that may include verification.

## Good Answers Look Like

- Clear recommendation, not a list of undecided possibilities
- One reasoned path, not three equally weighted paths
- For decision-tree problems, explicit option/state/lifecycle/phase/purpose analysis
- Explicit uncertainty when needed
- Specific verification or rollback steps
- Enough depth for the stakes, without ceremonial fluff
- Low-friction follow-up for the user

## Skip For

- Trivial requests
- Pure information questions
- Cases where the user explicitly says "just do it"
