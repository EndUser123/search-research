---
title: "CLAUDE.md Configuration Files"
created: 2026-07-28
source: nlm-sync-2026-07-28
tags: [nlm-synced, reference, obsidian]
summary: >
  CLAUDE.md files are configuration documents placed in Obsidian vault repositories to provide guidance and context to Claude Code when working within those repositories, establishing project-specific instructions, roles, and operational parameters.
agent: grok
host: both
cognitive_load: 2
verification: single-source-verified
sources:
  - "NotebookLM notebook 55c988d8-818d-4ed9-b08b-12d6c697ff5f" (Claude Code and QMD: Persistent Knowledge Architecture, synced 2026-07-28)
  - "NotebookLM source 0f99d3df-4903-433d-9e99-db6592d05cee" (manimohans-obsidian-local-llm-helper.md, synced 2026-07-28)
  - "NotebookLM source 7afa8d15-3d8d-48b1-9d8f-756fc36c45df" (heyitsnoah-claudesidian.md, synced 2026-07-28)
  - "NotebookLM source 9ed429a1-066e-4fd9-b9ce-b3e342d98a2f" (hancengiz-cc-obsidian-vault-api-skill.md, synced 2026-07-28)
  - "NotebookLM source 9f09a31b-9ae2-4d56-80d3-a38dd4b6da01" (iansinnott-obsidian-claude-code-mcp.md, synced 2026-07-28)
  - "NotebookLM source f08abd3a-4543-47b4-8f68-c28142081cea" (Magic-wei-obsidian_wiki_template.md, synced 2026-07-28)
provenance:
  chain:
    - level: concept
      id: claudemd-configuration-files
    - level: notebook
      id: 55c988d8-818d-4ed9-b08b-12d6c697ff5f
      title: Claude Code and QMD: Persistent Knowledge Architecture
      url: https://notebooklm.google.com/notebook/55c988d8-818d-4ed9-b08b-12d6c697ff5f
    - level: cluster
      id: 4
      name: obsidian-claude-readme
relations:
  - target: wiki/concepts/structured-vault-organization.md
    type: related
  - target: wiki/concepts/claude-code-skills-architecture.md
    type: related
  - target: wiki/concepts/mcp-integration-pattern.md
    type: related
---

# CLAUDE.md Configuration Files

## Decision context

**Definition:** CLAUDE.md files are configuration documents placed in Obsidian vault repositories to provide guidance and context to Claude Code when working within those repositories, establishing project-specific instructions, roles, and operational parameters.

Synthesized from **5 contributing transcripts** in NotebookLM notebook *Claude Code and QMD: Persistent Knowledge Architecture*, clustered into the "obsidian-claude-readme" sub-topic. Each claim below cites the specific transcript (source_id + title) that supports it; the frontmatter provenance chain carries the full concept → notebook → cluster → source URL hops.

**Why this matters:** concepts synced from NotebookLM carry provenance back to the source material (notebook → cluster → original URL when invoked via `--from-clusters`). A reader can verify any claim by following the provenance chain in the frontmatter.

## Operational details

- CLAUDE.md files serve as primary guidance documents for Claude Code when operating in a repository, as demonstrated by manimohans/obsidian-local-llm-helper which includes build commands and project structure information
- These configuration files can define build commands and development workflows, as seen in manimohans/obsidian-local-llm-helper where a 'Build Comman' section provides compilation instructions
- CLAUDE.md files establish developer roles and expertise areas, such as in hancengiz/cc-obsidian-vault-api-skill which identifies expertise in Claude Code Skills, YAML frontmatter, and Obsidian Local REST API
- Repositories may include multiple configuration variants such as CLAUDE-BOOTSTRAP.md in heyitsnoah/claudesidian for initial setup guidance distinct from standard operation
- The configuration files often accompany extensive documentation including TROUBLESHOOTING.md and EXPECTED_BEHAVIOR.md to provide comprehensive operational guidance

## Related concepts

- structured-vault-organization — Structured Vault Organization
- claude-code-skills-architecture — Claude Code Skills Architecture
- mcp-integration-pattern — MCP Integration Pattern

## Citations (from contributing transcripts)

- **Claim:** CLAUDE.md files serve as guidance documents for Claude Code in a repository
  - Source: manimohans-obsidian-local-llm-helper.md (`0f99d3df-4903-433d-9e99-db6592d05cee`)
  - Context: This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.
- **Claim:** CLAUDE.md files can define build commands and development workflows
  - Source: manimohans-obsidian-local-llm-helper.md (`0f99d3df-4903-433d-9e99-db6592d05cee`)
  - Context: ## Build Comman
- **Claim:** CLAUDE.md files establish developer roles and expertise areas
  - Source: hancengiz-cc-obsidian-vault-api-skill.md (`9ed429a1-066e-4fd9-b9ce-b3e342d98a2f`)
  - Context: You are an expert in: 1. Claude Code Skills: Understanding skill architecture, YAML frontm
- **Claim:** Repositories may include CLAUDE-BOOTSTRAP.md as a variant configuration file
  - Source: heyitsnoah-claudesidian.md (`7afa8d15-3d8d-48b1-9d8f-756fc36c45df`)
  - Context: CLAUDE-BOOTSTRAP.md

## Receipts

Source-derived concept: all claims in this page originate from
transcripts in NotebookLM notebook `55c988d8-818d-4ed9-b08b-12d6c697ff5f`
(cluster `obsidian-claude-readme`). No claims are made
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

- NotebookLM notebook [Claude Code and QMD: Persistent Knowledge Architecture](https://notebooklm.google.com/notebook/55c988d8-818d-4ed9-b08b-12d6c697ff5f)
- Studio artifacts: Report (concept extraction) + Data-Table (tabular facts)
