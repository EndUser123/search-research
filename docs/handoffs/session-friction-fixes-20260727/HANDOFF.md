---
thread_id: 019f9f4f-session-friction-fixes-20260727
parent_handoff_path: none
current_session_id: 019f9f4f-7f5b-7a71-9eaf-8f43ba9f8fb9
current_terminal_id: grok-build-terminal
produced_at: 2026-07-27T13:25:00Z
status: open
handoff_type: investigation
accurate_as_of_head: ea0a48be110dee12dd78317a611c1f6231c4d0f5
---

# Handoff: Session friction fixes — qmd parser + git lock contention

## Objective

Fix two recurring friction points from session 019f9f4f: (1) qmd search query parser fails on commas/keywords, (2) git index lock contention blocks commits when concurrent sessions are active.

## Status

SF-01: ✅ RESOLVED 2026-07-27 (root cause confirmed, fix applied, recovery script created).
SF-02: ✅ RESOLVED 2026-07-27 (retry-with-backoff helper added to grok-safe-git).

## Task packets

### SF-01: Fix qmd search query parser — ✅ RESOLVED

- **problem:** `qmd search --query "concurrent git commit collision multi-agent shared filesystem"` fails with `{"error":"no such column: <keyword>"}` on queries containing commas or certain SQL-like keywords. Failed 5+ times this session.
- **root cause (CONFIRMED Tier 1, 2026-07-27):** NOT SQL injection (the original hypothesis). The query was already parameterized via `?`. The actual cause: FTS5's MATCH expression parser interprets query-syntax characters (`-`, `:`, `^`, `"`, `*`, `(`, `)`) in the raw user query. A query like "build-vs-port" is misparsed — the hyphens trigger FTS5 query-syntax interpretation, and `vs` is treated as a column reference against the single-column `chunks_fts(text)` table, producing `no such column: vs`.
- **discriminating test (receipt):** `"build vs port"` (spaces) ✅ works; `"build-vs-port"` (hyphens) ❌ fails; `"vs"` (bare) ✅ works. Trigger isolated to FTS5 special characters, not the word "vs" itself.
- **fix applied:** added `_sanitize_fts5_query()` to `site-packages/qmd/core/collection.py` — wraps the query in double quotes (FTS5 phrase query), disabling syntax interpretation. Patched `_bm25_search` and `_check_strong_signal` to call it. Verified: original failing query now returns 3 results.
- **recovery:** `python P:/.agents/scripts/qmd_fts5_patch.py` — idempotent re-applier. Run after any `pip install --upgrade qmd`. Detects already-patched state and exits 0.
- **wiki concept:** `P:/.data/wiki/concepts/fts5-query-syntax-escaping-required.md` (the systemic pattern — affects any tool using FTS5 MATCH with user input).

### SF-02: Git index lock contention mitigation

- **problem:** concurrent sessions on the shared P:\ workspace hold `.git/index.lock` during commits, blocking other sessions for 10-60 seconds. Happened 5+ times this session.
- **root cause:** multi-agent shared working tree with no per-session isolation. Git's index.lock is a single-writer mutex on the staging area.
- **options:**
  - (A) Add retry-with-backoff to the commit commands (waits 5s, 10s, 20s before giving up). Lowest effort; doesn't fix the root cause.
  - (B) Document the pattern structurally in grok-safe-git (add a `git-commit-safe` helper that retries on index.lock)
  - (C) Use git worktrees per session (structural fix; each worktree has its own index). Highest effort; eliminates contention entirely.
  - (D) Accept the contention; document the wait-and-retry pattern. Zero effort.
- **in scope:** pick an option and implement or document
- **acceptance:** commits succeed within 30s even when concurrent sessions are active
- **falsifier:** the retry pattern masks a real stale lock that never clears

### SF-03: Gitleaks false positive (root cause identified — concurrent-commit collision)

- **problem:** gitleaks blocked a legitimate handoff commit with "SECRET DETECTED"
- **root cause:** the hook runs `git diff --cached | gitleaks stdin` — this scans ALL staged content, not just the file being committed. When concurrent sessions stage files between `git add` and `git commit`, gitleaks scans their content too.
- **status:** RESOLVED as a diagnosis — the gitleaks hook is correct; the concurrent-commit collision is the root cause (same as SF-02). No gitleaks fix needed; fixing SF-02 fixes this.
- **no action required** beyond documenting the diagnosis

## Resumption protocol

1. Read this handoff
2. For SF-01: inspect `site-packages/qmd/` for the SQL query construction code; add parameterized queries or escape the query string
3. For SF-02: pick option A/B/C/D based on how often the contention occurs in practice; implement or document

## Last user message (verbatim)

> "0" (proceed with all recommendations from /tp session)

## Epistemic labels

- SF-01 root cause is [INFERENCE] — the SQL interpolation hypothesis is strong but not confirmed by reading qmd source
- SF-02 root cause is [FACT] — git index.lock behavior is documented; contention observed 5+ times
- SF-03 root cause is [FACT] — the gitleaks hook source was read this session (`P:/.git/hooks/pre-commit` lines 55-59)
