# Python DX Safety Hardening Implementation Plan

## Overview

Add production-ready safety features to the existing Python DX Improvement Tools to address critical gaps identified in pre-mortem analysis:
1. **Observability Layer** - Metrics tracking and health checks for DX tools
2. **File Locking** - Multi-terminal safety for concurrent cache operations
3. **Block Decision Logging** - Feedback loop for authorization gate pattern refinement

## 1. Problem Statement

### Current State
Python DX Improvement Tools (cache manager, authorization gate enhancements, hook feedback UX) are **fully implemented and tested** (38/38 tests passing). However, pre-mortem analysis identified **3 critical production safety gaps**:

1. **No Observability** - Cannot detect failures or measure success
   - Can't answer "how many cache clears this week?"
   - Can't detect error rate spikes before user impact
   - No health checks to verify tools are working

2. **No Multi-Terminal Protection** - Race condition risk
   - Two terminals running `pip install -e /same/path` simultaneously
   - Cache deleted while package is being installed
   - No file locking for concurrent cache operations

3. **Unknown False Positive Rate** - No feedback loop
   - Don't know if whitelist patterns block legitimate work
   - Can't measure block rate (% blocked vs. auto-approved)
   - No mechanism to refine patterns based on real usage

### Impact
- **Risk Level**: HIGH (RISK:9) - State corruption, data loss, or user workflow disruption
- **Urgency**: Before production deployment
- **Scope**: Safety hardening of existing implementation (no new features)

## 2. Context Analysis

### Allowed APIs

**From existing codebase discovery:**

| API | Source | Purpose |
|-----|--------|---------|
| `python_cache_manager.clear_package_cache()` | `__lib/python_cache_manager.py` | Cache clearing |
| `python_cache_manager.pre_install_cache_clean()` | `__lib/python_cache_manager.py` | Auto-clear before pip install |
| `hook_feedback_summary.format_blocking_summary()` | `__lib/hook_feedback_summary.py` | User-friendly messages |
| `is_project_safe_operation()` | `PreToolUse_authorization_gate.py` | Check safe patterns |
| `has_explicit_authorization()` | `PreToolUse_authorization_gate.py` | Authorization check |

**Existing Infrastructure to Leverage:**

| Module | Capability | Integration Point |
|--------|------------|-------------------|
| `shared_utils.log_hook_event()` | JSONL logging | Use for metrics persistence |
| `__lib/file_lock.py` | Cross-platform locking (portalocker) | Use for cache operation locks |
| `terminal_detection.detect_terminal_id()` | Terminal/session ID | Include in all log entries |
| `cc_diagnostic_logger.log_hook_invocation()` | Structured diagnostics | Optional (if available) |

**Anti-Patterns to Avoid:**
- ❌ Don't write to stderr (Claude Code treats stderr as hook error)
- ❌ Don't break existing JSONL parsers (`logs/diagnostics/*.jsonl`)
- ❌ Don't create parallel logging systems (reuse existing infrastructure)
- ❌ Don't block on observability failures (graceful degradation)

### Configuration

**Environment Variables:**
```python
# Optional: Enable verbose metrics logging
DX_TOOLS_METRICS_VERBOSE = "true"  # default: false

# Optional: Health check interval (seconds)
DX_TOOLS_HEALTH_CHECK_INTERVAL = "3600"  # default: 3600 (1 hour)
```

**Paths:**
```
Metrics log: P:/.claude/hooks/logs/dx_tools_metrics.jsonl
Health report: P:/.claude/hooks/logs/dx_tools_health.json
Lock files: P:/.claude/hooks/logs/locks/*.lock
Block log: P:/.claude/hooks/logs/auth_blocks.jsonl
```

## 3. Existing Implementation Discovery

### Files to Modify

| File | Current Lines | Modification Type | Risk |
|------|---------------|-------------------|------|
| `__lib/python_cache_manager.py` | 82 | Add metrics tracking, file locking | LOW |
| `PreToolUse_authorization_gate.py` | 718 | Add block decision logging | LOW |
| `PreToolUse.py` | 883 | Integrate observability imports | LOW |

### Files to Create

| File | Purpose | Size Estimate |
|------|---------|---------------|
| `__lib/dx_tools_observability.py` | Metrics & health checks | ~200 lines |
| `__lib/dx_tools_locking.py` | File locking wrapper | ~80 lines |
| `scripts/dx_tools_analyze_blocks.py` | Weekly block analysis script | ~150 lines |

### Integration Points

**Cache Manager (Task 10):**
```python
# In __lib/python_cache_manager.py
from dx_tools_observability import get_metrics
from dx_tools_locking import with_cache_lock

@with_cache_lock(package_path)
def clear_package_cache(package_path):
    metrics = get_metrics()
    metrics.start_timer("cache_clear")
    try:
        # ... existing logic ...
        metrics.record_event("cache", "cleared", result["cleared_count"])
    except Exception as e:
        metrics.record_event("cache", "error", 1)
    finally:
        metrics.end_timer("cache_clear")
```

**Authorization Gate (Task 12):**
```python
# In PreToolUse_authorization_gate.py
from dx_tools_observability import get_metrics

def is_project_safe_operation(command, working_dir):
    metrics = get_metrics()
    if _is_safe_pattern_match(command):
        metrics.record_event("auth", "auto_approved")
        return True

    # Log block decisions
    _log_block_decision(command, working_dir, reason="not_project_safe")
    metrics.record_event("auth", "blocked")
    return False
```

## 4. Test Discovery

### Test Structure

**Follow existing patterns** (from 38 passing tests):

```python
# tests/test_dx_tools_observability.py
sys.path.insert(0, str(Path(__file__).parent.parent / "__lib"))
import dx_tools_observability

class TestDXToolsMetrics:
    def test_record_event(self):
        metrics = dx_tools_observability.DXToolsMetrics()
        metrics.record_event("cache", "cleared", 5)
        assert metrics.get_metrics("cache")["cleared"] == 5

    def test_persist_metrics(self, tmp_path):
        # Test metrics written to JSONL
        pass

    def test_health_check(self):
        health = dx_tools_observability.DXToolsHealth.check_cache_manager()
        assert health["overall"] in ["healthy", "unhealthy"]

# tests/test_dx_tools_locking.py
class TestCacheLocking:
    def test_concurrent_access(self, tmp_path):
        # Test that lock prevents concurrent cache clears
        pass

    def test_lock_timeout(self, tmp_path):
        # Test stale lock timeout
        pass

# tests/test_dx_tools_block_logging.py
class TestBlockLogging:
    def test_block_decision_logged(self, tmp_path):
        # Test that blocks are logged with full context
        pass

    def test_log_analysis_script(self, tmp_path):
        # Test that analysis script can parse logs
        pass
```

### Test Scenarios

| Scenario | Test Type | Verification |
|----------|-----------|--------------|
| Metrics persist across reloads | Unit | JSONL file contains correct data |
| Health check detects errors | Unit | Returns "unhealthy" when logs dir unwritable |
| File lock prevents concurrent access | Integration | Second process waits for lock |
| Lock timeout after stale lock | Integration | Lock acquired after timeout |
| Block decisions logged with context | Integration | JSONL has command, working_dir, pattern |
| Analysis script calculates rate | Integration | Correct block % from logs |

## 5. Proposed Solution

### Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Python DX Tools (Existing)                   │
│  ┌──────────────────┐  ┌──────────────────┐  ┌─────────────────┐ │
│  │  Cache Manager   │  │  Auth Gate       │  │  Feedback UX     │ │
│  └──────────────────┘  └──────────────────┘  └─────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                  NEW: Safety Hardening Layer                  │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │              dx_tools_observability.py                    │ │
│  │  • DXToolsMetrics - Event tracking, timing               │ │
│  │  • DXToolsHealth - Health checks, error detection        │ │
│  └────────────────────────────────────────────────────────────┘ │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │               dx_tools_locking.py                         │ │
│  │  • with_cache_lock() decorator                           │ │
│  │  • File lock with timeout (portalocker)                  │ │
│  └────────────────────────────────────────────────────────────┘ │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │               Block Logging (auth_gate.py)                │ │
│  │  • _log_block_decision() function                        │ │
│  │  • JSONL: logs/auth_blocks.jsonl                         │ │
│  └────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Observability Outputs                     │
│  • logs/dx_tools_metrics.jsonl (streaming metrics)           │
│  • logs/dx_tools_health.json (health status)                  │
│  • logs/auth_blocks.jsonl (block decisions)                   │
│  • scripts/dx_tools_analyze_blocks.py (weekly review)         │
└─────────────────────────────────────────────────────────────────┘
```

### Design Decisions

**1. Observability Design**
- **JSONL format** - Streamable, append-only, compatible with existing parsers
- **Graceful degradation** - Metrics failures don't break hooks
- **Global singleton** - `get_metrics()` for consistent tracking
- **Category-based** - Separate metrics for cache, auth, performance

**2. File Locking Design**
- **portalocker-based** - Cross-platform (Windows fcntl, Unix msvcrt)
- **Per-package locks** - Lock path includes package hash
- **Timeout with cleanup** - Stale locks auto-expire after 60 seconds
- **Decorator pattern** - `@with_cache_lock()` for clean integration

**3. Block Logging Design**
- **Complete context** - command, working_dir, pattern matched, reason
- **Structured format** - JSONL for programmatic analysis
- **Analysis script** - Weekly review script to calculate block rate
- **Alert threshold** - Warn if block rate > 10%

## 6. Implementation Plan

### Task 10: Observability Layer
**File**: `__lib/dx_tools_observability.py`

**Components**:
1. `DXToolsMetrics` class
   - `record_event(category, event, count)` - Track occurrences
   - `start_timer(operation)` / `end_timer(operation)` - Performance tracking
   - `get_metrics(category)` - Query current metrics
   - `_persist()` - Write to JSONL log

2. `DXToolsHealth` class
   - `check_cache_manager()` - Verify cache manager health
   - `check_authorization_gate()` - Verify auth gate health
   - `get_health_report()` - Comprehensive health status

3. Global `get_metrics()` function - Singleton access

**Integration Points**:
- Import in `python_cache_manager.py` - Track cache clears, errors
- Import in `PreToolUse_authorization_gate.py` - Track blocks, auto-approvals
- Import in `PreToolUse.py` - Track hook performance

### Task 11: File Locking
**File**: `__lib/dx_tools_locking.py`

**Components**:
1. `with_cache_lock(package_path)` decorator
   - Generate lock file path from package hash
   - Use `portalocker.lock()` with timeout
   - Cleanup lock file in finally block

2. Lock file management
   - Path: `logs/locks/cache_{hash}.lock`
   - Timeout: 60 seconds (configurable)
   - Auto-cleanup stale locks

**Integration Points**:
- Decorate `clear_package_cache()` function
- Wrap cache deletion operations

### Task 12: Block Decision Logging
**File**: `PreToolUse_authorization_gate.py` (modification)

**Components**:
1. `_log_block_decision(command, working_dir, reason)` function
   - Write to `logs/auth_blocks.jsonl`
   - Include: timestamp, terminal_id, session_id, command, working_dir, pattern, reason

2. `scripts/dx_tools_analyze_blocks.py`
   - Read `logs/auth_blocks.jsonl`
   - Calculate block rate (%)
   - Show top blocked patterns
   - Alert if rate > 10%

**Integration Points**:
- Call in `is_project_safe_operation()` when returning False
- Call in `has_explicit_authorization()` when blocking

### Tests (3 new test files)
| File | Test Count | Coverage |
|------|------------|----------|
| `tests/test_dx_tools_observability.py` | 6 tests | Metrics, health checks |
| `tests/test_dx_tools_locking.py` | 4 tests | Concurrent access, timeout |
| `tests/test_dx_tools_block_logging.py` | 5 tests | Block logging, analysis |

## 7. Risks, Success Criteria, Dependencies

### Top Risks

1. **[RISK:6] File locking causes performance degradation**
   - **Mitigation**: Lock only around cache deletion, not entire function
   - **Warning**: Cache operations take >5 seconds consistently
   - **Owner**: [Your name]

2. **[RISK:4] Metrics logging fills disk**
   - **Mitigation**: Rotate logs monthly, limit to last 1000 entries per category
   - **Warning**: `dx_tools_metrics.jsonl` > 10MB
   - **Owner**: [Your name]

3. **[RISK:4] portalocker not available**
   - **Mitigation**: Fallback to no-op if import fails, warn once
   - **Warning**: ImportError on portalocker
   - **Owner**: [Your name]

### Success Criteria

✅ **All tests pass** (15 new tests + existing 38 tests)
✅ **Health checks pass** - All components report "healthy"
✅ **Block rate measurable** - Can calculate % blocks from logs
✅ **No performance regression** - Cache operations <1 second overhead
✅ **Multi-terminal safe** - Concurrent pip install -e doesn't corrupt state
✅ **Graceful degradation** - Tools work even if observability fails

### Dependencies

**Required**:
- ✅ `portalocker` package (add to requirements if not present)
- ✅ Existing `__lib/file_lock.py` (use as fallback)
- ✅ Existing `shared_utils.log_hook_event()` (for logging pattern)

**Optional**:
- `cc_diagnostic_logger` - Use if available for structured diagnostics
- `terminal_detection` - Use if available for terminal/session IDs

### Rollback Strategy

**If issues arise**:
1. **Graceful degradation** - All new features fail open (allow without metrics)
2. **Feature flags** - Use `DX_TOOLS_OBSERVABILITY_ENABLED=false` to disable
3. **Revert by file** - Each task in separate file, easy to revert
4. **No breaking changes** - Existing functionality untouched

## Implementation Tasks

### Task 10.1: Create observability module
**File**: `P:/.claude/hooks/__lib/dx_tools_observability.py`
**Effort**: M
**Acceptance**:
- [ ] `DXToolsMetrics` class with event tracking
- [ ] `DXToolsHealth` class with health checks
- [ ] `get_metrics()` singleton function
- [ ] Metrics write to JSONL log
- [ ] Type hints on all functions
- [ ] Docstrings following Google style

### Task 10.2: Integrate metrics into cache manager
**File**: `P:/.claude/hooks/__lib/python_cache_manager.py`
**Effort**: S
**Acceptance**:
- [ ] Track cache clears (count, paths)
- [ ] Track errors (count, error messages)
- [ ] Track performance (duration_ms)
- [ ] Import observability module
- [ ] Tests verify metrics recorded

### Task 10.3: Integrate metrics into authorization gate
**File**: `P:/.claude/hooks/PreToolUse_authorization_gate.py`
**Effort**: S
**Acceptance**:
- [ ] Track auto-approved operations
- [ ] Track blocked operations
- [ ] Import observability module
- [ ] Tests verify metrics recorded

### Task 11.1: Create file locking module
**File**: `P:/.claude/hooks/__lib/dx_tools_locking.py`
**Effort**: M
**Acceptance**:
- [ ] `with_cache_lock()` decorator
- [ ] Use portalocker for cross-platform locking
- [ ] Lock file path includes package hash
- [ ] 60-second timeout with stale lock cleanup
- [ ] Fallback if portalocker unavailable
- [ ] Tests verify concurrent access protection

### Task 11.2: Integrate locking into cache manager
**File**: `P:/.claude/hooks/__lib/python_cache_manager.py`
**Effort**: S
**Acceptance**:
- [ ] Decorate `clear_package_cache()` with `@with_cache_lock`
- [ ] Lock only around deletion operations
- [ ] Tests verify lock acquired/released

### Task 12.1: Add block decision logging
**File**: `P:/.claude/hooks/PreToolUse_authorization_gate.py`
**Effort**: M
**Acceptance**:
- [ ] `_log_block_decision()` function
- [ ] Write to `logs/auth_blocks.jsonl`
- [ ] Include full context (command, working_dir, pattern, reason)
- [ ] Import `terminal_detection` if available
- [ ] Tests verify blocks logged

### Task 12.2: Create block analysis script
**File**: `P:/.claude/hooks/scripts/dx_tools_analyze_blocks.py`
**Effort**: M
**Acceptance**:
- [ ] Read `logs/auth_blocks.jsonl`
- [ ] Calculate block rate (%)
- [ ] Show top blocked patterns
- [ ] Alert if rate > 10%
- [ ] Accept `--days` parameter for time window
- [ ] Tests verify analysis accuracy

### Task 13: Create tests
**Files**: 3 test files
**Effort**: L
**Acceptance**:
- [ ] `test_dx_tools_observability.py` - 6 tests
- [ ] `test_dx_tools_locking.py` - 4 tests
- [ ] `test_dx_tools_block_logging.py` - 5 tests
- [ ] All new tests pass
- [ ] Total test count: 38 + 15 = 53 tests passing

### Task 14: Update documentation
**File**: `P:/.claude/plan.md`
**Effort**: S
**Acceptance**:
- [ ] Add Phase 2 tasks to plan.md
- [ ] Update observability planning section
- [ ] Document warning signs to monitor
- [ ] Include pre-mortem integration

## Next Actions

1. **Review this plan** - Verify all sections complete and accurate
2. **Run verifier** - `/plan-workflow review P:/.claude/hooks/plans/plan-20260304-dx-safety-hardening.md`
3. **Begin implementation** - Start with Task 10 (Observability) once verified
4. **Run tests** - Ensure 53/53 tests pass (38 existing + 15 new)
5. **Deploy monitoring** - Check health reports and block rates weekly

---

**Plan Status**: 🔄 READY FOR REVIEW
**Created**: 2026-03-04
**Trigger**: Pre-mortem analysis identified 3 critical safety gaps
