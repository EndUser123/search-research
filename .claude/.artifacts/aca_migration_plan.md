# ACA Migration Plan — Agent Control Architecture

**Date:** 2026-05-22
**Status:** Phase 1 complete, awaiting Phase 5 pilot approval

---

## 1. FACTS

### What was inspected
- `P:/.claude/hooks/` — 338 top-level Python files, 90+ `__lib/` shared modules
- `P:/.claude/settings.json` — 42 registered hooks across 9 lifecycle events
- Plugin hooks: 5 plugins with hook registrations (fact-guard, skill-guard, snapshot, cc-skills-sdlc, prompt-enhancer)
- `Stop.py` — 4801-line router with 44 `_run_*` gate functions
- `PreToolUse.py` — main PreToolUse dispatcher
- `PostToolUse.py` — main PostToolUse dispatcher
- `__lib/` — 90 shared modules providing runtime infrastructure

### Registration structure
Claude Code hooks use a nested format in settings.json:
```json
{"matcher": "...", "hooks": [{"type": "command", "command": "python <path>", "timeout": N}]}
```
Most hooks are invoked via `__lib/hook_runner.py` wrapper, which provides error handling and timeout enforcement.

### Key finding: Stop.py is the monolith
Stop.py contains 44 gate functions spanning ALL domains — reasoning, epistemic, safety, authority, SDLC, observability. It cannot be split until the other ACA plugins exist, because it references shared gate metadata, telemetry, and state management inline.

### What remains uncertain
- Exact cross-domain dependencies between `__lib/` modules (only top-level analysis done)
- Whether `plugin hooks.json` registration is reliable in current Claude Code version
- Whether some `__lib/` modules are used by only 1 domain (should be moved into that domain) vs. 3+ (should stay shared)

---

## 2. ACA CLASSIFICATION TABLE

### cc-aca-reasoning (6 hooks)
| Hook | Lifecycle | Confidence | Shared State | Rationale |
|------|-----------|------------|-------------|-----------|
| Start_reasoning_mode_selector.py | UserPromptSubmit | high | no | Selects reasoning mode at start of turn |
| PreToolUse_sequential_thinking.py | PreToolUse | high | yes: sequential_state | Manages sequential thinking iteration count |
| Stop_reasoning_quality_gate.py | Stop | high | no | Automatic reasoning quality gate at stop |
| StopHook_sequential_thinking.py | Stop | high | yes: sequential_state | Sequential thinking iteration management |
| posttooluse_self_reflection_reminder.py | PostToolUse | medium | no | Self-reflection reminder after edits |
| anti_lazy_diff_nudge.py | PostToolUse | medium | no | Anti-lazy nudge on trivial diffs |

### cc-aca-epistemic (8 hooks)
| Hook | Lifecycle | Confidence | Shared State | Rationale |
|------|-----------|------------|-------------|-----------|
| PreToolUse_evidence_hierarchy_gate.py | PreToolUse | high | no | Enforces evidence hierarchy for queries |
| PreToolUse_stop_epistemic_contract.py | PreToolUse | high | yes: investigation_state | Epistemic contract enforcement |
| PostToolUse_claim_verifier_smoke.py | PostToolUse | high | no | Verifies claims against tool evidence |
| self_verification_gate.py | PostToolUse | high | no | Self-verification after edits |
| SessionStart_cc_health.py | SessionStart | medium | no | Epistemic gate health surfacing |
| fact-guard_PreToolUse.py | PreToolUse | high | no | Blocks unsupported literals |
| fact-guard_PostToolUse.py | PostToolUse | high | yes: fact ledger | Records observed facts |
| provenance_verifier.py | PreToolUse | high | no | External M2.7 LLM provenance |

### cc-aca-session (10 hooks)
| Hook | Lifecycle | Confidence | Shared State | Rationale |
|------|-----------|------------|-------------|-----------|
| SessionStart_verification_cleanup.py | SessionStart | high | yes: state files | Verification state cleanup |
| SessionStart_breadcrumb_init.py | SessionStart | high | yes: breadcrumb state | Initialize breadcrumb tracking |
| SessionEnd_cleanup.py | SessionEnd | high | yes: state files | Janitor cleanup at session end |
| SessionEnd_breadcrumb_cleanup.py | SessionEnd | high | yes: breadcrumb state | Breadcrumb trail cleanup |
| SessionEnd_tdd_cleanup.py | SessionEnd | high | yes: tdd state | Terminal-isolated TDD cleanup |
| PreCompact.py | PreCompact | high | no | PreCompact stub (deprecated) |
| snapshot_PreCompact.py | PreCompact | high | yes: snapshot state | Snapshot before compaction |
| snapshot_SessionStart.py | SessionStart | high | yes: snapshot state | Session resume via snapshot |
| snapshot_SessionEnd_tldr.py | SessionEnd | high | no | TLDR generation |
| snapshot_UserPromptSubmit.py | UserPromptSubmit | high | yes: snapshot state | Snapshot context injection |

### cc-aca-authority (10 hooks)
| Hook | Lifecycle | Confidence | Shared State | Rationale |
|------|-----------|------------|-------------|-----------|
| PreToolUse_authorization_gate.py | PreToolUse | high | yes: auth state | Blocks destructive commands |
| PreToolUse_command_intent_gate.py | PreToolUse | high | yes: intent state | Validates bash matches intent |
| PreToolUse_delegation_gate.py | PreToolUse | high | yes: delegation state | Subagent delegation management |
| PreToolUse_skill_first_gate.py | PreToolUse | high | yes: skill intent | Skill-first mode enforcement |
| PreToolUse_ask_first_tool_gate.py | PreToolUse | medium | no | Ask-first tool availability |
| PreToolUse_plan_consumer_gate.py | PreToolUse | high | yes: phase ledger | Plan consumption validation |
| stop_permission_stall.py | Stop | high | no | Permission-seeking stall detection |
| skill-guard_PreToolUse.py | PreToolUse | high | yes: skill exec state | Skill dispatch enforcement |
| skill-guard_Stop.py | Stop | high | yes: skill exec state | Skill completion verification |
| skill-guard_UserPromptSubmit.py | UserPromptSubmit | high | yes: skill intent | Slash command routing |

### cc-aca-investigation (6 hooks)
| Hook | Lifecycle | Confidence | Shared State | Rationale |
|------|-----------|------------|-------------|-----------|
| PreToolUse_investigation_gate.py | PreToolUse | high | yes: investigation_state | Blocks writes to uninvestigated files |
| PreToolUse_discovery_tracker.py | PreToolUse | high | yes: discovery state | Discovery coverage tracking |
| PreToolUse_git_state_capture.py | PreToolUse | medium | yes: git state | Git status capture before mods |
| PreToolUse_implementation_default_gate.py | PreToolUse | medium | yes: intent state | Gates implementation w/o investigation |
| tool_availability_checker.py | PreToolUse | medium | no | Tool availability checking |
| PreToolUse_file_existence_guard.py | PreToolUse | high | no | Guards non-existent file operations |

### cc-aca-sdlc (11 hooks)
| Hook | Lifecycle | Confidence | Shared State | Rationale |
|------|-----------|------------|-------------|-----------|
| PostToolUse_tdd_state.py | PostToolUse | high | yes: tdd state | TDD phase transitions |
| PostToolUse_tdd_state_tracker.py | PostToolUse | high | yes: tdd state | TDD state persistence |
| StopHook_tdd_continuation.py | Stop | high | yes: tdd state | TDD workflow reminder |
| PreToolUse_tdd_gate.py | PreToolUse | high | yes: tdd state | TDD phase enforcement |
| PreToolUse_refactor_transition.py | PreToolUse | high | yes: refactor state | Refactor phase transitions |
| PostToolUse_documentation_validator.py | PostToolUse | medium | no | Documentation quality |
| post/PostToolWrite_doc_validator.py | PostToolUse | medium | no | Doc validation after writes |
| PreToolUse_arch_first_enforcer.py | PreToolUse | medium | yes: arch state | Architecture-first enforcement |
| cc-skills-sdlc_PreToolUse.py | PreToolUse | high | yes: refactor state | SDLC transition dispatching |
| cc-skills-sdlc_PostToolUse.py | PostToolUse | high | yes: refactor state | SDLC validation dispatching |
| cc-skills-sdlc_Stop.py | Stop | high | yes: refactor state | SDLC verifier dispatching |

### cc-aca-safety (12 hooks)
| Hook | Lifecycle | Confidence | Shared State | Rationale |
|------|-----------|------------|-------------|-----------|
| PreToolUse_destructive_git_guard.py | PreToolUse | high | no | Destructive git operation guard |
| PreToolUse_git_safety.py | PreToolUse | high | no | Git safety (forgettables, etc) |
| PreToolUse_git_auto_stage.py | PreToolUse | high | no | Auto-stage before risky ops |
| PreToolUse_git_remote_check_order_guard.py | PreToolUse | high | no | Local-first remote checking |
| PreToolUse_bulk_delete_gate.py | PreToolUse | high | no | Bulk delete protection |
| PreToolUse_directory_policy.py | PreToolUse | high | no | Directory access policy |
| PreToolUse_secret_scanner.py | PreToolUse | high | no | Secret scanning |
| PreToolUse_powershell_validator.py | PreToolUse | high | no | PowerShell argument validation |
| PostToolUse_bash_syntax_gate.py | PostToolUse | high | no | Bash syntax post-validation |
| PreToolUse_dependency_verification_gate.py | PreToolUse | medium | no | Dependency safety verification |
| PreToolUse_bash_syntax_validator.py | PreToolUse | high | no | Bash syntax pre-validation |
| PreToolUse_ownership_colocation_gate.py | PreToolUse | high | no | Infra placement guard |

### cc-aca-observability (18 hooks)
| Hook | Lifecycle | Confidence | Shared State | Rationale |
|------|-----------|------------|-------------|-----------|
| log_hook.py | All | high | yes: log files | Structured logging |
| PostToolUse_router.py | PostToolUse | high | yes: artifact ledger | Post-tool tracking router |
| PostToolUse_artifact_validator.py | PostToolUse | high | yes: artifact ledger | Artifact integrity |
| PostToolUse_artifact_scraper.py | PostToolUse | high | yes: artifact ledger | Artifact extraction |
| PostToolUse_artifact_access_tracker.py | PostToolUse | high | yes: access log | File access tracking |
| PostToolUse_e2e_tracker.py | PostToolUse | high | yes: e2e state | E2E workflow tracking |
| PostToolUse_breadcrumb_tracker.py | PostToolUse | high | yes: breadcrumb state | Breadcrumb trail updates |
| PreToolUse_breadcrumb_gate.py | PreToolUse | high | yes: breadcrumb state | Breadcrumb progression |
| PreToolUse_breadcrumb_verifier.py | PreToolUse | high | yes: breadcrumb state | Breadcrumb verification |
| PreToolUse_domain_tool_router.py | PreToolUse | medium | no | Search tool suggestions |
| PostToolUse_p2_filter_gate.py | PostToolUse | medium | no | P2 evidence filtering |
| PostToolUse_adversarial_aggregate.py | PostToolUse | medium | no | Adversarial review aggregation |
| PostToolUse_powershell_validator.py | PostToolUse | medium | no | PowerShell validation tracking |
| PostToolUse_wrapper_validator.py | PostToolUse | medium | no | Wrapper pattern validation |
| cjk_drift_detector.py | Multi | high | yes: drift state | CJK drift detection |
| Stop_diagnostic_analysis_quality_gate.py | Stop | medium | no | Diagnostic quality metrics |
| Notification_voice_hook.py | Notification | high | no | Voice notifications |
| judge_feedback.py | SessionStart | high | yes: judge state | Judge feedback processing |

### cc-aca-core (3 dispatchers + ~40 shared modules)
| Hook | Lifecycle | Confidence | Rationale |
|------|-----------|------------|-----------|
| PreToolUse.py | PreToolUse | high | Main PreToolUse dispatcher/router |
| PostToolUse.py | PostToolUse | high | Main PostToolUse dispatcher |
| Stop.py | Stop | high | Main Stop router (44 gates, all domains) |

**Shared `__lib/` modules by domain affinity:**
- Core (used by 3+ domains): hook_runner, hook_importer, hook_base, hook_ledger, shared_helpers, state_file_manager, state_paths, session_detection, session_manager, terminal_detection, runtime_env, file_lock, log_rotation, subprocess_helper, path_utils, path_classifier
- Epistemic: behavioral_protocol, claim_classifier, claim_layer_map, claim_patterns, epistemic_applicability, epistemic_validator, evidence_collector, unified_evidence_enforcer, validation_cache, runtime_claims, verification/
- Reasoning: cognitive_tag_helper, sequential_state, token_budget, trivial_turns, turn_mode, phase_machine, response_intent, suggestion_utils
- Session: behavioral_state, commitment_tracker, prompt_choice_state, prompt_session_state, session_constraints, migrate_legacy_state, memory_monitor
- Safety: bash_allowlist_validator, dx_tools_locking, git_guard_config, git_helper, worktree_helper, write_fix, write_tool_error_signal, type_validator, syntax_fixer, argument_forwarding_validator, pre_tool_use_logic, path_validator, protected_paths, protection_state
- SDLC: characterization_engine, test_generator, test_hook, binary_assertions, api_breakage_detector, task_contract, task_identity_manager, task_repository_client, task_self_doc_validator
- Observability: artifact_ledger, artifact_grounder, dx_tools_observability, pretooluse_observability, enforcement_telemetry, enforcement_rate_limiter, quality_log, stop_gate_telemetry, rsn_formatter, external_judge, judge_feedback, contract_health, semantic_matcher_llm

---

## 3. SHARED INFRASTRUCTURE

### Should remain shared (cc-aca-core or `__lib/`)
- `hook_runner.py` — universal hook execution wrapper
- `hook_importer.py` — in-process hook executor
- `hook_base.py` — base class pattern for hooks
- `hook_ledger.py` — enforcement ledger used across all domains
- `shared_helpers.py` — utility functions used by 10+ hooks
- `state_file_manager.py` / `state_paths.py` — state file operations
- `session_detection.py` / `session_manager.py` — session ID resolution
- `terminal_detection.py` / `terminal_id.py` — terminal ID resolution
- `runtime_env.py` — environment variable access
- `file_lock.py` — cross-process file locking
- `log_rotation.py` — log rotation for all hooks
- `path_utils.py` / `path_classifier.py` — path normalization

### Should move into specific ACA plugins
- `epistemic_*` modules → cc-aca-epistemic
- `sequential_state.py`, `turn_mode.py` → cc-aca-reasoning
- `task_contract.py`, `test_generator.py` → cc-aca-sdlc
- `bash_allowlist_validator.py`, `git_*.py` → cc-aca-safety
- `artifact_ledger.py`, `*_telemetry.py` → cc-aca-observability

### Should NOT be abstracted yet
- `semantic_matcher_llm.py` — only used by 1-2 gates in Stop.py
- `location_optimizer.py` — migration tooling, not runtime
- `migrate_to_hook_base.py` — one-time migration helper
- `v2_config.py` — minimal config, unclear ownership

---

## 4. MIGRATION ORDER

Recommended safest order:

### 1. cc-aca-session (lowest coupling, highest cohesion)
- All hooks are lifecycle-specific (SessionStart/End/PreCompact)
- Minimal cross-domain dependencies
- State is self-contained (cleanup, breadcrumb init, snapshot)
- Easy to verify: session starts/ends still work

### 2. cc-aca-safety (clear boundary, no cross-domain state)
- All hooks are PreToolUse guards
- No shared state beyond read-only git status
- Self-contained responsibility (git safety, path safety, delete protection)
- Easy to verify: destructive commands still blocked

### 3. cc-aca-reasoning (small domain, clear responsibility)
- Only 6 hooks
- Shared state limited to sequential_state
- No cross-domain dependencies
- Easy to verify: reasoning mode selection still works

### 4. cc-aca-epistemic (medium coupling, clear purpose)
- 8 hooks including fact-guard plugin
- Some shared __lib/ modules (claim_classifier, evidence_collector)
- Must coordinate with Stop.py gate extraction
- Medium verification complexity

### 5. cc-aca-investigation (medium coupling, shared state with epistemic)
- 6 hooks, all PreToolUse
- investigation_state is shared with epistemic contract
- Should be done after epistemic to resolve shared state ownership

### 6. cc-aca-sdlc (medium complexity, existing plugin)
- 11 hooks, already partially in cc-skills-sdlc plugin
- State management (TDD, refactor) is self-contained
- Must coordinate with cc-skills-sdlc plugin structure

### 7. cc-aca-authority (high complexity, skill-guard integration)
- 10 hooks including skill-guard plugin
- Complex state management (delegation, intent, skill execution)
- Must integrate with skill-guard routing

### 8. cc-aca-observability (highest coupling, cross-cutting)
- 18 hooks spanning all lifecycle events
- log_hook.py fires on every event
- Breadcrumb state is read by multiple domains
- Should be last to avoid breaking observability during migration

### 9. cc-aca-core (final consolidation)
- Stop.py, PreToolUse.py, PostToolUse.py routers
- Must wait until all domain plugins exist
- Then routers become thin dispatchers to domain plugins

---

## 5. PILOT IMPLEMENTATION PLAN

**Chosen pilot: cc-aca-session**

### Why this plugin first
- 10 hooks, all lifecycle-specific (SessionStart/End/PreCompact/UserPromptSubmit)
- Minimal cross-domain dependencies (breadcrumbs shared with observability, but reads are safe)
- Self-contained state management
- Currently scattered across global hooks + snapshot plugin
- Easy to verify: session starts/ends still fire correctly

### Files to create

```
P:/packages/cc-aca-session/
├── .claude-plugin/
│   └── plugin.json
├── CLAUDE.md
├── hooks/
│   ├── hooks.json
│   ├── sessionstart/
│   │   ├── aca_session_verification_cleanup.py
│   │   ├── aca_session_breadcrumb_init.py
│   │   └── aca_session_health.py
│   ├── sessionend/
│   │   ├── aca_session_cleanup.py
│   │   ├── aca_session_breadcrumb_cleanup.py
│   │   └── aca_session_tdd_cleanup.py
│   ├── precompact/
│   │   └── aca_session_snapshot.py
│   └── userpromptsubmit/
│       └── aca_session_snapshot_inject.py
├── lib/
│   ├── __init__.py
│   └── state_paths.py
└── tests/
    └── test_session_hooks.py
```

### Compatibility shim approach
Since `plugin hooks.json` may be unreliable:
1. Plugin becomes **canonical source** of hook code
2. **Compatibility wrappers** in `P:/.claude/hooks/` delegate to plugin via import
3. `settings.json` registration continues pointing to `P:/.claude/hooks/` paths
4. Each wrapper is a thin import-and-delegate:

```python
# P:/.claude/hooks/SessionStart_verification_cleanup.py (compat wrapper)
import sys, importlib
sys.path.insert(0, 'P:/packages/cc-aca-session')
mod = importlib.import_module('hooks.sessionstart.aca_session_verification_cleanup')
sys.exit(mod.main())
```

### Risks
1. **Stop.py inline gates**: Some Stop.py gates reference session state. The pilot does NOT move these — only standalone session hooks.
2. **snapshot plugin**: Already registered as a plugin. cc-aca-session should absorb snapshot's session hooks, but snapshot may need to remain for backward compat during migration.
3. **Breadcrumb state**: Shared with cc-aca-observability. Session init/cleanup is safe (creates/destroys), observability reads.

### What stays unchanged
- Stop.py router (no session gates extracted in pilot)
- PreToolUse.py dispatcher
- PostToolUse.py dispatcher
- All other domain hooks
- `__lib/` shared modules

---

## 6. FILES CHANGED

No files changed yet — Phase 5 implementation awaits approval.

### Planned for pilot (cc-aca-session):
- **Create**: `P:/packages/cc-aca-session/` (full plugin structure)
- **Create**: `P:/packages/cc-aca-session/.claude-plugin/plugin.json`
- **Create**: `P:/packages/cc-aca-session/hooks/hooks.json`
- **Create**: `P:/packages/cc-aca-session/hooks/sessionstart/*.py` (3 files, moved from global)
- **Create**: `P:/packages/cc-aca-session/hooks/sessionend/*.py` (3 files, moved from global)
- **Create**: `P:/packages/cc-aca-session/hooks/precompact/*.py` (1 file, moved from global)
- **Create**: `P:/packages/cc-aca-session/lib/state_paths.py`
- **Create**: `P:/packages/cc-aca-session/tests/test_session_hooks.py`
- **Modify**: `P:/packages/cc-aca-session/CLAUDE.md`
- **Keep**: Global hook wrappers (compat shims, thin delegation)
- **Keep**: `P:/.claude/settings.json` (no changes to registration)

---

## 7. TESTS

### Tests planned for pilot
1. **Hook execution**: Each session hook still fires when invoked via compat wrapper
2. **State paths**: Per-terminal isolation preserved (terminal ID in state dir name)
3. **Import resolution**: Plugin modules import correctly on Windows (no POSIX assumptions)
4. **Session lifecycle**: SessionStart → SessionEnd cleanup cycle works
5. **Compatibility**: settings.json registration still points to working code

### Test commands
```bash
cd P:/packages/cc-aca-session && python -m pytest tests/ -v
```

### Not yet run — implementation pending approval.

---

## 8. ASSUMPTIONS AND LIMITS

1. **plugin hooks.json reliability**: Assumed unreliable. Compatibility layer delegates from global hooks to plugin source. Registration stays in settings.json.
2. **Stop.py monolith**: Cannot be split in pilot. It references 44 gates across all domains. Requires all ACA plugins to exist first, then routers become thin dispatchers.
3. **__lib/ shared modules**: Not moved in pilot. Moving shared modules requires all dependent plugins to exist first.
4. **Naming convention**: `aca_session_*` prefix for hook files inside plugin, matching the `cc-aca-session` domain name.
5. **snapshot plugin**: May need coordination. Its session hooks (PreCompact, SessionStart, SessionEnd, UserPromptSubmit) should migrate into cc-aca-session, but snapshot may need to remain for non-session features.
6. **Windows paths**: All hooks use `P:/` paths with forward slashes. Plugin must use `$CLAUDE_PLUGIN_ROOT` for portability.
7. **Cross-domain hooks**: cjk_drift_detector fires on Stop, SubagentStop, and PostToolUse. Classified as observability but may need special handling in Stop.py extraction.
8. **Gate classification confidence**: All classifications are "high" confidence for the 70+ hooks with clear naming and docstrings. "Medium" for 14 hooks where the name is suggestive but the docstring was ambiguous.
9. **fact-guard → epistemic**: fact-guard currently classifies as its own plugin. Under ACA, its provenance/claim verification responsibility maps to cc-aca-epistemic. The fact-guard package could be absorbed or remain as a dependency of cc-aca-epistemic.
10. **skill-guard → authority**: Same pattern — skill-guard's dispatch/enforcement maps to cc-aca-authority.
