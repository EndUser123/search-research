---
title: "Agent Skills"
created: 2026-07-28
source: nlm-sync-2026-07-28
tags: [nlm-synced, reference, skills]
summary: >
  Agent Skills are structured packages of instructions, scripts, and resources that AI agents can discover and apply to perform specific tasks in a repeatable manner. These packages follow an open standard enabling distribution and reuse across different AI agent implementations.
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
      id: agent-skills
    - level: notebook
      id: f7806918-c135-4931-944d-09d94ccc458d
      title: ext-Gemini CLI, Jules CLI, and Claude Code
      url: https://notebooklm.google.com/notebook/f7806918-c135-4931-944d-09d94ccc458d
    - level: cluster
      id: 6
      name: skills-claude-skill
relations:
  - target: wiki/concepts/agent-configuration.md
    type: related
  - target: wiki/concepts/custom-instructions.md
    type: related
  - target: wiki/concepts/tool-integration.md
    type: related
---

# Agent Skills

## Decision context

**Definition:** Agent Skills are structured packages of instructions, scripts, and resources that AI agents can discover and apply to perform specific tasks in a repeatable manner. These packages follow an open standard enabling distribution and reuse across different AI agent implementations.

Synthesized from **6 contributing transcripts** in NotebookLM notebook *ext-Gemini CLI, Jules CLI, and Claude Code*, clustered into the "skills-claude-skill" sub-topic. Each claim below cites the specific transcript (source_id + title) that supports it; the frontmatter provenance chain carries the full concept → notebook → cluster → source URL hops.

**Why this matters:** concepts synced from NotebookLM carry provenance back to the source material (notebook → cluster → original URL when invoked via `--from-clusters`). A reader can verify any claim by following the provenance chain in the frontmatter.

## Operational details

- Skills are organized as folders containing instruction files (SKILL.md), scripts, and resource assets
- Skills enable repeatable task completion by packaging domain-specific capabilities into distributable units
- Skills can integrate with external services through accompanying scripts (e.g., API clients, authentication handlers)
- Skills follow an open standard documented at agentskills.io, allowing interoperability between agent implementations
- Skills may include configuration files, templates, and example data alongside executable scripts
- Skills can be installed into agent environments, making them available for discovery and use

## Related concepts

- [[agent-configuration]] — Agent Configuration
- [[custom-instructions]] — Custom Instructions
- [[tool-integration]] — Tool Integration
- [[open-standards]] — Open Standards

## Citations (from contributing transcripts)

- **Claim:** Agent Skills are folders of instructions, scripts, and resources that AI agents can discover and use to perform at specific tasks
  - Source: openai-skills.md (`c36f6057-ea46-4167-a09d-831da526bbd4`)
  - Context: Agent Skills are folders of instructions, scripts, and resources that AI agents can discover and use to perform at specific tasks. Write once, use everywhere.
- **Claim:** Skills enable repeatable task completion and distribution with Codex
  - Source: openai-skills.md (`c36f6057-ea46-4167-a09d-831da526bbd4`)
  - Context: Codex uses skills to help package capabilities that teams and individuals can use to complete specific tasks in a repeatable way. This repository catalogs skills for use and distribution with Codex.
- **Claim:** Skills follow an open standard for interoperability
  - Source: openai-skills.md (`c36f6057-ea46-4167-a09d-831da526bbd4`)
  - Context: Learn more: Agent Skills open standard - agentskills.io
- **Claim:** Skills are organized with instruction files, scripts, and resource directories
  - Source: sanjay3290-ai-skills.md (`3555e8a8-66e3-476a-b703-eee423e284ec`)
  - Context: skills/atlassian/ - SKILL.md, requirements.txt, scripts/ directory with api_client.py, auth.py, confluence.py, jira.py, mcp_client.py
- **Claim:** Skills can include service-specific integration scripts
  - Source: sanjay3290-ai-skills.md (`3555e8a8-66e3-476a-b703-eee423e284ec`)
  - Context: skills/azure-devops/scripts/ - api_client.py, attachments.py, auth.py, core.py, environments.py, pipelines.py, policies.py, repos.py, search.py, security.py, test_plans.py, variable_groups.py, wiki.py, work.py, work_items.py

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
