---
title: "SDLC Stop Hook Enforcement Pattern"
created: 2026-08-11
source: nlm-sync-2026-08-11
tags: [nlm-synced, reference, stop]
summary: >
  A design pattern used to prevent an agent from completing a task until specific quality gates and SDLC requirements are met. It utilizes a session-bound pointer model to evaluate state-based evidence before allowing a stop event to finalize.
agent: grok
host: both
cognitive_load: 2
verification: single-source-verified
provenance_status: complete_4_hop
sources:
  - "NotebookLM notebook 4017aa6e-35fb-426d-bc53-34620bec405e" ([INGESTED] - Claude Code Guide: Production Hooks and Agent Skills, synced 2026-08-11)
  - "NotebookLM source 03585e5b-6aa8-4960-afbf-5fb9c306740f" (go_full.md, synced 2026-08-11)
  - "NotebookLM source 36efff38-c1ca-4156-b685-1bcc2e82fca9" (cc-skills-sdlc_full.md, synced 2026-08-11)
  - "NotebookLM source 3b5367e8-bde2-4358-b2a2-efd10f099904" (go_sig.md, synced 2026-08-11)
  - "NotebookLM source 93b5c441-880d-4eef-b506-9472a5a0aee2" (cc-skills-sdlc_sig.md, synced 2026-08-11)
provenance:
  chain:
    - level: concept
      id: sdlc-stop-hook-enforcement-pattern
    - level: notebook
      id: 4017aa6e-35fb-426d-bc53-34620bec405e
      title: [INGESTED] - Claude Code Guide: Production Hooks and Agent Skills
      url: https://notebooklm.google.com/notebook/4017aa6e-35fb-426d-bc53-34620bec405e
    - level: cluster
      id: 3
      name: stop-hooks-enforce
relations:
  - target: wiki/concepts/phase-ledger.md
    type: related
  - target: wiki/concepts/pointer-based-state.md
    type: related
  - target: wiki/concepts/sdlc-hard-gate.md
    type: related
---

# SDLC Stop Hook Enforcement Pattern

## Decision context

**Definition:** A design pattern used to prevent an agent from completing a task until specific quality gates and SDLC requirements are met. It utilizes a session-bound pointer model to evaluate state-based evidence before allowing a stop event to finalize.

Synthesized from **4 contributing transcripts** in NotebookLM notebook *[INGESTED] - Claude Code Guide: Production Hooks and Agent Skills*, clustered into the "stop-hooks-enforce" sub-topic. Each claim below cites the specific transcript (source_id + title) that supports it; the frontmatter provenance chain carries the full concept → notebook → cluster → source URL hops.

**Why this matters:** concepts synced from NotebookLM carry provenance back to the source material (notebook → cluster → original URL when invoked via `--from-clusters`). A reader can verify any claim by following the provenance chain in the frontmatter.

## Operational details

- The approach relies on a session-bound pointer model where a `session_id` maps to a JSON file containing the `go_state_dir`, `run_id`, and `updated_at` timestamp.
- Stop hooks are wired directly via project settings (e.g., settings.json) and act additively to the native goal-loop evaluator rather than replacing it.
- Enforcement is typically split into two layers: a continuation gate that determines if work remains for active runs, and a hard-gate enforcer that validates SDLC compliance when a run claims completion.
- Trap prevention is handled via a `stop_hook_active` flag in the payload; if true, the hook exits silently to prevent infinite recursion loops during repeated block events.
- Stale pointer detection is enforced using a TTL (typically 6 hours); pointers older than this are treated as abandoned and the hook fails silent to avoid blocking unrelated sessions.
- Validation or audit modes can short-circuit enforcement if specific markers (like .go-validation-complete) are present in the state directory.
- The technique synthesizes an evaluation environment from pointer-resolved state rather than live environment variables to prevent tampering.
- Terminal isolation is maintained by namespacing state directories by the `terminal_id` to prevent cross-terminal contamination of enforcement state.
- The design follows a strict output contract: exit 0 for allow/fail-open paths, and exit 2 with a JSON-formatted message containing the decision and a reason for blocks.

## Verifiable values

| Name | Value |
|---|---|
| _STALE_TTL_SECONDS | `21600` |
| MAX_ATTEMPTS | `3` |
| DEFAULT_COVER_THRESHOLD | `80%` |

## Related concepts

- [[phase-ledger]] — Phase Ledger
- [[pointer-based-state]] — Pointer-based state
- [[sdlc-hard-gate]] — SDLC hard-gate

## Citations (from contributing transcripts)

- **Claim:** The stop-enforce-gate hook... is session-bound via a pointer model identical to G4
  - Source: go_full.md (`03585e5b-6aa8-4960-afbf-5fb9c306740f`)
  - Context: The stop-enforce-gate hook... is session-bound via a pointer model identical to G4
- **Claim:** Stale pointer TTL is 6 hours
  - Source: go_full.md (`03585e5b-6aa8-4960-afbf-5fb9c306740f`)
  - Context: Stale pointer TTL is 6 hours (_STALE_TTL_SECONDS = 6 * 3600)
- **Claim:** Trap prevention is driven by the payload's stop_hook_active field
  - Source: go_full.md (`03585e5b-6aa8-4960-afbf-5fb9c306740f`)
  - Context: Trap prevention is driven by the payload's stop_hook_active field (CC's recursion flag).
- **Claim:** The hook is wired directly via project settings... NOT through the plugin's hooks.json
  - Source: go_full.md (`03585e5b-6aa8-4960-afbf-5fb9c306740f`)
  - Context: The hook is wired directly via project settings... NOT through the plugin's hooks.json

## Receipts

Source-derived concept: all claims in this page originate from
transcripts in NotebookLM notebook `4017aa6e-35fb-426d-bc53-34620bec405e`
(cluster `stop-hooks-enforce`). No claims are made
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

- NotebookLM notebook [[INGESTED] - Claude Code Guide: Production Hooks and Agent Skills](https://notebooklm.google.com/notebook/4017aa6e-35fb-426d-bc53-34620bec405e)
- Studio artifacts: Report (concept extraction) + Data-Table (tabular facts)
