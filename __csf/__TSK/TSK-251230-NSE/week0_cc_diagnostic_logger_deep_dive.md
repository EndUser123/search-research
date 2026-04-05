# Week 0 Deep-Dive: cc_diagnostic_logger.py Analysis

**Date**: 2025-12-30
**Task**: TSK-251230-NSE
**Analyst**: Claude (CWO12 Workflow)
**Purpose**: Understand existing diagnostic logging infrastructure before implementing Week 1 enhancements

---

## Executive Summary

`cc_diagnostic_logger.py` (425 lines) is a **standalone JSON logging system** that currently operates **independently** of the event_queue → sendevent → SQLite pipeline. It provides session-based correlation across 5 diagnostic log files but lacks distributed tracing capabilities.

**Key Finding**: The logger writes directly to JSONL files and does NOT integrate with the broader observability infrastructure. This is a **design gap** that Week 1 must address.

---

## 1. Current Logging Structure

### 1.1 Configuration

```python
# Environment-based enablement
DIAGNOSTICS_ENABLED = os.environ.get("CC_DIAGNOSTICS_ENABLED", "true").lower() == "true"
LOG_DIR = Path(os.environ.get("CC_DIAGNOSTICS_DIR", "P:/.claude/hooks/logs/diagnostics"))
```

### 1.2 Log Files (5 JSONL files)

| File | Purpose | Key Fields |
|------|---------|------------|
| `cc_context.jsonl` | Per-request context | timestamp, session_id, request_id, context_snapshot, truncated |
| `hook_invocations.jsonl` | Hook execution tracking | timestamp, session_id, hook_name, event_type, action, duration_ms |
| `tool_calls.jsonl` | Tool usage tracking | timestamp, session_id, tool_name, arguments, result |
| `assumptions.jsonl` | Assumption detection | timestamp, session_id, assumption_text, source, pattern_matched |
| `cc_errors.jsonl` | Error logging | timestamp, session_id, error_type, error_message, stack_trace |

### 1.3 Record Format

All records follow this structure:
```json
{
  "timestamp": "2025-12-30T21:30:45.123456",
  "session_id": "20251230_213045",
  "event_type": "pre_tool_use",
  "hook_name": "constitutional_enforcer",
  "action": "pass",
  "duration_ms": 45.2,
  ...
}
```

---

## 2. Timing Mechanism

### 2.1 Current Implementation

**NOT automatic** - duration must be calculated by caller:

```python
def log_hook_invocation(
    hook_name: str,
    event_type: str,
    action: str,
    injection_content: Optional[str] = None,
    reason: Optional[str] = None,
    duration_ms: Optional[float] = None  # ← Optional, caller-provided
)
```

### 2.2 Usage Pattern

Hooks typically wrap their execution:
```python
import time
start = time.perf_counter()
# ... hook logic ...
duration_ms = (time.perf_counter() - start) * 1000
log_hook_invocation(hook_name, event_type, action, duration_ms=duration_ms)
```

### 2.3 Storage

- Stored in `hook_invocations.jsonl`
- Not aggregated or summarized
- No percentile calculation (P50, P95, P99)

---

## 3. Event Structure & Correlation

### 3.1 Session Correlation

**Mechanism**: File-based session ID

```python
def _get_session_id() -> str:
    """Get or create session ID for correlation."""
    session_file = LOG_DIR / ".current_session"
    if session_file.exists():
        return session_file.read_text().strip()
    # Generate: YYYYMMDD_HHMMSS format
    session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    session_file.write_text(session_id)
    return session_id
```

**Limitations**:
- No parent/child span relationship
- No distributed trace context
- No W3C traceparent format
- Session scoped to single directory only

### 3.2 Request Correlation

`cc_context.jsonl` includes `request_id` field, but:
- No propagation to other log files
- No linkage between hook_invocations and their originating request
- No causal chain tracking (unlike instrumentationutils.py)

---

## 4. Integration Points

### 4.1 Current Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     HOOK EXECUTION                               │
└─────────────────────────────────────────────────────────────────┘
                              │
              ┌───────────────┼───────────────┐
              ▼               ▼               ▼
┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐
│  cc_diagnostic   │  │instrumentation   │  │     Other        │
│     _logger.py   │  │     utils.py     │  │    Systems       │
└────────┬─────────┘  └────────┬─────────┘  └──────────────────┘
         │                     │
         │                     │
         ▼                     ▼
┌──────────────────┐  ┌──────────────────┐
│  Direct File     │  │   event_queue    │
│    Writes        │  │     .py          │
│  (JSONL files)   │  └────────┬─────────┘
└──────────────────┘           │
                               ▼
                      ┌──────────────────┐
                      │   sendevent.py   │
                      └────────┬─────────┘
                               ▼
                      ┌──────────────────┐
                      │  SQLite DB       │
                      │  (events.db)     │
                      └──────────────────┘
```

**Key Insight**: `cc_diagnostic_logger.py` is **isolated** from the event_queue pipeline.

### 4.2 Integration Opportunities

| Current | Proposed | Benefit |
|---------|----------|---------|
| Standalone JSONL writes | Also queue to event_queue | Single source of truth |
| No span context | Add W3C traceparent | Distributed tracing |
| No aggregation | Add metrics collection | P50/P95/P99 visibility |
| Manual duration | Decorator-based timing | Automatic span capture |

---

## 5. Backward Compatibility Analysis

### 5.1 Safe Changes

| Change | Risk Level | Reason |
|--------|------------|--------|
| Add W3C traceparent field | Low | Optional field, existing code ignores |
| Add span export method | Low | New function, doesn't affect existing writes |
| Decorator wrapper | Low | Opt-in via @hook_diagnostic |
| event_queue integration | Low | Additive only, keeps JSONL writes |

### 5.2 Breaking Changes (AVOID)

| Change | Impact | Mitigation |
|--------|--------|------------|
| Remove JSONL writes | Hooks may parse files | Keep both, phase out gradually |
| Change session_id format | Breaks log aggregation | Maintain format, add trace_id |
| Modify existing field names | Breaks parsers | Add new fields only |

### 5.3 Compatibility Strategy

**Phase 1 (Week 1-3)**: Dual-write
- Continue JSONL writes (backward compat)
- Add event_queue integration
- New fields: traceparent, span_id, parent_span_id

**Phase 2 (Week 4-6)**: Migration
- Dashboard queries SQLite (not JSONL)
- Existing hooks transition gradually

**Phase 3 (Week 7+)**: Deprecation
- JSONL writes become optional
- Default to SQLite-only

---

## 6. Recommended Enhancement Approach

### 6.1 Decision: EXTEND vs. REBUILD

**Recommendation: EXTEND**

| Criterion | Extend | Rebuild |
|-----------|--------|---------|
| Effort | 20-30h | 40-60h |
| Risk | Low | High |
| Data continuity | Preserved | Lost |
| Migration | None required | All hooks need updates |

### 6.2 Extension Design

```python
# Add to cc_diagnostic_logger.py

class TraceContext:
    """W3C traceparent format: version-trace_id-parent_id-flags"""
    def __init__(self, traceparent: str | None = None):
        if traceparent:
            self.version, self.trace_id, self.parent_id, self.flags = \
                traceparent.split('-')
        else:
            self.trace_id = uuid4().hex
            self.parent_id = '0' * 16
            self.flags = '01'

    def to_header(self) -> str:
        return f"00-{self.trace_id}-{self.parent_id}-{self.flags}"

class Span:
    """OpenTelemetry-style span for duration tracking"""
    def __init__(self, name: str, trace_context: TraceContext, parent: Span | None = None):
        self.name = name
        self.trace_context = trace_context
        self.span_id = uuid4().hex[:16]
        self.parent_span_id = parent.span_id if parent else trace_context.parent_id
        self.start_time = time.perf_counter()
        self.events = []

    def end(self) -> float:
        """Return duration in milliseconds"""
        return (time.perf_counter() - self.start_time) * 1000

def hook_diagnostic(func):
    """Decorator for automatic span tracking"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        trace_ctx = TraceContext(kwargs.pop('traceparent', None))
        span = Span(func.__name__, trace_ctx)
        try:
            result = func(*args, **kwargs)
            action = getattr(result, 'action', 'pass')
        except Exception as e:
            action = 'error'
            raise
        finally:
            duration_ms = span.end()
            log_hook_invocation(
                hook_name=func.__name__,
                event_type=kwargs.get('event_type', 'unknown'),
                action=action,
                duration_ms=duration_ms,
                traceparent=trace_ctx.to_header(),
                span_id=span.span_id,
                parent_span_id=span.parent_span_id
            )
            # NEW: Also queue to event_queue for SQLite insertion
            ConstitutionalInstrumentation._queue_manager.add_event({
                'timestamp': int(time.time() * 1000),
                'trace_id': trace_ctx.trace_id,
                'span_id': span.span_id,
                'parent_span_id': span.parent_span_id,
                'hook_name': func.__name__,
                'duration_ms': duration_ms,
                'action': action
            })
        return result
    return wrapper
```

### 6.3 Schema Extensions

**cc_context.jsonl** - Add fields:
```json
{
  "traceparent": "00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01",
  "span_id": "00f067aa0ba902b7"
}
```

**SQLite: constitutional_events table** - Add columns:
```sql
ALTER TABLE constitutional_events ADD COLUMN trace_id TEXT;
ALTER TABLE constitutional_events ADD COLUMN span_id TEXT;
ALTER TABLE constitutional_events ADD COLUMN parent_span_id TEXT;
ALTER TABLE constitutional_events ADD COLUMN duration_ms REAL;
CREATE INDEX idx_trace ON constitutional_events(trace_id);
```

---

## 7. Gap Resolution

### Gap 2 from Plan Review: "INTEGRATION IS UNCLEAR"

**Question**: What does cc_diagnostic_logger.py currently do?

**Answer**:
- 5 JSONL files for different diagnostic concerns
- Session-based correlation via file-based session ID
- Direct file writes, NOT integrated with event_queue pipeline
- Manual duration tracking (caller-provided)
- No distributed tracing, no W3C traceparent

**Implication for Week 1**:
1. Extend with TraceContext class (W3C traceparent)
2. Add Span class for automatic duration tracking
3. Create event_queue bridge (dual-write strategy)
4. Add @hook_diagnostic decorator for opt-in instrumentation

**Risk**: LOW - Extension is additive, maintains backward compatibility

---

## 8. Open Questions for Week 1

| Question | Impact | Decision Point |
|----------|--------|----------------|
| Should JSONL writes continue after dashboard is live? | Storage, maintenance | Week 3 |
| What telemetry backend? (Jaeger, Prometheus, Tempo) | Export format | Week 2 |
| Sampling strategy for high-volume hooks? | Performance | Week 2 |
| Span retention period in SQLite? | Storage growth | Week 3 |

---

## 9. Acceptance Criteria

Week 1 enhancement is complete when:

- [ ] TraceContext class implements W3C traceparent format
- [ ] Span class provides automatic duration tracking
- [ ] @hook_diagnostic decorator works on test hook
- [ ] event_queue receives diagnostic events (dual-write)
- [ ] SQLite schema extended with trace/span columns
- [ ] No existing JSONL writes broken
- [ ] Dashboard can query by trace_id

---

## 10. Next Steps

1. **Architecture Decision Record** (ADR-001): Instrumentation mechanism
2. **Metrics Schema Design**: Counter, Histogram, Gauge definitions
3. **Dashboard SQLite Schema**: Queries and aggregation patterns
4. **Performance Baseline**: Profile all 68 hooks before instrumentation
5. **Risk Register**: Document and track Week 1 risks

---

**Document Status**: Draft - Ready for review
**Next Review**: After ADR-001 completion
