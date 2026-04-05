# Graph-of-Thought (GoT) Integration

## Overview

/q integrates Graph-of-Thought (GoT) reasoning for enhanced requirement constraint analysis.

## What This Does

Automatically extract and categorize requirement constraints from strategic findings to discover hidden relationships between architectural requirements and constraints.

## Node Types Extracted

- **Requirements**: Functional needs like "Must authenticate users", "API response < 200ms"
- **Constraints**: Limitations like "Must use PostgreSQL", "Budget < $1000", "Timeline < 2 weeks"
- **Ideas**: Design approaches like "Use Redis for caching", "Implement OAuth 2.0"
- **Risks**: Strategic concerns like "OAuth latency", "Cache complexity", "Migration risk"
- **Components**: System boundaries like "Service A", "Database B", "Cache C"
- **Data flows**: Communication paths like "API → Service → Database"

## Relationship Types Detected

- **Supports**: One requirement enables another (e.g., "Use Redis" supports "Session caching")
- **Contradicts**: One requirement conflicts with another (e.g., "Must use JWT" contradicts "Stateful sessions")
- **Depends**: One requirement requires another (e.g., "OAuth integration" depends on "User service")
- **Unrelated**: No direct relationship between requirements

## Integration Point

Q3 (Strategic Analysis) phase:
```
Q3: Strategic Analysis
  ↓
Normalize findings from all subagents
  ↓
GotPlanner extracts constraint nodes from findings
  ↓
GotEdgeAnalyzer detects relationships between constraints
  ↓
Cycle detection warns about circular requirement dependencies
  ↓
Enhanced strategic health assessment with constraint analysis
```

## Example Output

```
GoT Analysis: Requirement Constraints
======================================

Nodes extracted: 8
  - Requirements: 2 (Must authenticate users, API response < 200ms)
  - Constraints: 3 (Must use PostgreSQL, Budget < $1000, Timeline < 2 weeks)
  - Ideas: 2 (Use Redis for caching, Implement OAuth 2.0)
  - Risks: 1 (OAuth latency concern)

Relationships detected: 5
  - Supports: 3 pairs (Redis → Caching, OAuth → Security, etc.)
  - Contradicts: 1 pair (JWT vs Stateful sessions - CONFLICT)
  - Depends: 1 pair (OAuth depends on User service)

Cycles detected: 0

Strategic Health: CONCERNING
Reason: Constraint conflict detected (JWT vs Stateful sessions)
```

## What This Catches

- Hidden requirement conflicts that would cause implementation deadlock
- Circular dependencies in requirements
- Missing prerequisite requirements
- Risk amplification when multiple risky constraints combine

## Opt-Out Flag

Disable GoT enhancement:
```bash
export Q_NO_GOT=true
```
