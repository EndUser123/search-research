# Review Bundle: Hooks, Memories, debugRCA

**Generated:** 2026-03-23
**Scope:** hooks/ + memories/ + debugRCA skill
**File Count:** ~200+ functional files (hooks ~150 Python/MD, memories 76 MD, debugRCA 60 files)
**Execution Mode:** Single-agent (focused scope)

---

## 1. PROJECT CONTEXT

### Bundle Metadata

| System | Location | Files | Type |
|---------|----------|-------|------|
| Hooks | `P:/.claude/hooks/` | ~150 functional | Constitutional enforcement |
| Memories | `C:\Users\brsth\.claude\projects\P--\memory\` | 76 | Session patterns & lessons |
| debugRCA | `P:\.claude\skills\debugRCA\` | 60 | Root cause analysis skill |

### Domain & Purpose

**Hooks** implement the Cognitive Steering Framework (CSF) - structural enforcement hooks that provide deterministic control over Claude Code behavior. They enforce constitutional rules (evidence tiers, anti-sycophancy, skill-first execution, truthfulness) at the PreToolUse, PostToolUse, UserPromptSubmit, SessionStart, and Stop event points.

**Memories** contain session-learned patterns, corrections, and best practices extracted from development history. They provide persistent context across sessions about what works, what fails, and why.

**debugRCA** is a systematic debugging and root cause analysis skill combining a Python library (`debugRCA`) with Claude Code hook integration for evidence saturation detection, phase state persistence, and hypothesis scoring.

### Scale Metrics

| Metric | Hooks | Memories | debugRCA |
|--------|-------|----------|----------|
| Python files | ~120 | 0 | 11 hooks + 30 tests |
| Markdown docs | ~30 | 76 | 8 docs |
| Lines of code | ~15,000 | N/A | ~5,000 |
| Test coverage | Partial | N/A | 83% (175 tests) |

### Environment

- **OS:** Windows 11 Pro 10.0.26200
- **Shell:** Bash (Unix syntax on Windows)
- **Primary language:** Python 3.14
- **Package manager:** pip, pytest
- **Build tools:** Claude Code CLI, PowerShell

---

## 2. ARCHITECTURE OVERVIEW

### Hooks Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                     CLAUDE CODE EVENT FLOW                          │
├─────────────────────────────────────────────────────────────────────┤
│  SessionStart → UserPromptSubmit → PreToolUse → Tool → PostToolUse │
│                                    ↓                    ↓           │
│                              Stop Hook ←←←←←←←←←←←←←←              │
└─────────────────────────────────────────────────────────────────────┘

Event Point Distribution:
├── SessionStart (2 hooks)
│   ├── SessionStart_cks_decision_load.py
│   └── SessionStart_router.py (consolidated)
├── UserPromptSubmit (25+ hooks, consolidated into router)
│   ├── skill_enforcer (Layer 1 enforcement)
│   ├── anti_sycophancy (ADVOCATE PROTOCOL)
│   ├── context_summary / handoff_task_injector (new 2026-03)
│   ├── truthfulness_gate / verify_before_claim (new 2026-03)
│   └── declaration_reminder (anti-lazy enforcement)
├── PreToolUse (routers + standalone)
│   ├── PreToolUse_write_router.py (v1.3, consolidated)
│   ├── PreToolUse_bash_router.py (v2.2, consolidated)
│   ├── PreToolUse_skill_pattern_gate.py (v3.2, parallel regex + daemon)
│   ├── PreToolUse_falsification_gate.py
│   ├── PreToolUse_dependency_verification_gate.py
│   ├── PreToolUse_hook_protection_gate.py
│   ├── PreToolUse_ownership_colocation_gate.py
│   └── PreToolUse_investigation_gate.py
├── PostToolUse (routers + standalone)
│   ├── PostToolUse_router.py (v2.1)
│   ├── PostToolUse_lint_router.py
│   ├── PostToolUse_write_router.py (v1.1)
│   ├── posttooluse/integration_verifier.py
│   ├── posttooluse/observable_effect_verifier.py
│   └── posttooluse/truth_validator_hook.py
└── Stop (routers + standalone)
    ├── Stop_router.py (consolidated)
    ├── StopHook_skill_execution_gate.py (v3.5, 3-layer defense)
    ├── StopHook_cross_validator.py (fabrication detection)
    ├── StopHook_unverified_stance.py (anti-sycophancy)
    ├── StopHook_spec_compliance.py
    └── StopHook_reality_check.py
```

### Memory System Architecture

```
MEMORY.md (index, <200 lines)
├── Topic files (76 files in C:\Users\brsth\.claude\projects\P--\memory\)
│   ├── Key lessons (constitution.md, reasoning_flaws.md, questioning_patterns.md)
│   ├── Hook guidance (hook_architecture.md, hooks_operational_guide.md)
│   ├── Technical patterns (mcp_*.md, perf_*.md, testing_*.md)
│   └── Project-specific (bugfixes.md, working_principles.md)
└── Safeguard hook (auto-memory integration)
```

### debugRCA Architecture

```
debugRCA Skill
├── SKILL.md (v2.10.0, enforcement: STRICT)
├── Python Package (P:/packages/debugRCA)
│   ├── evidence_saturation.py (detection threshold 0.75)
│   ├── phase_state_manager.py (resumable sessions)
│   ├── hypothesis_scorer.py (Bayesian updating)
│   ├── local_fallback_mode.py (local-only quality estimation)
│   ├── tool_checker.py (tool availability detection)
│   ├── confidence_tracker.py (Bayesian posterior tracking)
│   └── local_tool_adapter.py (remote→local tool adaptation)
├── Hooks (registered in SKILL.md)
│   ├── PostToolUse_rca_init.py
│   ├── PostToolUse_rca_phase_tracker.py
│   ├── PostToolUse_rca_action_tracker.py
│   ├── PostToolUse_rca_search_validator.py
│   ├── PostToolUse_rca_research_storage.py
│   ├── SessionEnd_rca_cleanup.py
│   └── StopHook_rca_enforcement.py
├── Templates
│   ├── hypothesis_ledger.md
│   └── investigation_report.md
└── Tests (30 files, 83% coverage)
```

---

## 3. EXECUTION AND DATA FLOW

### Hook Execution Flow

**Critical ordering constraint:** Hooks execute in priority order within each event. Priority numbers determine execution sequence.

**UserPromptSubmit execution order (sample):**
```
Priority -1:  style_friction (observability only)
Priority 0:   consent_granter (runs FIRST)
Priority 1:   skill_enforcer
Priority 2:   anti_sycophancy
Priority 3:   plan_context_injector
Priority 4:   value_check_injection
...
Priority 22:  truthfulness_gate
```

**PreToolUse blocking model:**
```
Input → Matcher check → [BLOCK/WARN/ALLOW] → Output JSON
                                    ↓
                    {"continue": bool, "reason": "..."}
```

**Stop hook output model:**
```
Response → Claim extraction → Evidence check → [BLOCK/ALLOW] → Output JSON
                                                         ↓
                                         {"allow": bool, "reason": "..."}
```

### State Management

**Hook state locations:**
| State | Location | Scope |
|-------|----------|-------|
| Session state | `P:/.claude/state/` | Session-scoped |
| Terminal state | `P:/.claude/state/` (terminal_id subdirs) | Terminal-scoped |
| Hook logs | `P:/.claude/hooks/logs/` | Session-scoped |
| Evidence store | `P:/.claude/hooks/evidence_store.py` | Shared |

**Key invariant:** Terminal isolation uses `terminal_id` for multi-terminal safety. State files are scoped by both `session_id` and `terminal_id`.

### Error Handling

**Fail-open default:** Hooks must fail open to prevent blocking user workflow due to system failures.

**Critical rule:** Hooks MUST NOT write to stderr. Claude Code treats stderr as an error.

**Bypass mechanism:** `CONSTITUTIONAL_HOOKS_BYPASS=1` disables all constitutional hooks.

---

## 4. COMPONENT INVENTORY

### Core Logic - Hooks

| Component | Path | Responsibility | Key Functions |
|-----------|------|----------------|---------------|
| **PreToolUse_skill_pattern_gate.py** | `PreToolUse/` | Block unauthorized tools before Skill execution | `_is_skill_first()`, `_check_workflow_steps()` |
| **PreToolUse_write_router.py** | PreToolUse/ | Consolidated write validation | investigation_gate, session_reversion_check, vague_directive_gate |
| **PreToolUse_bash_router.py** | PreToolUse/ | Consolidated bash validation | command_intent_gate, explore_gate, background_guard |
| **Stop_router.py** | hooks/ | Consolidated stop validation | skill_execution_gate, cross_validator, unverified_stance |
| **UserPromptSubmit_router.py** | hooks/ | Consolidated prompt injection | 25+ hooks merged by priority |
| **hook_tracker.py** | hooks/ | Shared constitutional tracking | `is_hook_self_operation()`, `is_bypass_enabled()`, `log_block()` |
| **cc_diagnostic_logger.py** | hooks/ | Structured JSONL logging | `get_enforcement_logger()`, `create_hook_entry()` |

### Utilities - Hooks

| Component | Path | Responsibility |
|-----------|------|----------------|
| **shared_utils.py** | `__lib/` | State management: load_state, save_state, clear_state, log_hook_event |
| **hook_importer.py** | `__lib/` | Import diagnostics to SQLite |
| **terminal_detection.py** | `__lib/` | Terminal/worktree isolation |
| **test_detection.py** | `__lib/` | Pytest-based test file detection |
| **enforcement_rate_limiter.py** | `__lib/` | Advisory warning rate limiting |
| **claim_patterns.py** | `__lib/` | Fabrication claim detection patterns |

### Configuration - Hooks

| File | Purpose |
|------|---------|
| `P:/.claude/settings.json` | Hook registration, env vars, matcher patterns |
| `config/directory_policy.json` | claude_restricted_paths configuration |
| `P:/.claude/hooks/ARCHITECTURE.md` | Constitutional enforcement map (v2.6) |
| `P:/.claude/hooks/HOOKS_CATALOG.md` | Complete hook catalog (updated 2026-03-18) |

### Memories (76 topic files)

| Category | Count | Key Files |
|----------|-------|-----------|
| Constitution/Philosophy | 5 | constitution.md, workflow_clarification.md, working_principles.md, reasoning_flaws.md, questioning_patterns.md |
| Hook guidance | 4 | hook_architecture.md, hooks_operational_guide.md, hooks_conceptual_guide.md, hook_debugging_lessons.md |
| Technical patterns | 25+ | mcp_*.md, perf_*.md, testing_*.md, python_version.md |
| Bug fixes | 5 | bugfixes.md, perf_file_lock_timeout.md, handoff_pre_mortem_lessons.md, adr_*.md |
| Project management | 10+ | skill_location_paths.md, p_drive_vs_home.md, registry-integration-verification.md |

### debugRCA Components

| Component | Path | Responsibility |
|-----------|------|----------------|
| **hook_launcher.py** | hooks/ | Launch RCA hooks via `python -m debug_rca.hook_launcher` |
| **PostToolUse_rca_*.py** | hooks/ | Phase tracking, action tracking, search validation |
| **SessionEnd_rca_cleanup.py** | hooks/ | Session cleanup on SessionEnd |
| **StopHook_rca_enforcement.py** | hooks/ | RCA enforcement at Stop |
| **evidence_saturation.py** | package/ | Semantic similarity + Jaccard overlap detection |
| **phase_state_manager.py** | package/ | Resumable RCA session state |
| **hypothesis_scorer.py** | package/ | Bayesian hypothesis confidence tracking |
| **local_fallback_mode.py** | package/ | Quality estimation when web tools unavailable |

---

## 5. DESIGN INTENT AND NON-NEGOTIABLES

### Architectural Pillars

1. **Hooks enforce, documents provide context** - CLAUDE.md is reference; hooks are authoritative enforcement
2. **Generic-first, specialization-later** - debugRCA principle: universal patterns before domain-specific
3. **Evidence tiers bound confidence** - Tier ceiling limits claims based on evidence source quality
4. **Terminal isolation for multi-session safety** - All state files scoped by terminal_id

### Technology Constraints

| Constraint | Rationale |
|------------|-----------|
| Python 3.14 primary | Main Python version for CI/CD, pyproject.toml, docs |
| No external API calls in hooks | Silent degradation, latency injection, credential complexity |
| No mocks in tests | Fragility, false confidence, maintenance burden |
| Fail-open for error handling | Prevent blocking user workflow |
| No stderr output | Claude Code treats stderr as error |

### Performance SLAs

| Component | SLA | Reference |
|-----------|-----|-----------|
| Hook execution | <100ms latency | SEV hook requirement |
| PreToolUse blocking | Immediate | Block message displayed |
| Stop hook enforcement | After response generation | Post-hoc validation |
| Semantic daemon search | Time-based idle timeout | Disabled before 9pm, 30min after |

### Things That Must NOT Change

| Constraint | Why |
|------------|-----|
| Terminal-scoped state files | Multi-terminal isolation depends on this |
| Priority ordering in routers | Hook behavior depends on execution order |
| Bypass mechanism exists | Debugging mode must be available |
| Evidence tier ceiling system | Constitutional enforcement relies on it |
| Skill execution gate Layer 0 | Prevents wasted token generation |

---

## 6. KNOWN ISSUES

### Active Issues

| Issue | Impact | Workaround |
|-------|--------|------------|
| **Breadcrumb logs accumulation** | Disk space growth | TASK-2273 in progress (self-cleanup) |
| **GTO viability gate performance** | Slow validation | TASK-2341 pending |
| **Adversarial review file rotation** | Accumulation risk | TASK-2274 pending |
| **Terminal ID detection fallback** | 10,700 empty directories created | Fixed (TASK-2275) |

### Resolved Issues (Recent)

| Issue | Fix Date | Reference |
|-------|----------|-----------|
| FileLock timeout fallback proceeds without lock | 2026-03-20 | TASK-2362 (CRIT-004) |
| TOCTOU in evidence freshness verification | 2026-03-20 | TASK-2363 (CRIT-003) |
| Off-by-one freshness error | 2026-03-20 | TASK-2364 (CRIT-003) |
| Path traversal in feedback_loop.py | 2026-03-20 | TASK-2287 |
| Authorization gate intent detection ("1" not recognized) | 2026-03-20 | TASK-2276 |
| Authorization gate 5-second timeout | 2026-03-20 | TASK-2277 |

### Historical Patterns

| Pattern | Root Cause | Prevention |
|---------|------------|------------|
| Dead file edits | LLMs edit files not in dispatch chain | Pre-edit dispatch chain verification |
| Skill not invoked | Prose instead of Skill tool execution | 3-layer defense (skill_enforcer + bypass detection + pattern gate) |
| Template updates skipped | Declaration without execution | Anti-lazy declaration enforcement |

---

## 7. INTEGRATION POINTS

### Hook Integration

**Registration methods:**
```json
// settings.json direct registration
{
  "hooks": {
    "PreToolUse": [{
      "matcher": "Bash|Task|...",
      "hooks": [{"type": "command", "command": "python ...", "timeout": 5}]
    }]
  }
}

// Router registration (UserPromptSubmit, Stop, PostToolUse)
// Add to HOOK_PRIORITY and HOOK_DISPATCH in router file
```

**Dispatch chain verification (MANDATORY before editing):**
```bash
grep -n "UNIVERSAL\|TOOL_HOOKS" P:/.claude/hooks/PreToolUse.py | grep -i "target_file"
```

### debugRCA Integration

**Hook launcher pattern:**
```bash
python -m debug_rca.hook_launcher PostToolUse_rca_phase_tracker.py
```

**State persistence:**
```python
from debugRCA import PhaseStateManager
manager = PhaseStateManager()
state_id = manager.save("gather", {"evidence": [...]}, "session-123")
state = manager.restore(state_id)
```

**Environment variables:**
| Variable | Default | Purpose |
|----------|---------|---------|
| `DEBUGRCA_SATURATION_THRESHOLD` | 0.75 | Evidence saturation threshold |
| `DEBUGRCA_STATE_DIR` | `P:/.claude/state/rca` | State directory |
| `DEBUGRCA_TOOL_GATE_ENABLED` | true | Tool availability gate |

### Memory System Integration

**Auto-memory safeguard hook:** Reads conversation for memory-worthy events, writes to `memory/` directory.

**Safeguard hook location:** `P:/.claude/hooks/UserPromptSubmit_modules/memory_safeguard.py`

**Topic file structure:**
```markdown
---
name: {filename}
description: {one-line description}
type: {user, feedback, project, reference}
---

Content with **Why:** and **How to apply:** lines for feedback/project types
```

---

## 8. APPENDIX: KEY FILE REFERENCES

### Hook Critical Paths

| File | Lines | Purpose |
|------|-------|---------|
| `PreToolUse.py` | ~500 | Dispatch chain manifest (UNIVERSAL + TOOL_HOOKS) |
| `Stop_router.py` | ~400 | Consolidated stop validation |
| `UserPromptSubmit_router.py` | ~600 | 25+ prompt hooks consolidated |
| `ARCHITECTURE.md` | ~500 | Constitutional enforcement map |

### Memory Key Files

| File | Purpose |
|------|---------|
| `MEMORY.md` | High-frequency index (<200 lines) |
| `constitution.md` | READ FIRST - Director + AI workforce philosophy |
| `verification_tiers.md` | Evidence tier system |
| `hook_architecture.md` | Hook enforcement patterns |

### debugRCA Key Files

| File | Purpose |
|------|---------|
| `SKILL.md` | v2.10.0, enforcement: STRICT, 8 PostToolUse + 2 SessionEnd + 1 Stop hook |
| `GENERIC_PROTOCOL.md` | Universal debugging principles |
| `HOOKS_SKILLS_SPECIALIZATION.md` | Domain-specific instantiation |
| `README.md` | v1.0.0, Tier 1 package documentation |

---

## 9. VALIDATION COMMANDS

```bash
# Verify hook dispatch chain
python P:/.claude/hooks/tests/test_dispatch_chain_verification.py

# Check hook registration
python P:/.claude/hooks/tests/test_hook_registration.py

# Run debugRCA tests
cd P:/packages/debugRCA && pytest tests/ -v --cov=. --cov-report=term-missing

# Check memory safeguard
python -c "from pathlib import Path; import sys; sys.path.insert(0, 'P:/.claude/hooks'); from memory_safeguard import check_memory_safeguard; print(check_memory_safeguard())"

# Hook diagnostics
python P:/.claude/hooks/hook_diagnostics.py
```

---

*Bundle generated by /review_bundle skill*
*Scope: hooks + memories + debugRCA*
*Timestamp: 2026-03-23*
