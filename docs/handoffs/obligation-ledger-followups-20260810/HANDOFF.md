---
title: "Obligation-ledger + directory-policy follow-ups"
status: open
created: 2026-08-10
session: 019fe88b-af8e-77b2-87cd-04711b7f8257
assignee: unassigned
---

# Obligation-ledger + directory-policy follow-ups

## Status
OPEN — follow-ups from completed workstreams, no blocker

## Objective
Track the non-critical residuals from the obligation-ledger spike and directory-policy convergence. These were classified as FOLLOW_UP or OBSERVATION in the closure pass and do not block current work.

## What was completed

### Obligation-ledger (commits f9ca5e9 → 319845a → a955e4b)
- Structural conditional-obligation mechanism replacing equivalence_bypass_gate (255 false blocks/day → 0)
- hooks/** modified → /review REQUIRED, enforced through transcript + mutation receipts
- Freshness binding via receipt completed_at timestamp
- Threat model recorded in code comments
- equivalence_bypass_gate retired (empty hooks array)
- Verification matrix A-O: 15/15 (14 PASS + 1 PARTIAL)

### Directory-policy convergence (commit 4472d65)
- directory_policy_loader.py as single shared loader
- PreToolUse_directory_policy.py wired for search_replace|write
- /maintain Step 2e consumes loader (hand-maintained blocklist deleted)
- _meta references fixed (v3.3.0)

## Open follow-ups (in priority order)

### F1: Fix _extract_explicit_paths scope binding (Medium-High)
**Problem:** The receipt writer's `_extract_explicit_paths` matches file paths against the obligation's `observed_paths`, not against ALL paths in the command text. This caused 4-5 repeated Stop blocks during this session where verification ran but the receipt didn't bind scope correctly.
**Trigger:** Next session that touches hooks files and triggers the obligation.
**Likely next action:** Modify `_extract_explicit_paths` in `verification_receipt_writer.py` to match against all file-path-like tokens in the command text, not just `observed_paths` from the obligation.

### F2: Live-verify directory_policy PreToolUse (Medium)
**Problem:** The PreToolUse hook is registered in quality-gate.json but has NOT been observed blocking a real write through the Grok runtime (only subprocess-tested).
**Trigger:** Next session start after reload.
**Likely next action:** Attempt a prohibited root write (e.g., `write` to `P:/test_scratch.json`) and confirm the hook blocks it.

### F3: run_terminal_command root mutation enforcement (FOLLOW_UP)
**Problem:** Shell mutations to P:\ root bypass the PreToolUse gate (which only covers search_replace|write). mutation_post observes Git-tracked changes but not root-level file creation.
**Trigger:** Root pollution recurs through run_terminal_command after enforcement is live.
**Likely next action:** Extend mutation_pre/post to diff root directory state for run_terminal_command, or add a root-directory-state snapshot in the PreToolUse for run_terminal_command.

### F4: codex-pi snapshot producer fix (FOLLOW_UP)
**Problem:** Each codex-pi delegation run drops ~18k-file workspace snapshots into P:\tmp (including a 1.18GB artifacts blob). Producer code not yet located.
**Trigger:** codex-pi snapshots again consume material disk space.
**Likely next action:** Locate producer code; switch to worktree+overlay with try/finally cleanup. Wiki concept at P:/.data/wiki/concepts/codex-pi-snapshot-lifecycle-producer-problem.md.

## Uncaptured knowledge (from /insight)

### K1: Iterative cross-model hardening loop
The 7-round ChatGPT review pattern (implement → send → critique → fix → resend) is a proven high-value workflow. Each round found real defects self-review missed. Should be captured as `[[iterative-cross-model-hardening-loop]]`.

### K2: Stop-hook self-reference testing
Testing a Stop hook on your own turn requires multi-turn observation: trigger in turn N, observe in turn N+1. The transcript records tool calls but the Stop fires at end-of-turn. Should be captured as `[[stop-hook-self-reference-multi-turn-testing]]`.

## Verbatim last user message
> /handoff

## Falsifier
This handoff is wrong if any follow-up was misclassified as non-blocking when it actually invalidates a completed workstream goal. Review against the closure report (ChatGPT's verification prompt response) before acting.
