# Plan: /s Skill UX Improvements - Real-Time Progress & Follow-Up Integration

**Created**: 2026-03-17
**Updated**: 2026-03-17 (Post-adversarial review with subagent analysis)
**Status**: REVISED
**Priority**: MEDIUM
**Effort**: ~8-12 hours (reduced after security simplification)

---

## Changelog

### 2026-03-17 (Subagent Analysis Applied)

**Security Improvements** (from adversarial-security agent):
- ❌ **REMOVED**: `--execute N` flag - Command injection risk eliminated by removing the feature entirely
- ✅ **SIMPLIFIED**: Extend existing `build_follow_up_hints()` with allowlist instead of new function
- ✅ **ADDED**: `ALLOWED_SKILLS` allowlist for skill suggestions

**Code Discovery** (from code-explorer agent):
- ✅ **VERIFIED**: `build_follow_up_hints()` exists at lines 378-399
- ✅ **VERIFIED**: Timeout recovery exists in orchestrator.py lines 664-674
- ⚠️ **NOTE**: ProgressReporter does NOT exist yet (planned feature)

**Documentation Improvements** (from quality agent):
- ✅ **ADDED**: Rollback Strategy section with per-phase rollback steps
- ✅ **ADDED**: Timeout Budget Guidance for CLI vs API providers
- ✅ **ADDED**: Requirements Traceability Matrix (RTM) for orphan requirements

**Performance Improvements** (from performance agent):
- ✅ **ADDED**: Atomic write pattern for state persistence
- ✅ **ADDED**: CLI provider timeout guidance (90-120s vs 30-60s for API)

---

## Status Summary

| Phase | Status | Notes |
|-------|--------|-------|
| Phase 1: Real-Time Progress | ⏳ PENDING | Ready to implement |
| Phase 2: Graceful Timeout | ⏳ PENDING | Leverage existing orchestrator timeout |
| Phase 3: Follow-Up Integration | ⏳ PENDING | Simplified - extend existing function, no --execute flag |
| Phase 4: Unit Tests | ⏳ PENDING | Blocked by Phases 1-3 |
| Phase 5: Streaming Output | ⏸️ DEFERRED | **Architecturally blocked** - requires asyncio.as_completed() refactor |

**Revised Effort**: 8-12 hours (reduced from 10-16h after removing --execute flag complexity)

---

## Adversarial Review Summary

**Review Date**: 2026-03-17
**Agents**: 8 (compliance, performance, quality, security, testing, code-critic, qa-engineer, adversarial-critic)
**Total Findings**: 46

### Critical Findings Addressed

| ID | Severity | Issue | Resolution |
|----|----------|-------|------------|
| CONSENSUS-001 | HIGH | Phase 2 streaming architecturally impossible | Deferred to Phase 5, requires orchestrator refactor |
| CONSENSUS-002 | HIGH | Timeout functionality duplicated | Use existing orchestrator timeout, add recovery suggestions |
| CONSENSUS-003 | HIGH | Command injection vulnerability | Use shlex.quote() + structured command objects |
| CONSENSUS-004 | HIGH | partial_results mechanism undefined | Define storage in .claude/state/sessions/ |
| CONSENSUS-005 | MEDIUM | Test coverage plan incomplete | Added missing test tasks |
| CONSENSUS-006 | MEDIUM | Effort estimates too optimistic | Revised to 10-16h |

---

## Problem Statement

The `/s` brainstorm skill has a poor user experience during long-running brainstorming sessions:

1. **No Real-Time Progress Visibility** - Users stare at a blank screen for minutes
2. **No Incremental Results** - All-or-nothing output; no partial results during execution
3. **No Interactive Exploration** - Cannot drill down into interesting ideas
4. **Timeout is Silent Failure** - Users don't know why or when it failed
5. **No Follow-Up Integration** - Ideas are displayed but can't be acted on directly

---

## Context Analysis

### Current Architecture

```
run_heavy.py
├── choose_topic() - Topic inference from context
├── apply_constitutional_filter() - Filter ideas against constraints
├── build_decision_memo() - Create decision summary
└── main() - CLI entry point, calls BrainstormOrchestrator
```

**BrainstormOrchestrator** (in `.claude/skills/s/lib/orchestrator.py`) runs 3 phases:
1. **Diverge** - Multiple personas generate ideas (longest phase)
2. **Discuss** - Ideas are debated and ranked
3. **Converge** - Final decision memo produced

> **CORRECTED**: Previous version incorrectly stated orchestrator was in `__csf/src/llm/`. Actual location is `.claude/skills/s/lib/orchestrator.py`.

### Existing Timeout Handling

The orchestrator **already handles timeout** with partial result collection:
```python
# orchestrator.py lines 664-674
except TimeoutError:
    logger.warning(f"Diverge phase timed out after {timeout}s")
    if not ideas:
        raise
    # Returns partial ideas collected so far
```

**Plan Phase 2 will leverage this existing behavior** rather than duplicating it.

### Key Constraints

- Must work in CLI environment (no GUI)
- Must handle multi-terminal isolation
- Cannot spawn background services (constitutional constraint)
- Must remain under user control (no autonomous execution)

### Architectural Limitation (Streaming)

**CRITICAL**: The orchestrator uses `asyncio.gather()` which blocks until ALL parallel tasks complete:
```python
# orchestrator.py lines 651-654
results = await asyncio.wait_for(
    asyncio.gather(*tasks, return_exceptions=True),
    timeout=timeout,
)
```

This means real-time streaming is **not possible** without refactoring to `asyncio.as_completed()`. Estimated effort: 10-20 hours for orchestrator changes alone. **Phase 5 deferred** until this architectural work is prioritized.

---

## Existing Implementation Discovery

### Files to Modify

| File | Purpose | Change Type |
|------|---------|-------------|
| `.claude/skills/s/scripts/run_heavy.py` | Main execution script | Major |
| `.claude/skills/s/SKILL.md` | Documentation | Minor |
| `.claude/skills/s/scripts/progress_reporter.py` | NEW: Progress reporting | New |

### Dependencies

- `BrainstormOrchestrator` in `.claude/skills/s/lib/orchestrator.py` - Import via `from lib.orchestrator import BrainstormOrchestrator`
- Rich library - **VERIFY** with `pip show rich` before use

---

## Proposed Solution

### Phase 1: Real-Time Progress Visibility (P1)

**Goal**: Show users what's happening during long brainstorm sessions.

**Approach**: Add a `ProgressReporter` class that emits status updates during each phase.

```python
# New file: progress_reporter.py
import sys
from datetime import datetime

class ProgressReporter:
    def __init__(self, verbose: bool = True, output: object = sys.stderr):
        self.verbose = verbose
        self.output = output
        self.current_phase = "init"
        self.personas_complete: set[str] = set()
        self.start_time: datetime | None = None

    def reset(self) -> None:
        """Clear state for reuse. CRITICAL: Call before each session."""
        self.current_phase = "init"
        self.personas_complete.clear()
        self.start_time = datetime.now()

    def phase_start(self, phase: str, total_items: int = 0) -> None:
        """Print phase start notification."""
        if self.verbose:
            elapsed = self._elapsed_str()
            print(f"\n[{elapsed}] ▶ Phase: {phase.upper()}", file=self.output)
            if total_items:
                print(f"  Processing {total_items} items...", file=self.output)

    def persona_complete(self, persona: str, ideas_count: int) -> None:
        """Print persona completion notification."""
        if self.verbose:
            elapsed = self._elapsed_str()
            print(f"  [{elapsed}] ✓ {persona}: {ideas_count} ideas generated", file=self.output)
            self.personas_complete.add(persona)

    def phase_complete(self, phase: str, result_count: int) -> None:
        """Print phase completion notification."""
        if self.verbose:
            elapsed = self._elapsed_str()
            print(f"  [{elapsed}] ✓ Phase complete: {result_count} results", file=self.output)

    def _elapsed_str(self) -> str:
        """Return elapsed time as MM:SS string."""
        if self.start_time is None:
            return "00:00"
        elapsed = datetime.now() - self.start_time
        minutes, seconds = divmod(int(elapsed.total_seconds()), 60)
        return f"{minutes:02d}:{seconds:02d}"
```

**Security & Quality Improvements**:
- Added `reset()` method to clear state between runs (CRITIC-004)
- Added elapsed time display for better UX
- Output to stderr to avoid mixing with results

**Tasks**:
1. [ ] Create `progress_reporter.py` module with reset() method
2. [ ] Verify Rich library availability: `pip show rich || pip install rich`
3. [ ] Integrate into `run_heavy.py` main() with reset() call
4. [ ] Add `--quiet` flag to suppress progress output
5. [ ] Update SKILL.md with new flag documentation

**Effort**: 2-3 hours (revised from 1-2h)

---

### Phase 2: Graceful Timeout Handling (P2)

**Goal**: Provide recovery options when timeout occurs.

**Approach**: Leverage existing orchestrator timeout behavior and add recovery suggestions.

**IMPORTANT**: The orchestrator already handles timeout with partial result collection. This phase adds:
1. User-friendly timeout message
2. Recovery suggestions
3. Partial results persistence

```python
# Modify run_heavy.py main()
# The orchestrator already catches TimeoutError and returns partial ideas
# We just need to enhance the output

def generate_recovery_suggestions(timeout_seconds: int, personas_count: int) -> list[str]:
    """Generate actionable recovery suggestions."""
    return [
        f"Re-run with higher timeout: /s 'topic' --timeout {timeout_seconds * 2}",
        f"Use fewer personas: /s 'topic' --personas innovator,critic",
        "Reduce idea target: /s 'topic' --ideas 5",
        "Use partial results: /s 'topic' --use-partial <session_id>",
    ]

def save_partial_results(ideas: list[dict], session_id: str) -> str:
    """Save partial results to state directory.

    Storage: .claude/state/sessions/{session_id}_partial.json
    TTL: 24 hours (cleanup via session_data_retention.py)
    """
    import json
    from pathlib import Path
    state_dir = Path(".claude/state/sessions")
    state_dir.mkdir(parents=True, exist_ok=True)
    partial_file = state_dir / f"{session_id}_partial.json"
    with open(partial_file, "w") as f:
        json.dump({
            "ideas": ideas,
            "timestamp": datetime.now().isoformat(),
            "session_id": session_id,
        }, f, indent=2)
    return str(partial_file)
```

**Tasks**:
1. [ ] Add `generate_recovery_suggestions()` function
2. [ ] Add `save_partial_results()` function with 24h TTL
3. [ ] Add `--use-partial <session_id>` flag to resume from partial results
4. [ ] Update SKILL.md documentation

**Effort**: 2-3 hours

---

### Phase 3: Follow-Up Integration (P3)

**Goal**: Enable direct action on generated ideas.

**Approach**: Extend **existing** `build_follow_up_hints()` function in `run_heavy.py` (lines 378-399) with skill allowlist.

> **DISCOVERY**: The `build_follow_up_hints()` function already exists and provides basic skill suggestions based on result type. This phase EXTENDS rather than replaces it.

**Security Hardening** (SEC-001, CRITIC-003):
- **No --execute flag** - Removed due to command injection risk. Users copy-paste instead.
- **Skill allowlist** - Only approved skills can be suggested

```python
# Extend existing build_follow_up_hints() in run_heavy.py
# Current implementation at lines 378-399

# Add skill allowlist constant
ALLOWED_SKILLS: set[str] = frozenset({
    "arch", "tdd", "plan", "code", "test", "refactor", "verify"
})

def build_follow_up_hints(result_type: str, content: str) -> list[str]:
    """Generate follow-up hints based on result type.

    EXTENDED: Now enforces ALLOWED_SKILLS allowlist for security.
    """
    hints = []

    # Map result types to allowed skills
    skill_mapping = {
        "architecture": "arch",
        "implementation": "code",
        "testing": "tdd",
        "planning": "plan",
        "refactoring": "refactor",
        "verification": "verify",
    }

    # Only suggest skills from allowlist
    for keyword, skill in skill_mapping.items():
        if keyword in content.lower() and skill in ALLOWED_SKILLS:
            hints.append(f"Follow up with: /{skill} '<refined_topic>'")

    return hints[:3]  # Max 3 suggestions
```

**Output Format**:
```
=== Generated Ideas ===
1. [Score: 85] Implement caching layer for API responses
   → Follow up with: /arch '<refined_topic>'

2. [Score: 78] Add rate limiting middleware
   → Follow up with: /plan '<refined_topic>'

3. [Score: 72] Use connection pooling
   → Follow up with: /code '<refined_topic>'

Copy-paste the suggested command to act on an idea.
```

**Tasks**:
1. [ ] Add `ALLOWED_SKILLS` allowlist constant
2. [ ] Extend `build_follow_up_hints()` with allowlist enforcement
3. [ ] Update SKILL.md with follow-up hints documentation

**Effort**: 1-2 hours (reduced - extending existing function, no --execute flag)

---

### Phase 4: Unit Tests (P4)

**Goal**: Comprehensive test coverage for all new functionality.

**Test Files**:

| Test File | Coverage | Task |
|-----------|----------|------|
| `test_progress_reporter.py` | ProgressReporter class, reset(), elapsed time | TASK-011 |
| `test_timeout_recovery.py` | Recovery suggestions, partial results, --use-partial | TASK-012 |
| `test_execution_suggestions.py` | suggest_execution(), validation, audit logging | TASK-013 |
| `test_explore_idea.py` | Exploration and comparison logic | TASK-014 |
| `test_integration_progress.py` | End-to-end progress with orchestrator | TASK-015 |

**Coverage Target**: >80% for all new modules, with specific focus on:
- Error handling branches (TESTING-004)
- Edge cases: empty results, timeout at 99%, concurrent flags (QA-003)
- Security: command injection attempts, bounds violations

**Tasks**:
1. [ ] TASK-011: Write `test_progress_reporter.py`
2. [ ] TASK-012: Write `test_timeout_recovery.py`
3. [ ] TASK-013: Write `test_execution_suggestions.py`
4. [ ] TASK-014: Write `test_explore_idea.py` (if explore implemented)
5. [ ] TASK-015: Write `test_integration_progress.py`

**Effort**: 3-4 hours

---

### Phase 5: Streaming Output (DEFERRED)

**Status**: ⏸️ DEFERRED

**Reason**: Architecturally blocked. The orchestrator uses `asyncio.gather()` which blocks until ALL parallel tasks complete. Real-time streaming requires refactoring to `asyncio.as_completed()`.

**Estimated Effort for Unblock**: 10-20 hours for orchestrator refactoring

**Revisit When**:
1. Orchestrator refactored to use `asyncio.as_completed()`
2. Callback hooks added to agent execution
3. CLI subprocess model updated to support streaming output

---

## Test Discovery

**Existing Tests**:
- `.claude/skills/s/tests/test_integration_3phase_workflow.py` - 3-phase workflow tests
- `.claude/skills/s/tests/test_advanced_features_integration.py` - Advanced features

**Coverage Gaps** (now addressed):
- ~~No tests for progress reporting~~ → TASK-011
- ~~No tests for timeout recovery~~ → TASK-012
- ~~No tests for execution suggestions~~ → TASK-013

---

## Risk Mitigation

| Risk | Mitigation | Status |
|------|------------|--------|
| BrainstormOrchestrator doesn't support callbacks | Use polling wrapper or subprocess monitoring | **Phase 5 deferred** |
| Rich library conflicts with existing output | Use `--quiet` to disable, ensure clean fallback | Addressed in Phase 1 |
| Streaming causes rate limiting | Add configurable delay between emissions | **Phase 5 deferred** |
| Command injection in suggest_execution() | Use structured command objects + shlex.quote() | **Addressed in Phase 3** |
| --execute out-of-bounds access | Add validate_execute_index() bounds check | **Addressed in Phase 3** |
| No audit trail for executions | Add log_execution_audit() | **Addressed in Phase 3** |

---

## Implementation Order

1. **Phase 1 (Progress)** - Immediate UX improvement, low risk
2. **Phase 2 (Timeout)** - Leverage existing behavior, add recovery suggestions
3. **Phase 3 (Follow-up)** - High value, security-hardened
4. **Phase 4 (Tests)** - Verify all functionality
5. **Phase 5 (Streaming)** - DEFERRED pending architectural changes

---

## Acceptance Criteria

- [ ] Users see phase progress with elapsed time during brainstorm (Phase 1)
- [ ] ProgressReporter.reset() clears state between runs (Phase 1)
- [ ] Timeout shows partial results + recovery options (Phase 2)
- [ ] Partial results saved to .claude/state/sessions/ with 24h TTL (Phase 2)
- [ ] Top ideas show executable follow-up commands (Phase 3)
- [ ] --execute N validates bounds before execution (Phase 3)
- [ ] All executions logged to audit trail (Phase 3)
- [ ] All phases have unit tests with >80% coverage (Phase 4)
- [ ] SKILL.md updated with new flags and security notes

---

## Implementation Plan

### Phase 1: Real-Time Progress Visibility

**TASK-001**: Create ProgressReporter module
- **File**: `.claude/skills/s/scripts/progress_reporter.py`
- **Action**: Implement ProgressReporter class with phase_start(), persona_complete(), phase_complete(), reset() methods
- **Acceptance**: Unit tests pass, class emits formatted progress messages with elapsed time
- **Effort**: M (2-3h)
- **Prerequisites**: None

**TASK-002**: Verify Rich library availability
- **Action**: Run `pip show rich`, add to requirements if missing
- **Acceptance**: Rich library confirmed available
- **Effort**: S (15min)
- **Prerequisites**: None

**TASK-003**: Integrate ProgressReporter into run_heavy.py
- **File**: `.claude/skills/s/scripts/run_heavy.py`
- **Action**: Import ProgressReporter, instantiate in main(), call reset() before each session, wire into execution flow
- **Acceptance**: Progress messages appear during brainstorm execution
- **Effort**: S (1h)
- **Prerequisites**: TASK-001

**TASK-004**: Add --quiet flag to suppress progress
- **File**: `.claude/skills/s/scripts/run_heavy.py`
- **Action**: Add argparse --quiet flag, pass to ProgressReporter constructor
- **Acceptance**: `--quiet` flag suppresses all progress output
- **Effort**: S (30min)
- **Prerequisites**: TASK-003

**TASK-005**: Update SKILL.md documentation
- **File**: `.claude/skills/s/SKILL.md`
- **Action**: Document --quiet flag in Supported Flags section
- **Acceptance**: Documentation shows --quiet flag with description
- **Effort**: S (15min)
- **Prerequisites**: TASK-004

### Phase 2: Graceful Timeout Handling

**TASK-006**: Add recovery suggestions generator
- **File**: `.claude/skills/s/scripts/run_heavy.py`
- **Action**: Add generate_recovery_suggestions() function that suggests --timeout, --personas, --ideas flags
- **Acceptance**: Recovery options displayed after timeout
- **Effort**: S (1h)
- **Prerequisites**: TASK-003

**TASK-007**: Add partial results persistence
- **File**: `.claude/skills/s/scripts/run_heavy.py`
- **Action**: Add save_partial_results() function with 24h TTL to .claude/state/sessions/
- **Acceptance**: Partial results saved and retrievable
- **Effort**: M (2h)
- **Prerequisites**: TASK-006

**TASK-008**: Add --use-partial flag for resume
- **File**: `.claude/skills/s/scripts/run_heavy.py`
- **Action**: Add --use-partial <session_id> flag that loads cached partial results
- **Acceptance**: Can resume from partial results
- **Effort**: M (2h)
- **Prerequisites**: TASK-007

### Phase 3: Follow-Up Integration

**TASK-009**: Add ALLOWED_SKILLS allowlist to run_heavy.py
- **File**: `.claude/skills/s/scripts/run_heavy.py`
- **Action**: Add `ALLOWED_SKILLS: frozenset[str]` constant with approved skills
- **Acceptance**: Allowlist defined and accessible to build_follow_up_hints()
- **Effort**: S (15min)
- **Prerequisites**: TASK-003

**TASK-010**: Extend build_follow_up_hints() with allowlist enforcement
- **File**: `.claude/skills/s/scripts/run_heavy.py`
- **Action**: Extend existing `build_follow_up_hints()` (lines 378-399) to check ALLOWED_SKILLS
- **Acceptance**: Only allowlisted skills appear in follow-up suggestions
- **Effort**: S (30min)
- **Prerequisites**: TASK-009

**TASK-011**: Update SKILL.md with follow-up hints documentation
- **File**: `.claude/skills/s/SKILL.md`
- **Action**: Document follow-up hints feature with copy-paste examples
- **Acceptance**: Users understand how to act on generated ideas
- **Effort**: S (15min)
- **Prerequisites**: TASK-010

**TASK-012**: ~~Integrate constitutional filter for execution~~ (REMOVED)
- **Status**: REMOVED - No --execute flag, so no execution filtering needed
- **Rationale**: Copy-paste model eliminates command injection risk

### Phase 4: Unit Tests

**TASK-013**: Write unit tests for ProgressReporter
- **File**: `.claude/skills/s/tests/test_progress_reporter.py`
- **Action**: Test phase_start(), persona_complete(), phase_complete(), reset() methods
- **Acceptance**: >80% coverage, all tests pass
- **Effort**: S (1h)
- **Prerequisites**: TASK-001

**TASK-014**: Write unit tests for timeout recovery
- **File**: `.claude/skills/s/tests/test_timeout_recovery.py`
- **Action**: Test generate_recovery_suggestions(), save_partial_results(), --use-partial flag
- **Acceptance**: >80% coverage, all tests pass
- **Effort**: S (1h)
- **Prerequisites**: TASK-006, TASK-007, TASK-008

**TASK-015**: Write unit tests for execution suggestions
- **File**: `.claude/skills/s/tests/test_execution_suggestions.py`
- **Action**: Test suggest_execution(), validate_execute_index(), log_execution_audit(), --execute flag
- **Acceptance**: >80% coverage, includes injection attempt tests
- **Effort**: M (2h)
- **Prerequisites**: TASK-009, TASK-010, TASK-011

**TASK-016**: Write integration test for progress with orchestrator
- **File**: `.claude/skills/s/tests/test_integration_progress.py`
- **Action**: Test end-to-end progress display during brainstorm execution
- **Acceptance**: Progress appears at correct phases
- **Effort**: M (2h)
- **Prerequisites**: TASK-003, TASK-013

---

## Rollback Strategy

### Phase 1 Rollback (ProgressReporter)
1. Remove `--quiet` flag from argparse in `run_heavy.py`
2. Delete `progress_reporter.py` file
3. Remove ProgressReporter import and instantiation from `run_heavy.py`
4. **Estimated rollback time**: <5 minutes

### Phase 2 Rollback (Timeout Recovery)
1. Remove `--use-partial` flag from argparse
2. Remove `generate_recovery_suggestions()` function
3. Remove `save_partial_results()` function
4. Delete partial results files in `.claude/state/sessions/`
5. **Estimated rollback time**: <10 minutes

### Phase 3 Rollback (Follow-Up Integration)
1. Remove `ALLOWED_SKILLS` constant from `run_heavy.py`
2. Revert `build_follow_up_hints()` to original implementation
3. **Estimated rollback time**: <5 minutes

### Full Rollback
```bash
# Revert all changes
git checkout HEAD -- .claude/skills/s/scripts/run_heavy.py
rm .claude/skills/s/scripts/progress_reporter.py
rm .claude/state/sessions/*_partial.json
```

---

## Timeout Budget Guidance

**Problem**: CLI providers (like Chutes) need 2-3x longer timeouts than API providers.

**Current Timeout**: 30 seconds (causing failures)

**Recommended Timeouts by Provider Type**:

| Provider Type | Min Timeout | Recommended | Notes |
|---------------|-------------|-------------|-------|
| **API** (Anthropic, OpenAI) | 30s | 60s | Fast response, rate limits |
| **CLI** (Chutes, local LLMs) | 90s | 120s | Model loading, inference time |
| **Hybrid** (unknown) | 60s | 90s | Conservative default |

**Implementation Pattern**:
```python
# In run_heavy.py or orchestrator.py
def get_timeout_for_provider(provider_name: str) -> int:
    """Get timeout based on provider type."""
    CLI_PROVIDERS = {"chutes", "ollama", "lmstudio", "local"}
    API_PROVIDERS = {"anthropic", "openai", "google", "azure"}

    if provider_name.lower() in CLI_PROVIDERS:
        return 120  # 2 minutes for CLI
    elif provider_name.lower() in API_PROVIDERS:
        return 60   # 1 minute for API
    else:
        return 90   # Default for unknown
```

**Atomic Write Pattern** (for state persistence):
```python
# Use atomic write to prevent partial file corruption
import os
from pathlib import Path

def save_partial_results_atomic(ideas: list[dict], session_id: str) -> str:
    """Save partial results with atomic write pattern."""
    state_dir = Path(".claude/state/sessions")
    state_dir.mkdir(parents=True, exist_ok=True)

    # Write to temp file first
    temp_file = state_dir / f"{session_id}_partial.tmp"
    final_file = state_dir / f"{session_id}_partial.json"

    with open(temp_file, "w") as f:
        json.dump({"ideas": ideas, "timestamp": ...}, f, indent=2)

    # Atomic rename (POSIX) or replace (Windows)
    os.replace(temp_file, final_file)

    return str(final_file)
```

---

## Risks, Success Criteria, Dependencies

### Risks
- **Rich library unavailable**: Install on first use → `pip install rich`
- **Concurrent terminal state pollution**: Per-terminal state directories already implemented
- **Timeout budget underestimated**: CLI providers need 2-3x longer timeouts (addressed above)

### Success Criteria
- [ ] Users see phase progress with elapsed time during brainstorm (Phase 1)
- [ ] Timeout shows partial results + recovery options (Phase 2)
- [ ] Top ideas show executable follow-up commands (Phase 3)
- [ ] All new code has unit tests with >80% coverage (Phase 4)
- [ ] SKILL.md updated with new flags and security notes

### Dependencies
- BrainstormOrchestrator in `.claude/skills/s/lib/orchestrator.py` must be importable
- Rich library available in environment (verify with `pip show rich`)

---

## Requirements Traceability Matrix (RTM)

| Requirement | Tasks | Coverage |
|-------------|-------|----------|
| **REQ-001**: No Real-Time Progress Visibility | TASK-001, TASK-003, TASK-004, TASK-013 | ✅ Complete |
| **REQ-002**: No Incremental Results | TASK-006, TASK-007, TASK-008, TASK-014 | ✅ Complete |
| **REQ-003**: No Interactive Exploration | ⏸️ DEFERRED (Phase 5 streaming blocked) | ⚠️ Blocked |
| **REQ-004**: Timeout is Silent Failure | TASK-006, TASK-007, TASK-014 | ✅ Complete |
| **REQ-005**: No Follow-Up Integration | TASK-009, TASK-010, TASK-011, TASK-015 | ✅ Complete |

### Orphan Tasks (Documented Purpose)

| Task | Purpose | Requirement Mapping |
|------|---------|---------------------|
| TASK-001 | Create ProgressReporter module | REQ-001 |
| TASK-002 | Verify Rich library | REQ-001 (dependency) |
| TASK-004 | Add --quiet flag | REQ-001 (user control) |
| TASK-005 | Update SKILL.md | Documentation |
| TASK-006 | Recovery suggestions | REQ-004 |
| TASK-010 | Extend build_follow_up_hints() | REQ-005 |
| TASK-011 | Update SKILL.md | Documentation |

### Coverage Statistics
- **Requirements Coverage**: 80% (4/5 mapped, 1 blocked by architecture)
- **Task Coverage**: 100% (all tasks mapped to requirements or documentation)
- **Acceptance Coverage**: 100% (all tasks have acceptance criteria)
