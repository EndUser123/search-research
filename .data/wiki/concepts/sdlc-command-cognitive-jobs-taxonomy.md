---
title: "SDLC Command Cognitive Jobs Taxonomy"
created: 2026-08-04
source: "Perplexity KB project (Jul 18, 2026) + ChatGPT consultation"
tags: [sdlc, command-design, naming, architecture-decision, cognitive-model, user-intent]
summary: >
  Design decision: each SDLC command owns a single cognitive job, defined by
  what kind of ambiguity it reduces. /research → reduce uncertainty (what is
  true?). /design → reduce decision ambiguity (what should we do?). /plan →
  reduce execution ambiguity (how do we do it?). /go → reduce implementation
  risk (do it safely). /review → evaluate the implementation. /risks →
  challenge trust and assumptions. The test: "I want to [command] X" must read
  as a natural sentence. Commands that answer "how does the system work" rather
  than "what do I want to accomplish" are misplaced in the user-facing surface.
agent: grok
host: grok
cognitive_load: 2
verification: multi-source-verified
sources:
  - "Perplexity KB project session: Designing a Unified Knowledge and Research System (Jul 18, 2026) — https://www.perplexity.ai/search/c4ad7639-d4cc-4333-8907-487de1d23bbe"
  - "ChatGPT conversation: Deep research help — https://chatgpt.com/c/6a6d1e1f-14d4-83e8-9815-ec870e5207d9"
relations:
  - target: wiki/concepts/skill-domain-map.md
    type: extends
  - target: wiki/concepts/skill-catalog.md
    type: related
  - target: wiki/concepts/design-graphs-solution-graphs-value-for-ai-agent-fleet.md
    type: related
  - target: wiki/concepts/persistent-kb-architecture-model-sunset-survivability.md
    type: related
---

# SDLC Command Cognitive Jobs Taxonomy

## Decision context

**Why this was needed:** the operator consulted ChatGPT and Perplexity about the SDLC skill taxonomy. The existing `/all` command was an implementation detail masquerading as user intent — it answered "run all tools" rather than expressing a cognitive goal. The question: what is the right naming/organization for SDLC commands so each has a clear input state, output state, and definition of done?

**The convergence:** three independent conversations (ChatGPT, two Perplexity sessions) converged on the same answer: each command should own a single cognitive job, defined by what kind of ambiguity it reduces. This is not just naming — it's a contract.

## The cognitive job definitions

| Command | Cognitive job | Trigger | Input | Output |
|---------|--------------|---------|-------|--------|
| `/research` | Reduce uncertainty | "I don't know enough to decide yet" | Question or problem area | Grounded answer with assessed evidence |
| `/design` | Reduce decision ambiguity | "I know what I'm deciding, help me decide well" | Scoped architectural decision | ADR, design gate, recorded decision |
| `/plan` | Reduce execution ambiguity | "Decision made, how do we do it?" | Decision | Ordered implementation path |
| `/go` | Reduce implementation risk | "Plan ready, execute safely" | Plan | Validated change |
| `/review` | Evaluate the implementation | "Is this code/diff correct?" | Code or diff | File/line findings |
| `/risks` | Challenge trust and assumptions | "Should we trust this?" | Proposal or implementation | PROCEED/REVISE/BLOCK verdict |

## The "I want to [command]" test

Any command that answers "how does the system work" rather than "what do I want to accomplish" is probably misplaced in the user-facing surface. For each command, can you write "I want to [command] X" as a natural sentence?

- "I want to research this" ✓
- "I want to design this" ✓
- "I want to plan this" ✓
- "I want to go" ✓
- "I want to review this" ✓
- "I want to all this" ✗
- "I want to tldr-router this" ✗
- "I want to dispatching-parallel-agents this" ✗

This test catches naming debt before it accumulates. `/all` failed the test — it's an implementation detail, not a cognitive job.

## The /research ↔ /design loop

Research and design form a loop, not a pipeline:
- `/research` → `/design` (informs)
- `/design` → `/research` (bounded call when assumptions are missing)

But the bounded part matters. `/design` should only pull `/research` back in for narrow, typed triggers:
- **Missing constraint** — design discovers an assumption it can't validate locally
- **Unexpected option** — a third option emerges during tradeoff analysis that needs evidence
- **Contradicting prior decision** — design conflicts with a wiki-recorded decision

Otherwise `/design` becomes `/research` with extra steps.

## /risks insertion points

`/risks` is most valuable **before commitment**, not after implementation:
- `/research` → `/risks` (challenge the evidence)
- `/design` → `/risks` (challenge the decision before it's recorded)
- `/plan` → `/risks` (challenge the approach before execution)
- `/go` → `/review` (evaluate the implementation)

`/review` is post-hoc evaluation. `/risks` is pre-commitment challenge. They're not the same phase.

## /research scope: local evidence not just external

`/research` should include local evidence, not just internet research:
```
/research
├── local evidence (QMD/codebase/docs)
├── external evidence (web search)
├── prior decisions (wiki)
└── claim assessment
```

Many of the hardest questions are "what is true about our system?" — not "what is true on the internet?" The most important source is often existing skills, hooks, artifacts, and prior decisions, not Google.

## What this means for our workspace

1. **Never create `/all` as a public command.** As of 2026-08-04, no `/all` skill exists in the catalog — this concept serves as a forward-looking guardrail, not a retirement recommendation. If someone proposes adding `/all` as a "run all backends" command, the "I want to all this" test should block it: it's an implementation detail, not user intent. The capability-routing system should remain the internal engine behind `/research`, not exposed as a "run everything" command. This aligns with [[skill-domain-map]] — the domain map should reflect cognitive jobs, not tool mechanics.

2. **`/research` and `/www` are the same cognitive job** — the `/www` skill already implements the wiki→web→wiki research loop. The alias `/research` → `/www` already exists in the skill catalog. See [[research-system-novel-ideas-external-synthesis]] for how this cognitive job could be enhanced with belief ledger and research market models.

3. **`/find` and `/web` remain explicit retrieval tools.** They're lower-level than `/research` — they return results, not understanding. If you find yourself typing `/web` and then synthesizing manually, the task actually wanted `/research`.

4. **The cognitive job definitions should appear in SKILL.md descriptions** so the `/ask` router can match user intent to the right cognitive job, not just to keyword matches. See [[skill-catalog]] for the current catalog that would need updating.

## Steelman (rejected alternative)

**Keep `/all` as a "unified retrieval" command.** The argument: `/all` provides a single entry point that runs all backends. Users who want breadth without ceremony can use it instead of remembering which backend to call. **Why rejected:** "I want to all this" fails the natural-language test. Users don't think in terms of "run all backends" — they think in terms of what they want to accomplish. The capability-routing system can run all backends internally when `/research` dispatches, without exposing the routing mechanics as a command.

## Falsifier

This taxonomy is wrong if:
- The cognitive jobs don't map to real workflow differences (if `/research` and `/design` produce the same output for the same input)
- The `/ask` clarification gate becomes friction that annoys more than it helps
- Users consistently prefer `/all` over typed commands because the cognitive job distinction adds ceremony without value
- The "I want to [command]" test fails to catch real naming problems (commands that pass the test are still confusing)

## Sources

- Perplexity KB project: Designing a Unified Knowledge and Research System (Jul 18, 2026)
- ChatGPT conversation: Deep research help (browser adapter architecture discussion)

## Receipts

- `/research` alias: `~/.grok/skills/research/SKILL.md` — alias for `/www`, confirms the cognitive job alignment
- `/www` SKILL.md: `~/.grok/skills/www/SKILL.md` — implements wiki→web→wiki research loop (Phase 1-3)
- `/ask` SKILL.md: `~/.grok/skills/ask/SKILL.md` — intent-based router that would benefit from cognitive job definitions
- [INFERENCE] `/all` is referenced in some skill descriptions but may not exist as a standalone skill — the capability-routing system is internal to `/www` and `/web`

## Auto-related

- [[skill-catalog]]
- [[skill-graph]]
- [[I'm-going-to-create-a-hook-to-enforce-discovery-be]]
- [[research-vs-design-vs-architect-skills-and-www-self-assessment]]
- [[design-docs-reaped-from-temp-pattern]]

