---
title: "Claude Code Write Restriction Pattern"
created: 2026-07-28
source: nlm-sync-2026-07-28
tags: [nlm-synced, reference, claude]
summary: >
  A workflow friction pattern in Claude Code environments where certain operations are blocked from writing directly to the project root directory, requiring use of designated subdirectories instead.
agent: grok
host: both
cognitive_load: 2
verification: single-source-verified
sources:
  - "NotebookLM notebook 2c9cc8e9-f1c4-4724-a83b-62412d20846c" (Claude Code - Workflow and Logic Inefficiencies, synced 2026-07-28)
  - "NotebookLM source 786d90b1-94da-4e95-8161-cecc066f132b" (inefficient chs 0.txt, synced 2026-07-28)
  - "NotebookLM source 7f92ba8f-473a-443b-9511-b6b6bcb2fc95" (inefficient debug 0.txt, synced 2026-07-28)
  - "NotebookLM source 8f275dc1-2854-42b8-885a-13dfd8239a4e" (inefficient main 0.txt, synced 2026-07-28)
  - "NotebookLM source b0ea4622-3918-477b-942a-1dfa34945965" (inefficient commitment 0.txt, synced 2026-07-28)
provenance:
  chain:
    - level: concept
      id: claude-code-write-restriction-pattern
    - level: notebook
      id: 2c9cc8e9-f1c4-4724-a83b-62412d20846c
      title: Claude Code - Workflow and Logic Inefficiencies
      url: https://notebooklm.google.com/notebook/2c9cc8e9-f1c4-4724-a83b-62412d20846c
    - level: cluster
      id: 8
      name: claude-inefficient-read
relations:
  - target: wiki/concepts/pretooluse-hook-validation.md
    type: related
  - target: wiki/concepts/claude-code-workflow-friction.md
    type: related
  - target: wiki/concepts/directory-path-restrictions.md
    type: related
---

# Claude Code Write Restriction Pattern

## Decision context

**Definition:** A workflow friction pattern in Claude Code environments where certain operations are blocked from writing directly to the project root directory, requiring use of designated subdirectories instead.

Synthesized from **4 contributing transcripts** in NotebookLM notebook *Claude Code - Workflow and Logic Inefficiencies*, clustered into the "claude-inefficient-read" sub-topic. Each claim below cites the specific transcript (source_id + title) that supports it; the frontmatter provenance chain carries the full concept → notebook → cluster → source URL hops.

**Why this matters:** concepts synced from NotebookLM carry provenance back to the source material (notebook → cluster → original URL when invoked via `--from-clusters`). A reader can verify any claim by following the provenance chain in the frontmatter.

## Operational details

- Operations that attempt to write to the project root (e.g., P:\) receive blocking errors directing users to appropriate subdirectories such as .claude/, docs/, or packages/
- The write restriction is enforced at the hook level, returning blocking status when directory validation fails
- Bash operations with mkdir commands using the project root path trigger the restriction even when using absolute path forms like /c/Users/
- This pattern appears consistently across different Claude Code versions (v2.1.85 and v2.1.86)
- The restriction is part of a PreToolUse hook pattern that validates directory paths before command execution

## Verifiable values

| Name | Value |
|---|---|
| Claude Code version affected | `v2.1.85 and v2.1.86` |
| permitted directories | `.claude/, docs/, packages/` |
| blocked directory | `project root (e.g., P:\)` |

## Related concepts

- [[pretooluse-hook-validation]] — PreToolUse hook validation
- [[claude-code-workflow-friction]] — Claude Code workflow friction
- [[directory-path-restrictions]] — Directory path restrictions

## Citations (from contributing transcripts)

- **Claim:** Write operations to project root are blocked with guidance to use subdirectories
  - Source: inefficient debug 0.txt (`7f92ba8f-473a-443b-9511-b6b6bcb2fc95`)
  - Context: Error: Cannot write to project root: P:\c error Use appropriate subdirectories (.claude/, docs/, packages/, etc.)
- **Claim:** The restriction is enforced via PreToolUse hook returning blocking status
  - Source: inefficient debug 0.txt (`7f92ba8f-473a-443b-9511-b6b6bcb2fc95`)
  - Context: PreToolUse:Bash hook returned blocking
- **Claim:** The write restriction applies even to absolute path forms of the project root
  - Source: inefficient main 0.txt (`8f275dc1-2854-42b8-885a-13dfd8239a4e`)
  - Context: Error: Cannot write to project root: P:-p Use appropriate subdirectories

## Receipts

Source-derived concept: all claims in this page originate from
transcripts in NotebookLM notebook `2c9cc8e9-f1c4-4724-a83b-62412d20846c`
(cluster `claude-inefficient-read`). No claims are made
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

- NotebookLM notebook [Claude Code - Workflow and Logic Inefficiencies](https://notebooklm.google.com/notebook/2c9cc8e9-f1c4-4724-a83b-62412d20846c)
- Studio artifacts: Report (concept extraction) + Data-Table (tabular facts)
