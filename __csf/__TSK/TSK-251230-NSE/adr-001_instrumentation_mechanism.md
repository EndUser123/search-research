# ADR-001: Hook Instrumentation Mechanism

**Status**: Proposed
**Date**: 2025-12-30
**Task**: TSK-251230-NSE
**Context**: Week 0 Design - CSF NIP Observability Enhancement

---

## Context

The CSF NIP has 68 behavioral hooks (~32K lines) in `P:/.claude/hooks/` with minimal observability. Currently:
- Hook execution is opaque - no timing, no failure rates, no performance visibility
- `cc_diagnostic_logger.py` exists but is standalone (JSONL files only)
- `instrumentationutils.py` has causal chain tracking but no span/duration metrics
- No correlation between hook invocations and distributed traces

**Problem**: How do we instrument hooks for observability without disrupting existing behavior?

---

## Decision

**Adopt a decorator-based instrumentation pattern with W3C tracecontext propagation.**

### Pattern: `@hook_observable`

```python
from .instrumentationutils import hook_observable

@hook_observable
def pre_tool_use(**kwargs):
    # Hook implementation unchanged
    return {"action": "pass"}
```

**Behavior**:
1. Wraps function with span timing (automatic duration_ms capture)
2. Extracts or creates W3C traceparent from context
3. Emits event to event_queue for SQLite insertion
4. Maintains existing return value semantics
5. Errors propagate unchanged (observable only)

---

## Alternatives Considered

### Alternative 1: Manual Instrumentation
```python
def pre_tool_use(**kwargs):
    start = time.perf_counter()
    try:
        result = implementation()
        log_success(start)
        return result
    except Exception as e:
        log_error(e, start)
        raise
```

**Rejected**: Requires modifying 68 hooks manually, high effort, error-prone.

### Alternative 2: Function Wrapping at Hook Load Time
```python
# In hook loader
original_fn = hook_module.get('pre_tool_use')
hook_module['pre_tool_use'] = wrap_with_instrumentation(original_fn)
```

**Rejected**: Requires changing hook loader, harder to debug, less explicit.

### Alternative 3: Background Metrics Collection
```python
# Separate thread polls hook execution files
```

**Rejected**: Violates C.1 constitutional constraint (no background threads), race conditions.

### Alternative 4: Subprocess Wrapper
```python
# Each hook runs in subprocess with metrics collection
```

**Rejected**: Massive overhead, breaks in-memory state, incompatible with current architecture.

---

## Consequences

### Positive

| Impact | Description |
|--------|-------------|
| **Low friction** | Hooks opt-in via decorator, no behavioral changes |
| **Automatic timing** | duration_ms captured without manual code |
| **Trace propagation** | W3C traceparent enables distributed tracing |
| **Single source of truth** | All metrics flow to SQLite via event_queue |
| **Backward compatible** | Non-decorated hooks work unchanged |
| **Debuggable** | Stack traces point to original function |

### Negative

| Impact | Mitigation |
|--------|------------|
| **Decorator required** | Gradual rollout, critical hooks first |
| **Python-only** | All hooks are Python, no concern |
| **Dependency on instrumentationutils** | Already imported by most hooks |
| **Minimal overhead** | Benchmark <1ms per call |

### Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Decorator breaks hook return semantics | Low | Unit tests for each decorated hook |
| Performance overhead degrades response time | Low | Baseline before/after, target <5% |
| W3C traceparent not propagated by Claude | Medium | Store in session_data, reconstruct |
| SQLite write bottleneck | Low | event_queue already batches writes |

---

## Implementation

### Phase 1: Core Infrastructure (Week 1, 20-30h)

**File**: `P:/.claude/hooks/instrumentationutils.py`

```python
import time
import uuid
from functools import wraps
from typing import Callable, Any, Optional

# W3C traceparent: version-trace_id-parent_id-flags
# Example: 00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01

class TraceContext:
    """W3C tracecontext for distributed tracing."""

    VERSION = "00"

    def __init__(self, traceparent: Optional[str] = None):
        if traceparent:
            parts = traceparent.split('-')
            if len(parts) != 4 or parts[0] != self.VERSION:
                # Invalid format, create new trace
                self.trace_id = self._generate_trace_id()
                self.parent_id = '0' * 16
                self.flags = '01'
            else:
                self.trace_id = parts[1]
                self.parent_id = parts[2]
                self.flags = parts[3]
        else:
            self.trace_id = self._generate_trace_id()
            self.parent_id = '0' * 16
            self.flags = '01'

    @staticmethod
    def _generate_trace_id() -> str:
        """Generate 32-char trace ID (16 random bytes)."""
        return uuid.uuid4().hex

    @staticmethod
    def _generate_span_id() -> str:
        """Generate 16-char span ID (8 random bytes)."""
        return uuid.uuid4().hex[:16]

    def to_header(self) -> str:
        """Export as W3C traceparent header."""
        return f"{self.VERSION}-{self.trace_id}-{self.parent_id}-{self.flags}"

    def create_child(self) -> "TraceContext":
        """Create child tracecontext for nested spans."""
        child = TraceContext(self.to_header())
        child.parent_id = self._generate_span_id()
        return child


class Span:
    """OpenTelemetry-style span for timing and metadata."""

    def __init__(
        self,
        name: str,
        trace_context: TraceContext,
        parent_span: Optional["Span"] = None,
        attributes: Optional[dict[str, Any]] = None
    ):
        self.name = name
        self.trace_context = trace_context
        self.span_id = trace_context._generate_span_id()
        self.parent_span_id = parent_span.span_id if parent_span else trace_context.parent_id
        self.start_time = time.perf_counter()
        self.attributes = attributes or {}
        self.events: list[dict[str, Any]] = []

    def end(self) -> float:
        """End span and return duration in milliseconds."""
        duration_sec = time.perf_counter() - self.start_time
        return duration_sec * 1000

    def to_dict(self, duration_ms: float) -> dict[str, Any]:
        """Export span for event_queue."""
        return {
            "timestamp": int(time.time() * 1000),
            "trace_id": self.trace_context.trace_id,
            "span_id": self.span_id,
            "parent_span_id": self.parent_span_id,
            "span_name": self.name,
            "duration_ms": duration_ms,
            "attributes": self.attributes
        }


def hook_observable(func: Callable) -> Callable:
    """
    Decorator for automatic hook instrumentation.

    Wraps function to:
    1. Create span with automatic timing
    2. Extract or create W3C tracecontext
    3. Emit event to event_queue on completion
    4. Preserve original function behavior

    Usage:
        @hook_observable
        def pre_tool_use(**kwargs):
            return {"action": "pass"}
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        # Extract or create tracecontext
        traceparent = kwargs.pop('traceparent', None)
        trace_ctx = TraceContext(traceparent)

        # Create span
        span = Span(
            name=func.__name__,
            trace_context=trace_ctx,
            attributes={
                "hook_type": _infer_hook_type(func.__name__),
                "module": func.__module__
            }
        )

        # Execute with instrumentation
        try:
            result = func(*args, **kwargs)
            action = _extract_action(result)
            status = "success"
        except Exception as e:
            action = "error"
            status = "error"
            span.events.append({
                "name": "exception",
                "attributes": {
                    "exception_type": type(e).__name__,
                    "exception_message": str(e)
                }
            })
            raise
        finally:
            duration_ms = span.end()

            # Emit to event_queue
            from .instrumentationutils import ConstitutionalInstrumentation
            span_dict = span.to_dict(duration_ms)
            span_dict.update({
                "status": status,
                "action": action,
                "hook_name": func.__name__
            })

            ConstitutionalInstrumentation._queue_manager.add_event(span_dict)

        return result

    return wrapper


def _infer_hook_type(hook_name: str) -> str:
    """Infer hook type from name for categorization."""
    if hook_name.startswith('pre_'):
        return 'pre_hook'
    elif hook_name.startswith('post_'):
        return 'post_hook'
    elif hook_name.endswith('_injection'):
        return 'injection_hook'
    else:
        return 'general_hook'


def _extract_action(result: Any) -> str:
    """Extract action from hook return value."""
    if isinstance(result, dict):
        return result.get('action', 'pass')
    return 'pass'
```

### Phase 2: Instrument Critical Hooks (Week 1, 3h per hook)

**Priority hooks** (6 total, ~18h):

1. `anti_sycophancy/advocate_injection.py` - Pre-response injection
2. `truth_validator.py` - Fact-checking gate
3. `goal_anchor.py` - Goal state tracking
4. `constitutional_enforcer.py` - Core enforcement
5. `pre_tool_use.py` - Tool call validation
6. `PostToolUse.py` - Tool result processing

**Pattern**:
```python
# Add to top of file
from .instrumentationutils import hook_observable

# Decorate main hook function
@hook_observable
def pre_tool_use(**kwargs):
    # ... existing implementation unchanged ...
    return {"action": "pass"}
```

### Phase 3: Dashboard Queries (Week 2)

**SQLite Schema Extension**:
```sql
ALTER TABLE constitutional_events ADD COLUMN trace_id TEXT;
ALTER TABLE constitutional_events ADD COLUMN span_id TEXT;
ALTER TABLE constitutional_events ADD COLUMN parent_span_id TEXT;
ALTER TABLE constitutional_events ADD COLUMN duration_ms REAL;
CREATE INDEX idx_trace ON constitutional_events(trace_id);
CREATE INDEX idx_span ON constitutional_events(span_id);
CREATE INDEX idx_hook_duration ON constitutional_events(hook_name, duration_ms);
```

**Dashboard Queries**:
```sql
-- P50, P95, P99 duration by hook
SELECT
    hook_name,
    percentile_50(duration_ms) as p50,
    percentile_95(duration_ms) as p95,
    percentile_99(duration_ms) as p99,
    COUNT(*) as invocations
FROM constitutional_events
WHERE trace_id IS NOT NULL
GROUP BY hook_name;

-- Trace waterfall
SELECT
    span_id,
    parent_span_id,
    hook_name,
    duration_ms,
    timestamp
FROM constitutional_events
WHERE trace_id = ?
ORDER BY timestamp;

-- Error rate by hook
SELECT
    hook_name,
    COUNT(*) FILTER (WHERE status = 'error') * 100.0 / COUNT(*) as error_rate
FROM constitutional_events
WHERE trace_id IS NOT NULL
GROUP BY hook_name;
```

---

## Testing Strategy

### Unit Tests
```python
def test_hook_observable_preserves_return_value():
    @hook_observable
    def test_hook():
        return {"action": "inject", "content": "test"}
    result = test_hook()
    assert result == {"action": "inject", "content": "test"}

def test_hook_observable_captures_duration():
    @hook_observable
    def slow_hook():
        time.sleep(0.01)
        return {"action": "pass"}
    # Verify event_queue received event with duration_ms >= 10
```

### Integration Tests
```python
def test_trace_context_propagation():
    parent_ctx = TraceContext()
    child_ctx = parent_ctx.create_child()
    assert child_ctx.parent_id != '0' * 16

def test_span_waterfall():
    # Execute hook with nested calls
    # Query SQLite for trace hierarchy
    spans = query_trace(trace_id)
    assert spans[0].parent_span_id == '0' * 16  # Root
    assert spans[1].parent_span_id == spans[0].span_id  # Child
```

---

## Rollout Plan

| Week | Hooks | Coverage |
|------|-------|----------|
| 1 | 6 critical | High-priority observability |
| 2 | 20 additional | Broad coverage |
| 3 | Remaining 42 | Full instrumentation |

---

## Success Metrics

| Metric | Before | Target | Week |
|--------|--------|--------|------|
| Hooks with span timing | 0 | 6 | 1 |
| Trace ID propagation | 0% | 100% (decorated hooks) | 1 |
| Dashboard: P50/P95/P99 | N/A | Available | 2 |
| Performance overhead | N/A | <5% | 1 |
| Hook behavior change | N/A | 0 | 1 |

---

**Document Status**: Proposed - Ready for architectural review
**Next Review**: After Week 1 implementation completion
