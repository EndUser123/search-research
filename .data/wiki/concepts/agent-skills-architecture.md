---
title: "Agent Skills Architecture"
created: 2026-07-28
source: nlm-sync-2026-07-28
tags: [nlm-synced, reference, skills]
summary: >
  Agent Skills represent a standardized organizational pattern for packaging instructions, scripts, and resources that AI agents can discover and use to perform specific tasks. This approach enables reusable, distributable capability modules across different AI agent platforms.
agent: grok
host: both
cognitive_load: 2
verification: single-source-verified
sources:
  - "NotebookLM notebook f7806918-c135-4931-944d-09d94ccc458d" ([INGESTED] - ext-Gemini CLI, Jules CLI, and Claude Code, synced 2026-07-28)
  - "NotebookLM source 0719e72b-8632-4c56-af6c-92948c5c567f" (sanjay3290-ai-skills.md, synced 2026-07-28)
  - "NotebookLM source 0e30fb74-c853-43b5-9b80-032cca22391d" (oaustegard-claude-skills.md, synced 2026-07-28)
  - "NotebookLM source 216d0ab8-25db-49bf-8f2c-2b7755b5ed80" (feiskyer-claude-code-settings.md, synced 2026-07-28)
  - "NotebookLM source 3555e8a8-66e3-476a-b703-eee423e284ec" (sanjay3290-ai-skills.md, synced 2026-07-28)
  - "NotebookLM source c36f6057-ea46-4167-a09d-831da526bbd4" (openai-skills.md, synced 2026-07-28)
  - "NotebookLM source c55e56bb-8ea6-4f8a-a341-8fe507241321" (davila7-claude-code-templates.md, synced 2026-07-28)
provenance:
  chain:
    - level: concept
      id: agent-skills-architecture
    - level: notebook
      id: f7806918-c135-4931-944d-09d94ccc458d
      title: [INGESTED] - ext-Gemini CLI, Jules CLI, and Claude Code
      url: https://notebooklm.google.com/notebook/f7806918-c135-4931-944d-09d94ccc458d
    - level: cluster
      id: 6
      name: skills-claude-skill
relations:
  - target: wiki/concepts/claude-code-plugins.md
    type: related
  - target: wiki/concepts/agent-capability-extension.md
    type: related
  - target: wiki/concepts/skill-installation-pattern.md
    type: related
---

# Agent Skills Architecture

## Decision context

**Definition:** Agent Skills represent a standardized organizational pattern for packaging instructions, scripts, and resources that AI agents can discover and use to perform specific tasks. This approach enables reusable, distributable capability modules across different AI agent platforms.

Synthesized from **6 contributing transcripts** in NotebookLM notebook *[INGESTED] - ext-Gemini CLI, Jules CLI, and Claude Code*, clustered into the "skills-claude-skill" sub-topic. Each claim below cites the specific transcript (source_id + title) that supports it; the frontmatter provenance chain carries the full concept → notebook → cluster → source URL hops.

**Why this matters:** concepts synced from NotebookLM carry provenance back to the source material (notebook → cluster → original URL when invoked via `--from-clusters`). A reader can verify any claim by following the provenance chain in the frontmatter.

## Operational details

- Skills are structured as folders containing instructions, scripts, and resources that AI agents can discover and execute [5]
- The skills repository structure follows a consistent pattern with SKILL.md documentation files and corresponding scripts/ directories [1][2][4]
- Skills enable packaging of domain-specific capabilities such as Atlassian integration, Azure DevOps operations, deep research, and Gmail management [1][4]
- The openai/skills repository catalogs skills for use and distribution with Codex, establishing an open standard referenced at agentskills.io [5]
- Skills can be installed system-wide (e.g., .system/skills/ in Codex) or distributed as packages [5]
- Custom skills are supported through defined creation patterns, allowing teams to extend agent capabilities [5]
- Skills implementations vary across repositories, with some using Python scripts (e.g., api_client.py, auth.py) while others use JavaScript/TypeScript [1][2][6]

## Verifiable values

| Name | Value |
|---|---|
| Repository count referenced | `6 repositories with skill implementations` |
| Skill domains documented | `Atlassian, Azure DevOps, deep-research, elevenlabs, Gmail, GitHub integration, Bluesky browsing` |
| Open standard reference | `agentskills.io` |

## Related concepts

- [[claude-code-plugins]] — Claude Code Plugins
- [[agent-capability-extension]] — Agent Capability Extension
- [[skill-installation-pattern]] — Skill Installation Pattern
- [[codex-skills-distribution]] — Codex Skills Distribution

## Citations (from contributing transcripts)

- **Claim:** Agent Skills are folders of instructions, scripts, and resources that AI agents can discover and use to perform at specific tasks
  - Source: openai-skills.md (`c36f6057-ea46-4167-a09d-831da526bbd4`)
  - Context: Agent Skills are folders of instructions, scripts, and resources that AI agents can discover and use to perform at specific tasks. Write once, use everywhere.
- **Claim:** Codex uses skills to package capabilities for repeatable task completion
  - Source: openai-skills.md (`c36f6057-ea46-4167-a09d-831da526bbd4`)
  - Context: Codex uses skills to help package capabilities that teams and individuals can use to complete specific tasks in a repeatable way. This repository catalogs skills for use and distribution with Codex.
- **Claim:** Skills follow a consistent folder structure with SKILL.md documentation
  - Source: sanjay3290-ai-skills.md (`3555e8a8-66e3-476a-b703-eee423e284ec`)
  - Context: File tree showing skills directories with SKILL.md and scripts/ subdirectories for each domain (atlassian, azure-devops, deep-research, elevenlabs, gmail)
- **Claim:** Skills implementations span multiple programming languages including Python and JavaScript
  - Source: davila7-claude-code-templates.md (`c55e56bb-8ea6-4f8a-a341-8fe507241321`)
  - Context: Repository contains api/ directory with JavaScript files, cli-tool/, and plugin configurations alongside skill definitions
- **Claim:** The skills open standard is documented at agentskills.io
  - Source: openai-skills.md (`c36f6057-ea46-4167-a09d-831da526bbd4`)
  - Context: Learn more: Agent Skills open standard (agentskills.io)

## Receipts

Source-derived concept: all claims in this page originate from
transcripts in NotebookLM notebook `f7806918-c135-4931-944d-09d94ccc458d`
(cluster `skills-claude-skill`). No claims are made
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
