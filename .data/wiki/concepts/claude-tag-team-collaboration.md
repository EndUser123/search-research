---
title: "Claude Tag Team Collaboration"
created: 2026-07-27
source: nlm-sync-2026-07-27
tags: [nlm-synced, reference, claude]
summary: >
  Claude Tag is a feature that enables Claude to collaborate directly with teams within existing work environments like Slack, functioning as a multiplayer AI assistant that can participate in group discussions, open and land pull requests, and maintain contextual memory across team interactions.
agent: grok
host: both
cognitive_load: 2
verification: single-source-verified
sources:
  - "NotebookLM notebook 23bf4931-d0cb-4550-9d11-f9b38843254a" (WL-Pilot: Claude Skills & Code, synced 2026-07-27)
  - "NotebookLM source 0b91340b-c89d-4ad8-8534-04617f5baefd" (Shocking Confirmation That Liquid Water Is Two Separate Substances, synced 2026-07-27)
  - "NotebookLM source 0f0f912d-c6f4-4233-b5f2-ee00754b54bf" (Tag Claude in, right where you already work, synced 2026-07-27)
  - "NotebookLM source 4d6febe1-261a-4731-872f-65f07b2b8fbf" (Anthropic Just Changed How We Work Forever.. (Claude Tag), synced 2026-07-27)
  - "NotebookLM source 71eec985-e541-4e5a-a485-dd6c79d587dc" (Karpathy's New Move is Huge for Claude Code Users, synced 2026-07-27)
  - "NotebookLM source 9e3bb059-84f3-4393-8236-051374776613" (Stop Prompting Claude. Use Karpathy's Method Instead., synced 2026-07-27)
  - "NotebookLM source b5ac0a66-c34c-4a16-b24b-49412fda2fa0" (I Turned Claude Into the Ultimate Second Brain, synced 2026-07-27)
  - "NotebookLM source e49c4d02-efed-4e5e-9921-fee7c6d77038" (Anthropic Just Dropped a Guide for WAY Better Claude Output (copy this), synced 2026-07-27)
  - "NotebookLM source f9f8f28e-0632-4bd6-bf3a-d1467c952007" (Dario and Sam have a problem..., synced 2026-07-27)
provenance:
  chain:
    - level: concept
      id: claude-tag-team-collaboration
    - level: notebook
      id: 23bf4931-d0cb-4550-9d11-f9b38843254a
      title: WL-Pilot: Claude Skills & Code
      url: https://notebooklm.google.com/notebook/23bf4931-d0cb-4550-9d11-f9b38843254a
    - level: cluster
      id: 7
      name: claude-anthropic-work
relations:
  - target: wiki/concepts/claude-code.md
    type: related
  - target: wiki/concepts/claude-fable.md
    type: related
  - target: wiki/concepts/claude-mythos.md
    type: related
---

# Claude Tag Team Collaboration

## Decision context

**Definition:** Claude Tag is a feature that enables Claude to collaborate directly with teams within existing work environments like Slack, functioning as a multiplayer AI assistant that can participate in group discussions, open and land pull requests, and maintain contextual memory across team interactions.

Synthesized from **8 contributing transcripts** in NotebookLM notebook *WL-Pilot: Claude Skills & Code*, clustered into the "claude-anthropic-work" sub-topic. Each claim below cites the specific transcript (source_id + title) that supports it; the frontmatter provenance chain carries the full concept → notebook → cluster → source URL hops.

**Why this matters:** concepts synced from NotebookLM carry provenance back to the source material (notebook → cluster → original URL when invoked via `--from-clusters`). A reader can verify any claim by following the provenance chain in the frontmatter.

## Operational details

- Enables tagging Claude directly into team channels and conversations within Slack
- Multiplayer collaboration model where Claude participates alongside human team members in real time
- Claude can open and land pull requests, understanding codebase structure and feature context
- Maintains memory and context as work progresses across team interactions
- Claude builds context about which channels and teams have relevant information for specific tasks
- Part of Claude Code evolution described as making the model more proactive and better suited for full team workflows

## Verifiable values

| Name | Value |
|---|---|
| Adoption rate at Anthropic | `65% of product pull requests opened using Claude Tag across the entire department` |
| Duration of internal use | `most of the year (prior to public launch)` |

## Related concepts

- claude-code — Claude Code
- claude-fable — Claude Fable
- claude-mythos — Claude Mythos
- andre-karpathy-joining-anthropic — Andre Karpathy joining Anthropic

## Citations (from contributing transcripts)

- **Claim:** Claude Tag enables multiplayer collaboration directly inside Slack with entire teams
  - Source: Tag Claude in, right where you already work (`0f0f912d-c6f4-4233-b5f2-ee00754b54bf`)
  - Context: Today we're launching Claude Tag, which lets Claude collaborate right alongside your team.
- **Claim:** 65% of product pull requests are opened using Claude Tag across Anthropic
  - Source: Tag Claude in, right where you already work (`0f0f912d-c6f4-4233-b5f2-ee00754b54bf`)
  - Context: across Anthropic, Claude Tag opens 65% of our product pull requests
- **Claim:** Claude can open and land pull requests with contextual understanding
  - Source: Tag Claude in, right where you already work (`0f0f912d-c6f4-4233-b5f2-ee00754b54bf`)
  - Context: It opens the PR and it lands the change. And the cool part is that Claude knew what the feature was and where in the codebase to go.
- **Claim:** Claude Tag is described as the beginning of an evolution of Claude Code
  - Source: Anthropic Just Changed How We Work Forever.. (Claude Tag) (`4d6febe1-261a-4731-872f-65f07b2b8fbf`)
  - Context: We see claude tag as the beginning of an evolution of claude code and makes the model even more proactive and works better with a full team.

## What this means for our workspace

Synced from NotebookLM. Provenance chain (concept → notebook → cluster → URL) is in frontmatter; follow it back to the source material.

## Falsifier

If a re-sync of the source notebook produces a different definition or different values, this page should be updated (or marked as superseded). The sync manifest at `P:/.data/wiki/_state/nlm-sync-manifest.json` records when this page was last regenerated.

## Sources

- NotebookLM notebook [WL-Pilot: Claude Skills & Code](https://notebooklm.google.com/notebook/23bf4931-d0cb-4550-9d11-f9b38843254a)
- Studio artifacts: Report (concept extraction) + Data-Table (tabular facts)
