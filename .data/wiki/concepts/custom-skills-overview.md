---
title: "Custom Skills Overview"
created: 2026-07-28
source: nlm-sync-2026-07-28
tags: [nlm-synced, reference, claude]
summary: >
  A skill is a packaged set of instructions, organized as a simple folder structure, that teaches Claude how to handle specific tasks or workflows. Skills allow users to encode their preferences, processes, and domain expertise once, eliminating the need to re-explain them in every conversation.
agent: grok
host: both
cognitive_load: 2
verification: single-source-verified
sources:
  - "NotebookLM notebook 8138a528-f5c2-4ee4-b5a9-f3359f48f0dc" ([INGESTED] - Mastering Claude Skills, synced 2026-07-28)
  - "The Complete Guide to Building Skills for Claude | Anthropic" (https://resources.anthropic.com/hubfs/The-Complete-Guide-to-Building-Skill-for-Claude.pdf, transcript synced 2026-07-28)
  - "How to create custom skills | Claude Help Center" (https://support.claude.com/en/articles/12512198-how-to-create-custom-skills, transcript synced 2026-07-28)
  - "What are skills? | Claude Help Center" (https://support.claude.com/en/articles/12512176-what-are-skills, transcript synced 2026-07-28)
  - "Use skills in Claude | Claude Help Center" (https://support.claude.com/en/articles/12512180-use-skills-in-claude, transcript synced 2026-07-28)
provenance:
  chain:
    - level: concept
      id: custom-skills-overview
    - level: notebook
      id: 8138a528-f5c2-4ee4-b5a9-f3359f48f0dc
      title: [INGESTED] - Mastering Claude Skills
      url: https://notebooklm.google.com/notebook/8138a528-f5c2-4ee4-b5a9-f3359f48f0dc
    - level: cluster
      id: 9
      name: claude-support-skills
    - level: source_url
      url: https://resources.anthropic.com/hubfs/The-Complete-Guide-to-Building-Skill-for-Claude.pdf
      title: The Complete Guide to Building Skills for Claude | Anthropic
    - level: source_url
      url: https://support.claude.com/en/articles/12512198-how-to-create-custom-skills
      title: How to create custom skills | Claude Help Center
    - level: source_url
      url: https://support.claude.com/en/articles/12512176-what-are-skills
      title: What are skills? | Claude Help Center
    - level: source_url
      url: https://support.claude.com/en/articles/12512180-use-skills-in-claude
      title: Use skills in Claude | Claude Help Center
relations:
  - target: wiki/concepts/mcp-integrations.md
    type: related
  - target: wiki/concepts/workflow-automation.md
    type: related
  - target: wiki/concepts/claude-capabilities.md
    type: related
---

# Custom Skills Overview

## Decision context

**Definition:** A skill is a packaged set of instructions, organized as a simple folder structure, that teaches Claude how to handle specific tasks or workflows. Skills allow users to encode their preferences, processes, and domain expertise once, eliminating the need to re-explain them in every conversation.

Synthesized from **4 contributing transcripts** in NotebookLM notebook *[INGESTED] - Mastering Claude Skills*, clustered into the "claude-support-skills" sub-topic. Each claim below cites the specific transcript (source_id + title) that supports it; the frontmatter provenance chain carries the full concept → notebook → cluster → source URL hops.

**Why this matters:** concepts synced from NotebookLM carry provenance back to the source material (notebook → cluster → original URL when invoked via `--from-clusters`). A reader can verify any claim by following the provenance chain in the frontmatter.

## Operational details

- Skills are organized as a folder structure containing instruction sets for specific tasks or workflows
- The approach is designed for repeatable workflows such as generating frontend designs from specs, conducting research with consistent methodology, or creating documents following team style guides
- Skills integrate with Claude's built-in capabilities including code execution and document creation
- For MCP integrations, skills provide an additional layer that helps transform raw tool access into reliable, optimized workflows
- The skill development lifecycle includes phases for planning and design, testing and iteration, distribution and sharing, and troubleshooting
- This approach allows customization of Claude without requiring repeated explanations of user preferences in each conversation

## Related concepts

- mcp-integrations — MCP Integrations
- workflow-automation — Workflow Automation
- claude-capabilities — Claude Capabilities
- skill-development-lifecycle — Skill Development Lifecycle

## Citations (from contributing transcripts)

- **Claim:** A skill is a set of instructions packaged as a simple folder that teaches Claude how to handle specific tasks or workflows
  - Source: The Complete Guide to Building Skills for Claude | Anthropic (`2de309d4-ad2d-4fcc-8585-1427c896b030`)
  - Context: A skill is a set of instructions - packaged as a simple folder - that teaches Claude how to handle specific tasks or workflows.
- **Claim:** Skills eliminate the need to re-explain preferences and processes in every conversation
  - Source: The Complete Guide to Building Skills for Claude | Anthropic (`2de309d4-ad2d-4fcc-8585-1427c896b030`)
  - Context: Instead of re-explaining your preferences, processes, and domain expertise in every conversation, skills let you teach Claude once and benefit every time.
- **Claim:** Skills work well for repeatable workflows like generating frontend designs, conducting research, or creating documents
  - Source: The Complete Guide to Building Skills for Claude | Anthropic (`2de309d4-ad2d-4fcc-8585-1427c896b030`)
  - Context: Skills are powerful when you have repeatable workflows: generating frontend designs from specs, conducting research with consistent methodology, creating documents that follow your team's style guide, or orchestrating multi-step processes.
- **Claim:** Skills integrate with Claude's built-in capabilities like code execution and document creation
  - Source: The Complete Guide to Building Skills for Claude | Anthropic (`2de309d4-ad2d-4fcc-8585-1427c896b030`)
  - Context: They work well with Claude's built-in capabilities like code execution and document creation.
- **Claim:** Skills help transform raw tool access into reliable, optimized workflows for MCP integrations
  - Source: The Complete Guide to Building Skills for Claude | Anthropic (`2de309d4-ad2d-4fcc-8585-1427c896b030`)
  - Context: For those building MCP integrations, skills add another powerful layer helping turn raw tool access into reliable, optimized workflows.

## Receipts

Source-derived concept: all claims in this page originate from
transcripts in NotebookLM notebook `8138a528-f5c2-4ee4-b5a9-f3359f48f0dc`
(cluster `claude-support-skills`). No claims are made
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

- NotebookLM notebook [[INGESTED] - Mastering Claude Skills](https://notebooklm.google.com/notebook/8138a528-f5c2-4ee4-b5a9-f3359f48f0dc)
- Studio artifacts: Report (concept extraction) + Data-Table (tabular facts)
