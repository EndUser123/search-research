---
title: "Agent Skill Documentation Patterns"
created: 2026-07-28
source: nlm-sync-2026-07-28
tags: [nlm-synced, reference, skills]
summary: >
  Agent skill documentation patterns define the structured approach for describing, organizing, and presenting modular AI capabilities in a standardized format that enables discovery, installation, and integration across different agent hosts.
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
      id: agent-skill-documentation-patterns
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
  - target: wiki/concepts/agent-plugin-architecture.md
    type: related
  - target: wiki/concepts/capability-interface-specification.md
    type: related
  - target: wiki/concepts/skill-distribution-registry.md
    type: related
---

# Agent Skill Documentation Patterns

## Decision context

**Definition:** Agent skill documentation patterns define the structured approach for describing, organizing, and presenting modular AI capabilities in a standardized format that enables discovery, installation, and integration across different agent hosts.

Synthesized from **7 contributing transcripts** in NotebookLM notebook *ext-Gemini CLI, Jules CLI, and Claude Code*, clustered into the "skills-design-readme" sub-topic. Each claim below cites the specific transcript (source_id + title) that supports it; the frontmatter provenance chain carries the full concept → notebook → cluster → source URL hops.

**Why this matters:** concepts synced from NotebookLM carry provenance back to the source material (notebook → cluster → original URL when invoked via `--from-clusters`). A reader can verify any claim by following the provenance chain in the frontmatter.

## Operational details

- Skills are packaged as modular components with explicit capability declarations (ASR, TTS, voice clone) to communicate functional scope to agent hosts
- Documentation structure follows a hierarchical file tree layout with SKILL.md at the root of each skill directory, serving as the primary interface contract
- Skill manifests (skills_index.json, CATALOG.md) aggregate individual skill metadata to enable catalog browsing and discovery
- Installation instructions use standardized commands (npx skills add) with explicit system and runtime requirements
- Skills declare environment variable dependencies (DASHSCOPE_API_KEY) and external tool requirements (ffmpeg) as part of their interface specification
- The documentation approach distinguishes between skill-level documentation (SKILL.md) and reference materials stored in subdirectories
- Skills may include guest insights and supplementary references in dedicated subdirectories to provide contextual knowledge without cluttering core documentation

## Verifiable values

| Name | Value |
|---|---|
| skill metadata format | `structured file tree with SKILL.md root file` |
| distribution mechanism | `npx skills add <repo> command pattern` |
| capability declaration | `explicit highlight sections listing functional components` |
| requirements specification | `system-level (ffmpeg) and runtime-level (Python 3.10+) separated` |

## Related concepts

- agent-plugin-architecture — Agent Plugin Architecture
- capability-interface-specification — Capability Interface Specification
- skill-distribution-registry — Skill Distribution Registry

## Citations (from contributing transcripts)

- **Claim:** Skills declare their capabilities explicitly through highlight sections listing functional components
  - Source: ada20204-qwen-voice.md (`e30f4ac7-4af3-42a3-ab8b-f46c3b0f5a61`)
  - Context: Highlights: - ASR: voice → text (optional coarse timestamps via chunking) - TTS: text → voice (default voice: Cherry) - Voice Clone: one sample voice → your custom voice → voice replies
- **Claim:** Skills use standardized installation commands with host compatibility notes
  - Source: ada20204-qwen-voice.md (`e30f4ac7-4af3-42a3-ab8b-f46c3b0f5a61`)
  - Context: Works great in Clawdbot (and other agent hosts that support Agent Skills). Install (Agent Skill): npx skills add ada20204/qwen-voice
- **Claim:** Skills follow a hierarchical file tree structure with SKILL.md as the primary documentation file
  - Source: RefoundAI-lenny-skills.md (`db1d2bbd-5708-4701-b70f-dcce391ce94f`)
  - Context: skills/ai-evals/ SKILL.md skills/ai-product-strategy/ SKILL.md
- **Claim:** Skills specify system-level and runtime-level requirements separately
  - Source: ada20204-qwen-voice.md (`e30f4ac7-4af3-42a3-ab8b-f46c3b0f5a61`)
  - Context: System: ffmpeg, Python: Python 3.10+, Recommended: uv (or any venv + pip)
- **Claim:** Skills organize supplementary reference materials in subdirectories separate from core documentation
  - Source: RefoundAI-lenny-skills.md (`db1d2bbd-5708-4701-b70f-dcce391ce94f`)
  - Context: skills/ai-evals/references/ guest-insights.md
- **Claim:** Skill catalogs aggregate individual skill metadata for discovery purposes
  - Source: sickn33-antigravity-awesome-skills.md (`c0b0106c-f209-4662-ab12-eded3bab925d`)
  - Context: skills_index.json CATALOG.md

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
