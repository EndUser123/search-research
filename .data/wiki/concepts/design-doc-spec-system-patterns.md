---
title: "Design Doc and Spec System Patterns: External Best Practices for Our /design Skill"
created: 2026-07-20
source: session-2026-07-20 (/www research on design system improvements)
tags: [design-doc, spec-driven, living-specs, write-review-loop, linter, multi-agent, cost-aware]
agent: grok
host: both
cognitive_load: 3
verification: multi-source-verified
summary: >
  External research on design-doc and spec-generation systems reveals five
  patterns our /design skill already implements well (write-review loop,
  personas, critical friend, consistency sweep, domain research) and five
  patterns we should adopt: bidirectional spec updates (living specs),
  protected-decision markers, hierarchical spec summaries (extended TOC),
  cost-aware model tiering per review task, and structured decision logs
  inside the design doc itself.
relations:
  - target: wiki/concepts/mandatory-step-enforcement-code-over-prose
    type: related
  - target: wiki/concepts/skill-step-downgraded-from-action-to-note
    type: related
---

## Summary

External research on design-doc generation and spec-driven development reveals a mature ecosystem of patterns. Our `/design` skill already implements many of the recommended practices — the write-review-revise loop, separate writer/reviewer personas, a critical friend step, consistency sweep, and domain research pre-loading. But five specific patterns from external systems would improve our design quality and reduce cost.

## What we already do well (validated by external research)

| Pattern | Our implementation | External source that validates it |
|---|---|---|
| Write → review → revise loop until consensus | Steps 1-5 in `/design` | Osmani: "spec-driven workflows with gated phases"; ThoughtWorks: "spec as evolving artifact" |
| Separate writer and reviewer personas | TOML persona files | Osmani: "subagents with separate system prompts"; multi-agent document writing (Barnacle) |
| Critical friend / premise challenge | Step 5.5 | Osmani: "LLM-as-a-Judge for subjective checks"; EITT: "agent-writer generates, agent-critic checks" |
| Consistency sweep after revision | Step 4.5 | Compiled AI pattern: "validation gauntlet — cross-checking across models" |
| Domain research before writing | Step 0.5 | Osmani: "start with a clear plan (specs before code)" |
| Three-tier boundaries (always/ask/never) | Inherited from AGENTS.md | GitHub 2,500-repo study: "most effective specs use three-tier boundaries" |

## Five patterns to adopt

### 1. Bidirectional spec updates ("living specs")

**Source:** Augment Code, "How to Write Living Specs for AI Agent Development" (2026)

**The pattern:** Static specs flow one way (developer writes → agent consumes). Living specs add a feedback loop: after implementation, agents or developers write implementation decisions back into the spec. This prevents "spec drift" where the document says one thing and the code says another.

**How it applies to our `/design` skill:** Currently, the design doc is a one-shot artifact. After the write-review loop converges, the doc is frozen. If implementation later changes the approach, the doc goes stale. The "living spec" pattern would add a post-implementation step: "update the design doc's Key Decisions section to reflect what was actually built, and note any deviations."

**Implementation:** Add a Step 7 to `/design`: "Post-Implementation Spec Update." After the PR plan is executed (by `/go` or manual implementation), the design doc is reopened and the Decision Log is updated with what actually happened vs what was planned. This makes the doc useful for future reference instead of dead scaffolding.

**Cost:** Low — one additional subagent call after implementation, or a manual edit by the orchestrator.

### 2. Protected-decision markers

**Source:** Augment Code guide, adapted from AGENTS.md patterns

**The pattern:** Inside a spec, certain decisions are wrapped in markers that say "DO NOT change this" with a rationale. This prevents reviewers (human or agent) from accidentally rewriting a load-bearing architectural decision during a revision.

**Example from the research:**
```text
<!-- BEGIN USER-SPECIFIED -->
Authentication Design Decision:
We use JWT tokens with 15-minute expiration and refresh token rotation.
DO NOT change this to session-based auth or increase token duration.
Rationale: Security audit requirement from 2026-01-15.
<!-- END USER-SPECIFIED -->
```

**How it applies to our `/design` skill:** The writer and reviewer sometimes disagree on architectural decisions. Currently the writer can set `Status: wontfix`, but this only works within a single review round. Protected-decision markers would persist across rounds and across the critical-friend step.

**Implementation:** Add a convention to the writer persona: decisions the user explicitly stated (from the prompt) should be wrapped in `<!-- PROTECTED -->` markers. The reviewer and critical friend are instructed to not challenge protected decisions without escalating to the user.

### 3. Hierarchical spec summaries (extended TOC)

**Source:** Addy Osmani, "How to write a good spec for AI agents" (2026)

**The pattern:** For large specs, generate a condensed table of contents with one-sentence summaries per section. This "extended TOC" stays in context while the full details are loaded on demand. It gives the model a "mental map" without consuming the full token budget.

**How it applies to our `/design` skill:** The current design doc can be 1000-2000 lines. When the reviewer reads it, it consumes significant context. An extended TOC would let the reviewer quickly identify which sections need deep reading and which can be skimmed.

**Implementation:** After Step 1 (write), generate a `spec-toc.md` file with one-line summaries per section. The reviewer reads the TOC first, then deep-reads only sections flagged as architecture-critical. The linter can also use the TOC to verify cross-references.

### 4. Cost-aware model tiering per review task

**Source:** Osmani: "use a cheaper/faster model for initial drafts or repetitions, and reserve the most capable model for final outputs or complex reasoning"; Compiled AI pattern: "validation gauntlet"

**The pattern:** Different review tasks have different difficulty. Mechanical verification (paths exist, identifiers match) can use a cheap model or deterministic code. Architectural judgment needs a strong model. Cost is minimized by routing each task to the cheapest model that can do it.

**How it applies to our `/design` skill:** This is exactly what our `design_lint.py` implements for the deterministic tier. The remaining gap: the LLM reviewer currently uses the parent (expensive) model for everything, including checking things the linter already verified. The fix (documented in our plan) is to instruct the reviewer to skip linter-covered checks and focus on architecture.

**Implementation:** Already partially done (the reviewer prompt now says "do not re-verify these"). The full fix requires model routing: spawn the reviewer with `model=<cheap>` for mechanical checks and `model=<strong>` for architecture. This depends on the `model` parameter on `spawn_subagent`, which is already supported.

### 5. Structured decision log inside the design doc

**Source:** Augment Code guide, "Seven Essential Sections" — section 7 is a Decision Log

**The pattern:** The design doc includes a running log of architectural decisions with dates and rationale. This isn't the same as "Key Decisions" (which is a summary); it's a chronological record that grows during the write-review loop.

**How it applies to our `/design` skill:** Currently, decisions are embedded in prose across sections. A structured Decision Log section would make it easier for the reviewer and critical friend to evaluate each decision independently, and for future implementers to understand why a choice was made.

**Implementation:** Add "## Decision Log" to the required sections in the writer persona. Each entry: date, decision, rationale, alternatives rejected.

## Patterns from other systems we reviewed but rejected

| Pattern | Source | Why rejected for our use |
|---|---|---|
| AWS Kiro EARS notation | Augment Code comparison table | Too formal for a solo developer; our specs are natural-language |
| Full multi-agent parallel writing | Barnacle (15 agents for briefing generation) | Overkill for our scale; we write one doc at a time |
| Spec Kit four-phase workflow | GitHub Spec Kit | We already have a gated workflow (write → lint → review → revise → critical friend); adding phases adds ceremony |
| RAG for spec context retrieval | Osmani, DigitalOcean guide | Our specs are <2000 lines; full context fits in a single read. RAG adds infrastructure for no gain at this scale |

## Related

- [[wiki/concepts/mandatory-step-enforcement-code-over-prose]] — the deterministic linter is an instance of moving verification from LLM to code
- [[wiki/concepts/skill-step-downgraded-from-action-to-note]] — the momentum problem that makes enforcement necessary

## Sources

- Augment Code, "How to Write Living Specs for AI Agent Development" (2026) — https://www.augmentcode.com/guides/living-specs-for-ai-agent-development
- Addy Osmani, "How to write a good spec for AI agents" (2026) — https://addyosmani.com/blog/good-spec/
- GitHub, "How to write a great agents.md" (2,500-repo analysis, 2026) — cited by Osmani and Augment Code
- ThoughtWorks, "Spec-driven development: unpacking 2025 new engineering practices" — cited by Augment Code
- Barnacle AI, "Building a Production Multi-Agent System for Document Writing" (2026) — https://www.barnacle.ai/blog/2026-01-16-multi-agent-document-writing
- Compiled AI pattern (itnext.io, 2026) — "LLM outputs through a validation gauntlet"

## Auto-related

- [[llm-handoff-best-practices]]

