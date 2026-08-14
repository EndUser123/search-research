# UCI Critical & High Priority Fixes - Implementation Plan

## Overview
Fix CRITICAL security vulnerabilities and performance bottlenecks identified by UCI inspection in search-research package.

## Architecture
- **SEC-001**: Replace pickle with JSON/msgpack + cryptographic signing
- **SEC-002**: Replace exec() with Jinja2 sandbox
- **PERF-001**: Sequential → Concurrent provider execution with asyncio.gather()

## Data Flow
```
Current (Sequential):
Provider 1 → Provider 2 → Provider 3 → Results
        ↓         ↓         ↓
      0.5s      0.5s      0.5s = 1.5s total

Fixed (Concurrent):
Provider 1 ─┐
Provider 2 ─┼→ asyncio.gather() → Results (0.5s total)
Provider 3 ─┘
```

## Test Strategy
- Security: RCE prevention tests, signing validation tests
- Performance: Benchmark before/after concurrent execution
- Integration: All backends still work with concurrent execution

## Standards Compliance
- Python 3.14+ type hints required
- pytest for all tests
- mypy type checking
- ruff linting

## Implementation Plan

### TASK-SEC-001: Fix Unsafe Pickle Deserialization (CRITICAL)
**File**: `core/backends/local/cds_backend.py:104`
- Replace `pickle.load()` with `json.load()` or `msgpack.unpack()`
- Add cryptographic signing (HMAC-SHA256) to prevent tampering
- Migration: Auto-convert old pickle files on first load
- Tests: Verify pickle RCE is blocked, signing validation works

### TASK-SEC-002: Fix Unsafe exec() Code Execution (CRITICAL)
**File**: `core/backends/rlm.py:397`
- Replace `exec()` with Jinja2 sandboxed templates
- Limit accessible built-ins to safe subset
- Add timeout protection
- Tests: Verify code injection is blocked, safe templates work

### TASK-PERF-001: Implement Concurrent Provider Execution (CRITICAL)
**File**: `core/orchestrator.py:134`
- Replace sequential `for` loop with `asyncio.gather()`
- Add timeout protection per provider
- Handle partial failures gracefully
- Tests: Benchmark 3x speedup, error isolation works

### TASK-PERF-002: Implement O(n) Deduplication (HIGH)
**File**: `core/processors/deduplication.py:167`
- Replace O(n²) deduplication with MinHash LSH (O(n))
- Add configurable similarity threshold
- Tests: Verify performance improvement, accuracy maintained

### TASK-QUAL-004: Split Multilang Backend (HIGH)
**File**: `core/backends/local/multilang_backend.py` (1,722 lines)
- Extract language-specific backends (Python, JavaScript, etc.)
- Create base class with shared logic
- Tests: All language backends work independently

### TASK-TEST-001: Add Concurrency Safety Tests (HIGH)
**File**: `core/cache.py:30`
- Add stress tests with concurrent cache access
- Verify `threading.Lock()` prevents races
- Tests: 100 concurrent operations, no data corruption

## Success Criteria
- All 3 CRITICAL issues resolved (verified by tests)
- All 3 HIGH issues resolved (verified by tests)
- Performance: 3-5x faster provider execution
- Security: No RCE vectors, no unsafe code execution
- Test coverage ≥ 80%

## Risks
- **Pickle migration**: Old cache files may be incompatible (auto-migration mitigates)
- **exec() replacement**: Jinja2 may have different semantics (sandbox mitigates)
- **Concurrent execution**: Some backends may not be async-ready (timeout mitigates)

## Dependencies
- `cryptography` library for HMAC signing
- `jinja2` for templating
- `msgpack` (optional, for performance)

## Rollback Strategy
- Git commit before each TASK
- Feature flags for concurrent execution
- Fallback to JSON if pickle migration fails
