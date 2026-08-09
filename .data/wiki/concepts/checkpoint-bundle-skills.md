---
title: "Checkpoint Bundle Skills"
created: 2026-08-09
source: nlm-sync-2026-08-09
tags: [nlm-synced, reference, checkpoint]
summary: >
  A suite of utility skills for managing project checkpoints stored in P:/.claude/checkpoints/, providing listing, comparison, deletion-with-recovery, and restoration capabilities. Each skill is a single-file SKILL.md document invoked via a slash command, sharing a trash-based recovery model for safe 
agent: grok
host: both
cognitive_load: 2
verification: single-source-verified
sources:
  - "NotebookLM notebook 16dac687-5ab6-4bf4-8330-632b0e92d852" (Software Quality Assurance (SQA), synced 2026-08-09)
  - "NotebookLM source 6f3fa10a-0f71-47df-9be8-b645b626bacb" (review_bundle_checkpoint-delete_20260326.md, synced 2026-08-09)
  - "NotebookLM source a3941493-cc23-4e60-81d1-3ffdd01d05ff" (review_bundle_checkpoint-diff_20260326.md, synced 2026-08-09)
  - "NotebookLM source bd2c3d94-dc16-45c7-a5c5-1534f5005b1f" (review_bundle_checkpoint-list_20260326.md, synced 2026-08-09)
  - "NotebookLM source e65eb07d-b736-4718-8a07-848cd99dbfda" (review_bundle_checkpoint-restore_20260326.md, synced 2026-08-09)
provenance:
  chain:
    - level: concept
      id: checkpoint-bundle-skills
    - level: notebook
      id: 16dac687-5ab6-4bf4-8330-632b0e92d852
      title: Software Quality Assurance (SQA)
      url: https://notebooklm.google.com/notebook/16dac687-5ab6-4bf4-8330-632b0e92d852
    - level: cluster
      id: 3
      name: checkpoint-bundle-skill
relations:
  - target: wiki/concepts//checkpoint-core-management.md
    type: related
  - target: wiki/concepts/trash-recovery-system.md
    type: related
  - target: wiki/concepts/checkpoint-metadata-format.md
    type: related
---

# Checkpoint Bundle Skills

## Decision context

**Definition:** A suite of utility skills for managing project checkpoints stored in P:/.claude/checkpoints/, providing listing, comparison, deletion-with-recovery, and restoration capabilities. Each skill is a single-file SKILL.md document invoked via a slash command, sharing a trash-based recovery model for safe destructive operations.

Synthesized from **4 contributing transcripts** in NotebookLM notebook *Software Quality Assurance (SQA)*, clustered into the "checkpoint-bundle-skill" sub-topic. Each claim below cites the specific transcript (source_id + title) that supports it; the frontmatter provenance chain carries the full concept → notebook → cluster → source URL hops.

**Why this matters:** concepts synced from NotebookLM carry provenance back to the source material (notebook → cluster → original URL when invoked via `--from-clusters`). A reader can verify any claim by following the provenance chain in the frontmatter.

## Operational details

- The bundle comprises four skills: /checkpoint-list, /checkpoint-diff, /checkpoint-delete, and /checkpoint-restore, each documented as a standalone SKILL.md file under P:/.claude/skills/.
- /checkpoint-list scans the checkpoints directory, reads metadata from each file, computes age from timestamps, and displays age, commit info, and metadata; it also supports --cleanup to remove old/invalid checkpoints and --validate to verify integrity.
- /checkpoint-diff identifies two checkpoints, reads their metadata, extracts commits with change detection, compares file counts and modified file lists, then outputs a structured diff covering commits, types, messages, files, and a validation checklist.
- /checkpoint-delete identifies a checkpoint by ID or pattern, verifies it exists in the checkpoints directory, then moves the file to ~/.claude/trash/ while preserving metadata so /checkpoint-restore can recover it.
- /checkpoint-restore supports --list to enumerate items in ~/.claude/trash/, or accepts a checkpoint ID, verifies its presence in trash, reads metadata, and restores the checkpoint to the active checkpoints directory.
- All four skills share an evidence-first approach: list/diff must read directory contents rather than speculate; delete/restore must verify existence in checkpoints or trash before acting.
- Safety rules across the suite prohibit permanently deleting without moving to trash first, bypassing the trash system, deleting without user confirmation, and restoring without verifying the checkpoint is actually in trash.
- Example identifiers used in usage docs include ckpt_20260107_120000 and patterns like ckpt_20260107_*; /checkpoint-diff also accepts a --latest flag (e.g. --latest manual_20260107_120000).
- All skills operate in single-agent execution mode on Windows 11 Pro using Bash, and share the same Category rating of 'utility' with SQA Relevance rated LOW.

## Verifiable values

| Name | Value |
|---|---|
| checkpoint storage directory | `P:/.claude/checkpoints/` |
| trash recovery directory | `~/.claude/trash/` |
| checkpoint-list SKILL.md length | `65 lines` |
| checkpoint-diff SKILL.md length | `71 lines` |
| checkpoint-restore SKILL.md length | `67 lines` |
| checkpoint-delete SKILL.md length | `81 lines` |
| files per skill | `1 (SKILL.md only)` |
| execution mode | `single-agent` |
| OS environment | `Windows 11 Pro` |
| shell environment | `Bash` |
| skill category | `utility` |
| test coverage rating | `N/A (no test files)` |
| checkpoint-delete safety rating | `EXCELLENT (trash-based deletion)` |

## Related concepts

- [[/checkpoint-core-management]] — /checkpoint core management
- [[trash-recovery-system]] — Trash recovery system
- [[checkpoint-metadata-format]] — Checkpoint metadata format
- [[evidence-first-validation-pattern]] — Evidence-first validation pattern

## Citations (from contributing transcripts)

- **Claim:** Checkpoint deletion moves files to a trash recovery directory rather than permanently deleting them.
  - Source: review_bundle_checkpoint-delete_20260326.md (`6f3fa10a-0f71-47df-9be8-b645b626bacb`)
  - Context: Safely delete a checkpoint using the trash recovery system
- **Claim:** Checkpoints are stored in P:/.claude/checkpoints/ and trash entries in ~/.claude/trash/.
  - Source: review_bundle_checkpoint-delete_20260326.md (`6f3fa10a-0f71-47df-9be8-b645b626bacb`)
  - Context: Checkpoints stored in P:/.claude/checkpoints/ Trash recovery in ~/.claude/trash/
- **Claim:** /checkpoint-list reads metadata and supports --cleanup and --validate flags.
  - Source: review_bundle_checkpoint-list_20260326.md (`bd2c3d94-dc16-45c7-a5c5-1534f5005b1f`)
  - Context: Scan P:/.claude/checkpoints/ directory for checkpoint files Read metadata from each checkpoint Calculate age based on timestamp Display list with age, commit info, and metadata If --cleanup flag: remove old/invalid checkpoints If --validate flag: verify checkpoint integrity
- **Claim:** /checkpoint-diff reads two checkpoint files and outputs commits, types, messages, modified files, and a validation checklist.
  - Source: review_bundle_checkpoint-diff_20260326.md (`a3941493-cc23-4e60-81d1-3ffdd01d05ff`)
  - Context: Identify two checkpoints to compare Read metadata from both checkpoint files Extract commits with change detection Compare file counts and modified file lists Display structured diff showing commits, types, messages, files
- **Claim:** /checkpoint-restore supports --list to show trashed checkpoints and restores by checkpoint ID.
  - Source: review_bundle_checkpoint-restore_20260326.md (`e65eb07d-b736-4718-8a07-848cd99dbfda`)
  - Context: If --list: show all checkpoints in trash If checkpoint ID provided: verify it exists in trash Read metadata from trash checkpoint Restore checkpoint to active checkpoints directory
- **Claim:** Each skill ships as a single SKILL.md file.
  - Source: review_bundle_checkpoint-list_20260326.md (`bd2c3d94-dc16-45c7-a5c5-1534f5005b1f`)
  - Context: File Count: 1 file (SKILL.md only)
- **Claim:** All skills operate as single-agent utilities on Windows 11 Pro with Bash.
  - Source: review_bundle_checkpoint-diff_20260326.md (`a3941493-cc23-4e60-81d1-3ffdd01d05ff`)
  - Context: OS: Windows 11 Pro Shell: Bash Primary Language: Markdown Execution Mode: single-agent
- **Claim:** Usage examples include named IDs like ckpt_20260107_120000 and a --latest flag for diff.
  - Source: review_bundle_checkpoint-delete_20260326.md (`6f3fa10a-0f71-47df-9be8-b645b626bacb`)
  - Context: /checkpoint-delete ckpt_20260107_120000 /checkpoint-delete ckpt_20260107_*
- **Claim:** Validation rules forbid speculation and require reading directories or verifying existence.
  - Source: review_bundle_checkpoint-list_20260326.md (`bd2c3d94-dc16-45c7-a5c5-1534f5005b1f`)
  - Context: Do NOT list checkpoints without reading directory Do NOT assume checkpoint format without verification
- **Claim:** Delete and restore prohibit bypassing the trash system or restoring without verifying trash presence.
  - Source: review_bundle_checkpoint-restore_20260326.md (`e65eb07d-b736-4718-8a07-848cd99dbfda`)
  - Context: Do NOT restore without verifying checkpoint exists in trash Do NOT assume trash location without checking

## Receipts

Source-derived concept: all claims in this page originate from
transcripts in NotebookLM notebook `16dac687-5ab6-4bf4-8330-632b0e92d852`
(cluster `checkpoint-bundle-skill`). No claims are made
about local workspace implementation. Trigger words like
'mechanism', 'scanner', 'gate', 'hook', 'because' refer to concepts
discussed in the source videos, not to local code behavior.
Implementation path: wiki-yt/scripts/synthesize_subtopics.py
(LLM synthesis from transcripts — no local code inspected).

## What this means for our workspace

Synced from NotebookLM. Provenance chain (concept → notebook → cluster → URL) is in frontmatter; follow it back to the source material.

## Falsifier

If a re-sync of the source notebook produces a different definition or different values, this page should be updated (or marked as superseded). The sync manifest at `P:/.data/wiki/_state/nlm-sync-manifest.json` records when this page was last regenerated.

## Sources

- NotebookLM notebook [Software Quality Assurance (SQA)](https://notebooklm.google.com/notebook/16dac687-5ab6-4bf4-8330-632b0e92d852)
- Studio artifacts: Report (concept extraction) + Data-Table (tabular facts)

## Auto-related

- [[skill-catalog]]
- [[skill-graph]]
- [[agent-config-directory-taxonomy]]
- [[claude-code-skills-and-mcp-integration]]
- [[claude-code-hooks-system]]

