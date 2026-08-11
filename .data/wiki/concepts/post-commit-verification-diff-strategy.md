---
title: Post-commit verification pipelines need commit-range diffs
title_short: post-commit-verification-diff-strategy
date: 2026-08-10
verified_date: 2026-08-10
tags: [ship-py, pipeline-design, post-commit, git-diff, verification]
host: both
---

# Post-commit verification pipelines need commit-range diffs

## The pattern

Pipelines that support post-commit verification mode (verifying already-committed
work rather than gating pre-commit work) must use a different git diff strategy
than pre-commit mode. Bare `git diff` returns nothing for committed changes.

## The diff strategy hierarchy

| Mode | Git command | When to use |
|------|-------------|-------------|
| Pre-commit | `git diff` (working tree) | Changes are uncommitted |
| Post-commit (single commit) | `git diff HEAD~1..HEAD` | Last commit only |
| Post-commit (session range) | `git diff <start>..<end>` | Full session commit range |
| Fallback | Read file contents directly | When no diff is available |

## What goes wrong without this

In ship-py session 019fe4c1, the pipeline ran in post-commit verification mode
(work already committed and pushed). `build_diff_summary` used bare `git diff`,
which returned nothing. The dispatch phases sent empty prompts to the model,
got empty stdout back, and blocked. Five pipeline re-runs were needed to
diagnose and patch the issue, each finding a new symptom:

1. Empty diff → model gets nothing → `empty_response`
2. `HEAD~1..HEAD` → only gets last commit, not full session
3. File-contents fallback → works but sends full file, not diff

## The fix

Store the session's commit range in the detect phase state. In
`build_diff_summary`, when post-commit mode is detected, use the stored range
instead of bare `git diff`.

```python
# In detect phase:
state["session_commit_range"] = f"{merge_base}..HEAD"

# In build_diff_summary:
if state.get("already_shipped"):
    commit_range = state.get("session_commit_range", "HEAD~1..HEAD")
    rc, diff_out = _git(repo, "diff", commit_range, "--", *paths)
```

## Reusability

This pattern applies to any verification pipeline that supports both:
- Pre-commit mode (gating before work ships)
- Post-commit mode (verifying after work ships)

The pipeline must detect which mode it's in and select the appropriate diff
strategy. Using the wrong strategy produces empty diffs, which cascade into
empty model output, blocked phases, and wasted debugging cycles.

## Reference

- Ship-py session 019fe4c1: the empty-diff cascade
- Handoff: `P:/docs/handoffs/ship-py-pipeline-integration-gaps-20260810/HANDOFF.md` gap 3
