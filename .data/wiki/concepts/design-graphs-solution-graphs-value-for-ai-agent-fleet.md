---
title: "Design Graphs and Solution Graphs: Do They Have Value for This Workspace?"
slug: design-graphs-solution-graphs-value-for-ai-agent-fleet
created: 2026-07-28
category: decision
tags: [knowledge-graph, design-graph, solution-graph, architecture-decisions, traceability, dependency-graph, graph-engineering, multi-agent, fleet, lightweight]
summary: >
  Yes — "design graphs" and "solution graphs" are real, well-documented
  concepts in software architecture (Architecture Knowledge Graphs,
  Decision Knowledge Graphs, Solution Graphs). They capture decisions,
  components, dependencies, and rationale as queryable graph nodes/edges.
  For enterprise teams, they deliver traceability, impact analysis, and
  decision reuse. For a solo operator, a full KG is overkill ($10-20M
  enterprise TCO, ontology tax, maintenance burden). BUT: the workspace
  already has the right data structure (relations: frontmatter, typed
  wikilinks, build_skill_graph.py). The optimal recommendation is NOT
  a Neo4j-backed KG — it's extending the existing file-based graph
  indexer to cover wiki concepts + ADRs + handoffs, enabling cross-
  artifact dependency queries without a graph database.
cognitive_load: 3
verification: multi-source-verified
agent: grok
host: both
sources:
  - "Architecture Knowledge Graphs (EAKG) position paper — https://dl.acm.org/doi/10.1145/3643657.3643914"
  - "Decision Knowledge Graph (DKG) — https://livrepository.liverpool.ac.uk/3131697/1/1_KnowledgeGraph_0203210527.pdf"
  - "Solution Graph paradigm (emergentmind) — https://www.emergentmind.com/topics/solution-graph-paradigm"
  - "ARG-Designer multi-agent solution graphs — https://arxiv.org/html/2507.18224v1"
  - "The Ontology Tax (real KG costs) — https://medium.com/graph-praxis/the-ontology-tax-what-nobody-tells-you-about-the-real-cost-of-knowledge-graphs-aee9e8d0cada"
  - "When to use a KG and when it's overkill — https://medium.com/@visrow/when-to-use-a-knowledge-graph-and-when-its-overkill-29750a42e65b"
  - "Why are we so bad at knowledge graphs (critique) — https://mark-burgess-oslo-mb.medium.com/why-are-we-so-bad-at-knowledge-graphs-55be5aba6df5"
  - "Graph engineering for enterprise AI — https://www.truefoundry.com/blog/graph-engineering-enterprise-guide"
  - "Knowledge graphs for agentic AI — https://zbrain.ai/knowledge-graphs-for-agentic-ai/"
  - "Gartner multi-agent systems — https://www.gartner.com/en/articles/multiagent-systems"
  - "Workspace: build_skill_graph.py — P:/.data/wiki/scripts/build_skill_graph.py (existing lightweight graph builder)"
  - "Workspace: wiki SCHEMA.md relations: frontmatter — P:/.data/wiki/SCHEMA.md:74-76"
relations:
  - target: wiki/concepts/codebase-knowledge-graph-mapping.md
    type: related
  - target: wiki/concepts/claude-code-automation-capabilities.md
    type: related
  - target: wiki/concepts/dynamic-wiki-driven-skill-configuration.md
    type: related
  - target: wiki/concepts/solo-director-ai-fleet-coordination-isolation-best-practices.md
    type: related
---

# Design Graphs and Solution Graphs: Do They Have Value for This Workspace?

## Decision context

**The problem:** the operator asked whether "design graphs" or "solution
graphs" exist as concepts, and if so, whether they have value for a solo
operator running an AI agent fleet with 151+ handoffs, 80+ wiki concepts,
ADRs, and cross-referenced design decisions.

**What the research found:** yes, these concepts are real and
well-documented. They fall into three families. But the enterprise-grade
implementations (Neo4j, ontology design, SPARQL) are massively over-engineered
for a solo operator. The workspace already has the data structures for a
lightweight graph — the gap is a query layer, not a graph database.

**What this decision changes:** nothing immediately. The recommendation is
to extend `build_skill_graph.py` into a general-purpose workspace graph
indexer (covering wiki, ADRs, handoffs) when the "what depends on X?"
question becomes painful enough to justify the ~200-line script. Until then,
the existing `relations:` frontmatter + `[[wikilinks]]` + `build_skill_graph.py`
cover the most common cases.

## What exists in the field

### Three families of graphs

| Family | What it captures | Key nodes | Key edges |
|--------|-----------------|-----------|-----------|
| **Architecture Knowledge Graph (AKG/EAKG)** | Architecture models, components, layers | Components, connectors, interfaces, qualities | depends-on, connects-to, realizes, constrains |
| **Decision Knowledge Graph (DKG)** | Architecture decisions with rationale | Decisions (ADR-style: context, alternatives, chosen, consequences) | affects, supersedes, constrains, enables |
| **Solution Graph** | Two meanings: (1) pruned reasoning subgraph from a KG; (2) multi-agent collaboration topology | (1) Variables, equations, rules; (2) Agents with roles | (1) depends-on, computes; (2) delegates-to, communicates-with |

These are documented in academic literature (EAKG Toolkit, ArchiMate → Neo4j),
enterprise platforms (Ardoq, CoLab, Graphwise), and emerging AI agent
frameworks (LangGraph, GraphRAG, ARG-Designer for dynamic agent topologies).

### What they deliver (for those who need them)

1. **Impact analysis** — "if I reverse decision X, what components/skills/docs are affected?"
2. **Traceability** — "why does this code exist? what decision drove it? what alternatives were rejected?"
3. **Decision reuse** — "have we solved a similar problem before? what did we choose and why?"
4. **Blast radius** — "if I change this skill, what downstream skills break?"
5. **Multi-hop reasoning** — "what skills consume a wiki concept that references a superseded ADR?"

### The cost (disconfirmation pass)

The critique is sharp and well-documented:

- **Ontology tax**: enterprise KG TCO estimated $10-20M, mostly people costs
  (not licenses or compute). POCs are cheap; production is expensive.
  Source: "The Ontology Tax" (Medium/Graph Praxis).
- **Maintenance burden**: continuous cleaning, schema evolution, data freshness.
  KGs are NOT "set and forget" — they require dedicated teams (5-15 people
  for enterprise scale).
- **Most KGs are glorified property graphs**: without deep semantic reasoning,
  the complexity is retained while the value is diluted. Source: Mark Burgess
  critique.
- **Decision framework**: if you have <5-10 entity/relationship types, rare
  multi-hop queries, stable schema, or can't articulate the value in 2
  sentences — skip it. Use simpler tools. Source: visrow/Medium.
- **Historical pattern**: multiple "years of the KG" (2001 Semantic Web, 2010
  Linked Data, 2012 Google KG, 2025 GraphRAG) failed to achieve broad escape
  velocity outside tech giants and niches.

## What already exists in THIS workspace

### The graph data is already there

| Source | Graph data | Format |
|--------|-----------|--------|
| Wiki concepts | `relations: [{target, type}]` frontmatter | Typed edges: supports, contradicts, refines, supersedes, related |
| Wiki body text | `[[wikilinks]]` | Untyped cross-references |
| ADRs | `P:\docs\adrs\ADR-NNN-*.md` | Sequential, with cross-references in body |
| Handoffs | `P:\docs\handoffs\*/HANDOFF.md` | Cross-references to wiki, skills, other handoffs |
| Skills | Composition tables, delegation patterns | `/www delegates to /web`, `/review calls /check` |
| Design docs | Traceability matrices | Per-doc component → implementation unit mapping |

### We already have a graph builder

`P:/.data/wiki/scripts/build_skill_graph.py` already:
- Scans all SKILL.md files across 5 scope directories
- Extracts three edge types: `delegates_to`, `consumes_provider`, `references_wiki`
- Builds adjacency lists + reverse index (who depends on X?)
- Outputs `P:/.data/wiki/concepts/skill-graph.md` (human-readable + embedded JSON)

This script was built session 2026-07-28 after the web-search-prime dependency
chain breakage (8 files needed updates but nothing tracked the dependencies).
It is exactly the lightweight, file-based, frontmatter-driven approach the
disconfirmation research recommends for solo/small teams.

## Recommendation

### NOT a full knowledge graph

A Neo4j-backed architecture KG with ontology design, SPARQL queries, and a
maintenance team is wildly over-engineered for this workspace. The operator
is solo. The entity types are <10. The multi-hop query frequency is low.
The maintenance burden would exceed the value.

### YES to extending the existing graph indexer

The optimal path is extending `build_skill_graph.py` (or building a sibling
`build_workspace_graph.py`) to cover:

| Artifact type | Edge source | Query it enables |
|---------------|------------|-----------------|
| Wiki concepts | `relations:` frontmatter + `[[wikilinks]]` | "What concepts does X refine/contradict/supersede?" |
| ADRs | Body cross-references + status | "What decisions are superseded? What still governs?" |
| Handoffs | Cross-references in body | "What handoffs reference this wiki concept?" |
| Skills | Existing `build_skill_graph.py` edges | "What skills depend on this provider?" |
| Design docs | Traceability matrix entries | "What design produced this implementation unit?" |

**Estimated effort:** ~200-300 lines of Python (extend the existing pattern).
**Maintenance:** near-zero — the script reads frontmatter that is already
written as part of normal wiki/handoff/ADR authoring.
**Query power:** "what depends on X?" across all artifact types — the
question that currently requires manual grep + reading.

### When to build it

Build it when the "what depends on X?" question becomes painful enough
that you're doing manual grep chains more than once per session. Until
then, the existing `build_skill_graph.py` + manual grep covers the
common case.

The trigger: the next time you change a wiki concept and wonder "what
else references this?" — that's the signal to build the indexer.

## The relationship to GraphRAG and agent memory

The research surfaced a 2025-2026 trend: knowledge graphs as the "brain"
or "trusted memory" for AI agent fleets. This is real and relevant:

- **GraphRAG**: retrieve relevant subgraphs + context for LLM generation
  (higher accuracy, less hallucination, explainable)
- **Agent memory**: agents query a shared KG for facts, history, and context
  instead of re-reading everything every session
- **Multi-hop reasoning**: graph traversal supports inferences that
  single-pass LLM reasoning struggles with

For this workspace, the wiki vault IS the agent memory. The `relations:`
frontmatter IS the graph. What's missing is not the graph — it's the
query layer that lets agents (and the operator) traverse it efficiently.

A future enhancement could expose the workspace graph as a queryable
interface that agents call instead of grep-ing wiki concepts. But that's
a v2 concern — the file-based indexer is v1.

## Falsifier

This analysis is wrong if:
- The workspace grows to 500+ artifacts and the flat-file grep approach
  becomes genuinely unworkable (would need a graph DB)
- The multi-hop query frequency increases dramatically (e.g., every /todo
  run needs to traverse the graph)
- A provider changes (like the web-search-prime incident) and the blast
  radius can't be determined from the existing skill graph alone
- The operator never actually asks "what depends on X?" (the question is
  theoretical, not practical)

## Decision context (why this research was needed)

The operator asked this question in the context of designing the
`email-skill` CLI wrapper (a `/design` run that produced a 1,700-line
design doc with traceability matrices). The question was whether the
design artifacts themselves should be linked in a graph, or whether the
existing flat-file + frontmatter approach is sufficient.

The answer: the existing approach is sufficient for now. The traceability
matrices in design docs are per-doc (they die with temp files). The durable
cross-references live in wiki concepts and ADRs, which already have the
`relations:` frontmatter structure. Extending `build_skill_graph.py` to
cover wiki + ADRs + handoffs is the right next step when the need arises.

## Related

- [[codebase-knowledge-graph-mapping]] — codebase KG tools (Graphify etc.)
- [[claude-code-automation-capabilities]] — mentions knowledge graph approaches
- [[dynamic-wiki-driven-skill-configuration]] — skills query wiki at runtime
- [[solo-director-ai-fleet-coordination-isolation-best-practices]] — fleet coordination patterns
