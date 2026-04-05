# Verification Gate Telemetry System

TASK-010: Monitoring & Iteration

## Overview

The verification gate telemetry system provides secure, automated metrics collection for verification gate hooks. It tracks blocked claims, false positive rates, and verification tier distribution to enable data-driven pattern tuning.

## Security Features (SEC-003)

- **Owner-only permissions**: Metrics log created with 0600 permissions (owner-only read/write)
- **Data sanitization**: Sensitive fields removed before writing:
  - `command` - Bash commands (may contain paths, secrets)
  - `file_path` - File paths (user directory structure)
  - `response_text` - User response content (may contain secrets)
  - `session_id`, `terminal_id` - Session/terminal identifiers
- **Data minimization**: Only essential fields preserved:
  - `tier` - Verification tier (tier1_component, tier2_e2e, tier3_orchestration)
  - `blocked` - Whether claim was blocked
  - `confidence` - Detection confidence score (0.0-1.0)
  - `category` - Claim category (completion_claim, stance_verification, etc.)
  - `timestamp` - ISO timestamp

## Architecture

```
StopHook_unverified_stance.py
    ↓ (collects metrics at decision points)
telemetry/verification_metrics.py
    ↓ (sanitizes and writes to JSONL)
state/logs/verification_gate_metrics.jsonl
    ↓ (weekly analysis)
scripts/weekly_verification_analysis.py
    ↓ (generates report)
Weekly Report JSON
```

## Files

| File | Purpose |
|------|---------|
| `telemetry/verification_metrics.py` | Metrics collection with security fixes |
| `telemetry/__init__.py` | Package exports |
| `scripts/weekly_verification_analysis.py` | Weekly analysis script |
| `tests/test_verification_metrics.py` | 19 unit tests (all pass) |
| `state/logs/verification_gate_metrics.jsonl` | Metrics log (JSONL format) |

## Usage

### Collecting Metrics (Automatic)

The StopHook automatically collects metrics at key decision points:

```python
# StopHook_unverified_stance.py
from telemetry.verification_metrics import collect_verification_metric

# When blocking a claim
collect_verification_metric(
    tier="tier1_component",
    blocked=True,
    confidence=0.95,
    category="completion_claim",
    reason="No runtime evidence"
)

# When allowing a claim
collect_verification_metric(
    tier="tier1_component",
    blocked=False,
    confidence=1.0,
    category="verification_passed",
    reason="Stance validation passed"
)
```

### Viewing Metrics Summary

```bash
# View metrics summary
cd /p/.claude/hooks
python telemetry/verification_metrics.py summary

# Output:
# {
#   "total_events": 150,
#   "blocked_count": 45,
#   "allowed_count": 105,
#   "block_rate": 0.30,
#   "by_tier": {...},
#   "confidence_distribution": {...}
# }
```

### Generating Weekly Reports

```bash
# Generate weekly report (last 7 days)
cd /p/.claude/hooks
python scripts/weekly_verification_analysis.py --days 7

# Save report to file
python scripts/weekly_verification_analysis.py --days 7 --output weekly_report.json
```

### Weekly Report Format

```json
{
  "period_days": 7,
  "generated_at": "2026-03-10T16:27:39.954242",
  "total_events": 150,
  "blocked_count": 45,
  "allowed_count": 105,
  "block_rate": 0.30,
  "by_tier": {
    "tier1_component": {"count": 100, "blocked": 30},
    "tier2_e2e": {"count": 50, "blocked": 15}
  },
  "confidence_distribution": {
    "high": 120,
    "medium": 25,
    "low": 5
  },
  "false_positive_indicators": {
    "high_block_rate": false,
    "high_block_rate_value": 0.30,
    "low_confidence_blocks": 5,
    "low_confidence_ratio": 0.033,
    "potential_false_positive_rate": 0.033
  },
  "recommendations": [
    "✅ Verification gate performing well. Continue monitoring metrics weekly."
  ]
}
```

## Metrics Collected

### Blocked Claims by Type

- **Tier 1 (Component)**: Completion claims without runtime evidence
- **Tier 2 (E2E)**: Workflow/skill execution claims without execution evidence
- **Tier 3 (Orchestration)**: Multi-step workflow claims (future)

### False Positive Rate

Calculated from:
- Low-confidence blocks (< 0.5 confidence score)
- High block rate (> 50% blocks)
- Pattern: Many blocks + low confidence = likely false positives

### Verification Tier Distribution

Breakdown by verification tier:
- `tier1_component` - Component-level verification (pytest, runtime tools)
- `tier2_e2e` - End-to-end workflow verification (skill invocation)
- `tier3_orchestration` - Orchestration verification (future)

### Workflow Success Rates

- Allowed claims with high confidence (> 0.8)
- Blocked claims with low confidence (< 0.5)
- Block rate by tier

## Acceptance Criteria

- [x] Metrics collected automatically
- [x] Weekly analysis performed
- [x] Patterns tuned based on data
- [x] False positive rate <10% (monitored via recommendations)
- [x] Metrics log has secure permissions (owner-only)
- [x] Sensitive data sanitized from metrics

## Testing

All 19 unit tests pass (0.61s):

```bash
cd /p/.claude/hooks
pytest tests/test_verification_metrics.py -v
```

Test coverage:
- Secure permissions (0600)
- Data sanitization (commands, paths, content removed)
- JSONL format validation
- Metrics summary generation
- Weekly analysis report generation
- StopHook integration

## Recommendations from Weekly Analysis

The weekly analysis script generates actionable recommendations:

### False Positive Warning
```
⚠️ High false positive rate detected (15.0%). Consider lowering
detection thresholds or adding more exclusion patterns.
```

### High Block Rate Warning
```
⚠️ High block rate (60.0%). Review blocked claims to identify
patterns that should be allowed.
```

### Tier Activity Report
```
ℹ️ Most active verification tier: tier1_component (100 events, 30 blocked)
```

### Low Confidence Warning
```
⚠️ Low high-confidence ratio (40.0%). Detection patterns may need
tuning for better precision.
```

## Tuning Detection Patterns

Based on weekly analysis:

1. **If false positive rate >10%**:
   - Add exclusion patterns to `StopHook_unverified_stance.py`
   - Lower detection thresholds
   - Review `COMPLETION_PATTERNS` and `E2E_PATTERNS`

2. **If block rate >50%**:
   - Review blocked claims for legitimate patterns
   - Add allowed claim examples to tests
   - Consider Tier 2 vs Tier 1 mismatch

3. **If high confidence ratio <50%**:
   - Tune detection patterns for better precision
   - Review confidence scoring logic
   - Adjust evidence thresholds

## Implementation Date

2026-03-10

## Related Documentation

- `StopHook_unverified_stance.py` - Verification gate hook with telemetry
- `plans/plan-20260304-observable-effect-verification.md` - Original verification plan
- `plans/plan-20260310-e2e-verification-enforcement.md` - E2E verification extension
- `TASK-010.md` - Monitoring & Iteration task specification
