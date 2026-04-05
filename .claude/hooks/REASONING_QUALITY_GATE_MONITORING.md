# Self-Reflection Quality Gate Monitoring

## Integration with /main and /hook-audit

The self-reflection quality gate monitoring system integrates seamlessly with both `/main` and `/hook-audit` for centralized visibility.

## Quick Start

### Standalone Usage
```bash
# Show statistics
python P:/.claude/hooks/self_reflection_monitor.py --stats

# Health check
python P:/.claude/hooks/self_reflection_monitor.py --health

# Recent entries
python P:/.claude/hooks/self_reflection_monitor.py --recent 20
```

### Integration with /main
```bash
/main health --include self_reflection
```
This will run the health check as part of the overall system health report.

### Integration with /hook-audit
```bash
/hook-audit Stop_self_reflection --detail
```
This will include quality gate statistics in the hook audit report.

## Statistics Tracked

| Metric | Description |
|--------|-------------|
| **Total evaluations** | Number of times quality gate triggered |
| **Passed** | Responses that passed quality gate (0 issues) |
| **Issues found** | Responses that failed quality gate (≥1 issues) |
| **Pass rate** | Percentage of responses that passed |
| **Average response length** | Mean character count of evaluated responses |
| **Result distribution** | Breakdown by result type |

## Health Check Thresholds

| Condition | Status | Action |
|-----------|--------|--------|
| No activity (0 evaluations) | ⚠️ Warning | Verify hook registration |
| 100% failure rate | 🚨 Critical | Quality threshold too sensitive |
| 100% pass rate | ⚠️ Warning | Quality threshold too lenient |
| 5-95% pass rate | ✅ Healthy | Normal operation |

## Current Configuration

**Quality gate threshold**: `<1 issue` (fail on ANY issue)

This means the quality gate will trigger improvements for any detected issue:
- Logical gaps
- Overconfidence
- Contradictions
- Missing alternatives

## Log Location

```
P:/packages/reasoning/hook_usage.log
```

Each log entry contains:
```json
{
  "timestamp": 1773203440.8783755,
  "hook": "Stop_self_reflection",
  "response_length": 237,
  "result": "passed"
}
```

## Debug Mode

Enable debug mode to see real-time statistics:
```bash
export SELF_REFLECTION_DEBUG=true
```

Debug output includes:
- Filter statistics (applied/skipped)
- Reason for skipping
- Quality gate results

## Performance Impact

- **Overhead**: <1ms for keyword matching
- **Quality check**: <200ms for critique engine
- **Logging**: Synchronous write (minimal impact)

## Troubleshooting

### No Activity Detected

If the health check shows no activity:
1. Verify hook is registered in Stop router:
   ```bash
   grep -r "self_reflection" P:/.claude/hooks/Stop.py
   ```
2. Check hook file exists:
   ```bash
   ls -la P:/.claude/hooks/Stop_self_reflection.py
   ```
3. Verify reasoning package is accessible:
   ```bash
   python -c "from reasoning.modes.sequential import SequentialMode; print('OK')"
   ```

### 100% Failure Rate

If all responses are failing:
1. Review recent logs for false positives:
   ```bash
   python P:/.claude/hooks/self_reflection_monitor.py --recent 50
   ```
2. Consider adjusting threshold in `sequential.py`:
   - More lenient: `return total_issues < 2` (fail on 2+ issues)
   - Even more lenient: `return total_issues < 3` (fail on 3+ issues)

### 100% Pass Rate

If all responses are passing:
1. Current threshold may be appropriate (responses are high quality)
2. Or critique patterns may not be detecting issues
3. Check critique patterns in `sequential.py`:
   - `_detect_logical_gaps()`
   - `_detect_overconfidence()`
   - `_detect_contradictions()`
   - `_detect_missing_alternatives()`

## Integration Examples

### /main Integration
```python
# In /main health check
def check_system_health():
    # ... existing checks ...

    # Self-reflection quality gate
    result = subprocess.run(
        ["python", "P:/.claude/hooks/self_reflection_monitor.py", "--health"],
        capture_output=True
    )
    print(result.stdout)

    return overall_status
```

### /hook-audit Integration
```python
# In /hook-audit Stop hook analysis
def audit_stop_hook(hook_name):
    if hook_name == "self_reflection":
        # Show statistics
        result = subprocess.run(
            ["python", "P:/.claude/hooks/self_reflection_monitor.py", "--stats"],
            capture_output=True
        )
        return result.stdout

    # ... other hook audits ...
```

## Related Systems

- **Stop_reflect_integration.py**: Automatic signal extraction for /reflect skill
- **reflect_performance_monitor.py**: Performance monitoring for reflect signal extraction
- **hook_usage.log**: Central log file for all Stop hook activity

## See Also

- [Stop Hook Architecture](P:\.claude\hooks\CLAUDE.md)
- [Reasoning Package Documentation](P:/packages/reasoning/README.md)
- [Self-Reflection Implementation](P:/packages/reasoning/reasoning/modes/sequential.py)
