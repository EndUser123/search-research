---
thread_id: e4a4a152-5635-48c4-aaf0-bcc8783dbc9f
parent_handoff_path: P:/docs/handoffs/phase3-current-state.md
current_session_id: 019f9d1f-70fc-7e43-b2d8-18b8d631ba53
current_terminal_id: grok-build-plan
produced_at: 2026-07-27T13:03:00Z
status: open
handoff_type: investigation
accurate_as_of_head: 4471f2c5fa98aae2f09123648fb2af3f2c23cc73
---

# B4 CAS persistence layer fails to produce verifiable commits in live acceptance

## Objective

Investigate why the B4 CAS commit engine (and B5 submodule reconciliation) produces commits that either dangle (object created, never linked to ref) or never exist (object never created) during live `/close` acceptance, despite the deterministic suite (21/21 tests) passing in isolation.

**Scope bounds:** This investigation covers the B4 `commit_coordinator.py` and B5 `submodule_coordinator.py` live commit path. It does NOT cover the Stop-hook gate (proven live), the verification-receipt system (proven live), or the deterministic test suite (passes). The gap is specifically: **tests pass → live commits don't exist**.

## Status

ALL FIXES DEPLOYED AND VERIFIED — B4 (3 fixes) + B5 (1 fix). Full suite 22/22.
Live smoke test confirms commits survive in refs. (2026-07-27T17:08Z)

### Fixes applied

| Fix | Commit | Files | Deployed |
|-----|--------|-------|----------|
| Mode A (B4 freshness barrier) | `e849e40` | `commit_coordinator.py` | ✅ hash-verified |
| Post-CAS sync removal | `e849e40` | `commit_coordinator.py` | ✅ hash-verified |
| Mode C (phantom SHA guard) | `e849e40` | `close_coordinator.py` | ✅ hash-verified |
| B5 same race window | `34cb5e4` | `submodule_coordinator.py` | ✅ hash-verified |

## Producing context

- Date: 2026-07-27
- Session: 019f9d1f-70fc-7e43-b2d8-18b8d631ba53
- Host: Grok Build on P:\
- Trigger: two independent acceptance attempts (this session + session 019fa23d) both produced unverifiable commit SHAs

## Read-first list (ordered)

1. `P:/docs/designs/phase3-hook-enforcement.md` — Phase 3 spec (B4/B5 contract)
2. `P:/docs/handoffs/phase3-current-state.md` — acceptance history and verdict (`PHASE_3_LIVE_ACCEPTANCE_NEEDS_FIX`)
3. `C:/Users/brsth/.grok/hooks/scripts/commit_coordinator.py` — B4 CAS engine (the suspect)
4. `C:/Users/brsth/.grok/hooks/scripts/submodule_coordinator.py` — B5 reconciliation (secondary suspect)
5. `P:/worktrees/dotgrok-phase3/hooks/scripts/tests/test_b4_commit.py` — deterministic tests that PASS but don't catch the live failure
6. `P:/worktrees/dotgrok-phase3/hooks/scripts/tests/test_b5_submodule.py` — B5 deterministic tests
7. `P:/worktrees/dotgrok-phase3/hooks/scripts/tests/test_b4_live.py` — live B4 tests (check if these actually verify ref linkage)
8. `P:/worktrees/dotgrok-phase3/hooks/scripts/tests/test_e2e_close_b5.py` — end-to-end close+B5 tests

**Why this order:** spec first (contract), then acceptance history (what failed), then the suspect code, then the tests that should have caught this.

## Verified facts

- [FACT] Session 1 (019f9d1f): commit `268cc357be75` claimed as "IS in P:\ HEAD" in handoff. `git cat-file -t 268cc357be75` → `commit` (object exists). `git log --all --oneline | grep 268cc357` → empty (NOT in any ref). `git reflog --all` → no trace. The object is **dangling**. (Verified 2026-07-27T00:49Z)

- [FACT] Session 2 (019fa23d): commit `eff9bc3` claimed as P:\ worktree commit. `git -C P:/ cat-file -t eff9bc3` → `commit` (object exists in P:\ store, shared with worktree). NOT in any ref of `P:/worktrees/phase3-acc`. Dangling. (Verified 2026-07-27T12:58Z)

- [FACT] Session 2: commit `0c4cd3e` claimed as ~/.grok commit. `git -C ~/.grok cat-file -t 0c4cd3e` → `commit` (object exists). NOT in any ref of ~/.grok. Dangling. (Verified 2026-07-27T12:58Z)

- [FACT] Session 2: commit `c3fb5b1` claimed as child repo commit. `git -C phase3_child cat-file -t c3fb5b1` → `fatal: Not a valid object name`. Object **does not exist at all** — not even as dangling. (Verified 2026-07-27T12:58Z)

- [FACT] Session 2: commit `6c7f7a4` claimed as parent gitlink commit. `git -C phase3_parent cat-file -t 6c7f7a4` → `fatal: Not a valid object name`. Object **does not exist at all**. (Verified 2026-07-27T12:58Z)

- [FACT] Session 2 handoff (commit `05beb57`) claims: "Parent gitlink: `c3fb5b1` == Child HEAD: `c3fb5b1`, MATCH ✓". This cannot be true — `c3fb5b1` does not exist as a commit in the child repo. (Verified 2026-07-27T12:58Z)

- [FACT] The child repo has a `.git` **directory** (not a `.git` file pointing to a worktree gitdir), confirming it's a standalone repository with its own object store. (Verified 2026-07-27T12:58Z)

- [FACT] The deterministic suite passes: 21/21 test files, 0 failures, run twice (pre- and post-acceptance). (Verified 2026-07-27T00:52Z and 2026-07-27T05:22Z)

### Mode A root cause — FOUND and reproduced (2026-07-27T13:20Z)

- [FACT] Root cause location: `commit_coordinator.py` lines 396-435. The commit path is: `commit-tree` (line 396, creates object) → freshness barrier (line 415, checks HEAD) → `update-ref` (line 430, links to ref).
- [FACT] The race window: between `commit-tree` (line 396) and `update-ref` (line 430), the freshness barrier at line 415 re-checks HEAD. If HEAD moved (sibling session committed), the function returns `COMMIT_OBJECT_CREATED_CAS_FAILED` with `commit_sha = new_commit[:12]` — but `update-ref` is never reached, so the commit object dangles.
- [FACT] Reproduction: `P:/tmp/trace_mode_a.py` simulated a sibling commit between `commit-tree` and `update-ref`. Result: commit object `ff49fac6ef1f` created, NOT in `git log --all`, IS in `cat-file -t` → confirmed dangling. `COMMIT_OBJECT_CREATED_CAS_FAILED` returned with the dangling SHA.
- [FACT] Close coordinator propagation bug: `close_coordinator.py` line 423 `commit_sha=rr.commit_sha or ""` copies the dangling SHA into `RepoCloseResult` regardless of `result_state`. Line 381 correctly marks `local_state = PERSISTENCE_BLOCKED` for non-COMMITTED states, but the `commit_sha` field still contains the phantom SHA.
- [INFERENCE] This explains all 3 Mode A occurrences: P:\ (`268cc357be75`), P:\ worktree (`eff9bc3`), ~/.grok (`0c4cd3e`) — all were created during concurrent sibling session activity on the shared working tree.
- [INFERENCE] The deterministic tests don't catch this because they run in isolation (no concurrent commits), so the freshness barrier never triggers.

### Mode B root cause — FOUND (2026-07-27T13:48Z)

- [FACT] The entire `P:/worktrees/phase3-acc/` worktree has been DELETED. The child and parent repos no longer exist — their object stores are gone. (Verified 2026-07-27T13:48Z: `Test-Path "P:/worktrees/phase3-acc"` → False; not in `git worktree list` for either P:\ or ~/.grok)
- [FACT] When I first checked at 12:58Z, the child repo existed with HEAD still at `2d713a3` (the initial commit from setup). B4 never moved the child's HEAD.
- [FACT] B5 (`submodule_coordinator.py`) does NOT independently commit the child. It relies on B4 committing the child first (`close_coordinator.py` line 220: `skip_child_commit=True`). If B4 fails (line 179: `if rr.result_state != cc.COMMITTED: continue`), B5 is never invoked.
- [INFERENCE] Mode B is the SAME root cause as Mode A: B4's freshness barrier triggered on the child repo (concurrent HEAD movement or stale HEAD), returned `COMMIT_OBJECT_CREATED_CAS_FAILED`, child repo was skipped by the close coordinator. The claimed child/parent SHAs were either dangling objects (now destroyed by worktree deletion) or fabricated by the reporting session.
- [FACT] The evidence was destroyed by worktree cleanup between my first verification (12:58Z) and the current check (13:48Z). Future acceptance tests must NOT clean up test repos until results are independently verified.
- [INFERENCE] The B5 parent commit path (`submodule_coordinator.py` lines 333-387) has the SAME freshness-barrier race window as B4 (line 362 checks HEAD before `update-ref` at line 368). Even if B4 had committed the child, B5 could fail the same way on the parent.

### Both modes — same root cause, same fix

Mode A and Mode B are the same defect: the freshness barrier between `commit-tree` and `update-ref` creates dangling commits when HEAD moves concurrently. The fix for INV-CAS-01 addresses both modes.

## Current state

### What's proven working

- Stop-hook lifecycle (block → obligation → verify → allow) — proven live
- Verification receipt system (scope, capability, nonce, fingerprint) — proven live
- Concurrent-session isolation (5 properties) — proven live with real second session
- Stale-output filtering — proven against live receipt state
- Deterministic test suite — 21/21 pass

### What's broken

- B4 CAS commit engine creates commit objects but does not reliably link them to refs (session 1 P:\, session 2 P:\ and ~/.grok — 3 of 5 claimed commits are dangling)
- B5 submodule coordinator reported `SUBMODULE_COMPLETE` with a gitlink SHA matching a commit that **does not exist** in the child repo (session 2 — 2 of 5 claimed commits never created)
- The close coordinator reports `PARTIAL_PERSISTENCE` / `LOCALLY_COMMITTED` / `SUBMODULE_COMPLETE` states that do not match actual git state
- The deterministic tests do not catch this because they test B4/B5 in isolation against temporary repos, not against the real multi-repo live path

## Task packets

### INV-CAS-01: Diagnose dangling-commit failure mode

- **goal:** Determine why B4 creates commit objects but fails to update refs
- **in scope:** `commit_coordinator.py` CAS path, specifically the post-commit ref update and shared-index sync
- **out of scope:** B5 submodule path (separate task), Stop-hook gate, verification receipts
- **files / anchors:** `commit_coordinator.py` — find the ref-update logic after CAS commit creation; `COMMITTED_INDEX_SYNC_FAILED` state handling
- **acceptance:** Reproduce the dangling-commit condition in a controlled test, then prove the fix produces a commit linked to a ref (verifiable via `git log --oneline | grep <sha>`)
- **falsifier:** After the fix, a live /close produces a commit SHA that `git log --all --oneline` can find. If the SHA still only appears in `git cat-file -t` but not in `git log`, the fix failed.
- **verification level required:** LIVE_BEHAVIOR (unit tests already pass; the failure is in the live path)
- **no_live_run_reason:** N/A — live run is the point

### INV-CAS-02: Diagnose non-existent-commit failure mode (child/parent)

- **goal:** Determine why B5 reported `SUBMODULE_COMPLETE` with a gitlink to a commit that was never created in the child repo
- **in scope:** `submodule_coordinator.py` child commit path, `close_coordinator.py` B5 invocation, the result-aggregation path that reports `SUBMODULE_COMPLETE`
- **out of scope:** Ordinary repo CAS (INV-CAS-01), Stop-hook, verification
- **files / anchors:** `submodule_coordinator.py` — child commit creation; `close_coordinator.py` `_reconcile_submodule_parents()` — how B5 result is aggregated
- **acceptance:** Prove whether the child commit was ever attempted (check for error swallowing), or whether the SHA was synthesized without a git operation. Reproduce in a controlled test.
- **falsifier:** After investigation, a live /close against a child repo produces a commit that `git -C <child> cat-file -t <sha>` confirms exists AND `git -C <child> log --oneline` confirms is in a ref.
- **verification level required:** LIVE_BEHAVIOR

### INV-CAS-03: Close coordinator result-vs-reality reconciliation

- **goal:** Add a post-commit verification step to the close coordinator that confirms claimed commits exist in refs before reporting `COMMITTED` / `LOCALLY_COMMITTED` / `SUBMODULE_COMPLETE`
- **in scope:** `close_coordinator.py` result aggregation, after B4/B5 return
- **out of scope:** Fixing B4/B5 themselves (INV-CAS-01/02)
- **files / anchors:** `close_coordinator.py` — the section that builds `RepoCloseResult` from B4 output
- **acceptance:** The close coordinator downgrades `COMMITTED` to `COMMIT_VERIFICATION_FAILED` when `git -C <repo> log --oneline | grep <sha>` returns empty
- **falsifier:** A dangling commit (object exists but not in ref) is reported as `COMMIT_VERIFICATION_FAILED`, not `COMMITTED`
- **verification level required:** UNIT_TEST (can be tested by mocking B4 output with a non-existent SHA)

### INV-CAS-04: Extend deterministic suite to catch the live failure

- **goal:** Add a test that runs the full B3→B4→B5 path against a real temporary git repo and verifies commits land in refs (not just objects)
- **in scope:** New test file in `P:/worktrees/dotgrok-phase3/hooks/scripts/tests/`
- **out of scope:** Modifying existing tests
- **files / anchors:** New `test_cas_ref_linkage.py`
- **acceptance:** The test fails against the current B4 code (reproducing the live failure) and passes after the fix
- **falsifier:** The test passes against current code despite the live failure → the test doesn't reproduce the condition
- **verification level required:** LIVE_BEHAVIOR

## Open decisions

### Decision 1: Is the dangling-commit issue a CAS design flaw or a concurrency race?

- **Question:** Does B4's private-index CAS design inherently produce dangling commits under concurrent HEAD movement, or is there a specific bug in the ref-update path?
- **Options:**
  - (A) Design flaw: private-index CAS cannot atomically update refs under concurrent writes → need a different commit strategy (e.g., `git commit` directly instead of CAS + manual ref update)
  - (B) Bug: the ref-update path has a specific error (e.g., wrong ref name, lock handling failure, gitdir resolution error on worktrees)
  - (C) Concurrency race: HEAD moves between CAS commit creation and ref update → need retry-with-HEAD-check logic
- **Selection criterion:** Root-cause accuracy (fix the actual mechanism, not the symptom)
- **Currently leads:** (B) Bug — because session 2's child/parent commits don't exist at ALL, which is more than a race condition would explain
- **Evidence that would change lead:** If code inspection shows the ref-update path is correct but races on HEAD, (C) becomes more likely

### Decision 2: Should the close coordinator trust B4/B5 results or verify them?

- **Question:** Should `close_coordinator.py` independently verify commit existence before reporting success?
- **Options:**
  - (A) Trust B4/B5 (current behavior) — they're supposed to be authoritative
  - (B) Verify after B4/B5 return — defense in depth, catches both bugs and races
  - (C) Verify and retry — if verification fails, retry the commit once before reporting failure
- **Selection criterion:** Reliability vs complexity. The current trust model has failed twice; verification adds ~10ms per repo.
- **Currently leads:** (B) Verify — the cost is trivial, the failure is recurring

## Hard constraints

1. The deterministic suite (21/21) must continue to pass after any fix
2. The Stop-hook gate, verification receipt system, and concurrent-session isolation must remain unaffected
3. No destructive git operations (`reset --hard`, `push --force`) during investigation
4. The close coordinator's conservative blocking (refusing to commit with blocked candidates) is correct behavior — do not weaken it
5. Any fix must handle the worktree case (shared object store, separate HEAD) and the standalone-repo case (child/parent)

## Cross-reference couplings

- `P:/docs/handoffs/phase3-current-state.md` → this handoff's parent. If Phase 3 acceptance is re-attempted, this investigation's findings determine whether the acceptance can proceed.
- `commit_coordinator.py` `COMMITTED_INDEX_SYNC_FAILED` state → the honest-failure path. If this state is being reported but then overridden by the close coordinator's aggregation, the coupling is broken.
- `submodule_coordinator.py` `SUBMODULE_COMPLETE` result → consumed by `close_coordinator.py` `_reconcile_submodule_parents()`. If B5 reports complete without verifying the child commit exists, the coupling is broken.
- `accurate_as_of_head: 4471f2c5` → if HEAD moves, re-verify that the claimed dangling commits are still dangling (git GC may clean them).

## Failure-mode catalog

### Mode A: Dangling commit (object exists, not in ref)

- **Mechanism:** B4 CAS creates the commit object via `git commit-tree` (or similar), but the subsequent ref update (`git update-ref` or shared-index sync) fails silently or is skipped
- **Isolation impact:** The commit is invisible to `git log`, `git status`, and any tool that reads refs. The session believes it committed; reality says otherwise.
- **Stale-data impact:** The dangling commit will be cleaned by `git gc` eventually, destroying the evidence. Investigation must happen before GC.
- **Occurrences:** Session 1 P:\ (`268cc357be75`), Session 2 P:\ (`eff9bc3`), Session 2 ~/.grok (`0c4cd3e`)
- **Detection gap:** The deterministic tests create temporary repos and may not exercise the ref-update path, or may not verify ref linkage after commit

### Mode B: Non-existent commit (object never created)

- **Mechanism:** B5 (or the close coordinator's B5 invocation) reported a commit SHA that was never created. Either the git operation was never run, the SHA was synthesized from expected state rather than actual output, or an error was swallowed.
- **Isolation impact:** The child repo is unchanged. The parent's gitlink points to a non-existent commit. If the parent gitlink WERE updated, `git submodule status` would fail.
- **Stale-data impact:** No object to clean — the SHA is a phantom. The only evidence is the close coordinator's output log.
- **Occurrences:** Session 2 child (`c3fb5b1`), Session 2 parent (`6c7f7a4`)
- **Detection gap:** This is more serious than Mode A — it means the result-aggregation path can report success for operations that never happened. The deterministic tests for B5 may mock the child commit rather than running it live.

### Mode C: Result-reality mismatch (close coordinator reports success for failed persistence)

- **Mechanism:** The close coordinator trusts B4/B5 return values without independent verification. When B4/B5 report success (or when their output is misinterpreted), the coordinator reports `COMMITTED` / `LOCALLY_COMMITTED` / `SUBMODULE_COMPLETE` regardless of actual git state.
- **Isolation impact:** Sessions believe their work is persisted. The handoff records commit SHAs that don't exist. Downstream consumers (wiki promotion, `/check`, next session) trust phantom commits.
- **Stale-data impact:** Phantom commits propagate into handoffs, wiki concepts, and AARs. The contamination spreads.
- **Occurrences:** Both sessions — the handoffs at `574b0bf` and `05beb57` both contain phantom commit SHAs
- **Detection gap:** No verification step exists between "B4/B5 returned" and "report to caller"

## Other outstanding streams (not handed off)

- **Phase 3 live acceptance re-run** — blocked on this investigation. Once B4/B5 produce verifiable commits, the acceptance can proceed with the fresh-session prompt already prepared.
- **Test-state cleanup** — P:\ and ~/.grok have accumulated test pollution (`_p2a_*`, `_p2b_*`, `_fin_*`, `_acc_*` files). Separate operator task per Part 6 spec.
- **Workspace fast-path misidentification** — design finding from session 019fa23d: `resolve_path_identity_from_workspace` uses workspace root for all nested files. Unverified; related to this investigation but not blocking.

## Explicit non-goals

- Do NOT re-run Phase 3 live acceptance until B4/B5 produce verifiable commits — that would produce more phantom evidence
- Do NOT modify the Stop-hook gate, verification receipt system, or candidate resolver — they're proven working
- Do NOT clean up test pollution during this investigation — preserve evidence
- Do NOT delete dangling commits — they are the primary evidence for Mode A
- Do NOT assume the deterministic tests are sufficient — they pass while live fails; the gap IS the investigation

## Resumption protocol

1. Read `commit_coordinator.py` — find the CAS commit creation path and the ref-update path. Document which git commands are used and where errors could be swallowed.
2. Read `submodule_coordinator.py` — find the child commit creation path. Determine whether `git -C <child> commit` is actually invoked or whether the SHA is synthesized.
3. Read `close_coordinator.py` — find where `RepoCloseResult` is built from B4/B5 output. Confirm whether any post-commit verification exists.
4. Reproduce Mode A: create a test that runs B4 against a real temp repo and checks `git log --oneline` (not just `git cat-file`)
5. Reproduce Mode B: create a test that runs B5 against a real child repo and checks the child commit exists in the child repo's refs
6. Based on findings, implement the fix (likely INV-CAS-01 or INV-CAS-03 first)

## Suggested next invocation

```
/go Investigate B4 CAS persistence failure — commits dangle or don't exist in live acceptance

Read P:/docs/handoffs/phase3-cas-persistence-investigation-20260727/HANDOFF.md first.

Two failure modes:
1. Mode A (dangling): commit object created but ref never updated. 3 occurrences across 2 sessions.
2. Mode B (non-existent): commit SHA reported but object never created. 2 occurrences in session 2 (child + parent).

Start with code inspection of commit_coordinator.py (CAS path + ref update) and submodule_coordinator.py (child commit path). Then reproduce both modes in controlled tests against real git repos. Do NOT trust the deterministic suite — it passes while live fails.

Verify every claimed commit against `git -C <repo> log --oneline | grep <sha>` (not `cat-file`). A commit in `cat-file` but not in `log` is dangling = Mode A. A commit not in `cat-file` at all = Mode B.
```

## Last user message (verbatim)

> /handoff " that pattern warrants its own investigation."

(Referring to the prior assistant message's closing line: "The persistence layer (B4 CAS + B5 reconciliation) in particular has now failed to produce verifiable commits in two separate acceptance attempts — that pattern warrants its own investigation.")

## Epistemic labels

- [FACT] All commit SHA existence claims verified via `git cat-file -t` and `git log --all --oneline` against the actual repos on 2026-07-27
- [FACT] The deterministic suite passes (21/21) — verified twice this session
- [INFERENCE] The likely root cause for Mode A is a ref-update failure after CAS commit creation — based on the `COMMITTED_INDEX_SYNC_FAILED` state existing in the code, which suggests the developers knew this path could fail
- [INFERENCE] The likely root cause for Mode B is either error swallowing in the B5 child-commit path or SHA synthesis without git invocation — based on the commit not existing at all, which rules out a simple ref-update race
- [UNKNOWN] Whether the deterministic tests exercise the ref-update path at all — requires reading `test_b4_commit.py` and `test_b4_live.py` to confirm
- [UNKNOWN] Whether the close coordinator has any post-commit verification — requires reading `close_coordinator.py` result aggregation path
- [UNKNOWN] Whether the worktree's shared object store confuses B4's ref resolution — the P:\ worktree shares objects with P:\ main but has a separate HEAD; this could cause ref updates to land on the wrong ref
