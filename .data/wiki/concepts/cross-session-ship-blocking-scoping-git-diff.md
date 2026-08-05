---
title: "Cross-session ship blocking: scoping git diff on multi-agent hosts"
created: 2026-08-04
updated: 2026-08-04
source: session-2026-08-04 (/ship blocked by concurrent sessions' unresolved wikilinks)
tags: [multi-terminal, ship, doc-check, cross-session, isolation, git-diff, scope]
agent: grok
host: grok
cognitive_load: 2
verification: single-source-verified
summary: >
  When a ship receipt runs `git diff merge-base HEAD origin/main` to find changed
  files for doc-checks, a multi-agent host that doesn't push frequently has a large
  divergence (39+ commits). This includes every concurrent session's files in the
  doc-check scan — causing cross-session ship blocking from unresolved wikilinks in
  files this session never touched. Fix: cap the auto-detected scope to HEAD~N
  (default 15) when the merge-base divergence exceeds a threshold.
---

# Cross-session ship blocking: scoping git diff on multi-agent hosts

## The problem

`ship_receipt.py` auto-detects the diff scope as `merge-base HEAD origin/main`.
On a multi-agent host where 2+ agents commit to `main` without pushing, the
divergence grows (39+ commits ahead of origin). Every file touched by any
session in that range gets scanned by the inline doc-check (wikilinks, code
fences, frontmatter). If a concurrent session left an unresolved wikilink in
their SKILL.md, this session's ship is blocked — even though this session's
files are clean.

## Root cause

The `/check` and `/review` receipt lookups were already session-scoped
(filtered by `session_id` content in JSON, or by mtime for markdown). But the
inline doc-check (`run_doc_checks_inline`) operated on the full `files_changed`
list from `git diff --name-only merge-base..HEAD` — the one check that was
never session-scoped.

## Fix

In `collect_git_state()`, when `--since` is not explicitly provided:

1. Detect `merge-base HEAD origin/main`
2. Count commits in the range (`git rev-list --count merge-base..HEAD`)
3. If count > `--max-commits` (default 15), narrow scope to `HEAD~max_commits`
4. Log the scope decision in the receipt output

The `--max-commits` parameter lets the operator control the cap. `--since`
remains available for precise scope control.

## Why not filter by session_id?

Git commits don't carry session_id metadata. We can't filter the diff to only
commits from this session without either: (a) tagging commits with session_id
(invasive), or (b) tracking session start HEAD and diffing from there (fragile
— what if the session started mid-commit?). The bounded-window approach is
simpler, robust, and sufficient — 15 commits is enough to cover a typical
session's work without reaching into other sessions' files.

## Relationship to existing patterns

- [[invariants-beat-environment-comfort]] — multi-terminal isolation is a
  workspace invariant. The ship receipt now respects it.
- The `/check` and `/review` receipt lookups already had session-scoped
  filtering. This fix brings the inline doc-check to the same standard.

## Falsifier

This fix is wrong if:
1. A session makes more than 15 commits and the 16th commit has a doc-check
   issue that gets missed because it's outside the window
2. The `HEAD~N` syntax breaks on repos with fewer than N commits (edge case
   — the fallback handles this via `since = head`)
