---
title: "Intent classification before routing — preprocessing user prompts for /ask"
created: 2026-08-04
source: session-019fca0e (/www research on intent classification)
sources:
  - https://tianpan.co/blog/2026-04-16-intent-classification-agent-routers (TianPan, Apr 2026 — intent layer before tool dispatch)
  - https://dev.to/wonderlab/agent-series-5-intent-recognition-and-routing-making-agents-actually-understand-users-3174 (WonderLab, May 2026 — conversation history as #1 quality multiplier)
  - https://medium.com/@pankaj_pandey/intent-to-action-layer-for-ai-agents-the-raw-user-prompts-should-not-directly-trigger-tools-9d3dab9aea17 (Pandey — intent-to-action layer)
  - https://docs.nvidia.com/aiq-blueprint/2.0.0/architecture/agents/intent-classifier.html (NVIDIA AI-Q — single-LLM intent + depth)
tags: [intent-classification, prompt-preprocessing, ask, skill-routing, agent-design]
summary: >
  The field consensus: raw user prompts should not directly trigger tool
  dispatch. An intent classification layer runs first — narrowing the
  namespace, injecting conversation history, and combining workspace state.
  For /ask this means: gather classification signals (conversation history
  + workspace state) before extracting keywords, so the keyword set reflects
  what the operator needs, not just what the prompt literally says.
agent: grok
host: grok
cognitive_load: 3
verification: multi-source-verified
relations:
  - target: wiki/concepts/prompting-patterns-for-ai-agent-control
    type: related — intent classification is the runtime application of prompt patterns
  - target: wiki/concepts/prompt-patterns-improvement-ideas-2026
    type: extends — the evaluate mode checks prompt quality; this preprocesses before routing
---

# Intent classification before routing

## Decision context

**Why this research was needed:** `/ask` missed `/ship` when the operator
asked "what skills should I use in addition?" The root cause was intent
misclassification — the agent framed it as capture/close, not
push/verify. The operator pointed out: "you likely won't get better
prompting from the user, so you'll need to preprocess the prompt or
determine the intent."

## The three external patterns

### Pattern 1: Intent classification layer before tool dispatch (TianPan)

> "The fix is a pattern that most teams skip: an intent classification layer
> that runs before tool dispatch. Not instead of the LLM—before it."
> — TianPan.co, Apr 2026

At 50+ tools, LLM routing accuracy drops from 94% to 64%. The classifier
narrows the namespace so the LLM only sees relevant tools. The cascade:

1. Keyword/regex filter (<1ms) — unambiguous commands
2. Embedding or small-model classifier (10-100ms) — routine intents
3. LLM fallback (100-500ms) — novel/compositional intents

**Transferable to /ask:** slash commands already bypass (layer 1 works).
The gap is layer 2/3 — the agent reads context but doesn't systematically
combine conversation history with workspace state before extracting
keywords.

### Pattern 2: Conversation history is the #1 quality multiplier (WonderLab)

> "The most impactful improvement across the entire demo was injecting
> conversation history into the classification prompt."
> — Dev.to/WonderLab, May 2026

"just optimize it" with no history → `clarify (50%)`; with code history →
`code (80%)`. Multi-turn context disambiguates pronouns and short prompts.

**Transferable to /ask:** the skill says "last 3-5 turns" but doesn't
explicitly extract signals from those turns and inject them as keywords.
The `/tp` critique saying "push now" was in context but wasn't converted
to a keyword.

### Pattern 3: Intent-to-action layer (Pandey)

> "Raw user prompts should not directly trigger tools."
> — Pandey, Medium

The intent-to-action layer sits between human language and agent dispatch.
It normalizes, classifies, and routes before any tool fires.

**Transferable to /ask:** the operator's raw prompt ("what skills in
addition?") shouldn't directly drive grep queries. A preprocessing step
should expand it: "in addition to what?" → look at session state →
generate keywords from both conversation AND workspace.

## The synthesis — what /ask needs

**Step 0: Gather classification signals (before keyword extraction)**

Three signal sources, combined:

1. **Conversation signals** — last 3-5 turns. What was just discussed?
   What did the last `/tp` or `/close` recommend? Extract action verbs
   and nouns from the most recent substantive turns.

2. **Workspace signals** — `git status` (unpushed commits?), `handoff list`
   (open handoffs?), recent commits (what shipped?). These produce
   keywords the conversation might not contain.

3. **Session arc** — what has this session been about? (implementation,
   debugging, review, capture, session-end). The arc determines which
   skill domains to search.

Combine all three into a keyword set BEFORE grepping the skill graph.
This is the structural fix for the /ship miss: workspace state would have
contributed `push`/`ship` even though the conversation didn't.

## Falsifier

This approach is wrong if:
- Workspace signals add noise (git status shows unrelated dirty files
  that generate misleading keywords). Mitigation: filter workspace
  signals to session-related changes only.
- Conversation history injection increases latency beyond acceptable
  thresholds. Mitigation: cap at 3-5 turns, extract keywords not full
  text.
- The preprocessing step becomes another layer the agent can skip under
  pressure. Mitigation: it's prose, not mechanical — same compliance
  risk as all prose steps. The receipt-file enforcement pattern (from
  mechanical-enforcement-of-llm-skill-steps) is the longer-term fix.
