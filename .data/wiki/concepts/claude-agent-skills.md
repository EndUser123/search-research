---
title: "Claude Agent Skills"
created: 2026-07-28
source: nlm-sync-2026-07-28
tags: [nlm-synced, reference, skills]
summary: >
  Agent Skills are standardized folder structures containing instructions, scripts, and resources that enable AI agents to discover and execute specific capabilities. This packaging approach allows teams and individuals to create reusable skill implementations that work across different AI agent platf
agent: grok
host: both
cognitive_load: 2
verification: single-source-verified
sources:
  - "NotebookLM notebook f7806918-c135-4931-944d-09d94ccc458d" (ext-Gemini CLI, Jules CLI, and Claude Code, synced 2026-07-28)
  - "NotebookLM source 0719e72b-8632-4c56-af6c-92948c5c567f" (sanjay3290-ai-skills.md, synced 2026-07-28)
  - "NotebookLM source 0e30fb74-c853-43b5-9b80-032cca22391d" (oaustegard-claude-skills.md, synced 2026-07-28)
  - "NotebookLM source 216d0ab8-25db-49bf-8f2c-2b7755b5ed80" (feiskyer-claude-code-settings.md, synced 2026-07-28)
  - "NotebookLM source 3555e8a8-66e3-476a-b703-eee423e284ec" (sanjay3290-ai-skills.md, synced 2026-07-28)
  - "NotebookLM source c36f6057-ea46-4167-a09d-831da526bbd4" (openai-skills.md, synced 2026-07-28)
  - "NotebookLM source c55e56bb-8ea6-4f8a-a341-8fe507241321" (davila7-claude-code-templates.md, synced 2026-07-28)
provenance:
  chain:
    - level: concept
      id: claude-agent-skills
    - level: notebook
      id: f7806918-c135-4931-944d-09d94ccc458d
      title: ext-Gemini CLI, Jules CLI, and Claude Code
      url: https://notebooklm.google.com/notebook/f7806918-c135-4931-944d-09d94ccc458d
    - level: cluster
      id: 6
      name: skills-claude-skill
relations:
  - target: wiki/concepts/autonomous-skill-pattern.md
    type: related
  - target: wiki/concepts/agent-guidance-documents.md
    type: related
  - target: wiki/concepts/skill-discovery-protocol.md
    type: related
---

# Claude Agent Skills

## Decision context

**Definition:** Agent Skills are standardized folder structures containing instructions, scripts, and resources that enable AI agents to discover and execute specific capabilities. This packaging approach allows teams and individuals to create reusable skill implementations that work across different AI agent platforms.

Synthesized from **6 contributing transcripts** in NotebookLM notebook *ext-Gemini CLI, Jules CLI, and Claude Code*, clustered into the "skills-claude-skill" sub-topic. Each claim below cites the specific transcript (source_id + title) that supports it; the frontmatter provenance chain carries the full concept → notebook → cluster → source URL hops.

**Why this matters:** concepts synced from NotebookLM carry provenance back to the source material (notebook → cluster → original URL when invoked via `--from-clusters`). A reader can verify any claim by following the provenance chain in the frontmatter.

## Operational details

- Skills follow a consistent folder structure, typically containing a SKILL.md instruction file, requirements.txt for dependencies, and a scripts/ directory with executable code
- Each skill targets a specific capability domain such as Atlassian integration, Azure DevOps workflows, deep research tasks, ElevenLabs audio processing, or Gmail management
- Skills use a modular design where SKILL.md defines the skill's purpose, instructions, and configuration while supporting scripts provide the executable logic
- The open standard for Agent Skills is documented at agentskills.io, enabling cross-platform skill sharing
- Skills can include supporting assets such as configuration examples, templates, and documentation files alongside executable code
- Repository structures typically organize skills hierarchically under a skills/ directory, with each skill operating as an independent module

## Related concepts

- autonomous-skill-pattern — Autonomous Skill Pattern
- agent-guidance-documents — Agent Guidance Documents
- skill-discovery-protocol — Skill Discovery Protocol

## Citations (from contributing transcripts)

- **Claim:** Agent Skills are folders of instructions, scripts, and resources that AI agents can discover and use to perform at specific tasks
  - Source: openai-skills.md (`c36f6057-ea46-4167-a09d-831da526bbd4`)
  - Context: Agent Skills are folders of instructions, scripts, and resources that AI agents can discover and use to perform at specific tasks. Write once, use everywhere.
- **Claim:** Skills use SKILL.md files for instruction definitions and separate scripts directories for executable code
  - Source: sanjay3290-ai-skills.md (`3555e8a8-66e3-476a-b703-eee423e284ec`)
  - Context: skills/atlassian/SKILL.md, skills/atlassian/requirements.txt, skills/atlassian/scripts/api_client.py
- **Claim:** Skills are organized by domain such as accessing-github-repos, api-credentials, asking-questions, and browsing-bluesky
  - Source: oaustegard-claude-skills.md (`0e30fb74-c853-43b5-9b80-032cca22391d`)
  - Context: 📁 accessing-github-repos/, 📁 api-credentials/, 📁 asking-questions/, 📁 browsing-bluesky/
- **Claim:** Skills can include hooks configurations and plugin structures for extending agent behavior
  - Source: feiskyer-claude-code-settings.md (`216d0ab8-25db-49bf-8f2c-2b7755b5ed80`)
  - Context: 📁 plugins/autonomous-skill/skills/autonomous-skill/hooks/hooks.json, 📁 plugins/autonomous-skill/skills/autonomous-skill/scripts/
- **Claim:** Skills target specific platforms and services including Azure DevOps, Gmail, and ElevenLabs
  - Source: sanjay3290-ai-skills.md (`3555e8a8-66e3-476a-b703-eee423e284ec`)
  - Context: 📁 skills/azure-devops/, 📁 skills/gmail/, 📁 skills/elevenlabs/
- **Claim:** The open standard for Agent Skills enables cross-platform distribution
  - Source: openai-skills.md (`c36f6057-ea46-4167-a09d-831da526bbd4`)
  - Context: Agent Skills open standard: https://agentskills.io

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

- NotebookLM notebook [ext-Gemini CLI, Jules CLI, and Claude Code](https://notebooklm.google.com/notebook/f7806918-c135-4931-944d-09d94ccc458d)
- Studio artifacts: Report (concept extraction) + Data-Table (tabular facts)
