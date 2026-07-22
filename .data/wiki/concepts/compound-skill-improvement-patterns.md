---
title: "Compound skill improvement patterns: recursive /www self-improvement"
created: 2026-07-21
source: session-2026-07-21 (/www recursive self-improvement run)
sources:
  - https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices
  - https://generativeprogrammer.com/p/skill-authoring-patterns-from-anthropics
  - https://anthonytd.com/blog/building-skills-for-ai-agents/
  - https://graphite.com/guides/ai-code-review-context-full-repo-vs-diff
  - https://www.emergentmind.com/topics/deep-research-llm-agents
  - https://apxml.com/courses/multi-agent-llm-systems-design-implementation/chapter-3-agent-communication-coordination/multi-agent-conflict-resolution
  - https://www.developersdigest.tech/blog/seven-ai-agent-orchestration-patterns
  - P:/.data/wiki/concepts/skill-authoring-patterns-dos-and-donts.md
  - P:/.data/wiki/concepts/prospective-prioritization-multi-lens-what-next.md
  - P:/.data/wiki/concepts/multi-agent-correlated-errors.md
tags: [skill-design, compound-skill, orchestrator, pipeline-pattern, incremental-reuse, conflict-resolution, source-quality, context-firewall, recursive-improvement]
agent: grok
verification: web_sources_cited
cognitive_load: 4
summary: "Improvement patterns for compound/orchestrator skills (like /www), synthesized from a recursive self-improvement run. Covers seven dimensions: gathering (source quality, gap analysis, research ledger), thinking (conflict detection, context firewall, evidence weighting, fresh-lens synthesis), outputting (confidence tagging, unresolved gaps, multi-artifact), prompting (exclusion clauses, checklists, shape templates), coding (helper script slots), agenting (pipeline pattern, model disclosure, A/B loop). Validates the incremental-reuse pattern from Graphite and the CREDIBLE source-quality framework."
host: both
---

# Compound skill improvement patterns: recursive /www self-improvement

## Context

This concept was produced by running `/www` on itself — a recursive self-improvement run. The topic was "improve /www across all aspects: gathering, thinking, outputting, prompting, coding, agenting." The run demonstrated the skill working end-to-end while simultaneously improving it.

## The seven improvement dimensions

### 1. Gathering improvements

**Source quality scoring (CREDIBLE-lite framework)**

Source: [CREDIBLE framework](https://www.mdpi.com/3042-8130/2/1/3) (Traga Philippakos, 2026); adapted for LLM research.

Score each scraped source on four dimensions, 1-3 each:

| Dimension | What it measures |
|---|---|
| **Authority** | Official docs > practitioner blog > anonymous |
| **Recency** | <12 months or evergreen > 1-3 years > >3 years (for time-sensitive) |
| **Evidence** | Cites sources + data > mix of opinion/evidence > pure assertion |
| **Bias** | Neutral, acknowledges trade-offs > mild vendor bias > strong sales pitch |

Sources scoring ≤6/12 are flagged `[LOW-QUALITY]` and used only for triangulation, not as primary citations. This prevents the common failure of citing a convincing-sounding but evidence-free blog post as a primary source.

**Gap analysis as explicit structured output**

Phase 1 should produce an explicit list of gaps (specific questions Phase 2 should answer), not a vague "what's missing." Each gap becomes a search query in Phase 2.

**Research ledger (incremental reuse)**

Source: [Graphite incremental-analysis-cache](https://graphite.com/guides/ai-code-review-context-full-repo-vs-diff).

> "Maintain state or cache between reviews; reuse prior context so you don't have to reprocess everything every time."

Applied to `/www`: each run writes a ledger entry at `P:/.data/www-ledger/<topic-slug>.md` recording what was researched, which sources were used, which gaps were addressed, and which remain unresolved. The next run on the same topic reads the ledger and either:
- Skips Phase 2 entirely (sources unchanged, gaps resolved)
- Researches only unresolved gaps
- Researches only new sources since the last run

This is the same pattern proposed for the AAR ledger — incremental reuse of interpretation while re-reading fresh evidence.

### 2. Thinking improvements

**Conflict detection (5 strategies)**

Source: [apxml.com multi-agent conflict resolution](https://apxml.com/courses/multi-agent-llm-systems-design-implementation/chapter-3-agent-communication-coordination/multi-agent-conflict-resolution).

When sources disagree, do NOT silently resolve. Surface the conflict explicitly:

| Conflict type | Resolution strategy |
|---|---|
| Factual disagreement | Authority + recency weighting; mark "⚠️ CONFLICTING CLAIMS" |
| Interpretive disagreement | Present both interpretations with reasoning; don't pick a winner unless evidence strongly favors one |
| Scope disagreement | Note the scope difference; both may be correct for their scope |

The 5 strategies from apxml.com (rule-based, negotiation, voting, mediation, argumentation) map to research-synthesis as:
- **Rule-based:** higher-authority source wins for factual claims
- **Presentation:** both sides shown for interpretive disagreements
- **Escalation:** unresolved conflicts marked `[UNRESOLVED]` for the user

**Context firewall (for large research outputs)**

Source: `/design` Step 0.5 pattern; [emergentmind deep-research agents](https://www.emergentmind.com/topics/deep-research-llm-agents).

When scraped content exceeds ~5000 words, compress into a brief before synthesis. Extract only gap-relevant passages; drop boilerplate and marketing copy. Write to `${scratch_dir}/www-evidence-brief.md`. Synthesize from the brief.

This prevents the failure mode where synthesis gets lost in 50k tokens of raw scraped content and produces shallow output because the model couldn't hold it all in context.

**Evidence weighting**

Tag each finding with confidence:
- `[HIGH]` — ≥2 independent sources agree
- `[MEDIUM]` — 1 strong source or 2 weak sources
- `[LOW]` — single weak source or inferred

This lets the user see at a glance which findings are well-supported and which are provisional.

**Fresh-lens synthesis (optional)**

Allow `model=<slug>` parameter. If set, Phase 2 synthesis runs in a fresh subagent with that model. This is the `/tp` two-lens pattern applied to research synthesis: the parent agent gathers sources, a fresh-model subagent synthesizes, the parent verifies.

### 3. Outputting improvements

**Source confidence per finding**

Every finding in the wiki concept carries its confidence tag (`[HIGH]`/`[MEDIUM]`/`[LOW]`). The wiki concept's summary distinguishes well-supported findings from provisional ones.

**Unresolved gaps explicit**

Phase 3 output includes an "Unresolved gaps" section listing gaps Phase 1 named that Phase 2 could not answer. These become candidates for future research or user clarification.

**Multi-artifact output (future)**

If findings are actionable (not just informational), the skill could produce:
- Wiki concept (default — always)
- Handoff doc (if findings imply a workstream)
- Plan doc (if findings imply a multi-step implementation)

Currently `/www` produces only the wiki concept. Multi-artifact output is a future enhancement gated on the finding type.

### 4. Prompting improvements

**Exclusion clause in description**

Source: generativeprogrammer Pattern 2.

The description now includes explicit exclusions: "Do NOT use for quick factual lookups (use /web), pure wiki queries (use /wiki), single-URL scrapes (use /firecrawl-scrape), or design-doc production (use /design)."

This prevents the skill from hijacking requests that belong to adjacent skills.

**Copyable checklist**

Source: generativeprogrammer Pattern 10.

The skill now includes a copyable checklist at the top that the model pastes into its response and ticks off. This makes skipped steps visible to both model and user.

**Shape templates**

Each shape (`dos-and-donts`, `comparisons`, etc.) now has an explicit output structure. This prevents the "vague research output" failure mode where the model produces an unstructured dump.

### 5. Coding improvements

**Helper script slots**

Per anthonytd "data in data files, logic in skill files": future helper scripts could automate:
- `www_query.py` — Phase 1: run qmd search + concept listing + gap detection in one call
- `www_dedup.py` — Phase 2: deduplicate sources by URL + content hash
- `www_credibility.py` — Phase 2: score sources by CREDIBLE-lite framework
- `www_ledger.py` — Phase 3: read/write the research ledger

Currently these are manual steps in the skill. Scripting them would reduce token cost and improve consistency, but adds maintenance burden. Defer until the skill is used frequently enough to justify.

### 6. Agenting improvements

**Pipeline pattern (explicit)**

Source: [developersdigest 7 orchestration patterns](https://www.developersdigest.tech/blog/seven-ai-agent-orchestration-patterns).

`/www` is explicitly a **Pipeline** pattern: "Sequential processing where each stage's output becomes the next stage's input. Unix pipes for agents." Phase 1 output → Phase 2 input → Phase 3 input.

Naming the pattern helps because it clarifies what `/www` is NOT: it's not a Supervisor (no parallel specialist subagents), not a Swarm (no independent parallel workers), not a Debate (no opposing-position agents). It's a pipeline with three stages.

**Model disclosure**

Source: `/tp` model disclosure edit (this session).

Phase 2 synthesis discloses which model ran the synthesis. If `model=` was passed, it's a cross-model lens. If omitted, it's parent-inherited. The disclosure is mandatory and appears in the final output.

**A/B loop testing (recommended)**

Source: anthonytd A/B loop.

The skill should be tested by having a fresh instance (Agent B) run it on a real topic and report friction. The current session was Agent A (author) testing it — which is necessary but not sufficient. A fresh-instance test is the real validation.

### 7. Recursive self-improvement (meta-pattern)

The most novel finding from this run: **a compound skill can improve itself by running on its own design.** `/www` was used to research "how to improve /www." The three-phase discipline (query → research → persist) produced both:
- Improvements to the skill (applied to SKILL.md)
- A wiki concept documenting the improvement patterns (this page)

This is a meta-pattern worth naming: **recursive skill improvement via self-invocation.** The skill's own discipline (query existing → research gaps → persist findings) is exactly the right shape for improving the skill itself, because:
- Phase 1 surfaces what the skill already does well (self-knowledge)
- Phase 2 researches what other skills/practices do better (external evidence)
- Phase 3 persists the improvements (durable change)

**Falsifier for recursive self-improvement:** if the skill cannot identify its own gaps in Phase 1 (because it lacks self-awareness of its weaknesses), the pattern fails. Mitigation: Phase 1 should explicitly ask "what does this skill NOT do well?" and read the skill's own falsifier section.

## Relationship to existing concepts

- [[skill-authoring-patterns-dos-and-donts]] — the foundational do's/don'ts; this concept extends them to compound/orchestrator skills specifically
- [[prospective-prioritization-multi-lens-what-next]] — the prioritization gap; `/www` is one tool for addressing it (research what to prioritize)
- [[multi-agent-correlated-errors]] — the fan-out pattern; `/www`'s fresh-lens synthesis option borrows from it
- [[deliberation-waste-re-deriving-same-answer]] — the research ledger prevents re-deriving prior research
- [[fabricated-causal-chain-receipt-required]] — source quality scoring and confidence tagging are receipt mechanisms for research claims

## Open questions

- Should `/www` produce multi-artifact output (wiki + handoff + plan) for actionable findings?
- Should helper scripts be built for Phase 1 automation?
- How does the research ledger interact with the AAR ledger? (Both are incremental-reuse patterns; could they share infrastructure?)
- What formal eval scenarios would test `/www`? (anthonytd eval-driven development)

## Sources (full list)

- [Skill authoring best practices](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices) — Anthropic official. Concision, progressive disclosure, control tuning, build evals first.
- [Skill Authoring Patterns from Anthropic's Best Practices](https://generativeprogrammer.com/p/skill-authoring-patterns-from-anthropics) — 14 patterns across 5 categories. Activation metadata, exclusion clause, context budget, progressive disclosure, control tuning, explain-the-why, template scaffold, in-skill examples, known gotchas, execution checklist, self-correcting loop.
- [Building Skills for AI Agents](https://anthonytd.com/blog/building-skills-for-ai-agents/) — A/B loop, eval-driven development, pointers beat descriptions, split by failure mode.
- [How much context do AI code reviews need?](https://graphite.com/guides/ai-code-review-context-full-repo-vs-diff) — Incremental-analysis cache, memory/stateful agents, hybrid strategy. Validates the research ledger.
- [Deep Research LLM Agents](https://www.emergentmind.com/topics/deep-research-llm-agents) — Dynamic planning, hierarchical memory, report synthesis and evidence grounding, hallucination mitigation, citation verification.
- [Managing Disagreements in Multi-Agent Interactions](https://apxml.com/courses/multi-agent-llm-systems-design-implementation/chapter-3-agent-communication-coordination/multi-agent-conflict-resolution) — 5 conflict resolution strategies: rule-based, negotiation, voting, mediation, argumentation.
- [7 AI Agent Orchestration Patterns](https://www.developersdigest.tech/blog/seven-ai-agent-orchestration-patterns) — Single, Supervisor, Pipeline, Swarm, Debate, Hierarchical, Harness. `/www` is a Pipeline.
