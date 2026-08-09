---
title: "Agent Skills Documentation Pattern"
created: 2026-07-28
source: nlm-sync-2026-07-28
tags: [nlm-synced, reference, skills]
summary: >
  A standardized approach for defining, installing, and configuring reusable capabilities (skills) for AI agents, implemented through structured markdown files that document purpose, installation, requirements, and usage patterns.
agent: grok
host: both
cognitive_load: 2
verification: single-source-verified
sources:
  - "NotebookLM notebook f7806918-c135-4931-944d-09d94ccc458d" ([INGESTED] - ext-Gemini CLI, Jules CLI, and Claude Code, synced 2026-07-28)
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
      id: agent-skills-documentation-pattern
    - level: notebook
      id: f7806918-c135-4931-944d-09d94ccc458d
      title: [INGESTED] - ext-Gemini CLI, Jules CLI, and Claude Code
      url: https://notebooklm.google.com/notebook/f7806918-c135-4931-944d-09d94ccc458d
    - level: cluster
      id: 5
      name: skills-design-readme
    - level: source_url
      url: https://www.researchgate.net/publication/311678834_Collaborative_Multidisciplinary_Design_Optimization_for_Conceptual_Design_of_Complex_Products
      title: (PDF) Collaborative Multidisciplinary Design Optimization for Conceptual Design of Complex Products - ResearchGate
relations:
  - target: wiki/concepts/agent-capability-packages.md
    type: related
  - target: wiki/concepts/plugin-architecture-pattern.md
    type: related
  - target: wiki/concepts/ai-agent-configuration-schema.md
    type: related
---

# Agent Skills Documentation Pattern

## Decision context

**Definition:** A standardized approach for defining, installing, and configuring reusable capabilities (skills) for AI agents, implemented through structured markdown files that document purpose, installation, requirements, and usage patterns.

Synthesized from **7 contributing transcripts** in NotebookLM notebook *[INGESTED] - ext-Gemini CLI, Jules CLI, and Claude Code*, clustered into the "skills-design-readme" sub-topic. Each claim below cites the specific transcript (source_id + title) that supports it; the frontmatter provenance chain carries the full concept → notebook → cluster → source URL hops.

**Why this matters:** concepts synced from NotebookLM carry provenance back to the source material (notebook → cluster → original URL when invoked via `--from-clusters`). A reader can verify any claim by following the provenance chain in the frontmatter.

## Operational details

- Skills are distributed as installable packages with structured documentation files (typically SKILL.md or README.md) that define the skill's goal, capabilities, and system requirements
- Installation is typically performed via command-line tools (e.g., npx skills add) with dependencies specified in package configuration files
- Skills document required environment variables (such as API keys) and system prerequisites (like ffmpeg for media processing) as installation requirements
- Repository organization follows a pattern where skills are contained in dedicated directories (e.g., skills/ai-evals/, skills/codex-review/) with supporting reference materials
- Configuration schemas are defined in JSON schema files that validate skill configuration parameters before runtime
- The skill definition files include operational details about what the capability enables, such as voice understanding combined with voice reply for agent interactions
- Skills can be organized by functional category, including domains such as product strategy, behavioral design, team culture, sales enablement, and code review workflows

## Verifiable values

| Name | Value |
|---|---|
| Python requirement | `3.10+` |
| System requirement | `ffmpeg` |
| Installation command | `npx skills add <repo>` |

## Related concepts

- agent-capability-packages — Agent Capability Packages
- plugin-architecture-pattern — Plugin Architecture Pattern
- ai-agent-configuration-schema — AI Agent Configuration Schema

## Citations (from contributing transcripts)

- **Claim:** Skills are defined through markdown files (SKILL.md) that document purpose, capabilities, and installation requirements
  - Source: RefoundAI-lenny-skills.md (`db1d2bbd-5708-4701-b70f-dcce391ce94f`)
  - Context: Skills are organized in directories with SKILL.md files that contain goal definitions, references, and guest insights for specialized domains like ai-evals, ai-product-strategy, and behavioral-product-design
- **Claim:** Skills are installed via command-line package managers with environment variable and system prerequisites
  - Source: ada20204-qwen-voice.md (`e30f4ac7-4af3-42a3-ab8b-f46c3b0f5a61`)
  - Context: Install command: npx skills add ada20204/qwen-voice. Required: DASHSCOPE_API_KEY environment variable and ffmpeg system requirement
- **Claim:** Configuration schemas validate skill parameters and define required configuration structures
  - Source: cexll-myclaude.md (`0f56e05b-6c73-4d24-96e2-63cf95e66b1b`)
  - Context: Repository contains config.schema.json files that define configuration validation for skill parameters
- **Claim:** Skills support voice-based capabilities combining speech recognition and synthesis
  - Source: ada20204-qwen-voice.md (`e30f4ac7-4af3-42a3-ab8b-f46c3b0f5a61`)
  - Context: Goal: Add voice understanding + voice reply to agent chats. Highlights: ASR (voice → text), TTS (text → voice), Voice Clone functionality
- **Claim:** Skills are categorized by functional domain such as development, product strategy, and team operations
  - Source: sickn33-antigravity-awesome-skills.md (`c0b0106c-f209-4662-ab12-eded3bab925d`)
  - Context: Repository contains skills_index.json and CATALOG.md organizing skills across code review, product strategy, and operational domains

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

- NotebookLM notebook [[INGESTED] - ext-Gemini CLI, Jules CLI, and Claude Code](https://notebooklm.google.com/notebook/f7806918-c135-4931-944d-09d94ccc458d)
- Studio artifacts: Report (concept extraction) + Data-Table (tabular facts)
