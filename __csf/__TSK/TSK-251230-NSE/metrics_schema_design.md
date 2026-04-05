# Metrics Schema Design

**Date**: 2025-12-30
**Task**: TSK-251230-NSE
**Purpose**: Define metrics collection schema for CSF NIP observability enhancement

---

## Overview

This document defines the metrics collection schema for the Constitutional Safety Framework observability enhancement. The design follows OpenTelemetry semantics while being pragmatic for SQLite storage.

---

## Metric Types

### 1. Counter

**Description**: Monotonically increasing value (cumulative).

**Use cases**:
- Hook invocations (total count)
- Hook actions (pass, inject, warn, block counts)
- Errors
- Cache hits/misses

**Schema**:
```sql
CREATE TABLE metrics_counters (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    metric_name TEXT NOT NULL,
    labels_json TEXT NOT NULL,  -- {"hook_name": "constitutional_enforcer", "action": "pass"}
    value INTEGER NOT NULL,      -- Increment amount
    timestamp INTEGER NOT NULL,  -- Unix milliseconds
    session_id TEXT,
    UNIQUE(metric_name, labels_json, timestamp)
);

CREATE INDEX idx_counter_name ON metrics_counters(metric_name, timestamp);
CREATE INDEX idx_counter_session ON metrics_counters(session_id);
```

**Examples**:
| metric_name | labels_json | value |
|-------------|-------------|-------|
| `hook_invocations_total` | `{"hook_name":"constitutional_enforcer"}` | 1 |
| `hook_actions_total` | `{"hook_name":"advocate_injection","action":"inject"}` | 1 |
| `hook_errors_total` | `{"hook_name":"truth_validator","error_type":"ValidationError"}` | 1 |

**Aggregation**:
```sql
-- Total invocations by hook
SELECT
    json_extract(labels_json, '$.hook_name') as hook_name,
    SUM(value) as total_invocations
FROM metrics_counters
WHERE metric_name = 'hook_invocations_total'
GROUP BY json_extract(labels_json, '$.hook_name');
```

---

### 2. Histogram

**Description**: Distribution of values (counts in buckets).

**Use cases**:
- Hook execution duration (ms)
- Tool call latency
- Response size
- Token usage

**Schema**:
```sql
CREATE TABLE metrics_histograms (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    metric_name TEXT NOT NULL,
    labels_json TEXT NOT NULL,
    value REAL NOT NULL,         -- Observed value
    timestamp INTEGER NOT NULL,
    session_id TEXT
);

CREATE INDEX idx_histogram_name ON metrics_histograms(metric_name, timestamp);
CREATE INDEX idx_histogram_session ON metrics_histograms(session_id);

-- Pre-computed percentiles (materialized view alternative)
CREATE TABLE metrics_histogram_percentiles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    metric_name TEXT NOT NULL,
    labels_json TEXT NOT NULL,
    window_start INTEGER NOT NULL,  -- Window start (ms)
    window_end INTEGER NOT NULL,    -- Window end (ms)
    count INTEGER NOT NULL,
    sum REAL NOT NULL,
    p50 REAL,
    p75 REAL,
    p90 REAL,
    p95 REAL,
    p99 REAL,
    max REAL,
    min REAL
);
```

**Examples**:
| metric_name | labels_json | value |
|-------------|-------------|-------|
| `hook_duration_ms` | `{"hook_name":"pre_tool_use"}` | 45.2 |
| `hook_duration_ms` | `{"hook_name":"advocate_injection"}` | 123.8 |
| `hook_duration_ms` | `{"hook_name":"constitutional_enforcer"}` | 12.1 |

**Percentile Query**:
```sql
-- P50, P95, P99 by hook (using SQLite percentile extension)
SELECT
    json_extract(labels_json, '$.hook_name') as hook_name,
    percentile_50(value) as p50,
    percentile_90(value) as p90,
    percentile_95(value) as p95,
    percentile_99(value) as p99,
    COUNT(*) as count,
    MIN(value) as min,
    MAX(value) as max
FROM metrics_histograms
WHERE metric_name = 'hook_duration_ms'
GROUP BY json_extract(labels_json, '$.hook_name');
```

**Fallback for standard SQLite** (no percentile extension):
```sql
-- Calculate P50 (median) using standard SQL
SELECT
    json_extract(labels_json, '$.hook_name') as hook_name,
    AVG(value) as mean,
    COUNT(*) as count
FROM metrics_histograms
WHERE metric_name = 'hook_duration_ms'
GROUP BY json_extract(labels_json, '$.hook_name');
```

---

### 3. Gauge

**Description**: Point-in-time value (can go up or down).

**Use cases**:
- Active session count
- Queue depth
- Memory usage
- Active hook count

**Schema**:
```sql
CREATE TABLE metrics_gauges (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    metric_name TEXT NOT NULL,
    labels_json TEXT NOT NULL,
    value REAL NOT NULL,
    timestamp INTEGER NOT NULL,
    session_id TEXT
);

CREATE INDEX idx_gauge_name ON metrics_gauges(metric_name, timestamp DESC);
```

**Examples**:
| metric_name | labels_json | value |
|-------------|-------------|-------|
| `event_queue_depth` | `{"queue":"default"}` | 7 |
| `active_sessions` | `{}` | 3 |
| `memory_usage_mb` | `{}` | 512.4 |

**Latest value query**:
```sql
SELECT
    metric_name,
    labels_json,
    value,
    timestamp
FROM metrics_gauges
WHERE (metric_name, timestamp) IN (
    SELECT metric_name, MAX(timestamp)
    FROM metrics_gauges
    GROUP BY metric_name, labels_json
);
```

---

## Metric Definitions

### Constitutional Hook Metrics

| Metric | Type | Labels | Description |
|--------|------|--------|-------------|
| `hook_invocations_total` | Counter | hook_name, module | Total hook executions |
| `hook_duration_ms` | Histogram | hook_name, status | Execution time in ms |
| `hook_actions_total` | Counter | hook_name, action | Count by action type |
| `hook_errors_total` | Counter | hook_name, error_type | Error count by type |
| `hook_cache_hits_total` | Counter | hook_name | Cache hit count |
| `hook_cache_misses_total` | Counter | hook_name | Cache miss count |

### Constitutional Compliance Metrics

| Metric | Type | Labels | Description |
|--------|------|--------|-------------|
| `compliance_violations_total` | Counter | article, severity, hook | Constitutional violations |
| `compliance_blocks_total` | Counter | article, hook | Blocked operations |
| `compliance_injections_total` | Counter | article, hook | Content injections |
| `compliance_warnings_total` | Counter | article, hook | Warnings issued |

### Telemetry Infrastructure Metrics

| Metric | Type | Labels | Description |
|--------|------|--------|-------------|
| `event_queue_depth` | Gauge | queue_name | Events waiting in queue |
| `event_flush_duration_ms` | Histogram | queue_name | Flush operation time |
| `event_flush_errors_total` | Counter | queue_name, error_type | Flush failures |
| `sqlite_write_duration_ms` | Histogram | table_name | DB write time |
| `sqlite_connection_pool_size` | Gauge | N/A | Active connections |

---

## Label Cardinality Management

**Problem**: High cardinality labels explode metric series count.

**Policy**:

| Label | Cardinality | Strategy |
|-------|-------------|----------|
| `hook_name` | ~68 | Allowed |
| `action` | 4 | Allowed |
| `error_type` | ~20 | Allowed |
| `session_id` | ~1000/day | **PROHIBITED** in metrics (use DB filter) |
| `trace_id` | ~10000/day | **PROHIBITED** in metrics |
| `user_id` | Variable | **PROHIBITED** (privacy) |
| `article` | ~150 | Allowed |

**Implementation**:
```python
ALLOWED_LABELS = {'hook_name', 'action', 'error_type', 'severity', 'article', 'module', 'status'}

def validate_labels(labels: dict[str, str]) -> dict[str, str]:
    """Filter labels to enforce cardinality bounds."""
    return {k: v for k, v in labels.items() if k in ALLOWED_LABELS}
```

---

## Storage Retention

| Metric Type | Raw Retention | Aggregated Retention |
|-------------|---------------|----------------------|
| Counters | 90 days | Forever (yearly rollup) |
| Histograms | 30 days | 90 days (hourly aggregates) |
| Gauges | 7 days | 30 days (5-min aggregates) |

**Cleanup job** (runs daily):
```sql
-- Delete old counter records (after rollup)
DELETE FROM metrics_counters WHERE timestamp < strftime('%s', 'now', '-90 days') * 1000;

-- Delete old histogram records (after rollup)
DELETE FROM metrics_histograms WHERE timestamp < strftime('%s', 'now', '-30 days') * 1000;

-- Delete old gauge records
DELETE FROM metrics_gauges WHERE timestamp < strftime('%s', 'now', '-7 days') * 1000;
```

---

## Integration with Existing Schema

### Extension to `constitutional_events`

The existing table already captures most observability data:

```sql
-- Existing columns
timestamp, sessionid, article, event_type, severity, evidence_tier,
confidence, payload, hook_name, blocked, causal_chain_id, caused_by_event_id

-- Add for metrics integration
ALTER TABLE constitutional_events ADD COLUMN trace_id TEXT;
ALTER TABLE constitutional_events ADD COLUMN span_id TEXT;
ALTER TABLE constitutional_events ADD COLUMN parent_span_id TEXT;
ALTER TABLE constitutional_events ADD COLUMN duration_ms REAL;
```

**Relationship**:
- `constitutional_events` = Event log (what happened)
- `metrics_*` tables = Aggregatable metrics (performance, rates)

**Hybrid query example**:
```sql
-- Hook compliance rate with timing
SELECT
    e.hook_name,
    SUM(CASE WHEN e.blocked = 1 THEN 1 ELSE 0 END) as blocks,
    COUNT(*) as total,
    AVG(h.duration_ms) as avg_duration_ms,
    percentile_95(h.duration_ms) as p95_ms
FROM constitutional_events e
LEFT JOIN metrics_histograms h
    ON json_extract(h.labels_json, '$.hook_name') = e.hook_name
    AND h.metric_name = 'hook_duration_ms'
WHERE e.trace_id IS NOT NULL
GROUP BY e.hook_name;
```

---

## Metrics Collector Class

```python
class MetricsCollector:
    """Metrics collection with cardinality bounds and batching."""

    def __init__(self, queue_manager: EventQueueManager):
        self._queue = queue_manager
        self._counters: defaultdict[str, int] = defaultdict(int)
        self._gauges: dict[str, float] = {}

    def increment(self, name: str, value: int = 1, labels: dict[str, str] | None = None):
        """Increment counter metric."""
        labels = validate_labels(labels or {})
        self._counters[f"{name}:{labels}"] += value
        self._flush_if_threshold()

    def record(self, name: str, value: float, labels: dict[str, str] | None = None):
        """Record histogram/gauge value."""
        labels = validate_labels(labels or {})
        self._queue.add_event({
            "metric_type": "histogram",
            "metric_name": name,
            "labels": labels,
            "value": value,
            "timestamp": int(time.time() * 1000)
        })

    def set_gauge(self, name: str, value: float, labels: dict[str, str] | None = None):
        """Set gauge value."""
        labels = validate_labels(labels or {})
        self._gauges[f"{name}:{labels}"] = value
        self._queue.add_event({
            "metric_type": "gauge",
            "metric_name": name,
            "labels": labels,
            "value": value,
            "timestamp": int(time.time() * 1000)
        })
```

---

## Dashboard API Endpoints

```
GET /api/metrics/counters?name=hook_invocations_total&hook_name=constitutional_enforcer
GET /api/metrics/histograms?name=hook_duration_ms&agg=p95
GET /api/metrics/gauges?name=event_queue_depth
GET /api/metrics/compliance?window=24h
```

---

## Success Criteria

- [ ] All metric types defined with clear use cases
- [ ] Schema constraints enforce cardinality bounds
- [ ] Integration path to existing `constitutional_events` documented
- [ ] Retention policy prevents unbounded growth
- [ ] Dashboard queries defined for all visualizations
- [ ] MetricsCollector class implemented in instrumentationutils.py

---

**Document Status**: Draft - Ready for review
**Next Review**: After Week 1 implementation
