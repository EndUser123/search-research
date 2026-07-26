---
title: "Thought-Partner Design: Dimensions Beyond Critique"
created: 2026-07-23
source: session-2026-07-23 (/www research on what /tp should consider beyond critique)
tags: [thought-partner, tp, critical-friend, pattern-recognition, lateral-thinking, six-thinking-hats, synthesis, design]
agent: grok
host: both
cognitive_load: 3
verification: multi-source-verified
sources:
  - https://coacharya.com/blog/pattern-recognition-in-coaching/ (Coacharya — pattern recognition as the differentiator of master coaching)
  - https://lifearchitect.ai/hats/ (Dr Alan Thompson — Six Thinking Hats + AI)
  - https://blog.startupstash.com/the-6-thinking-hats-of-ai-f7df09d05240 (Six Thinking Hats adapted for AI)
  - https://medium.com/@fabiolalli/ai-enhanced-thinking-hats-from-six-thinking-hats-to-eight-cognitive-agents-8f6960344920 (Fabio Lalli — expanding to 8 cognitive agents)
  - https://www.eightfoldadvantage.com/can-ai-replace-a-business-coach-in-2026 (business coaching + AI)
  - wiki/concepts/ai-thought-partner-industry-expectations-and-now-next-later
  - wiki/concepts/mental-models-for-tp-and-brainstorming
relations:
  - target: wiki/concepts/ai-thought-partner-industry-expectations-and-now-next-later
    type: extends
  - target: wiki/concepts/mental-models-for-tp-and-brainstorming
    type: extends
---

# Thought-Partner Design: Dimensions Beyond Critique

## Decision context

**Why this research was needed:** the operator identified that `/tp` only
critiques inward (what's wrong) but doesn't synthesize forward (what to do
next). They asked what else to consider before changing the skill. This
research surfaced that critique is one of six thinking modes a thought
partner should provide, and that the single highest-value missing capability
is pattern recognition — not synthesis.

## The problem: /tp is wearing one hat

De Bono's Six Thinking Hats maps cleanly to the gap:

| Hat | Mode | What it does | In /tp? |
|-----|------|-------------|---------|
| **Black** | Caution/critique | "What's wrong with this?" | ✅ This is almost all /tp does |
| **Yellow** | Optimism/benefits | "What's working? What opportunities exist?" | ⚠️ Partial — "What's significant" section only |
| **Green** | Creativity/alternatives | "What else is possible?" | ⚠️ Partial — domain 5 (solution-space broadening) |
| **White** | Facts/information | "What do we actually know vs. assume?" | ❌ Missing — /tp doesn't audit evidence quality |
| **Red** | Emotion/intuition | "How does this feel? What's the gut reaction?" | ❌ Out of scope (reasoning tool, not EI tool) |
| **Blue** | Process/meta | "Are we asking the right question? Going in circles?" | ❌ Missing — no conversation-level process awareness |

**Assessment:** /tp is a strong Black Hat tool with partial Green Hat. It's
missing White Hat (evidence audit), Yellow Hat (benefits/opportunities), and
Blue Hat (process awareness). Red Hat is correctly out of scope.

## The missing dimensions, ranked by value

### 1. Pattern recognition (HIGH — the master-coach differentiator)

Research (McClelland, Goleman, Hay-McBer cited by Coacharya) found that
**pattern recognition was the single cognitive ability that differentiated
outstanding leaders from merely good ones.** In coaching, master coaches
don't seek patterns — they let them emerge from sustained attention to the
client's narrative.

Three pattern types the research identifies:
- **Circular reasoning** — cause and consequence chasing each other ("I can't
  start because I haven't started")
- **Unstated assumptions** — taken-for-granted statements that constrain the
  option space without being examined
- **Strong assertions / identity locks** — "this is who I am" statements that
  prevent exploration

**For /tp:** the model has full session transcript access. It can detect:
"you've made the same dismissal argument three times across different
topics" or "every time X is proposed, you redirect to Y" or "these three
separate decisions are actually the same decision."

This is NOT critique. It's observation. The model sees patterns the user
can't see because the user is inside the conversation.

### 2. Forward synthesis (HIGH — what we already identified)

"What should we do next, in what order, across what horizons?" This is the
constructive complement to critique. The thought partner doesn't just find
problems — it helps construct the path forward.

Already proposed as a new domain. The research validates it: practitioners
expect their thought partners to provide "decision recommendations" and
"strategic synthesis," not just challenges.

### 3. Process/meta awareness (HIGH for long sessions)

Blue Hat thinking: observing the conversation itself. "We've been going in
circles on this binary decision for 4 turns" or "you keep returning to the
same question from different angles" or "we started on topic A and drifted
to topic Z without resolving A."

**For /tp:** this is especially valuable for the operator's long sessions
where scope drift and re-deliberation waste tokens. The thought partner
should be able to say "stop — you're re-deriving the same answer" (which is
already in AGENTS.md as a prose rule, but a /tp observation would be more
salient).

### 4. Evidence audit (MEDIUM — White Hat)

"What do we actually know vs. what are we assuming?" /tp's preflight step
(Step 0.5) partially does this — it checks what exists in the workspace. But
the core critique doesn't audit the evidence quality of the session's claims.

**For /tp:** this would catch the "claims without receipts" pattern we've
documented extensively. But the quality_gate Stop hook already does this
mechanically. The domain would add value only for non-code claims (design
decisions, inferences, plans).

### 5. Benefits/opportunities (LOW-MEDIUM — Yellow Hat)

"What's working well that should be amplified?" /tp's "What's significant"
section partially covers this. Full Yellow Hat would actively look for
opportunities, not just strengths.

**Lower priority** because the operator's workflow doesn't lack for
identifying what's working — the gap is in what's wrong and what to do next.

## What we already have (from earlier wiki research)

The `mental-models-for-tp-and-brainstorming` wiki concept identified:
- Pre-mortem → already added to /tp (domain 3a)
- Second-order thinking → already added to /tp (domain 2a)
- Systematic steelman → already added to /tp (domain 4a)
- Double Diamond → recommended for /brainstorming, not /tp

This research extends that list with three more:
- **Pattern recognition** → new domain (highest value)
- **Forward synthesis** → new domain (already proposed)
- **Process awareness** → new domain (valuable for long sessions)

## Recommended /tp enhancement

Add three domains to /tp's core set, making it a full thought partner:

| Domain | Name | What it does | Hat |
|--------|------|-------------|-----|
| **6** | Forward synthesis | What to do next, prioritized, horizon-aware | Green + Blue |
| **7** | Pattern recognition | Connecting dots across the session the user can't see | White + Blue |
| **8** | Process awareness | Observing the conversation itself (circles, drift, re-deliberation) | Blue |

This transforms /tp from "Black Hat tool" to "full-spectrum thought partner"
while keeping the two-lens architecture and verification synthesis intact.

## Falsifier

These additions are wrong if:
- Pattern recognition produces false patterns (model hallucinates connections that don't exist)
- Forward synthesis produces shallow prioritization (no better than "just do the obvious next thing")
- Process awareness fires on short sessions where it's noise (threshold: only fire when session >5 turns)
- The operator never uses the new domains because the Black Hat critique was what they actually wanted all along
