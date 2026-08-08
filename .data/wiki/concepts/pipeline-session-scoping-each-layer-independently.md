---
title: "Pipeline session-scoping — each layer must independently scope, not trust upstream"
created: 2026-08-08
source: session-019fdf3d
tags: [pipeline-design, multi-agent, session-scoping, ship-py, doc-check, transferable-technique]
summary: >
  On a multi-agent host where multiple sessions commit concurrently to the same
  branch, every layer of a verification pipeline must independently scope its
  checks to the current session's files — not trust an upstream filter. A single
  session-scoped entry point (detect) does not protect downstream phases that
  have their own diff mechanisms. The pattern: propagate the session file list
  to every phase via explicit parameters (--files-only, --files, --fix), never
  via implicit merge-base diff.
agent: grok
host: grok
cognitive_load: 2
verification: observed
relations:
  - target: wiki/concepts/narrative-sufficiency-awareness-enforcement-gap-2026.md
    type: related
  - target: wiki/concepts/check-after-ship-py-verification-sequence.md
    type: complements
  - target: wiki/concepts/mechanical-enforcement-over-behavioral-reminder.md
    type: extends
---

# Pipeline session-scoping — each layer must independently scope

## Decision context

Ship-py blocked three times on files the current session never touched. Each
time, the root cause was the same: a pipeline layer used merge-base diff
(HEAD~N) to determine which files to check, and the merge-base included
commits from sibling sessions running concurrently on the same branch.

The first fix (detect phase: stop appending dirty-tree noise) was insufficient
because the verify phase had its own merge-base diff. The second fix (verify
phase: --files-only parameter) was insufficient because the doc-check phase
called an external script with --since, not --files. Each layer needed its own
session-scoping — a single entry-point filter was not enough.

## The pattern

**Propagate the session file list to every layer that does file-based work.**
The session file list comes from the platform's per-session edit log
(hunk_records.jsonl or session-scoped git log). Once obtained, it must be
passed explicitly to:

1. **Entry-point detection** (detect phase) — don't append dirty-tree status
   when session data is precise
2. **Each mechanical check layer** (verify, doc-check, refactor-scan) — pass
   `--files` or `--files-only` parameters, never rely on the entry point having
   already filtered
3. **External tool invocations** (check.py, ship_receipt.py, script_scan.py) —
   each tool needs the file list via its own parameter mechanism

**Anti-pattern:** filtering at the entry point and trusting downstream layers
to inherit the scope. Downstream layers that call `git diff --name-only` or
`get_diff_files()` will re-expand to the full repo scope regardless of what
the entry point decided.

## Why merge-base fails on multi-agent hosts

```
origin/main ── A ── B ── C (sibling session 1)
                \
                 D ── E ── F (this session)
                      ^
                      G ── H (sibling session 2)
```

Merge-base of HEAD with origin/main is A. `git diff A..HEAD` includes B, C
(sibling 1), G, H (sibling 2), plus D, E, F (this session). On a host with 3+
concurrent sessions, the merge-base diff captures every session's files.

The fix is not "narrow the merge-base" (HEAD~N caps help but still cross
sessions). The fix is "don't use merge-base at all when a precise session
file list is available." This is the same principle as
[[multi-terminal-isolation-stale-data-immunity]]: each layer must scope its
own data, not trust that upstream handled it.

## What this means for our workspace

Ship-py now implements session-scoping at all three mechanical-check layers:

| Layer | Mechanism | Parameter |
|---|---|---|
| ship_orchestrator.py detect | files_changed from session_files, not dirty-tree status | internal |
| ship_receipt.py verify | `--files-only` filters files_changed before all checks | CLI parameter |
| doc-check check.py | `--files` overrides get_diff_files entirely | CLI parameter |

The pattern generalizes to any pipeline that runs on this host: `/review`,
`/check`, `/risk`, and any future verification skill should accept a file-list
parameter and scope to it when provided. The orchestrator (the entry point)
is responsible for obtaining the session file list and propagating it.
This is the [[concurrent-cdp-auth-contention]] problem generalized to file
state: each consumer must scope independently, not trust shared mutable state.
The same principle applies to [[multi-terminal-isolation-stale-data-immunity]]
where artifact directories must be session-scoped, not glob-matched.

## Falsifier

This pattern is wrong if the platform's per-session file log (hunk_records.jsonl)
becomes unreliable or if sessions start using worktrees that isolate them from
the shared branch entirely. In a worktree-isolated workflow, merge-base diff
would be sufficient because the branch would only contain one session's commits.

## Receipts

- `ship_orchestrator.py:377-391` — dirty-tree fallback now only fires when
  session_files is None (was: unconditionally appending all dirty files)
- `ship_receipt.py:1250-1270` — `--files-only` parameter filters files_changed
  by suffix match (last-3 path components) to handle absolute/relative path
  differences
- `check.py:410-425` — `--files` parameter overrides `get_diff_files()` with
  explicit comma-separated file list
- Session 019fdf3d: ship-py blocked 3 times on foreign files before all three
  layers were session-scoped

## Auto-related

- [[skill-graph]]
- [[scope-matching-verification-discipline]]
- [[context-firewall-architecture]]
- [[agent-control-plane-enforcement-architectures-2026]]
- [[claim-without-checking-industry-approaches-2026]]

