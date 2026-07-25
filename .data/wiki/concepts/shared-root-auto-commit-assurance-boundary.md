---
title: "Shared-root auto-commit assurance boundary"
concept_type: "constraint"
created: 2026-07-25
agent: grok
host: both
cognitive_load: 1
---

# Shared-root auto-commit assurance boundary

## Constraint

The `/close` receipt-primary auto-commit system is safe against cooperating
receipted sessions (all writers produce mutation receipts through active hooks).
It **cannot** prove exclusive ownership when external unreceipted writers
modify the same path in the shared working tree.

## Affected scenarios

- A human editor modifies a file directly (IDE, notepad)
- Codex CLI or Agy sessions modify files without Grok's mutation hooks
- Git operations in other terminals (`pull`, `merge`, `checkout`) change the
  working tree with no receipt

In these cases, the foreign content can be silently incorporated into a
current-session receipt's post-state, and the receipt's post-hash matches the
combined content. The three-way blob comparison cannot detect this because no
foreign receipt exists.

## Recommended response

Use worktree isolation (`git worktree add`) for sessions where unreceipted
writers may be active. Worktree isolation is the structural fix (ADR-008).

## Evidence

Proven by replay (U1-U3 false-allow scenarios in the falsification audit):
external writer modifies a file → no receipt → session A's terminal command
incorporates the content → A's post-hash matches → auto-commit allows.

## Related

- ADR-008 — worktree-per-session architecture
- [[private-index-staging-proof-canonical-blob-oid]]
