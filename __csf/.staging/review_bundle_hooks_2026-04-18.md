# Review Bundle: Claude Code Hooks Infrastructure

**Generated:** 2026-04-18
**Scope:** `P:/.claude/hooks/`
**File Count:** 1444 source files (excluding cache)
**Execution Mode:** 4-agents (parallel)

---

## 1. PROJECT CONTEXT

### Bundle Metadata

| Field | Value |
|-------|-------|
| Generated | 2026-04-18 |
| Scope | `P:/.claude/hooks/` |
| File Count | 1444 source files |
| Execution Mode | 4-agents (parallel) |
| Architecture Version | 2.6 (2026-03-16) |

### Domain & Purpose

Claude Code hooks infrastructure implementing the **Cognitive Steering Framework (CSF)** — structural enforcement hooks that provide deterministic control over Claude Code behavior. This is a solo-developer constitutional enforcement system ensuring truthfulness, evidence-first verification, and investigation-before-diagnosis patterns.

### Scale Metrics

| Metric | Value |
|--------|-------|
| Source files | 1444 |
| Major subsystems | 12+ |
| Hook event types | 5 (SessionStart, UserPromptSubmit, PreToolUse, PostToolUse, Stop) |
| Active constitutional hooks | ~25 |
| Archived hooks | ~15 |
| Lines of documentation | 10K+ |

### Environment

- **OS:** Windows 11 Pro (bash/git bash environment)
- **Primary language:** Python 3.11+
- **Package managers:** pip, pytest
- **Build tools:** ruff (linting), mypy (type checking)
- **Key dependencies:** hook_tracker, cc_diagnostic_logger, evidence_store, shared_utils

---

## 2. ARCHITECTURE OVERVIEW

```
┌─────────────────────────────────────────────────────────────────┐
│                    Claude Code Hook Events                       │
├─────────────────────────────────────────────────────────────────┤
│  SessionStart → UserPromptSubmit → PreToolUse → PostToolUse → Stop │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                     PreToolUse Router (v2.2)                    │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │ DISPATCH CHAIN:                                             │ │
│  │ 1. _pin_terminal_env()                                     │ │
│  │ 2. _check_skill_first_gate() ← THE skill-first gate        │ │
│  │ 3. UNIVERSAL hooks (via run_hook subprocess):               │ │
│  │    - PreToolUse_path_validator.py                           │ │
│  │    - PreToolUse/PreToolUse_skill_pattern_gate.py            │ │
│  │    - PreToolUse_risk_tier_gate.py                           │ │
│  │    - PreToolUse_observe_before_act_gate.py                  │ │
│  │ 4. TOOL_HOOKS for specific tool_name                        │ │
│  └─────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Constitutional Hooks                          │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────┐  │
│  │ Anti-Sycophancy  │  │ Evidence Tiers   │  │ Catch-22     │  │
│  │ constitutional_  │  │ assumption_      │  │ recursive_   │  │
│  │ enforcer.py      │  │ audit_v2.py     │  │ failure_     │  │
│  │                  │  │                  │  │ detector.py  │  │
│  └──────────────────┘  └──────────────────┘  └──────────────┘  │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────┐  │
│  │ Behavioral       │  │ Investigation    │  │ Skill       │  │
│  │ Quality          │  │ Ledger           │  │ Execution   │  │
│  │ Stop_reasoning_  │  │ investigation-   │  │ StopHook_   │  │
│  │ quality_gate.py  │  │ ledger/         │  │ skill_exec_ │  │
│  └──────────────────┘  └──────────────────┘  └──────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                     Shared Infrastructure                       │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────┐  │
│  │ __lib/          │  │ shared_utils     │  │ evidence_    │  │
│  │ hook_tracker.py │  │                  │  │ store.py     │  │
│  │ - is_hook_self  │  │ - load_state     │  │              │  │
│  │ - is_bypass     │  │ - save_state     │  │              │  │
│  │ - log_block     │  │ - log_hook_event │  │              │  │
│  └──────────────────┘  └──────────────────┘  └──────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

### Major Subsystems

| Subsystem | Path | Purpose |
|-----------|------|---------|
| PreToolUse hooks | `PreToolUse/` | Tool execution gating, path validation, skill routing |
| Stop hooks | `stop/` | Response validation, success claims, behavioral quality |
| PostToolUse hooks | `posttooluse/` | Output analysis, failure recording, artifact validation |
| SessionStart hooks | `SessionStart/` | Context initialization, health checks, daemon startup |
| UserPromptSubmit | `UserPromptSubmit_modules/` | Context injection, constraint display |
| Anti-Sycophancy | `anti_sycophancy/` | Hedged language detection, overconfidence detection |
| Investigation Ledger | `investigation-ledger/` | Track investigation completeness |
| Competence | `competence/` | Task type registry for behavioral tracking |
| Evidence | `evidence/` | Evidence spool and storage for enforcement |
| State | `state/` | Session/terminal state management |
| Shared Utils | `__lib/` | Common utilities (hook_tracker, ttl_utils, hook_ledger) |
| Config | `config/` | Daemon config, directory policies |

---

## 3. EXECUTION AND DATA FLOW

### Hook Event Flow

```
User Prompt
    │
    ▼
SessionStart (initialize context, health checks)
    │
    ▼
UserPromptSubmit (inject context, validate input)
    │
    ▼
PreToolUse (BLOCK phase - gate tool execution)
    │
    ▼
Tool Execution (if allowed)
    │
    ▼
PostToolUse (analyze output, detect failures)
    │
    ▼
Stop (validate response, enforce constitutional rules)
    │
    ▼
Next Turn / Response
```

### Constitutional Enforcement Modes

| Mode | Behavior |
|------|----------|
| BLOCK | Prevents action |
| WARN | Logs but allows |
| SELECTIVE | BLOCK severe, WARN moderate |
| SOFT | Injects LLM self-prompt for reflection |
| TRACK | Silent state tracking |

### Bypass Mechanism

```bash
export CONSTITUTIONAL_HOOKS_BYPASS=1  # Disable all constitutional hooks
```

### State Management

- **Session isolation:** `CLAUDE_SESSION_ID` pins context per session
- **Terminal isolation:** `CLAUDE_TERMINAL_ID` preserves terminal context
- **State stores:** JSON files in `state/` directory
- **Evidence spool:** `session_data/evidence_spool/` for enforcement data

### Error Handling

- **Fail-open prevention:** Critical hooks never fail open
- **Hook self-operation:** Exempts commands modifying hooks themselves
- **Test pattern detection:** Excludes test commands from enforcement logging
- **Structured logging:** JSONL logs in `logs/` directory

---

## 4. COMPONENT INVENTORY

### Core Logic Files

| File | Path | Responsibility |
|------|------|----------------|
| PreToolUse.py | `P:/.claude/hooks/` | Main PreToolUse router v2.2 with dispatch chain |
| PostToolUse.py | (in `posttooluse/`) | PostToolUse router |
| Stop.py | (in `stop/`) | Stop event router |
| hook_tracker.py | `__lib/` | Shared infrastructure for constitutional hooks |
| cc_diagnostic_logger.py | `__lib/` | Structured JSONL logging infrastructure |
| evidence_store.py | (in `evidence/`) | Evidence ledger for claim verification |

### PreToolUse Universal Hooks

| File | Purpose |
|------|---------|
| PreToolUse_path_validator.py | Path validation and protection |
| PreToolUse/PreToolUse_skill_pattern_gate.py | Skill-first routing enforcement |
| PreToolUse_risk_tier_gate.py | Risk assessment and gating |
| PreToolUse_observe_before_act_gate.py | Investigation-before-action enforcement |

### Constitutional Enforcement Hooks

| File | Event | Mode | Enforces |
|------|-------|------|----------|
| constitutional_enforcer.py | Stop | BLOCK | Anti-Sycophancy, Efficiency |
| assumption_audit_v2.py | Stop | BLOCK | Evidence tiers, retrospective claims |
| recursive_failure_detector.py | PreToolUse | BLOCK | Catch-22 detection |
| Stop_reasoning_quality_gate.py | Stop | SOFT | Behavioral quality |
| StopHook_skill_execution_gate.py | Stop | BLOCK | Skill invocation protocol |
| investigation-ledger/Stop_investigation_validator.py | Stop | BLOCK | Investigation completeness |

### Anti-Sycophancy Components

| File | Purpose |
|------|---------|
| anti_sycophancy/affirmation_detector.py | Detect sycophancy patterns |
| anti_sycophancy/overconfidence_detector.py | Flag overconfident claims |
| anti_sycophancy/hypothesis_as_fact_detector.py | Speculative claims as facts |
| anti_sycophancy/lazy_closure_detector.py | Lazy conclusion patterns |
| anti_sycophancy/unverified_stance_detector.py | Unverified stance claims |

### Utilities

| File | Path | Purpose |
|------|------|---------|
| shared_utils.py | root | State management, session utilities |
| hook_tracker.py | `__lib/` | Constitutional hook tracking |
| ttl_utils.py | `__lib/` | TTL expiration utilities |
| hook_ledger.py | `__lib/` | Event appending for audit |

### Configuration

| File | Purpose |
|------|---------|
| config/daemon_config.py | Daemon configuration |
| config/directory_policy.json | Directory access policies |
| settings.json | Hook registration and feature flags |

### Analysis & Diagnostics

| File | Purpose |
|------|---------|
| analyze_hooks.py | Hook behavior analysis |
| comprehensive_hook_health_check.py | Health monitoring |
| hook_diagnostics.py | Universal diagnostics |
| cc_diagnostic_logger.py | Enforcement decision logging |

### Archived/Retired Hooks

| File | Status | Notes |
|------|--------|-------|
| shell_complexity_gate.py | ⚠️ Archived | Log-only, preserved |
| unparseable_command_gate.py | ⚠️ Archived | Security patterns preserved |
| Stop_pre_clarification_gate.py | ⚠️ Archived | Replaced by investigation-ledger |
| empirical_claims_gate.py | ⚠️ Archived | TAV patterns preserved in `_archive/` |

---

## 5. DESIGN INTENT AND NON-NEGOTIABLES

### Architectural Pillars

1. **Constitutional Enforcement is Non-Negotiable** — Hooks enforce rules structurally, not via trust
2. **Fail Fast, Surface Immediately** — Hook failures surface problems at point of violation
3. **Evidence-First Verification** — Claims must cite evidence tier
4. **Solo-Developer Appropriate** — Pragmatic solutions over enterprise patterns

### Technology Constraints

- **Python 3.11+** with type hints
- **Hook events:** SessionStart, UserPromptSubmit, PreToolUse, PostToolUse, Stop
- **No external services** — self-contained, local execution
- **Bypass mechanism** via `CONSTITUTIONAL_HOOKS_BYPASS=1` env var

### Things That Must NOT Change

1. **Dispatch chain integrity** — PreToolUse.py DISPATCH CHAIN comment must remain accurate
2. **Critical hooks never fail open** — CRITICAL_HOOKS set in PreToolUse.py
3. **Self-exemption for hook maintenance** — Prevents Catch-22 when fixing hooks
4. **Evidence tier ceilings** — Tier 4 claims must be flagged [UNVERIFIED]

---

## 6. KNOWN ISSUES

### Historical Issues (Resolved)

| Issue | Impact | Status | Fix |
|-------|--------|--------|-----|
| LLMs repeatedly edit dead files not in dispatch chain | HIGH | ✅ Resolved | Added DISPATCH CHAIN documentation to PreToolUse.py |
| Dead code in PreToolUse_skill_pattern_gate.py | MEDIUM | ✅ Resolved | Removed unreachable `_read_pending_intent()` logic |
| Stop hook incorrectly fired for system failures | MEDIUM | ✅ Resolved | Added tool_blocked detection logic |
| Linter hook corrupted intermediate file states | HIGH | ✅ Resolved | Removed lint_hook.py and PreToolUse_auto_format.py |

### Current Observations

| Observation | Impact | Workaround |
|-------------|--------|------------|
| 1444 files creates high discovery overhead | LOW | Use DISPATCH CHAIN verification before editing |
| Multiple archive directories (.archive, _archive, _archived) | LOW | Dead code preserved for reference |
| Evidence tier enforcement via assumption_audit_v2.py | MEDIUM | Requires proper evidence citation discipline |

---

## 7. INTEGRATION POINTS

### Hook Registration

Hooks are registered in `settings.json`:
```json
{
  "hooks": {
    "PreToolUse": [...],
    "PostToolUse": [...],
    "Stop": [...]
  }
}
```

### Dispatch Chain Verification

Before editing any hook file:
```bash
grep -n "UNIVERSAL\|TOOL_HOOKS" P:/.claude/hooks/PreToolUse.py | grep -i "target_file"
```

### Invocation Model

1. HookImporter loads entry point (e.g., `PreToolUse.py`)
2. `main()` runs dispatch chain in order
3. Universal hooks run via `run_hook` subprocess
4. Tool-specific hooks run for matching `tool_name`

### Data Exchange Contracts

| Data | Source | Consumer |
|------|--------|----------|
| Session ID | `CLAUDE_SESSION_ID` env | All hooks |
| Terminal ID | `CLAUDE_TERMINAL_ID` env | All hooks |
| Tool sequence | `tool_sequence_manager.py` | Stop hooks |
| Evidence items | `evidence_store.py` | Enforcement hooks |

---

## 8. INPUT/OUTPUT CONTRACT

### Per-Phase Data Flow

| Phase | Reads | Writes | Key Constraint |
|-------|-------|--------|----------------|
| SessionStart | settings.json, env vars | state files | Initialize only |
| UserPromptSubmit | prior context, settings | breadcrumb init | Non-blocking |
| PreToolUse | tool_name, command, env | None | BLOCK allowed |
| PostToolUse | tool output, exit code | failure records | Analysis only |
| Stop | response, tool history | enforcement logs | Validation only |

### Agent Read Sources (CRITICAL)

For skills dispatching parallel agents:

| Source Type | Description |
|-------------|-------------|
| `analysis` | Operator/intermediary output (NOT source code) |
| `source` | Actual source code under review |
| `work` | User-provided work input |

**Distinction matters:** Agents reading `analysis` build on operator errors. Agents reading `source` catch issues directly.

---

## 9. AGENT DISPATCH DEFINITIONS

### Execution Mode: 4-Agents (Parallel)

| Agent | Scope | Files Expected |
|-------|-------|----------------|
| Explorer | File discovery, import tracing | 400-500 files |
| Core Reader | Main router files, core logic | 50-100 files |
| Config Reader | Settings, policies, configs | 50-100 files |
| Dependency Scanner | Env vars, imports, deps | 300-400 files |

### Parallel Dispatch Specification

**Explorer Agent:**
- **Type:** explore
- **Scope:** Discover all files, trace import relationships
- **Output:** File inventory, dependency graph

**Core Reader Agent:**
- **Type:** general-purpose
- **Scope:** Read PreToolUse.py, Stop.py, PostToolUse.py routers
- **Output:** Dispatch chain verification

**Config Reader Agent:**
- **Type:** general-purpose
- **Scope:** Read settings.json, directory_policy.json, feature flags
- **Output:** Configuration state

**Dependency Scanner Agent:**
- **Type:** general-purpose
- **Scope:** Scan for env vars, imports, external dependencies
- **Output:** Dependency manifest

---

## 10. FAILURE SCENARIOS

### Failure Chain Documentation

| Scenario | Trigger | Propagation | Detection |
|----------|---------|-------------|-----------|
| Dead file editing | LLM edits file not in dispatch chain | Fix never runs | Pre-edit verification |
| Hook Catch-22 | Hook blocks modification of itself | No recovery path | is_hook_self_operation() |
| Linter corruption | ruff --fix on intermediate state | Silent code loss | Sequential-edit prevention |
| Evidence fabrication | Claim without citation | Enforcement gap | assumption_audit_v2.py |

### Common Failure Patterns

1. **Edit without verification** — File not in dispatch chain
2. **Import without execution** — Skill loaded but command not run
3. **Claim without evidence** — Retrospective assertion without this-turn verification
4. **Sequential race** — Parallel edits cause file corruption

### Verified Fixes

| Fix | File | Line | Prevents |
|-----|------|------|----------|
| DISPATCH CHAIN docs | PreToolUse.py | 11-28 | Dead file edits |
| Dead code removal | PreToolUse_skill_pattern_gate.py | N/A | Unreachable branches |
| Tool blocked detection | StopHook_skill_execution_gate.py | 854-873 | System failure shame |
| Lint hook removal | posttooluse/__init__.py | 36, 147-152 | Intermediate corruption |

---

## 11. APPENDIX: RECENT BUNDLES

| Bundle | Date | Notes |
|--------|------|-------|
| review_bundle_hooks_2026-03-18.md | 2026-03-18 | Prior comprehensive review |
| review_bundle_hooks_system_20260307.md | 2026-03-07 | System-level review |
| review_bundle_hooks_memories_debugRCA_2026-03-23.md | 2026-03-23 | Debug RCA integration |

---

## VERIFICATION CHECKLIST

- [x] Scope Selection: hooks directory confirmed
- [x] File Count: 1444 source files (>50 threshold → 4-agent mode)
- [x] Architecture: PreToolUse v2.2 dispatch chain documented
- [x] Component Inventory: All major subsystems cataloged
- [x] Design Intent: Constitutional pillars and constraints stated
- [x] Known Issues: Historical issues and resolutions documented
- [x] Integration Points: Hook registration and invocation model documented
- [x] Failure Scenarios: Common patterns and verified fixes documented

**Generated by:** `/review_bundle P:/.claude/hooks`
**Output location:** `P:/__csf/.staging/review_bundle_hooks_2026-04-18.md`
