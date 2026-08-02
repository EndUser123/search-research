---
thread_id: close-check-known-block-caching-20260802
parent_handoff_path: none
current_session_id: 019fa276-89c7-7310-b882-096cf67652cf
current_terminal_id: grok-build-terminal
produced_at: 2026-08-02T20:00:00Z
status: open
handoff_type: implementation
accurate_as_of_head: 992b8d5
---

# Close-check known-block caching

## Objective

Cache "already known blocked" findings in the close-check workflow so it doesn't re-discover the same chronic blocks every invocation.

## Problem

The close-check workflow took 27 minutes and returned BLOCKED on findings that were 90% pre-existing (broken scanner, dirty git state from siblings, chronic hooks_audit failures). Every invocation re-discovers these same blocks from scratch. The operator sees "9 BLOCKED findings" and has to mentally filter which are new vs which are the same chronic issues from 3+ sessions.

## Proposed approach

Add a `known_blocks.json` cache file at `P:/.artifacts/close-check-known-blocks.json`. Each entry:
- Finding ID (hash of the finding text)
- First seen timestamp
- Last seen timestamp
- Session count (how many sessions it's appeared in)
- Finding text (one line)

When the workflow detects a finding that matches a known block:
- If seen in <3 sessions: report normally (may be transient)
- If seen in ≥3 sessions: mark as `[KNOWN: N sessions]` and de-prioritize in the report
- If new: add to cache

The report then has two tiers:
- **New findings** (surfaced prominently)
- **Known chronic findings** (collapsed, with session count)

## Acceptance criteria

1. The close-check report distinguishes new findings from known chronic ones
2. Known chronic findings include their session count (how many sessions they've appeared in)
3. The cache file is at a stable path and updated on every close-check run
4. New findings are never suppressed — only known ones are de-prioritized

## Dependencies

- **Requires:** Nothing
- **Blocks:** Faster close-check iterations (operator doesn't have to re-triage chronic blocks)

## Falsifier

This approach is wrong if the cache grows stale (findings that were resolved still appear as "known blocked") or if the hash-based matching produces false positives (different findings with similar text).
