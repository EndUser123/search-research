---
title: "Intent-based routing for AI agent skills — non-regex classification patterns (2026)"
created: 2026-07-25
source: session-2026-07-25 (/www research on intent classification for /tp session variant)
sources:
- https://tianpan.co/blog/2026-04-16-intent-classification-agent-routers (Tian Pan, "The Intent Classification Layer Most Agent Routers Skip", Apr 2026)
- https://dev.to/wonderlab/agent-series-5-intent-recognition-and-routing-making-agents-actually-understand-users-3174 (Agent Series 5, 2026)
- https://www.respan.ai/articles/intent-classification-with-llms (Intent Classification With LLMs, May 2026)
- https://blog.gopenai.com/intent-routing-for-ai-agents-e075d64da6c9 (GoPenAI, Intent Routing for AI Agents, 2026)
- https://docs.nvidia.com/aiq-blueprint/1.2.1/architecture/agents/intent-classifier.html (NVIDIA AI-Q Blueprint)
- P:/.data/wiki/concepts/non-regex-hook-optimizations.md (existing wiki)
- P:/.data/wiki/concepts/llm-judgment-hooks.md (existing wiki)
tags: [intent-classification, routing, non-regex, skill-dispatch, llm-agents, best-practice]
summary: >
  Industry research on non-regex intent classification for AI agent skill routing.
  Consensus: keyword/regex matching fails at scale (20% accuracy at 417 tools);
  the optimal pattern is a cascade (keyword → embedding → fine-tuned SLM → LLM catch-all).
  For small skill sets (<15 tools), LLM-based semantic classification is sufficient.
  Conversation history is the biggest quality multiplier for ambiguous routing.
  Our /tp "semantic intent classification" approach matches the industry's LLM-based
  pattern for small-scale routing — correct for our tool count.
agent: grok
host: both
cognitive_load: 2
verification: multi-source-verified
---

# Intent-based routing for AI agent skills — non-regex patterns (2026)

## Decision context

**Problem:** `/tp` used trigger-phrase lists (regex-like) to route between session-review, opportunity-scan, and critique modes. The operator asked: can't we have a non-regex solution? This research validates the approach and identifies the optimal pattern.

## What the research says

### The non-regex problem is well-documented

**Tian Pan (Apr 2026):** "Regular expressions do not understand meaning. The same pattern will hit past-tense reports, option presentations, future-step descriptions, and verified approval requests." At 417 tools, LLM function-calling accuracy drops to 20%. The "lost in the middle" effect is a physics constraint, not a prompting problem.

**Agent Series 5 (dev.to, 2026):** Keyword matching "only works when users happen to use the exact keywords in your rule table." Testing showed keyword routing returning `unknown` for "Has LangChain released a new version?" because the rule table didn't include "released."

**Our wiki (existing):** `llm-judgment-hooks.md` documents the "conversation collapse pattern" — 6-stage retry loops when regex false-positives block legitimate responses.

### The optimal pattern: cascade classification

The industry consensus (Tian Pan, Agent Series 5, NVIDIA AI-Q, vLLM semantic router):

```
Layer 1: Keyword/regex filter (<1ms) — handles ~5% of explicit commands
Layer 2: Embedding router (16-100ms) — handles majority of queries
Layer 3: Fine-tuned SLM (50-200ms) — handles ambiguous cases
Layer 4: LLM catch-all (1-5s) — handles novel/compositional intents
```

**Threshold:** move up the cascade when confidence < 0.8.

### But for small tool counts, skip the cascade

**Tian Pan's heuristic:**
- <15 tools: LLM function-calling is fine
- 15-50 tools: add embedding router
- 50+ tools: fine-tuned classifier
- 100+ tools: classification layer non-negotiable

**Our `/tp` has ~8 intent categories.** That's well under 15. The LLM-based semantic classification we implemented (the model reads the question and determines intent at screening time) is the correct approach for our scale. No embedding router or fine-tuned SLM needed.

### Conversation history is the biggest quality multiplier

**Agent Series 5 finding:** "Just optimize it" with zero history → `clarify` every time. With code conversation history → `code (80%)`. This validates our `/tp` inline-session approach: the orchestrator has full conversation history, which the semantic classifier uses implicitly.

### Confidence thresholds + clarification fallback

Both sources agree: when confidence is low, ask rather than guess. Our `/tp` already has this pattern — the "Better fit" routing table suggests `/brainstorming`, `/plan`, `/design`, or `/go` when the question doesn't fit `/tp`.

## What this means for our /tp implementation

Our approach (semantic intent classification at screening time, 4 categories) matches the industry's LLM-based pattern for small-scale routing. It's correct for our tool count. Key validations:

1. **Non-regex is right** — keyword matching fails at scale and for novel phrasings
2. **LLM classification is sufficient at our scale** — <15 categories means no embedding or fine-tuned model needed
3. **Conversation history matters** — our inline approach uses it implicitly
4. **Confidence threshold + clarification is the safety exit** — already built in
5. **Named variants are the optimal invocation** — `/tp session` bypasses classification entirely

## Relation to existing wiki concepts

- [[non-regex-hook-optimizations]] — 6 alternatives to regex in hooks (Aho-Corasick, SIMD, AST span, prompt hooks)
- [[llm-judgment-hooks]] — two-layer pattern (regex Layer 1 → LLM Layer 2)
- [[ai-agent-verification-orchestration-best-practices-2026]] — orchestrator + specialized sub-agents

## Falsifier

This research is wrong if, within 6 months:
- LLM-based intent classification becomes unreliable at <15 categories (would need cascade)
- A standard skill-routing protocol emerges that makes per-skill classification redundant
- Our tool count grows past 15 categories (would need embedding router)

## Auto-related

- [[non-regex-hook-optimizations]]
- [[llm-judgment-hooks]]
- [[ai-agent-verification-orchestration-best-practices-2026]]
