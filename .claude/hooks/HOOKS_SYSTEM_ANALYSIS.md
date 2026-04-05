# Hooks System Configuration and Data Analysis

**Analysis Date**: 2026-03-07
**Path**: `P:/.claude/hooks/`

---

## 1. Configuration Files

### Core Configuration

#### `domains.json`
**Purpose**: Maps hook domains to their constituent hooks with priorities and enablement status.

**Structure**:
```json
{
  "domains": {
    "safety": { "enabled": true, "priority": -999, "hooks": [...] },
    "git": { "enabled": true, "priority": 100, "hooks": [...] },
    "cognitive": { "enabled": true, "priority": 200, "hooks": [...] },
    "process": { "enabled": true, "priority": 300, "hooks": [...] }
  }
}
```

**Domains**:
- **safety** (priority: -999): Safety routers, truth validators, command directives
- **git** (priority: 100): Commit reminders, forgetfulness checks
- **cognitive** (priority: 200): Falsification injectors, doubt signals, infrastructure gates
- **process** (priority: 300): Periodic reminders, retrospectives, TDD evaluation

#### `metadata.json`
**Purpose**: Hook metadata including layer assignments, state I/O patterns, blocking behavior, and criticality.

**Metadata Fields**:
- `name`: Hook identifier
- `layer`: Execution layer (0, 1a_debug, 1b_git, 2_explore, etc.)
- `priority`: Execution order (lower = earlier)
- `blocking`: Whether hook can block operations
- `writes_state`: State files this hook writes
- `reads_state`: State files this hook reads
- `critical`: Whether hook is critical for system operation
- `description`: Human-readable hook purpose

**Key Hooks Documented**:
- `PreToolUse_tdd_gate` - TDD enforcement (layer: 0, priority: 100, blocking: true)
- `PostToolUse_system2` - Error detection and System 2 prompts (layer: 1_system2)
- `PostToolUse_drift_detector` - Monitors agent alignment with goal
- `PostToolUse_shadow_verifier` - Async test/syntax check on file edits

#### `config/directory_policy.json`
**Purpose**: Single source of truth for directory structure policy across the entire workspace.

**Version**: 3.1.0 (2026-02-13)

**Key Sections**:
- **workspace_root**: P:/ root level policy (required dirs, allowed configs, blocked patterns)
- **claude_directory**: P:/.claude structure policy (subdirectories, allowed files)
- **csf_nip_root**: P:/__csf as workspace root (required dirs, consolidation rules)
- **module_filename_patterns**: Patterns indicating reusable modules vs slash commands
- **protected_system_paths**: System paths that should never be written to
- **semantic_routing**: Intelligent file placement based on content type
- **claude_restricted_paths**: Paths reserved for user-authored content

**Blocked Root Patterns** (examples):
- `temp/` → belongs in `__csf/temp/`
- `test_*.py` → belongs in `tests/`
- `P:*.py` → path corruption from copy-paste error
- `*_report_*.json` → AI-generated reports (7-day max age)

#### `cognitive_enhancers_config.json`
**Purpose**: Configuration for cognitive enhancement hooks including FAP detection and topic routing.

**Settings**:
- **FAP Detection**: `fap_semantic_enabled`, `fap_similarity_threshold: 0.85`
- **Topics**: implementation, diagnostic, meta_rca, decomposition
- **Enhancers**: assumption_surfacing, outcome_anchoring, inversion_prompting, chestertons_fence
- **Limits**: `max_enhancers_per_prompt: 3`, `min_prompt_length: 30`
- **Modes**: #rca (meta_rca), #deep (implementation), #fast (disable all)

#### `research_router_config.json`
**Purpose**: Configuration for research routing to determine when research is required.

**Research Keywords** (triggers):
- "best way to", "fastest way to", "alternatives to", "tradeoffs between"
- "compare", "architecture for", "design for", "scaling strategy"
- "optimize performance", "performance bottleneck"

**Local Tools**: Bash, Grep, mcp__serena_serena__search

**Escape Phrases**: "no research", "local only", "skip research"

#### `critical_hooks.json`
**Purpose**: Lists critical hooks requiring comprehensive test coverage (unit + integration).

**Critical Hooks**:
- `assumption_audit_v2` - Anti-confabulation verification
- `StopHook_cross_validator` - Empirical verification enforcement
- `Stop_absence_claim_gate` - Absence assertion verification
- `tdd95_core` - TDD-95 state management
- `PreToolUse_tdd95_gate` - Evidence-based TDD enforcement

---

## 2. Test Structure

### Test Organization

#### Main Test Directory: `tests/`

**Test Categories**:

1. **Hook Integration Tests** (40+ files)
   - `test_hook_base.py` - Base hook functionality
   - `test_hook_runner.py` - Hook execution framework
   - `test_hook_validator.py` - Hook validation logic
   - `test_hook_registration.py` - Hook registration verification
   - `test_hook_loading.py` - Dynamic hook loading
   - `test_in_process_hooks.py` - In-process hook execution

2. **Specific Hook Tests** (100+ files)
   - **TDD Hooks**: `test_tdd95_core_unit.py`, `test_pretooluse_integration.py`
   - **Authorization**: `test_authorization_gate_safe_patterns.py`
   - **Behavioral**: `test_behavioral_prevention.py`, `test_behavioral_protocol.py`
   - **Cleanup**: `test_cleanup_verifier.py`
   - **Documentation**: `test_PostToolUse_documentation_validator.py`
   - **Dreaming Daemon**: `test_dreaming_daemon.py`, `test_dreaming_state.py`
   - **Intent**: `test_intent_classifier.py`, `test_intent_integration.py`
   - **Research**: `test_research_router.py`
   - **Router**: `test_router.py` (46KB comprehensive router tests)
   - **Skill Enforcement**: `test_skill_pattern_gate_coverage.py`
   - **Strawberry Validator**: `test_strawberry_validator.py`
   - **Unverified Stance**: `test_unverified_stance_detector.py`

3. **Constitutional Hooks Tests**
   - `test_assumption_audit.py`
   - `test_constitutional_enforcer.py`
   - `test_block_protocol.py`
   - `test_empirical_claims_gate.py`

4. **Validation and Verification**
   - `test_edit_verifier.py`
   - `test_artifact_validation_hooks.py`
   - `test_integration_verifier.py`
   - `test_observable_effect_verifier.py`

5. **System Integration Tests**
   - `test_session_manager.py` (28KB)
   - `test_transcript_extraction.py`
   - `test_task_context_enhancement.py` (78KB)
   - `test_unified_claim_verifier.py`

6. **Feature-Specific Tests**
   - **Handoff**: `test_handoff_hooks.py`
   - **Lazy Workaround Gate**: `test_lazy_workaround_gate.py`
   - **Memory Monitor**: `test_SessionStart_memory_monitor.py`
   - **Principle Monitor**: `test_principle_monitor.py`

#### Deprecated Tests: `tests/deprecated/`

**Purpose**: Archive for tests that reference deleted hooks or obsolete architecture.

**Why Deprecated**:
1. Deleted hooks during consolidation
2. Consolidated modules (merged/reorganized)
3. Architectural changes making tests obsolete

**Files**: 100+ deprecated test files including:
- `test_PreToolUse_anti_bleed_gate.py`
- `test_assumption_audit_v2_scope.py`
- `test_edit_verifier.py` (large suite, 43KB)
- `test_secret_scanner.py`
- `test_unparseable_command_gate.py`

**Migration Reference**: Current tests reference main routers (PreToolUse.py, PostToolUse.py, etc.)

---

## 3. State and Data

### State Directory: `.state/`

**Purpose**: Hook runtime state (isolated from source code)

**Key State Files**:
- `tdd-state/` - TDD cycle state files (tdd_state_guard.py)
- `debug_session_state.json` - Error tracking (PostToolUse_system2.py)
- `task-identity/` - Task recovery state (task_identity_manager.py)
- `explore-detector/` - Exploration detection state
- `guidance-cache/` - Cached guidance responses
- `self_reflection_state.json` - Self-reflection tracking
- `strategy_escalation_state.json` - Escalation state

### Session Data Directory: `session_data/`

**Purpose**: Session runtime data and persistent storage

**Key Files**:
- `evidence.db` (60MB) - Evidence collection database
- `audit.db` (0 bytes) - Audit database (empty)
- `enforcement_state.json` - Hook enforcement tracking
- `goal_state.json` - Goal tracking state
- `intent_state.json` - Intent tracking
- `investigation_state.json` - Investigation state
- `active_command.json` - Active command tracking
- `reflexion_retries.json` - Reflexion retry tracking
- `stop_block_cooldown.json` - Stop hook cooldown state
- `enforcement_events.jsonl` (521KB) - Enforcement event log
- `reflexion_evidence.jsonl` (4.8MB) - Reflexion evidence log

**Subdirectories**:
- `evidence/` - Evidence collection storage
- `evidence_spool/` - Temporary evidence spooling

### Data Directory: `data/`

**Purpose**: Runtime data (events, caches, benchmarks)

**Key Files**:
- `causal_learning.json` - Causal learning state
- `debug_session_state.json` - Debug session tracking
- `hook_baseline.json` - Hook performance baseline
- `post_debug_input.json` - Debug input state
- `strategy_escalation_state.json` - Strategy escalation state

**Subdirectories**:
- `explore-detector/` - Exploration detection data
- `guidance-cache/` - Guidance response cache
- `task-identity/` - Task identity data
- `tdd-state/` - TDD state data

---

## 4. Logs

### Logs Directory: `logs/`

**Purpose**: Runtime logs for hook behavior tracking and debugging

**Log Files** (by category):

#### Enforcement and Blocking
- `block_enforcement.jsonl` (408 lines) - Block enforcement events
- `constructional_blocks.jsonl` (1030 lines) - Constructional blocks
- `absence_claim_gate.jsonl` (111 lines) - Absence claim blocks
- `auth_blocks.jsonl` (2 lines) - Authorization blocks
- `skill_first_enforcement.jsonl` (73 lines) - Skill enforcement

#### Behavioral and Cognitive
- `assumption_audit_v2.jsonl` (676 lines) - Assumption audit logs
- `anti_sycophancy_violations.jsonl` (8 lines) - Anti-sycophancy violations
- `reasoning_profiles.jsonl` (44 lines) - Reasoning profile tracking
- `behavioral_quality_gate.log` - Behavioral quality logs

#### System Performance
- `parallel_execution.jsonl` (1314 lines) - Parallel execution tracking
- `enforcement.jsonl` (16 lines) - General enforcement logs

#### Research and Investigation
- `uninvestigated_question.log` - Uninvestigated questions
- `investigation_required.log` - Investigation requirements

#### Tool and Command Tracking
- `tool_thrashing.log` (94KB) - Tool thrash detection
- `windows_path_blocks.jsonl` (64KB) - Windows path blocks
- `windows_path_fixes.jsonl` (71KB) - Windows path fixes

#### Daemon Logs
- `dreaming-daemon.log` (4KB) - Dreaming daemon operations

#### Diagnostics Subdirectory
- `assumptions.jsonl` - Assumption tracking
- `cc_context.jsonl` - CC context data
- `cc_errors.jsonl` - CC error logs
- `hook_invocations.jsonl` - Hook invocation tracking

**Log Rotation**: Manual via `Rotate-HookLogs.ps1 -RetentionDays 7`

---

## 5. Evidence Collection

### Evidence Directory: `evidence/`

**Purpose**: Evidence collection and migration tracking

**Structure**:
- `__init__.py` - Evidence module initialization
- `migrate.py` - Evidence migration utilities
- `T-006/` - Task T-006 evidence (green.md, red.md, refactor.md, verify.md)
- `step_08_phase1_imports/` - Phase 1 import evidence
- `step_08_phase2_parallel/` - Phase 2 parallel execution evidence

**Evidence Types**:
1. **Task Evidence** (T-006/): Green/red/refactor/verify documentation
2. **Phase Evidence**: Implementation phase tracking
3. **Migration Evidence**: Schema and data migration records

---

## 6. Archive Analysis

### Archive Directory: `_archive/`

**Purpose**: Historical reference for dissolved/migrated systems

#### Key Archived Systems

##### `/analyze` Command System (archived 2026-02-25)
**Documentation**: `ANALYZE_COMMANDS_ARCHIVE.md`

**Archived Components** (10 core scripts):
- `analyze_assumption_audit.py` → Migrated to `/r` (Remember/Refine)
- `analyze_audit_compliance.py` → Migrated to `/p6` (Security Phase)
- `analyze_blocks.py` → Migrated to `/r` + `/debugRCA`
- `analyze_error_attribution.py` → Migrated to `/debugRCA` Phase 1
- `analyze_hooks.py` → Migrated to `/debugRCA` Phase 1
- `analyze_speculation.py` → Migrated to `/r` (Narrative Intent Detector)

**Migration Tasks**: #1065, #1066, #1073, #1074

##### Archived PostToolUse Hooks (40+ files)
**Patterns Observed**:
- **Adversarial Verification**: `PostToolUse_adversarial_verification.py`
- **Change Verification**: `PostToolUse_change_verification.py`
- **CKS Integration**: `PostToolUse_CKS.py`, `PostToolUse_cks_storage.py`
- **Artifact Tracking**: `PostToolUse_artifact_tracker.py`
- **Bash Routing**: `PostToolUse_bash_router.py`
- **Backup Systems**: `PostToolUse_auto_backup.py`

**Archival Reasons**:
1. **Consolidation**: Functionality merged into main routers
2. **Obsolescence**: Replaced by new architectural patterns
3. **Performance**: Optimized away with newer implementations
4. **Complexity**: Simplified into fewer, more capable hooks

**Documentation**:
- `SESSION_COMPACTION.md` - Session compaction archive notes
- `STOP_HOOK_TRANSCRIPT_PROBLEM.md` - Stop hook transcript issues

---

## 7. Configuration Integration

### Environment Variable Integration

**Key Environment Variables** (from `settings.json`):
- `CONSTITUTIONAL_HOOKS_BYPASS` - Bypass all constitutional hooks
- `CLEANUP_VERIFIER_ENABLED` - Enable cleanup verification
- `CLEANUP_VERIFIER_MODE` - Warn vs block mode
- `INTEGRATION_VERIFIER_ENABLED` - Enable integration verification
- `SEV_ENABLED` - Enable observable effect verifier
- `STRAWBERRY_VALIDATOR_VERBOSE` - Verbose mode for strawberry validator
- `UNVERIFIED_STANCE_ENABLED` - Enable unverified stance detection
- `TEST_LOCATION_GATE_ENABLED` - Enable test location gate

### Router Pattern Integration

**Router Files**:
- `UserPromptSubmit_router.py` - Consolidates UserPromptSubmit hooks
- `PreToolUse.py` - Main PreToolUse router
- `PostToolUse_router.py` - Consolidates PostToolUse hooks
- `Stop.py` - Main Stop router
- `SessionStart.py` - Main SessionStart router

**Hook Registration**:
1. Export `process_prompt()` function
2. Register in router's `import_hook()` function
3. Add to `HOOK_PRIORITY` and `HOOK_DISPATCH` dictionaries
4. Create runner function (if non-trivial)

---

## 8. System Architecture

### Hook Layers

| Layer | Purpose | Hooks |
|-------|---------|-------|
| 0 | Prerequisites | TDD gate |
| 1a_debug | Debug warnings | Debug warning |
| 1b_git | Git safety | Commit guard |
| 2_explore | Exploration | Explore gate |
| 1_system2 | System 2 monitoring | System 2 |
| 1_monitoring | Monitoring | Drift detector, shadow verifier |
| 2_tracking | Tracking | File activity tracker |

### State Management

**State File Patterns**:
- `{hook_name}_state.json` - Hook-specific state
- `session_activities/*.json` - Session-based activity tracking
- `tdd_*.json` - TDD state files
- `debug_session_state.json` - Error tracking state

**Session Isolation**:
- Terminal-specific state directories
- Time-based session expiry (2 hours inactivity)
- Cross-terminal bleed prevention

### Evidence and Verification

**Verification Stack**:
1. User Context (authoritative)
2. Local Artifacts (files read, tool outputs)
3. Codebase Facts (SKILL.md, CLAUDE.md)
4. Tool Results (Grep, Glob outputs)
5. External Sources (web search, fetched URLs)

**Evidence Collection**:
- `evidence.db` (60MB) - Central evidence database
- JSONL logs for structured evidence tracking
- Evidence spooling for temporary storage
- TTL-based cleanup (7 days default)

---

## 9. Testing Patterns

### Test Conventions

**Naming Patterns**:
- `test_<hook_name>.py` - Basic hook tests
- `test_<module>_unit.py` - Unit tests
- `test_<module>_integration.py` - Integration tests
- `test_<feature>_e2e.py` - End-to-end tests

**Test Fixtures**: `tests/fixtures/`

**Benchmarking**: `tests/.benchmarks/`

### Coverage Requirements

**Critical Hooks**: Must have unit + integration tests
**Standard Hooks**: Unit tests required
**Advisory Hooks**: Basic functionality tests

### Test Execution

```bash
# Run hook diagnostics
python P:/.claude/hooks/hook_diagnostics.py

# Check recent logs
python P:/.claude/hooks/shared_utils.py logs --limit 50

# Run pytest suite
pytest P:/.claude/hooks/tests/ -v
```

---

## 10. Maintenance and Operations

### Log Analysis

**PowerShell Queries**:
```powershell
# Recent enforcement decisions
.\..\scripts\Query-EnforcementLogs.ps1 -Minutes 30

# Find all blocks today
Get-Content enforcement.jsonl | ConvertFrom-Json | Where-Object { $_.decision -eq "block" }

# Count by hook
Get-Content enforcement.jsonl | ConvertFrom-Json | Group-Object hook | Sort-Object Count -Descending
```

### Cleanup Operations

**Auto-Cleanup Policies**:
- Backup files: 7 days max age
- Reports: 7 days max age
- Research files: 7 days max age
- Log files: 7 days max age
- Staging files: 30 days max age

### Health Checks

**Hook Health Monitoring**:
- `SessionStart_hook_health_check.py` - Hook health verification
- `SessionStart_hook_import_health.py` - Import health checks

---

## Summary

The hooks system is a sophisticated cognitive steering framework with:

- **45+ JSON configuration files** controlling behavior, domains, and policies
- **300+ test files** covering unit, integration, and end-to-end scenarios
- **60+ state files** tracking session data, evidence, and enforcement
- **40+ archived hooks** documenting architectural evolution
- **Comprehensive logging** with JSONL structured logs for analysis
- **Evidence collection** system with 60MB database
- **Router-based architecture** consolidating hooks by event type
- **Layer-based execution** with priority-based ordering
- **Session isolation** preventing cross-terminal interference
- **Automated cleanup** with TTL-based policies

The system demonstrates professional software engineering practices with comprehensive testing, structured logging, evidence-based verification, and clear separation of concerns.
