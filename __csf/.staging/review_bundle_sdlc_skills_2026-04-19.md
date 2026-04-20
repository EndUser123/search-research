# Review Bundle: SDLC Skills (/go, /code, /tdd, /refactor)

**Generated**: 2026-04-19
**Scope**: `/go`, `/code`, `/tdd`, `/refactor` skills — `P:/.claude/skills/`
**File Count**: ~90 files total (code=67, refactor=16, tdd=8, go=1)
**Execution Mode**: Single-agent (combined scope — skills are architecturally related)

---

## 1. PROJECT CONTEXT

### Domain & Purpose

Four SDLC (Software Development Life Cycle) skills that form a cohesive solo-developer workflow:
- **`/go`** — Ralph loop execution engine for autonomous task completion to PR-ready state
- **`/code`** — Feature development mission control (idea → PR) with mandatory consumer handshake
- **`/tdd`** — Test-Driven Development with parallel subagent delegation
- **`/refactor`** — Structured refactoring plan creation and adversarial review

These skills run inside Claude Code and enforce solo-dev constitutional constraints. Together they implement: plan → explore → contract → TDD → audit → trace → PR artifacts.

### Scale Metrics
- **Total files**: ~90 (code=67, refactor=16, tdd=8, go=1)
- **LOC**: ~3,500+ (code skill alone has 50+ .py files)
- **Major subsystems**: 4 (one per skill)
- **Deployment**: Ships inside Claude Code at `P:/.claude/skills/`
- **Change frequency**: Active development (recent merges from task #153-159)

### Environment
- **OS**: Windows 11 Pro (bash/PowerShell)
- **Primary language**: Python 3.12+
- **Package managers**: pip, pytest
- **Integration**: Claude Code hooks system, git worktrees, subprocess execution

---

## 2. ARCHITECTURE OVERVIEW

```
USER INPUT
    │
    ├─► /go ──────────────────────────────► Ralph Loop (worktree enforcement)
    │                                          ↓
    │                                      task-definition.md
    │                                      7-pass review
    │                                      PR artifacts
    │
    ├─► /code ───────────────────────────► 13-phase workflow
    │   (feature development)                  ↓
    │                                      .claude-state/
    │                                      plan.md (consumer handshake)
    │                                      checklist (5 questions)
    │
    ├─► /tdd ────────────────────────────► RED → GREEN → REFACTOR
    │   (TDD with parallel agents)              ↓
    │                                      tdd-test-writer (parallel)
    │                                      tdd-implementer (parallel)
    │                                      tdd-refactorer (parallel)
    │
    └─► /refactor ──────────────────────► refactor_plan.py
        (adversarial plan review)                ↓
                                              plan_review.py (adversarial)
                                              code_scanner.py (findings)
```

### Shared Infrastructure

| Component | Location | Purpose |
|-----------|----------|---------|
| `evidence_writer.py` | `tdd/lib/` | Unified EvidenceManager for `/code` and `/tdd` |
| `got_planner.py` | `code/utils/` | Graph-of-Thought node extraction from plan.md |
| `task_detector.py` | `code/lib/` | Ralph Loop auto-enable detection |
| `checklist.py` | `code/lib/` | 5-question pre-execution validation |
| `state_encryption.py` | `code/lib/` | Encrypted state management |

---

## 3. EXECUTION AND DATA FLOW

### `/code` Workflow (13 phases)

```
pre_execution_checklist
    ↓
analyze_query_intent
    ↓
select_execution_model
    ↓
resolve_plan_state
    ↓
initialize_resume_ledger
    ↓
requirements_clarity_check
    ↓
preflight_context_validation
    ↓
explore_codebase
    ↓
design_solution
    ↓
consumer_contract_precheck
    ↓
tdd_implementation
    ↓
smoke_validation
    ↓
full_test_suite
    ↓ [verification gates]
    tier0_checklist_verification
    audit_quality_checks
    critique_agent_review
    trace_manual_verification
    producer_consumer_trace_verification
    done_final_certification
```

**State isolation**: `.claude/state/` — each skill maintains isolated state files. Terminal-scoped via `terminal_id`.

### `/tdd` Workflow (5 phases)

```
DISCOVER → RED → GREEN → VERIFY → REGRESSION → REFACTOR
```

- **DISCOVER**: Read code, baseline test results
- **RED**: Write failing tests (parallel tdd-test-writer agents)
- **GREEN**: Minimal implementation (parallel tdd-implementer agents)
- **VERIFY**: Actual command execution (not mocks)
- **REGRESSION**: Auto-run related tests
- **REFACTOR**: Cleanup (parallel tdd-refactorer agents)

### `/go` Ralph Loop

```
worktree_enforcement → task_contract → verify_end_to_end
    ↓
simplify_code (quality gate)
    ↓
seven_pass_review (quick/standard/full based on diff size)
    ↓
create_pr_artifacts
    ↓
loop_check (reads plan.md for next task)
```

### `/refactor` Plan Lifecycle

```
code_scanner.py (find findings)
    ↓
refactor_plan.py (create structured plan)
    ↓
plan_review.py (adversarial review)
    ↓
deduplicate.py (deduplicate findings)
```

### Error Handling
- **Fail-fast**: Hooks block on constitutional violations
- **Graceful degradation**: EvidenceManager fallback to markdown if unavailable (`EVIDENCE_MANAGER_AVAILABLE = False`)
- **State encryption**: `state_encryption.py` with fail-open on decryption errors

---

## 4. COMPONENT INVENTORY

### `/go` (1 file)

| Component | Path | Responsibility |
|-----------|------|----------------|
| SKILL.md | `go/SKILL.md` | Ralph loop: 7-pass review, worktree enforcement, PR artifact generation |

### `/code` (67 files)

| Component | Path | Responsibility |
|-----------|------|----------------|
| SKILL.md | `code/SKILL.md` | 13-phase workflow, flags (--fast/--full/--ralph-*), hooks registration |
| task_detector.py | `code/lib/task_detector.py` | Keyword-based task type detection for Ralph Loop auto-enable |
| checklist.py | `code/lib/checklist.py` | 5-question pre-execution validation with evidence logging |
| state_encryption.py | `code/lib/state_encryption.py` | Encrypted state with Fernet, fail-open on errors |
| gap_loader.py | `code/lib/gap_loader.py` | Load gap data from state files |
| got_planner.py | `code/utils/got_planner.py` | Graph-of-Thought node/edge extraction from plan.md |
| tot_tracer.py | `code/utils/tot_tracer.py` | Tree-of-Thought tracing and branch scoring |
| evidence.py | `code/utils/evidence.py` | EvidenceManager for unified evidence tracking |
| phase_state.py | `code/utils/phase_state.py` | Per-phase state management |
| context7_client.py | `code/utils/context7_client.py` | Context7 API client with rate limiting |
| **Hooks** | `code/hooks/` | PreToolUse_plan_consumer_gate.py, SessionStart, PostToolUse breadcrumb |
| **Tests** | `code/tests/` | 50+ test files covering all phases |

### `/tdd` (8 files)

| Component | Path | Responsibility |
|-----------|------|----------------|
| SKILL.md | `tdd/SKILL.md` | RED-GREEN-REFACTOR with parallel delegation |
| evidence_writer.py | `tdd/lib/evidence_writer.py` | EvidenceManager integration, fallback to markdown |
| gap_loader.py | `tdd/gap_loader.py` | Load test gaps from `.claude/state/test_gaps/` |
| **References** | `tdd/references/` | parallel-delegation, discovery-and-regression, verify-phase, etc. |

### `/refactor` (16 files)

| Component | Path | Responsibility |
|-----------|------|----------------|
| refactor_plan.py | `refactor/scripts/refactor_plan.py` | Create structured refactoring plans from findings |
| plan_review.py | `refactor/scripts/plan_review.py` | Adversarial review of refactoring plans |
| code_scanner.py | `refactor/scripts/code_scanner.py` | Find code quality issues |
| deduplicate.py | `refactor/scripts/deduplicate.py` | Deduplicate findings |
| **References** | `refactor/references/` | ast-refactoring, tdd-implementation, agent-enhancements, etc. |

---

## 5. DESIGN INTENT AND NON-NEGOTIABLES

### Architectural Pillars
1. **Solo-dev first**: All skills enforce single-operator constraints (no multi-user gates)
2. **Evidence-driven**: Every phase produces artifacts in `.evidence/` or `.claude/state/`
3. **Parallel delegation**: Independent tasks delegated to parallel subagents (tdd-*, code-*)
4. **Consumer handshake**: `/code` requires explicit consumer proof before proceeding
5. **Worktree isolation**: `/go` requires git worktree — no main branch edits

### Technology Constraints
- Python 3.12+ with type hints throughout
- pytest for testing
- subprocess for hook execution (not inline imports where isolation needed)
- Fernet encryption for state at rest

### Things That MUST NOT Change
- `/go` must never push or create remote PRs (local artifacts only)
- `/tdd` must always write tests BEFORE code (RED phase enforced)
- Consumer contract precheck must run before TDD implementation in `/code`
- Worktree enforcement is blocking — no bypass exists

---

## 6. KNOWN ISSUES

### KI-001: `context7_client.py` uses requests (should be httpx)
**Severity**: MEDIUM
**Files**: `code/utils/context7_client.py`
**Description**: Uses `requests` library instead of `httpx` per Python 2025+ standards. CLAUDE.md mandates httpx for async-capable code.
**Status**: Open

### KI-002: `TDD_EVIDENCE_DEBUG` env var only controls logging, not full trace
**Severity**: LOW
**Files**: `tdd/lib/evidence_writer.py`
**Description**: Debug flag uses `logger.debug()` but no structured trace output for evidence flow debugging.
**Status**: Open

### KI-003: `refactor_plan.py` effort estimation uses arbitrary multipliers
**Severity**: LOW
**Files**: `refactor/scripts/refactor_plan.py:43-50`
**Description**: `multiplier` values (2.0, 1.5, 1.0, 0.5) have no empirical basis — classic arbitrary threshold violation.
```python
(priority_counts["P0"], 2.0),  # Bugs take longer — no citation
(priority_counts["P1"], 1.5),  # Error handling — no citation
```
**Status**: Open

### KI-004: `got_planner.py` keywords have no case-insensitivity
**Severity**: LOW
**Files**: `code/utils/got_planner.py`
**Description**: Keywords like `'must', 'shall', 'required'` are matched case-sensitively. Most plan files use Title Case for section headers.
**Status**: Open

### KI-005: Breadcrumb tracker hook in `code/hooks/`
**Severity**: MEDIUM
**Files**: `code/hooks/PostToolUse_breadcrumb_tracker.py`
**Description**: Breadcrumb tracker is a PostToolUse hook but CLAUDE.md Section 6 warns PostToolUse hooks cannot block. If breadcrumb tracking is critical for downstream phases, it should be a PreToolUse gate.
**Status**: Open

---

## 7. INTEGRATION POINTS

### Skill-to-Skill Handoffs

| From | To | Mechanism | Contract |
|------|----|-----------|----------|
| `/code` | `/tdd` | Subagent invocation (`tdd-test-writer`, `tdd-implementer`, `tdd-refactorer`) | Test file + failing test spec |
| `/code` | `/go` | Ralph Loop activates via `task_detector.py` | plan.md + task-type=IMPLEMENTATION |
| `/refactor` | `/go` | Findings → refactor_plan → adversarial review → execute | Structured plan in `.claude-state/` |
| `/tdd` | `/code` | Evidence written via EvidenceManager | JSON artifacts in `.evidence/` |

### Hook Integration

| Hook | File | Protects |
|------|------|----------|
| `PreToolUse_plan_consumer_gate.py` | `code/hooks/` | Consumer handshake before edits |
| `SessionStart_breadcrumb_init.py` | `code/hooks/` | Breadcrumb initialization |
| `PostToolUse_breadcrumb_tracker.py` | `code/hooks/` | Breadcrumb tracking (non-blocking) |
| `detect_continuous_mode.py` | `code/hooks/` | Continuous mode detection |

### External Dependencies
- **TDD Guard** (external): `https://github.com/nikosdev/tdd-guard` — referenced in `/tdd` SKILL.md
- **Context7 API**: For documentation lookup during TDD RED phase
- **Claude Code hooks system**: All `code/hooks/` run via settings.json subprocess registration

---

## 8. INPUT/OUTPUT CONTRACT

### `/code` Phase Inputs/Outputs

| Phase | Reads | Writes |
|-------|-------|--------|
| pre_execution_checklist | 5 questions from checklist.py | `.claude/state/checklist_{terminal_id}.json` |
| analyze_query_intent | User prompt | `task-type` + `confidence` |
| resolve_plan_state | `plan.md` | Phase state |
| tdd_implementation | Failing tests | Code artifacts |
| smoke_validation | `.claude/state/` | smoke result |
| full_test_suite | pytest output | test results |
| done_final_certification | All prior artifacts | `done_marker` |

### `/tdd` Phase Inputs/Outputs

| Phase | Reads | Writes |
|-------|-------|--------|
| DISCOVER | Source code | Baseline test results |
| RED | Spec + Context7 | Failing test files |
| GREEN | Failing tests | Minimal code |
| VERIFY | pytest output | Verification artifact |
| REGRESSION | Related tests | Regression report |
| REFACTOR | Working code + tests | Refactored code |

### `/go` Artifacts

| Artifact | Location | Format |
|----------|----------|--------|
| task-definition.md | `.claude-state/` | Markdown |
| verification-results.txt | `.claude-state/` | Plain text |
| review-passes/*.md | `.claude-state/review-passes/` | Markdown |
| commit-message.txt | cwd | Plain text |
| pr-title.txt | cwd | Plain text |
| pr-body.md | cwd | Markdown |

### State Isolation

- **Terminal-scoped**: `terminal_id` in state filenames (e.g., `checklist_{terminal_id}.json`)
- **Global fallback**: `_READY.json` when terminal_id unavailable
- **TTL**: Evidence files expire after 7 days (automatic cleanup)

---

## 9. SKILL METADATA COMPARISON

| Property | /go | /code | /tdd | /refactor |
|----------|-----|-------|------|-----------|
| **Version** | 0.4.0 | 2.29.0 | 2.26.0 | — |
| **Category** | execution | development | execution | execution |
| **Enforcement** | blocking | advisory | advisory | advisory |
| **Workflow Steps** | 7-step loop | 13-phase | 5-phase + 6 verification | 3-script pipeline |
| **Parallel Agents** | no | no | yes (tdd-*) | no |
| **Hooks** | no | yes (3 hooks) | no | no |
| **Ralph Loop** | native | auto-detect | via task_detector | no |
| **Test Coverage** | no tests | 50+ tests | 4 tests | no tests |
| **File Count** | 1 | 67 | 8 | 16 |

---

## 10. ARCHITECTURAL SHARED DEPENDENCIES

### EvidenceManager Sharing

`/tdd/lib/evidence_writer.py` imports EvidenceManager from `/code/utils/`:
```python
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code" / "utils"))
from evidence import EvidenceManager
```

This is a **cross-skill import** — if `code/utils/evidence.py` changes its API, `tdd/lib/evidence_writer.py` breaks silently (fallback to markdown mode).

### contract-primitives Import

`code/hooks/PreToolUse_plan_consumer_gate.py` imports from `contract-primitives` package:
```python
sys.path.insert(0, str(package_src))  # root / "contract-primitives" / "src"
from contract_primitives import discover_local_plan_path, validate_plan_for_execution
```

### Context

`/code` uses Context7 MCP server for documentation lookup during TDD phases. `/tdd` references `/search` integration for pattern discovery.

---

## 11. FAILURE SCENARIOS

### FS-001: Missing plan.md causes /code to hang at consumer_precheck
**Trigger**: User runs `/code "implement feature"` without plan.md
**Propagation**: `consumer_contract_precheck` → validates consumer proof exists → fails
**Current behavior**: Advisory enforcement (enforcement=advisory) — proceeds anyway
**Impact**: Feature built without consumer handshake proof
**Mitigation**: User must provide plan.md or use `--fast` flag

### FS-002: context7_client rate limit causes TDD RED phase to fail
**Trigger**: Multiple rapid `/tdd` invocations
**Propagation**: `context7_client.py` rate limiter hits limit → `/context7` query fails → RED phase uses stale docs
**Current behavior**: No circuit breaker — continues with fallback
**Impact**: Framework syntax may be incorrect in generated tests
**Mitigation**: Rate limiter with `TDD_CONTEXT7_RATE_LIMIT`

### FS-003: TDD enforcement bypass with `TDD_BYPASS=1`
**Trigger**: User sets `TDD_BYPASS=1`
**Propagation**: TDD enforcement disabled → RED phase skipped → code written without tests
**Current behavior**: `TDD_ENABLED=1` gate is bypassed trivially
**Impact**: Constitutional violation (TDD is mandatory) but advisory enforcement allows it
**Mitigation**: Change `/tdd` enforcement from `advisory` to `blocking`

### FS-004: Cross-skill EvidenceManager import path fragility
**Trigger**: `evidence_writer.py` uses relative path traversal to import EvidenceManager
**Propagation**: `sys.path.insert(0, ...parent.parent.parent/code/utils")` → fragile if refactored
**Current behavior**: Falls back to markdown mode silently
**Impact**: Evidence tracking degraded, no error reported
**Mitigation**: Create shared `__lib` at skills level, not nested in `code/`

### FS-005: `/go` worktree enforcement can be bypassed
**Trigger**: User runs `/go` outside a worktree with custom CWD
**Propagation**: Worktree check fails → `/go` blocks with error
**Current behavior**: Blocking enforcement — but uses `git worktree list` which could be spoofed
**Impact**: Edit on main branch instead of worktree
**Mitigation**: No known bypass — enforcement is hard

### FS-006: `refactor_plan.py` arbitrary effort multipliers
**Trigger**: Any refactoring plan generated
**Propagation**: Effort estimates are unverified heuristics (P0=2.0x, P1=1.5x, etc.)
**Current behavior**: Estimates shown to user without calibration
**Impact**: Poor task estimation, poor priority ranking
**Fix needed**: Base multipliers on historical data or remove numeric estimates

---

## 12. OBSERVATION

This review bundle was generated from static analysis. The following should be verified empirically:

1. **Context7 rate limiting behavior** — test actual limit before FS-002 can be confirmed
2. **Breadcrumb tracker non-blocking status** — verify PostToolUse hook cannot actually block
3. **TDD_BYPASS prevalence** — check if users are actually bypassing TDD
4. **EvidenceManager cross-skill coupling** — trace actual import at runtime

---

*Bundle generated by /review_bundle skill — 2026-04-19*
