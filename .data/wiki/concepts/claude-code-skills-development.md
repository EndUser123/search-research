---
title: "Claude Code Skills Development"
created: 2026-07-28
source: nlm-sync-2026-07-28
tags: [nlm-synced, reference, https]
summary: >
  Claude Code Skills are reusable, configurable prompt packages that extend Claude Code's capabilities for specialized tasks, functioning as persistent prompt libraries with defined frontmatter metadata that differentiate them from ephemeral slash commands and project-level CLAUDE.md files.
agent: grok
host: both
cognitive_load: 2
verification: single-source-verified
sources:
  - "NotebookLM notebook 8138a528-f5c2-4ee4-b5a9-f3359f48f0dc" ([INGESTED] - Mastering Claude Skills, synced 2026-07-28)
  - "I've been building Claude Skills for a month. Here's what I learned the hard way. - Reddit" (https://www.reddit.com/r/ClaudeAI/comments/1rklufk/ive_been_building_claude_skills_for_a_month_heres/, transcript synced 2026-07-28)
  - "Essential Claude Code Skills and Commands | (think) - Bozhidar Batsov" (https://batsov.com/articles/2026/03/11/essential-claude-code-skills-and-commands/, transcript synced 2026-07-28)
  - "Gap Analysis | Business and Management | Research Starters - EBSCO" (https://www.ebsco.com/research-starters/business-and-management/gap-analysis, transcript synced 2026-07-28)
  - "PokerSkill: Expert-Level Poker Play from Pure Language Models | OpenReview" (https://openreview.net/forum?id=PraRhQLyRF, transcript synced 2026-07-28)
  - "Claude Code Skills: The Complete Guide (2026) - Vanja Petreski" (https://vanja.io/claude-code-skills-guide/, transcript synced 2026-07-28)
  - "Interleaved Thinking Relaxes Documented API Constraint : r/Anthropic - Reddit" (https://www.reddit.com/r/Anthropic/comments/1qye2nr/interleaved_thinking_relaxes_documented_api/, transcript synced 2026-07-28)
  - "Best Claude Code Skills to Try in 2026 - Firecrawl" (https://www.firecrawl.dev/blog/best-claude-code-skills, transcript synced 2026-07-28)
  - "Content Gap Analysis 2026: 10 Tips For AI Search - Yotpo" (https://www.yotpo.com/blog/modern-content-gap-analysis/, transcript synced 2026-07-28)
  - "How to Set Up Claude Skills in <15 Minutes (for Non-Technical People) : r/ClaudeAI - Reddit" (https://www.reddit.com/r/ClaudeAI/comments/1onjxs9/how_to_set_up_claude_skills_in_15_minutes_for/, transcript synced 2026-07-28)
  - "Introduction | Getting to Outcomes® | RAND" (https://www.rand.org/pubs/tools/TL259/introduction.html, transcript synced 2026-07-28)
  - "How To Use LLMs for Competitive Research and Gap Analysis - Moz" (https://moz.com/blog/llm-competitive-research-gap-analysis, transcript synced 2026-07-28)
  - "A simple guide to gap analysis | MiroBlog" (https://miro.com/blog/gap-analysis/, transcript synced 2026-07-28)
  - "Claude Skill for Summarizing Electrical Engineering Technical Documents - Reddit" (https://www.reddit.com/r/ClaudeAI/comments/1sc42wa/claude_skill_for_summarizing_electrical/, transcript synced 2026-07-28)
provenance:
  chain:
    - level: concept
      id: claude-code-skills-development
    - level: notebook
      id: 8138a528-f5c2-4ee4-b5a9-f3359f48f0dc
      title: [INGESTED] - Mastering Claude Skills
      url: https://notebooklm.google.com/notebook/8138a528-f5c2-4ee4-b5a9-f3359f48f0dc
    - level: cluster
      id: 3
      name: https-reddit-claude
    - level: source_url
      url: https://www.reddit.com/r/ClaudeAI/comments/1rklufk/ive_been_building_claude_skills_for_a_month_heres/
      title: I've been building Claude Skills for a month. Here's what I learned the hard way. - Reddit
    - level: source_url
      url: https://batsov.com/articles/2026/03/11/essential-claude-code-skills-and-commands/
      title: Essential Claude Code Skills and Commands | (think) - Bozhidar Batsov
    - level: source_url
      url: https://www.ebsco.com/research-starters/business-and-management/gap-analysis
      title: Gap Analysis | Business and Management | Research Starters - EBSCO
    - level: source_url
      url: https://openreview.net/forum?id=PraRhQLyRF
      title: PokerSkill: Expert-Level Poker Play from Pure Language Models | OpenReview
    - level: source_url
      url: https://vanja.io/claude-code-skills-guide/
      title: Claude Code Skills: The Complete Guide (2026) - Vanja Petreski
    - level: source_url
      url: https://www.reddit.com/r/Anthropic/comments/1qye2nr/interleaved_thinking_relaxes_documented_api/
      title: Interleaved Thinking Relaxes Documented API Constraint : r/Anthropic - Reddit
    - level: source_url
      url: https://www.firecrawl.dev/blog/best-claude-code-skills
      title: Best Claude Code Skills to Try in 2026 - Firecrawl
    - level: source_url
      url: https://www.yotpo.com/blog/modern-content-gap-analysis/
      title: Content Gap Analysis 2026: 10 Tips For AI Search - Yotpo
    - level: source_url
      url: https://www.reddit.com/r/ClaudeAI/comments/1onjxs9/how_to_set_up_claude_skills_in_15_minutes_for/
      title: How to Set Up Claude Skills in <15 Minutes (for Non-Technical People) : r/ClaudeAI - Reddit
    - level: source_url
      url: https://www.rand.org/pubs/tools/TL259/introduction.html
      title: Introduction | Getting to Outcomes® | RAND
    - level: source_url
      url: https://moz.com/blog/llm-competitive-research-gap-analysis
      title: How To Use LLMs for Competitive Research and Gap Analysis - Moz
    - level: source_url
      url: https://miro.com/blog/gap-analysis/
      title: A simple guide to gap analysis | MiroBlog
    - level: source_url
      url: https://www.reddit.com/r/ClaudeAI/comments/1sc42wa/claude_skill_for_summarizing_electrical/
      title: Claude Skill for Summarizing Electrical Engineering Technical Documents - Reddit
relations:
  - target: wiki/concepts/claude-code-cli.md
    type: related
  - target: wiki/concepts/slash-commands.md
    type: related
  - target: wiki/concepts/claude.md.md
    type: related
---

# Claude Code Skills Development

## Decision context

**Definition:** Claude Code Skills are reusable, configurable prompt packages that extend Claude Code's capabilities for specialized tasks, functioning as persistent prompt libraries with defined frontmatter metadata that differentiate them from ephemeral slash commands and project-level CLAUDE.md files.

Synthesized from **13 contributing transcripts** in NotebookLM notebook *[INGESTED] - Mastering Claude Skills*, clustered into the "https-reddit-claude" sub-topic. Each claim below cites the specific transcript (source_id + title) that supports it; the frontmatter provenance chain carries the full concept → notebook → cluster → source URL hops.

**Why this matters:** concepts synced from NotebookLM carry provenance back to the source material (notebook → cluster → original URL when invoked via `--from-clusters`). A reader can verify any claim by following the provenance chain in the frontmatter.

## Operational details

- Skills are defined through frontmatter fields within markdown files, specifying parameters such as description, invocation name, and argument schema
- Skills persist across sessions unlike slash commands which are ephemeral and session-scoped
- Skills support configurable invocation modes including automatic detection, slash-style activation, and @mention patterns
- The skills approach differs from CLAUDE.md by enabling reusable, shareable configurations rather than project-specific instructions
- A skills file contains both metadata (frontmatter) and the actual prompt content that guides Claude's behavior
- Skills can be invoked through multiple entry points depending on how they are configured in the frontmatter
- Community skills exist for specialized domains such as summarizing technical documents and poker strategy analysis
- Skills development involves iterative testing and refinement based on actual usage patterns
- Best practices include organizing skill prompts clearly and defining appropriate scope for each skill's functionality

## Verifiable values

| Name | Value |
|---|---|
| skill file format | `markdown with YAML frontmatter` |
| frontmatter fields | `description, invocation name, arguments schema` |
| invocation modes | `automatic, slash, @mention` |

## Related concepts

- [[claude-code-cli]] — Claude Code CLI
- [[slash-commands]] — Slash Commands
- [[claude.md]] — CLAUDE.md
- [[prompt-engineering]] — Prompt Engineering

## Citations (from contributing transcripts)

- **Claim:** Skills are configured via frontmatter fields that define metadata and invocation parameters
  - Source: Claude Code Skills: The Complete Guide (2026) - Vanja Petreski (`59cfc2ee-3d05-4e8d-88bd-6bb5d086d372`)
  - Context: Skills are reus...
- **Claim:** Skills persist across sessions while slash commands are ephemeral and session-scoped
  - Source: Essential Claude Code Skills and Commands | (think) - Bozhidar Batsov (`0694a90f-b624-4843-ad5d-48785a71381d`)
  - Context: Skills vs. Slash Commands: What's the Difference?
- **Claim:** Skills can be created for specialized domains like technical document summarization
  - Source: Claude Skill for Summarizing Electrical Engineering Technical Documents - Reddit (`e6da9131-4daf-4a1e-a8e7-c78b65f1f215`)
  - Context: Claude Skill for Summarizing Electrical Engineering Technical Documents
- **Claim:** Skills represent reusable prompt configurations distinct from project-level CLAUDE.md files
  - Source: I've been building Claude Skills for a month. Here's what I learned the hard way. - Reddit (`02743583-6109-454a-9f01-0977bbbec26f`)
  - Context: I've been building Claude Skills for a month. Here's what I learned the hard way.
- **Claim:** Non-technical users can set up skills in under 15 minutes using the configuration approach
  - Source: How to Set Up Claude Skills in <15 Minutes (for Non-Technical People) : r/ClaudeAI - Reddit (`c71caf8b-f2bf-46d8-b0f5-6bec627dec05`)
  - Context: How to Set Up Claude Skills in <15 Minutes (for Non-Technical People)

## Receipts

Source-derived concept: all claims in this page originate from
transcripts in NotebookLM notebook `8138a528-f5c2-4ee4-b5a9-f3359f48f0dc`
(cluster `https-reddit-claude`). No claims are made
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
