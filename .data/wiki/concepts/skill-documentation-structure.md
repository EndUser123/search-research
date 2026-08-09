---
title: "Skill Documentation Structure"
created: 2026-07-28
source: nlm-sync-2026-07-28
tags: [nlm-synced, reference, skills]
summary: >
  Agent skills are modular components with structured documentation that define their purpose, implementation, and usage patterns within an agent system. The documentation typically resides alongside the skill code and follows conventions that enable discoverability and consistent integration across d
agent: grok
host: both
cognitive_load: 2
verification: single-source-verified
sources:
  - "NotebookLM notebook f7806918-c135-4931-944d-09d94ccc458d" (ext-Gemini CLI, Jules CLI, and Claude Code, synced 2026-07-28)
  - "NotebookLM source 0f56e05b-6c73-4d24-96e2-63cf95e66b1b" (cexll-myclaude.md, synced 2026-07-28)
  - "(PDF) Collaborative Multidisciplinary Design Optimization for Conceptual Design of Complex Products - ResearchGate" (https://www.researchgate.net/publication/311678834_Collaborative_Multidisciplinary_Design_Optimization_for_Conceptual_Design_of_Complex_Products, transcript synced 2026-07-28)
  - "NotebookLM source ad6e01d9-29c9-4ff7-aa9e-2442146de0a5" (RefoundAI-lenny-skills.md, synced 2026-07-28)
  - "NotebookLM source c0b0106c-f209-4662-ab12-eded3bab925d" (sickn33-antigravity-awesome-skills.md, synced 2026-07-28)
  - "NotebookLM source db1d2bbd-5708-4701-b70f-dcce391ce94f" (RefoundAI-lenny-skills.md, synced 2026-07-28)
  - "NotebookLM source e1de206e-11b1-40eb-ab99-46f335536ca7" (athola-claude-night-market.md, synced 2026-07-28)
  - "NotebookLM source e30f4ac7-4af3-42a3-ab8b-f46c3b0f5a61" (ada20204-qwen-voice.md, synced 2026-07-28)
provenance:
  chain:
    - level: concept
      id: skill-documentation-structure
    - level: notebook
      id: f7806918-c135-4931-944d-09d94ccc458d
      title: ext-Gemini CLI, Jules CLI, and Claude Code
      url: https://notebooklm.google.com/notebook/f7806918-c135-4931-944d-09d94ccc458d
    - level: cluster
      id: 5
      name: skills-design-readme
    - level: source_url
      url: https://www.researchgate.net/publication/311678834_Collaborative_Multidisciplinary_Design_Optimization_for_Conceptual_Design_of_Complex_Products
      title: (PDF) Collaborative Multidisciplinary Design Optimization for Conceptual Design of Complex Products - ResearchGate
relations:
  - target: wiki/concepts/agent-skill-architecture.md
    type: related
  - target: wiki/concepts/plugin-system-design.md
    type: related
  - target: wiki/concepts/multidisciplinary-design-optimization.md
    type: related
---

# Skill Documentation Structure

## Decision context

**Definition:** Agent skills are modular components with structured documentation that define their purpose, implementation, and usage patterns within an agent system. The documentation typically resides alongside the skill code and follows conventions that enable discoverability and consistent integration across different agent platforms.

Synthesized from **7 contributing transcripts** in NotebookLM notebook *ext-Gemini CLI, Jules CLI, and Claude Code*, clustered into the "skills-design-readme" sub-topic. Each claim below cites the specific transcript (source_id + title) that supports it; the frontmatter provenance chain carries the full concept → notebook → cluster → source URL hops.

**Why this matters:** concepts synced from NotebookLM carry provenance back to the source material (notebook → cluster → original URL when invoked via `--from-clusters`). A reader can verify any claim by following the provenance chain in the frontmatter.

## Operational details

- Skills are organized in dedicated directories containing a SKILL.md file that defines the skill's metadata and instructions
- The file tree structure reveals skills organized by functional categories such as ai-evals, ai-product-strategy, analyzing-user-feedback, and behavioral-product-design
- SKILL.md files serve as the primary documentation artifact for each skill, providing guidance on how the skill operates and should be invoked
- Some repositories include additional documentation files like PLUGIN_README.md, guest-insights.md references, and CONTRIBUTING.md to support skill development and collaboration
- Skills may reference external resources through reference directories, allowing supplementary materials to be attached to the skill documentation
- The presence of skills_index.json files in some repositories suggests cataloging mechanisms for discovering and managing available skills

## Verifiable values

| Name | Value |
|---|---|
| cexll/myclaude skill categories | `7+ agent types (bmad-architect, bmad-dev, bmad-orchestrator, bmad-po, bmad-qa, bmad-review, bmad-sm) and 8+ development commands` |
| RefoundAI/lenny-skills structure | `skills organized under skills/ subdirectory with individual SKILL.md per skill` |
| sickn33/antigravity-awesome-skills content size | `~229,582 words (~918,331 chars)` |
| athola/claude-night-market plugins | `multiple plugin archetypes including abstract, conjure, sanctum, scribe, and domain-specialist patterns` |

## Related concepts

- [[agent-skills-architecture]] — Agent Skill Architecture
- plugin-system-design — Plugin System Design
- multidisciplinary-design-optimization — Multidisciplinary Design Optimization

## Citations (from contributing transcripts)

- **Claim:** Skills are organized in directories containing SKILL.md files for documentation
  - Source: RefoundAI-lenny-skills.md (`db1d2bbd-5708-4701-b70f-dcce391ce94f`)
  - Context: skills/ai-evals/ SKILL.md, skills/ai-product-strategy/ SKILL.md, skills/analyzing-user-feedback/ SKILL.md
- **Claim:** Repository contains multiple agent types with specialized roles
  - Source: cexll-myclaude.md (`0f56e05b-6c73-4d24-96e2-63cf95e66b1b`)
  - Context: bmad-architect.md, bmad-dev.md, bmad-orchestrator.md, bmad-po.md, bmad-qa.md, bmad-review.md, bmad-sm.md
- **Claim:** Development commands provide standardized skill interactions
  - Source: cexll-myclaude.md (`0f56e05b-6c73-4d24-96e2-63cf95e66b1b`)
  - Context: ask.md, bugfix.md, code.md, debug.md, docs.md, enhance-prompt.md, optimize.md, refactor.md, review.md
- **Claim:** Skills include reference materials for supplementary documentation
  - Source: RefoundAI-lenny-skills.md (`db1d2bbd-5708-4701-b70f-dcce391ce94f`)
  - Context: skills/ai-evals/references/ guest-insights.md
- **Claim:** Large-scale skills repositories exist with extensive cataloging
  - Source: sickn33-antigravity-awesome-skills.md (`c0b0106c-f209-4662-ab12-eded3bab925d`)
  - Context: CATALOG.md, CHANGELOG.md, skills_index.json
- **Claim:** Plugin systems extend skill capabilities through specialized patterns
  - Source: athola-claude-night-market.md (`e1de206e-11b1-40eb-ab99-46f335536ca7`)
  - Context: abstract, archetypes, attune, conjure, conserve, domain-specialists, egregore, foundation-layer

## Receipts

Source-derived concept: all claims in this page originate from
transcripts in NotebookLM notebook `f7806918-c135-4931-944d-09d94ccc458d`
(cluster `skills-design-readme`). No claims are made
about local workspace implementation. Trigger words like
'mechanism', 'scanner', 'gate', 'hook', 'because' refer to concepts
discussed in the source videos, not to local code behavior.
Implementation path: nlm-to-wiki/scripts/synthesize_subtopics.py
(LLM synthesis from transcripts — no local code inspected).

## What this means for our workspace

Synced from NotebookLM. Provenance chain (concept → notebook → cluster → URL) is in frontmatter; follow it back to the source material.

## Falsifier

If a re-sync of the source notebook produces a different definition or different values, this page should be updated (or marked as superseded). The sync manifest at `P:/.data/wiki/_state/nlm-sync-manifest.json` records when this page was last regenerated.

## Sources

- NotebookLM notebook [ext-Gemini CLI, Jules CLI, and Claude Code](https://notebooklm.google.com/notebook/f7806918-c135-4931-944d-09d94ccc458d)
- Studio artifacts: Report (concept extraction) + Data-Table (tabular facts)
