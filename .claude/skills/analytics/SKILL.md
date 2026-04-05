---
name: analytics
description: Constitutionally-compliant on-demand analytics for CSF NIP Phase 2 Load Testing Optimization System
version: "1.0.0"
status: stable
category: analytics
triggers:
  - /analytics
  - "system analytics"
  - "performance monitoring"
  - "metrics collection"
aliases:
  - /analytics

suggest:
  - /nse
  - /analyze
  - /research
---

# Production Analytics CLI Command

## Purpose

Constitutionally-compliant on-demand analytics for CSF NIP Phase 2 Load Testing Optimization System.

## Project Context

### Constitution/Constraints
- **No Background Services** - All analytics are user-initiated only
- **Resource Safety Limits** - CPU 95%, Memory 2GB, Duration 10min enforced
- **Solo Developer Optimized** - Minimal overhead, maximum value
- **Evidence-Based** - All analytics based on verifiable metrics

### Technical Context
- SQLite database: `P:/__csf/data/analytics.db`
- 30-day retention default
- Supports dashboard, collect, query, export, health commands

### Architecture Alignment
- Part of CSF NIP Phase 2 system
- Integrates with load testing optimization
- Supports system metrics (cpu_usage, memory_usage, disk_usage)
- Tracks Phase 2 metrics (phase2_health, phase2_status, cpu_generator, phase2_error)

## Your Workflow

1. **Dashboard** - Show static or interactive dashboard with current metrics
2. **Collect** - Gather current system metrics with optional purpose tag
3. **Query** - Query metrics with time filters (--hours, --days, --limit) and aggregation (--avg, --sum, --min, --max)
4. **Export** - Export data to JSON for external analysis
5. **Health** - Show comprehensive system health report

## Validation Rules

### Prohibited Actions
- **NEVER run background services** - all commands must be user-initiated
- **NEVER exceed resource limits** - CPU 95%, Memory 2GB, Duration 10min
- **NEVER claim metrics without verification** - query actual database

### Required Output
- Show actual query results from analytics.db
- Include timestamps and metric values
- Flag when no data is available

## Quick Start

```bash
# Show static dashboard
/analytics --dashboard

# Collect current system metrics
/analytics --collect

# Query CPU usage for last 24 hours
/analytics --query "cpu_usage --hours 24"

# Show system health
/analytics --health
```

## Constitutional Compliance

- No Background Services - All analytics operations are user-initiated only
- Resource Safety Limits - CPU 95%, Memory 2GB, Duration 10min enforced
- Solo Developer Optimized - Minimal overhead, maximum value
- Evidence-Based - All analytics based on verifiable metrics

## Core Commands

### Dashboard

```bash
/analytics --dashboard           # Static dashboard
/analytics --dashboard --interactive  # Interactive (refresh on Enter)
```

### Data Collection

```bash
/analytics --collect                                    # Collect current metrics
/analytics --collect --purpose "performance_validation"  # With purpose
```

### Data Querying

```bash
# Query CPU usage for last 24 hours
/analytics --query "cpu_usage --hours 24"

# Query memory usage with limit
/analytics --query "memory_usage --limit 100"

# Query specific component
/analytics --query "phase2_health --component integration_system"

# Aggregated queries
/analytics --query "cpu_usage --hours 1 --avg"
/analytics --query "memory_usage --sum --hours 12"
```

### Data Export

```bash
# Export last 24 hours of data
/analytics --export analytics_export.json
```

### System Health

```bash
/analytics --health   # Comprehensive system health
/analytics --status   # Analytics system status
```

## Query Language

### Time Filters
- `--hours <N>` - Last N hours
- `--days <N>` - Last N days
- `--limit <N>` - Maximum records to return

### Data Filters
- `--type <metric_type>` - Filter by metric type
- `--component <component>` - Filter by component name

### Aggregation
- `--avg` - Average values
- `--sum` - Sum values
- `--min` - Minimum values
- `--max` - Maximum values

## Available Metrics

### System Metrics
- `cpu_usage` - CPU utilization percentage
- `memory_usage` - Memory utilization percentage
- `disk_usage` - Disk utilization percentage

### Phase 2 Metrics
- `phase2_health` - Phase 2 integration system health score
- `phase2_status` - Phase 2 component availability
- `cpu_generator` - CPU load generator performance metrics
- `phase2_error` - Phase 2 system errors

## Data Storage

Analytics data is stored in SQLite database: `P:/__csf/data/analytics.db`

Retention: 30 days default
