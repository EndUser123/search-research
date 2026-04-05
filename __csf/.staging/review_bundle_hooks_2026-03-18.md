# Review Bundle: CSF Hooks System

**Generated:** 2026-03-18
**Scope:** P:/.claude/hooks/ (Cognitive Steering Framework)
**File Count:** ~815 Python files (non-test), 104 config/json files
**Execution Mode:** 4-agent parallel (large scope >50 files)

---

## 1. PROJECT CONTEXT

### Bundle Metadata
- **System:** Cognitive Steering Framework (CSF) Hooks
- **Purpose:** Structural enforcement hooks for Claude Code - deterministic control over AI behavior
- **Version:** 2.6 (as of 2026-03-16)
- **Platform:** Windows 11, Python 3.12+
- **Change Frequency:** High (daily commits)

### Domain & Purpose
The CSF Hooks system implements **deterministic control** over Claude Code's AI behavior. Unlike advisory documentation, these hooks can **block actions** before they execute. The system enforces constitutional rules (CLAUDE.md), tracks evidence, validates claims, and coordinates multi-terminal sessions. Critical for solo development workflow quality and reliability.

### Scale Metrics
- **Total Python files:** ~815 (excluding tests)
- **Root-level hooks:** 100+ files
- **Major subsystems:** 12 functional domains, 5 router systems
- **Test files:** 600+ (in `tests/` subdirectory)
- **Documentation:** 20+ markdown files
- **State files:** 50+ JSON state files in `state/`
- **Directory size:** 603MB

### Your Environment
- **OS:** Windows 11 Pro (WSL-compatible paths)
- **Shell:** bash (Unix shell syntax required)
- **Python:** 3.12+ (type hints required, pytest for testing)
- **Package managers:** pip, npm (for some tools)
- **Databases:** SQLite (diagnostics.db, evidence.db)
- **External services:** CKS (Constitutional Knowledge System), CHS (Chat History System)

---

## 2. ARCHITECTURE OVERVIEW

```
┌─────────────────────────────────────────────────────────────────┐
│                    Claude Code Session                           │
└──────────────────────────┬──────────────────────────────────────┘
                           │
        ┌──────────────────┴──────────────────┐
        │         Hook Event Lifecycle       │
        └──────────────────┬──────────────────┘
                           │
     ┌─────────────────────┼─────────────────────┐
     │                     │                     │
     ▼                     ▼                     ▼
┌─────────┐         ┌──────────┐        ┌──────────┐
│Session  │         │UserPrompt│        │ PreTool  │
│ Start   │───────►│ Submit   │───────►│ Use      │
└────┬────┘         └─────┬────┘        └─────┬────┘
     │                    │                   │
     │                    ▼                   ▼
     │              ┌──────────┐        ┌──────────┐
     │              │  Inject  │        │  Block   │
     │              │ Context  │        │  Gate    │
     │              └─────┬────┘        └─────┬────┘
     │                    │                   │
     │                    ▼                   │
     │              ┌──────────┐             │
     │              │   AI     │◄────────────┘
     │              │ Process  │
     │              └─────┬────┘
     │                    │
     │                    ▼
     │              ┌──────────┐
     │              │  Tool    │
     │              │ Execute  │
     │              └─────┬────┘
     │                    │
     ▼                    ▼
┌─────────┐         ┌──────────┐
│  Post   │◄────────│  Tool    │
│  Tool   │         │ Complete │
│  Use    │         └─────┬────┘
└────┬────┘               │
     │                    ▼
     │              ┌──────────┐
     │              │  AI      │
     │              │ Response │
     │              └─────┬────┘
     │                    │
     ▼                    ▼
┌─────────┐         ┌──────────┐
│  Stop   │◄────────│Response  │
└─────────┘         └──────────┘
```

### Major Subsystems

#### 1. Router System (5 routers)
- **PreToolUse.py** (49KB) - Main PreToolUse router with DISPATCH CHAIN
- **UserPromptSubmit_router.py** (8.9KB) - Consolidates 20+ UserPromptSubmit hooks
- **PostToolUse_router.py** (21KB) - Consolidates 4+ PostToolUse hooks
- **Stop_router.py** (21KB) - Consolidates 20+ Stop hooks
- **PreToolUse_verification_router.py** (11KB) - Verification gates

**Purpose:** Reduce subprocess overhead by consolidating related hooks into single in-process execution (~90% latency reduction)

**Dependencies:** All routers depend on `hook_tracker.py` and `cc_diagnostic_logger.py`

#### 2. Domain System (12 Functional Domains)
- **Truth & Evidence** (12 hooks) - Block diagnostic claims without verification
- **Quality & Behavioral** (6 hooks) - Detect overconfidence, sycophancy, lazy closure
- **Constitutional Patterns** (5 hooks) - Assumption audit, anti-sycophancy
- **Code Protection** (5 hooks) - Syntax gates, hook protection, TDD
- **Investigation & Research** (3 hooks) - Block modifications without reading first
- **Path & File Safety** (5 hooks) - Path resolution, file locking
- **Task & Session Management** (5 hooks) - Task coordination, session tracking
- **Cognitive Frameworks** (2 hooks) - Solo dev injection, goal anchoring
- **Skill & Workflow Enforcement** (6 hooks) - Slash command enforcement
- **Observability & Logging** (5 hooks) - System 2 debugging, failure recording
- **Formatting & Style** (2 hooks) - Auto-formatting (ruff/prettier)
- **CKS** (4 hooks) - Decision capture, memory injection

#### 3. UserPromptSubmit_modules/ (47 modules)
- **Anti-sycophancy system** - `anti_sycophancy/` domain with 7 modules
- **Cognitive enhancers** - Think trigger, reasoning mode selector
- **Task detection** - Workflow tier tagging, memory size enforcement
- **Declaration reminder** - Anti-lazy declaration enforcement

#### 4. State Management System
- **Location:** `state/` directory (50+ JSON files)
- **Isolation:** Terminal-scoped state files (`{session_id}_{terminal_id}.json`)
- **Cleanup:** TTL-based (5-60 minutes depending on state type)
- **Consistency:** Fail-open on errors (graceful degradation)

#### 5. anti_sycophancy/ Domain
- **7 specialized modules** - affirmation_detector, overconfidence_detector, lazy_closure_detector, hypothesis_as_fact_detector, response_structure_detector, unverified_stance_detector, advocate_injection
- **3-layer architecture** - Layer 1 (injector), Layer 2 (detectors), Layer 3 (advocate protocol)
- **Integration:** Used by both UserPromptSubmit (injection) and Stop hooks (detection)

#### 6. Daemon Architecture
- **SessionStart_search_daemon.py** - Unified semantic daemon (CHS/CKS search)
- **SessionStart_dreaming_daemon.py** - Background dreaming/consolidation
- **SessionStart_semantic_daemon.py** - Legacy semantic daemon (being phased out)
- **Named pipes:** `\\.\pipe\csf_nip_semantic_{PID}_{timestamp}` (Windows)

#### 7. Verification System
- **StopHook_cross_validator.py** - Block "fixed" claims without empirical verification
- **observable_effect_verifier.py** - Verify expected side effects (logging FileHandler → log files)
- **integration_verifier.py** - Prevent aspirational documentation

#### 8. Constitutional Infrastructure
- **hook_tracker.py** - Shared infrastructure for all constitutional hooks
  - `is_hook_self_operation()` - Catch-22 prevention
  - `is_bypass_enabled()` - CONSTITUTIONAL_HOOKS_BYPASS check
  - `log_block()` - Log to `logs/constructional_blocks.jsonl`
- **cc_diagnostic_logger.py** - Structured JSONL logging
  - `logs/enforcement.jsonl` - Enforcement decisions (7-day retention)
  - `logs/diagnostics/hook_invocations.jsonl` - Router orchestration (1-day)

---

## 3. EXECUTION AND DATA FLOW

### Execution Sequences

#### SessionStart Flow
```
CLI Session Starts
  │
  ├─► SessionStart_terminal_id.py (derive/assign terminal_id)
  ├─► SessionStart_constraint_display.py (show constitutional rules)
  ├─► SessionStart_memory_monitor.py (check MEMORY.md size)
  ├─► SessionStart_semantic_daemon.py (start CHS/CKS daemon)
  ├─► SessionStart_hook_health_check.py (verify hook registration)
  └─► SessionStart_search_daemon.py (start unified semantic daemon)
```

#### UserPromptSubmit Flow
```
User submits prompt
  │
  ├─► UserPromptSubmit_router.py (in-process consolidation)
  │   ├─► skill_enforcement (detect slash commands)
  │   ├─► anti_sycophancy (ADVOCATE PROTOCOL injection)
  │   ├─► plan_context_injector (plan structure injection)
  │   ├─► unified_injector (solo dev, goal, falsification)
  │   └─► 15+ more hooks...
  │
  └─► Inject context into prompt
```

#### PreToolUse Flow
```
AI attempts tool use
  │
  ├─► PreToolUse.py (DISPATCH CHAIN verification)
  │   ├─► UNIVERSAL hooks (always run):
  │   │   ├─► PreToolUse_tdd_gate.py (TDD phase enforcement)
  │   │   ├─► PreToolUse_skill_pattern_gate.py (skill pattern v3.2)
  │   │   └─► PreToolUse_hook_edit_gate.py (test before editing hooks)
  │   │
  │   ├─► TOOL_HOOKS (matcher-based):
  │   │   ├─► Write/Edit → PreToolUse_syntax_gate.py
  │   │   ├─► Write/Edit → PreToolUse_hook_protection_gate.py
  │   │   ├─► Bash → PreToolUse_bash_router.py (parallel validation)
  │   │   └─► Task → PreToolUse_explore_gate.py
  │   │
  │   └─► Return {"continue": bool, "reason": "..."}
  │
  └─► If continue=false, block tool execution
```

#### PostToolUse Flow
```
Tool completes
  │
  ├─► PostToolUse_router.py (in-process consolidation)
  │   ├─► FixValidator (syntax/undefined method checks)
  │   ├─► ChangeVerification (tracks file changes)
  │   ├─► FalsificationAssessor (outcome validation)
  │   └─► SemanticCompress (context management)
  │
  ├─► PostToolUse_code_verification_gate.py (py_compile check)
  ├─► PostToolUse_lint_router.py (ruff/prettier auto-format)
  └─► repositories/doc_cks_ingester.py (CKS storage)
```

#### Stop Flow
```
AI response complete
  │
  ├─► Stop_router.py (consolidates 20+ hooks)
  │   ├─► StopHook_skill_execution_gate.py (skill execution v3.5)
  │   ├─► assumption_audit_v2.py (assumption compliance)
  │   ├─► StopHook_cross_validator.py ("fixed" claim verification)
  │   ├─► StopHook_unverified_stance.py (skeptical language detection)
  │   ├─► StopHook_behavioral_quality_gate.py (lazy fix, thrashing)
  │   └─► 15+ more hooks...
  │
  ├─► Session violation count → notification trigger
  └─► Return {"allow": bool, "reason": "..."}
```

### State Management

#### State Files (Terminal-Scoped)
- **Pattern:** `{hook_name}_{terminal_id}.json` or `{session_id}_{terminal_id}.json`
- **Location:** `state/` directory
- **Isolation:** Each terminal gets its own state (no cross-terminal bleed)
- **TTL:** 5-60 minutes (hook-specific)

**Key State Files:**
- `state/anti_sycophancy_injector/` - Challenge markers (TTL: 5 min)
- `state/tdd-state/` - TDD cycle state
- `state/debug_session_state.json` - Error tracking
- `state/task-identity/` - Task recovery state
- `state/terminals/` - Terminal-specific state

#### Multi-Terminal Safety
- **CONSTITUTIONAL REQUIREMENT:** All state MUST be terminal-scoped
- **UUID fallback:** When session_id/terminal_id are empty, generate `auto_{uuid}` fallback
- **No shared mutable state:** Prevents cross-terminal contamination

### Error Handling

#### Fail-Open Policy
- **Principle:** Hooks should fail open when state is corrupted/missing
- **Implementation:** Try/except blocks that return `None` or `{"continue": True}` on error
- **Rationale:** Prevent hooks from blocking legitimate work due to system failures

#### Exit Code Convention
- **Exit 0:** Allow action
- **Exit 2:** Block action (Claude Code protocol)
- **stderr:** Hook stderr is treated as error - use stdout or log files

#### Bypass Mechanism
```bash
export CONSTITUTIONAL_HOOKS_BYPASS=1  # Disable all constitutional hooks
```

#### Logging Strategy
- **Enforcement:** `logs/constructional_blocks.jsonl` (7-day retention)
- **Diagnostics:** `logs/diagnostics/` (JSONL structured logs)
- **Hook invocations:** `logs/diagnostics/hook_invocations.jsonl`
- **SQLite:** `logs/diagnostics/diagnostics.db` (importer diagnostics)

---

## 4. COMPONENT INVENTORY

### Core Logic

| Component | Path | Responsibility | Inputs | Outputs |
|-----------|------|----------------|--------|---------|
| **Hook Tracker** | `hook_tracker.py` | Constitutional enforcement infrastructure | hook_name, command | block decision, log entry |
| **Diagnostic Logger** | `cc_diagnostic_logger.py` | Structured logging for enforcement | hook_name, decision | JSONL log entries |
| **TDD Gate** | `skills/tdd/hooks/PreToolUse_tdd_gate.py` | Enforce RED→GREEN→REFACTOR cycle | tool_name, context | block/allow |
| **Skill Pattern Gate** | `PreToolUse/PreToolUse_skill_pattern_gate.py` | v3.2 parallel regex + daemon validation | bash command, context | block/allow |
| **Anti-Sycophancy** | `anti_sycophancy/` (7 modules) | Detect and block sycophantic patterns | response text | pattern match, severity |
| **Cross Validator** | `StopHook_cross_validator.py` | Block "fixed" claims without evidence | response, tool_events | block/allow |
| **Overconfidence Detector** | `anti_sycophancy/overconfidence_detector.py` | Detect overconfident claims without evidence | response text | pattern match, suggestion |
| **Investigation Gate** | `PreToolUse_investigation_gate.py` | Block modifications without reading first | tool_name, file_path | block/allow |

### Utilities/Helpers

| Component | Path | Responsibility |
|-----------|------|----------------|
| **Shared Utils** | `shared_utils.py` | State management, logging, session operations |
| **Hook Runner** | `__lib/hook_runner.py` | Subprocess execution wrapper for hooks |
| **Hook Base** | `__lib/hook_base.py` | `@hook_main` decorator for hook functions |
| **Test Detection** | `__lib/test_detection.py` | pytest-based test file detection |
| **Claim Patterns** | `__lib/claim_patterns.py` | ACTION_CLAIM_PATTERNS for fabrication detection |
| **Terminal Detection** | `terminal_detection.py` | Terminal ID derivation for multi-terminal safety |

### Configuration

| Component | Path | Responsibility |
|-----------|------|----------------|
| **domains.json** | `domains.json` | 4 domains for UserPromptSubmit execution order |
| **metadata.json** | `metadata.json` | Hook layer, priority, blocking, state I/O |
| **directory_policy.json** | `config/directory_policy.json` | Single source of truth for directory structure |
| **cognitive_enhancers_config.json** | `cognitive_enhancers_config.json` | FAP detection, topics, enhancers |
| **research_router_config.json** | `research_router_config.json` | Research routing triggers |
| **critical_hooks.json** | `critical_hooks.json` | Hooks requiring comprehensive test coverage |

### Infrastructure

| Component | Path | Responsibility |
|-----------|------|----------------|
| **Router Files** | `*_router.py` | Consolidated hook execution (5 routers) |
| **State Directory** | `state/` | Terminal-scoped state files (50+ JSON) |
| **Logs Directory** | `logs/` | Enforcement, diagnostics, hook invocation logs |
| **Session Data** | `session_data/` | Runtime data (evidence.db, enforcement_state.json) |
| **Scanners** | `scanners/` | Modular validation components (StrawberryValidator) |
| **Daemons** | `SessionStart_*_daemon.py` | Background services (semantic search, dreaming) |

### Known Limitations

1. **PreToolUse.py DISPATCH CHAIN** - Only hooks listed in UNIVERSAL or TOOL_HOOKS actually execute. Dead hooks exist but are not called.
2. **UserPromptSubmit_modules/** - Only 8 of 47 modules are registered in the router (17% registration rate).
3. **State file cleanup** - TTL-based cleanup doesn't always run on crash, may leave stale files.
4. **Multi-terminal isolation** - Relies on terminal_id being set correctly; edge cases exist.
5. **GitHub API 401** - Search-research integration has authentication issues (known problem).

---

## 5. DESIGN INTENT AND NON-NEGOTIABLES

### Architectural Pillars

1. **Deterministic Control** - Hooks MUST block when constitutional rules are violated. Advisory documentation is insufficient.
2. **Multi-Terminal Safety** - ALL state MUST be terminal-scoped. No shared mutable state across terminals.
3. **Evidence-Based Verification** - Claims require evidence from THIS turn's tool execution. No grandfathered evidence.
4. **Router Consolidation** - Hooks MUST be consolidated into routers to reduce subprocess overhead (~90% latency reduction goal).
5. **Fail-Open Error Handling** - Hooks MUST fail open on errors to prevent blocking legitimate work due to system failures.
6. **Hook Edit Verification** - Before editing ANY hook file, verify it's in the dispatch chain (DISPATCH CHAIN check is mandatory).

### Technology Constraints

1. **Python 3.12+** - Type hints required for all new code.
2. **pytest** - Required for testing (no unittest, no nose).
3. **bash shell syntax** - All bash commands must use Unix syntax (Windows paths use forward slashes).
4. **stderr = error** - Hooks MUST NOT write to stderr (Claude Code treats stderr as error).
5. **SQLite + JSONL** - Structured logging uses both formats.
6. **Named pipes** - Windows named pipes for daemon communication (`\\.\pipe\csf_nip_semantic_*`).

### Performance SLAs

1. **Router latency** - In-process routers should execute in <100ms.
2. **Hook timeout** - Individual hooks have 5-30 second timeouts.
3. **Total hook overhead** - Should be <300ms per turn (all hooks combined).
4. **State cleanup** - TTL-based cleanup should run within 1 second.

### Things That Must NOT Change

1. **DISPATCH CHAIN verification** - Before editing hooks, always verify the hook is in PreToolUse.py UNIVERSAL or TOOL_HOOKS lists.
2. **Exit code 2 = block** - This is Claude Code protocol. Never change exit code 2 to mean something else.
3. **Terminal-scoped state** - State files MUST include terminal_id in filename. No global state.
4. **Constitutional bypass** - `CONSTITUTIONAL_HOOKS_BYPASS=1` is the ONLY way to disable all constitutional hooks. No other backdoors.
5. **12 functional domains** - Domain structure is constitutional. Don't add/remove domains without architectural review.
6. **TDD enforcement** - TDD gate (Layer 0) is non-negotiable. Implementation before test is blocked.

---

## 6. KNOWN ISSUES

| # | Scenario | Expected vs Actual | Impact | Workaround |
|---|----------|-------------------|--------|------------|
| 1 | Hook file edited | Hook should execute | Hook doesn't execute (not in dispatch chain) | Verify DISPATCH CHAIN in PreToolUse.py before editing |
| 2 | Terminal ID empty | Should generate UUID fallback | Falls back to "unknown" (multi-terminal contamination) | Check `StopHook_unverified_stance.py` FIX-003 |
| 3 | Challenge marker old (>5 min) | Should be rejected | Marker persists, blocks legitimate responses | FIX-001: Add TTL validation to marker JSON |
| 4 | STATUS tag without Bash | Should warn or block | STATUS tags used without verification | FIX-002: Add STATUS tag compliance check |
| 5 | GitHub API 401 | Search should work | Authentication fails | Use alternative search methods (Tavily, Exa) |
| 6 | State file accumulation | TTL cleanup should remove old files | Files accumulate in `state/` | Manual cleanup: `find state/ -name "*.json" -mtime +1 -delete` |
| 7 | Mock patches in tests | Tests should verify real behavior | Mocks hide integration issues | Write integration tests without mocks (see `test_anti_sycophancy_integration.py`) |
| 8 | Read tool misclassified | Reading code should count as evidence | Read treated as "doc-only" | FIX-005: Remove "Read" from _DOC_ONLY_TOOL_NAMES |
| 9 | Concurrent marker writes | Should not corrupt | Multiple terminals writing same marker | FIX-003: UUID fallback prevents collision |
| 10 | Test files in wrong location | Should go to tests/ | Created in P:/ or __csf/ | Use `PreToolUse_test_location_gate.py` to enforce |

---

## 7. INTEGRATION POINTS

### Where New Solutions Can Plug In

#### 1. Adding a New Hook

**Step 1:** Determine event type (SessionStart, UserPromptSubmit, PreToolUse, PostToolUse, Stop)

**Step 2:** Choose registration method:
- **Router (preferred):** Add to existing router (UserPromptSubmit_router, Stop_router, etc.)
- **Direct settings.json:** For standalone hooks (deprecated for UserPromptSubmit)

**Step 3:** Export `process_prompt()` function (UserPromptSubmit) or return `{"continue": bool}` (other events)

**Step 4:** Register in router:
```python
# In router's import_hook() function:
elif name == "your_hook_name":
    import your_hook_name as mod
    return mod

# In HOOK_PRIORITY:
"your_hook_name": 4.5,  # Lower = earlier

# In HOOK_DISPATCH:
"your_hook_name": run_your_hook_function,
```

**Step 5:** Add to metadata.json (if constitutional):
```json
{
  "name": "YourHook",
  "layer": "0",
  "priority": 100,
  "blocking": true,
  "description": "Your hook description"
}
```

#### 2. Adding a New Domain

**Prerequisite:** Architectural review required. 12 domains is constitutional.

**Process:**
1. Document need in ARCHITECTURE.md "Gaps and Opportunities"
2. Propose domain with hooks that would belong to it
3. Update HOOKS_CATALOG.md with new domain
4. Migrate existing hooks if needed
5. Update dependencies matrix

#### 3. Adding State Management

**Use `shared_utils.py` functions:**
- `load_state(hook_name, key)` - Load state from `state/{hook_name}/{key}.json`
- `save_state(hook_name, key, data)` - Save state with TTL
- `clear_state(hook_name, key)` - Delete state file

**Terminal-scoped state:**
```python
from terminal_detection import get_terminal_id
terminal_id = get_terminal_id(data)
state_key = f"{session_id}_{terminal_id}"
```

#### 4. Adding to Router

**In-process (UserPromptSubmit, PostToolUse):**
```python
def process_prompt(data: dict) -> dict:
    # Your hook logic
    return {"additionalContext": "injection text"}
```

**Subprocess (Stop, PreToolUse):**
```python
def run(data: dict) -> dict | None:
    # Your hook logic
    if should_block:
        return {"block": True, "reason": "Blocked because..."}
    return None  # Allow
```

**Exit code protocol:**
- Exit 0 = allow
- Exit 2 = block
- stderr = error (don't use)

### Data Exchange Contracts

#### Hook Input (data dict)
| Field | Type | Description |
|-------|------|-------------|
| `tool_name` | str | Name of tool being executed (PreToolUse/PostToolUse) |
| `tool_input` | dict | Tool input parameters |
| `tool_response` | str | Tool output (PostToolUse) |
| `response` | str | AI response text (Stop) |
| `assistant_response` | str | Alias for `response` (Stop) |
| `tool_events` | list | List of tool execution events (Stop) |
| `session_id` | str | Session identifier |
| `terminal_id` | str | Terminal identifier |

#### Hook Output
| Format | Use Case |
|--------|----------|
| `{"additionalContext": "text"}` | UserPromptSubmit context injection |
| `{"continue": False, "reason": "..."}` | PreToolUse/PostToolUse block |
| `{"block": True, "reason": "..."}` | Stop hook block |
| `{"allow": True, "note": "..."}` | Stop hook allow with warning |
| `None` | Allow (default for most hooks) |

### Output/Exit Code Expectations

| Event | Exit 0 | Exit 2 | stderr |
|-------|--------|--------|--------|
| **PreToolUse** | Allow | **Block** (correct behavior) | Treated as error |
| **PostToolUse** | Always exit 0 | N/A (should not exit 2) | Treated as error |
| **Stop** | Allow stop | **Block stop** (continue generation) | Treated as error |
| **UserPromptSubmit** | Always exit 0 | N/A (in-process only) | Treated as error |

**Critical:** Exit code 2 from PreToolUse is the hook working correctly (it blocked the action). Do NOT interpret this as an error.

---

## 8. APPENDIX: SAMPLE RUNS / LOGS

### Example 1: TDD Gate Blocking Implementation Before Test

**Command:** `Edit file: new_service.py` (no test file exists)

**Hook:** `PreToolUse_tdd_gate.py`

**Log Output:**
```
⛔ TDD GATE VIOLATION

You are attempting to implement code without a test file.

TDD Rule: Test First (RED) → Implement (GREEN) → Refactor

Required actions:
1. Create test file: tests/test_new_service.py
2. Write failing test for the feature you want to add
3. Run test to verify it fails (RED)
4. Implement feature in new_service.py
5. Run test to verify it passes (GREEN)

To bypass: Add --allow-tdd-bypass to your message
```

**Result:** Blocked (exit code 2)

---

### Example 2: Skill Execution Gate Detecting Prose Substitution

**User Input:** `/code "add error handling"`

**AI Response (prose):** "I'll add error handling to the code..."

**Hook:** `StopHook_skill_execution_gate.py`

**Log Output:**
```
SLASH COMMAND IGNORED

The user invoked /code but you responded with prose instead of executing it.

You MUST:
1. Use the Skill tool to load /code
2. Follow the skill's documented procedure
3. Execute using the appropriate tools (Bash, Task, etc.)

Do NOT interpret slash commands as conversational text.
```

**Result:** Blocked (exit code 2), AI prompted to use Skill tool

---

### Example 3: Cross Validator Blocking "Fixed" Claim Without Evidence

**AI Response:** "✅ ALL FILES PASS - fixed the syntax error"

**Hook:** `StopHook_cross_validator.py`

**Log Output:**
```
⛔ COMPLETION CLAIM VERIFICATION FAILED

Claim: "ALL FILES PASS - fixed the syntax error"

No Bash execution found in session evidence.
Completion claims require runtime verification.

Valid alternatives:
• "I've read the files and identified the issue..."
• Show actual tool execution with error output
• Use tentative language: "I would need to verify..."
```

**Result:** Blocked (exit code 2), AI prompted to verify first

---

### Example 4: Investigation Gate Blocking Modification Without Reading

**Command:** `Edit file: P:/.claude/hooks/SomeHook.py`

**Hook:** `PreToolUse_investigation_gate.py`

**Log Output:**
```
⛔ INVESTIGATION REQUIRED

You are attempting to modify: P:/.claude/hooks/SomeHook.py

Required: Read target file first to understand current implementation

Investigation workflow:
1. Read: P:/.claude/hooks/SomeHook.py
2. Analyze: Understand current behavior and patterns
3. Propose: Explain what you're changing and why
4. Modify: Make targeted edits

To bypass: Add --allow-skip-investigation to your message
```

**Result:** Blocked (exit code 2)

---

### Example 5: Successful Hook Execution (Allowed)

**Command:** `Edit file: test_example.py` (with existing tests)

**Hooks Checked:**
- `PreToolUse_tdd_gate.py` → PASS (test file exists)
- `PreToolUse_syntax_gate.py` → PASS (no syntax error)
- `PreToolUse_hook_protection_gate.py` → PASS (not a hook file)
- `PreToolUse_investigation_gate.py` → PASS (file already read)

**Result:** Allowed (exit code 0), file edited successfully

---

### Enforcement Log Sample

**File:** `logs/constructional_blocks.jsonl`

```json
{"timestamp": "2026-03-18T09:00:00Z", "hook": "PreToolUse_tdd_gate", "tool": "Edit", "command": "Edit file: new_service.py", "decision": "block", "reason": "TDD GATE VIOLATION - No test file exists", "session_id": "session_123", "terminal_id": "console_abc"}
{"timestamp": "2026-03-18T09:01:00Z", "hook": "StopHook_cross_validator", "tool": "Stop", "command": "N/A", "decision": "block", "reason": "COMPLETION CLAIM VERIFICATION FAILED - No Bash execution found", "session_id": "session_123", "terminal_id": "console_abc"}
{"timestamp": "2026-03-18T09:02:00Z", "hook": "PreToolUse_investigation_gate", "tool": "Edit", "command": "Edit file: SomeHook.py", "decision": "block", "reason": "INVESTIGATION REQUIRED - Must read target file first", "session_id": "session_123", "terminal_id": "console_abc"}
```

---

### Router Invocation Log Sample

**File:** `logs/diagnostics/hook_invocations.jsonl`

```json
{"timestamp": "2026-03-18T09:00:00Z", "router": "UserPromptSubmit_router", "hook": "skill_enforcement", "duration_ms": 15, "decision": "allow", "session_id": "session_123", "terminal_id": "console_abc"}
{"timestamp": "2026-03-18T09:00:05Z", "router": "Stop_router", "hook": "StopHook_skill_execution_gate", "duration_ms": 25, "decision": "allow", "session_id": "session_123", "terminal_id": "console_abc"}
{"timestamp": "2026-03-18T09:00:10Z", "router": "PreToolUse.py", "hook": "PreToolUse_tdd_gate", "duration_ms": 8, "decision": "block", "session_id": "session_123", "terminal_id": "console_abc"}
```

---

## END OF BUNDLE

**Generated:** 2026-03-18
**Framework:** Cognitive Steering Framework (CSF) v2.6
**Documentation:** See README.md, ARCHITECTURE.md, CLAUDE.md for complete documentation
**Support:** Check `logs/constructional_blocks.jsonl` for recent enforcement decisions
