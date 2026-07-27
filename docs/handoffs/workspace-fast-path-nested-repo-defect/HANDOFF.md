# Handoff: Workspace fast-path misidentifies nested repos under P:\

**Created:** 2026-07-27
**Session:** 019fa23d-e74c-7ff2-ac51-980b5d999b87
**Status:** OPEN — defect confirmed, fix not implemented

## Problem

`resolve_path_identity_from_workspace(file_path, workspace)` in `path_identity.py:483-520` uses a workspace fast-path: if `file_norm.startswith(ws_norm + "/")`, it resolves identity from the WORKSPACE root rather than the file's actual git repo.

This causes files inside P:\ worktrees and nested git repos to be attributed to P:\ main, producing wrong `repository_root`, `git_relative_path`, and `expected_head` in mutation receipts.

## Situation

Discovered during Phase 3 acceptance testing (session 019fa23d). The child repo mutation at `P:/worktrees/phase3-acc/.agents/phase3_child/_acc_mut_c.py` was attributed to `repository_root: "p:"` instead of the child repo root. This caused:

1. HEAD conflicts in candidate resolution (P:\ main HEAD moves frequently from sibling sessions)
2. Wrong `expected_head` in mutation receipts (P:\ main HEAD instead of child repo HEAD)
3. B5 submodule reconciliation failures (child not recognized as a separate repository)

## Symptom

```python
from path_identity import resolve_path_identity_from_workspace, resolve_path_identity

# File inside P:\ worktree (workspace fast-path attributes to P:\ main)
test = "P:/worktrees/phase3-acc/.agents/phase3_child/_acc_mut_c.py"

from_ws = resolve_path_identity_from_workspace(test, "P:/")
# WRONG: repository_root = "p:" (P:\ main, not the child repo)

direct = resolve_path_identity(test)
# CORRECT: repository_root = "p:/worktrees/phase3-acc/.agents/phase3_child" (the child repo)
```

## Root cause

`resolve_path_identity_from_workspace` at line 496:
```python
if file_norm.startswith(ws_norm + "/") or file_norm == ws_norm:
    ident = _get_git_identity(ws_norm)  # ← uses WORKSPACE root, not file's repo
```

The fast-path assumes all files under the workspace belong to the workspace's git repo. This is true for flat repos but false for:
- Git worktrees (each worktree is a separate working tree of the same repo)
- Nested git repos (submodules, independent repos inside the workspace)
- Monorepo subdirectories that are independent git repos

The correct behavior: the workspace hint should be used as a STARTING POINT for `git rev-parse --show-toplevel`, not as the identity itself. The fast-path should run `git -C <file_dir> rev-parse --show-toplevel` (which the non-fast-path already does correctly), using the workspace only to skip the `find_git_root_from_path` walk.

## Fix

**Option A (minimal):** Remove the workspace fast-path entirely. Always use `resolve_path_identity(file_path)` which correctly finds the nearest git root from the file's directory. The workspace hint becomes unused (or used only as the fallback for paths that don't exist yet).

**Option B (optimal):** Keep the fast-path but fix it to run `git rev-parse --show-toplevel` from the file's directory, not the workspace root. The workspace hint optimizes the search by providing a known git repo to check first, but the result must be the file's actual repo root.

## Affected files

- `C:/Users/brsth/.grok/hooks/scripts/path_identity.py` (lines 483-520, deployed copy)
- `P:/worktrees/dotgrok-phase3/hooks/scripts/path_identity.py` (source)

## Acceptance criteria

1. `resolve_path_identity_from_workspace("P:/worktrees/any-worktree/file.py", "P:/")` returns the worktree's repository root, not `p:`
2. `resolve_path_identity_from_workspace("P:/.agents/some_nested_repo/file.py", "P:/")` returns the nested repo's root
3. Phase 3 acceptance test with child repo inside P:\ produces correct `repository_root` in mutation receipts
4. Deterministic suite 21/21 still passes
5. No regression for files directly in P:\ main (the common case must still work)

## Priority

Medium — the defect doesn't break Phase 3 for repos OUTSIDE P:\ (the workaround used in the latest acceptance). But it makes P:\-internal nested-repo testing impossible and will affect any real work that touches files in P:\ worktrees or nested repos.
