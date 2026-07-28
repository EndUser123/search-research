---
title: "Skill dependency graph: industry approaches and how ours compares"
created: 2026-07-28
source: session-2026-07-28
tags: [skill-graph, dependency-extraction, blast-radius, sbom, agentflow, research]
summary: >
  External research on skill dependency graphs in AI agent frameworks.
  Found 8 approaches across academic papers, GitHub repos, and industry
  proposals. Our lexical-extraction approach is structurally similar to
  published work (Graph-of-Skills, AgentFlow ADG), but the field is
  converging on structured frontmatter (depends_on:) as the ground truth
  and lexical scanning as the linter for undeclared edges.
agent: grok
host: grok
cognitive_load: 2
verification: multi-source-verified
sources:
  - https://github.com/davidliuk/graph-of-skills (Graph-of-Skills, 2026-07)
  - https://arxiv.org/abs/2607.01136v1 (Skills Are Not Islands, 2026-07)
  - https://arxiv.org/html/2607.01640 (AgentFlow ADG, 2026-07)
  - https://msaad00.github.io/agent-bom/features/blast-radius/ (Agent BOM, 2026-07)
  - https://github.com/williamzujkowski/nexus-agents (nexus-agents, 2026-07)
  - https://github.com/agentskills/agentskills/discussions/210 (Skill Manifest Proposal, 2026-07)
  - https://arxiv.org/abs/2508.05152 (Tool Graph Retriever, 2025-08)
  - https://www.linkedin.com/pulse/we-need-go-deeper-gitlabs-transitive-dependency-gambit-linc-williams-ig1de (Harness Doctrine, 2026-07)
relations:
  - target: wiki/concepts/skill-graph.md
    type: grounds
  - target: wiki/concepts/skill-domain-map.md
    type: related
---

# Skill dependency graph: industry approaches

## Decision context

**Why this research was needed:** we built a lexical skill dependency graph
extracted from SKILL.md files. The question: is anyone else doing this, and
are they doing it better?

**What the research changed:** validated our approach (it's structurally
similar to published work) and identified the highest-leverage upgrade path
(structured frontmatter `depends_on:` as ground truth, lexical scan as linter).

## What exists in the field

| Approach | Source | Input | Method | Use case |
|----------|--------|-------|--------|----------|
| **Graph-of-Skills (GoS)** | GitHub: davidliuk/graph-of-skills | SKILL.md | Auto-extracted graph + PageRank | Dependency-aware skill retrieval |
| **AgentFlow (ADG)** | arxiv 2607.01640 | Agent source code | AST-derived typed edges | Static analysis + Agent BOM |
| **Skills Are Not Islands** | arxiv 2607.01136 | Skill ecosystems | Empirical analysis | Supply chain risk measurement |
| **agent-bom** | GitHub: msaad00/agent-bom | Agent manifest | Auto-generated SBOM | Blast-radius traversal |
| **nexus-agents** | GitHub: williamzujkowski/nexus-agents | In-framework | TypeScript graph module | Runtime dependency resolution |
| **Skill Manifest Proposal** | agentskills Discussion #210 | Declarative manifest | Explicit `depends_on:` fields | Dependency resolution + distribution |
| **Tool Graph Retriever** | arxiv 2508.05152 | Tool descriptions | Learned discriminator (ML) | Semantic dependency detection |
| **Harness Doctrine** | LinkedIn article | Skill files | Audit module | SBOM-equivalent for skills |

## How our approach compares

| Dimension | Ours | Published best |
|-----------|------|----------------|
| **Input** | SKILL.md files (prose) | SKILL.md + AST + manifests |
| **Extraction** | Lexical (regex patterns) | AST (AgentFlow) / ML (TGR) / explicit (Manifest) |
| **Edge types** | delegates_to, consumes_provider, references_wiki | Component, control-flow, data-flow (AgentFlow) |
| **Use case** | Blast-radius analysis | Blast-radius + retrieval + supply-chain risk |
| **Precision** | Medium (mention ≠ edge) | High (AST resolves actual calls) |
| **Recall** | Low-Medium (misses paraphrased refs) | High for code; varies for prose |
| **Cost** | Very low (regex, ~5s) | Medium (AST/ML) to high (training data) |

**Verdict:** our approach is in the same family as GoS (auto-extracted from
SKILL.md) and agent-bom (blast-radius traversal). The main gap is precision
— lexical extraction conflates mentions with real edges. But no published
tool handles the prose-in-SKILL.md problem well; they either target code
(AST) or require explicit manifests.

## The convergence: structured frontmatter as ground truth

Three independent sources converged on the same upgrade path:

1. **AgentFlow:** "declarative manifest fields for declared dependencies"
2. **Skill Manifest Proposal (agentskills #210):** "explicit `depends_on:`"
3. **Harness Doctrine:** "structured, auditable dependency record"

The pattern: add `depends_on:` to SKILL.md frontmatter → lexical scanner
becomes a **linter that detects undeclared edges** → combines cheap scanning
with ground-truth declarations. This is the dependency-cruiser model:
explicit rules + automated detection of violations.

Example frontmatter addition (not yet adopted):

```yaml
---
name: www
depends_on: [web, wiki, crawl4ai]
consumes: [ddg, firecrawl, mmx]
---
```

The scanner then flags: "skill `www` calls `/check` but doesn't declare it
in `depends_on`" — an undeclared dependency, same as a missing import.

## Method taxonomy (from research)

| Method | Precision | Recall | Cost | Prose deps? |
|--------|-----------|--------|------|-------------|
| Lexical/regex (ours) | Medium | Low-Med | Low | Partially |
| AST/structural (tree-sitter) | High | High (code) | Medium | No |
| Runtime/tracing (telemetry) | High | High | High | N/A |
| Learned/ML (TGR) | Med-High | High | High (training) | Yes |
| **Structured frontmatter** | **High** | **High** | **Low per-file** | **Yes, if authored** |

## What we should do next (not yet adopted)

1. **Pilot `depends_on:` frontmatter** on 5 core skills (/www, /web, /tp,
   /why, /close). Validates the format.
2. **Upgrade build_skill_graph.py** to read frontmatter as ground truth and
   use lexical scan only for undeclared-edge detection (linter mode).
3. **Re-evaluate after 3 months:** does the frontmatter drift? If yes,
   consider AST or runtime extraction. If no, the manual + lexical combo
   is sufficient.

## Falsifier

Our approach is wrong if:
- The lexical scanner produces >30% false-positive rate on a manual audit
  of 50 edges (precision too low for blast-radius trust)
- Frontmatter `depends_on:` fields drift from reality (skill changes but
  frontmatter not updated) at >20% rate over 3 months
- A published tool (AgentFlow, agent-bom) matures enough to handle
  SKILL.md prose directly, making our custom scanner redundant

## Receipts

- `P:/.data/wiki/scripts/build_skill_graph.py` — our lexical extraction script
- `P:/.data/wiki/concepts/skill-graph.md` — auto-generated graph output
- `/www` Phase 2 research: 2 subagents (minimax-m3 + glm-5-2), 26 tool calls,
  8 sources verified
