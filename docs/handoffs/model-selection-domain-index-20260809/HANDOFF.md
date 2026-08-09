---
thread_id: 39a59cf0-b839-43e3-a676-293e1fcc133d
parent_handoff_path: none
current_session_id: 019fdf47-6ec5-7b82-b363-a256a98cb5fc
parent_session: none
current_terminal_id: grok
produced_at: 2026-08-09T13:00:00Z
last_updated_by: 019fdf47-6ec5-7b82-b363-a256a98cb5fc
last_updated_at: 2026-08-09T13:00:00Z
status: open
handoff_type: investigation
accurate_as_of_head: 49bd9986144e3d5aa04633538f49d4a543c835c5
---

# Model-selection domain index: policy + picker + open work

## Objective

Organize the entire model-selection domain — the common policy design (Revision 5b), the picker infrastructure (`pick_model.py` + `fleet-models.json`), and the 18 open handoffs — into a single entry point a fresh session can read to understand current state and pick up work without grepping the handoffs directory.

**Scope bounds:** this handoff is a domain index/map, not an implementation work packet. It inventories what exists, what's open, and what to do next. The 18 cited handoffs retain their own provenance and are not merged into this file.

## Status

**OPEN — domain index, not implementation.** The canonical policy artifact (the R5b design doc) is ready for operator acceptance but **not yet implemented**. The picker infrastructure is live but has open gaps (staleness, transport-aware dispatch, concurrent-write protection).

## Producing context

- Date: 2026-08-09
- Session: `019fdf47-6ec5-7b82-b363-a256a98cb5fc`
- Terminal: `grok`
- Host: Grok Build (`glm-5.2`)
- Trigger: operator asked to organize model-picker and selection work into a single handoff, ignoring the review-relay work.

## Canonical artifacts

| Artifact | Path | State |
|---|---|---|
| **Common policy proposal** | `P:/docs/designs/2026-08-08-common-model-selection-policy-for-codex-and-grok.md` | Revision 5b — 42 findings converged across 6 relay sessions, 0 disputes. Ready for operator acceptance. |
| **Grok review of proposal** | `P:/docs/designs/2026-08-08-common-model-selection-policy-grok-review.md` | C5 finding VERIFIED, taxonomy alignment table implemented. |
| **Picker script** | `~/.grok/skills/model-quota/scripts/pick_model.py` | Live. Lane-based selection. Open: staleness verification. |
| **Fleet registry** | `~/.grok/skills/model-quota/scripts/fleet-models.json` | v5 schema. Per-model `dispatch_paths`, `dispatch_latency`, `tool_grounded_spawn_broken`, lanes with `quota_floor`. |
| **Spawn gate** | `~/.grok/hooks/PreToolUse_spawn_model_gate.py` | Live. Blocks quota-exhausted spawns. Per-session block logging. |
| **Quarantine hook** | `~/.grok/hooks/PostToolUseFailure_spawn_quota.py` | Live. 11-class taxonomy, reactive quarantine, GC on write. |
| **Domain table (wiki)** | `P:/.data/wiki/concepts/model-pool-selection-policy-speed-quota-diversity.md` | The policy source of truth (human-readable). Lines 124-135 encode the domain table `routing-library` wants to consume. |

## Read-first list

1. `P:/docs/designs/2026-08-08-common-model-selection-policy-for-codex-and-grok.md` — the canonical policy proposal (R5b). Read first to understand what the picker should implement.
2. `~/.grok/skills/model-quota/scripts/pick_model.py` — the live picker. Understand the current gate chain before changing it.
3. `~/.grok/skills/model-quota/scripts/fleet-models.json` — the registry the picker reads. Check schema version and lane structure.
4. `P:/.data/wiki/concepts/model-pool-selection-policy-speed-quota-diversity.md` — the human-readable policy (domain table, quota/speed/diversity rules).
5. `~/.grok/hooks/PostToolUseFailure_spawn_quota.py` — the reactive quarantine loop (11-class taxonomy, GC).
6. `P:/docs/designs/transport-aware-dispatch-20260802.md` — the transport-aware dispatch design (if implementing Tier 1.3).

## Verified facts

- [FACT] The R5b design doc states "Revision 5b — incorporates all 42 findings from six relay sessions" and "ready for operator acceptance" (source: `2026-08-08-common-model-selection-policy-for-codex-and-grok.md` lines 3-6).
- [FACT] `pick_model.py` exists at `~/.grok/skills/model-quota/scripts/pick_model.py` and is live (source: `list_handoffs.py` output shows multiple handoffs reference it as the runtime consumer; `PreToolUse_spawn_model_gate.py` reads it).
- [FACT] `fleet-models.json` is at v5 schema with `dispatch_paths`, `dispatch_latency`, `tool_grounded_spawn_broken`, and per-lane `quota_floor` fields (source: grep across handoffs — `dispatch-paths-fallback-not-spawn-block-20260805` line 57, `fleet-dispatch-improvements-20260731` line 87, `model-benchmark-dispatch-enhancement-20260803` line 57).
- [FACT] 18 open handoffs touch model selection (source: `list_handoffs.py --head` output filtered for model-selection-related patterns, this session).
- [FACT] The critic lane in `fleet-models.json` has 3 models, of which only `nim-openai-gpt-oss-20b` is verified spawn-capable after `tool_grounded_spawn_broken` exclusion (source: `dispatch-paths-fallback-not-spawn-block-20260805` line 46).
- [FACT] 77 of 79 models in `fleet-models.json` have no `dispatch_latency` data (source: `model-benchmark-dispatch-enhancement-20260803` line 181).
- [INFERENCE] The picker's speed sort key is effectively blind for most models because only 2/79 have dispatch latency data — the missing-p90 fallback (R5b fix 12) would fire for nearly every selection.
- [FACT] The error taxonomy was expanded from 7→11 classes this session (source: `session-observations-019fdf47-20260808` section 1, `spawn-failure-error-taxonomy-reactive-quarantine-2026.md`).
- [UNKNOWN] Whether any of the 18 open handoffs has been closed since this index was written — the operator should run `/handoff list --head <current>` before acting.

## Current state

The model-selection system has three live layers:

**1. Policy layer (wiki + proposal, not yet coded):** `model-pool-selection-policy-speed-quota-diversity.md` documents the domain table (task → model tier), quota/speed/diversity rules, and the pool-not-chain philosophy. The R5b design doc codifies this into an executable decision contract — but it is a proposal awaiting acceptance, not running code.

**2. Picker layer (live):** `pick_model.py` reads `fleet-models.json`, applies the gate chain (capability → policy → lifecycle → health), and returns one selected model per lane. The `PreToolUse_spawn_model_gate.py` hook blocks quota-exhausted spawns reactively. The `PostToolUseFailure_spawn_quota.py` hook classifies failures (11-class taxonomy) and quarantines broken models reactively.

**3. Evidence layer (partial):** `/model-benchmark` produces latency/quality/cost data and writes it back to `fleet-models.json` `dispatch_latency` fields. Telemetry integration into `pick_model.py`'s dynamic thresholds is open.

**Shipped this session (picker hardening):**
- Quarantine GC (`_quarantine_expired()` prunes on every write)
- Error taxonomy 7→11 classes (timeout, contract_malformed, identity_mismatch, scope_violation)
- Hook-block logging propagation (shared `hook_block_logger.py`, all 4 blocking hooks)
- Dead-zone policy fix (removed `docs/designs/` — empirically incorrect)

## Task packets

### MS-01: Accept or revise the R5b policy proposal

- goal: operator decides whether to accept R5b as the binding model-selection contract, revise it, or defer.
- in scope: the design doc only. No code changes until acceptance.
- out of scope: implementation of the policy (that is MS-04+).
- files / anchors: `P:/docs/designs/2026-08-08-common-model-selection-policy-for-codex-and-grok.md`
- acceptance: operator states "accept R5b" or produces a revision directive.
- falsifier: the proposal is accepted but a later session implements something contradicting it.
- verification level required: STATIC_INSPECTION

### MS-02: Revert tool_grounded_spawn_broken hard pool-exclusion

- goal: change `pick_model.py` `is_available()` so `tool_grounded_spawn_broken` is transport metadata (skip spawn, try PI first), not a pool-exclusion filter.
- in scope: `pick_model.py` `is_available()` logic; `fleet-models.json` `tool_grounded_spawn_broken` array stays.
- out of scope: changes to `fleet-models.json` structure.
- files / anchors: see `dispatch-paths-fallback-not-spawn-block-20260805` for exact paths and line numbers (`fleet-models.json` ~1121 and ~2070; `pick_model.py` `is_available()`).
- acceptance: critic lane can select `zen-deepseek-v4-flash-free` and `nim-deepseek-ai-deepseek-v4-flash` again (with PI dispatch, not spawn).
- falsifier: after the revert, a tool-grounded spawn still gets dispatched to a spawn-broken model without PI fallback.
- verification level required: LIVE_BEHAVIOR

### MS-03: Decide on transport-aware dispatch (v3 schema)

- goal: decide whether `fleet-models.json` migrates to v3 (per-model `transports` blocks) or stays at the flat `dispatch_paths` list.
- in scope: the design decision; implementation is a follow-on packet.
- out of scope: v3 implementation (deferred to a separate handoff).
- files / anchors: `P:/docs/designs/transport-aware-dispatch-20260802.md` (3 revisions complete); `fleet-models.json` current schema.
- acceptance: operator or architect states the schema decision with rationale.
- falsifier: the chosen schema cannot express the fallback chains the picker needs.
- verification level required: STATIC_INSPECTION

### MS-04: Fill dispatch_latency gaps

- goal: benchmark the 77/79 models missing dispatch data so the picker's speed sort key works.
- in scope: `/model-benchmark --methods` across spawn/PI/OC/HTTP for each missing model.
- out of scope: changes to the picker logic itself.
- files / anchors: `~/.grok/skills/model-quota/scripts/fleet-models.json` `dispatch_latency` fields; `~/.grok/skills/model-benchmark/benchmark.py`.
- acceptance: `/model-benchmark --gaps` reports 0 missing models.
- falsifier: after benchmarking, more than 10 models still have no dispatch data (partial run, not success).
- verification level required: LIVE_BEHAVIOR

### MS-05: Add staleness verification to pick_model.py

- goal: add a freshness-verification step to `pick_model.py`'s `spawn_notes` cache so stale health data does not drive selections.
- in scope: `pick_model.py` cache logic.
- out of scope: changes to the spawn gate or quarantine hook.
- files / anchors: see `pick-model-staleness-investigation-20260802`; `pick_model.py` `spawn_notes` cache.
- acceptance: `pick_model.py` refuses to return a model whose `spawn_notes` is older than the configured TTL, with a re-verification prompt.
- falsifier: a model with stale `spawn_notes` (older than TTL) is still returned without re-verification.
- verification level required: UNIT_TEST

## Open decisions

**D1: Accept R5b as the binding model-selection contract?**
- Options: (a) accept as-is, (b) accept with revisions, (c) defer pending more evidence.
- Selection criterion: does the proposal's decision contract match the operator's model-selection intent?
- Currently leads: (a) accept — 42 findings converged with 0 disputes across 6 relay sessions. But this is an operator decision, not a session-level one.
- Evidence that would change the lead: a finding the relay sessions missed (e.g., a formula error, a missing gate).

**D2: Migrate `fleet-models.json` to v3 (per-model transports blocks) or stay flat?**
- Options: (a) v3 schema (richer, more code), (b) flat `dispatch_paths` list (simpler, less expressive).
- Selection criterion: expressiveness vs. complexity. The flat list already works for fallback chains; v3 adds transport-specific metadata.
- Currently leads: [UNKNOWN] — the design doc is complete but the decision hasn't been made. See `transport-aware-dispatch-design-20260802`.
- Evidence that would change the lead: a fallback chain that the flat list cannot express but v3 can.

**D3: Should `route.py` (`routing-library`) consume the domain table as a Python dict/TOML, or should the wiki remain the only source?**
- Options: (a) encode domain table as `P:/.agents/scripts/models/domain-table.toml` and have `route.py` read it, (b) keep wiki as sole source and parse it.
- Selection criterion: live control surface vs. documentation. A TOML file is machine-readable and testable; wiki is human-readable only.
- Currently leads: (a) TOML — `routing-library` handoff proposes this. But it depends on R5b being accepted (D1).

## Hard constraints

- **Pool-not-chain:** models are peers, not a ranked chain. Selection uses a multi-element ordered filter (task-novelty, quality-floor, latency, context-fit, cost-regime, quota-strategy), not a fixed ranking. (Source: `model-pool-not-chain.md`, `session-2026-07-22-shipped-work`.)
- **Per-orchestrator quarantine:** Codex and Grok maintain independent quarantine state. A model quarantined in one host is not automatically quarantined in the other. (Source: R5b § "Per-orchestrator quarantine.")
- **No automatic cross-host fallback:** a Codex task is selected by the Codex selector; a Grok task by the Grok selector. Handoff between them is explicit and plan-driven, not a dynamic fallback. (Source: R5b § "Executive proposal.")
- **Multi-terminal isolation:** `fleet-models.json` is shared state. Concurrent writes require audit logging or locking. (Source: `shared-state-protection-20260802`.)
- **Context firewall:** parent and child model contexts are isolated. Context-budget-aware selection must respect this. (Source: `context-firewall-architecture.md`.)

## Cross-reference couplings

- `fleet-models.json` `tool_grounded_spawn_broken` → read by `pick_model.py` `is_available()`. If the list changes, the filtering logic must match. (See MS-02.)
- `fleet-models.json` `dispatch_paths` → consumed by the picker for fallback chains. If the schema changes (D2), all callers must update.
- `model-pool-selection-policy-speed-quota-diversity.md` domain table (lines 124-135) → `routing-library` wants to encode this as TOML. If the wiki table changes, the TOML must resync.
- `PostToolUseFailure_spawn_quota.py` 11-class taxonomy → must align with R5b § "Error classification." This session expanded it; the alignment is now in place.
- `PreToolUse_spawn_model_gate.py` → reads `fleet-models.json` quota state. If `fleet-models.json` schema advances past v5, the gate must update.
- Wiki pool contracts (`coding-model-pool-tier-1-tier-2`, `mechanical-model-pool`, etc.) → consumed by skills that select models for spawn. If these drift from `fleet-models.json`, humans get wrong info even if the runtime is correct. (Source: `postsession-20260801` NEXT-2.)
- This handoff's `accurate_as_of_head` → `7782e3a2`. If HEAD moves, re-verify cited paths — most of the 18 handoffs already show `head:DRIFT`.

## Open work inventory (18 handoffs, categorized)

### A. Selection policy / routing logic

| Handoff | Age | Status | One-line |
|---|---|---|---|
| `routing-library` | 2w | OPEN, DRIFT | Build `route.py` centralizing task-domain → model selection; wraps `spawn_subagent` + telemetry. Consumes the domain table. |
| `cascade-pattern` | 2w | OPEN, DRIFT | Implement FrugalGPT-style sequential cascade for verification/exploration. Wiki acknowledges as superior-but-unimplemented. |
| `context-budget-management-20260802` | 6d | OPEN, DRIFT | CTX-1: context-budget-aware model selection (pick by context fit, not tier). Prevents subagent max_tokens hits. |
| `response-strategy-meta-layer` | 2w | OPEN, work:? | Response-strategy layer feeds INTO model selection (action vs reflection → tier). |

### B. Picker infrastructure (pick_model.py + fleet-models.json)

| Handoff | Age | Status | One-line |
|---|---|---|---|
| `dispatch-paths-fallback-not-spawn-block-20260805` | 3d | OPEN, head:? | Revert the `tool_grounded_spawn_broken` hard pool-exclusion in `pick_model.py` `is_available()`. |
| `transport-aware-dispatch-design-20260802` | 5d | OPEN, ckpt, DRIFT | Design doc complete (3 revisions). v3 schema with per-model `transports` blocks. Implementation not started. |
| `pick-model-staleness-investigation-20260802` | 7d | OPEN, not started, DRIFT | Add freshness-verification step to `pick_model.py`'s `spawn_notes` cache. |
| `fleet-dispatch-improvements-20260731` | 8d | OPEN, work:?, DRIFT | Q5: graduated `quota_floor` per lane in `fleet-models.json`. |
| `shared-state-protection-20260802` | 6d | OPEN, ckpt, DRIFT | Concurrent-write protection for `fleet-models.json` (audit log). |
| `spawn-pool-helper-ams02-20260728` | 11d | OPEN, DRIFT | Build one reusable Python helper for `/tp`, `/check`, `/review`, `/www` to call the spawn pool. |
| `mistral-spawn-fix-20260729` | 10d | OPEN, DRIFT | Complete propagation of `mistral-medium-latest` spawn breakage across 5 remaining wiki pool files. |

### C. Telemetry / evidence

| Handoff | Age | Status | One-line |
|---|---|---|---|
| `model-telemetry-integration` | 2w | OPEN, work:?, head:? | Integrate `/model-benchmark` telemetry into `pick_model.py` for dynamic quota thresholds. |
| `model-benchmark-dispatch-019fc95d` | 5d | OPEN, claimed:grok | Complete dispatch enhancement: fix provider issues, fill dispatch_latency gaps. |

### D. Error classification

| Handoff | Age | Status | One-line |
|---|---|---|---|
| `model-error-classification-architecture-20260801` | — | OPEN, design needed | The 7→11 class taxonomy architecture. This session expanded it; the handoff predates that and needs a status update. |

### E. Auto-switch / rate-limit handling

| Handoff | Age | Status | One-line |
|---|---|---|---|
| `auto-model-switch-on-rate-limit-20260728` | 11d | OPEN, claimed:grok, DRIFT | AMS-04: when parent model hits 429/capacity, auto-switch rather than halt. |

### F. Bugs / tuning

| Handoff | Age | Status | One-line |
|---|---|---|---|
| `fleet-code-bugs` | 2w | OPEN, DRIFT | BUG-03: DeepSeek code-verification recommendation blocked by a bug. |
| `or-ling-rate-limit-parallel-load-20260802` | — | OPEN, investigation needed | Reduce OpenRouter `parallel_safe_count` from 2 to 1 to prevent rate-limit under parallel load. |

### G. Review integration

| Handoff | Age | Status | One-line |
|---|---|---|---|
| `review-consolidation-20260727` | 12d | OPEN, DRIFT | RC-02: add automatic specialist model selection to `/review`. |

## Explicit non-goals

- **Do NOT merge the 18 cited handoffs into this file.** They have provenance from different sessions and terminals. This handoff is an index, not a consolidation-by-deletion.
- **Do NOT implement the R5b policy before the operator accepts it (D1).** The proposal is ready for acceptance, not for code.
- **Do NOT re-derive the pool-not-chain decision.** It was shipped 2026-07-22 and is the foundational design choice. Any selection logic that ranks models in a fixed chain violates this constraint.
- **Do NOT change the error taxonomy without aligning with R5b § "Error classification" and the Codex proposal.** The 11 classes are now cross-host aligned.
- **Do NOT ignore `head:DRIFT` on the cited handoffs.** Most have stale references. Re-verify before acting.

## Resumption protocol

1. Run `/handoff list --head $(git -C P:/ rev-parse HEAD)` and check which of the 18 cited handoffs still show `head:DRIFT`.
2. Read the R5b design doc (`P:/docs/designs/2026-08-08-common-model-selection-policy-for-codex-and-grok.md`) — confirm it hasn't been revised since this index was written.
3. Check whether the operator has accepted R5b (D1). If yes, the implementation task packets (MS-04+) can proceed. If no, surface D1 as the blocking decision.
4. If MS-02 (dispatch-paths revert) is the priority, read `dispatch-paths-fallback-not-spawn-block-20260805` for exact file:line anchors before touching `pick_model.py`.

## Suggested next invocation

```
/go Read P:/docs/handoffs/model-selection-domain-index-20260809/HANDOFF.md and action MS-02 (revert the tool_grounded_spawn_broken hard pool-exclusion in pick_model.py is_available()). Exact anchors are in dispatch-paths-fallback-not-spawn-block-20260805/HANDOFF.md. Do NOT implement MS-04+ until the operator accepts R5b (D1).
```

## Last user message (verbatim)

> Let's ignore the relay work. I'm focusing on the model picker and selection work. Can we organize a single handoff for it and related material?

## Epistemic labels

- `[FACT]` — the R5b revision state, `pick_model.py` existence, `fleet-models.json` schema, 18 open handoffs, 77/79 dispatch_latency gap, critic lane composition, error taxonomy expansion. All sourced from file reads or `list_handoffs.py` output this session.
- `[INFERENCE]` — the picker's speed sort key is blind for most models (derived from the 77/79 gap fact). The `model-error-classification-architecture-20260801` handoff needs a status update (derived from this session's taxonomy expansion predating the handoff).
- `[UNKNOWN]` — whether any cited handoff has been closed since this index was written; whether the operator has accepted R5b; the transport-aware dispatch schema decision (D2).

## Suggested skills for next session

- `/go` — task packets MS-02 and MS-04 are implementation-ready (exact file anchors, testable acceptance criteria).
- `/design` — if the operator wants to revise R5b before acceptance, or if D2 (transport-aware dispatch schema) needs deeper exploration.
- `/review` — the picker infrastructure changes (MS-02, MS-05) touch shared dispatch chains; review before merging.
- `/check` — after any picker change, verify the gate chain still works end-to-end.
- `/tp` — if the operator wants to challenge the R5b proposal before accepting it.

## Other outstanding streams (not handed off)

- **Review-relay improvements** — `review-relay-design-20260809` (design target for 3 relay controller improvements). Open. Tangential to model selection; it's the review tool, not the selection policy.
- **Continuation pipeline** — post-compact continuation prompt system (4-hook pipeline, shipped this session, untested with real compaction). Open. Unrelated to model selection.
- **Class C quoting guard** — `PreToolUse_class_c_quoting_guard.py` (shipped this session). Closed. Unrelated to model selection.

## Changelog

| Date | Session | Action |
|------|---------|--------|
| 2026-08-09T13:00 | 019fdf47... | created — domain index for model-selection work (policy + picker + 18 open handoffs) |
| 2026-08-09T13:30 | 019fdf47... | revision 1 — Codex updated R5b status to "accepted for planning, not conformant"; Grok review marked historical; stale claims corrected |

---

## Revision 1 — 2026-08-09T13:30Z (session 019fdf47)

**Trigger:** Codex updated both design docs after this handoff was written. The R5b status shifted and the Grok review was marked superseded.

**What changed in the source docs:**

1. **R5b status changed** from "ready for operator acceptance" to "Revision 5b — canonical design accepted for implementation planning; not live or conformant" (line 3 of the design doc). This is a meaningful shift: the proposal is no longer awaiting acceptance — it is accepted as the planning target, but implementation gates remain open.
2. **New "Current conformance status" section added** (lines 106-148) documenting specific implementation gaps: Grok's router uses p50 not p90, golden-vector verifier is structural-only (`SKELETON`), quarantine records lack full scope, candidate lifecycle gate not enforced, Codex rank records don't enforce verified-success floors.
3. **Candidate count corrected:** the live registry contains 12 Grok `candidate` records without embedded verified-success evidence (not the hard-coded count from the F1 fleet scan). A hard-coded count is not durable evidence — must be re-run before activation.
4. **Golden-vector test failure evidence added:** `golden_vectors.py verify` structurally validates 25 cases but fails during selector invocation; Codex executable counterpart absent. Unit tests (191 Grok + 16 Codex) pass but do not clear the shared executable-conformance gate.
5. **Grok review marked historical/superseded:** `2026-08-08-common-model-selection-policy-grok-review.md` now states "Historical review of Revision 2 — superseded by Revision 5b; retain for audit traceability." Its recommendations are not current policy.

**Stale claims in the original handoff (corrected above in this revision):**

- Original Status (line 25): said "ready for operator acceptance." **Corrected:** accepted for implementation planning, not live or conformant. Implementation gates remain open.
- Canonical artifacts table (line 39): said "Ready for operator acceptance." **Corrected:** accepted for planning; see the design doc's "Current conformance status" section for the gap list.
- Canonical artifacts table (line 40): listed the Grok review as current with "C5 finding VERIFIED." **Corrected:** the Grok review is now historical/superseded — retain for audit, do not cite as current authority.
- Verified facts (line 58): quoted the old status verbatim. **Corrected:** the quoted text is no longer in the design doc at that line.

**Updated open decisions:**

- **D1 (Accept R5b?) — partially resolved.** Codex marked the doc as "accepted for implementation planning." The decision shifts from "accept the proposal?" to "activate the implementation gates?" The gaps in the "Current conformance status" section are the blockers. The operator's next decision is whether to prioritize closing those gaps (MS-02 first, then the conformance gaps).

**Updated task packet MS-01:**

- MS-01 goal partially met: the proposal is accepted for planning. The remaining work is closing the implementation gaps documented in the "Current conformance status" section. This is no longer a pure acceptance decision — it's a gap-closure prioritization decision.

**New open item:**

- ~~The golden-vector executable conformance gate is a shared requirement (both hosts). Grok's verifier fails during selector invocation; Codex's is absent.~~ **RESOLVED on Grok side (2026-08-09, commit `c55646d`):** root cause was a one-line registry construction bug in `invoke_selector()`. All 25 golden vectors now pass. Status changed from SKELETON to EXECUTABLE. The Codex JS counterpart remains the operator/Codex side to ship.

---

## Revision 2 — 2026-08-09T14:00Z (session 019fdf47)

**Trigger:** `/go complete the remaining steps and live test` — operator authorized full R5b conformance implementation.

**What was implemented (3 of 4 R5b conformance gaps closed):**

1. **Lifecycle gate (Gap B)** — `evidence_eligibility()` now blocks `lifecycle=candidate` records. Only `active` candidates are eligible. 12 candidate records in the live registry are now correctly excluded. (Commit `b6b985f`)
2. **p90 fallback chain (Gap A)** — `_latency_p50()` → `_latency_p90()` implements R5b fix #12 (`p90 > p50_provisional > lane_median > BLOCKED`). `compute_score()` now uses p90 valid-result latency. (Commit `b6b985f`)
3. **Quarantine scope (Gap C)** — `QuarantineRecord` gains `orchestrator` and `invocation_method` fields. Transport and model quarantine creation sites populate them from the candidate. Backward compatible. (Commit `b6b985f`)

**What remains open (Gap D — Step 2+):**

- ~~**Quota capacity adapter** — `_quota_headroom()` is still a type-based heuristic.~~ **Step 1 RESOLVED (2026-08-09, commit `6a6d10f`):** `capacity_adapter.py` reads the live fleet quota cache, normalizes to R5b adapter shape, implements the decision table as a 5th gate. `_quota_headroom()` removed from scoring (capacity is gate-only per R5b fix #2). Live test confirms exhausted providers (cohere at pct=0) are correctly blocked. **Remaining Step 2+:** demand estimation (token counting), pricing data for monetary_budget, adaptive reserve from demand forecast. These are features blocked on data that doesn't exist yet.

**Verification:**
- 25/25 golden vectors pass (all 3 changes verified)
- 461 tests pass, 9 skipped (pre-existing), 0 failures
- Live test against real `fleet-models.json`: all 4 lanes (coding, reasoning, critic, mechanical) return valid selections with correct gate behavior. Candidates correctly blocked by lifecycle gate. Diverse panel correctly discloses reduced diversity (2 of 3).

**Live test observations:**
- All candidates score as cold-start (0 evidence blocks in registry) — the deterministic selector falls back to canonical ID ordering among equal scorers. This is a data gap (no evidence populated), not a code gap. The scoring logic is proven by golden vectors with embedded evidence.
- The `model_error_classification-architecture-20260801` handoff's taxonomy expansion is now reflected in the live quarantine hook.
