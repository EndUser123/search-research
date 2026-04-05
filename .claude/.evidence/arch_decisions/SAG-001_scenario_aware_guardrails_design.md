# Solution Design: Scenario-Aware Guardrails for TRACE and /debugRCA

**Document ID**: SAG-001
**Created**: 2026-03-02
**Status**: Design Review - v2.0
**Version**: 2.0
**Author**: AI Assistant (for external LLM review)
**Revision**: Major restructure — inference-first, lean scope, unified engine

---

## Executive Summary

**Scenario-Aware Guardrails (SAG)** detects cross-scenario lifecycle bugs in automated debugging workflows. Both TRACE and /debugRCA analyze scenarios in isolation, missing bugs that manifest across consecutive invocations (e.g., cleanup code unreachable after early returns).

**Problem**: Early returns (`sys.exit`, `return`, `raise`) can skip cleanup code, causing state leaks across invocations. Neither TRACE nor /debugRCA checks for this.

**Solution**: A single `LifecycleAnalyzer` engine that infers cleanup reachability from AST analysis — no configuration required. Optional ownership contracts add precision where inference is ambiguous.

**Key change from v1.x**: Inference-first design. The analyzer works out of the box by examining code structure. Contracts are an optional enhancement, not a prerequisite.

**Estimated Effort**: 15-25 hours for prototype, 40-60 hours for production-ready

---

## Table of Contents

1. [Problem Statement](#1-problem-statement)
2. [Proposed Solution](#2-proposed-solution)
3. [Technical Architecture](#3-technical-architecture)
4. [Implementation Details](#4-implementation-details)
5. [Acceptance Criteria](#5-acceptance-criteria)
6. [Testing Strategy](#6-testing-strategy)
7. [Risks and Mitigations](#7-risks-and-mitigations)
8. [Alternatives Considered](#8-alternatives-considered)
9. [Rollout Plan](#9-rollout-plan)
10. [Open Questions](#10-open-questions)

---

## 1. Problem Statement

### 1.1 Current Limitations

| Tool | Methodology | Blind Spot |
|------|-------------|------------|
| **TRACE** | State-table driven analysis with 3 scenarios per file | Each scenario analyzed in isolation; misses lifecycle bugs across invocations |
| **/debugRCA** | 5-phase evidence-driven protocol | Symptom-triggered; requires deployment before detecting bugs |

### 1.2 Real-World Example: Artifact Cleanup Bug

**Context**: `PostToolUse_artifact_validator.py` (lines 110-117)

```python
injection_result = check_and_inject_artifact(data)
if injection_result:
    print(json.dumps(injection_result))
    sys.exit(0)        # exits here, skips cleanup

cleanup_stale_artifact(data)  # only runs when NO artifact exists
```

**Bug**: `sys.exit(0)` prevents cleanup from running, causing infinite injection loops.

**Why Both Tools Missed It**:
- **TRACE**: Each scenario worked correctly individually. Cross-scenario lifecycle not traced.
- **/debugRCA**: Symptom-triggered; bug only manifests after deployment during actual usage patterns.

**How Manual Review Caught It**: Human reviewer traced what happens BETWEEN consecutive invocations and noticed cleanup was unreachable.

### 1.3 Root Cause: Scenario Isolation

Both methodologies analyze scenarios in isolation:
- Within-scenario analysis: Excellent at catching logic errors, exception handling, edge cases
- Cross-scenario analysis: Cannot detect state mutations, cleanup violations, or resource lifecycle issues across invocations

**This is a fundamental architectural limitation, not a missing feature.**

---

## 2. Proposed Solution

### 2.1 Design Principles

1. **Inference-first**: The analyzer examines code structure (AST) to detect lifecycle issues without any configuration. No contracts, no YAML, no setup.
2. **Single engine, two entry points**: One `LifecycleAnalyzer` module serves both TRACE (preventive) and /debugRCA (diagnostic).
3. **Contracts are optional**: Ownership contracts add precision for complex cases where inference is ambiguous. They are never required.
4. **Lean scope**: Solve the demonstrated problem (unreachable cleanup after early returns) before expanding to broader lifecycle analysis.

### 2.2 Solution Components

| Component | Purpose |
|-----------|---------|
| **LifecycleAnalyzer** | Unified engine: AST-based early return detection + cleanup reachability checking |
| **TRACE Phase 9** | Entry point: runs LifecycleAnalyzer after normal scenario analysis |
| **/debugRCA Phase 0.5** | Entry point: runs LifecycleAnalyzer before evidence gathering |
| **Ownership Contracts** | Optional: structured metadata for cases where inference needs guidance |

### 2.3 How It Works (Zero-Config)

```
Input: Python source file
  │
  ├─ 1. AST Parse
  │    └─ Extract all functions/methods
  │
  ├─ 2. Early Return Detection
  │    └─ Find sys.exit(), return, raise in each function
  │
  ├─ 3. Cleanup Function Identification
  │    ├─ Pattern matching: *cleanup*, *close*, *dispose*, *release*, *teardown*
  │    ├─ Context managers (with blocks)
  │    ├─ finally blocks
  │    └─ atexit registrations
  │
  ├─ 4. Reachability Analysis
  │    └─ For each early return: is every cleanup function reachable?
  │
  └─ 5. Report
       ├─ Unreachable cleanup → VIOLATION (HIGH)
       ├─ Cleanup in finally/with → OK
       └─ No cleanup functions found → SKIP (nothing to check)
```

### 2.4 How Contracts Add Value (Optional)

Without contracts, the analyzer relies on naming conventions to identify cleanup functions. This works for most cases but can miss:
- Cleanup functions with non-standard names
- Resources that require specific cleanup ordering
- Cross-file cleanup dependencies

Contracts let developers explicitly declare these relationships when inference falls short.

---

## 3. Technical Architecture

### 3.1 LifecycleAnalyzer (Core Engine)

The single engine that powers both TRACE Phase 9 and /debugRCA Phase 0.5.

**Inputs**:
- Source file path (required)
- Ownership contracts (optional, enhances accuracy)
- Analysis mode: `preventive` (TRACE) or `diagnostic` (debugRCA)

**Algorithm**:
```
analyze(file_path, contracts=None, mode="preventive"):
    tree = ast.parse(read(file_path))

    # Step 1: Find all early returns
    early_returns = []
    for node in ast.walk(tree):
        if is_early_return(node):  # sys.exit, return, raise
            early_returns.append(EarlyReturn(
                function=enclosing_function(node),
                exit_kind=classify(node),  # "sys.exit" | "return" | "raise"
                line=node.lineno
            ))

    # Step 2: Find cleanup functions
    if contracts:
        cleanups = extract_from_contracts(contracts)
    else:
        cleanups = infer_cleanups(tree)
        # Pattern: function calls matching *cleanup*, *close*, *dispose*, etc.
        # Pattern: code after early return in same scope
        # Pattern: finally blocks, context managers

    # Step 3: Check reachability
    violations = []
    for er in early_returns:
        for cleanup in cleanups:
            if same_scope(er, cleanup) and not reachable(er, cleanup):
                violations.append(LifecycleViolation(
                    early_return=er,
                    cleanup=cleanup,
                    severity=compute_severity(er, cleanup)
                ))

    return LifecycleReport(early_returns, violations)
```

**Reachability Rules**:
- Cleanup BEFORE early return in same scope → reachable
- Cleanup AFTER early return in same scope → unreachable (VIOLATION)
- Cleanup in `finally` block enclosing early return → reachable
- Cleanup in `with` block's `__exit__` enclosing early return → reachable
- Cleanup registered via `atexit` → reachable (from `sys.exit` only)
- Cleanup in `except` block → reachable only from matching `raise`

### 3.2 Ownership Contract Schema (Optional)

For cases where inference needs explicit guidance:

```yaml
---
scenario:
  name: "happy_path"
  owns:
    - resource: "temp_artifact"
      resource_type: "file"          # file | db_connection | memory_object | lock
      lifetime: "function_scope"     # function_scope | session_scope | global_scope
      cleanup: "cleanup_stale_artifact(data)"
  depends_on:
    - resource: "temp_artifact"
      from_scenario: "previous_invocation"
      required_state: "created"
  ensures:
    - resource: "temp_artifact"
      state: "injected"
  early_returns:
    - function: "validate_and_inject"
      exit_kind: "sys.exit"
      condition: "injection_result exists"
      cleanup_required: true
    # cleanup_reachable is COMPUTED by analyzer, never authored
---
```

**Key design decisions**:
- `cleanup_reachable` is always computed, never authored (humans get this wrong)
- Stable anchors (`function` + `exit_kind`) instead of brittle line numbers
- Structured `depends_on`/`ensures` instead of free-text predicates
- `resource_type` enables type-specific validation rules

### 3.3 TRACE Integration (Phase 9)

**Added after existing Phases 1-8. Runs LifecycleAnalyzer in preventive mode.**

```
TRACE Phase 9: Cross-Scenario Validation

  Inputs:
  - State tables from Phases 1-8
  - Source file
  - Ownership contracts (if present)

  Process:
  1. Run LifecycleAnalyzer(file, contracts, mode="preventive")
  2. If contracts exist: validate pairwise scenario dependencies
     - For each pair (S_prev, S_curr):
       - Check S_curr.depends_on satisfied by S_prev.ensures
       - Validate resource ownership transfers
  3. Generate cross-scenario state table

  Output:
  - Cross-scenario state table with lifecycle status
  - Violations with severity and suggested fixes
```

### 3.4 /debugRCA Integration (Phase 0.5)

**Inserted before existing Phase 1. Runs LifecycleAnalyzer in diagnostic mode.**

```
/debugRCA Phase 0.5: State Lifecycle Analysis

  Inputs:
  - Symptom description
  - Target file(s)

  Process:
  1. Run LifecycleAnalyzer(file, contracts, mode="diagnostic")
  2. If violations found: shortcut to root cause
  3. If no violations: proceed to Phase 1

  Output:
  - Early return table with cleanup status
  - Lifecycle violations (if any)
  - Suggested fixes
```

**Difference from Phase 9**: Diagnostic mode focuses on the symptom's code path first and provides more actionable fix suggestions. Preventive mode checks everything.

---

## 4. Implementation Details

### 4.1 File Structure

```
.claude/
├── skills/
│   ├── trace/
│   │   ├── scripts/
│   │   │   └── lifecycle_analyzer.py   # Unified engine (NEW)
│   │   └── SKILL.md                    # UPDATE (add Phase 9)
│   └── debugRCA/
│       └── SKILL.md                    # UPDATE (add Phase 0.5)
└── hooks/
    └── (no new hooks required)
```

Note: One script file (`lifecycle_analyzer.py`), not three. Both TRACE and /debugRCA import from the same module.

### 4.2 Core Module: `lifecycle_analyzer.py`

```python
"""Unified lifecycle analysis engine for TRACE Phase 9 and /debugRCA Phase 0.5."""

import ast
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

# --- Data Structures ---

@dataclass
class EarlyReturn:
    function: str           # enclosing function name (stable anchor)
    exit_kind: str          # "sys.exit" | "return" | "raise"
    line: int               # for reporting only, not matching
    condition: str = ""     # human-readable condition description

@dataclass
class CleanupFunction:
    name: str               # function/method name
    line: int               # for reporting
    source: str = "inferred"  # "inferred" | "contract" | "finally" | "context_manager"

@dataclass
class LifecycleViolation:
    violation_type: str     # "cleanup_unreachable" | "state_leak" | "contract_breach"
    early_return: EarlyReturn
    cleanup: CleanupFunction
    severity: str           # "HIGH" | "MEDIUM" | "LOW"
    location: str           # "file:line"
    description: str
    suggested_fix: str

@dataclass
class LifecycleReport:
    file_path: str
    early_returns: list[EarlyReturn] = field(default_factory=list)
    cleanups: list[CleanupFunction] = field(default_factory=list)
    violations: list[LifecycleViolation] = field(default_factory=list)

    @property
    def has_violations(self) -> bool:
        return len(self.violations) > 0

# --- Public API ---

def analyze(
    file_path: Path,
    contracts: Optional[list] = None,
    mode: str = "preventive"
) -> LifecycleReport:
    """Analyze a file for lifecycle violations.

    Args:
        file_path: Python source file to analyze
        contracts: Optional ownership contracts (enhances accuracy)
        mode: "preventive" (TRACE) or "diagnostic" (debugRCA)

    Returns:
        LifecycleReport with early returns, cleanups, and violations
    """
    ...

def format_report(report: LifecycleReport, mode: str = "preventive") -> str:
    """Format a LifecycleReport as markdown for TRACE or /debugRCA output."""
    ...
```

### 4.3 Cleanup Inference Heuristics

The analyzer identifies cleanup functions without contracts using these patterns:

| Pattern | Examples | Confidence |
|---------|----------|------------|
| Name contains cleanup keyword | `cleanup_*`, `close_*`, `dispose_*`, `release_*`, `teardown_*` | HIGH |
| Code after early return in same scope | Any function call after `sys.exit()` / `return` | HIGH (it's unreachable) |
| `finally` block | `try: ... finally: cleanup()` | HIGH (always runs) |
| Context manager `__exit__` | `with open(...) as f:` | HIGH (always runs) |
| `atexit.register()` | `atexit.register(cleanup)` | MEDIUM (runs on `sys.exit`, not on `os._exit`) |
| Destructor | `__del__` method | LOW (GC timing uncertain) |

### 4.4 Suppression Mechanisms

**Inline suppression** (for individual lines):
```python
sys.exit(0)  # sag: ignore[cleanup-unreachable] - cleanup handled by parent process
```

**File-level whitelist** (`.sag-whitelist.yaml` in project root):
```yaml
whitelist:
  - pattern: "logger.*"
    reason: "Logging handlers flush on process exit"
  - pattern: "temp_file.*"
    reason: "OS handles temp file cleanup on process exit"
```

---

## 5. Acceptance Criteria

### 5.1 Functional Requirements

| ID | Requirement | Test | Priority |
|----|-------------|------|----------|
| FR-1 | Analyzer detects unreachable cleanup after `sys.exit()` | Artifact cleanup bug test case | P0 |
| FR-2 | Analyzer recognizes `finally`/`with` as valid cleanup | No false positive on properly guarded code | P0 |
| FR-3 | TRACE Phase 9 runs analyzer and includes results | End-to-end TRACE run produces Phase 9 output | P0 |
| FR-4 | /debugRCA Phase 0.5 runs analyzer and shortcuts to root cause | End-to-end /debugRCA with lifecycle bug | P1 |
| FR-5 | Zero-config mode works without contracts | Analyzer produces correct results on plain Python files | P0 |
| FR-6 | Contracts enhance accuracy when provided | Contract-guided analysis has fewer false positives | P2 |
| FR-7 | Suppression comments prevent false positives | `# sag: ignore` suppresses specific violations | P1 |

### 5.2 Non-Functional Requirements

| ID | Requirement | Metric | Priority |
|----|-------------|--------|----------|
| NFR-1 | Performance | Phase 9 adds < 2 seconds per file | P1 |
| NFR-2 | False positive rate | < 15% without contracts, < 5% with contracts | P1 |
| NFR-3 | Backward compatibility | Existing TRACE/debugRCA work unchanged without Phase 9/0.5 | P0 |

---

## 6. Testing Strategy

### 6.1 Unit Tests

| Component | Key Scenarios |
|-----------|---------------|
| Early return detection | `sys.exit()`, bare `return`, `raise Exception()`, nested in `if`/`try`/`with` |
| Cleanup inference | Naming patterns, `finally`, context managers, `atexit`, `__del__` |
| Reachability analysis | Before/after early return, in `finally`, in `with`, in `except` |
| Suppression | Inline `# sag: ignore`, whitelist file |

### 6.2 Regression Tests

**Real-world bugs**:
- Artifact cleanup bug (`PostToolUse_artifact_validator.py:113`) — must detect

**Synthetic edge cases**:
- Nested early returns (`if` inside `try` inside `with`)
- Cleanup in `finally` block (should NOT flag as violation)
- Cleanup via context manager (should NOT flag as violation)
- Multiple resources with different lifetimes
- `raise` from inside `except` blocks
- `sys.exit()` inside `atexit`-registered function (recursive cleanup)

**Expected false positives** (to validate suppression):
- Logger cleanup (not required — handlers flush on exit)
- Temp files (OS cleanup sufficient)
- DB cursors managed by connection pool

### 6.3 Integration Tests

| Test | Expected Outcome |
|------|------------------|
| TRACE full run with Phase 9 | Phase 9 output appended to report |
| /debugRCA with lifecycle bug | Phase 0.5 shortcuts to root cause |
| TRACE on clean code | Phase 9 reports no violations |
| /debugRCA on non-lifecycle bug | Phase 0.5 finds nothing, proceeds to Phase 1 |

---

## 7. Risks and Mitigations

### 7.1 Risks

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| False positives from naming heuristics | Medium | Medium | Start with HIGH-confidence patterns only; add suppression mechanism |
| Missed cleanups with non-standard names | Low | Medium | Contracts fill the gap for non-standard cases |
| AST analysis doesn't handle dynamic dispatch | Low | Low | Out of scope for v1; document as known limitation |
| Performance on large files | Low | Low | AST parsing is fast; set 5-second timeout per file |

### 7.2 False Positive Management

**Strategy**: Start strict, widen carefully.

1. **Phase 1** (prototype): Only flag `cleanup_unreachable` from `sys.exit()` — the highest-confidence violation
2. **Phase 2** (production): Add `return` and `raise` patterns with slightly lower confidence
3. **Phase 3** (refinement): Tune based on real-world false positive data

**Suppression**: Two mechanisms (inline comment and whitelist file) ensure users can quickly silence false positives without waiting for analyzer updates.

### 7.3 Rollback Plan

**Immediate disable**:
```bash
export SAG_DISABLED=true  # Disables Phase 9 and Phase 0.5
```

**Feature flags** (`.claude/settings.json`):
```json
{
  "trace": { "enable_phase_9": true },
  "debugRCA": { "enable_phase_0_5": true }
}
```

**Safe to remove**: SAG adds no runtime dependencies. Disabling it returns TRACE and /debugRCA to their original behavior. Contract files (`.sag-whitelist.yaml`) are inert metadata — safe to delete.

---

## 8. Alternatives Considered

### 8.1 Heavy Contract-First Design (v1.x of this document)

**Description**: Required YAML ownership contracts before analysis could run.

**Why rejected**: Creates a synchronization problem (contracts drift from code), high adoption barrier (developers must learn schema before getting value), and the motivating bug is detectable without contracts.

### 8.2 Hybrid Anomaly Detection

**Description**: Unified telemetry layer aggregating data across all systems.

**Why rejected**: Requires always-on monitoring infrastructure. Reactive (detects after deployment) vs. preventive.

### 8.3 TTL-Based Cleanup ("Kitchen Timer")

**Description**: Auto-reclaim resources after timeout.

**Why rejected**: Addresses symptoms, not root cause. Arbitrary timeouts may be wrong.

### 8.4 Chosen: Inference-First with Optional Contracts

**Why selected**:
- Zero-config: works immediately on any Python file
- Catches the demonstrated bug without setup
- Contracts available for precision when needed
- Single engine, minimal code, easy to maintain
- Preventive AND diagnostic (works before and after deployment)

---

## 9. Rollout Plan

### 9.1 Phase 1: Prototype (1-2 weeks)

**Goal**: Validate the approach with minimal code.

**Scope**:
- Implement `lifecycle_analyzer.py` (~200-300 lines)
- AST-based early return detection
- Pattern-matching cleanup inference (naming conventions only)
- Basic reachability check (before/after in same scope)
- Test on artifact cleanup bug

**Success criteria**:
- Detects artifact cleanup bug
- Generates correct suggested fix
- No false positives on 5+ clean files
- Runs in < 2 seconds per file

**Deliverables**:
- Working `lifecycle_analyzer.py`
- Test results on artifact cleanup bug
- 5+ test cases

### 9.2 Phase 2: Production (3-4 weeks)

**Goal**: Full integration with TRACE and /debugRCA.

**Scope**:
- Add `finally`/`with`/`atexit` recognition
- Integrate as TRACE Phase 9
- Integrate as /debugRCA Phase 0.5
- Add suppression mechanisms (`# sag: ignore`, whitelist file)
- Expand test corpus to 15+ cases
- Optional: contract schema support

**Success criteria**:
- Detection rate > 90% on test corpus
- False positive rate < 15%
- All integration tests passing
- Documentation complete

**Deliverables**:
- Production `lifecycle_analyzer.py`
- Updated TRACE and /debugRCA SKILL.md files
- Test suite
- Usage documentation

### 9.3 Phase 3: Refinement (2-3 weeks)

**Goal**: Tune based on real usage.

**Scope**:
- Collect false positive data from real analysis runs
- Tune detection heuristics
- Add contract support if inference proves insufficient
- Decide on default enablement

**Success criteria**:
- False positive rate < 10% with tuning
- No backward compatibility issues
- Positive results on real codebase

### 9.4 Phase 4: Default Enablement (1 week)

- Remove opt-in flag
- Update documentation
- Add kill-switch for emergency rollback

---

## 10. Open Questions

### 10.1 Technical

1. **Cleanup naming conventions**: Are `*cleanup*`, `*close*`, `*dispose*`, `*release*`, `*teardown*` sufficient, or do we need more patterns?
   - **Approach**: Start with these, expand based on false negatives in real usage.

2. **Cross-file analysis**: What about cleanup defined in a different file?
   - **Approach**: Out of scope for v1. Single-file analysis only. Contracts can bridge cross-file gaps later.

3. **`os._exit()` vs `sys.exit()`**: `os._exit()` skips `atexit` and `finally`. Should we treat it differently?
   - **Approach**: Yes — `os._exit()` gets highest severity since no cleanup mechanism can catch it.

### 10.2 Operational

1. **Default on or off?**: Should Phase 9/0.5 be enabled by default from the start?
   - **Approach**: Opt-in during Phases 1-3, default-on in Phase 4.

2. **Performance budget**: What's acceptable overhead?
   - **Approach**: < 2 seconds per file for Phase 9. If exceeded, skip and log warning.

---

## Appendix A: Example Output

### A.1 TRACE Phase 9 Output

```markdown
## Phase 9: Cross-Scenario Validation

**File**: PostToolUse_artifact_validator.py

| Early Return | Type | Cleanup Required | Reachable? | Status |
|-------------|------|------------------|------------|--------|
| validate_and_inject:113 | sys.exit(0) | cleanup_stale_artifact(data) | NO | BUG |

**VIOLATION**: cleanup_stale_artifact(data) unreachable from sys.exit(0)
at validate_and_inject (line 113)

**Suggested Fix**:
  if injection_result:
      print(json.dumps(injection_result))
      cleanup_stale_artifact(data)  # ADD: cleanup before exit
      sys.exit(0)

**Result**: FAIL (1 lifecycle violation)
```

### A.2 /debugRCA Phase 0.5 Output

```markdown
## Phase 0.5: State Lifecycle Analysis

**File**: PostToolUse_artifact_validator.py
**Symptom**: Infinite artifact injection loops

**Early Returns Found**: 1
| Location | Type | Cleanup | Reachable? | Status |
|----------|------|---------|------------|--------|
| validate_and_inject:113 | sys.exit(0) | cleanup_stale_artifact | NO | BUG |

**Root Cause**: cleanup_stale_artifact(data) unreachable from sys.exit(0).
Stale artifacts persist across invocations, causing infinite injection loops.

**Suggested Fix**:
  # Add cleanup before early exit:
  if injection_result:
      print(json.dumps(injection_result))
      cleanup_stale_artifact(data)
      sys.exit(0)

**Confidence**: HIGH (cleanup function exists but is unreachable from early return)

Proceeding to Phase 1 skipped — root cause identified.
```

---

## Appendix B: Glossary

| Term | Definition |
|------|------------|
| **Cross-scenario bug** | A bug that manifests across multiple invocations rather than within a single scenario |
| **Early return** | Any exit point that terminates execution before reaching the end (`sys.exit`, `return`, `raise`) |
| **Lifecycle violation** | Cleanup code unreachable from an early return path |
| **Ownership contract** | Optional metadata declaring resource ownership and cleanup requirements |
| **Cleanup inference** | Automatic identification of cleanup functions from naming patterns and code structure |

---

## Document Metadata

**Version History**:
- v2.0 (2026-03-02): **Major restructure**
  - Inference-first design: analyzer works without contracts (zero-config)
  - Unified engine: single `LifecycleAnalyzer` serves both TRACE and /debugRCA
  - Removed contract-first requirement (contracts now optional enhancement)
  - Reduced scope: solve demonstrated problem first, expand later
  - Reduced effort: 15-25h prototype (was 40-60h), 40-60h production (was 120-160h)
  - Eliminated duplicate appendix sections from v1.0/v1.1 merge
  - Consolidated duplicated subsections (Performance, Adoption in Section 7)
  - Simplified file structure: one module instead of three
- v1.1 (2026-03-02): Multi-LLM review feedback incorporated
- v1.0 (2026-03-02): Initial design document

**Key Changes v1.1 → v2.0**:

| Aspect | v1.1 | v2.0 |
|--------|------|------|
| Contracts | Required for analysis | Optional enhancement |
| Engine | Separate Phase 9 + Phase 0.5 implementations | Single LifecycleAnalyzer |
| Setup | YAML contracts must be authored | Zero-config (AST inference) |
| File count | 3 new Python files + schema | 1 new Python file |
| Effort estimate | 120-160 hours total | 40-60 hours total |
| False positive mgmt | Whitelist file only | Inline suppression + whitelist |
| Scope | Broad lifecycle analysis | Focused: early return → unreachable cleanup |

**Next Steps**:
1. Begin Phase 1 (Prototype) — implement `lifecycle_analyzer.py`
2. Test on artifact cleanup bug
3. Expand to 5+ real codebase files for false positive calibration
