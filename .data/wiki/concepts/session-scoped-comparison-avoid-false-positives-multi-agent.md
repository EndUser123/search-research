---
title: "Session-scoped comparison: avoid false positives from absolute state on multi-agent hosts"
created: 2026-08-09
source: session-019fe403 (verdict staleness false positive from absolute HEAD comparison)
tags: [failure-pattern, session-scoped, multi-agent, false-positive, git-comparison, ship-py, bug-class]
host: grok
agent: grok
verification: observed
relations:
  - target: wiki/concepts/rag-apr-evidence-retrieval-augmented-generation-improves-llm-bug-repair.md
    type: supports — fills gap in wiki failure-pattern coverage for /why-in-fix
  - target: wiki/concepts/invariants-beat-environment-comfort.md
    type: applies — multi-terminal isolation is the invariant
summary: >
  Comparing absolute state (HEAD commit hash) between pipeline phases produces
  false positives on multi-agent hosts — sibling sessions move HEAD constantly.
  Fix: compare session-scoped state only. Use `git diff <old_head>..HEAD --
  <session_files>` to detect if THIS session's files changed, not whether HEAD
  moved.
---

# Session-scoped comparison on multi-agent hosts

## The pattern

```
Phase A records HEAD = "abc123"
  ↓
Phase B runs, compares current HEAD to "abc123"
  ↓
HEAD is now "def456" (sibling session committed)
  ↓
Phase B reports "drift detected!" — FALSE POSITIVE
  ↓
Pipeline blocks even though THIS session's files didn't change
```

## Evidence

**ship-py verdict→merge staleness check (session 019fe403):** The verdict
phase recorded `verdict_heads["P:/"] = "abc123"`. The merge phase compared
`git rev-parse HEAD` against the recorded value. On this host, a sibling
session committed between verdict and merge (seconds apart), moving HEAD
to "def456." The merge blocked with "HEAD drift detected" even though none
of the files this session touched had changed.

## How to detect this bug class

- **Symptom:** a staleness or drift check fires when no session-scoped change occurred
- **Diagnostic:** check whether the comparison uses absolute state (HEAD hash)
  vs. session-scoped state (specific files)
- **Environment:** only occurs on multi-agent hosts where sibling sessions
  share the same git repository

## Structural fix

```python
# WRONG: absolute comparison
current_head = git("rev-parse", "HEAD")
if current_head != recorded_head:
    block()  # false positive on multi-agent hosts

# CORRECT: session-scoped comparison
changed_files = git("diff", "--name-only", f"{recorded_head}..HEAD", "--", *session_files)
if changed_files.strip():
    block()  # only blocks if THIS session's files actually changed
```

The principle: on a multi-agent host, never compare absolute repository
state. Always scope comparisons to the session's own files.

## Why /why-in-fix would benefit from this concept

When the fix agent encounters "staleness check fires but no real drift,"
querying the wiki for "session-scoped comparison" would surface this pattern
and the fix (git diff scoped to session files, not absolute HEAD).
