---
title: "Prompt patterns improvement ideas for Grok Build — external research"
created: 2026-08-04
source: session-019fca0e (/www research on improving /prompt-patterns)
sources:
  - https://simonwillison.net/guides/agentic-engineering-patterns/ (Willison, Feb-Apr 2026)
  - https://paperswithcode.co/paper/2603.10477 (PEEM, Hong et al. 2026)
  - https://www.promptingguide.ai/introduction/elements (Prompt Engineering Guide)
  - https://www.promptingguide.ai/introduction/tips (General Tips)
  - https://aiagentsnews.top/posts/agentic-systems-simple-patterns-win-in-2026/ (Anthropic agentic patterns)
  - P:/.data/wiki/concepts/prompting-patterns-for-ai-agent-control.md (existing 10 patterns)
tags: [prompt-patterns, prompt-engineering, agentic-patterns, skill-improvement, research]
summary: >
  Five improvement ideas for /prompt-patterns gathered from external research:
  (1) add a live-prompt evaluation mode using PEEM's 9-axis rubric, (2) add
  Willison's agentic-specific patterns we're missing, (3) add "say what to do,
  not what not to do" as a pattern, (4) add prompt-element completeness check,
  (5) add the "compound engineering loop" as a meta-pattern. The highest-value
  addition is the live-prompt evaluation mode — it converts /prompt-patterns
  from a passive reference into an active quality tool.
agent: grok
host: grok
cognitive_load: 3
verification: multi-source-verified
relations:
  - target: wiki/concepts/prompting-patterns-for-ai-agent-control
    type: extends — adds external patterns + evaluation mode to the existing 10
---

# Prompt patterns improvement ideas for Grok Build

## Decision context

**Why this research was needed:** `/prompt-patterns` is a pure reference
skill — it teaches 10 structural patterns for authoring instructions. It
has no active mode for checking whether a prompt the operator is about to
send has structural weaknesses. The operator asked what good ideas exist
to improve it for Grok Build.

## The five improvement ideas

### Idea 1: Live-prompt evaluation mode (highest value)

**Source:** PEEM (arxiv 2603.10477, Hong et al. 2026)

PEEM defines a 9-axis evaluation rubric for prompts: 3 prompt criteria
(clarity/structure, linguistic quality, fairness) and 6 response criteria
(accuracy, coherence, relevance, objectivity, clarity, conciseness). It
uses an LLM evaluator to score each axis 1-5 with rationale.

**The transferable part:** `/prompt-patterns` could gain an interactive
mode where the operator pastes a prompt they're about to send, and the
skill evaluates it against the 10 existing patterns + PEEM's prompt
criteria. Output: "your prompt is missing negative constraints (pattern 1),
has no receipt-first framing (pattern 6), and scores 2/5 on clarity —
consider adding X."

This converts the skill from passive reference to active quality tool.
**High value** — directly actionable, no new infrastructure needed.

### Idea 2: Add Willison's agentic patterns we're missing

**Source:** Simon Willison's Agentic Engineering Patterns guide (Feb-Apr 2026)

Willison's guide documents patterns for coding agents that our 10 patterns
don't cover:

| Willison pattern | What it does | In our 10? |
|---|---|---|
| **"First run the tests"** | Before any change, run the test suite to establish a baseline | Partially in pattern 6 (receipt-first) but not as a standalone |
| **Compound engineering loop** | Iterate: prompt → output → review → refine → repeat. The meta-pattern of agentic work | ❌ Not in our 10 |
| **Hoard things you know how to do** | Capture reusable prompts, snippets, and patterns as you discover them — build a personal library | ❌ Not in our 10 (but our /wiki + /prompt-patterns already implement this) |
| **Annotated prompts** | Show the prompt AND the output AND the reasoning in between — makes the prompt's effect visible | ❌ Not in our 10 |
| **Agentic manual testing** | Have the agent manually test the UI/behavior by describing what it sees, not just running automated tests | ❌ Not in our 10 |

**The transferable ones:** "First run the tests" and "compound engineering
loop" are directly applicable. "Annotated prompts" is interesting for
handoff quality. **Medium value** — adds 2-3 patterns to the catalog.

### Idea 3: "Say what to do, not what not to do"

**Source:** Prompt Engineering Guide (promptingguide.ai), OpenAI best practices

The field consensus is shifting: negative constraints ("do not X") are
weaker than positive directives ("do Y instead"). Our pattern 1 (negative
constraint preamble) is built around "do not" framing.

**The nuance:** for AGENTS (not chatbots), negative constraints are still
necessary because they prevent destructive actions. But the general prompt
engineering guidance is: lead with what you want, then add constraints as
guardrails. We should add a note to pattern 1 acknowledging this tension
and recommending "positive directive first, negative constraint as
guardrail" rather than "negative constraint first."

**Low value** — refinement to existing pattern, not a new idea.

### Idea 4: Prompt-element completeness check

**Source:** Prompt Engineering Guide (promptingguide.ai/introduction/elements)

Every prompt has up to 4 elements: Instruction, Context, Input Data,
Output Indicator. A prompt quality check could verify all 4 are present
and non-trivial.

This is a simpler version of PEEM's clarity/structure axis — useful as a
quick checklist in the live-prompt evaluation mode (Idea 1).

**Low-medium value** — folds into Idea 1.

### Idea 5: "Simple patterns win" (Anthropic agentic guidance)

**Source:** Anthropic's agentic systems guidance (via aiagentsnews.top, 2026)

Anthropic's data shows that successful agentic systems split workflows
from agents and prefer simple patterns over complex frameworks. The
implication for prompt patterns: don't over-engineer instructions. A
prompt with 10 patterns applied is likely worse than one with 2-3
well-chosen patterns.

**The transferable part:** add a "pattern budget" recommendation to the
skill — "use at most 3-4 patterns per instruction. Adding more reduces
compliance because the cognitive load on the model increases." This is the
prompt-engineering equivalent of our Check 6 (leanness scan).

**Medium value** — counterbalances pattern accumulation tendency.

## What we already have that the field validates

| Our pattern | External validation |
|---|---|
| Pattern 1 (negative constraints) | Validated by all sources — but field is shifting to "positive first" |
| Pattern 4 (anti-scope-creep) | Validated by Anthropic's "simple patterns win" |
| Pattern 6 (receipt-first) | Validated by Willison's "first run the tests" |
| Pattern 7 (alternatives gate) | Validated by Anthropic's "consider more options" |
| Pattern 10 (workspace safety) | Validated by Willison's anti-pattern: "inflicting unreviewed code on collaborators" |

## Recommendation

**Implement Idea 1 (live-prompt evaluation mode) as the primary improvement.**
It's the highest-value addition — converts a passive reference into an
active tool, and the evaluation rubric (10 existing patterns + PEEM's 3
prompt criteria) is directly implementable as a skill mode.

**Add Ideas 2 and 5 as pattern catalog additions** — 2-3 new patterns
(compound loop, pattern budget) and one refinement (pattern 1: positive
first, negative as guardrail).

**Defer Ideas 3 and 4** — they fold into Idea 1's evaluation rubric.

## Falsifier

This research is wrong if:
- The live-prompt evaluation mode produces false positives (flags good
  prompts as weak) at >15% rate. Measure: test against 10 known-good
  prompts from session history.
- The new patterns (compound loop, pattern budget) don't fire in practice
  because operators don't use them. Measure: track invocation after 5
  sessions.
- PEEM's rubric doesn't translate to agentic prompts (it was designed for
  chatbot prompts). Measure: check whether the 3 prompt criteria
  (clarity/structure, linguistic quality, fairness) map to agentic
  instruction quality.
