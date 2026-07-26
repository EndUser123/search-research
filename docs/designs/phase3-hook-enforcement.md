# Phase 3 Hook Enforcement System — Authoritative Specification

This document is the durable contract. It describes what must remain true,
not the implementation history. Source files are cited by repository-relative
path from the integration worktree root.

## 1. Purpose, scope, and non-goals

**Purpose:** provide path-specific repository identity, schema-v2 mutation
receipts, read-only candidate resolution, private-index CAS commit engine,
submodule child-parent reconciliation, verification enforcement with
continuation obligations, and session-close coordination for Grok Build.

**Scope:** the hooks/scripts/ Python modules that implement the enforcement
and persistence pipeline. The pipeline runs from mutation detection
(PreToolUse/PostToolUse) through verification gating (Stop) to session
close (/close).

**Non-goals:** auto-push, remote publication, CI/CD integration, cross-host
synchronization, or replacing Git itself. This system produces local commits
only and never pushes.

## 2. Safety invariants

- Never: reset, clean, stash, globally stage, force checkout, overwrite
  unrelated files, commit foreign-session files, auto-push, claim
  publication without proof, or infer ownership from Git dirtiness, mtime,
  or file proximity.
- Preserve unrelated: staged files, unstaged files, untracked files,
  repository branches, shared indexes, background processes, foreign receipts.
- All persistence operations use private temporary Git indexes, not the
  shared working index. The shared index is touched ONLY for post-CAS
  synchronization of committed paths (see §10).
- Failures are represented honestly. A commit that did not land is not
  reported as committed. A sync that failed is reported as
  COMMITTED_INDEX_SYNC_FAILED.

*Source: `hooks/scripts/commit_coordinator.py` (B4), `hooks/scripts/close_coordinator.py` (B6)*

## 3. Session, run, repository, and worktree authority

- **Session ID** from the runtime payload is the ownership authority. No
  other field may substitute for it.
- **Repository identity is path-specific.** Each file path resolves to its
  own repository root, repository ID, worktree ID, and HEAD SHA via
  `hooks/scripts/path_identity.py`.
- **`workspaceRoot` is contextual metadata**, not repository authority.
  It is used only as a search optimization hint, never as identity proof.
- **Verification receipts and mutation receipts are separate evidence types**
  and must remain separate throughout the pipeline.

*Source: `hooks/scripts/path_identity.py`*

## 4. Mutation receipt contract

Schema version 2.0. Required fields per receipt:

- `schema_version`: "2.0"
- `receipt_id`: unique per receipt
- `session_id`: the owning session
- `tool_name`: the tool that produced the mutation
- `workspace`: contextual workspace path
- `head`: HEAD SHA at mutation time
- `operation_status`: "success" | "failed" | "partial"
- `changed_files[]`: per-file record with:
  - `path`, `canonical_path`, `change_type`
  - `pre_hash`, `post_hash`
  - `ownership_status`: "provisionally_owned" | "ambiguous"
  - `repository_root`, `repository_id`, `worktree_id`
  - `git_relative_path`, `resolution_status`, `identity_source`

Canonical wire statuses: `RESOLVED` | `AMBIGUOUS` | `OUTSIDE_GIT` |
`LEGACY_RECONSTRUCTED` | `MISMATCH`. Readers accept historical long-form
aliases via `normalize_resolution_status()`.

*Source: `hooks/scripts/mutation_receipt.py`, `hooks/scripts/path_identity.py`*

## 5. Verification receipt contract

Verification receipts distinguish claimed scope from observed state:

- `claimed_scope_refs`: paths the verifier claims to have covered
- `observed_state_refs`: paths whose fingerprints were actually checked
- `scope_basis`: must be an approved basis (EXPLICIT_PATH_ARGUMENT,
  TEST_TO_SOURCE_MAPPING, REPOSITORY_WIDE_VERIFIER, OPERATOR_DECLARED_SCOPE)
- `verifier_capability`: syntax | import | static_analysis | unit_behavior |
  integration_behavior | runtime_hook | repository_suite
- `obligation_nonce`: causal link to the continuation obligation
- `scope_fingerprint_at_execution`: fingerprint of observed paths at run time

A receipt satisfies an obligation only when: nonce matches, claimed scope
covers all blocked paths, observed state covers all blocked paths, identity
matches, scope basis is approved, capability is sufficient, and fingerprint
is current.

*Source: `hooks/scripts/quality_gate.py` (`_check_obligation_satisfied`),
`hooks/scripts/verification_receipt_writer.py`*

## 6. Continuation-obligation contract

When the Stop gate blocks (code modified + completion claimed + no
verification), it writes a continuation obligation:

- `session_id`, `status`: "PENDING"
- `nonce`: UUID for causal ordering
- `blocked_paths[]`, `blocked_fingerprints{}`
- `reason_code`, `required_capability`
- `identity`: repository/worktree snapshot

The obligation persists until a matching VERIFICATION_SUCCEEDED receipt
satisfies it. The nonce binds the receipt to the obligation causally —
a receipt without a matching nonce cannot clear the obligation.

*Source: `hooks/scripts/quality_gate.py` (`_write_obligation`, `_read_obligation`,
`_clear_obligation`)*

## 7. Enforcement-health and compatibility contract

**Stable API:** `quality_gate.get_verification_enforcement_status(session_id)`
returns `VerificationEnforcementStatus` with:

- `contract_version`: "1.0"
- `implementation_version`: identifies the hook version
- `enforcement_status`: one of the states below
- `obligation_status`, `health_status`, `health_reason`
- `obligation_reads_authoritative`, `receipt_reads_authoritative`
- `compatibility_status`

**Enforcement-health states:**
- `ENFORCEMENT_AVAILABLE` — enforcement is healthy and authoritative
- `ENFORCEMENT_HEALTH_UNKNOWN` — cannot determine health
- `ENFORCEMENT_UNAVAILABLE` — obligation subsystem reported failure
- `ENFORCEMENT_CORRUPT` — obligation state is corrupt
- `INCOMPATIBLE_VERSION` — hook version does not match expected contract

**Rule:** `/close` may proceed ONLY when `enforcement_status ==
ENFORCEMENT_AVAILABLE` AND both `*_authoritative` flags are True.
Missing API → `INCOMPATIBLE_VERSION` → close BLOCKS. No fail-open.

*Source: `hooks/scripts/quality_gate.py`, `hooks/scripts/verification_status_adapter.py`*

## 8. Candidate resolution

Every relevant target-session path appears in exactly one category:

### Eligible
All checks pass: identity resolved, HEAD coherent, fingerprint matches,
foreign scan complete with no match, operation order proven, ownership
status not ambiguous, operation succeeded.

### Blocked
Path is session-owned but cannot currently commit. Blocked candidates
carry structured evidence:
- `session_id`, `canonical_path`, `git_relative_path`
- `repository_root`, `repository_id`, `worktree_id`
- `source_receipt_ids[]`
- `expected_head`, `current_head`
- `expected_fingerprint`, `current_fingerprint`
- `reason_codes[]`, `eligibility`
- `retryability`: RETRYABLE | RETRY_AFTER_HEAD_SYNC | RETRY_AFTER_RESCAN | NOT_RETRYABLE
- `required_next_action`: human-readable next step

Blocking conditions: CURRENT_HEAD_MOVED, EXPECTED_HEAD_CONFLICT,
HEAD_EVIDENCE_UNAVAILABLE, stale fingerprint, unresolved identity,
FOREIGN_OVERLAP, FOREIGN_SCAN_INCOMPLETE, SHELL_WRITE_AMBIGUOUS,
OPERATION_ORDER_UNPROVEN, FAILED_OPERATION, PARTIAL_OPERATION,
deferred parent Git-link dependency.

### Excluded
Proven irrelevant to the target session: FAILED_OPERATION,
PARTIAL_OPERATION, NO_SESSION_OWNED_CHANGE, OUTSIDE_GIT,
LEGACY_IDENTITY_UNPROVEN. A path is NOT excluded merely because it
cannot currently commit.

*Source: `hooks/scripts/candidate_resolver.py`*
*Tests: `hooks/scripts/tests/test_b2_b3.py`, `test_b3_acceptance.py`,
`test_defect_fixes.py`*

## 9. Private-index and CAS persistence

The commit engine uses a private temporary Git index (GIT_INDEX_FILE)
seeded from the expected HEAD via `read-tree`. Only approved candidate
paths are staged via `update-index --add` or `--force-remove`.

Steps: read-tree → update-index (exact paths) → write-tree → diff-tree
(scope verification) → commit-tree → freshness check → update-ref CAS.

The CAS uses `update-ref refs/heads/<branch> <new> <expected-old>`,
which atomically rejects if the branch has moved since expected-old.

*Source: `hooks/scripts/commit_coordinator.py`*
*Tests: `hooks/scripts/tests/test_b4_commit.py`, `test_cas_race.py`*

## 10. Post-CAS shared-index semantics

After successful branch CAS, committed paths are synchronized into the
shared index via `update-index --add` for each committed path. This makes
committed files clean relative to the new HEAD.

Properties:
- Only committed paths are synchronized
- Unrelated staged blobs remain unchanged
- Unrelated unstaged and untracked files remain unchanged
- No working-tree file is overwritten
- Lock contention is retried (4 attempts with backoff)
- If sync fails after retries: `COMMITTED_INDEX_SYNC_FAILED` (commit is in
  the ref but shared index doesn't reflect it; overall state is PARTIAL)

*Source: `hooks/scripts/commit_coordinator.py`*

## 11. Multi-repository partial outcomes

When committing across multiple repositories in one operation:
- Each repository commits independently via private index + CAS
- Per-repository results are collected (COMMITTED, BLOCKED_*, NO_CANDIDATES)
- Partial outcomes are represented honestly: SUCCESS | PARTIAL | BLOCKED | NO_CANDIDATES
- A repository with any required blocked candidate reports blocked or partial
- No repository failure rolls back another repository's success

*Source: `hooks/scripts/commit_coordinator.py` (`commit_multi_repository`)*

## 12. Submodule child and parent Git-link reconciliation

When a target session owns an eligible submodule-child mutation:

1. Child persistence is attempted via B4
2. Parent Git-link reconciliation is REQUIRED (Design A: coordinator-owned)
3. B5 result is included in the same close result
4. Child success + parent failure → PARTIAL_PERSISTENCE
5. LOCALLY_COMMITTED is NOT returned when a parent Git-link is unreconciled
6. SESSION_CLOSED is impossible until the parent Git-link is reconciled
7. Retry processes only the unresolved parent operation (skip_child_commit=True)
8. Publication remains separate from local persistence

The B5 coordinator (`submodule_coordinator.commit_submodule`) resolves
parent identity, derives the Git-link candidate, updates the parent's
private index with `update-index --cacheinfo 160000,<sha>,<path>`, and
performs parent CAS. The close coordinator calls B5 directly — no
separate orchestrator needed.

*Source: `hooks/scripts/submodule_coordinator.py`, `hooks/scripts/close_coordinator.py`
(`_reconcile_submodule_parents`)*
*Tests: `hooks/scripts/tests/test_b5_submodule.py`, `test_b5_live.py`,
`test_cas_race.py`, `test_e2e_close_b5.py`*

## 13. Authoritative `/close` call sequence

```
close_coordinator.run_close_persistence(session_id)
  1. Validate target session (non-empty session_id)
  2. Evaluate authoritative verification state via adapter
  3. STOP immediately if verification blocks
  4. Run B3 candidate resolution (eligible + blocked + excluded)
  5. Retain blocked candidates (do not silently drop)
  6. Commit eligible ordinary repositories through B4
  7. Reconcile child/parent dependencies through B5 (coordinator-owned)
  8. Aggregate partial or blocked persistence
  9. Compute local/upstream/publication state per repository
  10. Return session-close status
```

*Source: `hooks/scripts/close_coordinator.py`*

## 14. Session-close truthfulness requirements

`SESSION_CLOSED` requires ALL of:
- Verification accepted (or no obligation)
- No pending obligation
- No required blocked candidate
- All required local persistence complete
- Every child-parent dependency reconciled
- No enforcement-unavailable condition

`LOCALLY_COMMITTED` requires: all eligible committed AND no blocked
candidates AND no unreconciled submodule parents.

`PARTIAL_PERSISTENCE`: some committed, some blocked or B5 partial.

`PERSISTENCE_BLOCKED`: nothing committed, all blocked.

No session may close with pending obligations, unresolved paths, partial
persistence, or unreconciled parent Git-links.

*Source: `hooks/scripts/close_coordinator.py`*

## 15. Local persistence versus publication

- Local commit is reported via `local_persistence_state`: LOCALLY_COMMITTED | PERSISTENCE_BLOCKED
- Publication is reported via `publication_state`: REMOTE_PUBLICATION_PENDING | UPSTREAM_UNKNOWN | PUSH_VERIFIED | PUSH_UNAUTHORIZED | PUSH_FAILED
- The two are SEPARATE fields, never conflated
- PUSH_VERIFIED is only reachable through an explicit push operation (which this system does NOT perform)
- A local commit with no upstream reports UPSTREAM_UNKNOWN, not PUSH_VERIFIED
- No auto-push path exists anywhere in the codebase

*Source: `hooks/scripts/close_coordinator.py`*

## 16. Concurrent-session and stale-evidence isolation

- Session ID is the isolation key for ALL state (receipts, obligations, candidates)
- Receipt files are session-scoped: `mutation-receipts-<session_id>.jsonl`,
  `quality-receipts-<session_id>/`, `quality-obligation-<session_id>.json`
- A stale session's receipts are never read by a current session's resolver
- Foreign receipts are indexed once per run; same-path overlap blocks
- Identical foreign final content does NOT transfer ownership
- Stale or superseded task output cannot: create current mutation ownership,
  become verification evidence, satisfy verification scope, clear an
  obligation, block current Stop processing, or become /close evidence

*Source: `hooks/scripts/candidate_resolver.py`, `hooks/scripts/quality_gate.py`*
*Tests: `hooks/scripts/tests/test_concurrent_isolation.py`, `test_stale_isolation.py`*

## 17. Deployment and rollback invariants

- The 10 production files form an atomic deployment set (cross-imports)
- All files must deploy together; mixed versions cause import failure or
  incorrect behavior
- Deployment creates a full backup of the destination before writing
- Each deployed file is hash-verified post-copy
- Partial failure triggers automatic rollback from backup
- Rollback removes only newly-introduced Phase 3 files absent from the backup
- Rollback does not use git reset, stash, clean, or checkout
- `worktree_identity.py` is an unchanged pre-existing dependency (not in the
  atomic set but required by `quality_gate.py` and `verification_receipt_writer.py`)
- Python `__pycache__` is cleared after deployment
- A fresh session is required to activate the new hooks

*Source: `hooks/scripts/tests/DEPLOYMENT_MANIFEST.json`,
`hooks/scripts/tests/Deploy-Phase3.ps1`*

## 18. Deterministic and live acceptance criteria

### Deterministic (must all pass from the integration worktree)

- Path identity resolution (all statuses, submodule detection, normalization)
- Interface acceptance (schema compliance across components)
- B2/B3 legacy receipt compatibility + candidate resolution
- B3 acceptance (blocked-candidate surfacing, retryability, exclusion rules)
- B4 private-index commit (CAS, scope verification, post-CAS sync)
- B4 live disposable acceptance (real P:\ and ~/.grok repos)
- B5 submodule child-parent (CAS race, retry, parent identity)
- B5 live submodule acceptance (real git submodule checkout)
- B6 close coordinator (verification gate, blocked evidence, B5 integration)
- B6 expanded (14 scenarios, 32+ checks)
- CAS race injection + retry proofs
- Concurrent-session isolation (deterministic)
- Stale-output isolation (mutation + verification sides)
- Quality gate Phase 2 (receipt coverage, capability, nonce)
- Scope/capability/nonce checks
- Continuation obligation
- A+B identity compatibility
- Workstream A hardening (13 pytest tests)
- Defect fixes (HEAD-moved surfacing, verification gate, evidence retention)
- Mixed-state health (10 scenarios: incompatible, corrupt, partial, stale)
- E2E close + B5 (18 scenarios through authoritative /close path)

### Live (operator-run, post-deployment, fresh session)

1. Mutate one harmless path in each: P:\, ~/.grok, disposable submodule
2. Claim completion without verification → Stop hook blocks
3. Capture the pending obligation
4. Prove all paths have: canonical path, repository ID, worktree ID,
   fingerprint, required capability, nonce
5. Verify paths one at a time (P:\ → ~/.grok → child)
6. Claim completion after each → Stop blocks until all verified
7. After verification allows → invoke /close
8. Prove: commits only approved paths, updates parent Git-link, retains
   per-repository evidence, reports local vs publication separately, no push

## 19. Verdict vocabulary

### Enforcement-health states
`ENFORCEMENT_AVAILABLE` | `ENFORCEMENT_HEALTH_UNKNOWN` |
`ENFORCEMENT_UNAVAILABLE` | `ENFORCEMENT_CORRUPT` | `INCOMPATIBLE_VERSION`

### Verification decisions
`VERIFICATION_ACCEPTED` | `VERIFICATION_BLOCKED` |
`VERIFICATION_NO_OBLIGATION` | `VERIFICATION_ENFORCEMENT_UNAVAILABLE` |
`VERIFICATION_CORRUPT` | `VERIFICATION_WRONG_SESSION` |
`VERIFICATION_INCOMPATIBLE` | `VERIFICATION_HEALTH_UNKNOWN`

### Close states
`SESSION_CLOSED` | `LOCALLY_COMMITTED` | `PARTIAL_PERSISTENCE` |
`PERSISTENCE_BLOCKED` | `VERIFICATION_BLOCKED` |
`VERIFICATION_INCOMPATIBLE` | `VERIFICATION_HEALTH_UNKNOWN` |
`SESSION_CLOSE_BLOCKED`

### Publication states
`REMOTE_PUBLICATION_PENDING` | `UPSTREAM_UNKNOWN` |
`PUSH_VERIFIED` | `PUSH_UNAUTHORIZED` | `PUSH_FAILED`

### Submodule states
`SUBMODULE_COMPLETE` | `SUBMODULE_CHILD_ONLY` | `SUBMODULE_PARENT_ONLY` |
`SUBMODULE_BLOCKED` | `SUBMODULE_NO_CHILD_CANDIDATES` |
`SUBMODULE_PARENT_UNRESOLVED`

### Commit result states
`COMMITTED` | `COMMITTED_INDEX_SYNC_FAILED` |
`COMMIT_OBJECT_CREATED_CAS_FAILED` | `COMMIT_FAILED` | `NO_CANDIDATES` |
various `BLOCKED_*` states for specific failure conditions

### Candidate eligibility states
`ELIGIBLE` | `CURRENT_HEAD_MOVED` | `EXPECTED_HEAD_CONFLICT` |
`HEAD_EVIDENCE_UNAVAILABLE` | `CURRENT_FINGERPRINT_MISMATCH` |
`STALE_RECEIPT` | `FOREIGN_OVERLAP` | `FOREIGN_SCAN_INCOMPLETE` |
`SHELL_WRITE_AMBIGUOUS` | `OPERATION_ORDER_UNPROVEN` |
`FAILED_OPERATION` | `PARTIAL_OPERATION` | `OUTSIDE_GIT` |
`NO_SESSION_OWNED_CHANGE` | `LEGACY_IDENTITY_UNPROVEN` |
`AMBIGUOUS_IDENTITY` | `DELETED_PATH_UNRESOLVED` |
`REPOSITORY_ID_MISMATCH` | `WORKTREE_ID_MISMATCH`
