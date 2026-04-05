# ADR-20260324: Clean-Room TDD Loop Architecture v2 (Enhanced)

**Status:** Accepted
**Date:** 2026-03-24
**Context:** User wants TDD system that works **better than what they had before** — not just restoring NotebookLM Clean-Room TDD, but improving it with modern patterns.

**Supersedes:** Original ADR-20260324 (Proposed) → Now Accepted with enhancements

---

## Decision

Implement **Clean-Room TDD Loop v2** — a six-component system combining:

1. **Phase-Level State Machine** — Extend TDD95State to include RED/GREEN/REFACTOR phases
2. **Autonomous Ralph Loop** — State-machine driven iteration (no LLM dependency)
3. **Three-File Contract** — spec.md + impl.py + test_*.py with immutable judge
4. **Cold Code Review** — Adversarial subagent dispatch after GREEN phase
5. **Constitutional Enforcement Tiers** — enforce/warn modes per TDD phase
6. **GTO-Style Self-Verification** — evals.json assertions for contract compliance

---

## Rationale

### Original NotebookLM Clean-Room TDD (What User Had Before)

| Layer | Function |
|-------|----------|
| **Red/Green/Refactor Orchestration** | Subagent dispatch for each phase |
| **Ralph Wiggum Loop** | Autonomous iterative fix-until-pass |
| **Cold Code Review** | Blinded adversarial critique |
| **Three-File Contract** | spec + impl + tests as explicit artifacts |

### Current TDD-95 Gap

| Layer | Current State | Gap |
|-------|--------------|-----|
| Phase tracking | TDD95State (5 states: NONE → COMPLETE) | No RED/GREEN/REFACTOR phases |
| Autonomous loop | None (gate-keeper only) | No fix-until-pass iteration |
| Cold Code Review | None | No adversarial critique |
| Three-File Contract | Partial (test scaffolding) | No immutable judge |

### v2 Enhancements Over Original

| Enhancement | Original | v2 Improvement |
|-------------|----------|----------------|
| **State Machine** | External orchestration | Integrated into TDD95StateManager (FileLock-safe) |
| **Ralph Loop** | LLM-dependent | State-machine driven, no external API |
| **Cold Code Review** | Separate process | Adversarial subagent dispatch via Stop hook |
| **Three-File Contract** | Informal | Immutable judge + GTO-style evals.json |
| **Enforcement** | All-or-nothing | Constitutional tiers (enforce/warn/none) |
| **Multi-Terminal** | Not specified | Per-terminal isolation via canonicalize_path |

---

## Tradeoffs

| Quality | Improved | Degraded |
|---------|----------|----------|
| **Reliability** | State-machine loop (no LLM dependency) | Higher complexity |
| **Correctness** | Cold Code Review + immutable judge | Additional execution latency |
| **Iteration Speed** | Autonomous RED→GREEN→REFACTOR | Higher total compute per task |
| **Maintainability** | Three-File Contract makes intent explicit | More files to manage |
| **Multi-Terminal** | Per-terminal state isolation | State file cleanup needed |

---

## Multi-Terminal Safety

**Assessment:** SAFE with instance isolation

The Clean-Room TDD loop v2 operates on **per-file, per-terminal state**:

```python
# Existing infrastructure (tdd95_core.py:39-76)
def canonicalize_path(path: Path) -> str:
    """Windows-safe path normalization with instance hashing."""
    instance_id = hashlib.md5(str(Path.cwd()).encode()).hexdigest()[:8]
    return f"{path.resolve().as_posix()}#{instance_id}"

# State directory per terminal
state_file = STATE_DIR / f"tdd95_{terminal_id}.json"
```

**Isolation mechanisms:**
- `canonicalize_path()` ensures per-instance hashing
- `FileLock` prevents concurrent state corruption
- Contract directories scoped by `session_id` + `terminal_id`

---

## Implementation

### Core Architecture v2

```
clean_room_tdd/
├── TDDPhaseState          → NONE → RED → GREEN → REFACTOR → COMPLETE
│   └── (extends TDD95State via adapter)
├── RALPH_LOOP_ENGINE      → State-machine driven iteration (no LLM)
│   └── Uses: FileLock, state polling, max_iterations guard
├── THREE_FILE_CONTRACT    → spec.md + impl.py + test_*.py + evals.json
│   └── test_*.py is IMMUTABLE (agent cannot modify)
├── COLD_CODE_REVIEW       → Adversarial subagent dispatch after GREEN
│   └── Uses: Stop hook + adversarial-* agents
├── ENFORCEMENT_TIERS      → enforce | warn | none per phase
│   └── Constitutional compliance via settings.json
└── GTO_ASSERTIONS         → Self-verifying evals.json in contract
```

### Phase State Machine v2

```
NONE → RED(Write failing tests) → GREEN(Write impl) → REFACTOR → COMPLETE
           ↑                           ↓
           └─── FAIL: Ralph Loop ←────┘
                    (max_iterations=10)
```

### Context Injection Strategy (Demand-Driven Context)

**DDC Pattern**: Instead of loading full contract state at each phase, inject only:

| Phase | Context Injected | Rationale |
|-------|-----------------|-----------|
| RED | spec.md excerpt + existing test patterns | Focus on requirements |
| GREEN | spec.md + failing test output (minimal) | Target the failure |
| REFACTOR | impl.py + passing test metrics | Optimization context |

**Benefit**: Reduces context window pressure during autonomous loops.

**State transitions (FileLock-safe):**

```python
class TDDPhaseState(Enum):
    NONE = "none"
    RED = "red"           # Writing failing tests
    GREEN = "green"       # Writing minimal implementation
    REFACTOR = "refactor" # Improving code, tests pass
    COMPLETE = "complete"

    def can_transition_to(self, target: TDDPhaseState) -> bool:
        VALID_TRANSITIONS = {
            TDDPhaseState.NONE: {TDDPhaseState.RED},
            TDDPhaseState.RED: {TDDPhaseState.GREEN},
            TDDPhaseState.GREEN: {TDDPhaseState.REFRACTOR, TDDPhaseState.RED},  # Loop back on fail
            TDDPhaseState.REFRACTOR: {TDDPhaseState.COMPLETE},
            TDDPhaseState.COMPLETE: set(),  # Terminal state
        }
        return target in VALID_TRANSITIONS.get(self, set())
```

### Ralph Loop Engine (No LLM Dependency)

```python
class RalphLoopEngine:
    """State-machine driven autonomous iteration."""

    MAX_ITERATIONS = 10
    POLL_INTERVAL_SECONDS = 0.1

    def __init__(self, state_manager: TDD95StateManager, contract: ThreeFileContract):
        self.state_manager = state_manager
        self.contract = contract
        self.iterations = 0

    def run(self) -> RalphLoopResult:
        """Execute Ralph Loop: iterate GREEN until tests pass or max iterations."""
        with FileLock(self.state_manager.state_file):
            while self.iterations < self.MAX_ITERATIONS:
                phase = self.state_manager.get_phase(self.contract.impl_path)

                if phase == TDDPhaseState.GREEN:
                    # Run tests
                    result = self._run_tests()
                    if result.passed:
                        return RalphLoopResult.SUCCESS
                    # Transition back to RED for fix
                    self.state_manager.transition(
                        self.contract.impl_path,
                        TDDPhaseState.RED
                    )

                self.iterations += 1
                time.sleep(self.POLL_INTERVAL_SECONDS)

            return RalphLoopResult.MAX_ITERATIONS_EXCEEDED
```

### Ralph Loop Dialogue Strategy (SDA Pattern)

When tests fail during GREEN→RED transition, apply Strategic Dialogue Architecture:

| Step | Action | Output |
|------|--------|--------|
| **Diagnose** | Extract error type | `import_error` \| `assertion_failure` \| `timeout` |
| **Localize** | Identify specific location | Test file:line + function name |
| **Generate** | Create minimal fix candidate | Single targeted change |
| **Verify** | Run only affected test | Not full suite (speed optimization) |

**Escalation rule**: After `MAX_ITERATIONS=10`, escalate to human with diagnostic summary.

### Three-File Contract with Immutable Judge

```python
@dataclass
class ThreeFileContract:
    """Karpathy's AutoResearch pattern with immutable evaluation."""

    spec_path: Path      # Human-written directive (mutable by human only)
    impl_path: Path      # Agent-editable implementation
    test_paths: list[Path]  # IMMUTABLE — agent cannot modify
    evals_path: Path     # GTO-style assertions (self-verifying)

    def verify_immutability(self) -> bool:
        """Ensure test files haven't been tampered with."""
        for test_path in self.test_paths:
            if self._agent_modified_this_session(test_path):
                return False
        return True

    def run_evals(self) -> EvalsResult:
        """Execute GTO-style assertions."""
        # evals.json format:
        # {
        #   "assertions": [
        #     {"type": "file_exists", "path": "impl.py"},
        #     {"type": "test_passes", "pattern": "test_*.py"},
        #     {"type": "no_import_errors", "module": "impl"}
        #   ]
        # }
        return gto_assertions.run(self.evals_path)
```

### Hook Integration Points

| Hook | Role | Implementation |
|------|------|----------------|
| `PreToolUse` | Block non-TDD edits to contracted files | `PreToolUse_tdd_gate.py` (extend) |
| `Stop` | Ralph Loop enforcement, Cold Code Review trigger | `Stop_ralph_loop.py` (new) |
| `PostToolUse` | Phase transition logging, eval verification | `PostToolUse_tdd_phase_tracker.py` (extend) |

### Hook Integration Contracts

| Hook | Event | Action | Blocking |
|------|-------|--------|----------|
| `PreToolUse_tdd_gate` | Edit to contracted impl.py | Verify phase allows edit | Yes (if RED/REFACTOR) |
| `Stop_ralph_loop` | Stop event during loop | Check iteration count, log state | No (advisory) |
| `PostToolUse_tdd_phase_tracker` | Any edit to contract files | Update phase state | No |

### Evidence Binding

Each phase transition generates evidence binding:

| Transition | Evidence Hash | Storage |
|------------|---------------|---------|
| RED→GREEN | Test failure output + impl.py hash | `.claude/evidence/tdd95/{contract_id}/` |
| GREEN→REFACTOR | Test pass output + impl.py hash | JSON with timestamp, phase, hashes |
| REFACTOR→COMPLETE | Final test output + coverage metrics | Test output excerpt included |

**Evidence format:**
```json
{
  "timestamp": "2026-03-24T10:30:00Z",
  "phase": "green",
  "impl_hash": "sha256:abc123",
  "test_output_hash": "sha256:def456",
  "test_excerpt": "AssertionError: expected X got Y"
}
```

### State File Schema

```json
{
  "terminal_id": "env_xxx",
  "contracts": {
    "path/to/impl.py": {
      "phase": "green",
      "iterations": 2,
      "last_test_result": "pass",
      "phase_entered_at": "2026-03-24T10:30:00Z"
    }
  }
}
```

### Cold Code Review Dispatch

```python
def dispatch_cold_code_review(contract: ThreeFileContract) -> ColdReviewResult:
    """Dispatch blinded adversarial review after GREEN phase.

    The reviewer is intentionally blinded to the implementation plan,
    evaluating code strictly on merits (like human peer review).
    """
    # Use adversarial-* subagents via Agent tool
    result = Agent(
        subagent_type="adversarial-review",
        prompt=f"""
        Review this implementation for correctness, security, and quality.
        You do NOT have access to the original spec or implementation plan.
        Evaluate strictly on code merits.

        Implementation: {contract.impl_path}
        Tests: {contract.test_paths}

        Focus on: logic errors, edge cases, security vulnerabilities.
        """,
        description="Cold Code Review",
    )
    return ColdReviewResult.from_agent(result)
```

### Cold Code Review Blindness Enforcement

**Blinding contract:**
1. Review subagent receives ONLY: `impl.py` + `test_paths`
2. Review subagent MUST NOT receive: `spec.md`, plan files, previous review notes
3. Prompt explicitly states: "You have NO access to original requirements"

**Verification mechanism:**
- Log file access: confirm only impl.py and test files were read
- Review artifact must NOT contain spec references
- Post-review audit: grep review output for spec.md mentions

---

## Enforcement Tier Configuration

| Phase | Default Tier | Rationale |
|-------|--------------|-----------|
| RED | `enforce` | Must write failing test before implementation |
| GREEN | `enforce` | Must write minimal implementation |
| REFACTOR | `warn` | Optional improvement phase |
| COMPLETE | `none` | No enforcement needed |

**Configuration (settings.json):**

```json
{
  "tdd95_enforcement_tiers": {
    "red": "enforce",
    "green": "enforce",
    "refactor": "warn",
    "complete": "none"
  }
}
```

---

## Alternatives Considered

| Option | Description | Why Rejected |
|--------|-------------|--------------|
| **A: Extend current gate only** | Add state callbacks to TDD-95 | Maintains gate-keeper paradigm; no autonomous execution |
| **B: LLM-dependent Ralph Loop** | Use Claude API for iteration | Violates hook external dependency policy; adds latency |
| **C: External orchestration** | Separate Ralph Wiggum process | Multi-terminal safety complexity; state synchronization issues |
| **D: Full Clean-Room v1 (chosen)** | Four-layer orchestration as described | Matches user's original system + enhancements |

---

## Consequences

**Positive:**
- Autonomous RED→GREEN→REFACTOR execution without LLM dependency
- Ralph Loop iterates via state machine (reliable, no API calls)
- Cold Code Review provides adversarial validation
- Three-File Contract with immutable judge prevents tampering
- GTO-style assertions enable self-verification
- Constitutional tiers allow flexible enforcement
- Multi-terminal safe via existing canonicalize_path + FileLock

**Negative:**
- Higher complexity than current gate-keeper
- More hook coordination required
- Contract directories need cleanup after completion
- Cold Code Review adds latency per TDD cycle

---

## Edge Case Considerations

- **Concurrent access:** FileLock on state files prevents corruption; contract directories scoped by terminal_id
- **Crash recovery:** See detailed protocol below
- **State propagation:** Polling-based with FileLock ensures no stale reads
- **Platform-specific:** Uses existing canonicalize_path for Windows safety
- **Async safety:** Ralph Loop is synchronous polling (no event loop issues)
- **Resource limits:** MAX_ITERATIONS=10 prevents infinite loops; state cleanup on completion

### Crash Recovery Protocol

**State file recovery on Ralph Loop start:**

1. Check for existing `tdd95_{terminal_id}.json`
2. If `phase != NONE`: validate contract files still exist
3. If `GREEN` phase with `iterations > 0`: resume from last test result
4. If `REFACTOR` phase: re-run tests to verify current state

**Corruption detection:**

- State file includes CRC32 checksum in header
- If checksum fails: reset to `NONE` phase, log warning to `tdd95_recovery.log`
- Recovery creates backup: `tdd95_{terminal_id}.json.corrupted`

---

## Success Metrics

| Metric | Target | Measurement Method |
|--------|--------|-------------------|
| Ralph Loop iterations (median) | ≤3 | State file iteration counter |
| Cold Code Review catch rate | ≥20% issues found | Review artifact count vs impl changes |
| Contract immutability violations | 0 | Hash verification on test files |
| Phase transition correctness | 100% | State machine audit log |
| Multi-terminal isolation | 0 cross-talk events | Per-terminal state file analysis |
| Crash recovery success | 100% | Resume-from-crash integration tests |

---

## Implementation Checklist

### Phase 1: Core Infrastructure (MUST) - ✅ COMPLETE (2026-03-24)
- [x] Extend TDD95State → TDDPhaseState with RED/GREEN/REFACTOR
- [x] Implement RalphLoopEngine with FileLock + polling
- [x] Create ThreeFileContract dataclass with immutability check
- [x] Add evals.json support (GTO-style assertions)

### Phase 2: Hook Integration (SHOULD) - ✅ COMPLETE (2026-03-25)
- [x] Extend PreToolUse_tdd_gate.py for contract enforcement → PreToolUse_tdd_contract_gate.py
- [x] Create Stop_ralph_loop.py for autonomous iteration
- [x] Register Stop_ralph_loop.py in Stop_router.py HOOK_SEQUENCE (RALPH_LOOP_ENABLED)
- [x] Register PreToolUse_tdd_contract_gate.py in PreToolUse.py TOOL_HOOKS (Write/Edit arrays)

### Phase 3: Constitutional Compliance (MAY) - ✅ COMPLETE (2026-03-25)
- [x] Add enforcement tier configuration (`enforcement_tiers.py`)
- [x] Implement phase transition logging with evidence binding (`phase_transition_logger.py`)
- [x] Create cleanup task for completed contract directories (`contract_cleanup.py`)

---

## Rollback Strategy

1. **Phase 1 fails:** Revert TDDPhaseState to TDD95State, remove RalphLoopEngine
2. **Phase 2 fails:** Disable new hooks, revert to TDD-95 gate-keeper mode
3. **Phase 3 fails:** Disable enforcement tiers, use all-enforce mode

**Rollback trigger:** If autonomous loop causes >3 terminal state corruptions in 24 hours, disable and investigate.

---

## Next Steps

1. **Phase 1 Implementation:** Extend `tdd95_core.py` with TDDPhaseState
2. **Create RalphLoopEngine:** New module in `hooks/tdd/ralph_loop_engine.py`
3. **Three-File Contract:** Create contract template and validation
4. **Hook Registration:** Register new hooks in `settings.json`
5. **Testing:** Integration tests for multi-terminal isolation

---

## Evidence Sources

- Original Clean-Room TDD: NotebookLM query (chat transcript)
- GTO Assertions: `memory/gto_self_verifying_implementation.md`
- Constitutional Tiers: `hooks/CLAUDE.md` Enforcement Tier System v5.0
- Multi-Terminal Safety: `tdd95_core.py:39-76` canonicalize_path, FileLock
- Autonomy Gate: `hooks/autonomy_gate.py` execution signal detection
- RCA Contract: `hooks/StopHook_rca_contract.py` 8-field structural gate
