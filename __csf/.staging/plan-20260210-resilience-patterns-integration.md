# Implementation Plan: Resilience Patterns Integration for CSF NIP Skills

**Date:** 2025-02-10
**Status:** READY-FOR-IMPLEMENTATION
**Confidence:** 78%

---

## 1. Problem Statement

Current CSF NIP skills (/code, /debug, /rca, /tdd) orchestrate multiple subagent calls without structured resilience patterns. When subagents fail, timeout, or return errors, skills lack consistent mechanisms for:

- **Retry with exponential backoff** - Transient failures cause immediate failure
- **Circuit breaker** - Persistent outages aren't isolated, causing cascading failures
- **Fallback** - No continuity when primary subagent fails
- **Observability** - No metrics on pattern effectiveness

This leads to:
- Unreliable skill execution under stress
- Poor user experience during transient failures
- No visibility into failure patterns
- Inconsistent error handling across skills

---

## 2. Context Analysis

### Existing Infrastructure (Discovery Results)

**Already Exists:**
- `P:\__csf\src\cks\integration\adapters\resilience_error_handler.py` - Full CircuitBreaker, RetryHandler, HealthMonitor classes
- `P:\__csf\src\core\cli_infrastructure\decorators.py` - `@with_retry` decorator (lines 254-312)
- Decorator patterns throughout codebase: `@with_timeout`, `@with_progress`, `@with_caching`

**Gap:**
- No unified `resilience_patterns.py` library with decorator interface for skills
- Skills don't use existing resilience classes
- No enforcement/adoption tracking

### Integration Points

| Skill | Subagent Calls | Risk Level |
|-------|----------------|------------|
| /tdd | tdd-test-writer, tdd-refactorer, tdd-implementer | HIGH - parallel subagents |
| /code | analysis, implementation, verification subagents | HIGH - multi-phase |
| /rca | rca-specialist delegation | MEDIUM - single specialist |
| /debug | analysis subagents | MEDIUM - analysis focus |

### Evidence Sources

- https://portkey.ai/blog/retries-fallbacks-and-circuit-breakers-in-llm-apps (July 2025)
- https://dev.to/paulotorrestech/building-resilient-and-fault-tolerant-applications-with-azure-resiliency-patterns-49an (January 2025)

---

## 3. Existing Implementation Discovery

### Files Examined

1. **`P:\__csf\src\cks\integration\adapters\resilience_error_handler.py`** (1029 lines)
   - `CircuitBreaker` class (lines 157-236) - Full implementation with CLOSED/OPEN/HALF_OPEN states
   - `RetryHandler` class (lines 238-331) - Exponential backoff with jitter
   - `HealthMonitor` class (lines 334-463) - Component health checking
   - `CKSFallbackErrorHandler` class (lines 465-1013) - Comprehensive orchestration

2. **`P:\__csf\src\core\cli_infrastructure\decorators.py`** (742 lines)
   - `@with_retry` decorator (lines 254-312) - Basic retry without circuit breaker
   - `@with_timeout` decorator (lines 35-83) - Timeout handling

3. **Skill Files**
   - `P:\.claude\skills\tdd\SKILL.md`
   - `P:\.claude\skills\code\SKILL.md`
   - `P:\.claude\skills\debug\SKILL.md`
   - `P:\.claude\skills\rca\SKILL.md`

### Existing Resilience Features

| Feature | Location | Reusability |
|---------|----------|-------------|
| CircuitBreaker | resilience_error_handler.py | HIGH - extract to lib |
| RetryHandler | resilience_error_handler.py | HIGH - extract to lib |
| @with_retry | decorators.py | MEDIUM - no jitter, no circuit breaker |
| HealthMonitor | resilience_error_handler.py | LOW - CKS-specific |

---

## 4. Test Discovery

### Existing Test Coverage

```bash
# Search for existing resilience tests
find P:\__csf -name "*test*resilience*" -o -name "*resilience*test*"
```

**Expected gaps:**
- No unit tests for CircuitBreaker class
- No tests for RetryHandler with jitter
- No integration tests for skill-level resilience

### Required Test Coverage

1. **Unit Tests** (`P:\__csf\src\lib\tests\test_resilience_patterns.py`)
   - CircuitBreaker state transitions (CLOSED → OPEN → HALF_OPEN → CLOSED)
   - RetryHandler exponential backoff with jitter
   - Decorator application to sync/async functions

2. **Integration Tests** (`P:\__csf\tests\test_skill_resilience.py`)
   - Subagent failure simulation
   - Circuit breaker activation
   - Fallback behavior

3. **Performance Tests**
   - Overhead measurement (<5% target)
   - Jitter distribution validation

---

## 5. Proposed Solution

### Architecture: Pattern Library + Opt-In Decorator

Create `P:\__csf\src\lib\resilience_patterns.py` with:

```python
# Core decorator
@with_resilience(
    patterns=['retry', 'circuit_breaker'],
    retry_config=RetryConfig(max_attempts=3, base_delay_ms=100, jitter_ms=50),
    circuit_config=CircuitConfig(failure_threshold=5, timeout_seconds=60)
)

# Usage in skills
@with_resilience(['retry', 'circuit_breaker'])
async def execute_subagent(agent_type, prompt):
    return await agent_type.delegate(prompt)
```

### Design Decisions

| Decision | Rationale |
|----------|-----------|
| **Opt-in decorator** vs automatic enforcement | Lowest risk, gradual adoption, no single point of failure |
| **Extract from resilience_error_handler.py** | Reuse proven implementation vs rewrite |
| **Decorator pattern** vs wrapper function | Pythonic, composable with existing decorators |
| **Library at src/lib/** vs per-skill | Shared location, independent versioning |

### Pattern Stack (Layered)

```
┌─────────────────────────────────────────┐
│  @with_resilience (outer orchestrator)   │
│  ┌─────────────────────────────────────┐ │
│  │  @with_fallback (if configured)     │ │
│  │  ┌──────────────────────────────────┐│ │
│  │  │  @circuit_breaker (middle guard) ││ │
│  │  │  ┌─────────────────────────────┐││ │
│  │  │  │  @retry_with_jitter (inner) │││ │
│  │  │  │  function()                 │││ │
│  │  │  └─────────────────────────────┘││ │
│  │  └──────────────────────────────────┘│ │
│  └─────────────────────────────────────┘ │
└─────────────────────────────────────────┘
```

### Components

1. **Retry with Jitter** - Prevent thundering herd
2. **Circuit Breaker** - Isolate persistent failures
3. **Fallback** - Graceful degradation (optional)
4. **Metrics Export** - Observability integration
5. **Config Profiles** - Presets for common use cases (NEW)
6. **Error Classification** - Selective retry by exception type (NEW)
7. **Idempotency Modeling** - Prevent dangerous retry of writes (NEW)
8. **Feature Flags** - Safe rollout with kill-switch (NEW)

### Config Profiles (NEW)

Named presets to avoid hard-coded thresholds:

```python
# Profile definitions
PROFILES = {
    "conservative": ResilienceProfile(
        retry_max_attempts=2,
        circuit_failure_threshold=3,
        idempotent=False,
    ),
    "aggressive": ResilienceProfile(
        retry_max_attempts=5,
        circuit_failure_threshold=10,
        idempotent=True,
    ),
    "read_only": ResilienceProfile(
        retry_max_attempts=3,
        circuit_failure_threshold=5,
        idempotent=True,
        read_only=True,
    ),
    "write_path": ResilienceProfile(
        retry_max_attempts=1,  # Single retry only for writes
        circuit_failure_threshold=3,
        idempotent=False,
    ),
}

# Usage
@with_resilience(profile="conservative")
async def execute_subagent(agent_type, prompt):
    return await agent_type.delegate(prompt)
```

### Error Classification (NEW)

Distinguish retryable from non-retryable errors:

```python
class TransientLLMError(Exception):
    """Base for transient LLM failures - safe to retry."""
    pass

class QuotaError(Exception):
    """Resource quota exceeded - do NOT retry."""
    pass

class InvalidUserInputError(Exception):
    """Invalid input - do NOT retry."""
    pass

# Usage in decorator
@with_resilience(
    profile="aggressive",
    retry_on=[TransientLLMError, TimeoutError],
    no_retry_on=[QuotaError, InvalidUserInputError],
)
```

### Idempotency Parameter (NEW)

```python
@with_resilience(
    profile="write_path",
    idempotent=False,  # Circuit-breaker only, minimal retry
)
async def write_file(path: str, content: str):
    # Non-idempotent operation
    pass

@with_resilience(
    profile="read_only",
    idempotent=True,  # Full retry + circuit breaker
)
async def fetch_data(url: str):
    # Idempotent read operation
    pass
```

### Observability Events (NEW)

Structured logging with event types:

```python
class ResilienceEvent(Enum):
    RETRY_SCHEDULED = "retry_scheduled"
    RETRY_GAVE_UP = "retry_gave_up"
    CIRCUIT_OPENED = "circuit_opened"
    CIRCUIT_HALF_OPEN = "circuit_half_open"
    CIRCUIT_CLOSED = "circuit_closed"
    FALLBACK_USED = "fallback_used"

# In-memory stats API
def get_resilience_stats() -> dict:
    """Return snapshot of resilience metrics."""
    return {
        "retry_attempts": 42,
        "circuit_breaker_state": "CLOSED",
        "fallback_activations": 3,
        "last_event": ResilienceEvent.RETRY_SCHEDULED,
    }
```

### Feature Flags (NEW)

```bash
# Disable resilience per skill
export RESILIENCE_DISABLED_FOR=/tdd,/rca

# Observe-only mode (log don't block)
export RESILIENCE_OBSERVE_ONLY=true
```

---

## 6. Implementation Plan

### Phase 1: Foundation (Day 1-2)

**T-001:** Create `P:\__csf\src\lib\__init__.py` if not exists
- Action: `touch P:\__csf\src\lib\__init__.py`
- Acceptance: `from __csf.src.lib import resilience_patterns` succeeds
- Verification: `python -c "from __csf.src.lib import resilience_patterns; print('OK')"`

**T-002:** Create `P:\__csf\src\lib\resilience_patterns.py`
- Depends on: T-001
- Action: Extract CircuitBreaker, RetryHandler from resilience_error_handler.py; create @with_resilience decorator
- Acceptance: Decorator applies to test function without error
- Verification: `python -c "from __csf.src.lib.resilience_patterns import with_resilience; print('OK')"`

**T-002a:** Create `P:\__csf\src\lib\resilience_config.py` (NEW)
- Depends on: T-001
- Action: Define ResilienceProfile dataclass with presets; implement resolve_config()
- Acceptance: `@with_resilience(profile="conservative")` works
- Verification: `python -c "from __csf.src.lib.resilience_config import PROFILES; assert 'conservative' in PROFILES"`

**T-002b:** Add error classification classes (NEW)
- Depends on: T-002
- Action: Create TransientLLMError, QuotaError, InvalidUserInputError; add retry_on/no_retry_on parameters
- Acceptance: Retries only on configured exception types
- Verification: `pytest P:\__csf\src\lib\tests\test_resilience_patterns.py -k "classification" -v`

**T-002c:** Add `idempotent` parameter to decorator (NEW)
- Depends on: T-002
- Action: Add idempotent: bool parameter; implement conditional retry logic
- Acceptance: Non-idempotent functions get conservative retry
- Verification: `pytest P:\__csf\src\lib\tests\test_resilience_patterns.py -k "idempotent" -v`

**T-002d:** Add feature flag support (NEW)
- Depends on: T-002
- Action: Read RESILIENCE_DISABLED_FOR and RESILIENCE_OBSERVE_ONLY env vars
- Acceptance: Env vars control decorator behavior
- Verification: `RESILIENCE_DISABLED_FOR=/tdd python -c "from __csf.src.lib.resilience_patterns import is_resilience_enabled; assert not is_resilience_enabled('/tdd')"`

**T-002e:** Add structured logging events (NEW)
- Depends on: T-002
- Action: Define ResilienceEvent enum; emit structured logs with skill/subagent tags
- Acceptance: Events visible in logs with correlation
- Verification: `python -c "from __csf.src.lib.resilience_patterns import ResilienceEvent; assert ResilienceEvent.RETRY_SCHEDULED"`

**T-003:** Create `P:\__csf\src\lib\tests\test_resilience_patterns.py`
- Depends on: T-002, T-002a, T-002b, T-002c, T-002d, T-002e
- Action: Create unit tests for all components
- Acceptance: `pytest P:\__csf\src\lib\tests\test_resilience_patterns.py` passes
- Verification: `pytest P:\__csf\src\lib\tests\test_resilience_patterns.py -v`

**T-004:** Add `P:\__csf\src\lib\tests\__init__.py`
- Depends on: T-003
- Action: `touch P:\__csf\src\lib\tests\__init__.py`
- Acceptance: Tests discoverable by pytest
- Verification: `pytest P:\__csf\src\lib\tests/ --collect-only | grep test_resilience`

**T-002:** Create `P:\__csf\src\lib\resilience_patterns.py`
- Extract `CircuitBreaker` from `resilience_error_handler.py`
- Extract `RetryHandler` from `resilience_error_handler.py`
- Add jitter validation
- Create `@with_resilience` decorator
- Acceptance: Decorator applies to test function without error

**T-002a:** Create `P:\__csf\src\lib\resilience_config.py` (NEW)
- Define `ResilienceProfile` dataclass with presets
- Implement `PROFILES` dict: conservative, aggressive, read_only, write_path
- Create `resolve_config()` to merge profile + inline + env overrides
- Acceptance: `@with_resilience(profile="conservative")` works

**T-002b:** Add error classification classes (NEW)
- Create `TransientLLMError`, `QuotaError`, `InvalidUserInputError`
- Add `retry_on` and `no_retry_on` parameters to decorator
- Implement exception classifier function
- Acceptance: Retries only on configured exception types

**T-002c:** Add `idempotent` parameter to decorator (NEW)
- Add `idempotent: bool = True` parameter to `@with_resilience`
- When `idempotent=False`: circuit-breaker only, max 1 retry
- When `idempotent=True`: full retry + circuit breaker
- Acceptance: Non-idempotent functions get conservative retry

**T-002d:** Add feature flag support (NEW)
- Read `RESILIENCE_DISABLED_FOR` env var (comma-separated skill list)
- Read `RESILIENCE_OBSERVE_ONLY` env var for logging mode
- Implement `is_resilience_enabled(skill_name)` helper
- Acceptance: Env vars control decorator behavior

**T-002e:** Add structured logging events (NEW)
- Define `ResilienceEvent` enum with event types
- Emit structured logs for each resilience event
- Include skill, subagent, attempt, timing in logs
- Acceptance: Events visible in logs with correlation

**T-003:** Create `P:\__csf\src\lib\tests\test_resilience_patterns.py`
- Test CircuitBreaker state transitions
- Test RetryHandler with jitter
- Test decorator on sync/async functions
- Test config profile resolution
- Test error classification (retry vs no-retry)
- Test idempotent parameter behavior
- Test feature flag enable/disable
- Acceptance: `pytest P:\__csf\src\lib\tests\test_resilience_patterns.py` passes

**T-004:** Add `P:\__csf\src\lib\tests\__init__.py`
- Acceptance: Tests discoverable by pytest

### Phase 2: Skill Integration (Day 2-3)

**T-005:** Update `/tdd/SKILL.md` to use `@with_resilience`
- Depends on: T-003 (tests must pass first)
- Action: Wrap Task() calls for tdd-test-writer, tdd-refactorer, tdd-implementer with @with_resilience(profile="aggressive")
- Acceptance: Decorator present in skill execution documentation
- Verification: `grep -c "@with_resilience" P:\.claude\skills\tdd\SKILL.md | grep -q "^3$" || grep "@with_resilience" P:\.claude\skills\tdd\SKILL.md`

**T-006:** Update `/code/SKILL.md` to use `@with_resilience`
- Depends on: T-003
- Action: Wrap multi-phase orchestration subagents with @with_resilience(profile="aggressive")
- Acceptance: Decorator present in skill execution documentation
- Verification: `grep "@with_resilience" P:\.claude\skills\code\SKILL.md`

**T-007:** Update `/rca/SKILL.md` to use `@with_resilience`
- Depends on: T-003
- Action: Wrap rca-specialist delegation with @with_resilience(profile="conservative")
- Acceptance: Decorator present in skill execution documentation
- Verification: `grep "@with_resilience" P:\.claude\skills\rca\SKILL.md`

**T-008:** Update `/debug/SKILL.md` to use `@with_resilience`
- Depends on: T-003
- Action: Wrap analysis subagent calls with @with_resilience(profile="conservative")
- Acceptance: Decorator present in skill execution documentation
- Verification: `grep "@with_resilience" P:\.claude\skills\debug\SKILL.md`

### Phase 3: Validation (Day 4-5)

**T-009:** Create `P:\__csf\tests\test_skill_resilience.py`
- Depends on: T-005, T-006, T-007, T-008 (skills must have decorators first)
- Action: Create integration tests for subagent failure simulation, retry verification, circuit breaker activation
- Acceptance: Tests pass, metrics exported
- Verification: `pytest P:\__csf\tests\test_skill_resilience.py -v`

**T-010:** Add observability to resilience_patterns.py (UPDATED)
- Depends on: T-002e (logging events must exist first)
- Action: Create get_resilience_stats() in-memory API
- Acceptance: Stats API returns current metrics
- Verification: `python -c "from __csf.src.lib.resilience_patterns import get_resilience_stats; print(get_resilience_stats())"`

**T-010a:** Add per-skill + per-subagent tag to metrics (NEW)
- Depends on: T-010
- Action: Tag all resilience events with skill_name and subagent_name
- Acceptance: Logs include skill/subagent tags
- Verification: Review logs for skill/subagent tags

**T-010b:** Add correlation IDs to resilience events (NEW)
- Depends on: T-010
- Action: Generate unique request_id per decorated call; include in logs
- Acceptance: Related events traceable via correlation_id
- Verification: Review logs for correlation_id consistency

**T-011:** Run failure scenario tests
- Depends on: T-009
- Action: Simulate timeout, error responses, persistent outage
- Acceptance: All failure scenarios handled gracefully
- Verification: `pytest P:\__csf\tests\test_skill_resilience.py -k "failure" -v`

**T-012:** Verify rollback procedure
- Depends on: T-009
- Action: Remove decorator from one skill, delete resilience_patterns.py, confirm skill still works
- Acceptance: Skills function without patterns (graceful degradation)
- Verification: Manual test: run skill after rollback, confirm no errors

### Phase 4: Documentation (Day 5)

**T-013:** Update `P:\__csf\CLAUDE.md` with reliability principles
- Depends on: T-002 (library must exist first)
- Action: Document pattern library location, decorator usage, rollback procedure
- Acceptance: CLAUDE.md contains resilience section
- Verification: `grep -A 10 "resilience" P:\__csf\CLAUDE.md | grep -q "resilience_patterns"`

**T-014:** Create pattern usage examples
- Depends on: T-002
- Action: Create P:\__csf\src\lib\examples/resilience_usage.py
- Acceptance: Examples run without error
- Verification: `python P:\__csf\src\lib\examples/resilience_usage.py`

**T-015:** Update `/arch` skill templates to auto-include resilience considerations (NEW)
- Depends on: Phase 1 complete (T-001 through T-004 must pass) - library must exist before referencing it
- Action: Add "Resilience Considerations" section to fast.md, deep.md, python.md, data-pipeline.md, cli.md; reference P:\__csf\src\lib\resilience_patterns.py
- Acceptance: `/arch` outputs include resilience considerations by default
- Verification: `grep "Resilience" P:\.claude\skills\arch\resources\*.md`

---

## 7. Risks, Success Criteria, Dependencies

### Success Criteria

| Criterion | Measurement | Target |
|-----------|-------------|--------|
| Retry effectiveness | Success rate after retry | >95% |
| Circuit breaker activation | Time to OPEN on persistent failure | <5 consecutive failures |
| Performance overhead | Latency added by decorator | <5% |
| Adoption | Skills using decorator | 4/4 core skills |

### Risks and Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Decorator adds significant latency | MEDIUM | HIGH | Benchmark before/after, add metrics |
| Inconsistent adoption | HIGH | MEDIUM | Non-blocking enforcement hook |
| Circuit breaker false positives | MEDIUM | MEDIUM | Configurable thresholds |
| Extraction breaks existing code | LOW | HIGH | Preserve original classes, copy not move |

### Dependencies

| Dependency | Type | Status |
|------------|------|--------|
| `resilience_error_handler.py` | Internal source | EXISTS |
| Python 3.12+ | Runtime | SATISFIED |
| pytest | Test framework | EXISTS |
| No external packages | New deps | NONE |

### Rollback Strategy

**Trigger:** Performance overhead >10% or critical skill failure

**Steps:**
1. Remove `@with_resilience` decorator from skill SKILL.md files (T-005 to T-008 reversed)
2. Delete `P:\__csf\src\lib\resilience_patterns.py`
3. Delete test files `test_resilience_patterns.py`, `test_skill_resilience.py`
4. Verify skills work without patterns

**Rollback Time:** <5 minutes

---

## 8. Top Risks

1. **Performance overhead** - Decorator chaining could add latency
   - **Mitigation:** Benchmark during Phase 1, add overhead monitoring

2. **Inconsistent adoption** - Skills may forget to apply decorator
   - **Mitigation:** Non-blocking enforcement hook logs warnings

3. **Circuit breaker false positives** - Transient issues trigger OPEN unnecessarily
   - **Mitigation:** Configurable failure_threshold, half-open testing

---

## 9. Next Actions

```bash
# Phase 1: Foundation
mkdir -p P:\__csf\src\lib\tests
touch P:\__csf\src\lib\__init__.py
# Then implement T-002: Create resilience_patterns.py

# Verify existing patterns work
python -c "from __csf.src.cks.integration.adapters.resilience_error_handler import CircuitBreaker; print('OK')"

# Run initial tests
pytest P:\__csf\src\lib\tests\test_resilience_patterns.py -v
```

---

## References

- Architecture Decision: `P:\__csf\.staging\2025-02-10_deep_reliability-patterns-integration.md`
- Evidence: https://portkey.ai/blog/retries-fallbacks-and-circuit-breakers-in-llm-apps (July 2025)
- Evidence: https://dev.to/paulotorrestech/building-resilient-and-fault-tolerant-applications-with-azure-resiliency-patterns-49an (January 2025)
- Evidence: [Building Fault-Tolerant Systems in Python](https://medium.com/algomart/building-fault-tolerant-systems-in-python-retries-circuit-breakers-and-resilience-patterns-9f81669fc5dc) (August 2025)
- Evidence: [Circuit Breakers in Microservices with FastAPI](https://medium.com/@vinaybilla2021/circuit-breakers-in-microservices-preventing-cascading-failures-0d6b06180a86) (February 2025)
- Evidence: [Python structlog for correlation IDs](https://blog.naveenpn.com/pythons-structlog-modern-structured-logging-for-clean-json-ready-logs) (2025)
- Evidence: [Building Resilient Observability Stack](https://dzone.com/articles/building-a-resilient-observability-stack) (2025)
