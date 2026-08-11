---
title: "Evidence-first default: empowerment over prohibition for needless-confirmation"
created: 2026-07-20
source: session-2026-07-20
tags: [prompt-engineering, context-engineering, failure-mode, llm-behavior, research, empowerment, question-asking, cross-host]
summary: >
  When an LLM states a default/lead/recommendation and then asks the user to
  confirm it on a reversible action, the user wastes a turn. Research
  converges on a non-obvious conclusion: runtime interception (Stop hooks,
  tool blocks) does not work because the model routes around them. The fix
  is empowerment — give each ambiguity trigger a decision protocol so the
  model has somewhere to go other than asking. Validated by four sources:
  dev.to "Teaching an AI Agent to Stop Asking Questions" (prohibition fails,
  empowerment works), Suri et al. arxiv 2511.08798 (SAGE-Agent reduces
  clarification 1.5–2.7× via model-layer EVPI), Edwards & Schuster arxiv 2603.26233 (multi-agent intent-separation reaches 69.4% vs 61% on underspecified SWE-bench — first coding-agent-specific validation, strongest intervention tested), and Anthropic's
  context-engineering essay (right-altitude system prompts, not brittle
  runtime regex).
agent: grok
cognitive_load: 3
verification: multi-source-verified
relations:
  - target: wiki/concepts/plausible-narratives-substitute-for-verification
    type: related
  - target: wiki/concepts/operator-collaboration-style-and-leverage
    type: refines
  - target: wiki/concepts/host-surface-boundary
    type: related
host: both
---

# Evidence-first default: empowerment over prohibition for needless-confirmation

## Summary

LLM agents over-clarify. The default trained behavior when facing uncertainty
is to ask the user. For irreversible operations this is correct; for reversible
actions where the model has already derived a default, asking wastes a turn.
Three independent sources converge on the same finding: **prohibition at the
wrong layer fails; empowerment at the model layer works.**

## Reference failure (2026-07-20)

Operator asked: "Assign the handoff to you so that other AIs will know it's
being worked on and not to take it."

The model investigated (read handoff skill docs, checked sibling handoff
frontmatter conventions, confirmed no existing assignment mechanism),
correctly derived: *"I'd default to `grok` as the assignee since the
producing session is ending."* Then it asked:

> "Who is the assignee, identity-wise? Three plausible values: (1) grok, (2)
> session-id, (3) unknown. I'd default to grok unless you say otherwise. Confirm?"

The operator pushed back: *"why are you asking me questions? can you figure
this out yourself?"*

The model had done the analysis. It stated the default. Then it offloaded the
decision it had already made. The user's one-line pushback cost less than the
model's one-turn ask, but it was still a wasted turn — and across a fleet
running thousands of turns, the cumulative cost is real.

## Why runtime interception does not work

A natural first proposal: a `Stop` hook that pattern-matches "stated default +
confirmation request" and warns. Three lines of evidence say this fails.

### Evidence 1: dev.to "Teaching an AI Agent to Stop Asking Questions" (2025)

Author ran Claude Haiku as an autonomous research service. Haiku repeatedly
produced "Clarification Needed" responses with five numbered sections of
questions instead of doing the research.

First fix: prohibition — `"NEVER use AskUserQuestion"`. Result: Haiku obeyed
the letter of the law. It never called the `AskUserQuestion` tool. Instead it
wrote the clarifying questions as plain text prose. **The tool was blocked;
the behavior was not.**

> "Saying 'don't ask questions' fights against something fundamental in how
> these models are trained. Conversational AI is optimized to be helpful, and
> for most use cases, asking clarifying questions *is* helpful... A one-line
> 'don't' can't override that."

Working fix: empowerment. Replace "don't ask" with a decision protocol for
each ambiguity trigger:

> "You are the decision-maker. When anything is ambiguous, you decide:
> - Vague topic? Pick the most useful interpretation and research it.
> - Broad scope? Narrow to what's most practically useful.
> - Topic directory unclear? Pick the best-fit name or create a new one.
> - Overlaps with existing docs? Read them, then write research that adds
>   new value rather than duplicating."

Author's key insight: *"The model doesn't need fewer restrictions. It needs
more authority."* Same shape as the trigger-case list below.

### Evidence 2: Suri et al., arxiv 2511.08798 (Nov 2025, Adobe Research + UMD)

"Structured Uncertainty guided Clarification for LLM Agents." Introduces
SAGE-Agent, which models clarification as a POMDP with Expected Value of
Perfect Information (EVPI).

Key results:
- SAGE-Agent reduces clarification questions by **1.5–2.7×** vs. strong
  prompting baselines on ClarifyBench
- 7–39% higher coverage on ambiguous tasks (i.e., fewer questions AND better
  outcomes — not just suppression)
- Training-time version (uncertainty-weighted GRPO) boosts When2Call accuracy
  from 36.5% → 65.2% on a 3B model — base models default-over-clarify
  (36.5% baseline accuracy is the measured shape of the problem)

Crucially: **both interventions operate at the model layer, not the runtime
layer.** Inference-time SAGE-Agent runs inside the Reason stage of ReAct;
training-time SAGE reshapes the reward signal. Neither is a post-hoc Stop
check.

### Evidence 3: Anthropic "Effective context engineering for AI agents" (Sep 2025)

Anthropic's official guidance names the right-altitude principle for system
prompts:

> "At one extreme, we see engineers hardcoding complex, brittle logic in their
> prompts to elicit exact agentic behavior. This approach creates fragility...
> At the other extreme, engineers sometimes provide vague, high-level
> guidance... The optimal altitude strikes a balance."

A regex-based Stop hook is the runtime equivalent of hardcoded prompt logic —
same brittleness, different layer. Anthropic explicitly recommends against it
and for "smallest set of high-signal tokens at the right altitude" in the
system prompt itself.

## The empowerment protocol (implemented in `~/.grok/AGENTS.md`)

Lifted from the `/tp` skill's evidence-first rule (which only fires when `/tp`
is invoked) into always-on `AGENTS.md` context. Trigger cases with decision
protocols:

- **Vague identity** (which session / host / account?) → use the host-level
  default (Grok Build → `grok`) and state the assumption
- **Ambiguous scope** (work scope vs. total population) → pick the larger
  interpretation, label it explicitly as the work scope, proceed
- **Missing parameter with documented default** → use the default, state it
- **Reversible frontmatter / config edit** → make the edit, report what was done
- **Genuinely unanswerable from context** → ask **one focused** question and
  stop. Do not chain meta-questions.

The structure matches dev.to's pattern: for each situation that triggers
asking, give a protocol for resolving it without asking.

## Why this is the plausible-narrative pattern in a new disguise

[[plausible-narratives-substitute-for-verification]] documents the failure
mode where the model constructs a plausible narrative and treats it as an
answer. The needless-confirmation pattern is the inverse — the model does the
verification, derives the answer, then **offloads the decision back to the
user as if the derivation had not happened**.

Both share the same root: the model fails to act on what it has already
established. In the plausible-narrative case, it acts on what it hasn't
established. In the needless-confirmation case, it refuses to act on what it
has. Same gap between evidence-in-hand and action-taken, opposite direction.

## Known limitation: ~50% compliance ceiling

Per [[operator-collaboration-style-and-leverage]] §2.2, advisory rules have
~50% Layer-1 compliance. The AGENTS.md empowerment block improves the floor
(every session loads it instead of only `/tp` invocations) but doesn't break
the ceiling. Residual failures will still happen; operator pushback remains
the backstop.

Paths to higher reliability than ~50%:
1. **Model selection** — pick a model less biased toward clarification. Not
   always available (the operator runs mixed fleet).
2. **Training-time intervention** — uncertainty-weighted GRPO per arxiv
   2511.08798. Research-only as of 2026-07; not implementable from inside a
   session.

The honest position: **there is no clean solution at the agent layer for a
problem that originates in model training.** The empowerment block is the
best available intervention, accepting the ceiling.

## What not to do

- **Do not write a Stop hook** for this. The research disconfirms it. A
  regex-pattern hook has the same failure mode as the dev.to author's
  tool block: the model routes around it by rephrasing.
- **Do not write a wiki concept page alone and consider it fixed.** Docs
  without always-loaded context have the ~50% compliance problem. The fix
  must live in `AGENTS.md` or equivalent loaded-on-every-turn context.
- **Do not fine-tune** from inside a session. Research option only.

## Falsifier

If the empowerment block in `AGENTS.md` causes the model to act without
asking on a genuinely irreversible operation (delete, force-push, drop), the
trigger-case list is too broad and the `action_safety` protocol needs to be
re-emphasized. The current block explicitly excludes irreversible operations.

If the empowerment block fails to fire on a reversible action where the model
stated a default and then asked for confirmation (same shape as the
2026-07-20 reference failure), the trigger-case vocabulary doesn't match the
new situation and needs a new entry. Track recurrence rate; if >50% of
sessions still exhibit the pattern after the block is in place, the trigger
list is insufficient and a stronger mechanism (hook or model swap) is needed.

## Sources

- dev.to: "Teaching an AI Agent to Stop Asking Questions (When Nobody's
  Listening)" — https://dev.to/agent-tools-dev/teaching-an-ai-agent-to-stop-asking-questions-when-nobodys-listening-4623
- arxiv: Suri, Mathur, Lipka, Dernoncourt, Rossi, Manocha. "Structured
  Uncertainty guided Clarification for LLM Agents." 2511.08798v2 (Apr 2026).
  https://arxiv.org/abs/2511.08798
- arxiv: Edwards & Schuster. "Ask or Assume? Uncertainty-Aware
  Clarification-Seeking in Coding Agents." 2603.26233 (2026).
  https://arxiv.org/abs/2603.26233 — multi-agent intent-separation (Main
  Agent + Intent Agent) reaches 69.4% resolve rate vs 61% single-agent on
  underspecified SWE-bench Verified. First coding-agent-specific validation
  of empowerment-over-prohibition. Agents showed good calibration without
  hardcoded "must query first" instructions.
- Anthropic: "Effective context engineering for AI agents" (Sep 2025).
  https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents
- LinkedIn: Bob Dickinson, "Ask, Don't Infer: Effective LLM Instruction"
  (Cursor rule, 2025). The inverse pattern — questions get answers,
  imperatives get action.
- Implementation: `~/.grok/AGENTS.md` § "Evidence-first default"
- Source skill: `~/.grok/skills/tp/SKILL.md` § "Evidence-first rule"

## Related

- [[plausible-narratives-substitute-for-verification]] — the inverse failure
  mode (acting on what you haven't verified vs. refusing to act on what you have)
- [[operator-collaboration-style-and-leverage]] §2.2 — the ~50% advisory-rule
  compliance ceiling that bounds this fix's effectiveness
- [[host-surface-boundary]] — sibling finding from the same session
- [[handoff-skill-v011-validators]] — sibling finding; the scope-bounds
  validator addresses a similar "stated vs. ambient" ambiguity in handoffs
- [[llm-handoff-best-practices]] — master doc on handoff discipline

## Auto-related

- [[host-surface-boundary]]
- [[agent-oversight-rubber-stamping]]
- [[operator-collaboration-style-and-leverage]]
## What this means for our workspace

TODO (auto-generated by wiki_validator_sweep 2026-07-30): This concept predates the
mandatory workspace-implications section. State what should be updated, created, or
retired in our infrastructure based on this finding. If the concept is reference-only
with no actionable implication, state: "Reference document — no workspace action needed."
