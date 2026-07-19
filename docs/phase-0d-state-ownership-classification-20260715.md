# Phase 0D: State Family Registration and Ownership Classification

**Date:** 2026-07-15
**Phase:** 0D — Discovery and classification only. No migrations, no consumers changed.
**Status:** READY for classification; NOT READY for consumer migration (pre-requisites remain).

---

## Executive Verdict

**NOT READY FOR CONSUMER MIGRATION.**

### Why not ready

| Blocking issue | Count | Impact |
|----------------|-------|--------|
| Many UNKNOWN state families lack identified producer/consumer chains | >40 subfamilies | Cannot establish canonical destination |
| **task_tracker split-brain confirmed** — local vs plugin diverge on status values | ~2,169 + ~994 files | Would replicate corruption if migrated |
| `.state/state/` (hooks/.state/state/) contains a nested copy of hooks/state/ content | ~141 files | Hidden duplicate root |
| Multiple plugin state dirs at `state/<plugin-name>/` where plugin owns the data model | ~9 plugin dirs | Plugin decoupling prerequisite unclear |
| No per-family cleanup/TTL policy exists for most families | Nearly all families | Migration would accumulate forever |

### Prerequisites for READY

1. Resolve task_tracker split-brain: establish one authoritative writer
2. Resolve `.state/state/` hidden duplicate: confirm source and clean up
3. Add cleanup/TTL policy to LOG, TRANSIENT, and CACHE families
4. Complete per-plugin scope registration for plugin-owned families
5. Build and verify the state-inventory regression test

---

## 1. State Family Inventory (Complete)

### Verified (resolver-registered) families

| Family | Category | Current root | Files | Status |
|--------|----------|-------------|-------|--------|
| investigation_state_console | TERMINAL | state/terminals/ | 116 | CANONICAL_CANDIDATE |
| pretool_degraded | TERMINAL | state/terminals/ | 64 | CANONICAL_CANDIDATE |
| lazy_closure_capitulation_console | TERMINAL | state/terminals/ | 31 | CANONICAL_CANDIDATE |
| delegation_expected | TERMINAL | state/terminals/ | 4 | CANONICAL_CANDIDATE |
| compaction_marker | SESSION | state/sessions/ | 12 | CANONICAL_CANDIDATE |
| auth_gate | SESSION | state/ | 637 | MIGRATION_CANDIDATE (→ sessions/) |
| terminal | SESSION | state/ | 11 | MIGRATION_CANDIDATE (→ sessions/) |
| session_ledger | SESSION_LEDGER | .session/ | 341 | CANONICAL_CANDIDATE |
| reasoning_metrics | SESSION_LEDGER | .session/ | 1 | CANONICAL_CANDIDATE |
| tool_use_log | LOG | hooks/.state/ | 340 | RESOLVED writer (see §2) |
| path_errors | LOG | hooks/.state/ | 298 | CANONICAL_CANDIDATE |
| negation_hits | LOG | hooks/.state/ | 43 | CANONICAL_CANDIDATE |
| referent_anchors | LOG | hooks/.state/ | 6 | CANONICAL_CANDIDATE |
| agentic_reliability_telemetry | LOG | hooks/.state/ | 3 | CANONICAL_CANDIDATE |
| claim_type | LOG | hooks/.state/ | 6 | CANONICAL_CANDIDATE |
| anti_sycophancy_injector | TERMINAL | hooks/state/ | ~50 | MIGRATION_CANDIDATE (→ state/terminals/) |
| followup_context | TERMINAL | hooks/state/ | 65 | MIGRATION_CANDIDATE (→ state/terminals/) |
| consultation_aware | TERMINAL | hooks/state/ | ~35 | MIGRATION_CANDIDATE (→ state/terminals/) |
| arch_declaration | TERMINAL | hooks/state/ | ~10 | MIGRATION_CANDIDATE (→ state/terminals/) |

### UNKNOWN families (need registration)

| Family | Root | Files | Producer | Consumer | Scope | Status |
|--------|------|-------|----------|----------|-------|--------|
| session_tldr | state/ | 3,159 | snapshot plugin SessionStart_tldr.py, snapshot_SessionEnd_tldr.py | snapshot tldr renderer | terminal | CANONICAL_CANDIDATE |
| task_tracker | state/ | 2,169 | PostToolUse_task_tracker.py → posttooluse/task_tracker_hook.py (local) | TaskList/TaskUpdate APIs, task_context_enhancement | terminal | **MIGRATION_BLOCKED** (split-brain) |
| cc-aca-observability | state/ | 1,001 | cc-aca-observability plugin | Plugin consumers | plugin | PLUGIN_OWNED |
| diagnostics | logs/ | 760 | Multiple Stop hooks | diagnostics viewer | shared | LEGACY_ACTIVE |
| model-router | state/ | 750 | cc-model-router plugin | Router state readers | terminal | PLUGIN_OWNED |
| prompt_session | state/ | 573 | cc-skills-sdlc skill_context | SessionStart injector | session | CANONICAL_CANDIDATE |
| tdd95 | state/ | 481 | tdd95_core.py | tdd95 phase machine | terminal | CANONICAL_CANDIDATE |
| skill_context | state/ | 223 | cc-skills-sdlc | Multiple hooks | session | CANONICAL_CANDIDATE |
| cc-aca-epistemic | state/ | 170 | cc-aca-epistemic plugin | Plugin consumers | plugin | PLUGIN_OWNED |
| handoff | state/ | 156 | cc-skills-sdlc/cc-skills-analysis | Handoff/snapshot consumers | terminal | CANONICAL_CANDIDATE |
| **.state/state/** | hooks/.state/ | **141** | **UNKNOWN — possible nested copy** | **UNKNOWN** | **SUSPICIOUS** | **UNKNOWN** |
| prompt_choice | state/ | 103 | cc-aca-epistemic prompt_choice_state.py | Prompt choice injector | session | CANONICAL_CANDIDATE |
| cks_context_injected | state/ | 98 | cks_context.py (UserPromptSubmit) | CKS context injector | session | CANONICAL_CANDIDATE |
| cc-lazy-closure-debt | state/ | 81 | cc-lazy-closure-debt plugin | Plugin consumers | terminal | PLUGIN_OWNED |
| recommendation_loop | state/ | 29 | recommendation_loop.py | Recommendation injector | session | CANONICAL_CANDIDATE |
| sessions (canonical) | state/ | 29 | state_paths.py | Multiple | session | CANONICAL_CANDIDATE |
| terminals (canonical) | state/ | 20 | state_paths.py | Multiple | terminal | CANONICAL_CANDIDATE |
| sqa_phase | state/ | 19 | posttooluse_sqa_phase_tracker.py | SQA phase machine | terminal | CANONICAL_CANDIDATE |
| logs | state/ | 18 | cc-aca-observability posttooluse | History/cleanup | shared | TRANSIENT |
| anti_sycophancy_injector | hooks/.state/ | 17 | anti_sycophancy_injector.py (deep subdir) | Same as hooks/state/ version | terminal | MIGRATION_CANDIDATE |
| constraints | state/ | 16 | session_constraints.py | Session constraint checks | session | CANONICAL_CANDIDATE |
| .state/(root) | hooks/.state/ | 14 | Ad-hoc files | Various | mixed | LEGACY_ACTIVE |
| anti_sycophancy_injector | state/ | 12 | cc-aca-epistemic plugin | Plugin injector | terminal | MIGRATION_CANDIDATE (duplicate root) |
| stop_recommendation_gate | state/ | 10 | cc-skills-sdlc | Stop recommendation gate | terminal | CANONICAL_CANDIDATE |
| observe_before_act | hooks/.state/ | 9 | observe_before_act gate | PreToolUse enforcement | terminal | CANONICAL_CANDIDATE |
| shared | state/ | 5 | state_paths.py | Shared state (hook_ledger.db) | shared | CANONICAL_CANDIDATE |
| v_findings | state/ | 4 | cc-skills-sdlc verification | Verification reporting | session | CANONICAL_CANDIDATE |
| local-model-crashes | state/ | 4 | Crash RCA runbook | Crash dossiers | repository | CANONICAL_CANDIDATE |
| auto_commit | state/ | 3 | cc-skills-utils Stop hook | Auto-commit state | terminal | CANONICAL_CANDIDATE |
| next_step_choice | state/ | 3 | cc-skills-analysis | Next step injector | session | CANONICAL_CANDIDATE |
| stop_meta_conversation | state/ | 3 | Stop_meta_conversation_loop.py | Meta conversation | session | CANONICAL_CANDIDATE |
| tdd | state/ | 3 | tdd_core.py | TDD phase | terminal | CANONICAL_CANDIDATE |
| chs_delta_reindex | state/ | 2 | SessionStart_chs_delta_reindex.py | CHS delta reindex | session | CANONICAL_CANDIDATE |
| edit_consent | state/ | 2 | edit_consent.py | Write consent tracking | terminal | CANONICAL_CANDIDATE |
| task_receipts | state/ | 2 | cc-skills-sdlc task_receipt.py | PreToolUse done-evidence gate | terminal | CANONICAL_CANDIDATE |
| local_summary_guidance | state/ | 2 | cc-skills-sdlc | Local summary guidance | terminal | CANONICAL_CANDIDATE |

---

## 2. Producer → Artifact → Consumer Evidence Map

### task_tracker

**PRODUCER (local):** `P:/.claude/hooks/posttooluse/task_tracker_hook.py`
- Called from PostToolUse_router.py (line 583: `track_tool_use(session_id_str, terminal_id_str, tool_name_raw, tool_input_raw)`)
- Also standalone `PostToolUse_task_tracker.py` (legacy file)
- Writes to: `state/task_tracker/{terminal_id}_tasks.json`

**PRODUCER (plugin):** `cc-aca-observability/__lib/posttooluse/task_tracker_hook.py`
- Writes to: `state/cc-aca-observability/task_tracker/{terminal_id}_tasks.json`

**CONSUMERS:**
- `cc-aca-observability/__lib/posttooluse/task_tracker_hook.py` (reads local to skip)
- `test_task_context_enhancement.py` (internal import for tests)

**CONFIRMED SPLIT-BRAIN:**
- Same terminal_id: `console_01f0572e-c0f1-4c0f-8bda-c61d4e653181`
- Same task IDs: 867, 868, 869, 870
- **Diverging status:** task #867 shows `local=in_progress` → `plugin=completed`
- Schema identical across both: `{terminal_id, tasks: {id: {id, subject, status, created_at, session_id, terminal_id}}}`

**Evidence:** `P:/tmp/phase0d-tt-compare.py` can reproduce on any terminal_id present in both roots.

### tool_use_log

**PRODUCER:** `cc-aca-observability/__lib/posttooluse/artifact_access_tracker.py`
- Writes to `hooks/.state/tool_use_log_{terminal_id}.jsonl`
- Append-only, rotates per session

**CONSUMER:** Not directly consumed by any hook. Historical artifact. The evidence system uses SQLite WAL (`evidence_store.py`, `hook_ledger.py`), not JSONL.

**SCHEMA:** `{ts, session_id, terminal_id, tool, accessed[]}` — file paths accessed by tool calls.

**LIFECYCLE:** No retention/cleanup. Files accumulate indefinitely. Session-scoped variants also exist (`tool_use_log_console_{tid}_{sid}.jsonl`).

### evidence artifacts (evidence_store.py)

**PRODUCER:** `P:/.claude/hooks/evidence_store.py` (SQLite WAL, NOT JSONL)
- `append_tool_event()` called from PostToolUse.py
- Primary store: `P:/.claude/state/evidence.db` (SQLite WAL, multi-terminal safe)
- Fallback: spool JSONL files

**CONSUMER:** Multiple Stop hooks via `tool_events_loader.py`, `turn_tool_events.py`, `hook_ledger.py`
- `evidence_store.get_active_turn()` — used by claim verification
- `tool_events_loader.load_tool_events_from_transcript()` — Stop gate consumption

**SCHEMA:** SQLite with `tool_events` table — `session_id`, `terminal_id`, `turn_id`, `tool_name`, `output_excerpt`, `success`, `ts`

**STATUS:** Already migrated from JSONL spool to SQLite WAL. No further migration needed.

### receipts

**PRODUCER:** `cc-skills-sdlc/skills/task/scripts/task_receipt.py`
- Terminal-scoped: `state/task_receipts/{task_id}.json`

**CONSUMER:** `PreToolUse_task_done_evidence_gate.py`
- Reads receipt at `receipt_path_for(task_id)` → validates completion claim

**LIFECYCLE:** No cleanup. Receipts persist indefinitely.

### read/search trackers (observe_before_act)

**PRODUCER:** `.claude/hooks/.state/observe_before_act/observe_gate_{terminal_id}_{session_id}.json`
- Written by observe_before_act PreToolUse gate

**CONSUMER:** **Itself** — the gate reads its own state file at the START of each turn to enforce search-before-modification

**ENFORCEMENT DEPENDENCY:** **YES** — this is a blocking gate. If state file is missing/corrupt, the gate cannot determine whether search occurred.

---

## 3. Ownership Classification

### By Owner

| Owner | Families | Notes |
|-------|----------|-------|
| **Local hooks** (`.claude/hooks/`) | auth_gate, terminal, path_errors, negation_hits, referent_anchors, claim_type, anti_sycophancy_injector, followup_context, consultation_aware, arch_declaration, observe_before_act, stop_meta_conversation, next_step_choice, edit_consent, constraints, tdd, tdd95, compaction_marker, investigation_state, pretool_degraded, lazy_closure_capitulation, delegation_expected | Core gate/injector state |
| **cc-aca-observability plugin** | task_tracker(+plugin root), tool_use_log, sqa_phase, logs, change_propagation, cleanup_tracker | Plugin-owned state (split-brain for task_tracker) |
| **cc-aca-epistemic plugin** | anti_sycophancy_injector (state/ root), prompt_choice, dependency_verification | Plugin-owned state |
| **cc-model-router plugin** | model-router | Plugin-owned state |
| **cc-skills-sdlc plugin** | task_receipts, stop_recommendation_gate, v_findings, recommendation_loop, prompt_session, skill_context, cks_context_injected, handoff | Plugin-owned state |
| **snapshot plugin** | session_tldr | Plugin-owned state |
| **cc-lazy-closure-debt plugin** | debt_store | Plugin-owned state |
| **cc-skills-utils plugin** | auto_commit | Plugin-owned state |
| **Claude Code CLI (built-in)** | session_ledger, reasoning_metrics | Built-in session management |
| **state_paths.py struct** | sessions/, terminals/, shared/ | Canonical structured subdirs |

### By Scope

| Scope | Families | Count |
|-------|----------|-------|
| terminal | task_tracker, tool_use_log, anti_sycophancy_injector, followup_context, consultation_aware, arch_declaration, investigation_state, pretool_degraded, lazy_closure, delegation_expected, tdd95, tdd, observe_before_act, stop_recommendation_gate, model-router (varies), session_tldr, debt_store | ~18 families |
| session | compaction_marker, auth_gate, prompt_session, skill_context, cks_context_injected, prompt_choice, constraints, recommendation_loop, stop_meta_conversation, next_step_choice, v_findings, chs_delta_reindex, terminal | ~13 families |
| shared | diagnostics (logs/), evidence store, hook_ledger, hook-health-summary | ~4 families |
| repository | local-model-crashes | 1 family |
| plugin | cc-aca-observability/*, cc-aca-epistemic/*, cc-aca-investigation, cc-model-router/*, cc-lazy-closure-debt/* | ~5 dirs |

### By Lifecycle

| Lifecycle | Families | Count |
|-----------|----------|-------|
| Permanent | task_tracker, tool_use_log, evidence_store, auth_gate, terminal | ~5 families |
| Session lifetime | compaction_marker, prompt_session, skill_context, cks_context_injected, prompt_choice, constraints, recommendation_loop | ~7 families |
| Terminal lifetime | anti_sycophancy_injector, followup_context, consultation_aware, arch_declaration, investigation_state, pretool_degraded, lazy_closure | ~7 families |
| TTL | diagnostics/stop_blocks, logs/hook-health-summary | ~2 families |
| Cache / regenerable | cks_cache, session_tldr (partial), rule_engine_cache | ~2 families |
| Disposable / no cleanup | tool_use_log, path_errors, negation_hits, referent_anchors | ~4 families |

### By Migration Readiness

| Status | Families | Count |
|--------|----------|-------|
| READY | session_tldr, tool_use_log, path_errors, negation_hits, referent_anchors, agentic_reliability_telemetry, anti_sycophancy_injector, followup_context, consultation_aware, arch_declaration, observe_before_act, receipts, prompt_session, skill_context, cks_context_injected, constraints, recommendation_loop, prompt_choice, stop_meta_conversation, next_step_choice, v_findings, chs_delta_reindex, edit_consent, local_summary_guidance, tdd95, sqa_phase, stop_recommendation_gate, auto_commit, tdd, handoff | ~29 families |
| BLOCKED | task_tracker (split-brain), `.state/state/` (hidden duplicate), | ~2 families |
| PLUGIN_OWNED | cc-aca-observability/*, cc-aca-epistemic/*, cc-model-router/*, cc-lazy-closure-debt/* | ~4 dirs |
| UNKNOWN | `.state/state/` exact provenance | 1 family |

---

## 4. Resolver Registration Recommendations

| Family | Recommendation | Reason |
|--------|---------------|--------|
| **session_tldr** | Register now | Producer (snapshot plugin) known, consumer known, terminal-scoped, canonical root `state/sessions` or separate `state/session_tldr/` |
| **task_tracker** | **Do NOT register yet** | Split-brain must be resolved first. Register only when one authoritative writer is established. |
| **cc-aca-observability** | Register per subfamily (task_tracker, sqa_phase, logs) | Plugin-owned sub-trees need individual classification |
| **model-router** | Register per subfamily | Mix of terminal and session state within same root |
| **prompt_session** | Register now | Producer: cc-skills-sdlc skill_context. Consumer: SessionStart injector. Session-scoped. |
| **tdd95** | Register now | Producer: tdd95_core.py. Terminal-scoped. |
| **skill_context** | Register now | Producer: cc-skills-sdlc. Consumer: multiple hooks. Session-scoped. |
| **handoff** | Register now | Producer: cc-skills-analysis/cc-skills-sdlc. Terminal-scoped. |
| **`.state/state/`** | **Investigate first** | Hidden duplicate of hooks/state/ content. May be a migration artifact or concurrent write destination. |
| **prompt_choice** | Register now | Producer: cc-aca-epistemic prompt_choice_state.py. Session-scoped. |
| **cks_context_injected** | Register now | Producer: cks_context.py. Session-scoped. |
| **sqa_phase** | Register now | Producer: posttooluse_sqa_phase_tracker.py. Terminal-scoped. |
| **constraints** | Register now | Producer: session_constraints.py. Session-scoped. |
| **observe_before_act** | Register now | Producer: PreToolUse gate. Terminal-scoped. **Enforcement-critical.** |
| **receipts (task_receipts)** | Register now | Producer: task_receipt.py. Consumer: PreToolUse_task_done_evidence_gate.py. Terminal-scoped. |
| **auto_commit** | Register now | Producer: cc-skills-utils Stop hook. Terminal-scoped. |
| **v_findings** | Register now | Producer: cc-skills-sdlc verification. Session-scoped. |
| **stop_recommendation_gate** | Register now | Producer: cc-skills-sdlc. Terminal-scoped. |
| **local-model-crashes** | Inventory only | Documentation files, not runtime state. |
| **edit_consent** | Register now | Producer: edit_consent.py. Terminal-scoped. |
| **chs_delta_reindex** | Register now | Producer: SessionStart_chs_delta_reindex.py. Session-scoped. |
| **next_step_choice** | Register now | Producer: cc-skills-analysis. Session-scoped. |
| **stop_meta_conversation** | Register now | Producer: Stop_meta_conversation_loop.py. Session-scoped. |
| **local_summary_guidance** | Register now | Producer: cc-skills-sdlc. Terminal-scoped. |

---

## 5. Task Tracker Migration Prerequisites

### Current state

| Aspect | Local root | Plugin root |
|--------|-----------|-------------|
| Path | `state/task_tracker/{tid}_tasks.json` | `state/cc-aca-observability/task_tracker/{tid}_tasks.json` |
| Writer | `posttooluse/task_tracker_hook.py` → `TaskList`/`TaskCreate`/`TaskUpdate` | `cc-aca-observability/__lib/posttooluse/task_tracker_hook.py` |
| Files | ~2,169 | ~994 |
| Plugin wrapper import | `PostToolUse_router.py:583` calls `track_tool_use()` | **Writes plugin root, reads local root for dedup** |

### Split-brain details

**Confirmed divergence on terminal `console_01f0572e-c0f1-4c0f-8bda-c61d4e653181`:**
- Task #867: local=`in_progress`, plugin=`completed`
- All other tasks in same file: identical statuses

**Root cause of divergence:**
The plugin `task_tracker_hook.py` reads local state/task_tracker/ to determine "has this been tracked?" but writes its OWN record to `state/cc-aca-observability/task_tracker/`. The update path goes through different code — the local hook processes TaskCreate/TaskUpdate/Stop, the plugin hook only processes PostToolUse events. If one fires without the other, they diverge.

### Prerequisites for migration

| # | Prerequisite | Verification | Status |
|---|-------------|--------------|--------|
| P1 | **Establish one authoritative writer** — decide whether local or plugin wins | Design decision: plugin already wraps local; make plugin the exclusive writer | NOT DONE |
| P2 | **Reconciliation** — merge divergent records for common terminal_ids before cutover | Script exists (manual) | NOT DONE |
| P3 | **Add session_id/terminal_id to schema explicitly** (currently implicit in filename) | Schema review | NOT DONE |
| P4 | **Establish canonical destination** — `state/terminals/{tid}/task_tracker.json` | Path design | NOT DONE |
| P5 | **Dual-base T2 period** — write both for 1 cycle, then cut over readers | Test plan | NOT DONE |

---

## 6. Migration Priority Ranking

| Priority | Family | Why | Dependencies |
|----------|--------|-----|--------------|
| **P0** | task_tracker | Highest migration risk. Split-brain actively causes data loss. | Resolve split-brain first |
| **P0** | `.state/state/` | Hidden duplicate root. Unknown provenance could mask lost state. | Determine origin |
| **P1** | observe_before_act | Enforcement-critical blocking gate depends on this state | None |
| **P1** | task_receipts (receipts) | PreToolUse evidence gate depends on receipts | None |
| **P2** | tool_use_log | 1000+ files at `.state/` need canonicalization. No retention. | None |
| **P2** | anti_sycophancy_injector | Split across 3 roots: `hooks/state/`, `hooks/.state/`, `state/` | Dedup first |
| **P2** | consultation_aware | Split across `hooks/state/` AND `hooks/.state/` | Dedup first |
| **P3** | followup_context, arch_declaration | Canonical target `state/terminals/` exists; migration straightforward | None |
| **P3** | session_tldr | Largest family by file count (3159). Non-critical but high volume. | None |
| **P4** | prompt_session, skill_context, cks_context_injected | Session-scoped; low migration risk | None |
| **P5** | All plugin-owned families | Plugin decoupling prerequisite needed first | Plugin scope design |
| **P6** | diagnostics (logs/) | Already in logs/ root; low priority | None |
| **P7** | All TRANSIENT/CACHE families | Small footprint, low risk | None |

---

## 7. Invariants (for Future Migration)

| Invariant | Definition | Enforcement | Test |
|-----------|-----------|-------------|------|
| **Ownership** | One authoritative writer per artifact type. No two hooks may write the same state type to the same root. | state_resolver.inventory() detects duplicate roots per family | `test_no_duplicate_roots()` |
| **Identity** | No silent cross-terminal/session collision. Every state file must encode its scope (terminal_id, session_id, or shared). | Filename pattern audit | `test_identity_in_filenames()` |
| **Schema** | Readers understand writers. If schema versions differ, reader must fail (not silently degrade). | Per-family schema version in state_resolver | `test_schema_compatibility()` |
| **Migration** | Old state remains recoverable until verified migrated. No delete of legacy path without dual-base T0 period. | Dual-base pattern (state_paths.py §MIGRATION_PATTERN) | `test_dual_base_precedence()` |
| **Lifecycle** | Every registered state type has a lifecycle policy (permanent, TTL, session, terminal, cache, disposable). | state_resolver entry requires lifecycle field | `test_lifecycle_policy_present()` |

---

## 8. Required Future Tests

| Test | What it covers | Priority |
|------|---------------|----------|
| `test_no_duplicate_roots()` | Detects identical state types across multiple roots (split-brain detector) | P0 |
| `test_identity_in_filenames()` | Every state file has terminal_id or session_id in its name | P1 |
| `test_task_tracker_split_brain()` | Reproducible divergence detection for task_tracker | P0 |
| `test_state_registration_completeness()` | Ensures all active state families are registered in the resolver | P1 |
| `test_dual_base_precedence()` | When both new and legacy state exist, new wins | P2 |
| `test_retention_policy()` | LOG files are cleaned up after TTL (after policy is set) | P3 |
| `test_state_inventory_regression()` | Baseline inventory file — diffs alert on new state families | P1 |

---

## 9. Critical Issues (must resolve before consumer migration)

| # | Issue | Impact | Evidence |
|---|-------|--------|----------|
| **C1** | task_tracker status divergence between local and plugin roots | Data loss: completed tasks appear in-progress (or vice versa) | Verified: task #867 local=in_progress, plugin=completed |
| **C2** | `.state/state/` hidden duplicate root | Unknown provenance — may be migration artifact, concurrent write, or stale copy | 141 files with same naming patterns as hooks/state/ |
| **C3** | anti_sycophancy_injector split across THREE roots | Triple-redundant state — hooks/state/, hooks/.state/, state/ | Diffing needed to confirm identical |
| **C4** | No retention/cleanup on any LOG family | 1000+ tool_use_log files, 298 path_errors files — indefinite accumulation | No `unlink`/`cleanup` calls found for these paths |

---

## Claim Ledger

| Claim | Evidence | Confidence | How to falsify |
|-------|----------|-----------|----------------|
| task_tracker has split-brain | Verified: task #867 status diverges between state/task_tracker/ and state/cc-aca-observability/task_tracker/ | HIGH | Show that both files are identical for all terminal_ids (check 10+ terminals) |
| tool_use_log writer is cc-aca-observability artifact_access_tracker.py | grep confirms `tool_use_log` path construction at line 31, write at line 100 | HIGH | Show a different hook writes the same file pattern |
| task_receipts producer is task_receipt.py, consumer is PreToolUse_task_done_evidence_gate.py | Both files explicitly reference receipt paths | HIGH | Block both paths and show no other writer/reader |
| `.state/state/` is a hidden split-brain | Files match `hooks/state/` patterns (consultation_aware, arch_declaration) | MEDIUM | Need to diff content between `.state/state/` and `hooks/state/` for same files |
| observe_before_act enforcement depends on its own state file | Code reads state at turn start to determine if search occurred | HIGH | Remove state file and show gate degrades |
| prompt_session producer is unknown (no grep hit in hooks/plugins) | 573 files with no identified writer in `.claude/hooks/` or plugin code — possibly claude.exe or CCS/OpenCode built-in | MEDIUM | Find a writer in plugin or hook code |
| prompt_choice producer is unknown (no grep hit in hooks/plugins) | 103 files, same assessment — likely claude.exe built-in | MEDIUM | Find the writer |
| recommendation_loop producer is unknown (no grep hit) | 29 files, same assessment — likely claude.exe built-in | MEDIUM | Find the writer |
| stop_recommendation_gate producer unknown | 10 files, same assessment | MEDIUM | Find the writer |

---

## Supplementary Findings (Cross-reference: investigation agents)

The following details were contributed by parallel investigation agents and cross-referenced with direct inspection.

### A. Evidence subsystems (5 found, not just evidence_store.py)

| Subsystem | State type | Blocking? | Producer | Consumer |
|-----------|-----------|-----------|----------|----------|
| **UEEA** | `ueea_state.jsonl` at `hooks/state/` | YES (Stop) | `__lib/unified_evidence_enforcer.py` | Same file (`run()`, `check_grace()`) |
| **Evidence Validator** | `hash_cache_{terminal}.json` | NO (advisory) | `evidence/__init__.py` (`update_hash_cache()`) | `validate_claim_evidence()` |
| **Recent Evidence Gate** | `recent_evidence_{tid}.json` | YES (PreToolUse) | `cc-aca-epistemic/.../recent_evidence_tracker.py` | `cc-aca-epistemic/.../recent_evidence_gate.py` |
| **Evidence Hierarchy Gate** | (no standalone state) | YES (PreToolUse) | `cc-aca-epistemic/.../evidence_hierarchy_gate.py` | Same file |
| **Planning Evidence Gate** | (sidecar artifact) | NO (workflow) | `cc-skills-sdlc/planning/evidence_gate.py` | `go/orchestrate.py` |

**Key finding:** The UEEA state file (`hooks/state/ueea_state.jsonl`) is a blocking enforcement dependency — it's read by the Stop hook for claim verification. It writes to `hooks/state/`, NOT `hooks/.state/` — a different root than most other state families.

### B. Read/Search Tracker subsystems (5 found)

| Subsystem | State root | Blocking? | Identity |
|-----------|-----------|-----------|----------|
| Observe Before Act | `hooks/.state/observe_before_act/` | YES (PreToolUse) | terminal_id + session_id composite |
| Skill Context | `hooks/state/skill_context/` | YES (PreToolUse) | terminal_id |
| CKS Context Injection | (no local state — queries external DB) | NO | shared |
| Prompt Session State | `state/prompt_session/` | NO (advisory Stop) | session_id + terminal_id |
| Prompt Choice State | `state/prompt_choice/` | NO (interactive UX) | session_id |

### C. Unresolved unknowns

**Four families with NO identified producer in hook or plugin code** (likely written by claude.exe, CCS, or OpenCode):

1. **prompt_session** (~573 files at `state/prompt_session/`) — no grep hit for writer
2. **prompt_choice** (~103 files at `state/prompt_choice/`) — no grep hit for writer
3. **recommendation_loop** (~29 files at `state/recommendation_loop/`) — no grep hit for writer
4. **stop_recommendation_gate** (~10 files at `state/stop_recommendation_gate/`) — no grep hit for writer

These cannot be registered without knowing their producer. They may be:
- Written by claude.exe / CCS / OpenCode (not in plugin or hook code)
- Generated by an older subsystem that was removed
- Artifacts from auto-prompt enhancement or TDD tooling

### D. Corrected `.state/state/` classification

The `.state/state/` directory at `hooks/.state/state/` (~141 files) contains:
- `consultation_aware_*.json` — same content as `hooks/state/`
- `arch_declaration_*.json` — same content as `hooks/state/`
- `anti_sycophancy_injector/` subdir — SAME as `hooks/.state/anti_sycophancy_injector/`

**Classification:** This is a stale copy of `hooks/state/` state files that was written by a prior code path (likely an older version of `consultation_aware_injector.py` that used `.state/state/` instead of `.state/` directly). The anti_sycophancy_injector subdir is acknowledged in `challenge_marker.py:25-26` with a hardcoded path + tempdir fallback.

**Action:** Diff these files against `hooks/state/` originals. If identical, the `.state/state/` dir is a stale migration artifact — safe to clean up. If diverging, there's a second active writer.
