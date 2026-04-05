# Context7 Integration Improvements - Implementation Plan

## Overview
Implement 6 critical improvements to Context7 integration for library freshness checker:
1. API key validation on module import
2. Circuit breaker with exponential backoff
3. Canary test with real Context7 API
4. Offline mode fallback
5. Cache management documentation
6. Schema validation for API responses

## Architecture

### Module Structure
```
src/library/
├── context7_client.py (enhanced)
│   ├── get_api_key() - Add validation on first call
│   ├── make_request() - Add circuit breaker decorator
│   └── validate_response_schema() - New function
├── library_checker.py (enhanced)
│   ├── check_api_usage() - Add offline_mode parameter
│   └── _is_context7_available() - Enhanced validation
└── tests/
    ├── test_library_checker.py (update)
    └── test_context7_integration.py (new - canary test)
```

### Key Components
1. **Circuit Breaker Pattern**: Decorator with exponential backoff (1s → 2s → 4s → 8s)
2. **API Key Validation**: Test query on first use to verify key validity
3. **Offline Mode Detection**: Try/except around Context7 calls with graceful degradation
4. **Schema Validation**: Validate API response structure before parsing

## Data Flow

```
User runs check_api_usage()
    ↓
Check CONTEXT7_API_KEY environment variable
    ↓
If offline_mode=False:
    Try Context7 API call (with circuit breaker)
    ↓
If network/API failure:
    Log warning, continue without Context7
    ↓
Return findings (may be empty if Context7 unavailable)
```

## Error Handling

### Circuit Breaker States
- **CLOSED**: Normal operation, requests pass through
- **OPEN**: After 3 consecutive failures, rejects requests immediately
- **HALF-OPEN**: After cooldown period, allow test request

### Error Recovery
- **Rate limit (429)**: Exponential backoff, max 3 retries
- **Network error**: Log warning, return empty results
- **API key invalid**: Log error, disable Context7 checks
- **Offline mode**: Skip Context7 entirely

## Test Strategy

### Unit Tests
1. **Circuit breaker behavior**: Test retry logic, backoff timing
2. **API key validation**: Test valid/invalid/missing keys
3. **Schema validation**: Test valid/malformed API responses
4. **Offline mode**: Test graceful degradation when Context7 unavailable

### Integration Test (Canary)
- **Real API test**: Test against actual Context7 API (requires CONTEXT7_API_KEY)
- **Contract validation**: Verify API response schema matches expectations
- **Marked**: `@pytest.mark.integration` and `@pytest.mark.skipif(not os.environ.get("CONTEXT7_API_KEY"))`

### Regression Tests
- All existing tests must pass
- No behavior changes for valid Context7 responses
- Offline mode doesn't break when Context7 disabled

## Standards Compliance

### Python 2025+ Standards (`/code-python`)
- Use type hints for all function signatures
- Async/await patterns: Not applicable (synchronous code)
- Error handling: Specific exceptions, not bare `except:`
- Logging: Structured logging with appropriate levels
- Documentation: Docstrings for all public functions

### Universal Principles (`/code-standards`)
- **DRY**: Circuit breaker decorator reusable
- **Separation of concerns**: Validation, retry, parsing separate
- **YAGNI**: Implement only what's needed (no over-engineering)
- **Testing**: TDD with RED → GREEN → REFACTOR cycle

## Ramifications

### Breaking Changes
- None (backward compatible)

### Migration Impact
- No database migrations
- No configuration changes required
- Users can opt-in to Context7 by setting CONTEXT7_API_KEY

### Performance Impact
- Minimal overhead from circuit breaker (< 1ms per request)
- Cache validation on import adds ~100ms one-time cost
- Offline mode adds zero overhead

## Pre-Mortem Integration

**Failure Modes Identified:**
1. API key expires → Silent failure → Security breach
   - **Prevention**: Issue #1 (API key validation)
2. API format changes → All checks fail
   - **Prevention**: Issue #2 (canary test)
3. No circuit breaker → API account locked
   - **Prevention**: Issue #3 (circuit breaker)
4. No offline mode → Useless without internet
   - **Prevention**: Issue #4 (offline mode)

**Observability Planning:**
- **Metrics to track**: Cache hit rate, API error rate, circuit breaker state transitions
- **Alerts to configure**: Circuit breaker opens, API key invalid, cache miss rate > 50%
- **Diagnostic locations**: Context7 logs, cache directory, circuit breaker state

## Implementation Tasks

### Task 1: Circuit Breaker Implementation
**File**: `src/library/context7_client.py`
- Add `circuit_breaker` decorator function
- Implement exponential backoff (1s → 2s → 4s → 8s)
- Max 3 retries before giving up
- Track failure count in cache for persistence

### Task 2: API Key Validation
**File**: `src/library/context7_client.py`
- Add `validate_api_key()` function
- Call on first use of get_api_key()
- Test with cheap query (search_library with simple query)
- Log error if key invalid

### Task 3: Schema Validation
**File**: `src/library/context7_client.py`
- Add `validate_response_schema()` function
- Validate search results have 'id' and 'description' fields
- Validate context fetch returns non-empty string
- Call in make_request() before returning data

### Task 4: Offline Mode
**File**: `src/library/library_checker.py`
- Add `offline_mode` parameter to `check_api_usage()`
- Wrap Context7 calls in try/except for URLError
- Log warning when Context7 unavailable
- Continue with version/CVE checks only

### Task 5: Canary Test
**File**: `tests/library/test_context7_integration.py` (NEW)
- Create integration test file
- Add `test_context7_api_contract()` function
- Mark with `@pytest.mark.integration`
- Skip if CONTEXT7_API_KEY not set
- Test search and fetch operations

### Task 6: Cache Documentation
**File**: `src/library/README.md`
- Add "Clearing Context7 Cache" section
- Document cache location: `~/.claude/cache/context7/`
- Add force refresh instructions
- Add troubleshooting for stale warnings

## Success Criteria

- [ ] All 6 tasks implemented
- [ ] All existing tests pass
- [ ] Canary test passes (when CONTEXT7_API_KEY set)
- [ ] Circuit breaker opens after 3 failures
- [ ] Offline mode gracefully degrades
- [ ] Schema validation catches malformed responses
- [ ] Build verification passes (pytest + ruff)
