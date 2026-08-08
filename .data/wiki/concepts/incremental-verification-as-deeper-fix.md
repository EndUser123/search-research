# Incremental Verification as the Deeper Fix

**Status:** concept (captured 2026-08-08)
**Provenance:** /tp fresh-lens critique (session 019fdf3c), disconfirming the hash-bound suppression approach
**Citations:** [[predictable-enforcement-for-recommendation-commitment]], [[verification-claim-admissibility]]
**Host applicability:** Host-agnostic (pattern applies to any LLM agent workspace)

## The core insight

The hash-bound verification receipt system (shipped 2026-08-08) suppresses false "hasn't run" suggestions from `/todo` by binding receipts to session diff hashes. This is correct but treats the symptom: **verification is expensive, so we want to avoid redundant re-runs.**

The deeper fix: **make verification cheap enough to re-run after every commit.** If `/check` takes <2 seconds instead of 2 minutes, suppression logic becomes unnecessary — you just always re-run, and the result is always current.

## The disconfirmation

The /tp fresh-lens critique raised this during review of the hash-binding work:

> "Is hash-bound suppression actually the right layer? The real problem is that `/check` is too expensive to re-run casually. If we made it incremental — only re-check what changed since the last verified state — suppression would be unnecessary."

This reframes the problem from "track when we verified" to "make verification trivially re-runnable." The hash-binding is the correct fix for the current cost profile; incremental verification is the fix that would make hash-binding unnecessary.

## Two approaches, not either/or

| Dimension | Hash-bound suppression (shipped) | Incremental verification (proposed) |
|-----------|----------------------------------|-------------------------------------|
| **What it fixes** | False "hasn't run" suggestions | Verification cost itself |
| **Complexity** | Moderate (receipt registry, hash computation, rotation) | High (change-detection, incremental scope, result caching) |
| **Failure mode** | Stale receipt → false suppression (mitigated by dirty-tree hash) | Scope drift → missed regressions (mitigated by file-level coverage) |
| **Time to value** | Shipped, working now | Multi-session investigation + build |
| **Re-runs /check?** | No (avoids it via suppression) | Yes (makes it cheap enough to not need avoidance) |

**They compose, not compete.** Hash-binding is the right fix at the current cost profile. Incremental verification is the longer-term fix that would simplify the system. If incremental `/check` ships and is fast enough, the hash-binding layer becomes a harmless safety net rather than load-bearing infrastructure.

## What incremental /check would look like

1. **Scope detection:** compare current `git diff` against the last verified commit hash. Only the changed files (+ their import graph) are in scope.
2. **Fast verifiers:** run only the file-specific checks (ruff, ast.parse, import resolution) on the in-scope files, not the full workspace scan.
3. **Result caching:** store per-file verification results. A file that hasn't changed since the last PASS doesn't need re-checking.
4. **Aggregate verdict:** PASS if all in-scope files PASS and no out-of-scope file was invalidated by the change.

**Estimated cost reduction:** from ~2 min (full workspace) to <5 sec (changed files only) for typical sessions where 2-5 files change.

## Relationship to existing work

- **ship-py's `_compute_session_diff_hash`** — already computes session-scoped diffs. The incremental /check would use the same mechanism but apply it to per-file verification scoping, not just hash computation.
- **script_scan.py** — already runs per-skill, not per-workspace. The incremental approach would extend this to per-file granularity.
- **`/close`'s `scan_check_receipts`** — reads receipt files. Incremental /check would produce richer receipts (per-file coverage, not just session-level verdict).

## When to build this

**Trigger:** if the hash-binding layer proves insufficient (false suppressions at >5% rate) OR if operators report that `/check` takes too long to run casually.

**Anti-trigger:** if the hash-binding layer works well and operators don't avoid `/check` due to cost, incremental verification is over-engineering.

## Falsifier

This concept is wrong if:
- `/check` is already fast enough that operators don't avoid re-running it (then the hash-binding is sufficient and incremental is unnecessary)
- The per-file scoping produces false confidence (a changed file in import graph A breaks file in import graph B, but B isn't re-checked)
- The result caching becomes stale faster than the hash-binding (e.g., dependency changes invalidate cached results faster than commits change the hash)
