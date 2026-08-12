---
title: "Rename staleness in session-scoped diffs: pathspec filtering defeats git rename detection"
created: 2026-08-12
source: session-019fef48 (ship-py check-phase false positive after close→close-py consolidation)
tags: [failure-pattern, rename-detection, session-scoped, git-internals, pathspec, diffcore, content-identity, ship-py, bug-class]
host: both
agent: grok
verification: observed
relations:
  - target: wiki/concepts/session-scoped-comparison-avoid-false-positives-multi-agent.md
    type: refines — covers the rename variant of session-scoped false positives
  - target: wiki/concepts/multi-terminal-isolation-stale-data-immunity.md
    type: instance-of — rename staleness is a stale-data failure
  - target: wiki/concepts/session-scoped-comparison-avoid-false-positives-multi-agent.md
    type: complements — that concept covers absolute-HEAD false positives; this covers path-staleness false positives
summary: >
  Session-scoped diff tools that read file paths from a hunk log (edit-time
  paths) and pass them to `git diff -- <paths>` produce empty diffs after a
  rename. Pathspecs are applied BEFORE diffcore-rename in git's pipeline, so
  `--find-renames` cannot rescue a stale-path-filtered diff. The fix is NOT
  `git diff --find-renames` (it still pathspec-filters first); the fix is
  `git log --follow` to resolve each stale path to its HEAD-tracked location,
  THEN diff the resolved paths. Confirmed empirically against gitdiffcore(7)
  and the git source. L5+ (drop pathspec, use content-filtered diff) does NOT
  work for wide commit ranges because rename detection across many intermediate
  commits degrades to add/delete pairs.
---

# Rename staleness in session-scoped diffs

## The failure

```
1. Session edits skills/close/__lib/config.py (recorded in hunk log)
2. A rename commit (git mv) moves config.py → close-py/__lib/_scanners/config.py
3. Session-scoped diff tool reads hunk log → gets OLD path
4. git diff -- skills/close/__lib/config.py → EMPTY (path doesn't exist in HEAD)
5. git diff --find-renames -- skills/close/__lib/config.py → ALSO EMPTY
6. Diff tool reports "no changes" or feeds a near-empty diff to a model
7. Model correctly reports "no implementation file exists" — true for the diff it received
```

## Why --find-renames does NOT fix this

The gitdiffcore(7) documentation is explicit:

> "The pathspecs are used to limit the world diff operates in. They remove the filepairs outside the specified sets of pathnames."

**Pathspecs are applied BEFORE diffcore-rename.** The rename detection only sees filepairs that survived the pathspec filter. If the pathspec is `skills/close/__lib/config.py` and HEAD has `skills/close-py/__lib/_scanners/config.py`, the filepair is removed before rename detection ever runs. `--find-renames` has nothing to match.

Git commit history confirms this ordering was an explicit design decision: `[PATCH 11/12] Move pathspec to the beginning of the diffcore chain` (Junio C Hamano, git mailing list).

## Empirical verification (session 019fef48)

```
# Path-filtered with --find-renames: EMPTY (pathspec kills it)
$ git diff --find-renames --name-status 4ae7f74..HEAD -- skills/close/__lib/config.py
(empty)

# Unfiltered with --find-renames across wide range: shows ADD not RENAME
$ git diff --find-renames --name-status 8348370^..HEAD | grep config
A skills/close-py/__lib/_scanners/config.py

# --follow traversal: WORKS (traces path history across rename)
$ git log --follow --oneline -- skills/close-py/__lib/_scanners/config.py
4ae7f74 fix(ship-py): session-scoped diff in check phase...
5de08b8 fix: clear 8 code defects...
8348370 refactor close_accounting: extract Config to config.py (seam A)
```

`--find-renames` fails across wide commit ranges because rename detection compares blob similarity between adjacent tree states. With many intermediate commits, the file accumulates enough changes that the similarity score drops below the 50% threshold, and git records it as add+delete instead of rename.

## Why L5+ (content-filtered diff) is NOT the optimal fix

Previous analysis (session 019fef48 /tp) recommended dropping pathspec filters entirely and using `git diff --find-renames <session_range>` without path arguments, then matching results to the session by content. **This does not work** for two reasons:

1. **Pathspec removal loses session scoping.** On a multi-agent host, the unfiltered diff includes sibling-session commits within the time range. You trade rename-staleness false positives for sibling-contamination false positives.

2. **Wide-range rename detection degrades.** `git diff --find-renames` across many commits with intermediate edits produces `A` (added) + `D` (deleted) pairs instead of `R` (renamed) pairs. The rename is only detectable on a NARROW range around the rename commit itself.

## The actual fix: path resolution via --follow

The correct approach is a **path-resolution layer** that maps edit-time paths to HEAD-tracked paths using `git log --follow`:

```python
def resolve_to_head(edit_path: str, repo: str) -> str | None:
    """Map an edit-time path to its HEAD-tracked location.

    Uses git log --follow to trace the file's history across renames.
    Returns the current path if the file still exists at the original location.
    Returns None if the file was deleted (not renamed).
    """
    # Fast path: does it exist in HEAD as-is?
    rc, _ = _git(repo, "ls-tree", "HEAD", "--", edit_path)
    if rc == 0 and _.strip():
        return edit_path  # path unchanged

    # Stale path — trace history to find current location
    rc, log = _git(repo, "log", "--follow", "--format=%H", "--", edit_path)
    if not log.strip():
        return None  # file deleted, not renamed

    # Get the current path from the most recent commit touching this history
    latest_commit = log.strip().split("\n")[0]
    rc, tree = _git(repo, "ls-tree", "-r", "HEAD", "--name-only")
    # Match the blob hash from latest_commit to find current path
    # ... (implementation detail)
```

This is the **L2 path resolver** from the abstraction analysis — confirmed as the correct level. L5+ (content-filtered diff) is empirically denied by git's own diffcore ordering.

## Impact surface

This bug affects every tool that reads hunk-log paths and passes them to `git diff`:

| Tool | Files with session-scoping logic | Vulnerable? |
|------|--------------------------------|-------------|
| ship-py | 16 files, 40+ refs | YES — confirmed false positive |
| close-py | 10 files, 13+ refs | YES — same pattern |
| /check receipt scanning | separate logic | LIKELY — uses session_id filtering |
| /review file resolution | separate logic | LIKELY — same pattern |

The DRY violation (4 systems each have their own session-scoping code) means the fix needs to be a shared module, not a per-system patch.

## Design-choice audit

| Decision | CONCEPT | SCOPE | FIT | Rejected alternative |
|---|---|---|---|---|
| Path resolver via `--follow` | Right mechanism — uses git's native rename traversal | Fires only when ls-tree fails (opt-in per stale path) | Read-only, no side effects | `--find-renames` on pathspec: denied (pathspec kills it) |
| Shared module in _shared.py | Right unit — 4 consumers need the same logic | All consumers inherit the fix | No per-system patches | Per-system patches: rejected (DRY violation, 4x maintenance) |
| `ls-tree` fast path before `--follow` | Right optimization — no-op when path unchanged | Common case (no rename) is a cheap ls-tree | Multi-terminal safe | Always run --follow: rejected (slow, O(N) per file) |

## Falsifier

This concept is wrong if:
- `git diff --find-renames` with pathspecs EVER detects renames across wide ranges (it doesn't — verified empirically and via gitdiffcore docs)
- `--follow` fails to trace a file across a `git mv` rename (it doesn't — verified: both old and new paths trace to the same history)
- The pathspec-before-rename ordering is changed in a future git version (unlikely — it's a documented design decision with a named commit)

## Reference incident

Session 019fef48 (2026-08-12): ship-py check phase blocked with "no implementation file exists" after a close→close-py consolidation renamed 14 files. The model (nim-openai-gpt-oss-20b) correctly assessed the diff it received — the diff only contained marketplace-bridge/SKILL.md (not renamed) and was missing all 7 refactor modules (renamed). Two prior RCAs (compaction-boundary split, timestamp-filter exclusion) were refuted by direct evidence. The actual root cause was confirmed via gitdiffcore docs + empirical testing.
