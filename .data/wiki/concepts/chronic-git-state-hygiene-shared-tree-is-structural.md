---
title: "Chronic git-state hygiene: shared-tree multi-agent is structurally fragile"
created: 2026-08-06
tags: [git-state, multi-agent, shared-tree, worktree, chronic, close-check, external-validation]
host: both
---

# Chronic git-state hygiene: shared-tree multi-agent is structurally fragile

## Summary

The recurring `git_state: needs_attention` findings in close-check (27-55 uncommitted files, 7-25 unpushed commits across P:/ and ~/.grok, session after session) are not a hygiene discipline problem. They are a **structural consequence of the shared-working-tree regime**. External research confirms: the multi-agent development field has converged on **worktree isolation** as the answer. No published pattern solves "keep a shared working tree continuously clean with multiple concurrent writers."

## The pattern (internal evidence)

| Session | Date | P:/ uncommitted | P:/ unpushed | ~/.grok uncommitted | ~/.grok unpushed |
|---------|------|-----------------|--------------|---------------------|------------------|
| 019fa111 | 2026-08-01 | 25 | 15 | 4 | — |
| 019fa8f8 | 2026-08-01 | 27 | 15 | 9 | 23 |
| 019fb937 | 2026-08-02 | 27 | 17 | 4 | 25 |
| 019fc927 | 2026-08-03 | 42 | 7 | 55 | 6 |

The pattern recurs every session. The close-check scanner correctly detects it but cannot attribute specific dirty files to specific sessions (see [[session-write-path-attribution-gap-no-receipts]]).

## External research (web findings)

**Meta-finding:** the field has converged on isolation, not on shared-tree cooperation.

### 1. Worktrees are the dominant consensus

The Zylos research piece (2026-02-22) catalogs the most complete set of multi-agent git patterns. 7 of 10 search results converged on worktrees. Documented failure modes of shared-tree multi-agent:
- File collisions (silent overwrites)
- **Context contamination** (agent reads a partially-edited file, reasons incorrectly)
- **Index corruption from concurrent `git add`**
- Conversation confusion (agent's mental model diverges from disk state)

### 2. auto-git concluded "you need worktrees"

The auto-git project (github.com/async/auto-git) was literally designed for multi-agent git hygiene. Its coordinated mode uses:
- Per-chat branches + worktrees
- Shared lease files for cross-agent visibility
- Per-repo ledger for attribution
- Commit-by-intent taxonomy (feat:, fix:, security:, etc.)

Even this project concluded that shared-tree multi-agent is the wrong regime.

### 3. Firsthand accident record (yurukusa)

800+ hours of unattended Claude Code documented that auto-commit hooks themselves become a source of dirty state:
> "Your work gets auto-committed. Safety hooks and test scripts sometimes run git add / git commit internally. Work you weren't ready to commit gets swept into automatic checkpoint commits, and your branch fills with commits you didn't mean to make."

His conclusion: **isolation is the only thing that actually works.**

### 4. Shared-tree discipline patterns exist but are unenforced

The eliteai git-hygiene skill (eliteai.tools) is the closest published "shared dirty tree rules of engagement":
- Commit only staged changes (your files)
- Never `git add .` — always `git add <specific paths>`
- Never stage/commit someone else's changes
- Avoid rebases/non-ff merges
- `git fetch origin --prune` is the only safe sync

**No locking, no leases.** Relies entirely on every agent following the rules. This is what AGENTS.md already mandates — but without enforcement, it fails under concurrent load.

### 5. Auto-commit daemons are all single-writer

gitwatch, etckeeper, gwatch — every tool in the "watch a folder and auto-commit" family is single-writer by construction. The moment a second writer enters the same repo, debounce windows overlap, `git add -A` collides, and index corruption follows.

### 6. FlowCheck provides session-level attribution

FlowCheck (github.com/backslash-ux/flowcheck) is a Python MCP server that monitors git state in real-time and nudges agents to checkpoint-commit. It provides per-session correlation IDs — the closest thing to answering "whose file is this?" at the session level. But it doesn't prevent collisions or serialize writes.

## Why the current close-check regime produces false BLOCKED verdicts

The close-check scanner correctly detects dirty working trees. But the BLOCKED verdict is misleading because:

1. **Most uncommitted files are from sibling sessions**, not the current session
2. **The scanner cannot attribute specific files to specific sessions** (no write-path receipts — see [[session-write-path-attribution-gap-no-receipts]])
3. **The BLOCKED verdict recurs every session** because the structural condition (shared tree, many writers) doesn't change
4. **Cleaning the tree manually is Sisyphean** — it dirties again as soon as sibling sessions resume

## Structural fixes (ranked by leverage)

1. **Per-session worktrees** — eliminates the class entirely. Each session gets its own working tree; merges happen via PR or branch integration. AGENTS.md already says "For multi-file project work, prefer a worktree." The web research validates this as the dominant consensus.

2. **Session write-path receipts** — even without worktrees, tracking which files each session touched would let the scanner attribute dirty files correctly. Currently no receipt mechanism exists (see [[session-write-path-attribution-gap-no-receipts]]).

3. **Close-check should distinguish session-owned vs sibling-owned dirty files** — the scanner currently flags ALL dirty files as session-attributed, inflating the BLOCKED count. Fix: the git_state gate should report session-owned files as FAIL and sibling files as INFO.

4. **Scheduled background push** — a cron/scheduled task that pushes unpushed commits every N minutes would eliminate the "unpushed commits" finding class without operator intervention.

## What does NOT work

- **Discipline-only coordination** (AGENTS.md auto-commit rule): already in place, already fails under concurrent load
- **Auto-commit daemons**: all single-writer; would collide in a multi-agent tree
- **Ignoring the finding**: the close-check workflow BLOCKS on it every session, producing noise
- **Manual cleanup every session**: Sisyphean; the tree dirties again immediately

## Cross-references

- [[git-state-drift-multi-repo]] — documents the pattern
- [[concurrent-session-commit-collision]] — documents the overwrite risk
- [[git-worktree-multi-terminal-best-prategies]] — structural fix via worktrees (the field consensus)
- [[session-write-path-attribution-gap-no-receipts]] — why the scanner can't attribute dirty files
- [[chronic-workspace-health-debt-inventory-2026-08-01]] — classified git-state as "NOT chronic" (incorrectly — it recurs every session)
- [[close-check-workflow-replaces-close-for-session-readiness]] — the workflow that keeps BLOCKING on this
- [[close-runner-windows-path-json-stringification-bug]] — compounding issue

## Sources

| Source | Key finding |
|--------|------------|
| zylos.ai/research/2026-02-22-git-worktree-parallel-ai-development | Most complete catalog of worktree patterns and shared-tree failure modes |
| github.com/async/auto-git | Project designed for this problem that concluded "you need worktrees" |
| gist.github.com/yurukusa/2e22111de49dd1bf534bd223487b8aa9 | Firsthand 800h unattended Claude: auto-commit hooks create dirty state |
| eliteai.tools/agent-skills/git-hygiene | Closest published shared-tree rules of engagement (discipline-only) |
| github.com/backslash-ux/flowcheck | Real-time git monitoring with session-level attribution |
| safjan.com/git-autocommit-on-file-changes | Catalog of auto-commit daemons (all single-writer) |
