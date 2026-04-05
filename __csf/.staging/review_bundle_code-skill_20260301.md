# Review Bundle: /code Skill

**Generated**: 2026-03-01
**Scope**: P:\.claude\skills\code\
**File Count**: 11 files (10 excluding __pycache__)
**Execution Mode**: 2-agent analysis (10-50 file range)

---

## 1. PROJECT CONTEXT

### Bundle Metadata
- **Skill Name**: `/code` - AI-assisted feature development workflow
- **Version**: v2.9.0 (7-phase workflow with STATIC ANALYSIS + TRACE)
- **Primary Language**: Markdown (SKILL.md), Python (hooks), JSON (config)
- **Last Major Update**: 2026-02-28 (TRACE phase implementation)

### Domain & Purpose

The `/code` skill is mission control for AI-assisted feature development, providing a systematic 6-phase workflow to transform ideas into production-ready features. It bridges the gap between "I want X" and "X is done" by enforcing TDD discipline, automated verification, and manual code trace-through.

**Target Users**: Solo developers using AI agents (Claude Code, Cursor, Copilot) who need systematic workflow enforcement.

**Why Critical**: Prevents the common failure mode of AI-assisted development—generating code that passes tests but contains hidden logic errors, resource leaks, or race conditions. The TRACE phase (v2.9.0) catches 60-80% of logic errors that automated testing misses, with documented 12x ROI.

### Scale Metrics
- **LOC**: ~2,500 lines (SKILL.md main workflow + references)
- **Major Subsystems**: 7 phases, 4 execution models, 25+ validation rules
- **Deployment Scope**: Local development workflows (not production deployment)
- **Change Frequency**: Active development (last major release: v2.9.0 with TRACE phase)

### Your Environment
- **OS and Shell**: Windows 11, Git Bash, PowerShell
- **Primary Languages**: Python 3.12+, TypeScript, Bash
- **Package Managers**: uv (Python), pnpm (TypeScript), standard system package managers
- **Databases or External Services**: No external services (local git, pytest, static analysis tools)

---

## 2. ARCHITECTURE OVERVIEW

```
┌─────────────────────────────────────────────────────────────┐
│                    /code Skill Entry Point                   │
│                        (SKILL.md)                            │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
        ┌──────────────────────────────┐
        │   Phase Selection Logic      │
        │  (auto-detect or --phase=N)  │
        └──────────────┬───────────────┘
                       │
        ┌──────────────┴───────────────┐
        │                             │
        ▼                             ▼
┌──────────────┐              ┌────────────────┐
│ Planning     │              │ Execution      │
│ Phases       │              │ Model          │
│ (0, 1, 2)    │              │ Selection      │
│              │              │                │
│ Flexible     │              │ Thresholds:    │
│ Order        │              │ - ≤2 files     │
│              │              │   → Standard    │
│ BOOTSTRAP    │              │ - >5 files     │
│ ALIGN        │              │   → Team       │
│ DESIGN       │              │ - >8 files     │
│              │              │   → Hybrid      │
└──────────────┘              └────────┬───────┘
                                         │
                      ┌──────────────────┴──────────────┐
                      │                                 │
                      ▼                                 ▼
            ┌──────────────────┐              ┌────────────────┐
            │ Execution        │              │ Phase Order    │
            │ Phase (3)        │              │ Enforcement    │
            │                  │              │ Hook           │
            │ TDD Loop:        │              │                │
            │ RED →            │              │ validate_code_  │
            │ GREEN →          │              │ phase_order.py  │
            │ REFACTOR         │              │                │
            │                  │              │ Blocks:        │
            │ Builder/Verifier │              │ - TRACE before │
            │ Subagents        │              │   SHIP         │
            └──────┬───────────┘              │ - BUILD before │
                   │                         │   TRACE        │
                   │                         └────────────────┘
                   │
        ┌──────────┴──────────┐
        │                     │
        ▼                     ▼
┌──────────────────┐  ┌─────────────────┐
│ STATIC ANALYSIS  │  │ TRACE (3.5)     │
│ (3.4)            │  │                 │
│                  │  │ Manual code     │
│ Tool-based:      │  │ trace-through   │
│ - ruff, pylint   │  │ for logic       │
│ - mypy, bandit   │  │ correctness     │
│ - eslint, tsc    │  │                 │
│                  │  │ References:     │
│ Standards:       │  │ - TRACE_        │
│ - /code-python   │  │   TEMPLATES.md  │
│ - /code-ts       │  │ - TRACE_        │
│ - /code-stds     │  │   CHECKLIST.md  │
└──────────────────┘  └────────┬────────┘
                               │
                               ▼
                    ┌──────────────────┐
                    │ SHIP (4)         │
                    │                  │
                    │ Certify DONE     │
                    │ Smart build      │
                    │ verification     │
                    └──────────────────┘
```

### Major Subsystems

#### 1. Planning Phases (0, 1, 2)
- **Purpose**: Define WHY and WHAT before HOW
- **Files**: SKILL.md sections 238-294
- **Main Entry Points**: Phase 0 (BOOTSTRAP), Phase 1 (ALIGN), Phase 2 (DESIGN)
- **Dependencies**: `/search`, `spec_kit`, `/brainstorm`, `/arch` skills
- **Critical Invariants**: Flexible order—can skip or revisit planning phases

#### 2. Execution Model Selection
- **Purpose**: Choose implementation approach based on complexity
- **Files**: SKILL.md sections 296-440
- **Main Entry Points**: Threshold-based routing (trivial, standard, team, hybrid)
- **Dependencies**: Task list ID, shared task list discipline
- **Critical Invariants**: Deterministic thresholds prevent arbitrary selection

#### 3. BUILD Phase (3)
- **Purpose**: Autonomous builder/verifier loop with TDD discipline
- **Files**: SKILL.md sections 296-440
- **Main Entry Points**: RED → GREEN → REFACTOR → VERIFY cycle
- **Dependencies**: `/test`, `/qa`, subagent dispatch infrastructure
- **Critical Invariants**: Completion guard (4 evidence types required before marking task done)

#### 4. STATIC ANALYSIS Phase (3.4)
- **Purpose**: Automated quality checks before manual verification
- **Files**: SKILL.md sections 470-568
- **Main Entry Points**: Tool-based validation (ruff, mypy, pylint, eslint, tsc)
- **Dependencies**: Language-specific tools, `/code-python`, `/code-typescript`, `/code-standards`
- **Critical Invariants**: Blocking failures (security, type errors) must be fixed before TRACE

#### 5. TRACE Phase (3.5)
- **Purpose**: Manual code trace-through for logic correctness
- **Files**: SKILL.md sections 570-880, plus 4 reference documents
- **Main Entry Points**: TRACE_TEMPLATES.md, TRACE_CHECKLIST.md
- **Dependencies**: `/trace` skill (if available), TRACE reference documents
- **Critical Invariants**: Mandatory for file I/O, locking, exception handling, resource management, concurrent access

#### 6. SHIP Phase (4)
- **Purpose**: Certify DONE with smart build verification
- **Files**: SKILL.md sections 882-950
- **Main Entry Points**: Stop hook enforcement, done claim validation
- **Dependencies**: Git, pytest, build verification scripts
- **Critical Invariants**: Smart build hook prevents shipping broken code

#### 7. Phase Order Enforcement
- **Purpose**: Prevent skipping critical verification phases
- **Files**: hooks/validate_code_phase_order.py
- **Main Entry Points**: PreToolUse hook intercepts Skill() calls
- **Dependencies**: `.claude/state/*.marker` files
- **Critical Invariants**: BUILD → TRACE → SHIP is enforced; planning phases are flexible

---

## 3. EXECUTION AND DATA FLOW

### Execution Sequences

**Standard /code Invocation (Auto-Detect)**:
```
User: /code "implement user authentication"
  ↓
1. Load flows/feature.md for detailed workflow
2. Parse intent → choose path (new feature vs. bug fix vs. refactor)
3. Select execution model (standard/subagents/team/hybrid)
4. Setup task list ID and ownership rules
5. Resolve plan state (continue existing plan.md or create new)
6. Initialize resume ledger and evidence tracking
7. Phase 0 (BOOTSTRAP): Health check, runtime fingerprint, checkpoint
8. Phase 1 (ALIGN): Define WHY with /search
9. Phase 2 (DESIGN): Define WHAT with /brainstorm or /arch
10. Phase 3 (BUILD): RED → GREEN → REFACTOR → VERIFY loop for each task
11. Phase 3.4 (STATIC ANALYSIS): Run ruff, mypy, pylint, etc.
12. Phase 3.5 (TRACE): Manual trace-through using TRACE_TEMPLATES.md
13. Phase 4 (SHIP): Certify DONE with smart build verification
```

**Explicit Phase Invocation**:
```
User: /code --phase=3.5 "verify lock cleanup"
  ↓
1. Hook (validate_code_phase_order.py) checks phase prerequisites
   - Phase 3.5 (TRACE) requires BUILD marker
   - If marker missing → block with error message
   - If marker present → allow
2. Load Phase 3.5 section from SKILL.md
3. Execute TRACE phase workflow
```

### Mandatory Ordering Constraints

| Phase | Prerequisites | Enforcement Mechanism |
|-------|--------------|---------------------|
| **0 (BOOTSTRAP)** | None | Flexible—no enforcement |
| **1 (ALIGN)** | None | Flexible—no enforcement |
| **2 (DESIGN)** | None | Flexible—no enforcement |
| **3 (BUILD)** | None | Always allowed (first execution phase) |
| **3.4 (STATIC ANALYSIS)** | BUILD marker | Hook blocks if missing |
| **3.5 (TRACE)** | BUILD marker | Hook blocks if missing |
| **4 (SHIP)** | BUILD + TRACE markers | Hook blocks if either missing |

**Key Design Decision**: Planning phases (0, 1, 2) are intentionally flexible—developers can skip or revisit them. Verification phases (3.4, 3.5, 4) are strictly enforced.

### State Management

**State Stores**:
1. **`.claude/state/*.marker`** - Phase completion markers
   - `code-build-complete.marker`
   - `code-static-analysis-complete.marker`
   - `code-trace-complete.marker`
2. **`.claude/state/build-state.json`** - Build runtime state
3. **`.claude/history/build-runs.jsonl`** - Run analytics
4. **`plan.md`** - Task specification and acceptance criteria
5. **Resume ledger** - Per-run evidence tracking

**Consistency Model**:
- **Markers**: Created by workflow phases, validated by hook
- **No rollback detection**: Markers persist even if code is reverted (known limitation)
- **Session isolation**: Each run has unique ledger but shares markers across sessions

**Isolation Boundaries**:
- **Task scope**: Each task has independent RED/GREEN/REFACTOR/VERIFY evidence
- **Phase scope**: Markers prevent skipping phases but don't track intra-phase state
- **Multi-terminal**: Scoped task list ID prevents collisions

### Error Handling

**Fail-Open vs Fail-Closed Policy**:
- **Fail-Closed**: Phase order enforcement (hook blocks violations)
- **Fail-Open**: Static analysis warnings (document but continue to TRACE)
- **Fail-Closed**: Blocking static analysis failures (security, type errors)

**Retry/Timeout Behavior**:
- **BUILD phase**: Max 3 attempts per task before HALT and escalation
- **Retry with expanded context**: Each retry includes more surrounding code
- **No automatic escalation**: Requires user decision after 3 failures

**Error Path Tracing**:
- **TRACE phase**: Explicitly traces exception paths (not just happy path)
- **Resource cleanup verification**: Ensures locks/files/connections released in all paths
- **Case studies**: TRACE_CASE_STUDIES.md shows bugs found only in error paths

---

## 4. COMPONENT INVENTORY

### Core Logic

#### SKILL.md (Main Workflow)
- **Path**: `P:\.claude\skills\code\SKILL.md`
- **Key Functions**:
  - Phase selection logic (auto-detect or explicit)
  - Execution model selection (threshold-based routing)
  - Validation rules enforcement (25+ rules)
  - TDD cycle integration (RED → GREEN → REFACTOR → VERIFY)
- **Responsibility**: Orchestrates entire feature development workflow
- **Inputs**: User intent, feature flow document, plan state
- **Outputs**: Production-ready feature with test coverage and verification
- **Known Limitations**:
  - Solo-dev constraints (no team approval gates)
  - Manual TRACE dependency (requires `/trace` skill)
  - Tool availability (ruff, mypy, pylint must be installable)

#### Phase Order Enforcement Hook
- **Path**: `P:\.claude\skills\code\hooks\validate_code_phase_order.py`
- **Key Functions**:
  - `main()`: Read JSON from stdin, validate phase prerequisites
  - Phase validation logic: Check markers for BUILD, STATIC ANALYSIS, TRACE
  - Error messaging: Clear stderr messages explaining blocks
- **Responsibility**: Prevent skipping critical verification phases
- **Inputs**: Hook JSON input via stdin (`tool_name`, `tool_input.args`, `tool_input.name`)
- **Outputs**: JSON decision (`{"continue": true}` or `{"continue": false, "reason": "..."}`)
- **Known Limitations**:
  - No marker creation (only validates)
  - No rollback detection
  - State directory assumption (fails if `.claude/state/` missing)

### Utilities/Helpers

#### TRACE Templates
- **Path**: `P:\.claude\skills\code\references\TRACE_TEMPLATES.md`
- **Key Functions**:
  - Template 1: File I/O with Locking
  - Template 2: File Descriptor Management (with bug/fix examples)
  - Template 3: Concurrent Access & Race Conditions
  - Template 4: Exception Handling with Cleanup
  - Template 5: Lock Acquisition with Timeout
- **Responsibility**: Provide ready-to-use TRACE table templates for common code patterns
- **Inputs**: Function code, line numbers, variables
- **Outputs**: Structured TRACE tables showing variable state at each line
- **Known Limitations**:
  - Manual process (requires developer to fill in templates)
  - Language-agnostic (doesn't detect language-specific patterns)

#### TRACE Checklist
- **Path**: `P:\.claude\skills\code\references\TRACE_CHECKLIST.md`
- **Key Functions**:
  - 9 categories of checks (Resource Management, Exception Handling, Concurrency, Logic, Security, Performance, Code Quality, Testing, Documentation)
  - Priority levels P0-P3 (Critical → Low)
  - Common bugs for each category with detection patterns
  - TRACE report template
- **Responsibility**: Comprehensive verification checklist for TRACE phase
- **Inputs**: Function code, TRACE table
- **Outputs**: List of findings with severity levels
- **Known Limitations**:
  - Manual verification (no automation)
  - Requires expertise to apply correctly

### Configuration

#### Behavior Gates Config
- **Path**: `P:\.claude\skills\code\behavior_gates_config.json`
- **Key Functions**:
  - Agreement patterns: Detect direct implementation commitments ("I'll update", "Let me fix")
  - Guidance patterns: Detect directive guidance to user ("you should modify", "change the config")
  - Tool blacklist: List of tools that trigger behavioral gate violations (currently only "Task")
- **Responsibility**: Define pattern-matching rules for behavioral gates
- **Inputs**: Agent response text
- **Outputs**: Pattern match results
- **Known Limitations**:
  - False positives (patterns may match legitimate advice)
  - No context awareness (doesn't consider execution model)
  - Limited scope (English language patterns only)

### Infrastructure

#### Phase Markers
- **Path**: `.claude/state/code-{phase}-complete.marker`
- **Key Functions**:
  - BUILD_MARKER: Tracks BUILD phase completion
  - STATIC_ANALYSIS_MARKER: Tracks STATIC ANALYSIS phase completion
  - TRACE_MARKER: Tracks TRACE phase completion
- **Responsibility**: Track phase completion for order enforcement
- **Inputs**: Phase completion signal from workflow
- **Outputs**: Marker file creation with timestamp
- **Known Limitations**:
  - No rollback detection (markers persist even if code reverted)
  - No cross-session validation (doesn't validate session continuity)

#### Resume Ledger
- **Path**: `.claude/state/resume-ledger.json` (created per run)
- **Key Functions**:
  - Track evidence for RED/GREEN/REFACTOR/VERIFY stages
  - Enable resume after interruption
  - Support multi-terminal coordination
- **Responsibility**: Per-run evidence tracking
- **Inputs**: Stage completion signals
- **Outputs**: Ledger updates with evidence pointers
- **Known Limitations**:
  - Manual updates required (no automatic ledger creation in workflow)
  - Multi-terminal collision risk without scoped task list ID

---

## 5. DESIGN INTENT AND NON-NEGOTIABLES

### Architectural Pillars

1. **TDD Discipline (RED → GREEN → REFACTOR)**:
   - Non-negotiable: Test-first is mandatory where applicable
   - Implementation follows failing test(s)
   - Independent verification with explicit evidence

2. **Verification Gating**:
   - Non-negotiable: Cannot SHIP before TRACE completes
   - Non-negotiable: Cannot TRACE before BUILD completes
   - STATIC ANALYSIS is recommended but not blocking for TRACE

3. **Evidence Requirements**:
   - Non-negotiable: Four evidence types required before marking task done (RED, GREEN, REFACTOR, VERIFY)
   - No silent stops (must provide blocker contract or done claim)

4. **Phase Flexibility vs. Strictness**:
   - Planning phases (0, 1, 2): Flexible—can skip or revisit
   - Verification phases (3.4, 3.5, 4): Strict—enforced by hook

### Technology Constraints

1. **Python 3.12+** for hooks and scripts
2. **Git repository** required for checkpoint/restore
3. **Static analysis tools** must be installed or installable (ruff, mypy, pylint, eslint, tsc)
4. **Markdown** for workflow documentation (SKILL.md)
5. **JSON** for configuration and state (behavior_gates_config.json, markers)

### Performance SLAs

- **BUILD phase**: Variable (depends on task complexity)
- **STATIC ANALYSIS**: 2-5 minutes
- **TRACE phase**: 30-60 minutes (manual verification)
- **SHIP phase**: 5-10 minutes

### Things That Must NOT Change

1. **Critical Path Enforcement**: BUILD → TRACE → SHIP must remain enforced
2. **TDD Discipline**: RED → GREEN → REFACTOR → VERIFY evidence required
3. **Phase Marker System**: Hook validates markers; workflow creates markers
4. **Completion Guard**: All four evidence types required before marking task done
5. **Standards Integration**: Reference pattern (not delegation) for `/code-python`, `/code-typescript`, `/code-standards`

---

## 6. KNOWN ISSUES

### High Impact

**Issue #1: No Rollback Detection**
- **Scenario**: Developer reverts code after phase marker created
- **Expected**: Hook detects revert and re-quires phase
- **Actual**: Marker persists, phase considered complete even though code reverted
- **Impact**: Can ship code that never passed TRACE verification
- **Workaround**: Manually delete markers after significant reverts (`rm .claude/state/code-*.marker`)

**Issue #2: Silent Stop After RED/GREEN**
- **Scenario**: Agent says "done" after partial TDD cycle, pauses without blocker contract
- **Expected**: Agent provides blocker contract explaining what blocked
- **Actual**: Agent stops silently, unclear what to do next
- **Impact**: Wasted time debugging stopped workflow
- **Workaround**: Re-run with completion guard (`/code --full` forces explicit evidence)

**Issue #3: Multi-Terminal Collisions**
- **Scenario**: Two sessions edit same task simultaneously
- **Expected**: One session blocks, ownership clear
- **Actual**: Both sessions proceed, ownership ambiguous
- **Impact**: Lost work, merge conflicts, confusion
- **Workaround**: Use scoped task list ID (`--task-list-id=<unique-id>`)

### Medium Impact

**Issue #4: Path Translation Errors**
- **Scenario**: Verifier can't find files because paths use `P:\` in one runtime and `/mnt/p/` in another
- **Expected**: Runtime normalizes paths automatically
- **Actual**: Commands pass in one runtime and fail in another
- **Impact**: False verification failures, wasted time
- **Workaround**: Run `runtime_fingerprint.py`, normalize paths manually, re-run failed step

**Issue #5: TRACE Phase Not Always Mandatory**
- **Scenario**: Trivial changes (< 10 lines, documentation-only) skip TRACE
- **Expected**: TRACE required for ALL code changes
- **Actual**: SKILL.md says TRACE is optional for trivial changes
- **Impact**: Hidden bugs in trivial changes can ship
- **Workaround**: Manually invoke TRACE for all changes (`/code --phase=3.5`)

### Low Impact

**Issue #6: False Positives in Behavioral Gates**
- **Scenario**: Agreement patterns match legitimate advice or documentation
- **Expected**: Only direct implementation commitments blocked
- **Actual**: Patterns may match benign text
- **Impact**: Unnecessary warnings, workflow friction
- **Workaround**: Ignore warnings when context makes it clear it's not direct implementation

---

## 7. INTEGRATION POINTS

### Where New Solutions Can Plug In

**1. Custom Validation Rules**
- **Existing Hooks**: `validate_code_phase_order.py`
- **Invocation Model**: PreToolUse hook intercepts Skill() calls
- **Data Exchange**: JSON input via stdin, JSON output via stdout
- **Exit Code Expectations**: 0 (allow), 2 (deny)

**2. TRACE Phase Extensions**
- **Existing Interface**: TRACE_TEMPLATES.md, TRACE_CHECKLIST.md
- **Invocation Model**: Manual reference during Phase 3.5
- **Data Exchange**: Markdown templates copied and filled in
- **Output Expectations**: TRACE report with findings and before/after code

**3. Standards Integration**
- **Existing Interface**: Phase 3.4 (STATIC ANALYSIS) references `/code-python`, `/code-typescript`, `/code-standards`
- **Invocation Model**: Reference pattern (documentation, not delegation)
- **Data Exchange**: Apply standards when writing code, verify compliance in Phase 3.4
- **Output Expectations**: Static analysis findings report

**4. Execution Model Extensions**
- **Existing Interface**: Execution model selection logic in SKILL.md
- **Invocation Model**: Threshold-based routing (trivial → standard, >5 files → team, >8 files → hybrid)
- **Data Exchange**: File count, module count, infrastructure risk assessment
- **Output Expectations**: Chosen execution model with rationale

**5. Behavioral Gate Extensions**
- **Existing Interface**: behavior_gates_config.json
- **Invocation Model**: Pattern matching on agent responses
- **Data Exchange**: Regex patterns for agreement and guidance detection
- **Output Expectations**: Block/warn/signal for behavioral gate violations

---

## 8. APPENDIX: SAMPLE RUNS / LOGS

### Example 1: Phase Order Enforcement Block

**Scenario**: User tries to run TRACE before BUILD completes

**Command**:
```bash
/code --phase=3.5 "verify lock cleanup"
```

**Hook Output**:
```json
{
  "continue": false,
  "reason": "Cannot run TRACE before BUILD completes. TRACE needs built code to analyze. Run /code without --phase flag to auto-detect phase."
}
```

**Exit Code**: 2 (deny)

**Resolution**: Run `/code` without `--phase` flag to auto-detect phase

---

### Example 2: TRACE Phase Finding (Real Bug)

**From**: TRACE_CASE_STUDIES.md (Lock Cleanup Race Condition)

**Code Before**:
```python
def transfer_data(src, dst):
    lock = acquire_lock(src, timeout=30)
    try:
        if lock:
            data = read_data(src)
            write_data(dst, data)
    finally:
        # BUG: Deletes lock even if timeout occurred
        os.unlink(lock_file)
```

**TRACE Table (Timeout Scenario)**:
| Line | Variable State | Resource State |
|------|---------------|----------------|
| `lock = acquire_lock(src, timeout=30)` | lock = None (timeout) | No lock acquired |
| `if lock:` | False (skips block) | No lock acquired |
| `finally:` | (executes cleanup) | **BUG: Deletes another process's lock** |
| `os.unlink(lock_file)` | (runs unconditionally) | Lock file deleted |

**Finding**: P0 Critical - Finally block deletes another process's lock when timeout occurs

**Code After**:
```python
def transfer_data(src, dst):
    lock_acquired = False
    lock = acquire_lock(src, timeout=30)
    try:
        if lock:
            lock_acquired = True
            data = read_data(src)
            write_data(dst, data)
    finally:
        # FIX: Only unlink lock if we acquired it
        if lock_acquired:
            os.unlink(lock_file)
```

**Detection Method**: TRACE of timeout scenario (tests passed, bug found only in TRACE)

**ROI**: 75 min TRACE prevents 5-10 production incidents/month (15-30 hours saved)

---

### Example 3: Successful Workflow Completion

**Command**:
```bash
/code "implement user authentication"
```

**Workflow Output**:
```
🔄 [Phase 0] Starting BOOTSTRAP...
✅ Health check passed
✅ Runtime fingerprint: Windows 11, Python 3.12.1
✅ Checkpoint created: ckpt_20260301_120000

🔄 [Phase 1] Starting ALIGN...
✅ Requirements clarified from plan.md
✅ Scope validated (in/out of scope defined)
✅ Risk assessment: 2 high-risk areas (security, concurrency)

🔄 [Phase 2] Starting DESIGN...
✅ Architecture defined (3 modules: auth, session, middleware)
✅ Data flow mapped (request → auth → session → response)
✅ Test strategy identified (happy path, edge cases, error paths)

🔄 [Phase 3] Starting BUILD...
🔄 Task 1/5: Implement auth module
  ✅ RED: 3 tests created, confirmed FAILING
  ✅ GREEN+REFACTOR: Implementation passes tests, cleanup complete
  ✅ VERIFY: Spec compliance ✅, Code quality ✅, Error handling ✅
🔄 Task 2/5: Implement session module
  ✅ RED: 4 tests created, confirmed FAILING
  ✅ GREEN+REFACTOR: Implementation passes tests, cleanup complete
  ✅ VERIFY: Spec compliance ✅, Code quality ✅, Error handling ✅
🔄 Task 3/5: Implement middleware
  ✅ RED: 2 tests created, confirmed FAILING
  ✅ GREEN+REFACTOR: Implementation passes tests, cleanup complete
  ✅ VERIFY: Spec compliance ✅, Code quality ✅, Error handling ✅
🔄 Task 4/5: Integration tests
  ✅ RED: 5 tests created, confirmed FAILING
  ✅ GREEN+REFACTOR: Implementation passes tests, cleanup complete
  ✅ VERIFY: Spec compliance ✅, Code quality ✅, Error handling ✅
🔄 Task 5/5: Documentation
  ✅ RED: 2 tests created, confirmed FAILING
  ✅ GREEN+REFACTOR: Implementation passes tests, cleanup complete
  ✅ VERIFY: Spec compliance ✅, Code quality ✅, Error handling ✅

🔄 [Phase 3.4] Starting STATIC ANALYSIS...
✅ Python standards: ruff, mypy checks passed
✅ Universal standards: DRY compliance verified
Blocking issues to fix: 0
Warnings documented: 5 (line length, naming)

🔄 [Phase 3.5] Starting TRACE...
🔍 Tracing auth.py (3 functions)
  ✅ Resource management: No leaks
  ✅ Exception handling: All paths covered
  ✅ Concurrency safety: No races
  ✅ Logic correctness: Edge cases handled
🔍 Tracing session.py (2 functions)
  ✅ Resource management: No leaks
  ✅ Exception handling: All paths covered
  ✅ Concurrency safety: No races
  ✅ Logic correctness: Edge cases handled
🔍 Tracing middleware.py (1 function)
  ✅ Resource management: No leaks
  ✅ Exception handling: All paths covered
  ✅ Concurrency safety: No races
  ✅ Logic correctness: Edge cases handled
✅ TRACE complete: 0 findings

🔄 [Phase 4] Starting SHIP...
✅ All tests passing (16/16)
✅ Coverage threshold met (87%)
✅ No blocking findings from review
✅ No blocking validation errors
✅ Production-ready certification

## Pipeline Status: COMPLETE
**Status**: ✅ ALL PHASES PASSED
**Summary**: Code is production-ready, added to portfolio index

### Next Steps
1. Commit changes: `git commit`
2. Push to remote: `git push`
3. Or continue development
```

---

**END OF REVIEW BUNDLE**

This bundle provides comprehensive context for the `/code` skill including architecture, execution flow, component inventory, design constraints, known issues, and integration points. Use this for LLM question-answering, code review, or system understanding tasks.
