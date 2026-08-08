# Handoff — hash-bound verification receipt system: open workstreams

## Status
OPEN — post-ship follow-ons from verification receipt system (shipped + SHIP VERIFIED 2026-08-08).

## Objective

The hash-bound verification receipt system is shipped and working. Three
non-blocking improvements were surfaced by the /tp fresh-lens critique and
/risk scan. This handoff captures them for a future session.

## Workstreams

### W1: Dirty-tree hash component (5-line fix)

`verification_receipt.py:_compute_session_diff_hash()` hashes session-scoped
committed work only (`git log --since`). Uncommitted edits are invisible.

**The gap:** if operator edits files → runs `/check` (hash from commits) →
makes more uncommitted edits → `/todo` queries → hash matches → suppresses
re-run suggestion incorrectly.

**The fix:** add `git status --porcelain` output to the hash:
```python
# After the commit-diff hashing loop:
rc_status, status_output = _git(repo_path, "status", "--porcelain")
if rc_status == 0 and status_output:
    hasher.update(status_output.encode("utf-8"))
    found_any = True
```

**Confirmation needed:** the gap is confirmed by code reading but its
real-world frequency is unmeasured. A historical transcript scan checking
for sessions where `/check` ran then `git status` showed dirty files
before the next `/todo` would confirm necessity. If >15% of sessions show
this pattern, the fix is confirmed necessary.

**Trade-off:** adding dirty-tree to the hash means sibling sessions'
uncommitted edits in shared repos mix in. This is acceptable because the
hash is per-session (the session's own `git status` includes only the
shared working tree, but two sessions on the same workspace see the same
dirty state — and if either made edits, re-verification is warranted).

### W2: Registry rotation

`P:/.artifacts/verification-receipts.jsonl` is append-only with no rotation.
The query (`verification_receipt.py:222-233`) linearly scans for the latest
matching `(session_id, skill)` pair.

**Current scale:** ~2 entries, 556 bytes. Not a problem.
**Future scale:** 4 skills × N sessions × ~280 bytes per entry. At 1000
sessions, ~1.1MB. Linear scan is still <10ms.

**The fix:** add rotation following the `_hook_timing.py` pattern (10MB /
5000 lines, one rotated copy). Or migrate to per-session manifest files
(`P:/.artifacts/verification-receipts/<session-id>.json`) so the scanner
reads one file per session.

### W3: SKILL.md → script-level receipt registration

`/review`, `/risk`, `/refactor` register receipts via SKILL.md instruction
(~50% compliance ceiling under session pressure). `/check` has script-level
registration via `write_check_state.py` (~100% compliance).

**The asymmetry:** today this is harmless — `/risk` and `/refactor` aren't
in `/todo`'s suggestion set, so under-coverage doesn't suppress anything
incorrectly. But the moment `/todo` adds `/risk` or `/refactor` suggestions,
the coverage gap will silently produce incorrect-skip suggestions.

**The fix:** when those skills eventually get `__lib/` scripts (or their
artifact-writing protocols mature), move receipt registration from SKILL.md
instruction to script-level automatic registration.

## Acceptance criteria

- W1: dirty-tree hash component added + historical confirmation scan run
- W2: rotation implemented OR per-session manifest migration done
- W3: at least one of /review, /risk, /refactor has script-level registration

## Provenance

- Source: /tp fresh-lens critique (subagent 019fe242, 15 tool calls), /risk scan, /aar session 019fdf3c
- Related wiki: [[predictable-enforcement-for-recommendation-commitment]] (the /www research)
- Shipped system: commit 85b0c5e (C:) + 9609875 (P:)
