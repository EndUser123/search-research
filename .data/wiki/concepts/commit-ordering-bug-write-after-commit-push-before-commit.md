---
title: "Commit-ordering bug: writing files after commit but before push"
created: 2026-08-09
source: session-019fe403 (version-bump wrote uncommitted files, push sent old version)
tags: [failure-pattern, commit-ordering, version-bump, git-push, ship-py, bug-class]
host: grok
agent: grok
verification: observed
relations:
  - target: wiki/concepts/rag-apr-evidence-retrieval-augmented-generation-improves-llm-bug-repair.md
    type: supports — fills gap in wiki failure-pattern coverage for /why-in-fix
summary: >
  When a pipeline phase modifies files (e.g., version-bumping SKILL.md) and
  then pushes to remote WITHOUT committing the modified files first, the push
  sends the old committed version. The modified files stay dirty in the
  working tree. Remote and local diverge silently. Fix: commit ALL modified
  files BEFORE the push command. The invariant: nothing is pushed that wasn't
  committed.
---

# Commit-ordering bug: write after commit, push before commit

## The pattern

```
Phase modifies files (version bump, changelog)
  ↓
Phase pushes to remote (git push)
  ↓
Modified files are UNCOMMITTED — push sends the old version
  ↓
Remote has old version; local has dirty modified files
  ↓
Silent divergence: remote ≠ local
```

## Evidence

**ship-py publish version-bump bug (session 019fe403):** The `_bump_skill_versions()`
function wrote new version numbers to SKILL.md files. Then `git push origin main`
pushed. But the bumped files were never committed — `git push` only sends
committed changes. The remote received the old version numbers. The bumped
files stayed dirty in the working tree.

## How to detect this bug class

- **Symptom:** files appear dirty after a push that was supposed to include them
- **Diagnostic:** `git status` after push shows modified files that should
  have been pushed
- **Code pattern:** `write_files(); git_push()` without `git_add(); git_commit()`
  in between

## Structural fix

```python
# WRONG: write then push (skips commit)
write_files()
git("push", "origin", "main")  # pushes old version

# CORRECT: write, commit, THEN push
write_files()
git("add", *modified_files)
git("commit", "-m", "chore: bump version")
git("push", "origin", "main")  # pushes new version
```

The invariant: **nothing is pushed that wasn't committed.** Any phase that
modifies files must commit them before the push command runs.

## Why /why-in-fix would benefit from this concept

When the fix agent encounters "remote has old version after version bump,"
querying the wiki for "commit ordering bug" would surface this pattern and
the fix (commit before push).
