---
title: "Claude Code External Integration Patterns"
created: 2026-07-28
source: nlm-sync-2026-07-28
tags: [nlm-synced, reference, github]
summary: >
  GitHub-hosted projects demonstrating how Claude Code integrates with external tools and platforms, including Obsidian plugins, skill creation pipelines, and hook template systems for extending AI-assisted development workflows.
agent: grok
host: both
cognitive_load: 2
verification: single-source-verified
sources:
  - "NotebookLM notebook 55c988d8-818d-4ed9-b08b-12d6c697ff5f" (Claude Code and QMD: Persistent Knowledge Architecture, synced 2026-07-28)
  - "heyitsnoah/claudesidian - GitHub" (https://github.com/heyitsnoah/claudesidian, transcript synced 2026-07-28)
  - "Skill Creator - anthropics/claude-plugins-official - GitHub" (https://github.com/anthropics/claude-plugins-official/blob/main/plugins/skill-creator/skills/skill-creator/SKILL.md, transcript synced 2026-07-28)
  - "claude-skills/SKILL_PIPELINE.md at main - GitHub" (https://github.com/alirezarezvani/claude-skills/blob/main/SKILL_PIPELINE.md, transcript synced 2026-07-28)
  - "GitHub - tobi/qmd: mini cli search engine for your docs, knowledge bases, meeting notes, whatever. Tracking current sota approaches while being all local" (https://github.com/tobi/qmd, transcript synced 2026-07-28)
  - "iamrajiv/claude-code-hook-templates - GitHub" (https://github.com/iamrajiv/claude-code-hook-templates, transcript synced 2026-07-28)
  - "GitHub - YishenTu/claudian: An Obsidian plugin that embeds Claude Code as an AI collaborator in your vault" (https://github.com/YishenTu/claudian, transcript synced 2026-07-28)
  - "ballred/obsidian-claude-pkm: A complete starter kit for an Obsidian + Claude Code personal knowledge management system. - GitHub" (https://github.com/ballred/obsidian-claude-pkm, transcript synced 2026-07-28)
  - "Skill auto-triggering: recall=0% in headless mode (claude -p) regardless of description content #32184 - GitHub" (https://github.com/anthropics/claude-code/issues/32184, transcript synced 2026-07-28)
provenance:
  chain:
    - level: concept
      id: claude-code-external-integration-patterns
    - level: notebook
      id: 55c988d8-818d-4ed9-b08b-12d6c697ff5f
      title: Claude Code and QMD: Persistent Knowledge Architecture
      url: https://notebooklm.google.com/notebook/55c988d8-818d-4ed9-b08b-12d6c697ff5f
    - level: cluster
      id: 2
      name: github-https-claude
    - level: source_url
      url: https://github.com/heyitsnoah/claudesidian
      title: heyitsnoah/claudesidian - GitHub
    - level: source_url
      url: https://github.com/anthropics/claude-plugins-official/blob/main/plugins/skill-creator/skills/skill-creator/SKILL.md
      title: Skill Creator - anthropics/claude-plugins-official - GitHub
    - level: source_url
      url: https://github.com/alirezarezvani/claude-skills/blob/main/SKILL_PIPELINE.md
      title: claude-skills/SKILL_PIPELINE.md at main - GitHub
    - level: source_url
      url: https://github.com/tobi/qmd
      title: GitHub - tobi/qmd: mini cli search engine for your docs, knowledge bases, meeting notes, whatever. Tracking current sota approaches while being all local
    - level: source_url
      url: https://github.com/iamrajiv/claude-code-hook-templates
      title: iamrajiv/claude-code-hook-templates - GitHub
    - level: source_url
      url: https://github.com/YishenTu/claudian
      title: GitHub - YishenTu/claudian: An Obsidian plugin that embeds Claude Code as an AI collaborator in your vault
    - level: source_url
      url: https://github.com/ballred/obsidian-claude-pkm
      title: ballred/obsidian-claude-pkm: A complete starter kit for an Obsidian + Claude Code personal knowledge management system. - GitHub
    - level: source_url
      url: https://github.com/anthropics/claude-code/issues/32184
      title: Skill auto-triggering: recall=0% in headless mode (claude -p) regardless of description content #32184 - GitHub
relations:
  - target: wiki/concepts/claude-code-desktop-mode.md
    type: related
  - target: wiki/concepts/claude-code-skill-system.md
    type: related
  - target: wiki/concepts/obsidian-plugin-development.md
    type: related
---

# Claude Code External Integration Patterns

## Decision context

**Definition:** GitHub-hosted projects demonstrating how Claude Code integrates with external tools and platforms, including Obsidian plugins, skill creation pipelines, and hook template systems for extending AI-assisted development workflows.

Synthesized from **8 contributing transcripts** in NotebookLM notebook *Claude Code and QMD: Persistent Knowledge Architecture*, clustered into the "github-https-claude" sub-topic. Each claim below cites the specific transcript (source_id + title) that supports it; the frontmatter provenance chain carries the full concept → notebook → cluster → source URL hops.

**Why this matters:** concepts synced from NotebookLM carry provenance back to the source material (notebook → cluster → original URL when invoked via `--from-clusters`). A reader can verify any claim by following the provenance chain in the frontmatter.

## Operational details

- Obsidian plugins like claudian embed Claude Code as an AI collaborator within vaults, enabling in-context document interaction
- Skill creator plugins from anthropics/claude-plugins-official provide templates for defining reusable AI task patterns
- Hook template repositories offer patterns for extending Claude Code behavior at key interaction points
- Personal knowledge management starter kits combine Obsidian with Claude Code for AI-augmented note-taking and retrieval
- A documented issue shows that skill auto-triggering has zero recall in headless mode (claude -p), regardless of skill description content
- Search engine integrations like qmd provide local CLI-based retrieval for knowledge bases, potentially usable with Claude Code context
- SKILL_PIPELINE.md defines workflow patterns for chaining multiple skill definitions together
- These integrations primarily target the desktop mode rather than headless execution environments

## Verifiable values

| Name | Value |
|---|---|
| Headless mode skill recall | `0%` |
| Integration platforms documented | `5+ (Obsidian, skill pipelines, hook templates, CLI search, PKM systems)` |
| Skill format documented | `SKILL.md files with YAML frontmatter` |

## Related concepts

- claude-code-desktop-mode — Claude Code Desktop Mode
- claude-code-skill-system — Claude Code Skill System
- obsidian-plugin-development — Obsidian Plugin Development
- ai-assisted-personal-knowledge-management — AI-Assisted Personal Knowledge Management

## Citations (from contributing transcripts)

- **Claim:** A GitHub issue documents that skill auto-triggering has zero recall in headless mode regardless of description content
  - Source: Skill auto-triggering: recall=0% in headless mode (claude -p) regardless of description content #32184 - GitHub (`d7b3c464-b1e4-4e5e-8ff5-12b27fa57a41`)
  - Context: Skill auto-triggering: recall=0% in headless mode (claude -p) regardless of description content
- **Claim:** claudian is an Obsidian plugin that embeds Claude Code as an AI collaborator in the vault
  - Source: GitHub - YishenTu/claudian: An Obsidian plugin that embeds Claude Code as an AI collaborator in your vault (`7cc9c05f-5b72-49ca-a660-97a1885842dc`)
  - Context: An Obsidian plugin that embeds Claude Code as an AI collaborator in your vault
- **Claim:** obsidian-claude-pkm provides a starter kit combining Obsidian with Claude Code for personal knowledge management
  - Source: ballred/obsidian-claude-pkm: A complete starter kit for an Obsidian + Claude Code personal knowledge management system. - GitHub (`bf89dca2-1542-479b-bd55-dafec872e3a4`)
  - Context: A complete starter kit for an Obsidian + Claude Code personal knowledge management system
- **Claim:** claude-plugins-official contains skill-creator plugins for defining reusable AI task patterns
  - Source: Skill Creator - anthropics/claude-plugins-official - GitHub (`5ea09f33-edb7-4f4d-891e-de6723f75e1b`)
  - Context: claude-plugins-official/plugins/skill-creator/skills/skill-creator/SKILL.md
- **Claim:** Hook templates repository provides patterns for extending Claude Code
  - Source: iamrajiv/claude-code-hook-templates - GitHub (`6e5fabe1-1c35-46b3-9436-451a6e5bf26c`)
  - Context: claude-code-hook-templates
- **Claim:** qmd is a local CLI search engine that tracks current approaches while being all local
  - Source: GitHub - tobi/qmd: mini cli search engine for your docs, knowledge bases, meeting notes, whatever. Tracking current sota approaches while being all local (`688b62f1-d9fe-4f57-ae8e-5131450133bb`)
  - Context: mini cli search engine for your docs, knowledge bases, meeting notes, whatever
- **Claim:** SKILL_PIPELINE.md defines workflow patterns for chaining skill definitions
  - Source: claude-skills/SKILL_PIPELINE.md at main - GitHub (`6419d08b-cfef-4d76-a3ff-8d73a3e4f59d`)
  - Context: SKILL_PIPELINE.md

## Receipts

Source-derived concept: all claims in this page originate from
transcripts in NotebookLM notebook `55c988d8-818d-4ed9-b08b-12d6c697ff5f`
(cluster `github-https-claude`). No claims are made
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
