# Implementation Plan: Extended Breadcrumb Schema and Verification System

**Generated**: 2026-03-13
**Status**: DRAFT
**Scope**: skill-guard breadcrumb system extension

---

## Problem Statement

The current breadcrumb tracking system in skill-guard lacks:

1. **Workflow-level evidence tracking** - No automatic tool-to-step mapping with evidence collection. TASK-002.5 extends set_breadcrumb() to accept evidence parameter for tracking tool usage

2. **Verification step support** - Cannot distinguish optional verification steps from mandatory execution steps. TASK-001 adds kind/optional fields to workflow_steps, TASK-004 adds check_verification_reminder() function to emit warn-only reminders

3. **Run-level isolation** - Multiple executions of same skill lack unique run identifiers. TASK-002 adds run_id generation (timestamp + UUID) to breadcrumb trail initialization

4. **Structured step metadata** - Workflow steps are simple strings, limiting extensibility. TASK-001 normalizes workflow_steps to list[dict] with id, kind, optional fields

**Impact**: Verification steps in /code skill (audit_quality_checks, trace_manual_verification, done_final_certification) are treated as mandatory. Warn-only behavior without step-level evidence has been hard to act on in practice. The goal is a more comprehensive *reminder + evidence* system, still warn-only, not hard-blocking.

---

## Context Analysis

### Current Breadcrumb Schema (tracker.py:168-177)
```python
trail = {
    "skill": "code",
    "terminal_id": "detected_uuid",
    "workflow_steps": ["step1", "step2", ...],  # Simple strings
    "completed_steps": ["step1"],
    "current_step": "step2",
    "tool_count": 5,
    "initialized_at": timestamp,
    "last_updated": timestamp
}
```

**Limitations**:
- No run_id for multiple executions
- No evidence field for tool usage tracking
- No step metadata (optional, kind)
- completed_steps as list lacks per-step status

### Proposed Schema Extension
```python
trail = {
    "skill": "code",
    "terminal_id": "detected_uuid",
    "run_id": "code_1742368451234_abc123",  # NEW: Timestamp-based UUID
    "steps": {
        "analyze_query_intent": {
            "kind": "execution",
            "optional": False,
            "status": "done",
            "evidence": [{"tool": "AskUserQuestion", "input": {...}, "timestamp": ...}]
        },
        "audit_quality_checks": {
            "kind": "verification",  # NEW: Distinguish verification steps
            "optional": True,        # NEW: Mark as optional
            "status": "pending",
            "evidence": []
        }
    },
    "tool_count": 5,
    "initialized_at": timestamp,
    "last_updated": timestamp
}
```

### Existing Code Leveraged

**PostToolUse_breadcrumb_tracker.py** (lines 96-121):
- Already implements automatic tool-to-step inference
- Uses `infer_step_from_tool_use(tool_name, tool_input)` from `skill_guard.breadcrumb.inference`
- Already calls `set_breadcrumb()` automatically
- **Only needs**: Evidence field added to breadcrumb schema

**PreToolUse_workflow_steps_gate.py** (lines 191-195):
- Enforces first-tool gating for skills with workflow_steps
- Currently expects `_load_workflow_steps()` to return `list[str]`
- **Needs update**: Handle new `list[dict]` format

**StopHook_skill_execution_gate.py**:
- Currently handles bypass detection
- **Needs addition**: Verification reminder function (warn-only, no block)

---

## Existing Implementation Discovery

### Files to Modify (3 total)

1. **P:\packages\skill-guard\src\skill_guard\breadcrumb\tracker.py**
   - Function `_load_workflow_steps()` (line 113): Return `list[dict]` instead of `list[str]`
   - Function `initialize_breadcrumb_trail()` (line 147): Add run_id generation, normalize schema
   - Function `set_breadcrumb()` (line 201): Accept evidence parameter, update steps dict
   - Schema: Add run_id field, convert completed_steps/workflow_steps to steps dict

2. **P:\.claude\hooks\PreToolUse_workflow_steps_gate.py**
   - Lines 191-195: Handle new `list[dict]` format from `_load_workflow_steps()`
   - Backward-compatible: Support both string and dict formats

3. **P:\.claude\hooks\StopHook_skill_execution_gate.py**
   - Add function `check_verification_reminder(breadcrumb_trail)`
   - Emit warn-only reminder for pending verification steps (kind=verification, status!=done)

### SKILL.md Format Update

**P:\.claude\skills\code\SKILL.md** (lines 21-34):
- Current: `workflow_steps: [step1, step2, ...]`
- Change: Tag 3 verification steps with dict format:
```yaml
workflow_steps:
  - analyze_query_intent
  - select_execution_model
  - plan_decomposition
  - execution_and_validation
  - result_delivery
  - id: audit_quality_checks
    kind: verification
    optional: true
  - id: trace_manual_verification
    kind: verification
    optional: true
  - id: done_final_certification
    kind: verification
    optional: true
```

### Backward Compatibility Strategy

**Normalization in _load_workflow_steps()**:
```python
def _load_workflow_steps(skill_name: str) -> list[dict]:
    """Load workflow_steps from SKILL.md frontmatter.

    Returns:
        list[dict] with keys: id, kind (default: execution), optional (default: false)

    Guarantees:
        Every step dict has all three keys (id, kind, optional) with sensible defaults
    """
    steps = []
    # ... load from YAML ...

    DEFAULTS = {"kind": "execution", "optional": False}
    normalized = []
    for step in raw_steps:
        if isinstance(step, str):
            normalized.append({
                "id": step,
                **DEFAULTS
            })
        elif isinstance(step, dict):
            # Merge defaults to handle missing fields
            base = {"id": step.get("id"), **DEFAULTS}
            normalized.append({**base, **step})

    return normalized
```

**PreToolUse gate update**:
```python
workflow_steps = _load_workflow_steps(skill)
step_count = len(workflow_steps)
step_names = [s["id"] if isinstance(s, dict) else s for s in workflow_steps]
```

---

## Test Discovery

### Existing Test Infrastructure

**P:\packages\skill-guard\tests\**:
- Breadcrumb tracking tests exist
- Terminal detection tests exist
- Hook integration tests exist

**Test Coverage Needed**:
1. Schema normalization (string → dict, dict → dict)
2. Backward compatibility (old SKILL.md format still works)
3. Evidence tracking (tool → step mapping with evidence dict)
4. Verification reminder (warn-only, no block)
5. Run ID generation (unique per execution)
6. Multi-terminal isolation (no cross-terminal contamination)

### Test Scenarios

**Schema Normalization**:
```python
def test_load_workflow_steps_string_format():
    """Test backward compatibility with string format."""
    steps = _load_workflow_steps("code")
    assert all(isinstance(s, dict) for s in steps)
    assert all("id" in s and "kind" in s for s in steps)

def test_load_workflow_steps_dict_format():
    """Test new dict format with optional verification steps."""
    steps = _load_workflow_steps("code")
    verification_steps = [s for s in steps if s.get("kind") == "verification"]
    assert len(verification_steps) == 3
    assert all(s.get("optional") for s in verification_steps)
```

**Evidence Tracking**:
```python
def test_set_breadcrumb_with_evidence():
    """Test evidence collection in breadcrumb trail."""
    initialize_breadcrumb_trail("code")
    set_breadcrumb("code", "analyze_query_intent", evidence={
        "tool": "AskUserQuestion",
        "input": {...},
        "timestamp": ...
    })
    trail = get_breadcrumb_trail("code")
    assert trail["steps"]["analyze_query_intent"]["status"] == "done"
    assert len(trail["steps"]["analyze_query_intent"]["evidence"]) > 0
```

**Verification Reminder**:
```python
def test_verification_reminder_warn_only():
    """Test verification reminder doesn't block execution."""
    trail = {
        "steps": {
            "audit_quality_checks": {"kind": "verification", "status": "pending"}
        }
    }
    result = check_verification_reminder(trail)
    assert result["allow"] is True  # Don't block
    assert "reminder" in result
```

---

## Proposed Solution

### Architecture Decision: Extend Existing Breadcrumb System

**Rationale**:
- Reuses 80% of existing code (tracker.py, hooks, terminal detection)
- No migration needed (backward-compatible schema normalization)
- Single directory structure: `P:/.claude/state/breadcrumbs_{terminal_id}/`
- Proven multi-terminal isolation from `verify_session_isolation()`

**Rejected Alternative**: Create parallel `TENANT_ROOT` structure
- Too much duplication
- Migration complexity
- No clear benefit over extension

### Implementation Phases

**Phase 1: Core Schema Extension** (2-3 hours)
- Modify `_load_workflow_steps()` to return `list[dict]`
- Add run_id generation (timestamp + UUID)
- Convert breadcrumb trail to use steps dict instead of completed_steps/workflow_steps lists
- Update `initialize_breadcrumb_trail()` to use new schema

**Phase 2: Evidence Tracking** (1-2 hours)
- Extend `set_breadcrumb()` to accept evidence parameter
- Update steps dict with status and evidence array
- Modify PostToolUse_breadcrumb_tracker.py to pass evidence

**Phase 3: Backward Compatibility** (1 hour)
- Update PreToolUse_workflow_steps_gate.py to handle new format
- Support both string and dict formats in SKILL.md parsing
- Add unit tests for backward compatibility

**Phase 4: Verification Reminder** (1 hour)
- Add `check_verification_reminder()` to StopHook_skill_execution_gate.py
- Filter steps by kind=verification and status!=done
- Emit warn-only reminder (no block)

**Phase 5: SKILL.md Update** (30 minutes)
- Update /code SKILL.md to tag 3 verification steps
- Verify format parses correctly

**Phase 6: Testing and Validation** (1-2 hours)
- Unit tests for all new functions
- Integration tests for hook execution
- Multi-terminal isolation tests
- Performance tests (target: <100ms per breadcrumb operation)

**Total Effort**: 6-9 hours

---

## Implementation Plan

**TASK-001**: Modify _load_workflow_steps() to return list[dict]
- File: `P:\packages\skill-guard\src\skill_guard\breadcrumb\tracker.py`
- Action: Update function at line 113 to normalize workflow_steps (addresses REQ-004: Structured step metadata)
- Acceptance: Returns `list[dict]` with keys: id, kind, optional. String format converts to dict with kind=execution, optional=false. Dict format passes through unchanged.
- Effort: Medium (1-2 hours)
- Prerequisites: None

**TASK-002**: Extend breadcrumb schema with run_id and steps dict
- File: `P:\packages\skill-guard\src\skill_guard\breadcrumb\tracker.py`
- Action: Update `initialize_breadcrumb_trail()` at line 147 (addresses REQ-003: Run-level isolation, REQ-004: Structured step metadata). Generate run_id: `{skill}_{timestamp}_{uuid}`. Replace workflow_steps/completed_steps with steps dict. **Initialize each step explicitly**: For every step ID from `_load_workflow_steps()`, create entry with `kind` and `optional` from SKILL.md, plus `status: "pending"` and `evidence: []`.
- Acceptance: run_id is unique per execution. steps dict contains all workflow steps with explicit initialization (kind, optional, status=pending, evidence=[]). Backward compatibility: old trails still readable.
- Effort: Medium (2-3 hours)
- Prerequisites: TASK-001

**TASK-002.5**: Extend set_breadcrumb() to accept evidence parameter
- File: `P:\packages\skill-guard\src\skill_guard\breadcrumb\tracker.py`
- Action: Update function at line 201 (addresses REQ-001: Workflow-level evidence tracking). Add optional `evidence: dict | None = None` parameter. Update step status in steps dict. Append evidence to step's evidence array.
- Acceptance: Evidence is appended to step's evidence array. Step status updates to "done". Backward compatible: works without evidence parameter.
- Effort: Small (1 hour)
- Prerequisites: TASK-002

**TASK-003**: Update PreToolUse_workflow_steps_gate.py for new format
- File: `P:\.claude\hooks\PreToolUse_workflow_steps_gate.py`
- Action: Modify lines 191-195 to handle `list[dict]`. Extract step names from dict format: `[s["id"] if isinstance(s, dict) else s for s in workflow_steps]`. Display step count from new format.
- Acceptance: Works with new list[dict] format. Backward compatible with old list[str] format. Gate message displays step names correctly.
- Effort: Small (1 hour)
- Prerequisites: TASK-001

**TASK-004**: Add verification reminder to Stop hook
- File: `P:\.claude\hooks\StopHook_skill_execution_gate.py`
- Action: Add `check_verification_reminder()` function (addresses REQ-002: Verification step support). Filter steps by kind=verification, status!=done. Return {"allow": True, "reminder": "..."} for pending verification steps. **Integration**: Call as additional check AFTER bypass detection but BEFORE final response. Reminder text is injected as system reminder (doesn't override skill-first violations or other enforcement). Warn-only: reminder emitted but never blocks execution.
- Acceptance: Verification steps identified correctly. Reminder emitted but doesn't block execution. Works with extended schema. Reminder composes with existing skill-first and bypass checks (additional check, not replacement).
- Effort: Small (1 hour)
- Prerequisites: TASK-002

**TASK-005**: Update /code SKILL.md with verification step tags
- File: `P:\.claude\skills\code\SKILL.md`
- Action: Modify lines 21-34 to tag 3 verification steps. Convert audit_quality_checks to dict format with kind=verification, optional=true. Convert trace_manual_verification to dict format. Convert done_final_certification to dict format.
- Acceptance: All 3 steps tagged as verification. All 3 steps marked optional=true. SKILL.md parses without error.
- Effort: Small (30 minutes)
- Prerequisites: TASK-001

**TASK-006**: Write unit tests for schema changes
- File: `P:\packages\skill-guard\tests/test_breadcrumb_extended.py`
- Action: Create test file with comprehensive coverage. test_load_workflow_steps_string_format(), test_load_workflow_steps_dict_format(), test_run_id_generation(), test_set_breadcrumb_with_evidence(), test_steps_dict_structure().
- Acceptance: All tests pass. Coverage >80% for modified functions.
- Effort: Medium (1-2 hours)
- Prerequisites: TASK-001, TASK-002, TASK-002.5

**TASK-007**: Write integration tests for hooks
- File: `P:\packages\skill-guard\tests/test_breadcrumb_hooks_integration.py`
- Action: Create integration tests for hook execution. test_pretooluse_gate_with_new_format(), test_stop_hook_verification_reminder(), test_posttooluse_evidence_tracking().
- Acceptance: PreToolUse gate blocks when Skill not used first. Stop hook emits reminder but doesn't block. PostToolUse tracks evidence correctly.
- Effort: Medium (1-2 hours)
- Prerequisites: TASK-003, TASK-004

---

## Risks, Success Criteria, Dependencies

### Top Risks

1. **Schema migration breakage**: Old breadcrumb trails may not load with new schema
   - **Mitigation**: Maintain backward compatibility in `get_breadcrumb_trail()`
   - **Fallback**: If trail lacks steps dict, convert from old format on read

2. **Performance regression**: Evidence tracking may slow down breadcrumb operations
   - **Mitigation**: Target <100ms per breadcrumb operation, profile before/after
   - **Acceptable**: User preference is "effectiveness over speed"

3. **Multi-terminal contamination**: New schema may break `verify_session_isolation()`
   - **Mitigation**: Reuse existing terminal_id detection (no changes needed)
   - **Test**: Run multi-terminal tests before deployment

4. **SKILL.md parsing errors**: Dict format may break YAML parsing
   - **Mitigation**: Test with real SKILL.md files before deployment
   - **Fallback**: String format still supported (backward compatible)

### Success Criteria

- [ ] All 3 verification steps in /code tagged as optional
- [ ] Verification reminder emits but doesn't block execution
- [ ] Evidence tracking collects tool usage per step
- [ ] Run IDs are unique per execution
- [ ] Backward compatibility maintained (old SKILL.md format works)
- [ ] All unit tests pass with >80% coverage
- [ ] All integration tests pass
- [ ] Performance target met (<100ms per breadcrumb operation)
- [ ] Multi-terminal isolation verified

### Dependencies

**Required**:
- Existing breadcrumb system (tracker.py, hooks)
- Terminal detection utility (terminal_detection.py)
- Tool inference engine (PostToolUse_breadcrumb_tracker.py)

**Blocking**:
- None (all dependencies exist)

**Optional**:
- Performance profiling (python -m cProfile)
- Multi-terminal test environment (2+ terminal windows)

---

## Rollback Strategy

**If schema migration breaks**:
1. Revert tracker.py to use old schema (workflow_steps/completed_steps lists)
2. Revert PreToolUse_workflow_steps_gate.py to expect list[str]
3. Remove verification reminder from Stop hook
4. Restore /code SKILL.md to string format

**If verification reminder blocks execution**:
1. Add flag to disable verification reminder: `VERIFICATION_REMINDER_ENABLED=false`
2. Or change reminder to log-only (no console output)

**If performance regresses**:
1. Disable evidence tracking: `EVIDENCE_TRACKING_ENABLED=false`
2. Or defer evidence logging to async background task

---

## Appendix: Design Decisions

### Decision 1: Extend Existing Schema vs. Parallel Structure
**Choice**: Extend existing breadcrumb schema
**Rationale**: 80% code reuse, no migration needed, proven multi-terminal isolation
**Trade-off**: More complex schema vs. simpler parallel structure

### Decision 2: Evidence Collection Strategy
**Choice**: Hybrid (automatic inference + explicit override)
**Rationale**: Already implemented in PostToolUse_breadcrumb_tracker.py, minimal changes
**Trade-off**: May miss edge cases vs. comprehensive explicit tracking

### Decision 3: Verification Step Behavior
**Choice**: Warn-only (no block)
**Rationale**: User preference is "warn, don't block"
**Trade-off**: Less enforcement vs. better user experience

### Decision 4: Performance Priority
**Choice**: Effectiveness over speed
**Rationale**: User stated "I care about effectiveness, not speed of revert"
**Trade-off**: Slower operations vs. better evidence collection

### Decision 5: Schema Breaking Changes
**Choice**: Acceptable if ROI positive
**Rationale**: User stated "I'm ok breaking if the ROI is positive"
**Trade-off**: Migration complexity vs. extensibility benefits

---

## Adversarial Review Findings (8-Agent Analysis)

**Total findings**: 48 issues
- **CRITICAL**: 4
- **HIGH**: 16
- **MEDIUM**: 21
- **LOW**: 7

**Adversarial Review Date**: 2026-03-13
**Reviewers**: adversarial-compliance, adversarial-performance, adversarial-quality, adversarial-security, adversarial-testing, adversarial-critic, code-critic, qa-engineer

---

### CRITICAL Priority Findings (4)

#### PERF-001: Evidence Array Unbounded Memory Growth
- **Category**: Performance
- **Severity**: CRITICAL
- **Description**: Evidence tracking appends to array with no size limit, causing unbounded memory growth (5MB+ per skill session)
- **Evidence**: 100 tool calls × 5KB evidence × 10 concurrent skills = 500MB memory growth
- **Recommendation**: Add evidence retention policy (max 10 items per step), prune old entries when limit exceeded
- **Confidence**: 85%

#### PERF-002: Write Amplification - Triple-Write on Every Update
- **Category**: Performance
- **Severity**: CRITICAL
- **Description**: Three disk writes per breadcrumb update (log + cache + JSON snapshot). With evidence, this becomes 21KB I/O per breadcrumb (3.5x increase)
- **Evidence**: Current 3 writes × 2KB = 6KB. With evidence: 3 writes × 7KB = 21KB. 100 calls × 30ms avg = 3 seconds overhead on network drives
- **Recommendation**: Remove redundant JSON snapshot writes. Append-only log is sufficient for crash recovery. Snapshot only periodically (30s) or on skill completion
- **Confidence**: 90%

#### SEC-001: Path Traversal via Malformed skill_name
- **Category**: Security
- **Severity**: CRITICAL
- **Description**: `_get_breadcrumb_file()` only checks for '.' and '..' but doesn't protect against URL-encoded sequences, Unicode homoglyphs, null byte injection, Windows path separators
- **Evidence**: Current check `if "." in skill_name or ".." in skill_name` is incomplete. Allows bypass via %2e%2e%2f, full-width characters, \\\\ on Windows
- **Recommendation**: Replace with comprehensive allowlist validation using regex `^[a-zA-Z0-9_-]+$`, limit to 64 chars
- **Confidence**: 95%

#### SEC-002: Terminal ID Spoofing via Environment Variables
- **Category**: Security
- **Severity**: CRITICAL
- **Description**: Terminal detection relies on environment variables without cryptographic verification. Attackers who can set env vars can spoof terminal IDs and bypass multi-terminal isolation
- **Evidence**: `os.environ.get("CLAUDE_TERMINAL_ID")` read directly without signature verification
- **Recommendation**: Add HMAC signature verification to terminal IDs using `CLAUDE_TERMINAL_SECRET`. Store `terminal_signature` with breadcrumb trail, verify on read
- **Confidence**: 90%

---

### HIGH Priority Findings (16)

#### COMP-001: Multi-Terminal Coordination Violates Solo-Dev Constraints
- **Category**: Compliance
- **Severity**: HIGH
- **Description**: Plan introduces multi-terminal state management complexity that borders on enterprise-grade concurrency patterns
- **Evidence**: Run_id generation, cross-terminal isolation verification, evidence tracking across terminals
- **Recommendation**: Simplify to single-terminal scope or document specific use case requiring multi-terminal. Explicitly justify why this complexity is appropriate for solo dev vs enterprise patterns
- **Confidence**: 85%

#### COMP-002: Schema Breaking Change Violates "Effectiveness Over Speed"
- **Category**: Compliance
- **Severity**: HIGH
- **Description**: Plan proposes fundamental schema change with insufficient backward compatibility detail. TASK-002 acceptance criteria lacks migration implementation
- **Evidence**: "Backward compatibility: old trails still readable" (how? No implementation shown)
- **Recommendation**: Add TASK-002.1: "Implement backward-compatible schema migration in get_breadcrumb_trail()" with acceptance: (1) Old trails auto-convert, (2) Conversion is idempotent, (3) No data loss
- **Confidence**: 90%

#### PERF-003: Schema Migration O(n) Penalty on Every Read
- **Category**: Performance
- **Severity**: HIGH
- **Description**: Backward compatibility converts old trails to new schema on every read via `get_breadcrumb_trail()`, adding O(n) overhead
- **Evidence**: 10 workflow steps × 5 field conversions = 50 operations per read. 100 breadcrumb reads = 5,000 operations = 500ms overhead per session
- **Recommendation**: Implement lazy migration: on first read of old-format trail, immediately convert and rewrite to new format. Subsequent reads skip conversion
- **Confidence**: 80%

#### QUAL-001: Schema Migration Breakage Risk
- **Category**: Quality
- **Severity**: HIGH
- **Description**: Plan claims "maintain backward compatibility" but provides no migration implementation details
- **Evidence**: TASK-002 acceptance says "old trails still readable" but no `migrate_trail_schema()` function shown
- **Recommendation**: Add explicit migration function that detects old schema (workflow_steps/completed_steps lists) and converts to new schema (steps dict)
- **Confidence**: 85%

#### QUAL-002: Missing Evidence Schema Validation
- **Category**: Quality
- **Severity**: HIGH
- **Description**: Evidence array schema has no validation. Evidence objects can contain arbitrary data with no type checking
- **Evidence**: Plan shows evidence dict with 3 fields but no validation. No Pydantic models, no type hints
- **Recommendation**: Define BreadcrumbEvidence dataclass with typed fields (tool, input, timestamp). Add validation in set_breadcrumb()
- **Confidence**: 85%

#### SEC-003: YAML Injection via Malformed SKILL.md
- **Category**: Security
- **Severity**: HIGH
- **Description**: Plan extends workflow_steps to dict format but doesn't validate dict structure, allowing injection of unexpected keys
- **Evidence**: Normalization logic doesn't validate dict has required 'id' field. Allows __proto__, constructor injection
- **Recommendation**: Implement strict schema validation using TypedDict or pydantic. Allowlist keys: id, kind, optional. Reject unexpected keys
- **Confidence**: 75%

#### TEST-001: Missing Schema Migration Failure Testing
- **Category**: Testing
- **Severity**: HIGH
- **Description**: Plan claims backward compatibility but has no tests for schema migration failures
- **Evidence**: "Fallback: If trail lacks steps dict, convert from old format on read" but no test verifies this works
- **Recommendation**: Add test_get_breadcrumb_trail_migrates_old_schema() that creates old-format trail, reads it, verifies conversion to new format
- **Confidence**: 90%

#### TEST-002: No Concurrent Access Testing
- **Category**: Testing
- **Severity**: HIGH
- **Description**: No tests for concurrent evidence tracking when multiple tools used in rapid succession
- **Evidence**: Evidence appended to arrays but no concurrent access tests. Race conditions possible
- **Recommendation**: Add test_concurrent_evidence_tracking_integrity() that simulates 50 rapid tool calls and verifies all evidence captured
- **Confidence**: 85%

#### TEST-003: Missing Performance Regression Tests
- **Category**: Testing
- **Severity**: HIGH
- **Description**: Plan includes <100ms performance target but no benchmarks for evidence tracking overhead
- **Evidence**: test_benchmark.py exists but only tests log replay, not set_breadcrumb() with evidence parameter
- **Recommendation**: Add test_evidence_tracking_performance() that benchmarks with small/large inputs and verifies <100ms target
- **Confidence**: 85%

#### CR-001: Inconsistent set_breadcrumb() Function Signature
- **Category**: Code Review
- **Severity**: HIGH
- **Description**: Plan adds optional evidence parameter but doesn't specify if it's dict, list, or custom type. No schema definition
- **Evidence**: "Add optional evidence: dict | None = None parameter" but no TypedDict or schema shown
- **Recommendation**: Define EvidenceEntry TypedDict with tool, input, timestamp, output_excerpt fields. Update signature with type hints
- **Confidence**: 90%

#### CR-002: Missing Type Hints for Workflow Steps
- **Category**: Code Review
- **Severity**: HIGH
- **Description**: Plan shows _load_workflow_steps() returning list[dict] but doesn't define dict structure as TypedDict
- **Evidence**: Lines 132-154 show dict access with string keys 'id', 'kind', 'optional' without type definitions
- **Recommendation**: Define WorkflowStep TypedDict with id, kind (Literal['execution', 'verification']), optional fields
- **Confidence**: 90%

#### CR-007: Missing TypedDict for Breadcrumb Trail Schema
- **Category**: Code Review
- **Severity**: HIGH
- **Description**: Plan proposes complex breadcrumb schema with run_id, steps dict, step metadata but no TypedDict definitions
- **Evidence**: Lines 44-67 show new schema structure without TypedDict. Leads to incomplete type hints and potential runtime errors
- **Recommendation**: Define BreadcrumbStep and BreadcrumbTrail TypedDicts. Use in function signatures for type safety
- **Confidence**: 90%

#### QA-001: Acceptance Criteria Lack Quantifiable Metrics
- **Category**: QA
- **Severity**: HIGH
- **Description**: Success criteria are not objectively measurable. No baseline metrics or target thresholds
- **Evidence**: "Performance target met (<100ms per breadcrumb operation)" - no baseline, no test environment specified
- **Recommendation**: Convert success criteria to SMART format with baselines: "Reduce breadcrumb latency from Xms to Yms based on pre-implementation baseline"
- **Confidence**: 95%

#### QA-002: No Test Environment Specifications
- **Category**: QA
- **Severity**: HIGH
- **Description**: Plan does not specify test environments, data requirements, or environment setup procedures
- **Evidence**: No "Test Environment" or "Testing Infrastructure" section in plan
- **Recommendation**: Define test environment specs: OS/browser versions, test data sets, environment provisioning (Docker/cloud), isolation requirements
- **Confidence**: 90%

#### QA-004: Rollback Strategy Lacks Verification Procedures
- **Category**: QA
- **Severity**: HIGH
- **Description**: Plan mentions rollback capability but doesn't specify how to verify rollback was successful
- **Evidence**: "If schema migration breaks: Revert tracker.py" - no smoke tests or data integrity checks specified
- **Recommendation**: Add rollback verification protocol: post-rollback smoke tests, data integrity checks, performance regression tests
- **Confidence**: 88%

#### QA-005: No Explicit Definition of Done
- **Category**: QA
- **Severity**: HIGH
- **Description**: Plan does not define what "done" means. Risk of incomplete delivery or scope creep
- **Evidence**: No "Definition of Done" section in plan
- **Recommendation**: Create Definition of Done checklist: code complete, unit tests >80% coverage, integration tests passing, security review complete, performance benchmarks met
- **Confidence**: 92%

---

### Adversarial Critic Meta-Analysis (10 Findings)

#### META-001: RTM Validation Failure Ignored [CRITICAL]
- **Issue**: Plan has BLOCKED status from RTM validation (0% requirement coverage). 4 orphan requirements (REQ-001 through REQ-004) have no task mappings
- **Recommendation**: Map all 4 requirements to tasks before implementing. Each requirement must have corresponding task
- **Confidence**: 95%

#### META-002: Hybrid Logging System Already Implements Evidence Tracking [BLIND SPOT]
- **Issue**: Plan assumes evidence tracking doesn't exist, but `tracker.py:179-198` shows HYBRID LOGGING with AppendOnlyBreadcrumbLog, cache, ledger events
- **Recommendation**: Discovery phase to understand existing hybrid logging before TASK-002.5. May be reinventing functionality
- **Confidence**: 90%

#### META-003: Schema Backward Compatibility Claims Conflict [CONTRADICTION]
- **Issue**: TASK-002 says "backward compatible" but changes workflow_steps/completed_steps lists → steps dict. Breaking change cannot be both
- **Recommendation**: Implement explicit migration logic OR acknowledge breaking change with clear migration path
- **Confidence**: 85%

#### META-004: Over-Engineering Bias - Solving Wrong Problem [BIAS]
- **Issue**: Stated problem: "verification steps treated as mandatory". Solution: comprehensive schema restructuring. Simpler: add optional flag without schema change
- **Recommendation**: Apply lean thinking - verify schema extension is necessary. Consider lightweight alternative
- **Confidence**: 75%

#### META-005: Missing Performance Baseline Measurement [BLIND SPOT]
- **Issue**: Performance target set at "<100ms" without baseline. Current performance unknown, making target unmeasurable
- **Recommendation**: Measure baseline with cProfile before implementation. Set relative target (e.g., "no more than 20% regression")
- **Confidence**: 85%

#### META-008: Missing YAML Parsing Validation [BLIND SPOT]
- **Issue**: Plan converts workflow_steps to list[dict] with optional keys but no validation schema for required fields
- **Recommendation**: Add TASK-007.5 for YAML validation schema using pydantic or jsonschema
- **Confidence**: 80%

#### META-009: Stop Hook Verification Reminder Conflicts with Workflow [CONTRADICTION]
- **Issue**: Reminder fires at Stop hook (after work completed). Verification steps at END of workflow. Creates friction
- **Recommendation**: Emit reminder BEFORE verification steps OR remove entirely
- **Confidence**: 70%

#### META-010: Single-Skill Optimization Bias [BIAS]
- **Issue**: All modifications focused on /code skill. Verification reminders hardcoded, not configurable per skill
- **Recommendation**: Make verification reminder configurable via SKILL.md frontmatter
- **Confidence**: 65%

---

### MEDIUM Priority Findings (21)

*(Key MEDIUM findings - full list of 21 available in review bundle)*

- **COMP-003**: Integration test scenarios missing critical evidence workflows
- **COMP-004**: TASK-005 lists TASK-001 as prerequisite but should require TASK-003
- **COMP-005**: SKILL.md dict format lacks YAML parsing validation tests
- **COMP-006**: Verification reminder warn-only behavior lacks enforcement integration
- **PERF-004**: Cache invalidation storms on multi-terminal contamination
- **PERF-005**: Run ID generation unnecessary overhead
- **PERF-006**: Evidence payload size not limited (1MB+ risk)
- **QUAL-003**: Run ID collision risk (timestamp-based UUID not unique enough)
- **QUAL-004**: Verification reminder has no test coverage for edge cases
- **QUAL-005**: PreToolUse gate assumes workflow_steps returns list[dict]
- **QUAL-006**: No performance baseline for evidence tracking
- **QUAL-007**: SKILL.md YAML parsing assumes success without validation
- **SEC-004**: Evidence tampering via direct file modification
- **SEC-005**: Cross-terminal state leakage via directory enumeration
- **TEST-004**: Verification reminder not tested for blocking execution
- **TEST-005**: Missing regression test for existing breadcrumb functionality
- **TEST-006**: No edge case testing for malformed evidence dict
- **TEST-007**: Missing test for run_id uniqueness across rapid invocations
- **TEST-008**: No test for SKILL.md YAML parsing with dict format
- **CR-003**: No validation for step status transitions
- **CR-004**: Inconsistent terminology: step_id vs step_name
- **CR-005**: set_breadcrumb() doesn't return success/failure indication

---

### LOW Priority Findings (7)

*(Key LOW findings - full list of 7 available in review bundle)*

- **COMP-006**: YAML injection vulnerability (mitigated by safe_load but complex dict structure)
- **PERF-007**: [Additional performance finding]
- **CR-006**: Step normalization logic duplicated
- **CR-008**: No error handling for corrupt breadcrumb trail migration
- **CR-009**: check_verification_reminder() return value inconsistent with hook patterns
- **CR-010**: Terminal detection logic duplicated across files
- **QA-003**: Success criteria not objectively measurable

---

## Required Plan Updates Before Implementation

Based on adversarial review findings, the following MUST be addressed before implementation:

1. **MAP REQUIREMENTS TO TASKS** (META-001, RTM-001):
   - REQ-001 (Workflow-level evidence tracking) → TASK-002.5
   - REQ-002 (Verification step support) → TASK-004
   - REQ-003 (Run-level isolation) → Remove run_id (META-005), use terminal_id only
   - REQ-004 (Structured step metadata) → TASK-001, TASK-002

2. **DISCOVERY PHASE** (META-002):
   - Investigate existing hybrid logging system (AppendOnlyBreadcrumbLog, cache, ledger)
   - Verify if evidence tracking already implemented
   - Avoid reinventing existing functionality

3. **ADD CRITICAL SECURITY FIXES** (SEC-001, SEC-002):
   - Fix path traversal vulnerability in _get_breadcrumb_file()
   - Add HMAC signature verification for terminal IDs

4. **ADD PERFORMANCE BASELINE** (META-005, PERF-002):
   - Measure current breadcrumb operation latency with cProfile
   - Set relative performance target (e.g., "no more than 20% regression")
   - Add performance benchmark tests before implementation

5. **IMPLEMENT SCHEMA MIGRATION** (COMP-002, QUAL-001, META-003):
   - Add TASK-002.1: Implement migrate_trail_schema() function
   - Add conversion logic in get_breadcrumb_trail()
   - Add migration tests

6. **ADD TYPE SAFETY** (CR-001, CR-002, CR-007):
   - Define BreadcrumbEvidence TypedDict
   - Define WorkflowStep TypedDict
   - Define BreadcrumbTrail TypedDict
   - Add type hints to all function signatures

7. **ADD EVIDENCE SIZE LIMITS** (PERF-001, PERF-006):
   - Limit evidence arrays to 10 items per step
   - Limit individual evidence entries to 10KB
   - Truncate or summarize large payloads

8. **REMOVE REDUNDANT WRITES** (PERF-002):
   - Remove JSON snapshot write from set_breadcrumb()
   - Keep append-only log and cache
   - Snapshot only on skill completion or every 30 seconds

9. **ADD TEST SCENARIOS** (TEST-001 through TEST-008):
   - Schema migration failure tests
   - Concurrent access tests
   - Performance regression tests
   - Edge case tests for malformed evidence
   - Run ID uniqueness tests
   - YAML parsing tests

10. **CONSIDER LEANER ALTERNATIVE** (META-004):
    - Evaluate if simpler solution exists: add `optional` flag to existing steps without full schema restructuring
    - Warn-only behavior might not require evidence tracking, run_id, or steps dict

---

## Updated Effort Estimate

**Original Estimate**: 6-9 hours

**Revised Estimate**: 18-24 hours (due to critical fixes, testing, security hardening)

**Breakdown**:
- Core implementation: 6-9 hours (original)
- Security fixes: 2-3 hours (path traversal, terminal ID signatures)
- Schema migration: 2-3 hours (backward compatibility)
- Type safety (TypedDicts): 2 hours
- Testing (expanded): 3-4 hours
- Performance optimization: 2-3 hours (remove redundant writes, add limits)
- Discovery phase: 1 hour (verify existing hybrid logging)

---

## Next Actions

1. Address META-001: Map 4 orphan requirements to tasks
2. Execute META-002: Discovery phase for existing hybrid logging
3. Add critical security fixes (SEC-001, SEC-002)
4. Add TypedDict definitions for type safety
5. Implement schema migration logic (META-003)
6. Add evidence size limits and remove redundant writes
7. Expand test coverage for adversarial findings
8. Re-run verification to confirm BLOCKED status resolved
9. Approve updated plan for implementation
10. Create Claude TaskList items from approved tasks
