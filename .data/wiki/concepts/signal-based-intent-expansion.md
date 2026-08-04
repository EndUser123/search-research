---
title: "Signal-based intent expansion — preprocessing before routing or discovery"
created: 2026-08-04
source: session-019fca0e (extracted from /ask Step 0)
sources:
  - P:/.data/wiki/concepts/intent-classification-before-routing-2026.md (research basis)
tags: [intent-expansion, preprocessing, skill-routing, signal-fusion, reusable-pattern]
summary: >
  A reusable preprocessing pattern: combine three signal sources
  (conversation history, workspace state, session arc) to expand a raw
  operator prompt into a complete keyword set before routing or discovery.
  Prevents the failure where narrow keywords produce narrow recommendations.
  Implemented in /ask Step 0; applicable to /todo, /tp session, /close,
  /handoff auto-update, and any skill that asks "what does the operator
  need right now?"
agent: grok
host: grok
cognitive_load: 2
verification: session-validated
relations:
  - target: wiki/concepts/intent-classification-before-routing-2026
    type: implements — this is the reusable extraction of the research synthesis
  - target: wiki/concepts/prompting-patterns-for-ai-agent-control
    type: related — pattern 2 (required sequence) and pattern 3 (source-of-truth directives)
---

# Signal-based intent expansion (SIE)

## What it is

A preprocessing step that runs before keyword extraction, routing, or
discovery. It fuses three signal sources into a complete intent picture
so the downstream grep/query/recommendation sees the full landscape, not
just what the operator's raw prompt contained.

## The three signals

| Signal | Source | What it contributes | Example |
|--------|--------|---------------------|---------|
| **Conversation** | Last 3-5 substantive turns | Action verbs, nouns, recommendations from prior skills | `/tp` said "push now" → adds `push`, `ship` |
| **Workspace** | `git status`, `git rev-list`, `handoff list` | State signals the conversation doesn't contain | Unpushed commits → adds `push`, `ship`, `publish` |
| **Session arc** | What the session has been about | Domain selection (which skill areas to search) | Session-end arc → capture + close + ship, not just one |

## Why it exists

Without SIE, the agent reads the operator's raw prompt ("what skills in
addition?") and extracts keywords from it alone. If the prompt is
capture-oriented, the keywords are capture-oriented, and `/ship` is
invisible to every grep. The signal sources that would have surfaced
`ship` (workspace: unpushed commits; conversation: `/tp` said "push now")
are available but not consulted.

SIE structurally prevents this by mandating that all three sources are
consulted before keywords are finalized.

## How to implement (for any skill)

Add a Step 0 before the skill's main extraction/routing/discovery logic:

```
### Step 0: Signal-based intent expansion

1. **Conversation signals** — scan last 3-5 turns for action verbs and
   recommendations from prior skills. Extract as keywords.
2. **Workspace signals** — check workspace state:
   git status, unpushed commits, open handoffs, recent commits.
   Convert state findings to keywords.
3. **Session arc** — determine session phase (implementation, debugging,
   review, capture, session-end). Use to select which domains to search.
4. **Combine** — merge all three into the keyword set before proceeding.
```

## Skills that should use SIE

| Skill | Where SIE helps | What it prevents |
|-------|----------------|------------------|
| `/ask` | Step 0 (implemented) | Missing `/ship` when all keywords are capture-oriented |
| `/todo` | Before scanning sources | Missing push/ship tasks when session-arc is capture-only |
| `/tp session` | Before NOW/NEXT/LATER | Missing push as a NOW item because the retrospective lens didn't look at workspace state |
| `/close` | Before gate resolution | Missing "unpushed commits" gate because the scanner didn't check `git rev-list` |
| `/handoff` auto-update | Before work-stream detection | Missing the push/ship stream because the session arc was framed as capture-only |

## Falsifier

This pattern is wrong if:
- Workspace signals add noise (unrelated dirty files generate misleading
  keywords). Mitigation: filter workspace signals to session-related
  changes only — check commit timestamps, not just `git status`.
- The three-signal combination increases latency beyond acceptable
  thresholds. Mitigation: the git commands are <100ms total; the
  conversation scan is in-context (no file reads). Total overhead is
  negligible.
- Skills implement SIE inconsistently (each skill gathers signals
  differently). Mitigation: reference this wiki concept as the
  authoritative spec; use the same 3-signal structure everywhere.

## Provenance

Extracted from `/ask` Step 0 (session 2026-08-04). The research basis is
`[[intent-classification-before-routing-2026]]` — TianPan (intent layer
before dispatch), WonderLab (conversation history as #1 multiplier),
Pandey (intent-to-action layer).
