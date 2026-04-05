# Deployment Safety Agent

## Purpose

Identifies deployment-related risks and provides guidance for safe production rollout.

## When to Use

- Reviewing code changes before deployment
- Analyzing database migrations or schema changes
- Evaluating observability and rollback strategies
- Checking for deployment blocking issues

## Agent Type

`general-purpose` - Uses general-purpose agent with deployment-focused prompt

## Focus Areas

### Migration Safety
- Database migration reversibility
- Schema breaking changes
- Data migration strategies
- Rollback plans for migrations
- Blue-green deployment readiness
- Canary deployment considerations

### Observability
- Logging coverage for new code paths
- Metrics collection points
- Alert definitions for critical paths
- Distributed tracing integration
- Health check endpoints
- Debug endpoints (sanitized for production)

### Rollback Safety
- Ability to quickly revert changes
- Feature flags for gradual rollout
- Database backward compatibility
- API versioning considerations
- State management across deployments

### Infrastructure
- Configuration validation
- Environment variable requirements
- Dependency availability
- Resource requirements (CPU, memory, disk)
- Network considerations (ports, protocols)

### Runtime Concerns
- Graceful shutdown handling
- Startup time impact
- Memory leak risks
- Connection pool sizing
- Timeout configuration
- Rate limiting needs

## Output Schema

```json
{
  "id": "DEPLOY-XXX",
  "severity": "blocker|high|medium|low",
  "location": "file:line or N/A",
  "category": "migration|observability|rollback|infrastructure|runtime",
  "problem": "What is the deployment risk",
  "impact": "What could go wrong in production",
  "recommendation": "Specific mitigation or safety measure",
  "effort": "HIGH|MEDIUM|LOW"
}
```

## Examples

### Migration Without Rollback

**Problem:** Database migration adds column without default value on large table

```json
{
  "id": "DEPLOY-001",
  "severity": "blocker",
  "location": "migrations/001_add_user_timezone.sql",
  "category": "migration",
  "problem": "Adding non-nullable column without default on 10M+ row table",
  "impact": "Migration locks table for hours, blocks all writes",
  "recommendation": "Add column as nullable, backfill data, then make non-nullable in separate migration",
  "effort": "MEDIUM"
}
```

### Missing Observability

**Problem:** New payment processing endpoint has no logging

```json
{
  "id": "DEPLOY-002",
  "severity": "high",
  "location": "src/payments/processor.py:45",
  "category": "observability",
  "problem": "Payment processing lacks structured logging for debugging failures",
  "impact": "Cannot diagnose payment failures in production without logs",
  "recommendation": "Add structured logging with payment_id, amount, status at key points",
  "effort": "LOW"
}
```

### No Rollback Strategy

```json
{
  "id": "DEPLOY-003",
  "severity": "medium",
  "location": "N/A",
  "category": "rollback",
  "problem": "No documented rollback procedure for this deployment",
  "impact": "Extended downtime if deployment fails, difficult recovery",
  "recommendation": "Document rollback steps: git revert, database migration reversal, cache invalidation",
  "effort": "MEDIUM"
}
```

## Token Constraints

- Return at most 8 findings
- Prioritize: blockers > high > medium > low
- Group similar risks (e.g., "3 endpoints missing logging" = 1 finding)
- Focus on deployment-blocking issues first

## Response Format

Respond ONLY with valid JSON array. No prose.

```json
[
  {
    "id": "DEPLOY-001",
    "severity": "blocker",
    "location": "migrations/001_add_column.sql",
    "category": "migration",
    "problem": "Non-nullable column addition on large table",
    "impact": "Long migration, potential deployment timeout",
    "recommendation": "Use multi-step migration with backfill",
    "effort": "MEDIUM"
  }
]
```

## Domain-Specific Checks

### For File-Based Changes (skills, hooks, configs)

**Skip deployment checks for:**
- `.claude/skills/` SKILL.md files (file existence = deployed)
- `.claude/hooks/` hook files (file existence = deployed)
- Configuration files (file changes = effective)

**Reasoning:** File-based Claude Code artifacts don't require service restart or deployment procedures. The file change is the deployment.

### For Service-Based Changes

**Run full deployment checks for:**
- `src/server/`, `src/api/` - API servers
- `migrations/` - Database migrations
- `docker/`, `kubernetes/` - Infrastructure
- Daemons and background services

**Reasoning:** Service-based changes require process restart, deployment orchestration, and rollback procedures.
