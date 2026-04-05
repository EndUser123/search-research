# Dashboard SQLite Schema

**Date**: 2025-12-30
**Task**: TSK-251230-NSE
**Purpose**: Define SQLite schema for Constitutional Compliance Dashboard

---

## Overview

The dashboard provides real-time visibility into constitutional compliance, hook performance, and system health. Data is sourced from SQLite with pre-computed aggregations for responsive queries.

---

## Schema Design

### 1. Base Tables (Extended Existing)

```sql
-- Extend existing constitutional_events table
ALTER TABLE constitutional_events ADD COLUMN trace_id TEXT;
ALTER TABLE constitutional_events ADD COLUMN span_id TEXT;
ALTER TABLE constitutional_events ADD COLUMN parent_span_id TEXT;
ALTER TABLE constitutional_events ADD COLUMN duration_ms REAL;

-- Indexes for dashboard queries
CREATE INDEX idx_events_trace ON constitutional_events(trace_id);
CREATE INDEX idx_events_hook_time ON constitutional_events(hook_name, timestamp DESC);
CREATE INDEX idx_events_session_trace ON constitutional_events(sessionid, trace_id);
```

---

### 2. Dashboard Materialized Views

#### 2.1 Hook Performance Summary

```sql
CREATE TABLE dashboard_hook_performance (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    hook_name TEXT NOT NULL UNIQUE,
    total_invocations INTEGER DEFAULT 0,
    total_errors INTEGER DEFAULT 0,
    error_rate REAL DEFAULT 0,
    avg_duration_ms REAL DEFAULT 0,
    p50_duration_ms REAL DEFAULT 0,
    p95_duration_ms REAL DEFAULT 0,
    p99_duration_ms REAL DEFAULT 0,
    min_duration_ms REAL DEFAULT 0,
    max_duration_ms REAL DEFAULT 0,
    last_invocation INTEGER,
    last_updated INTEGER NOT NULL DEFAULT (strftime('%s', 'now') * 1000)
);

-- Refreshed every 5 minutes via cron
-- Query: Aggregates from constitutional_events WHERE duration_ms IS NOT NULL
```

#### 2.2 Compliance Scorecard

```sql
CREATE TABLE dashboard_compliance_scorecard (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT NOT NULL,  -- YYYY-MM-DD
    article TEXT NOT NULL,
    total_checks INTEGER DEFAULT 0,
    passes INTEGER DEFAULT 0,
    blocks INTEGER DEFAULT 0,
    warnings INTEGER DEFAULT 0,
    injections INTEGER DEFAULT 0,
    compliance_rate REAL DEFAULT 0,
    severity_breakdown_json TEXT,  -- {"critical": 0, "high": 2, "medium": 5}
    UNIQUE(date, article)
);

-- Refreshed daily at midnight
-- Query: GROUP BY article FROM constitutional_events WHERE event_type='compliance_check'
```

#### 2.3 Session Timeline

```sql
CREATE TABLE dashboard_session_timeline (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    start_time INTEGER NOT NULL,
    end_time INTEGER,
    total_hooks INTEGER DEFAULT 0,
    total_tools INTEGER DEFAULT 0,
    total_blocks INTEGER DEFAULT 0,
    total_injections INTEGER DEFAULT 0,
    compliance_score REAL DEFAULT 100,
    trace_count INTEGER DEFAULT 0
);

CREATE INDEX idx_session_time ON dashboard_session_timeline(start_time DESC);
```

#### 2.4 Alert Thresholds

```sql
CREATE TABLE dashboard_alert_thresholds (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    metric_name TEXT NOT NULL UNIQUE,
    warning_threshold REAL,
    critical_threshold REAL,
    comparison_type TEXT NOT NULL,  -- 'greater_than', 'less_than', 'equals'
    enabled INTEGER DEFAULT 1,
    last_triggered INTEGER,
    notification_sent INTEGER DEFAULT 0
);

-- Seed data
INSERT INTO dashboard_alert_thresholds (metric_name, warning_threshold, critical_threshold, comparison_type) VALUES
('hook_error_rate', 5.0, 10.0, 'greater_than'),
('hook_p95_duration_ms', 500, 1000, 'greater_than'),
('compliance_rate', 95.0, 90.0, 'less_than'),
('event_queue_depth', 50, 100, 'greater_than');
```

---

### 3. Metrics Tables (New)

```sql
-- Counter metrics (invocations, errors, etc.)
CREATE TABLE metrics_counters (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    metric_name TEXT NOT NULL,
    labels_json TEXT NOT NULL,
    value INTEGER NOT NULL,
    timestamp INTEGER NOT NULL,
    session_id TEXT
);

CREATE INDEX idx_counter_name_time ON metrics_counters(metric_name, timestamp DESC);

-- Histogram metrics (durations, sizes)
CREATE TABLE metrics_histograms (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    metric_name TEXT NOT NULL,
    labels_json TEXT NOT NULL,
    value REAL NOT NULL,
    timestamp INTEGER NOT NULL,
    session_id TEXT
);

CREATE INDEX idx_histogram_name_time ON metrics_histograms(metric_name, timestamp DESC);

-- Gauge metrics (queue depth, memory)
CREATE TABLE metrics_gauges (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    metric_name TEXT NOT NULL,
    labels_json TEXT NOT NULL,
    value REAL NOT NULL,
    timestamp INTEGER NOT NULL,
    session_id TEXT
);
```

---

## Dashboard Queries

### 1. Overview Panel

```sql
-- Key metrics for last 24 hours
SELECT
    COUNT(DISTINCT sessionid) as active_sessions,
    COUNT(*) FILTER (WHERE timestamp > strftime('%s', 'now', '-24 hours') * 1000) as total_events,
    SUM(CASE WHEN blocked = 1 THEN 1 ELSE 0 END) as blocks,
    AVG(CASE WHEN duration_ms IS NOT NULL THEN duration_ms END) as avg_hook_duration_ms
FROM constitutional_events
WHERE timestamp > strftime('%s', 'now', '-24 hours') * 1000;
```

### 2. Hook Performance Table

```sql
-- Sorted by error rate, then P95 duration
SELECT
    hook_name,
    total_invocations,
    total_errors,
    error_rate,
    avg_duration_ms,
    p95_duration_ms,
    p99_duration_ms,
    last_invocation
FROM dashboard_hook_performance
ORDER BY error_rate DESC, p95_duration_ms DESC
LIMIT 50;
```

### 3. Compliance Trend Chart

```sql
-- Daily compliance rate by article
SELECT
    date,
    article,
    compliance_rate,
    total_checks,
    passes,
    blocks
FROM dashboard_compliance_scorecard
WHERE date >= date('now', '-30 days')
ORDER BY date DESC, article;
```

### 4. Trace Waterfall

```sql
-- All spans in a trace, ordered by timestamp
SELECT
    span_id,
    parent_span_id,
    hook_name,
    duration_ms,
    timestamp,
    CASE WHEN blocked = 1 THEN 'blocked' ELSE 'pass' END as status
FROM constitutional_events
WHERE trace_id = ?
    AND span_id IS NOT NULL
ORDER BY timestamp;
```

### 5. Top Violations

```sql
-- Most blocked articles/hooks
SELECT
    article,
    hook_name,
    SUM(CASE WHEN blocked = 1 THEN 1 ELSE 0 END) as block_count,
    COUNT(*) as total_checks,
    ROUND(SUM(CASE WHEN blocked = 1 THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) as block_rate
FROM constitutional_events
WHERE timestamp > strftime('%s', 'now', '-7 days') * 1000
    AND article IS NOT NULL
GROUP BY article, hook_name
ORDER BY block_count DESC
LIMIT 20;
```

### 6. Session Detail

```sql
-- Complete session timeline
SELECT
    timestamp,
    event_type,
    hook_name,
    CASE
        WHEN blocked = 1 THEN 'BLOCK'
        WHEN injection_content IS NOT NULL THEN 'INJECT'
        ELSE 'PASS'
    END as action,
    duration_ms,
    article,
    severity
FROM constitutional_events
WHERE sessionid = ?
ORDER BY timestamp;
```

---

## API Endpoints

### Flask Server (`dashboard.py`)

```python
from flask import Flask, jsonify, request
import sqlite3
from pathlib import Path

app = Flask(__name__)
DB_PATH = Path.home() / ".claude" / "events.db"

def query_db(sql: str, params: tuple = ()):
    """Execute query and return results."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute(sql, params)
    results = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return results

@app.route('/api/overview')
def overview():
    """24-hour summary metrics."""
    data = query_db("""
        SELECT
            COUNT(DISTINCT sessionid) as active_sessions,
            COUNT(*) as total_events,
            SUM(CASE WHEN blocked = 1 THEN 1 ELSE 0 END) as blocks,
            AVG(CASE WHEN duration_ms IS NOT NULL THEN duration_ms END) as avg_duration
        FROM constitutional_events
        WHERE timestamp > strftime('%s', 'now', '-24 hours') * 1000
    """)
    return jsonify(data[0] if data else {})

@app.route('/api/hooks/performance')
def hook_performance():
    """Hook performance summary."""
    limit = request.args.get('limit', 50, type=int)
    data = query_db("""
        SELECT * FROM dashboard_hook_performance
        ORDER BY error_rate DESC, p95_duration_ms DESC
        LIMIT ?
    """, (limit,))
    return jsonify(data)

@app.route('/api/compliance/trend')
def compliance_trend():
    """30-day compliance trend."""
    days = request.args.get('days', 30, type=int)
    data = query_db("""
        SELECT * FROM dashboard_compliance_scorecard
        WHERE date >= date('now', '-' || ? || ' days')
        ORDER BY date DESC, article
    """, (days,))
    return jsonify(data)

@app.route('/api/trace/<trace_id>')
def trace_detail(trace_id: str):
    """Trace waterfall for visualization."""
    data = query_db("""
        SELECT span_id, parent_span_id, hook_name, duration_ms, timestamp,
               CASE WHEN blocked = 1 THEN 'blocked' ELSE 'pass' END as status
        FROM constitutional_events
        WHERE trace_id = ? AND span_id IS NOT NULL
        ORDER BY timestamp
    """, (trace_id,))
    return jsonify(data)

@app.route('/api/sessions')
def sessions():
    """Recent sessions with filters."""
    hours = request.args.get('hours', 24, type=int)
    data = query_db("""
        SELECT * FROM dashboard_session_timeline
        WHERE start_time > strftime('%s', 'now', '-' || ? || ' hours') * 1000
        ORDER BY start_time DESC
        LIMIT 100
    """, (hours,))
    return jsonify(data)

@app.route('/api/alerts')
def alerts():
    """Current alerts based on thresholds."""
    data = query_db("""
        SELECT
            a.metric_name,
            a.warning_threshold,
            a.critical_threshold,
            a.last_triggered,
            CASE
                WHEN a.last_triggered IS NULL THEN 'ok'
                WHEN a.last_triggered > strftime('%s', 'now', '-1 hour') * 1000 THEN 'active'
                ELSE 'resolved'
            END as status
        FROM dashboard_alert_thresholds a
        WHERE a.enabled = 1
        ORDER BY a.last_triggered DESC
    """)
    return jsonify(data)

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5555, debug=False)
```

---

## Refresh Jobs

### Materialized View Refresh (cron or Flask-APScheduler)

```python
import sqlite3
from pathlib import Path
import time

DB_PATH = Path.home() / ".claude" / "events.db"

def refresh_hook_performance():
    """Update dashboard_hook_performance table."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Use UPSERT (SQLite 3.24+)
    cursor.execute("""
        INSERT INTO dashboard_hook_performance (
            hook_name, total_invocations, total_errors, error_rate,
            avg_duration_ms, p50_duration_ms, p95_duration_ms, p99_duration_ms,
            min_duration_ms, max_duration_ms, last_invocation, last_updated
        )
        SELECT
            hook_name,
            COUNT(*) as total_invocations,
            SUM(CASE WHEN blocked = 1 OR event_type = 'error' THEN 1 ELSE 0 END) as total_errors,
            ROUND(SUM(CASE WHEN blocked = 1 OR event_type = 'error' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) as error_rate,
            AVG(duration_ms) as avg_duration_ms,
            NULL as p50_duration_ms,  -- Requires extension
            NULL as p95_duration_ms,
            NULL as p99_duration_ms,
            MIN(duration_ms) as min_duration_ms,
            MAX(duration_ms) as max_duration_ms,
            MAX(timestamp) as last_invocation,
            strftime('%s', 'now') * 1000 as last_updated
        FROM constitutional_events
        WHERE duration_ms IS NOT NULL
        GROUP BY hook_name
        ON CONFLICT(hook_name) DO UPDATE SET
            total_invocations = excluded.total_invocations,
            total_errors = excluded.total_errors,
            error_rate = excluded.error_rate,
            avg_duration_ms = excluded.avg_duration_ms,
            min_duration_ms = excluded.min_duration_ms,
            max_duration_ms = excluded.max_duration_ms,
            last_invocation = excluded.last_invocation,
            last_updated = excluded.last_updated
    """)

    conn.commit()
    conn.close()

def refresh_compliance_scorecard():
    """Update daily compliance metrics."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO dashboard_compliance_scorecard (
            date, article, total_checks, passes, blocks, warnings, injections, compliance_rate
        )
        SELECT
            DATE(timestamp / 1000, 'unixepoch') as date,
            article,
            COUNT(*) as total_checks,
            SUM(CASE WHEN blocked = 0 AND injection_content IS NULL THEN 1 ELSE 0 END) as passes,
            SUM(CASE WHEN blocked = 1 THEN 1 ELSE 0 END) as blocks,
            SUM(CASE WHEN event_type = 'warning' THEN 1 ELSE 0 END) as warnings,
            SUM(CASE WHEN injection_content IS NOT NULL THEN 1 ELSE 0 END) as injections,
            ROUND(SUM(CASE WHEN blocked = 0 AND injection_content IS NULL THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) as compliance_rate
        FROM constitutional_events
        WHERE article IS NOT NULL
        GROUP BY DATE(timestamp / 1000, 'unixepoch'), article
        ON CONFLICT(date, article) DO UPDATE SET
            total_checks = excluded.total_checks,
            passes = excluded.passes,
            blocks = excluded.blocks,
            warnings = excluded.warnings,
            injections = excluded.injections,
            compliance_rate = excluded.compliance_rate
    """)

    conn.commit()
    conn.close()
```

---

## Frontend Visualization (Chart.js)

```html
<!DOCTYPE html>
<html>
<head>
    <title>CSF NIP Dashboard</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
</head>
<body>
    <h1>Constitutional Compliance Dashboard</h1>

    <!-- Overview Cards -->
    <div class="cards">
        <div class="card">
            <h3>Active Sessions (24h)</h3>
            <p id="sessions">-</p>
        </div>
        <div class="card">
            <h3>Total Events</h3>
            <p id="events">-</p>
        </div>
        <div class="card">
            <h3>Blocks</h3>
            <p id="blocks" style="color: red">-</p>
        </div>
        <div class="card">
            <h3>Avg Hook Duration</h3>
            <p id="duration">-</p>
        </div>
    </div>

    <!-- Charts -->
    <canvas id="complianceTrend"></canvas>
    <canvas id="hookPerformance"></canvas>

    <script>
        // Fetch overview
        fetch('/api/overview')
            .then(r => r.json())
            .then(data => {
                document.getElementById('sessions').textContent = data.active_sessions;
                document.getElementById('events').textContent = data.total_events;
                document.getElementById('blocks').textContent = data.blocks;
                document.getElementById('duration').textContent = Math.round(data.avg_duration) + 'ms';
            });

        // Compliance trend chart
        fetch('/api/compliance/trend')
            .then(r => r.json())
            .then(data => {
                // Group by date, calculate average compliance
                // Render Chart.js line chart
            });

        // Hook performance table
        fetch('/api/hooks/performance?limit=20')
            .then(r => r.json())
            .then(data => {
                // Render table
            });
    </script>
</body>
</html>
```

---

## Success Criteria

- [ ] Schema DDL executable without errors
- [ ] Flask server starts on port 5555
- [ ] All API endpoints return valid JSON
- [ ] Materialized views refresh within 5 seconds
- [ ] Dashboard loads overview panel in <1 second
- [ ] Trace waterfall renders hierarchical spans correctly

---

**Document Status**: Draft - Ready for implementation
**Next Review**: After Week 2 dashboard implementation
