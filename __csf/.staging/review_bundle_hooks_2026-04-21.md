# Review Bundle: Claude Code Hooks System

**Generated:** 2026-04-21 11:00 UTC
**Scope:** `P:/.claude/hooks/`
**File Count:** 2598 files (excluding caches, state, logs)
**Execution Mode:** 4-agents (50+ files threshold)

---

## 1. PROJECT CONTEXT

### Bundle Metadata

| Field | Value |
|-------|-------|
| **Generated** | 2026-04-21 11:00 UTC |
| **Scope** | `P:/.claude/hooks/` |
| **File Count** | 2598 (Python, Markdown, YAML, JSON) |
| **Execution Mode** | 4-agents (large scope optimization) |
| **Symlinks** | 10 active symlinks to external packages |

### Domain & Purpose

The **Cognitive Steering Framework (CSF) Hooks System** is a constitutional enforcement infrastructure for Claude Code. It provides deterministic control over AI behavior through event-driven hooks that block, warn, or track actions based on rules defined in CLAUDE.md. Critical for enforcing truthfulness, evidence verification, anti-sycophancy, and solo-developer workflow discipline.

### Scale Metrics

| Metric | Value |
|--------|-------|
| **Total Files** | ~2598 (excluding caches/state) |
| **Python Hook Files** | ~413 at root + subdirectories |
| **Major Subsystems** | 6 (PreToolUse, PostToolUse, Stop, SessionStart, UserPromptSubmit, anti_sycophancy) |
| **Lines of Core Logic** | ~58K in PreToolUse.py alone |
| **External Package Links** | 3 packages (skill-guard, handoff, cc-skills-sdlc) |
| **Change Frequency** | High (active development, recent changes from Apr 2026) |

### Your Environment

- **OS:** Windows 11 Pro (WSL/bash compatible)
- **Primary Language:** Python 3.11+
- **Framework:** Claude Code Hooks (CSF NIP)
- **Package Managers:** pip, uv
- **Key Paths:**
  - Hooks root: `P:/.claude/hooks/`
  - External packages: `/p/packages/skill-guard/`, `/p/packages/handoff/`, `/p/packages/cc-skills-sdlc/`

---

## 2. ARCHITECTURE OVERVIEW

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                     CLAUDE CODE HOOK DISPATCH FLOW                           │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  SessionStart ──► UserPromptSubmit ──► PreToolUse ──► [TOOL] ──► PostToolUse │
│       │                  │                  │                 │                │
│       ▼                  ▼                  ▼                 ▼                │
│  SessionStart_router  UserPromptSubmit    PreToolUse.py    PostToolUse_router│
│       │             _router.py             (58K main)              │          │
│       │                  │                     │                   ▼          │
│       │                  │                     │           ┌────────────────┐ │
│       │                  │                     │           │ posttooluse/   │ │
│       │                  │                     │           │ - FixValidator │ │
│       │                  │                     │           │ - ChangeVerify │ │
│       │                  │                     │           │ - FalsifyAssess│ │
│       │                  │                     │           │ - SemanticCompress │
│       │                  │                     │           └────────────────┘ │
│       │                  │                     │                               │
│       │                  ▼                     ▼                               │
│       │           ┌──────────────────┐  TOOL_HOOKS (tool-specific)          │
│       │           │ UserPromptSubmit/ │  - Read_path_gate.py                 │
│       │           │ PreToolUse/       │  - Write_*.py                        │
│       │           │ Stop_*/           │  - Edit_*.py                         │
│       │           │ anti_sycophancy/  │  - Bash_*.py                         │
│       │           └──────────────────┘  - Glob_*.py                         │
│       │                                                                  │
│       ▼                                                                  │
│  ┌───────────────────────────────────────────────────────────────────┐     │
│  │                         STOP ROUTER                                 │     │
│  │              (Single authoritative entrypoint)                     │     │
│  │                                                                     │     │
│  │  Enforces:                                                          │     │
│  │  - assumption_audit_v2.py (retrospective claims)                   │     │
│  │  - constitutional_enforcer.py (anti-sycophancy, effectiveness)      │     │
│  │  - investigation-ledger/ (confidence validation)                   │     │
│  │  - skill_execution_gate.py (skill protocol enforcement)            │     │
│  └───────────────────────────────────────────────────────────────────┘     │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Symlink Destinations (External Packages)

| Symlink | Target Package | Purpose |
|---------|----------------|---------|
| `skill_execution_state.py` | `skill-guard/src/skill_guard/` | Skill execution state tracking |
| `StopHook_skill_execution_gate.py` | `skill-guard/src/skill_guard/` | Skill protocol enforcement |
| `StopHook_rca_contract.py` | `cc-skills-sdlc/skills/rca/hooks/` | RCA contract hooks |
| `StopHook_rca_reflector.py` | `cc-skills-sdlc/skills/rca/hooks/` | RCA reflection |
| `PreCompact_handoff_capture.py` | `handoff/scripts/hooks/` | Handoff capture |
| `SessionStart_handoff_restore.py` | `handoff/scripts/hooks/` | Session restore from handoff |
| `PostToolUse_breadcrumb_tracker.py` | `skill-guard/src/skill_guard/` | Breadcrumb tracking |
| `PreToolUse/PreToolUse_skill_pattern_gate.py` | `skill-guard/src/skill_guard/` | Skill pattern enforcement |
| `SessionStart_handoff_restore.py` | `handoff/scripts/hooks/` | Handoff restore |
| `UserPromptSubmit_modules/handoff_task_injector.py` | `handoff/scripts/hooks/` | Handoff task injection |
| `UserPromptSubmit_modules/slash_command_observability.py` | `skill-guard/src/skill_guard/` | Slash command tracking |

### Major Subsystems

| Subsystem | Path | Purpose |
|-----------|------|---------|
| **PreToolUse** | `./PreToolUse.py` + `PreToolUse/*.py` | Pre-tool execution validation (paths, auth, risk) |
| **PostToolUse** | `./PostToolUse_router.py` + `posttooluse/` | Post-tool validation, fix verification, semantic compression |
| **Stop Hooks** | `./Stop_router.py` + `Stop_*.py` | Response validation, constitutional enforcement |
| **UserPromptSubmit** | `./UserPromptSubmit_router.py` + `UserPromptSubmit/*.py` | Prompt injection, cognitive frameworks, truthfulness gates |
| **SessionStart** | `./SessionStart_router.py` | Session restore, CKS context loading |
| **Anti-Sycophancy** | `./anti_sycophancy/` | Belief/claim detection, advocacy injection |
| **Shared Infrastructure** | `./__lib/` | Hook base class, ledger, terminal detection, TTL utilities |

---

## 3. EXECUTION AND DATA FLOW

### Hook Event Sequence

```
User Prompt → SessionStart → UserPromptSubmit → PreToolUse → [TOOL]
                                                              │
                                                              ▼
                                                         PostToolUse
                                                              │
                                                              ▼
                                                         Stop (response validation)
```

### PreToolUse Dispatch Chain (Critical)

Per `PreToolUse.py` lines 11-28:

```
1. _pin_terminal_env()
2. _check_skill_first_gate() ← THE skill-first gate. Nowhere else.
3. UNIVERSAL hooks:
   - PreToolUse_path_validator.py
   - PreToolUse/PreToolUse_skill_pattern_gate.py
   - PreToolUse_risk_tier_gate.py
   - PreToolUse_observe_before_act_gate.py
4. TOOL_HOOKS for specific tool_name
```

**Files NOT in dispatch chain (do not edit expecting results):**
- `PreToolUse_skill_first_gate.py` (standalone, not called)
- `PreToolUse_workflow_steps_gate.py` (deleted, was never in chain)

### State Management

| State Type | Storage | Isolation |
|------------|---------|-----------|
| Session ID | Environment + ledger | Per terminal |
| Terminal ID | `terminal_detection.py` | Per terminal |
| Tool Sequence | `tool_sequence_manager.py` | Per session/terminal |
| Evidence Store | `evidence/` directory | Per turn |
| Hook Ledger | `__lib/hook_ledger.py` | Per session |

### Error Handling Policy

- **CRITICAL_HOOKS**: Never fail open (`PreToolUse_path_validator.py`, `PreToolUse_authorization_gate.py`, `PreToolUse_deny_root_write.py`, `PreToolUse_risk_tier_gate.py`)
- **Bypass mechanism**: `CONSTITUTIONAL_HOOKS_BYPASS=1` env var
- **Logging**: JSONL to `logs/enforcement.jsonl`, `logs/diagnostics/hook_invocations.jsonl`

---

## 4. COMPONENT INVENTORY

### Core Logic Files

| File | Purpose | Key Functions |
|------|---------|---------------|
| `PreToolUse.py` | Main router for pre-tool validation | `_pin_terminal_env()`, `_check_skill_first_gate()`, `run_hook()` |
| `PostToolUse_router.py` | Consolidated post-tool validation | `FixValidator`, `ChangeVerification`, `FalsificationAssessor`, `SemanticCompress` |
| `Stop_router.py` | Single authoritative Stop hook entry | Terminal + turn scoped ledger snapshots, in-process validators |
| `SessionStart_router.py` | Session initialization | `capture_settings`, `cks_restore`, `session_restore` |
| `UserPromptSubmit_router.py` | Prompt injection router | 25+ hooks consolidated (context_summary, handoff_task_injector, truthfulness_gate, etc.) |

### Shared Infrastructure (`__lib/`)

| File | Purpose |
|------|---------|
| `hook_base.py` | Auto-logging decorator, in-process hook protocol |
| `hook_ledger.py` | Append events, build response snapshots, terminal detection |
| `terminal_detection.py` | Detect terminal ID from environment |
| `runtime_env.py` | Ledger availability check, environment detection |
| `ttl_utils.py` | TTL expiration checking |
| `circuit_breaker.py` | Failure recovery |

### Constitutional Enforcement Hooks

| Hook | Event | Mode | Source | Status |
|------|-------|------|--------|--------|
| `constitutional_enforcer.py` | Stop | BLOCK | CLAUDE.md Part A | ✅ Active |
| `empirical_claims_gate.py` | Stop | BLOCK | verification_tiers.md | ⚠️ Archived |
| `assumption_audit_v2.py` | Stop | BLOCK | verification_tiers.md | ✅ Active |
| `Stop_hook_skill_execution_gate.py` | Stop | BLOCK | Skill protocol | ✅ Active (symlink) |
| `recursive_failure_detector.py` | PreToolUse | BLOCK | CLAUDE.md D.5 | ✅ Active |
| `anti_sycophancy/*` | Various | BLOCK/SOFT | CLAUDE.md | ✅ Active |

### Analysis and Diagnostic Tools

| Directory | Contents |
|-----------|----------|
| `analysis/` | Compatibility matrices, pattern analysis, audit reports |
| `baselines/` | Baseline measurement scripts |
| `docs/` | Implementation specs, troubleshooting guides |
| `damage-control/` | Damage control patterns and solutions |

---

## 5. DESIGN INTENT AND NON-NEGOTIABLES

### Architectural Pillars

1. **Deterministic Control**: Hooks provide structural enforcement, not suggestions
2. **Fail-Fast**: Critical hooks never fail open; errors surface immediately
3. **Terminal Isolation**: Each terminal has isolated state to prevent cross-contamination
4. **Evidence-First**: Claims require verification; speculation must be marked
5. **Constitutional Rules**: CLAUDE.md rules enforced structurally via hooks

### Technology Constraints

- **Python 3.11+**: Type hints, async patterns
- **In-Process Execution**: Routers use in-process calls (not subprocess) for performance
- **JSONL Logging**: Standardized enforcement decision logging
- **Symlink Integration**: Hooks reference external packages via symlinks

### Things That Must NOT Change

1. **Dispatch Chain Documentation**: The DISPATCH CHAIN comment block in `PreToolUse.py` must remain accurate
2. **Critical Hooks Never Fail Open**: Path validator, auth gate, risk tier gate must always enforce
3. **Skill-First Gate Location**: `_check_skill_first_gate()` in `PreToolUse.py` is the ONLY skill-first gate
4. **Terminal ID Propagation**: All ledger events must include terminal_id for isolation
5. **Hook Edit Verification**: Pre-edit checklist must be followed (verify file is in dispatch chain)

---

## 6. KNOWN ISSUES

### Issue 1: Ghost File References (Resolved 2026-03-17)

- **Scenario**: LLMs editing dead files not in dispatch chain
- **Impact**: Persistent deadlocks, fixes that never run
- **Resolution**: Added DISPATCH CHAIN comment block to `PreToolUse.py`
- **Current State**: ✅ Resolved

### Issue 2: Dead Code in PreToolUse_skill_pattern_gate.py (Resolved)

- **Scenario**: Dead `_read_pending_intent()` logic (intent file deleted before hook runs)
- **Impact**: Unreachable branches, confusing code
- **Resolution**: Removed dead code block and helper functions

### Issue 3: Stop Hook False Positives on System Failure (Resolved)

- **Scenario**: Stop hook fired "SLASH COMMAND IGNORED" when hook system blocked all tools
- **Impact**: Shaming LLM for system failure
- **Resolution**: Added `tool_blocked` detection logic in `StopHook_skill_execution_gate.py`

### Issue 4: Skill Substitution Compliance Failures

- **Scenario**: LLMs load skill but provide own analysis instead of executing skill command
- **Impact**: Skill protocol violations
- **Enforcement**: `StopHook_skill_execution_gate.py` tracks skill execution state

---

## 7. INTEGRATION POINTS

### External Package Integration

| Package | Integration Method | Hooks Using It |
|---------|-------------------|----------------|
| `skill-guard` | Symlinks in root + PreToolUse/ | Skill execution tracking, breadcrumb tracking |
| `handoff` | Symlinks in root + UserPromptSubmit_modules/ | Handoff capture/restore |
| `cc-skills-sdlc` | Symlinks in root | RCA contract and reflection |

### Configuration Files

| File | Purpose |
|------|---------|
| `settings.json` (user .claude/) | Hook registration |
| `.pre-commit-config.yaml` | Pre-commit hooks |
| `config/daemon_config.py` | Daemon configuration |
| `config/directory_policy.json` | Directory access policy |

### Environment Variables

| Variable | Default | Purpose |
|----------|---------|---------|
| `CONSTITUTIONAL_HOOKS_BYPASS` | false | Disable all constitutional hooks |
| `HOOK_PROTECTION_ENABLED` | false | Enable hook protection validation |
| `HOOK_PROTECTION_BLOCKING` | false | Block mode in PreToolUse |
| `INVESTIGATION_LEDGER_ENABLED` | false | Enable investigation tracking |
| `CONFIDENCE_VALIDATOR_ENABLED` | false | Enable confidence ceiling validation |

---

## 8. INPUT/OUTPUT CONTRACT

### Per-Phase Data Flow

#### SessionStart Phase
- **Reads**: Environment variables, previous session state
- **Writes**: Session context to `state/` directory
- **Key Constraint**: Must run before any tool use

#### UserPromptSubmit Phase
- **Reads**: User prompt, session state, CKS context
- **Writes**: Injection text to prompt modification
- **Key Constraint**: Runs before PreToolUse

#### PreToolUse Phase
- **Reads**: Tool name, arguments, dispatch chain config
- **Writes**: Block/warn modification, ledger events
- **Key Constraint**: Must approve before tool execution

#### PostToolUse Phase
- **Reads**: Tool result, tool sequence, evidence store
- **Writes**: Fix validation, change tracking
- **Key Constraint**: Runs after tool completes

#### Stop Phase
- **Reads**: Full response, turn context, evidence
- **Writes**: Block/warn on response, ledger snapshot
- **Key Constraint**: Final gate before response is sent

### Agent Read Sources

For this bundle (single-operator generation):
- `analysis` = This bundle generator's output (not source code)
- `source` = Actual hook files and documentation
- `work` = User provided path `P:/.claude/hooks/`

### Quality Gates

This bundle does not dispatch parallel agents, so no quality gates apply.

---

## 9. AGENT DISPATCH DEFINITIONS

This bundle was generated by a single operator (no parallel agent dispatch) due to:
- Direct file system access for efficient scanning
- Context already loaded from key architecture files
- User requested following symlinks which requires direct path resolution

---

## 10. FAILURE SCENARIOS

### Failure Chain 1: Editing Non-Dispatched Files

**Trigger**: LLM edits `PreToolUse_skill_first_gate.py` expecting it to run
**Propagation**: Edit completes → no enforcement → constitutional violation slips through
**Detection**: User notices hook not firing
**Actual vs Expected**: Expected hook to run; file not in dispatch chain
**Root Cause**: Violation of pre-edit verification checklist

### Failure Chain 2: Symlink Target Missing

**Trigger**: External package moved or deleted
**Propagation**: Symlink becomes broken → import fails → hook fails silently
**Detection**: Hook stops firing, no error logged (depends on error handling)
**Actual vs Expected**: Hook should run; symlink broken
**Root Cause**: External package dependency not verified on package updates

### Failure Chain 3: Terminal ID Collision

**Trigger**: Two terminals with same ID write to shared state
**Propagation**: Cross-terminal state contamination → wrong evidence for claims
**Detection**: Claims blocked unexpectedly in one terminal due to another terminal's state
**Actual vs Expected**: Claims should be scoped to terminal; collision causes contamination
**Root Cause**: `detect_terminal_id()` collision or env var not set

---

## 11. APPENDIX: KEY FILE LOCATIONS

### Router Files (Primary Entry Points)

| File | Full Path |
|------|-----------|
| PreToolUse Router | `P:/.claude/hooks/PreToolUse.py` |
| PostToolUse Router | `P:/.claude/hooks/PostToolUse_router.py` |
| Stop Router | `P:/.claude/hooks/Stop_router.py` |
| SessionStart Router | `P:/.claude/hooks/SessionStart_router.py` |
| UserPromptSubmit Router | `P:/.claude/hooks/UserPromptSubmit_router.py` |

### Shared Infrastructure

| File | Full Path |
|------|-----------|
| Hook Base | `P:/.claude/hooks/__lib/hook_base.py` |
| Hook Ledger | `P:/.claude/hooks/__lib/hook_ledger.py` |
| Terminal Detection | `P:/.claude/hooks/__lib/terminal_detection.py` |
| Runtime Env | `P:/.claude/hooks/__lib/runtime_env.py` |

### Constitutional Enforcement

| File | Full Path |
|------|-----------|
| Constitutional Enforcer | `P:/.claude/hooks/constitutional_enforcer.py` |
| Assumption Audit v2 | `P:/.claude/hooks/assumption_audit_v2.py` |
| Anti-Sycophancy Module | `P:/.claude/hooks/anti_sycophancy/` |
| Skill Execution Gate | `P:/.claude/hooks/StopHook_skill_execution_gate.py` (symlink) |

### Architecture Documentation

| File | Full Path |
|------|-----------|
| Architecture Doc | `P:/.claude/hooks/ARCHITECTURE.md` |
| Hooks Catalog | `P:/.claude/hooks/HOOKS_CATALOG.md` |
| CLAUDE.md | `P:/.claude/hooks/CLAUDE.md` |
| Change Log | `P:/.claude/hooks/CHANGELOG.md` |

---

*Bundle generated by /review_bundle skill*
*File count: 2598 | Symlinks followed: 10 | Execution mode: single-operator*