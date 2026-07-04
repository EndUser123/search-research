
### Added

- .claude/agents/red-team-critic.md
- .claude/agents/red-team-gate-reviewer.md
- .claude/agents/red-team-planner.md
- .claude/agents/red-team-workflow-reviewer.md


### Added

- __csf/.staging/rank_hook_costs.py: new hook


### Added

- .claude/hooks/tests/test_stop_json_validation_guard.py: new hook

### Removed

- .claude/hooks/tests/_quarantine/QUARANTINE.md
- .claude/hooks/tests/_quarantine/test_SessionStart_dreaming_daemon.py
- .claude/hooks/tests/_quarantine/test_Stop_semantic_critic.py
- .claude/hooks/tests/_quarantine/test_anti_sycophancy_fixes.py
- .claude/hooks/tests/_quarantine/test_anti_sycophancy_three_layer_fix.py
- .claude/hooks/tests/_quarantine/test_authorization_state_management.py
- .claude/hooks/tests/_quarantine/test_cc_health.py
- .claude/hooks/tests/_quarantine/test_circuit_breaker_flag.py
- .claude/hooks/tests/_quarantine/test_cks_context_hook.py
- .claude/hooks/tests/_quarantine/test_cks_correction_inject.py
- .claude/hooks/tests/_quarantine/test_cks_hybrid_retrieval.py
- .claude/hooks/tests/_quarantine/test_cks_knowledge_injection.py
- .claude/hooks/tests/_quarantine/test_claude_sensitive_edit_policy.py
- .claude/hooks/tests/_quarantine/test_contract_preserving.py
- .claude/hooks/tests/_quarantine/test_deletion_verification_guard.py
- .claude/hooks/tests/_quarantine/test_dependency_verification_gate.py
- .claude/hooks/tests/_quarantine/test_destructive_git_guard.py
- .claude/hooks/tests/_quarantine/test_dispatch_chain_verification.py
- .claude/hooks/tests/_quarantine/test_documentation_validator_integration.py
- .claude/hooks/tests/_quarantine/test_dreaming_backup_strategy.py
- .claude/hooks/tests/_quarantine/test_dx_tools_block_logging.py
- .claude/hooks/tests/_quarantine/test_dx_tools_locking.py
- .claude/hooks/tests/_quarantine/test_dx_tools_observability.py
- .claude/hooks/tests/_quarantine/test_e2e_tracker.py
- .claude/hooks/tests/_quarantine/test_edit_verification_hybrid.py
- .claude/hooks/tests/_quarantine/test_epistemic_format_fix.py
- .claude/hooks/tests/_quarantine/test_evidence_store_api_validation.py
- .claude/hooks/tests/_quarantine/test_existence_gate.py
- .claude/hooks/tests/_quarantine/test_existence_gate_repair.py
- .claude/hooks/tests/_quarantine/test_file_lock_improvements.py
- .claude/hooks/tests/_quarantine/test_gate_metadata.py
- .claude/hooks/tests/_quarantine/test_gen_dispatch_manifest.py
- .claude/hooks/tests/_quarantine/test_git_creation_blocking.py
- .claude/hooks/tests/_quarantine/test_guard_false_positive_fixes.py
- .claude/hooks/tests/_quarantine/test_hook_audit_stats.py
- .claude/hooks/tests/_quarantine/test_hook_baseline_metrics.py
- .claude/hooks/tests/_quarantine/test_hook_bytecode_cleanup.py
- .claude/hooks/tests/_quarantine/test_hook_chain_e2e.py
- .claude/hooks/tests/_quarantine/test_hook_error_rca.py
- .claude/hooks/tests/_quarantine/test_hook_health_inline_imports.py
- .claude/hooks/tests/_quarantine/test_hook_inprocess.py
- .claude/hooks/tests/_quarantine/test_hook_loading.py
- .claude/hooks/tests/_quarantine/test_hook_registration_liveness.py
- .claude/hooks/tests/_quarantine/test_hook_runner.py
- .claude/hooks/tests/_quarantine/test_hook_runner_stop_protocol.py
- .claude/hooks/tests/_quarantine/test_import_deletion_guard.py
- .claude/hooks/tests/_quarantine/test_import_resolver.py
- .claude/hooks/tests/_quarantine/test_in_process_hooks.py
- .claude/hooks/tests/_quarantine/test_integration_rootcause.py
- .claude/hooks/tests/_quarantine/test_integration_verifier_integration.py
- .claude/hooks/tests/_quarantine/test_intent_extractor_migration.py
- .claude/hooks/tests/_quarantine/test_investigation_gate_terminal_scoped.py
- .claude/hooks/tests/_quarantine/test_investigation_loop_blocked.py
- .claude/hooks/tests/_quarantine/test_investigation_verification_e2e.py
- .claude/hooks/tests/_quarantine/test_location_optimizer.py
- .claude/hooks/tests/_quarantine/test_monitoring_infrastructure.py
- .claude/hooks/tests/_quarantine/test_no_stderr_in_hooks.py
- .claude/hooks/tests/_quarantine/test_ownership_colocation_hooks.py
- .claude/hooks/tests/_quarantine/test_package_import_gate.py
- .claude/hooks/tests/_quarantine/test_performance_baseline.py
- .claude/hooks/tests/_quarantine/test_phase2_epistemic.py
- .claude/hooks/tests/_quarantine/test_pipe_name_consistency.py
- .claude/hooks/tests/_quarantine/test_post_skill_prose_edge_cases.py
- .claude/hooks/tests/_quarantine/test_post_skill_prose_integration.py
- .claude/hooks/tests/_quarantine/test_post_skill_prose_logging.py
- .claude/hooks/tests/_quarantine/test_pre_tool_use_file_guard.py
- .claude/hooks/tests/_quarantine/test_precompact_session_files.py
- .claude/hooks/tests/_quarantine/test_pretooluse_bash_syntax_routing.py
- .claude/hooks/tests/_quarantine/test_pretooluse_empty_stdin_fix.py
- .claude/hooks/tests/_quarantine/test_pretooluse_observability.py
- .claude/hooks/tests/_quarantine/test_pretooluse_pytest_timeout_guard.py
- .claude/hooks/tests/_quarantine/test_pretooluse_task_self_doc_gate.py
- .claude/hooks/tests/_quarantine/test_pretooluse_type_validator.py
- .claude/hooks/tests/_quarantine/test_pretooluse_user_delegation_gate.py
- .claude/hooks/tests/_quarantine/test_pretooluse_verification_router.py
- .claude/hooks/tests/_quarantine/test_proposal_decision_scanner.py
- .claude/hooks/tests/_quarantine/test_python_cache_manager.py
- .claude/hooks/tests/_quarantine/test_rca_contract_bugs_red.py
- .claude/hooks/tests/_quarantine/test_rca_single_hard_gate.py
- .claude/hooks/tests/_quarantine/test_recursive_escalation.py
- .claude/hooks/tests/_quarantine/test_redos_vulnerability.py
- .claude/hooks/tests/_quarantine/test_referent_hooks.py
- .claude/hooks/tests/_quarantine/test_referent_hooks_handoff.py
- .claude/hooks/tests/_quarantine/test_repo_visibility_guard.py
- .claude/hooks/tests/_quarantine/test_rsn_formatter.py
- .claude/hooks/tests/_quarantine/test_scope_adapter_migrations.py
- .claude/hooks/tests/_quarantine/test_self_correcting_agent_loop.py
- .claude/hooks/tests/_quarantine/test_self_reflection_gate.py
- .claude/hooks/tests/_quarantine/test_semantic_critic_live.py
- .claude/hooks/tests/_quarantine/test_semantic_v2.py
- .claude/hooks/tests/_quarantine/test_sequential_thinking_hooks.py
- .claude/hooks/tests/_quarantine/test_session_manager.py
- .claude/hooks/tests/_quarantine/test_session_namespace_isolation.py
- .claude/hooks/tests/_quarantine/test_skill_enforcement_flow.py
- .claude/hooks/tests/_quarantine/test_skill_enforcer_hook.py
- .claude/hooks/tests/_quarantine/test_skill_pattern_gate_state_file.py
- .claude/hooks/tests/_quarantine/test_skill_structure_gate_readonly.py
- .claude/hooks/tests/_quarantine/test_skill_workflow_enforcement_v5.py
- .claude/hooks/tests/_quarantine/test_stale_discovery_detection.py
- .claude/hooks/tests/_quarantine/test_standalone_hook.py
- .claude/hooks/tests/_quarantine/test_stateless_skill_first_gate.py
- .claude/hooks/tests/_quarantine/test_stop_gate_telemetry_rotation.py
- .claude/hooks/tests/_quarantine/test_stop_hypothesis_as_fact_refactor.py
- .claude/hooks/tests/_quarantine/test_stop_ralph_loop.py
- .claude/hooks/tests/_quarantine/test_stop_trivial_integration.py
- .claude/hooks/tests/_quarantine/test_stop_verification_gate_tool_awareness.py
- .claude/hooks/tests/_quarantine/test_strawberry_decommission.py
- .claude/hooks/tests/_quarantine/test_subprocess_patch_fix.py
- .claude/hooks/tests/_quarantine/test_task_005_integration.py
- .claude/hooks/tests/_quarantine/test_task_identity_manager.py
- .claude/hooks/tests/_quarantine/test_task_tool_modify_integration.py
- .claude/hooks/tests/_quarantine/test_terminal_detection.py
- .claude/hooks/tests/_quarantine/test_terminal_id_standardization.py
- .claude/hooks/tests/_quarantine/test_think_trigger_dataclass.py
- .claude/hooks/tests/_quarantine/test_toctou_runtime.py
- .claude/hooks/tests/_quarantine/test_tool_check.py
- .claude/hooks/tests/_quarantine/test_unified_evidence_enforcer.py
- .claude/hooks/tests/_quarantine/test_unverified_stance_observability.py
- .claude/hooks/tests/_quarantine/test_us_telemetry_integration.py
- .claude/hooks/tests/_quarantine/test_verification_router_performance.py
- .claude/hooks/tests/_quarantine/test_verification_theater.py
- .claude/hooks/tests/_quarantine/test_why_blocked_rca.py
- .claude/hooks/tests/_quarantine/test_worktree_helper.py
- .claude/hooks/tests/_quarantine/test_wrapper_validator_integration.py


### Removed

- packages/.claude-marketplace/plugins/cc-model-router/pack.py


### Added

- packages/.claude-marketplace/plugins/cc-model-router/pack.py: consolidated router


### Added

- .claude/hooks/Stop_sound_hook.py: new hook


### Added

- .claude/hooks/tests/test_claim_gap_telemetry_probe.py: new hook


### Added

- .claude/context/RELIABILITY_2026_07_02_POST_MERGE.md
- .claude/hooks/tests/test_stop_user_prompt_enrichment.py: new hook


### Removed

- packages/.claude-marketplace/plugins/quickstop/agents/audit-ecosystem.md
- packages/.claude-marketplace/plugins/quickstop/agents/audit-global.md
- packages/.claude-marketplace/plugins/quickstop/agents/audit-project.md
- packages/.claude-marketplace/plugins/quickstop/agents/research-core.md
- packages/.claude-marketplace/plugins/quickstop/agents/research-ecosystem.md
- packages/.claude-marketplace/plugins/quickstop/agents/research-optimization.md
- packages/.claude-marketplace/plugins/quickstop/references/cache-check-protocol.md
- packages/.claude-marketplace/plugins/quickstop/references/decision-memory-protocol.md
- packages/.claude-marketplace/plugins/quickstop/skills/cks-status/SKILL.md
- packages/.claude-marketplace/plugins/quickstop/skills/knowledge/SKILL.md
- packages/.claude-marketplace/plugins/quickstop/skills/refresh/SKILL.md


### Added

- .claude/hooks/analysis/stop_gate_retirement_candidates_20260701.md: new hook

# Hooks CHANGELOG

## 2026-02-07

### Fixed: Session/Terminal-Scoped Evidence for Stop Validators

**Problem addressed:** Stop-time validators could misread investigation evidence across sessions/terminals, causing false-positive blocks (notably `VERIFICATION_THEATER` and unsubstantiated-claim loops).

**Root cause:**
- `Stop` hook input often lacked `response`; transcript fallback could feed stale assistant content.
- `ToolSequenceManager` used a single shared file without scoped reads by session/terminal.
- PostToolUse sequence writes did not persist `session_id`.

**Solution:** Added session-context pinning and scoped evidence loading across Stop/PostToolUse/assumption-audit paths.

**Code changes:**
- `Stop_router.py`
  - Added helper-based transcript extraction using latest assistant message only.
  - Extracts text blocks (`type == "text"`) to avoid tool payload contamination.
  - Pins session context via `CLAUDE_SESSION_ID` and preserves/derives `CLAUDE_TERMINAL_ID`.
- `PostToolUse_router.py`
  - Added session-context pinning from hook input metadata.
  - `ToolSequenceManager.append(...)` now stores `session_id` in entries and passes `session_id` argument.
- `tool_sequence_manager.py`
  - Added `load_tool_sequence_filtered(session_id, terminal_id)`.
  - `load_tool_sequence()` now routes through filtered loading.
- `assumption_audit_v2.py`
  - Evidence sequence load now uses `load_tool_sequence_filtered(...)` with current session+terminal scope.
- `investigation-ledger/ledger.py`
  - Added stable identity resolution precedence:
    - `CLAUDE_TERMINAL_ID` → `CLAUDE_SESSION_ID` → terminal detection fallback.
  - Added terminal key sanitization for filesystem-safe ledger filenames.

**Tests added:**
- `investigation-ledger/test_posttooluse_session_context.py`
- `investigation-ledger/test_terminal_id_resolution.py`
- `investigation-ledger/test_tool_sequence_filtering.py`
- `tests/test_stop_router_transcript_sanitization.py` (helper-level coverage; full pytest run constrained in this environment)

**Validation:**
- `pytest -q P:/.claude/hooks/investigation-ledger/test_posttooluse_session_context.py` → pass
- `pytest -q P:/.claude/hooks/investigation-ledger/test_terminal_id_resolution.py` → pass
- `pytest -q P:/.claude/hooks/investigation-ledger/test_tool_sequence_filtering.py` → pass

### Documentation Updated

Updated to reflect session/terminal-scoped evidence flow and filtered sequence loading:
- `README.md`
- `ARCHITECTURE.md`
- `investigation-ledger/README.md`

---

## 2026-02-05

### Hook System Improvements Plan - COMPLETE ✅

**Problem addressed:** Hook system performance and parallel execution infrastructure required completion and feature flag removal.

**Solution:** Completed Phase 4 of hook system improvements plan, removed parity checking (validated with 0 mismatches over 971+ executions), and removed PARALLEL_HOOKS_ENABLED feature flag (parallel execution now always-on).

**Changes:**
- **PreToolUse_bash_router.py v2.2**: Removed `PARALLEL_HOOKS_ENABLED` feature flag
  - Removed variable declaration (line 53)
  - Removed auto-disable block (lines 424-439)
  - Changed `if PARALLEL_HOOKS_ENABLED and parallel_hooks:` to `if parallel_hooks:` (line 507)
  - Parallel execution is now always-on behavior
- **PreToolUse_write_router.py**: Removed parity checking from all 3 in-process wrappers
  - `wrap_session_reversion_check_inprocess`: Simplified to direct in-process call
  - `wrap_exec_orchestrator_inprocess`: Simplified to direct in-process call
  - `wrap_skill_enforcement_gate_inprocess`: Simplified to direct in-process call
  - Each simplified from 30+ lines of parity checking code to ~3 lines
  - Comment added: `# Run in-process (parity validated 2026-02-05: 0 mismatches over 971+ executions)`
- **hook_system_improvements.md**: Updated status to COMPLETE
  - All 5 phases complete (Prerequisites, Subprocess Consolidation, Atomic Logging, Timeout Budgeting, Parallel Execution)
  - All success criteria met
  - Final metrics: 0 parity mismatches, 0 parallel execution errors, 971+ parallel execution entries, 139-141ms latency per batch

**Validation:**
- Parity checking: 0 mismatches over 971+ executions
- Parallel execution: 0 errors over extended testing period
- Import test passed for both modified files

**Files modified:**
- `PreToolUse_bash_router.py` - Feature flag removed
- `PreToolUse_write_router.py` - Parity checking removed
- `.claude/plans/hook_system_improvements.md` - Status updated to COMPLETE

**Implementation plan:** [hook_system_improvements.md](../plans/hook_system_improvements.md)

---

## 2026-02-05

### Comprehensive Hook Catalog Update

**Problem addressed:** README.md hook catalog was incomplete and didn't reflect all registered hooks from settings.json.

**Solution:** Created comprehensive catalog documenting all 60 registered hooks organized by event type.

**Changes:**
- Added complete hook inventory table (60 hooks total)
- Organized hooks by event type (SessionStart, UserPromptSubmit, PreToolUse, PostToolUse, Stop, PreCompact, Notification)
- Added comprehensive documentation for 23 core hook systems
- Updated environment variables section with all settings from settings.json
- Added detailed descriptions for:
  - Hook Protection System (PreToolUse + PostToolUse)
  - Skill Enforcement v3.2 (UserPromptSubmit + PreToolUse + PostToolUse + Stop)
  - TDD Enforcement (PreToolUse + PostToolUse)
  - Contract System (PreToolUse + PostToolUse + Stop)
  - Task Detection & Tracking (UserPromptSubmit + PostToolUse)
  - Evidence & Claim Tracking (PostToolUse + Stop)
  - File System Operations (PreToolUse + PostToolUse)
  - Code Quality & Validation (PreToolUse + PostToolUse)
  - Shell Command Safety (PreToolUse + PostToolUse)
  - Investigation & Speculation Detection (PostToolUse + Stop)
  - Change Propagation & Validation (PostToolUse)
  - CKS Integration (PostToolUse + Stop + UserPromptSubmit)
  - Session Management (PostToolUse + SessionStart)
  - Skill Routing (UserPromptSubmit + PostToolUse)
  - Semantic File Routing (PreToolUse)
  - System Monitoring (PostToolUse + SessionStart)
  - Context & Compaction (UserPromptSubmit + PreCompact)
  - Architecture & Evidence (Stop)
  - Cross-Validation (Stop)
  - Auto-Commit (Stop)
  - Voice Notifications (Notification)
  - Overcomplication Loop Prevention (PreToolUse)
  - Goal Drift Detection (PostToolUse)

**Files modified:**
- `README.md` - Complete catalog rewrite and reorganization

**Bug fix:**
- Fixed Hook JSON validation error in `assumption_audit_v2.py` (decision value mapping: "allow" → "approve")

**Environment variables added:**
- All settings from settings.json now documented in README.md
- 40+ environment variables with descriptions and defaults

---

## 2026-02-04

### Migrated: Diagnostic Logger to SQLite with WAL Mode

**Problem addressed:** File-based JSONL logging caused lock contention errors (`[Errno 13] Permission denied`) when multiple terminals wrote concurrently.

**Root cause:** Manual file locking with msvcrt.locking() used non-blocking locks, causing log drops when multiple processes tried to write simultaneously.

**Solution:** Migrated from JSONL files to SQLite with WAL (Write-Ahead Logging) mode.

**Architecture changes:**
- **Before:** 5 JSONL files (cc_context.jsonl, hook_invocations.jsonl, tool_calls.jsonl, assumptions.jsonl, cc_errors.jsonl)
- **After:** Single SQLite database (diagnostics.db) with 5 tables
- **Concurrency:** WAL mode enables concurrent reads/writes without manual file locking
- **Timeout:** 5-second busy timeout queues writes instead of dropping them

**Database schema:**
```sql
context       -- Context logs (prompt tracking)
hooks         -- Hook invocations (performance tracking)
tools         -- Tool call logs (I/O tracking)
assumptions   -- Assumption detection
errors        -- Error logging with stack traces
```

**Benefits:**
- No more lock contention errors
- ACID transactions for data integrity
- Thread-local connections for safety
- SQL queries for analysis (vs. file parsing)
- Indexed queries (session_id, timestamp DESC)

**Files modified:**
- `cc_diagnostic_logger.py` - Complete rewrite (v2.0.0)
  - Removed: File locking, JSONL writes, manual rotation
  - Added: SQLite schema, WAL mode, thread-local connections
  - Same API: `log_context()`, `log_hook_invocation()`, `log_tool_call()`, `log_assumption()`, `log_error()`

**CLI commands:**
```bash
# View recent logs
python P:/.claude/hooks/cc_diagnostic_logger.py recent --type hooks --count 10

# Session summary
python P:/.claude/hooks/cc_diagnostic_logger.py summary

# Database status
python P:/.claude/hooks/cc_diagnostic_logger.py status

# Clear all logs
python P:/.claude/hooks/cc_diagnostic_logger.py clear
```

**Database location:** `P:\.claude\hooks\logs\diagnostics\diagnostics.db`

**Migration notes:**
- Old JSONL files remain in `archive/` directory
- No migration script required (fresh start)
- Backward compatible API (no changes to hook code)

---

## 2026-01-31

### Added: Investigation Ledger System (Two-Layer Defense)

**Problem addressed:** LLM made diagnostic claims about system behavior without reading any code. Existing hooks validated tool sequences but couldn't detect when LLM responds with speculation and uses NO tools at all.

**Root cause:** No structural enforcement for "must investigate before answering diagnostic questions."

**Solution:** Two-layer defense system:

1. **Layer 1: Investigation Required** (`StopHook_investigation_required.py`)
   - Detects: Diagnostic question + No tools used + Substantial response
   - Action: Injects self-assessment prompt (WARN, non-blocking)
   - Principle: "The LLM knows if it investigated or speculated"

2. **Layer 2: Investigation Validator** (`investigation-ledger/Stop_investigation_validator.py`)
   - Detects: Claims about system behavior exceed investigation evidence
   - Action: Blocks response (CRITICAL)
   - Principle: "Confidence cannot exceed evidence tier ceiling"

**Architecture:**
```
PostToolUse → InvestigationTracker → session_ledger.json
                                            ↓
Stop → StopHook_investigation_required → "Did you investigate?" (self-prompt)
Stop → Stop_investigation_validator → "Do claims match ledger?" (block)
```

**Files added:**
- `StopHook_investigation_required.py` - Self-prompt for diagnostic questions without tools
- `posttooluse/investigation_tracker.py` - In-process tracker for tool usage

**Files modified:**
- `Stop_router.py` - Added both hooks to HOOK_SEQUENCE
- `posttooluse/__init__.py` - Registered InvestigationTracker in registry

**Environment variables:**
- `INVESTIGATION_REQUIRED_ENABLED` (default: true)
- `INVESTIGATION_LEDGER_ENABLED` (default: true)

**Key insight:** Pattern-based detection is fragile. Use structural checks (tool usage - binary) + LLM self-assessment (the LLM knows if it investigated).

---

## 2026-01-28

### Fixed: Windows Console Flash During Session Startup

**Problem addressed:** Console windows were flashing during Claude Code session startup on Windows, interrupting typing and stealing characters.

**Root cause:** Multiple subprocess calls in hooks were missing `CREATE_NO_WINDOW` flag on Windows. The flash was traced to `__lib/task_identity_manager.py` which runs git commands during every session startup via `SessionStart_task_identity.py` → `SessionStart_checkpoint_restore.py` import chain.

**Resolution:**
1. Deleted `.claude/hooks/bin/git.bat` - Was intercepting git commands and spawning PowerShell windows
2. Added `_get_git_executable()` helper to `SessionStart_task_identity.py` to bypass git.bat wrapper
3. Fixed `__lib/task_identity_manager.py` - Added `CREATE_NO_WINDOW` flag to git subprocess in `_from_git_worktree()` method (lines 164-172)
4. Fixed `UserPromptSubmit_topic_switch_check.py` - Added `CREATE_NO_WINDOW` to git subprocess calls
5. Re-enabled all 8 SessionStart hooks in `SessionStart_router.py` after verification

**Files changed:**
- `bin/git.bat` - DELETED (wrapper calling PowerShell)
- `__lib/task_identity_manager.py` - Added `CREATE_NO_WINDOW` flag
- `SessionStart_task_identity.py` - Added `_get_git_executable()` helper
- `UserPromptSubmit_topic_switch_check.py` - Added `CREATE_NO_WINDOW` flag
- `SessionStart_router.py` - Re-enabled all hooks (HOOK_SEQUENCE restored)

**Technical fix applied:**
```python
import sys
creation_flags = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
result = subprocess.run(
    ["git", "branch", "--show-current"],
    creationflags=creation_flags,
    ...
)
```

**Verification:** User confirmed "no flash" after fix was applied.

---

### Fixed: PostToolUse JSON Validation Errors

**Problem addressed:** Multiple PostToolUse hooks were outputting invalid JSON format (`{"passed": True, ...}` instead of `{"hookSpecificOutput": {...}}` or `{}`), causing "JSON validation failed" errors on Bash/Edit/Write operations.

**Root cause:**
- `UserPromptSubmit_truth_validator.py` was registered as PostToolUse hook but outputs wrong format
- `strategy_escalation_tracker.py` was outputting `{"passed": True, ...}` format
- `PostToolUse_file_activity_tracker.py` was outputting `{"passed": True}` format

**Resolution:**
1. Created `PostToolUse_truth_validator.py` - PostToolUse-compatible truth validator
2. Fixed `strategy_escalation_tracker.py` - Changed to use `hookSpecificOutput` format and `{}` for no output
3. Fixed `PostToolUse_file_activity_tracker.py` - Changed `result = {"passed": True}` to `result = {}`
4. Removed incorrect `UserPromptSubmit_truth_validator.py` from PostToolUse registration
5. Updated `settings.json` - Registered new `PostToolUse_truth_validator.py`
6. Fixed all `echo` commands in `settings.json` - Changed from bare `echo` to `python -c "import json; print(json.dumps({}))"` to output valid JSON

**Files changed:**
- `PostToolUse_truth_validator.py` (NEW) - PostToolUse-compatible version
- `strategy_escalation_tracker.py` - Fixed JSON output format
- `PostToolUse_file_activity_tracker.py` - Fixed JSON output format
- `PostToolUse_system2.py` - Fixed JSON output format (changed `result = {"passed": True, "action": "pass"}` to `result = {}`)
- `settings.json` - Updated hook registrations

**Correct PostToolUse JSON format:**
```python
# With output:
{
    "hookSpecificOutput": {
        "hookEventName": "PostToolUse",
        "additionalContext": "message"
    }
}

# Without output:
{}
```

### Added: Symlink Blocking

**Problem addressed:** Symlinks create fragile path references and security concerns in workspace.

**Resolution:** Added symlink detection to path resolution orchestrator with clear error message.

**Files changed:**
- `deny_root_write.py` - Added `SYMLINK_CREATING_COMMANDS` list and `is_symlink_creating_command()` function
- `PreToolUse_directory_policy.py` - Added symlink detection (mirror of module)
- `path_resolution_orchestrator.py` - Added symlink check in Bash validation

**Blocked commands:**
- Windows: `mklink`
- Unix: `ln -s`, `ln`
- PowerShell: `New-Item -ItemType SymbolicLink`

### Added: CKS Model Pre-Load

**Problem addressed:** CKS queries had 6.8s delay due to model loading on first use.

**Resolution:** SessionStart hook pre-loads sentence transformer model with local caching.

**Files added:**
- `SessionStart_cks_preload.py` - Model pre-load with multi-terminal lock
- `_cks_cache.py` - File-based caching module
- `profile_cks.py` - CKS performance profiling
- `tests/test_cks_preload.py` - Unit tests for pre-load
- `tests/test_cks_cache_verification.py` - Cache verification tests

**Configuration:**
- `settings.json` - Added `SENTENCE_TRANSFORMERS_HOME`, `TRANSFORMERS_CACHE`, `HF_HOME` env vars

**Cache location:** `P:\.model_cache\`

**Performance:**
- First session: ~6.8s (download)
- Subsequent sessions: ~0.5s (load from cache)

### Updated: Documentation

**Files changed:**
- `README.md` - Added symlink blocking (#15) and CKS pre-load (#16) to hooks catalog
- `CLAUDE.md` - CKS auto-retrieval already documented

---

## 2026-01-27

### Added: Behavioral Quality Gate System (v3.0.0)

**Problem addressed:** AI exhibits several behavioral anti-patterns:
1. Tool thrashing (reading same file 3x without synthesis)
2. Lazy fix proposals ("quick fix", "bypass", "workaround")
3. Premature solution offers ("Want me to do it?") before understanding
4. Question-type mismatch (verbose response to binary question)

**Resolution:** Three-component system using word-boundary detection + LLM self-prompt approach (consistent with existing hooks).

**New files:**
- `anti_sycophancy/lazy_closure_detector.py` - Extended with `LAZY_FIX_PHRASES` and `PREMATURE_OFFER_PHRASES`
- `posttooluse/tool_thrashing_tracker.py` - In-process tracker for overlapping file reads
- `StopHook_behavioral_quality_gate.py` - Unified Stop hook checking all gaps

**Router updates:**
- `posttooluse/__init__.py` - Added ToolThrashingTracker to registry
- `Stop_router.py` - Added StopHook_behavioral_quality_gate.py to HOOK_SEQUENCE
- `UserPromptSubmit_router.py` - Clears turn state on new user message

**Pattern examples detected:**
| Pattern | Type | Self-prompt |
|---------|------|-------------|
| "5-line fix" | lazy_fix | "Does this address root cause or patch symptoms?" |
| "Want me to do it?" | premature_offer | "Did you complete Investigation Gate?" |
| Same file read 3x | thrashing | "Synthesize findings before re-reading" |
| Binary Q → verbose A | question_mismatch | "Answer the question first, then elaborate" |

**Environment variables:**
```bash
LAZY_CLOSURE_DETECTOR_ENABLED=true
TOOL_THRASHING_TRACKER_ENABLED=true
BEHAVIORAL_QUALITY_GATE_ENABLED=true
```

---

## 2026-01-26

### Fixed: Structural verification for error explanations (v2.1.0)

**Pre-mortem issue:** The merged `speculation_gate.py` only checked text patterns (did response mention "Read()"?) instead of actual tool calls (was Read tool invoked?).

**Resolution:** Added `ToolSequenceManager` integration to check recent tool calls structurally.

**Files changed:**
- `speculation_gate.py` - Added VERIFICATION_TOOLS set, ToolSequenceManager import, structural check before text fallback

**Verification logic (v2.1.0):**
```python
# Primary: Structural verification (did tool actually get called?)
recent_tools = ToolSequenceManager.get_recent(20)
has_structural_verification = bool({t["name"] for t in recent_tools} & VERIFICATION_TOOLS)

# Fallback: Text pattern verification (less reliable)
has_text_verification = any(re.search(p, content) for p in SOURCE_READ_PATTERNS)
```

### Fixed: Orphaned references cleanup

**Files archived:**
- `tests/test_error_gate.py` → `archive/test_error_gate.py`
- `tests/error_explanation_gate_tests.md` → `archive/error_explanation_gate_tests.md`

**Files updated:**
- `CLAUDE.md` - Updated hook references from `error_explanation_gate.py` to `speculation_gate.py`

### Fixed: Cache cleanup

Removed `__pycache__` directories to prevent stale bytecode issues.

---

### Merged: error_explanation_gate → speculation_gate (v2.0.0)

**Issue:** `error_explanation_gate.py` was misconfigured as a PostToolUse hook, but PostToolUse hooks don't have access to response text. The hook also lacked a `main()` entry point, causing "hook error" messages on every Bash execution.

**Resolution:**
1. **Merged** unique error-explanation patterns into `speculation_gate.py` (Stop phase)
2. **Removed** non-functional PostToolUse configuration from `settings.json`
3. **Archived** `error_explanation_gate.py` to `archive/error_explanation_gate.py`
4. **Updated** implementation documentation

**Files changed:**
- `speculation_gate.py` - Added ERROR_EXPLANATION_PATTERNS, version bumped to v2.0.0
- `settings.json` - Removed error_explanation_gate from PostToolUse hooks
- `error_explanation_gate.py` - Moved to `archive/`
- `error_explanation_gate_IMPLEMENTATION.md` - Updated with archive notice

**Patterns moved to speculation_gate.py:**
```python
ERROR_EXPLANATION_PATTERNS = [
    r"(?:can't|cannot|couldn't|unable to) access",
    r"workspace restrict(?:ion)?s?",
    r"permission denied",
    r"(?:path|file|directory) (?:doesn't|does not|isn't|is not) exist",
    r"no such file or directory",
]
```

**Impact:** The "PostToolUse:Bash hook error" messages should no longer appear. Error explanation detection now runs in the Stop phase where response text is available.

---

## Legend

- **Merged:** Functionality consolidated into another hook
- **Archived:** Hook moved to `archive/` directory (not deleted for history)
- **Fixed:** Bug resolved
- **Added:** New hook or feature
- **Removed:** Hook permanently deleted
