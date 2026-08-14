---
title: "Review and Refine Meta Prompt Design"
date: "2026-07-04"
mode: "ASI"
uuid: "2b35d337-5624-4011-aed1-6a87c064a5b3"
entry_count: 1
---

## Human

Build a 'Review-and-Refine' meta-prompt for your main agent that forces it to spawn a critical subagent to review any proposed next steps before showing them to me. The meta-prompt should instruct the main agent to (1) draft a plan, (2) pass the plan and the current project context to a 'Critic' subagent with instructions to identify logical flaws, missing dependencies, and potential risks, and (3) wait for the critic's report to refine the final output before the primary agent presents it to the user

## Assistant

Built the Review-and-Refine meta-prompt as a drop-in artifact: [review-and-refine-meta-prompt.md](file).

## What's in it

- **Main agent meta-prompt** — forces the 4-step gate: DRAFT (private) → CRITIC REVIEW (blocking) → REFINE → PRESENT. No final answer ships without a completed Critic report.
- **Critic subagent prompt** — adversarial posture ("assume the plan is wrong until proven otherwise"), hunts logical flaws, missing dependencies, hidden assumptions, tool/env risks, verification gaps, and over/under-specification. Anti-rubber-stamping rules require falsifying evidence and forbid empty/N/A sections.
- **Context handoff YAML** — schema the primary agent passes verbatim (request, project context, relevant files, plan, assumptions, evidence inspected, environment state, side-effects/risks, verification strategy).
- **Critic report schema** — structured `BLOCK | REVISE | PROCEED` verdict with severity-tagged issues, falsifying evidence, and confidence level.
- **Refinement rules + failure-mode table** — how to resolve each verdict, and explicit fallbacks for unavailable/timeout/vague/disagreement cases.
- **Implementation notes** — how to wire it into Claude Code subagents, a hook gate for hard enforcement, Bifrost/CCR routing of the Critic to a distinct model, cost gating, and epistemic-validation tie-in.

## Two caveats worth flagging

- The prompt is a **behavioral contract, not hard enforcement**. The model can still roleplay the Critic internally. True enforcement requires a Claude Code hook that blocks the final message unless a persisted `critic_report` artifact exists — Section 7 covers this.
- The timeout/unavailable path now stops and asks the user rather than auto-proceeding, so the gate can't be quietly bypassed.

If you want, I can package this as a Claude Code skill or generate the actual hook script that enforces the `critic_report` gate.
