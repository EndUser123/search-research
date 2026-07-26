---
title: "Spec-Driven Development and Harness Engineering: Ecosystem Map for Our /design Skill"
created: 2026-07-20
source: session-2026-07-20 (/www deep investigation of design system repos)
tags: [spec-driven-development, harness-engineering, design-system, ecosystem, spec-kit, compiled-ai, state-machine]
agent: grok
host: both
cognitive_load: 4
verification: multi-source-verified
summary: >
  Deep investigation of the spec-driven development and harness engineering
  ecosystem reveals three maturity tiers of systems. GitHub Spec Kit is the
  most mature open-source spec generation toolkit, with template-driven
  quality gates, constitutional enforcement, and a specify→plan→tasks command
  chain. The awesome-harness-engineering repo (ai-boost) is the definitive
  curated map of 100+ harness engineering primitives across 12 categories.
  Four patterns from external systems would directly improve our /design
  skill: (1) constitutional gates, (2) [NEEDS CLARIFICATION] markers,
  (3) the Compiled AI validation gauntlet, and (4) entropy management via
  periodic repair agents. Our linter + reviewer split is validated as the
  industry-standard "hybrid deterministic + LLM" pattern.
relations:
  - target: wiki/concepts/design-doc-spec-system-patterns
    type: refines
  - target: wiki/concepts/mandatory-step-enforcement-code-over-prose
    type: related
---

## Summary

This is a deeper follow-up to the prior `/www` run on design system patterns. Where that run identified 5 patterns to adopt from blog-level sources, this run investigated actual repos, techniques, and the broader harness engineering ecosystem. The findings validate our architecture choices and identify four specific techniques worth adopting.

## The ecosystem: three tiers of maturity

### Tier 1: Production-grade spec-driven development systems

| System | Stars | Key innovation | Relevance to us |
|---|---|---|---|
| **GitHub Spec Kit** (`github/spec-kit`) | High | Constitutional enforcement via templates; `/speckit.specify` → `/speckit.plan` → `/speckit.tasks` command chain; `[NEEDS CLARIFICATION]` markers | **Directly applicable** — our `/design` is a lighter version of this; Spec Kit's template-driven quality and constitutional gates are patterns we should adopt |
| **AWS Kiro** | N/A (commercial) | EARS notation for formal specs; human review gates | Too formal for solo developer use; our natural-language specs are sufficient |
| **Augment Cosmos** | N/A (commercial) | Unified cloud agents with shared context; spec/intent-review checkpoint before execution | The "living spec" pattern (bidirectional updates) is the key takeaway — already identified in prior run |
| **cc-sdd** (`gotalab/cc-sdd`) | Moderate | Long-running spec-driven implementation for Claude Code; `/kiro-discovery` command | Demonstrates the specify→implement→verify loop as a Claude Code skill; very close to our `/design` → `/go` workflow |

### Tier 2: Harness engineering reference repos

| Repo | Stars | What it covers |
|---|---|---|
| **awesome-harness-engineering** (`ai-boost`) | Growing | The definitive curated list: 100+ entries across 12 categories (agent loop, planning, context delivery, tool design, skills/MCP, permissions, memory, orchestration, verification, observability, debugging, HITL) |
| **RUCAIBox/awesome-agent-harness** | Growing | Academic complement: 500+ references mapping harness design across workflows, memory, skills, multi-agent orchestration |
| **lopopolo/harness-engineering** | Growing | Ryan Lopopolo's anthology: reusable AGENTS.md/CLAUDE.md artifacts, playbooks, evals, domain modeling docs. The most systematic open-source synthesis of organizational judgment as cumulative agent artifacts |
| **Loop Engineering** (`cobusgreyling`) | Moderate | 7 production patterns for agent loops with cross-tool starter kits, CLI tools for scoring readiness, scaffolding state, cost estimation, drift detection |
| **hybrid** (`justinstimatze`) | New | Design pattern for LLM-and-code cycles: "places LLM judgment and deterministic code in alternating layers that mutually generate each other's working context" |

### Tier 3: Individual techniques and patterns

| Pattern | Source | How it applies to our `/design` |
|---|---|---|
| **Compiled AI validation gauntlet** | itnext.io | "Putting LLM outputs through a validation gauntlet — cross-checking across models, filtering invalid output." This is exactly our linter → LLM reviewer → critical friend chain |
| **State machine guardrails** | `statewright` | "Local models went from 2/10 to 10/10 passing purely by shrinking the tool space." Our linter does this for design docs — it shrinks the review space by pre-catching mechanical issues |
| **Entropy management / doc-gardening** | OpenAI harness engineering + Martin Fowler | "Periodic agents that scan for stale or obsolete documentation that does not reflect real code behavior and open fix-up pull requests." Our `/close` skill does a lightweight version of this; could formalize |
| **Progressive crystallization** | LMsys paper | "Converts validated agent behaviors into cumulative, reusable patterns over time." Our wiki concept system does this — validated lessons are promoted to durable wiki entries |

## Four techniques to adopt from GitHub Spec Kit

Spec Kit's template-driven approach has several techniques that directly improve design doc quality:

### 1. Constitutional enforcement via Phase -1 gates

Spec Kit uses a `constitution.md` file with nine articles that govern every generated implementation. Before any plan proceeds, it must pass Phase -1 gates:

```
### Phase -1: Pre-Implementation Gates

#### Simplicity Gate (Article VII)
- [ ] Using ≤3 projects?
- [ ] No future-proofing?

#### Anti-Abstraction Gate (Article VIII)
- [ ] Using framework directly?
- [ ] Single model representation?
```

**How to adopt:** Our `/design` skill could have a pre-write gate that checks the design problem against our governing constraints (from AGENTS.md). Before the writer starts, the orchestrator asks: "Does this design respect the optimal-long-term-over-minimal-diff preference? Is it proposing a new system when extending an existing one would work? Does it assume Claude Code semantics for Grok Build?"

### 2. `[NEEDS CLARIFICATION]` markers

Spec Kit templates mandate:

```
When creating this spec from a user prompt:
1. Mark all ambiguities: Use [NEEDS CLARIFICATION: specific question]
2. Don't guess: If the prompt doesn't specify something, mark it
```

**How to adopt:** The writer persona should require `[NEEDS CLARIFICATION]` markers for any design assumption that isn't grounded in a stated user requirement or verified code inspection. The linter can check for unresolved `[NEEDS CLARIFICATION]` markers and flag them as open issues.

### 3. Template-driven quality (how structure constrains LLMs)

Spec Kit's templates include:
- Comprehensive checklists that act as "unit tests" for the specification
- Explicit `✅ Focus on WHAT` and `❌ Avoid HOW` constraints
- Hierarchical detail management (main doc stays readable; details in `implementation-details/`)

**How to adopt:** Our writer persona already has some of this (required sections, PR plan, key decisions). We could add:
- A completeness checklist the writer runs before declaring the draft done
- An explicit instruction to separate "WHAT" (requirements, architecture) from "HOW" (implementation details)
- A maximum line count per section with overflow to appendices

### 4. The specify→plan→tasks command chain

Spec Kit's three-command workflow:
1. `/speckit.specify` — transforms a description into a structured spec
2. `/speckit.plan` — generates an implementation plan from the spec
3. `/speckit.tasks` — decomposes the plan into executable tasks

**How to adopt:** Our `/design` → `/go` workflow is already this pattern, but the handoff is manual. The design doc's PR Plan section could be machine-parseable (structured YAML or JSON), so `/go` can consume it directly without re-reading the full design doc. This would close the loop: design produces a structured plan, `/go` consumes it, `/check` verifies implementation against it.

## Validation: our patterns are industry-standard

The research confirms our architecture choices:

| Our pattern | Industry equivalent | Source |
|---|---|---|
| Linter → LLM reviewer → critical friend | "Hybrid deterministic + LLM" | Alibaba open-code-review (10.9k stars); Compiled AI pattern |
| Writer + reviewer personas | "Agent-writer generates, agent-critic checks" | EITT 2026; multi-agent document writing |
| Consistency sweep after revision | "Validation gauntlet" | itnext.io; OpenAI harness engineering |
| Move enforcement from prose to code | "Architectural constraints (deterministic linters and structural tests)" | Martin Fowler / Birgitta Böckeler |
| Wiki promotion of key decisions | "Progressive crystallization" | LMsys paper |
| Three-tier boundaries | "Always / Ask first / Never" | GitHub 2,500-repo study |

## What we're NOT doing that the ecosystem has moved toward

| Pattern | Why we're not doing it (yet) | When to reconsider |
|---|---|---|
| Full multi-agent parallel design writing | Overkill for one-design-at-a-time solo workflow | If we start producing multiple design docs per session |
| RAG-based spec context retrieval | Our specs are <2000 lines; full context fits | If design docs regularly exceed 5000 lines |
| MCP-based design doc consumption | Design docs are consumed by the orchestrator, not by MCP tools | If `/go` needs to programmatically parse the PR plan |
| Constitutional amendment process | We don't have enough accumulated decisions yet | After 10+ design runs establish a pattern |
| Version-controlled specs in the repo | Our design docs are temp scaffolding by design | If a design doc becomes a reference that future sessions re-read |

## Related

- [[wiki/concepts/design-doc-spec-system-patterns]] — prior run's findings; this concept refines with deeper repo investigation
- [[wiki/concepts/mandatory-step-enforcement-code-over-prose]] — our linter is an instance of the "Compiled AI" validation gauntlet
- [[wiki/concepts/skill-step-downgraded-from-action-to-note]] — the momentum problem that makes all of this necessary

## Sources

- GitHub Spec Kit: https://github.com/github/spec-kit — full `spec-driven.md` read
- awesome-harness-engineering: https://github.com/ai-boost/awesome-harness-engineering — full README read (326K bytes)
- Addy Osmani, "How to write a good spec for AI agents": https://addyosmani.com/blog/good-spec/
- Augment Code, "Living Specs": https://www.augmentcode.com/guides/living-specs-for-ai-agent-development
- Martin Fowler / Birgitta Böckeler: "Harness engineering for coding agent users"
- OpenAI, "Harness engineering": https://openai.com/index/harness-engineering/
- Alibaba open-code-review: https://github.com/alibaba/open-code-review (10.9k stars)
- engineering4ai/awesome-spec-driven-development: https://github.com/engineering4ai/awesome-spec-driven-development
- cobusgreyling/Loop Engineering: https://github.com/cobusgreyling/loop-engineering
- justinstimatze/hybrid: https://github.com/justinstimatze/hybrid
- statewright/statewright: https://github.com/statewright/statewright
- lopopolo/harness-engineering: https://github.com/lopopolo/harness-engineering

## Auto-related

- [[skill-catalog]]

