# Example Observability Artifacts for PRD Verifier

This directory contains example observability artifacts showing how the PRD Verifier integrates with the Ralph Loop observability system.

## Decision Log Example

### File: `.claude/loop/terminals/example_terminal/decision.log`

```json
{"terminal_id": "term_abc123", "event": "LOOP_START", "payload": {"plan": "Implement authentication system", "total_tasks": 5}, "timestamp": "2026-03-15T14:00:00.000000"}
{"terminal_id": "term_abc123", "event": "PLAN_PARSED", "payload": {"tasks_found": 5, "task_ids": ["t1", "t2", "t3", "t4", "t5"]}, "timestamp": "2026-03-15T14:00:01.000000"}
{"terminal_id": "term_abc123", "event": "ITERATION_START", "payload": {"iteration_number": 1}, "timestamp": "2026-03-15T14:00:02.000000"}
{"terminal_id": "term_abc123", "event": "TASK_START", "payload": {"task_id": "t1", "description": "Setup database schema"}, "timestamp": "2026-03-15T14:00:03.000000"}
{"terminal_id": "term_abc123", "event": "TASK_COMPLETE", "payload": {"task_id": "t1", "duration_seconds": 120, "success": true}, "timestamp": "2026-03-15T14:02:03.000000"}
{"terminal_id": "term_abc123", "event": "TASK_START", "payload": {"task_id": "t2", "description": "Implement user model"}, "timestamp": "2026-03-15T14:02:04.000000"}
{"terminal_id": "term_abc123", "event": "TASK_COMPLETE", "payload": {"task_id": "t2", "duration_seconds": 180, "success": true}, "timestamp": "2026-03-15T14:05:04.000000"}
{"terminal_id": "term_abc123", "event": "TASK_START", "payload": {"task_id": "t3", "description": "Create authentication endpoint"}, "timestamp": "2026-03-15T14:05:05.000000"}
{"terminal_id": "term_abc123", "event": "TASK_COMPLETE", "payload": {"task_id": "t3", "duration_seconds": 240, "success": true}, "timestamp": "2026-03-15T14:09:05.000000"}
{"terminal_id": "term_abc123", "event": "TASK_START", "payload": {"task_id": "t4", "description": "Write unit tests"}, "timestamp": "2026-03-15T14:09:06.000000"}
{"terminal_id": "term_abc123", "event": "TASK_COMPLETE", "payload": {"task_id": "t4", "duration_seconds": 90, "success": true}, "timestamp": "2026-03-15T14:10:36.000000"}
{"terminal_id": "term_abc123", "event": "TASK_START", "payload": {"task_id": "t5", "description": "Update documentation"}, "timestamp": "2026-03-15T14:10:37.000000"}
{"terminal_id": "term_abc123", "event": "TASK_COMPLETE", "payload": {"task_id": "t5", "duration_seconds": 60, "success": true}, "timestamp": "2026-03-15T14:11:37.000000"}
{"terminal_id": "term_abc123", "event": "ITERATION_COMPLETE", "payload": {"iteration_number": 1, "tasks_completed_this_iteration": 5, "all_tasks_complete": true}, "timestamp": "2026-03-15T14:11:38.000000"}
{"terminal_id": "term_abc123", "event": "VERIFICATION_TRIGGERED", "payload": {"reason": "all_tasks_complete", "verifier_skill": "prd-verifier"}, "timestamp": "2026-03-15T14:11:39.000000"}
{"terminal_id": "term_abc123", "event": "VERIFICATION_START", "payload": {"verifier": "prd-verifier", "plan_path": "plan.md", "prd_path": "PRD.md"}, "timestamp": "2026-03-15T14:11:40.000000"}
{"terminal_id": "term_abc123", "event": "VERIFICATION_PRD_COVERAGE_CHECK", "payload": {"total_requirements": 12, "covered_requirements": 11, "coverage_percentage": 92, "missing_requirements": ["Multi-factor authentication"]}, "timestamp": "2026-03-15T14:11:41.000000"}
{"terminal_id": "term_abc123", "event": "VERIFICATION_SPEC_COMPLIANCE_CHECK", "payload": {"total_specs": 8, "compliant_specs": 8, "compliance_percentage": 100, "deviations": []}, "timestamp": "2026-03-15T14:11:42.000000"}
{"terminal_id": "term_abc123", "event": "VERIFICATION_QUALITY_CHECK", "payload": {"quality_score": 9, "user_concerns": [], "issues": [], "recommendations": ["Add integration tests for authentication flow"]}, "timestamp": "2026-03-15T14:11:43.000000"}
{"terminal_id": "term_abc123", "event": "VERIFICATION_COMPLETE", "payload": {"passed": true, "report_path": ".claude/loop/verification-report.md", "duration_seconds": 3}, "timestamp": "2026-03-15T14:11:43.000000"}
{"terminal_id": "term_abc123", "event": "LOOP_EXIT", "payload": {"reason": "all_tasks_complete_and_verified", "total_iterations": 1, "final_score": 100}, "timestamp": "2026-03-15T14:11:44.000000"}
```

## Metrics File Example

### File: `.claude/loop/terminals/example_terminal/loop_metrics.json`

```json
{
  "terminal_id": "term_abc123",
  "start_time": "2026-03-15T14:00:00.000000",
  "end_time": "2026-03-15T14:11:44.000000",
  "iterations": 1,
  "tasks_completed": 5,
  "total_tasks": 5,
  "exit_reason": "all_tasks_complete_and_verified",
  "last_activity": "2026-03-15T14:11:44.000000",
  "current_phase": "complete",
  "error_count": 0,
  "verification_runs": 1,
  "verification_passes": 1,
  "verification_failures": 0,
  "last_verification": "2026-03-15T14:11:43.000000",
  "verification_passed": true,
  "total_task_duration_seconds": 690,
  "average_task_duration_seconds": 138
}
```

## Verification Report Example

### File: `.claude/loop/verification-report.md`

```markdown
# PRD Verification Report

**Generated**: 2026-03-15T14:11:43.000000
**Terminal ID**: term_abc123
**Status**: ✅ **PASS**

## Summary

The implementation has been verified against PRD requirements and specifications. All verification dimensions have passed the required thresholds.

| Dimension | Status | Score | Threshold |
|-----------|--------|-------|-----------|
| PRD Coverage | ✅ PASS | 92% | ≥80% |
| Spec Compliance | ✅ PASS | 100% | ≥80% |
| Implementation Quality | ✅ PASS | 9/10 | ≥7/10 |

## PRD Coverage

**Coverage**: 92% (11/12 requirements met)

### Missing Requirements
1. **Multi-factor authentication** - Not yet implemented

### Requirements Met
- ✅ User authentication with email/password
- ✅ Password hashing with bcrypt
- ✅ Session management
- ✅ JWT token generation
- ✅ Password reset flow
- ✅ User registration
- ✅ Login/logout endpoints
- ✅ Protected routes
- ✅ Input validation
- ✅ Error handling
- ✅ Unit tests for authentication

## Spec Compliance

**Compliance**: 100% (8/8 specifications met)

### Verified Specifications
- ✅ API endpoint: POST /api/auth/login
- ✅ API endpoint: POST /api/auth/register
- ✅ API endpoint: POST /api/auth/logout
- ✅ API endpoint: POST /api/auth/reset-password
- ✅ Data model: User entity with email, password_hash, created_at
- ✅ Security: Password hashing with bcrypt (cost factor 12)
- ✅ Security: JWT tokens with 24-hour expiration
- ✅ Architecture: Stateless authentication with JWT

### Deviations
None detected

## Implementation Quality

**Quality Score**: 9/10

### User Concerns Detected
No critical issues or concerns detected in recent chat history.

### Issues Found
None

### Recommendations
1. Add integration tests for authentication flow
2. Consider adding rate limiting to login endpoint
3. Document API endpoints in OpenAPI format

## Detailed Findings

### PRD Coverage Analysis
- Total requirements extracted: 12
- Requirements met: 11
- Requirements missing: 1
- Coverage percentage: 92%
- Status: **PASS** (threshold: ≥80%)

### Spec Compliance Analysis
- Total specifications: 8
- Specifications compliant: 8
- Deviations found: 0
- Compliance percentage: 100%
- Status: **PASS** (threshold: ≥80%)

### Quality Metrics
- Completion score: 9/10
- User concerns: 0
- Blockers: 0
- Issues: 0
- Recommendations: 3
- Status: **PASS** (threshold: ≥7/10, no critical issues)
```

## Key Observability Integration Points

### 1. Verification Triggered Event

Logged when verification is triggered by the loop policy:

```python
from scripts.loop_observability import log_decision

log_decision(terminal_id, "VERIFICATION_TRIGGERED", {
    "reason": "all_tasks_complete",
    "verifier_skill": "prd-verifier"
})
```

### 2. Verification Start Event

Logged when verification begins:

```python
log_decision(terminal_id, "VERIFICATION_START", {
    "verifier": "prd-verifier",
    "plan_path": "plan.md",
    "prd_path": "PRD.md"
})
```

### 3. Verification Progress Events

Logged for each verification dimension:

```python
log_decision(terminal_id, "VERIFICATION_PRD_COVERAGE_CHECK", {
    "total_requirements": 12,
    "covered_requirements": 11,
    "coverage_percentage": 92,
    "missing_requirements": ["Multi-factor authentication"]
})

log_decision(terminal_id, "VERIFICATION_SPEC_COMPLIANCE_CHECK", {
    "total_specs": 8,
    "compliant_specs": 8,
    "compliance_percentage": 100,
    "deviations": []
})

log_decision(terminal_id, "VERIFICATION_QUALITY_CHECK", {
    "quality_score": 9,
    "user_concerns": [],
    "issues": [],
    "recommendations": ["Add integration tests for authentication flow"]
})
```

### 4. Verification Complete Event

Logged when verification finishes:

```python
log_decision(terminal_id, "VERIFICATION_COMPLETE", {
    "passed": True,
    "report_path": ".claude/loop/verification-report.md",
    "duration_seconds": 3
})
```

### 5. Metrics Update

Update metrics with verification results:

```python
from scripts.loop_observability import update_metrics

update_metrics(terminal_id, {
    "verification_runs": 1,
    "verification_passes": 1,
    "verification_failures": 0,
    "last_verification": datetime.now().isoformat(),
    "verification_passed": True
})
```

## Query Examples

### Find All Verification Events

```bash
# Get all verification events for a terminal
grep '"event": "VERIFICATION' .claude/loop/terminals/term_abc123/decision.log

# Count verification runs
grep -c '"event": "VERIFICATION_COMPLETE"' .claude/loop/terminals/term_abc123/decision.log
```

### Analyze Verification Outcomes

```python
import json
from pathlib import Path

def analyze_verifications(terminal_id: str):
    """Analyze verification outcomes from decision log."""
    log_file = Path(f".claude/loop/terminals/{terminal_id}/decision.log")

    verification_events = []
    for line in log_file.read_text().strip().split("\n"):
        entry = json.loads(line)
        if "VERIFICATION" in entry["event"]:
            verification_events.append(entry)

    # Extract completion events
    completions = [e for e in verification_events if e["event"] == "VERIFICATION_COMPLETE"]

    return {
        "total_verifications": len(completions),
        "passed_count": sum(1 for c in completions if c["payload"]["passed"]),
        "failed_count": sum(1 for c in completions if not c["payload"]["passed"]),
        "average_duration": sum(c["payload"]["duration_seconds"] for c in completions) / len(completions) if completions else 0
    }
```

### Track Verification Trends

```python
def track_verification_trends(terminal_id: str):
    """Track verification outcomes over time."""
    log_file = Path(f".claude/loop/terminals/{terminal_id}/decision.log")

    completions = []
    for line in log_file.read_text().strip().split("\n"):
        entry = json.loads(line)
        if entry["event"] == "VERIFICATION_COMPLETE":
            completions.append({
                "timestamp": entry["timestamp"],
                "passed": entry["payload"]["passed"],
                "duration": entry["payload"]["duration_seconds"]
            })

    return completions
```

## Best Practices

### 1. Granular Progress Tracking

Log events for each verification dimension to enable detailed analysis:

```python
# Good - granular tracking
log_decision(terminal_id, "VERIFICATION_PRD_COVERAGE_CHECK", {...})
log_decision(terminal_id, "VERIFICATION_SPEC_COMPLIANCE_CHECK", {...})
log_decision(terminal_id, "VERIFICATION_QUALITY_CHECK", {...})

# Avoid - only logging start and complete
log_decision(terminal_id, "VERIFICATION_START", {...})
log_decision(terminal_id, "VERIFICATION_COMPLETE", {...})
```

### 2. Context-Rich Payloads

Include all relevant context in event payloads:

```python
# Good - rich context
log_decision(terminal_id, "VERIFICATION_PRD_COVERAGE_CHECK", {
    "total_requirements": 12,
    "covered_requirements": 11,
    "coverage_percentage": 92,
    "missing_requirements": ["Multi-factor authentication"],
    "threshold": 80,
    "passed": True
})

# Avoid - minimal context
log_decision(terminal_id, "VERIFICATION_PRD_COVERAGE_CHECK", {
    "passed": True
})
```

### 3. Consistent Timestamps

Use ISO format timestamps for all events:

```python
from datetime import datetime

timestamp = datetime.now().isoformat()
```

### 4. Metrics Updates

Update metrics atomically after verification:

```python
update_metrics(terminal_id, {
    "verification_runs": 1,  # Increment
    "verification_passes": 1 if result.passed else 0,  # Conditional increment
    "last_verification": datetime.now().isoformat(),
    "verification_passed": result.passed  # Set current state
})
```

## Troubleshooting

### Verification Not Triggering

**Symptom**: No VERIFICATION_TRIGGERED event in decision log

**Diagnosis**:
```python
# Check if all tasks are complete
metrics = get_terminal_metrics(terminal_id)
print(f"Tasks completed: {metrics['tasks_completed']}/{metrics['total_tasks']}")
print(f"All complete: {metrics['tasks_completed'] == metrics['total_tasks']}")
```

### Verification Failing

**Symptom**: VERIFICATION_COMPLETE with `passed: false`

**Diagnosis**:
```python
# Find the verification report
import json
from pathlib import Path

log_file = Path(f".claude/loop/terminals/{terminal_id}/decision.log")
for line in log_file.read_text().strip().split("\n"):
    entry = json.loads(line)
    if entry["event"] == "VERIFICATION_COMPLETE":
        report_path = entry["payload"]["report_path"]
        print(f"Report: {report_path}")
        print(Path(report_path).read_text())
```

### Metrics Not Updating

**Symptom**: `verification_runs` not incrementing

**Diagnosis**:
```python
# Check if metrics file exists and is valid
state_dir = get_terminal_state_dir(terminal_id)
metrics_file = state_dir / "loop_metrics.json"

if not metrics_file.exists():
    print("Metrics file does not exist")
else:
    try:
        with metrics_file.open() as f:
            metrics = json.load(f)
            print(f"Verification runs: {metrics.get('verification_runs', 0)}")
    except json.JSONDecodeError as e:
        print(f"Metrics file corrupted: {e}")
```
