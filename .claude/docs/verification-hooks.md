# Verification Hooks Documentation

## Overview

The verification claim grounding system provides per-terminal, evidence-based validation of claims made by AI responses. This prevents the AI from stating hypotheses as confirmed facts without verification evidence from tool output.

## Architecture

The system consists of three main components:

1. **Claim Detection** (`anti_sycophancy/hypothesis_as_fact_detector.py`)
   - Pattern-based detection of confident claims
   - Supports ABSENCE, PRESENCE, RULE, and SYSTEM claim types
   - Hedging detection to allow tentative statements

2. **Verification Engine** (`verification/claims.py`, `verification/engine.py`)
   - Unified claim representation via `Claim` dataclass
   - Entity matching against tool events
   - Three verdicts: SUPPORTED (confirmed), REFUTED (contradicted), SILENT (no evidence)

3. **Stop Hook Enforcement** (`Stop_hypothesis_as_fact_gate.py`)
   - Blocks or warns based on claim confidence and evidence
   - Terminal-scoped evidence filtering (multi-terminal safe)
   - Structured JSONL logging for observability

## Environment Variables

### Gate Control

| Variable | Default | Description |
|----------|---------|-------------|
| `HYPOTHESIS_AS_FACT_GATE_ENABLED` | `true` | Enable/disable the gate globally |
| `HYPOTHESIS_AS_FACT_GATE_MODE` | `warn` | Enforcement mode: `"warn"` (advisory) or `"block"` (hard blocking) |

### Evidence Filtering

| Variable | Default | Description |
|----------|---------|-------------|
| `VERIFICATION_USE_TURN_SCOPING` | `false` | Enable turn-scoped event filtering (Phase 3 feature) |

### Logging

| Variable | Default | Description |
|----------|---------|-------------|
| `VERIFICATION_LOG_ENABLED` | `true` | Enable structured JSONL logging |
| `VERIFICATION_LOG_PATH` | `state/logs/hypothesis_as_fact_gate.jsonl` | Path to log file |

## Rollback Procedure

### Immediate Rollback (Emergency)

If the gate is causing false positives or blocking legitimate work:

**Option 1: Disable the gate entirely**
```bash
# Set environment variable
export HYPOTHESIS_AS_FACT_GATE_ENABLED=false

# Or add to .claude/settings.json
{
  "env": {
    "HYPOTHESIS_AS_FACT_GATE_ENABLED": "false"
  }
}
```

**Option 2: Switch to advisory mode**
```bash
# Already in warn mode by default, but to confirm:
export HYPOTHESIS_AS_FACT_GATE_MODE=warn
```

### Tuning False Positives

If the gate is producing false positives, use the log data to tune patterns:

1. **Review log entries**
   ```bash
   # View recent blocks/warns
   tail -20 .claude/hooks/state/logs/hypothesis_as_fact_gate.jsonl | jq

   # Count by claim type
   cat .claude/hooks/state/logs/hypothesis_as_fact_gate.jsonl | \
     jq -r '.claim_type' | sort | uniq -c
   ```

2. **Identify patterns**
   ```bash
   # Find most common targets
   cat .claude/hooks/state/logs/hypothesis_as_fact_gate.jsonl | \
     jq -r '.targets[]' | sort | uniq -c | sort -rn | head -10
   ```

3. **Adjust detector patterns**
   - Edit `anti_sycophancy/hypothesis_as_fact_detector.py`
   - Update `ENTITY_ABSENCE_PATTERNS` or `ENTITY_PRESENCE_PATTERNS`
   - Add exclusion patterns for false positive cases

### Partial Rollback (Feature-Specific)

If only specific features are causing issues:

**Disable turn scoping** (if enabled)
```bash
export VERIFICATION_USE_TURN_SCOPING=false
```

**Disable logging** (if performance issues)
```bash
export VERIFICATION_LOG_ENABLED=false
```

## Conservative Defaults

The gate ships with conservative defaults to minimize disruption:

- **Enabled**: `true` (active by default for production safety)
- **Mode**: `warn` (advisory mode - warns before blocking)
- **Turn scoping**: `false` (terminal-scoped only, not turn-scoped)

This default configuration:
- ✅ Catches ungrounded claims (warns user)
- ✅ Allows manual override (user can proceed)
- ✅ Collects tuning data (logs all warn events)
- ❌ Does not block automatically (requires mode change to "block")

## Production Deployment

### Step 1: Deploy in WARN Mode (Default)

The gate ships in warn mode. Monitor logs for false positives:

```bash
# Count warnings per day
cat .claude/hooks/state/logs/hypothesis_as_fact_gate.jsonl | \
  jq -r 'select(.outcome == "warn") | .outcome' | wc -l

# View sample warnings
cat .claude/hooks/state/logs/hypothesis_as_fact_gate.jsonl | \
  jq -r 'select(.outcome == "warn")' | head -5
```

### Step 2: Tune Patterns (If Needed)

If false positive rate > 10%, adjust patterns in `hypothesis_as_fact_detector.py`.

### Step 3: Switch to BLOCK Mode (When Ready)

Once false positive rate is acceptable (< 5%):

```bash
# Update settings.json
{
  "env": {
    "HYPOTHESIS_AS_FACT_GATE_MODE": "block"
  }
}
```

### Step 4: Monitor Block Rate

Track block rate to ensure system remains usable:

```bash
# Daily block rate
cat .claude/hooks/state/logs/hypothesis_as_fact_gate.jsonl | \
  jq -r 'select(.outcome == "block") | .outcome' | wc -l
```

## Troubleshooting

### Gate Not Firing

If the gate is not catching ungrounded claims:

1. **Check gate is enabled**
   ```bash
   echo $HYPOTHESIS_AS_FACT_GATE_ENABLED
   # Should output: true
   ```

2. **Check session_id and terminal_id are present**
   - Gate requires both fields in hook data
   - Missing fields cause early return (allow)

3. **Check verification engine is available**
   - `verification/claims.py` must be importable
   - `verification/engine.py` must be importable

### False Positives

If the gate blocks legitimate claims:

1. **Add hedging to claim**
   - Use phrases like "appears to be", "seems like", "possibly"
   - Hedged claims pass without evidence

2. **Verify tool events are recorded**
   - Check `evidence_store.db` for tool events
   - Tool events must be in same session_id and terminal_id

3. **Review entity matching**
   - Check that claim targets match tool event paths
   - Path normalization handles Windows/Unix differences

## Performance Characteristics

Baseline performance (measured with pytest benchmark):

| Response Length | Tool Events | P50 (ms) | P95 (ms) | P99 (ms) |
|----------------|-------------|----------|----------|----------|
| 500 chars      | 5 events     | 0.00     | 0.00     | 0.01     |
| 500 chars      | 20 events    | 0.00     | 0.00     | 0.01     |
| 500 chars      | 50 events    | 0.00     | 0.00     | 0.00     |
| 2000 chars     | 5 events     | 0.00     | 0.00     | 0.00     |
| 2000 chars     | 20 events    | 0.00     | 0.00     | 0.00     |
| 2000 chars     | 50 events    | 0.00     | 0.00     | 0.01     |
| 8000 chars     | 5 events     | 0.00     | 0.00     | 0.05     |
| 8000 chars     | 20 events    | 0.00     | 0.00     | 0.00     |
| 8000 chars     | 50 events    | 0.00     | 0.00     | 0.00     |

**All combinations**: P95 < 0.01ms (well below 20ms target)

## Related Documentation

- Implementation plan: `.claude/hooks/plans/plan-20260314-verification-claim-grounding.md`
- Test coverage: `.claude/hooks/tests/test_verification_*.py`
- Engine architecture: `.claude/hooks/verification/README.md` (if exists)

## Support and Feedback

For issues or questions:
1. Check log file: `state/logs/hypothesis_as_fact_gate.jsonl`
2. Review this documentation
3. Check implementation plan for design rationale
4. File issue with log entries attached
