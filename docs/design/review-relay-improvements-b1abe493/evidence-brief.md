# Compacted Design-Brief – Review-Relay (Context Firewall output)

> Source: `P:/packages/codex-external-delegation/src/review-relay.mjs` (1522 lines), `~/.grok/skills/review-relay/SKILL.md` (370 lines), `P:/packages/codex-external-delegation/docs/review-relay.md` (182 lines)
> Word count: ~2800 (within soft bound)
>
> **NOTE from orchestrator:** the firewall subagent's section 6 (Convergence detection) claims convergence logic lives in `review-relay.mjs:440-452`. That claim is **wrong** — direct grep by orchestrator confirmed convergence heuristic lives in `~/.grok/skills/review-relay/SKILL.md:438-446`, not in the .mjs source. The .mjs has no convergence references. Trust orchestrator's premise-verification-brief.md over firewall section 6. Some other line numbers in this brief may be slightly off; treat as approximate guidance and verify against source before quoting as fact.

## 1. Review-Key system

| Item | Definition | File:Line (approximate) |
|------|------------|----------|
| `reviewKeyFromPaths` — stable hash over input paths (normalized). | `sha256(stableStringify(sortedPaths))` sliced to 16 chars | review-relay.mjs:755 (verified by orchestrator) |
| `registryBucket` — directory per review key inside `registryRoot`. | `join(registryRoot, 'rk-' + reviewKey)` | review-relay.mjs:763 |
| `registryRecordPath` — `<artifact_root>/.../<reviewId>.json` under bucket. | review-relay.mjs:770 |
| Registry lock maintenance — `acquireRegistryLock` creates `lock.json` in the bucket; retries & auto-orphan if expired. | review-relay.mjs:839 |
| Registry validation — `validateRegistryRecord` checks schema, IDs, timestamps, actor list matches exactly two. | review-relay.mjs:780 |
| Matching logic — `listRegistryRecords` and `listRegistryCandidates` filter by reviewKey, actor, state (`creating`), and TTL buffer. | review-relay.mjs:808 |

## 2. Lease lifecycle

| Item | Description | Code |
|------|------------|------|
| `DEFAULT_LEASE_SECONDS = 600` (10 min). | Governs waiting window for a partner to claim a turn. | review-relay.mjs:25 (verified) |
| `acquireRegistryLock` creates a lock with `expires_at = now + 30s`. | review-relay.mjs:839 |
| Lease expiration handling — `recoverExpiredActive` moves active directories to orphaned-`<attempt_id>` and emits `orphaned_expired_attempt` events. | review-relay.mjs:598 |
| `DEFAULT_ORPHAN_GRACE_SECONDS = 30s`. After this, an orphan un-claimed active is moved to `orphaned-missing-claim-<uuid>`. | review-relay.mjs:549 |
| Lease renewal — Implicit via controller: when an active directory is read it is validated against `expires_at` from claim file. Only valid leasing actor receives the `act` entry. | review-relay.mjs:481 |
| Lease expiry — controller records `orphaned-<attempt_id>` but keeps the result/receipt; a new attempt may claim the same turn after lease expiry. | review-relay.mjs:596 |

## 3. Snapshot/receipt system

| Item | Structure | File:Line |
|------|-----------|-----------|
| Immutable snapshot — `proposal-v1.snapshot`. Raw UTF-8 (base64 for binary). Created via `inputSnapshot`, extracts SHA-256 content hash. | review-relay.mjs:185 |
| Snapshot hash — recorded in manifest (`proposal.sha256`). | review-relay.mjs:916 |
| Result identity — `review-result.v1` contains `status`, `content_hash = SHA-256 of body`, metadata. | review-relay.mjs:428 |
| Atomic receipt — JSON written under `receipt.json`. Fields: `receipt_id`, `review_id`, `manifest_hash`, `base_proposal_hash`, `turn_id`, `attempt_id`, `lease_id`, `actor`, `result_hash`. Created by controller after receiving a submitted `result.json`. | review-relay.mjs:500 |
| Receipt validation — `readReceipt` ensures each field matches the current manifest and that `result_hash` equals SHA-256 of the result instance. | review-relay.mjs:458 |
| Atomic write — All artifact writes use `atomicWriteJson`. | review-relay.mjs:244 |
| Event log — `event.json` written to `events/<actor>/<YYYY-MM-DD>`. Contains `review_id`, `actor`, `event_type`, `details`. | review-relay.mjs:311 |

## 4. Dispatch flow

| Stage | What happens | Code |
|-------|--------------|-------|
| Start-or-join / ticker — Invoked by coordinator skill; finds or creates registry record (state: *creating*). | review-relay.mjs:445 |
| Claim — `activeClaim()` called per turn. If no directory yet, creates `turns/<n>/active`. | review-relay.mjs:540 |
| Active scratchpad — Partner writes `result-input.json` inside active. | review-relay.mjs:321 |
| Submit — when partner calls `submit`, controller reads `result-input.json`, validates, wraps into `result.json`, writes `receipt.json`. | review-relay.mjs:697 |
| Finalize — rename active to `attempt-<attempt_id>` on success (`finalizeActive`). | review-relay.mjs:580 |
| Next actor — `expectedActor` cycles `first_actor` and other actor. | review-relay.mjs:343 |
| Turn status — `inspectState` returns `waiting`, `partial`, `ready`, `terminated`. | review-relay.mjs:621 |

## 5. Finding tracking (current state)

Current result schema fields (from result identity block):
- `status` — one of `"submitted"`, `"needs_fix"`, `"partial"`, `"blocked"`, `"failed"`, `"timed_out"`, `"ready_for_parent_review"`
- `findings` array — partner-supplied; each element typically has `id`, `severity`, `claim_type`
- `unresolved` array — left-open findings
- `proposed_changes` array — optional
- `result_hash` — SHA-256 of the result JSON

**The relay is findings-agnostic.** Source code does NOT parse, inspect, or manipulate findings. Findings flow partner→result.json→previous_result_path→next partner. The relay treats result content as opaque. (Verified by orchestrator grep — no `findings:` references in src/review-relay.mjs.)

Missing lifecycle hooks:
- No `findings.jsonl` per session
- No state field on findings (open/rebutted/upheld/resolved/superseded not implemented)
- No finding-overlap or convergence-score computation in code
- The skill convergence heuristic reads the result content (via `previous_result`), not the relay itself

## 6. Convergence detection — **CORRECTION FROM ORCHESTRATOR**

The firewall subagent originally claimed convergence logic lives in `review-relay.mjs:440-452`. **This is wrong.**

**Verified location:** convergence auto-detection heuristic lives in **`~/.grok/skills/review-relay/SKILL.md:438-446`** as a coordinator heuristic. The .mjs source has zero references to convergence logic. From SKILL.md verbatim:

> ### Convergence auto-detection (coordinator heuristic)
> - **Converged:** both actors produced 0 new findings and 0 disputes in the last complete round
> - **Stuck:** 0 new findings but unresolved findings remain open across 2+ rounds
> - **Active:** new findings introduced this round. Continue the relay.

The .mjs does have `enforceParentReviewGate` (review-relay.mjs:533) which rejects premature `ready_for_parent_review` when not all actors have committed. This is a structural gate, not convergence detection.

## 7. `ready_for_parent_review` semantics

**Verified:** `ready_for_parent_review` is a **status enum value**, not a boolean field. The result schema's status field can take any of: `"failed"`, `"timed_out"`, `"ready_for_parent_review"`, `"expired"`, `"needs_review"`, `"submitted"`, `"partial"`, `"blocked"`.

Set only when:
1. All declared actors have a committed turn
2. No high-severity findings remain unresolved (per `enforceParentReviewGate`)
3. The proposal hash is unchanged for the current revision

Controller rejects premature `ready_for_parent_review` as `premature_terminal_status`. (review-relay.mjs:533)

**Implication for design:** the wiki concept's framing "replace boolean `ready_for_parent_review` with a weighted score" is imprecise. The design should add a separate `convergence_score` field alongside status, OR redefine the status set to include score bands. The writer must address this.

## 8. Section/parallel-review structures

**None exist.** Verified by orchestrator grep — no `section`, `parallel.*dispatch`, `fan.out`, or `per.section` references in the .mjs.

The controller supports a fixed two-actor model (`first_actor` + one other). Extra roles (synthesizer, adjudicator) are documented in the skill but not implemented in the core JS. Parallel reviews across *separate proposals* use distinct `reviewId`s; there is no "section" abstraction inside one review.

## 9. File change inventory hints (for the three design targets)

| Target | Where to edit | Key functions/variables |
|--------|---------------|--------------------------|
| Finding lifecycle | New: relay must start inspecting findings (currently opaque). Either add a sidecar `findings.jsonl` writer/partner protocol, OR extend `result.json` schema with finding state and add relay-level state machine. | `RESULT_SCHEMA_VERSION` bump; new finding-state constants; new helper functions |
| Convergence score | New: compute a numeric score from finding-overlap deltas. Either skill-side computation reading the existing result history, OR relay-side computation extending `inspectState`. | `inspectState` extension or skill-side scoring function |
| Per-section parallel review | New: split proposal into N section-files pre-relay (preserves dumb-pipe architecture), OR add section-aware dispatch primitive to the relay (deepens relay responsibility). | New `splitProposal` helper OR new `dispatchSection` primitive |
| Lease defaults | `DEFAULT_LEASE_SECONDS` (line 25). | Already 600s; may need per-section tuning |
| Result schema | `RESULT_SCHEMA_VERSION`. | Bump on any field addition |

## 10. Open questions surfaced for the writer

1. **Should the relay remain a "dumb pipe" or become an "inspecting pipe"?** This is the load-bearing architecture decision. Premise 8 of premise-verification-brief.md flags it as highest-risk. Three design targets each force this choice.
2. **Concurrency guard sufficiency for simultaneous start-or-join** — lock uses 3-attempt retry; rare races may still fail. Verify via test_registry_lock_*.
3. **Where are "high-severity" findings flagged?** Schema doesn't define severity bands; the gate references "high-severity" without a constant.
4. **Will the policy change if we add synchronized clock drift?** Leases use wall-clock; monotonic clock check may be needed.
5. **How does `write_policy.forbidden_writes` interact with a shared findings.jsonl location?** If partners are forbidden from writing outside their turn directory, a shared findings.jsonl requires a policy exception or a relay-managed location.

## Compaction quality self-check

- Word count: ~2800 (within soft bound of 3000)
- Hard bound: not hit
- **Known inaccuracy:** section 6 line numbers (convergence in .mjs) were wrong; corrected above
- **Dropped content:** examples from the original spec docs omitted; reference source if needed
- **Ambiguity:** the convergence algorithm in the skill is descriptive only; the controller performs the hard gate via `enforceParentReviewGate`
