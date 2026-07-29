---
title: "Custom Skills for Claude"
created: 2026-07-28
source: nlm-sync-2026-07-28
tags: [nlm-synced, reference, claude]
summary: >
  Custom skills are packaged instruction sets that teach Claude to handle specific tasks or workflows, allowing users to encode preferences, processes, and domain expertise once for reuse across conversations.
agent: grok
host: both
cognitive_load: 2
verification: single-source-verified
sources:
  - "NotebookLM notebook 8138a528-f5c2-4ee4-b5a9-f3359f48f0dc" (Mastering Claude Skills, synced 2026-07-28)
  - "The Complete Guide to Building Skills for Claude | Anthropic" (https://resources.anthropic.com/hubfs/The-Complete-Guide-to-Building-Skill-for-Claude.pdf, transcript synced 2026-07-28)
  - "How to create custom skills | Claude Help Center" (https://support.claude.com/en/articles/12512198-how-to-create-custom-skills, transcript synced 2026-07-28)
  - "What are skills? | Claude Help Center" (https://support.claude.com/en/articles/12512176-what-are-skills, transcript synced 2026-07-28)
  - "Use skills in Claude | Claude Help Center" (https://support.claude.com/en/articles/12512180-use-skills-in-claude, transcript synced 2026-07-28)
provenance:
  chain:
    - level: concept
      id: custom-skills-for-claude
    - level: notebook
      id: 8138a528-f5c2-4ee4-b5a9-f3359f48f0dc
      title: Mastering Claude Skills
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
  - target: wiki/concepts/claude-code-execution.md
    type: related
  - target: wiki/concepts/mcp-integrations.md
    type: related
  - target: wiki/concepts/workflow-automation.md
    type: related
---

# Custom Skills for Claude

## Decision context

**Definition:** Custom skills are packaged instruction sets that teach Claude to handle specific tasks or workflows, allowing users to encode preferences, processes, and domain expertise once for reuse across conversations.

Synthesized from **4 contributing transcripts** in NotebookLM notebook *Mastering Claude Skills*, clustered into the "claude-support-skills" sub-topic. Each claim below cites the specific transcript (source_id + title) that supports it; the frontmatter provenance chain carries the full concept → notebook → cluster → source URL hops.

**Why this matters:** concepts synced from NotebookLM carry provenance back to the source material (notebook → cluster → original URL when invoked via `--from-clusters`). A reader can verify any claim by following the provenance chain in the frontmatter.

## Operational details

- Packaged as a simple folder containing a set of instructions that define the skill's behavior
- Designed for repeatable workflows such as generating frontend designs from specs, conducting research with consistent methodology, or creating documents following team style guides
- Integrate with built-in Claude capabilities including code execution and document creation
- For MCP integrations, skills provide a layer that helps transform raw tool access into reliable, optimized workflows

## Related concepts

- [[claude-code-execution]] — Claude Code Execution
- [[mcp-integrations]] — MCP Integrations
- [[workflow-automation]] — Workflow Automation

## Citations (from contributing transcripts)

- **Claim:** A skill is a set of instructions packaged as a folder
  - Source: The Complete Guide to Building Skills for Claude | Anthropic (`2de309d4-ad2d-4fcc-8585-1427c896b030`)
  - Context: A skill is a set of instructions - packaged as a simple folder - that teaches Claude how to handle specific tasks or workflows
- **Claim:** Skills teach Claude once for reuse across conversations
  - Source: The Complete Guide to Building Skills for Claude | Anthropic (`2de309d4-ad2d-4fcc-8585-1427c896b030`)
  - Context: Instead of re-explaining your preferences, processes, and domain expertise in every conversation, skills let you teach Claude once and benefit every time
- **Claim:** Skills support repeatable workflows including design generation, research, and document creation
  - Source: The Complete Guide to Building Skills for Claude | Anthropic (`2de309d4-ad2d-4fcc-8585-1427c896b030`)
  - Context: Skills are powerful when you have repeatable workflows: generating frontend designs from specs, conducting research with consistent methodology, creating documents that follow your team's style guide, or orchestrating multi-step processes
- **Claim:** Skills integrate with built-in capabilities like code execution and document creation
  - Source: The Complete Guide to Building Skills for Claude | Anthropic (`2de309d4-ad2d-4fcc-8585-1427c896b030`)
  - Context: They work well with Claude's built-in capabilities like code execution and document creation
- **Claim:** For MCP integrations, skills turn raw tool access into reliable workflows
  - Source: The Complete Guide to Building Skills for Claude | Anthropic (`2de309d4-ad2d-4fcc-8585-1427c896b030`)
  - Context: For those building MCP integrations, skills add another powerful layer helping turn raw tool access into reliable, optimized workflows

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

- NotebookLM notebook [Mastering Claude Skills](https://notebooklm.google.com/notebook/8138a528-f5c2-4ee4-b5a9-f3359f48f0dc)
- Studio artifacts: Report (concept extraction) + Data-Table (tabular facts)
