---
title: "Git worktree best practices for multi-terminal fleets"
created: 2026-07-22
tags: [decision, git-worktree, multi-terminal, multi-agent, isolation, best-practices]
host: both
agent: grok
verification: local-only
cognitive_load: 2
summary: >
  When multiple agents work on the same repo without worktrees, uncommitted edits to tracked
  files risk silent overwrite from concurrent commits. Worktrees provide structural isolation.
  Commit-after-each-logical-unit is the fallback when worktrees aren't used.
---

# Git worktree best practices for multi-terminal fleets

## Rule

1. **Prefer worktrees for multi-file project work.** `git worktree add -b session-<id> P:/worktrees/session-<id>` isolates edits from concurrent commits.
2. **Commit after each logical unit — automatically, without asking.** Uncommitted edits to tracked files can be silently overwritten. A WIP commit is recoverable; an overwritten working-tree edit is not.
3. **Expect commit-time collisions.** Before staging, run `git log --oneline -5 -- <path>` — a sibling session may have already committed the same file.

## Why worktrees

The structural problem: multiple agents share one working tree. Agent A edits file X. Agent B commits (which may update the working tree). Agent A's edit is silently lost. Worktrees give each agent its own working tree, eliminating the collision class entirely.

## Falsifier

Wrong if commit-after-each-unit is sufficient without worktrees. Test: track how many working-tree edits are lost to concurrent commits over 1 month with commit-frequency rule but no worktrees.

## Relations

- [[agents-md-construction-best-practices]]
- [[enforcement-hierarchy-and-compaction-strategy]]
