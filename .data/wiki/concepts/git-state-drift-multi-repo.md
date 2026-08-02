---
title: "Git state drift across multiple repos"
type: concept
tags: [git, multi-repo, state-drift, workspace-health]
created: 2026-08-02
source: session 019fa8f8, git-state FAIL
---

# Git state drift across multiple repos

## Summary

Session 019fa8f8 left both P:/ (27 uncommitted files, 15 unpushed commits) and C:/Users/brsth/.grok (9 uncommitted files, 23 unpushed commits) in dirty state. This is a recurring pattern across sessions — the auto-commit rule fires for tracked files but untracked files and the .grok repo require manual intervention.

## Context

The workspace has two git repos that are independently tracked:
- `P:/` — the main workspace repo
- `C:/Users/brsth/.grok` — the user-level Grok Build repo

Each repo can accumulate uncommitted changes independently. The AGENTS.md auto-commit rule covers tracked files, but untracked files and the .grok repo are not automatically committed.

## Pattern

1. Session starts with clean state in both repos
2. Work produces uncommitted changes in both repos
3. Auto-commit fires for tracked files in P:/ but not for untracked files or .grok repo
4. Session ends with dirty state in both repos
5. Next session inherits the dirty state, complicating any git-based operations

## Implications

- Uncommitted changes can be lost if another agent commits and the working tree updates
- The .grok repo has 23 unpushed commits — these contain hook script changes and state logs that may be needed by other sessions
- The 9 dirty files in .grok include state files (hook_failures.jsonl) that are hot-write targets

## Remediation

1. Commit untracked files in P:/ as logical units (surgical `git add`)
2. Commit untracked files in C:/Users/brsth/.grok
3. Push both repos after operator review
4. Consider adding a session-end check that warns about dirty state in both repos

## Related

- `close-runner-windows-path-json-stringification-bug.md` — the close-runner bug that blocked close-check
- `workspace-script-fmea-concurrent-io-and-shell-injection-patterns.md` — FMEA patterns

## Falsifier

If both repos are clean and in sync with origin/main after the remediation steps, the pattern is broken.
