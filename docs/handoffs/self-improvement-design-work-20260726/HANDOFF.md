---
thread_id: 019f9f4f-self-improvement-design-work-20260726
parent_handoff_path: none
current_session_id: 019f9f4f-7f5b-7a71-9eaf-8f43ba9f8fb9
current_terminal_id: grok-build-terminal
produced_at: 2026-07-27T00:45:00Z
status: open
handoff_type: investigation
accurate_as_of_head: ea0a48be110dee12dd78317a611c1f6231c4d0f5
---

# Handoff: Three self-improvement features needing design work

## Objective

Design and implement three features from the self-improving-agent-systems research that need design decisions before implementation: (1) proactive task anticipation, (2) curiosity-driven exploration, (3) /www deep-dive on key repos.

## Status

OPEN — three independent items, each needs a design decision before coding.

## Read-first list

1. `P:/.data/wiki/concepts/self-improving-agent-systems-techniques-and-workspace-gaps.md` — the research base with all source citations
2. `~/.grok/skills/notice/SKILL.md` — proactive task anticipation extends /notice
3. `~/.grok/skills/dream/SKILL.md` — curiosity-driven exploration could be a /dream trigger

## Task packets

### SI-01: Proactive task anticipation (ProactiveAgent pattern)

- **goal:** extend /notice or create a new mechanism that PREDICTS what the operator will need next and prepares it — not just detects problems after they occur
- **design question:** what signals predict upcoming needs? Examples: operator starts editing a hook file → predict they'll need the hook test file; operator mentions a model name → predict they'll need tool-fallbacks.md; operator commits to P:\ → predict concurrent-session collision risk
- **research base:** thunlp/ProactiveAgent (99 citations), ProActLLM, arxiv 2410.12361
- **options:**
  - (A) Extend /notice with a new trigger type (T6: predictive) — simplest but stretches /notice's scope
  - (B) New skill /anticipate — separate concern, clean boundary
  - (C) Add to /tp recap — surface predictions during mid-session status
- **acceptance:** when operator starts a task, the system surfaces the 1-2 most likely next needs before they're asked
- **falsifier:** predictions are wrong >50% of the time (worse than random)
- **estimate:** 2-3 hours (design + implement + test)

### SI-02: Curiosity-driven exploration

- **goal:** route agents toward high-uncertainty paths as a discovery signal — unverified claims, stale wiki concepts, skills that haven't been runtime-tested
- **design question:** what counts as "high uncertainty"? How is uncertainty measured mechanically?
- **research base:** arxiv 2210.16468 (curiosity-driven exploration via prediction error)
- **options:**
  - (A) Wiki staleness index — concepts with old `created:` dates and no recent qmd hits → flag for /dream review
  - (B) Skill runtime-test gap — skills that were edited but never runtime-verified (like this session's /aar Phase 4 before the OA-01 verification) → flag for verification
  - (C) Unverified-claim tracker — claims tagged [INFERENCE] in transcripts that were never upgraded to [FACT] → flag for verification
- **acceptance:** a /curiosity or /explore-uncertainty pass that surfaces the top 5 highest-uncertainty items in the workspace
- **falsifier:** surfaced items are already known/stale (the signal isn't predictive of real gaps)
- **estimate:** 3-4 hours (design the uncertainty metric + implement + test)

### SI-03: /www deep-dive on key self-improvement repos

- **goal:** research the four key repos from the wiki concept in depth — extract implementable techniques, not just summaries
- **repos:**
  - Awesome-Self-Evolving-Agents (XMUDeepLIT) — https://github.com/XMUDeepLIT/Awesome-Self-Evolving-Agents
  - MaximeRobeyns/self_improving_coding_agent — https://github.com/MaximeRobeyns/self_improving_coding_agent
  - selfimproving-agent.github.io — https://selfimproving-agent.github.io/
  - teacherpeterpan/self-correction-llm-papers — https://github.com/teacherpeterpan/self-correction-llm-papers
- **design question:** which repo has the most transferable technique for our workspace topology (solo operator + fleet of concurrent coders + wiki-grounded + handoff-based)?
- **acceptance:** a wiki concept with ≥5 concrete techniques extracted, each with: what it does, how it maps to our workspace, implementation estimate
- **falsifier:** repos contain only research papers with no implementable code (academic only)
- **estimate:** 1-2 hours (/www run with depth=deep)

## Hard constraints

1. Each feature needs a DESIGN DECISION before implementation — don't code without resolving the design question first
2. Anti-"smallest viable" applies — design for optimal long-term, not minimal viable
3. "Could You Be Wrong?" prompt applies — for each design decision, state what would make it wrong

## Cross-reference couplings

- `P:/.data/wiki/concepts/self-improving-agent-systems-techniques-and-workspace-gaps.md` → research base for all three
- `~/.grok/skills/notice/SKILL.md` → SI-01 extends or parallels /notice
- `~/.grok/skills/dream/SKILL.md` → SI-02 could be a /dream trigger; SI-03 uses /www

## Resumption protocol

1. Read the wiki concept + this handoff
2. For each SI: resolve the design question (pick an option), then implement
3. SI-01 and SI-02 are independent; SI-03 is pure research (no design needed, just /www)

## Suggested next invocation

```
Pick up self-improvement design work from P:/docs/handoffs/self-improvement-design-work-20260726/HANDOFF.md.
Three items: proactive task anticipation (SI-01), curiosity-driven exploration (SI-02),
/www repo deep-dive (SI-03). Each needs a design decision before implementation.
Start with SI-03 (pure research, no design needed) — run /www on the four key repos.
```

## Last user message (verbatim)

> "yes" (proceed with two now + handoffs for three that need design work)

## Epistemic labels

- All research citations are `[FACT]` from the wiki concept's sourced findings
- Design options are `[INFERENCE]` — based on the research but not workspace-tested
- Estimates are `[INFERENCE]` based on similar implementations this session
