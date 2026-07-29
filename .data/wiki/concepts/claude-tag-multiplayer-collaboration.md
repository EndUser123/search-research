---
title: "Claude Tag Multiplayer Collaboration"
created: 2026-07-27
source: nlm-sync-2026-07-27
tags: [nlm-synced, reference, claude]
summary: >
  Claude Tag is a team-based interaction method for Claude AI integrated into collaboration platforms like Slack, enabling multiple team members to engage with AI assistance simultaneously through a tagging mechanism that maintains contextual awareness across group threads and shared workspaces.
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
      id: claude-tag-multiplayer-collaboration
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
  - target: wiki/concepts/ai-collaboration-patterns.md
    type: related
---

# Claude Tag Multiplayer Collaboration

## Decision context

**Definition:** Claude Tag is a team-based interaction method for Claude AI integrated into collaboration platforms like Slack, enabling multiple team members to engage with AI assistance simultaneously through a tagging mechanism that maintains contextual awareness across group threads and shared workspaces.

Synthesized from **8 contributing transcripts** in NotebookLM notebook *WL-Pilot: Claude Skills & Code*, clustered into the "claude-anthropic-work" sub-topic. Each claim below cites the specific transcript (source_id + title) that supports it; the frontmatter provenance chain carries the full concept → notebook → cluster → source URL hops.

**Why this matters:** concepts synced from NotebookLM carry provenance back to the source material (notebook → cluster → original URL when invoked via `--from-clusters`). A reader can verify any claim by following the provenance chain in the frontmatter.

## Operational details

- Tagging at Claude opens a shared thread where team members can ask questions and receive AI responses visible to the entire group
- Claude processes group threads in real time, reacting to product decisions and tracking team communications without requiring individual queries
- The AI opens pull requests and lands code changes when tagged by team members, maintaining awareness of feature context and codebase locations
- Claude builds memory over time by tracking work progress and understands downstream impacts, such as recognizing when a pushed change affects launch marketing
- At Anthropic, the product team uses Claude Tag for approximately 65% of their total Claude interactions across the department
- Tagging operations are designed as multiplayer interactions where one team member tags and Claude responds within the shared group context
- The approach is positioned as an evolution of Claude Code that makes the model more proactive and better suited for full team environments

## Verifiable values

| Name | Value |
|---|---|
| Claude Tag usage at Anthropic | `65% of product pull requests` |

## Related concepts

- [[claude-code]] — Claude Code
- [[claude-fable]] — Claude Fable
- [[ai-collaboration-patterns]] — AI Collaboration Patterns

## Citations (from contributing transcripts)

- **Claim:** Claude Tag usage rate is 65% of product pull requests at Anthropic
  - Source: Tag Claude in, right where you already work (`0f0f912d-c6f4-4233-b5f2-ee00754b54bf`)
  - Context: And across Anthropic, Claude Tag opens 65% of our product pull requests.
- **Claim:** Claude Tag enables multiplayer team collaboration in Slack
  - Source: Anthropic Just Changed How We Work Forever.. (Claude Tag) (`4d6febe1-261a-4731-872f-65f07b2b8fbf`)
  - Context: Anthropic just released something called Claude Tag and this is basically a way to use Claude directly inside of Slack with your entire team think of this like a multiplayer way to interact with Claude inside of Slack
- **Claim:** Claude processes group threads and reacts to product decisions in real time
  - Source: Tag Claude in, right where you already work (`0f0f912d-c6f4-4233-b5f2-ee00754b54bf`)
  - Context: Nadia tags Claude, then Claude keeps up with the group thread, reacting to product decisions made in real time.
- **Claim:** Claude Tag is positioned as an evolution of Claude Code
  - Source: Anthropic Just Changed How We Work Forever.. (Claude Tag) (`4d6febe1-261a-4731-872f-65f07b2b8fbf`)
  - Context: We see claude tag as the beginning of an evolution of claude code and makes the model even more proactive and works better with a full team.

## Receipts

Source-derived concept: all claims in this page originate from
transcripts in NotebookLM notebook `23bf4931-d0cb-4550-9d11-f9b38843254a`
(cluster `claude-anthropic-work`). No claims are made
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

- NotebookLM notebook [WL-Pilot: Claude Skills & Code](https://notebooklm.google.com/notebook/23bf4931-d0cb-4550-9d11-f9b38843254a)
- Studio artifacts: Report (concept extraction) + Data-Table (tabular facts)
