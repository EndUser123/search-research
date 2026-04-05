# Verification Rollout Plan (TASK-008)

**Objective**: Gradual rollout with monitoring

**Status**: Phase 1 - Advisory Mode

---

## Week 1: Documentation + Tier 3 Tracking (Non-Blocking)

**Status**: ✅ COMPLETE

**Configuration**:
```bash
# Set advisory mode (non-blocking)
export E2E_TRACKER_MODE=advisory

# Enable E2E tracking
export E2E_TRACKING_ENABLED=true
```

**Implementation**:
- Deployed `PostToolUse_e2e_tracker.py` in advisory mode
- E2E tracking collects workflow execution data
- Logs stored in: `.claude/state/e2e_executions_{session_id}.jsonl`

**Data Collection**:
- Skill invocations (UserPromptSubmit → execution → response)
- Multi-step workflows (tool sequences)
- State changes (file writes, git operations)
- Session isolation (session_id + terminal_id)

**Week 1 Deliverables**:
- [x] E2E tracker deployed
- [x] Advisory mode configuration documented
- [x] Log rotation implemented (PERF-002)
- [x] Session cleanup implemented (2-hour TTL)

**Gap Analysis**: Document any e2e gaps found during Week 1

---

## Week 2: Enable Verification Gate (Warn Mode)

**Status**: ⏳ PENDING

**Configuration**:
```bash
# Verification gate (warn mode - default)
export UNVERIFIED_STANCE_MODE=warn
export UNVERIFIED_STANCE_ENABLED=true

# Enable E2E verification
export E2E_VERIFICATION_ENABLED=true
```

**Implementation**:
- Enable `StopHook_unverified_stance.py` in warn mode
- Collect telemetry on verification violations
- Log violations to: `.claude/state/logs/unverified_stance.log`

**Metrics Collected**:
- Blocked claims by type
- False positive rate
- Tier distribution
- Tool usage patterns

**Week 2 Deliverables**:
- [ ] Warn mode enabled
- [ ] Telemetry collection active
- [ ] False positive rate documented
- [ ] Pattern tuning recommendations

---

## Week 3: Full Enforcement (Block Mode Optional)

**Status**: ⏳ PENDING

**Configuration**:
```bash
# Optional: Switch to block mode after tuning
export UNVERIFIED_STANCE_MODE=block
```

**Prerequisites**:
- False positive rate < 10%
- Pattern tuning complete
- Documentation reviewed

**Week 3 Deliverables**:
- [ ] Block mode available (optional)
- [ ] Metrics documented
- [ ] Rollback procedures tested

**Rollback**:
```bash
# Immediate rollback to warn mode
export UNVERIFIED_STANCE_MODE=warn

# Complete disable (emergency only)
export UNVERIFIED_STANCE_ENABLED=false
export CONSTITUTIONAL_HOOKS_BYPASS=1
```

---

## Security Fix (SEC-005): Audit Logging

**Status**: ⏳ PENDING

**Implementation**:
- Log file: `.claude/state/logs/verification_bypass.log`
- Format: JSON with timestamp, PID, security_impact=HIGH, reason

**Trigger Conditions**:
- When `UNVERIFIED_STANCE_ENABLED=false`
- When verification is bypassed
- When security violations detected

**Log Entry Example**:
```json
{
  "timestamp": "2026-03-10T16:30:00Z",
  "pid": 12345,
  "security_impact": "HIGH",
  "reason": "UNVERIFIED_STANCE_ENABLED=false",
  "action": "verification_bypass",
  "user": "system"
}
```

**Security Monitoring**:
- Review logs weekly for bypass patterns
- Alert on repeated bypass attempts
- Document legitimate bypass reasons

---

## Telemetry Collection

**Metrics Script**: `.claude/hooks/scripts/analyze_verification_telemetry.py`

**Weekly Analysis**:
```bash
# Run weekly analysis
python P:/.claude/hooks/scripts/analyze_verification_telemetry.py --week

# Show false positive rate
python P:/.claude/hooks/scripts/analyze_verification_telemetry.py --false-positive-rate

# Tier distribution
python P:/.claude/hooks/scripts/analyze_verification_telemetry.py --tiers

# Export to JSON
python P:/.claude/hooks/scripts/analyze_verification_telemetry.py --format json --output verification_metrics.json
```

**Pattern Tuning Recommendations**:
- Adjust detection patterns based on false positives
- Add exclusion patterns for common mistakes
- Update threshold values for claim detection

---

## Acceptance Criteria

### Phase 1: Advisory Mode ✅
- [x] Advisory mode deployed
- [x] E2E tracking active
- [x] Log rotation implemented
- [x] Session cleanup implemented

### Phase 2: Warn Mode ⏳
- [ ] Warn mode enabled
- [ ] Telemetry collected
- [ ] False positive rate documented
- [ ] Pattern tuning recommendations

### Phase 3: Block Mode (Optional) ⏳
- [ ] Block mode available
- [ ] Metrics documented
- [ ] Rollback procedures tested

### Security (SEC-005) ⏳
- [ ] Bypass activity logged
- [ ] Security monitoring active
- [ ] Audit log review process

---

## Configuration Reference

**Environment Variables**:

| Variable | Default | Purpose |
|----------|---------|---------|
| `E2E_TRACKER_MODE` | `advisory` | E2E tracking mode (advisory/warn/block) |
| `E2E_TRACKING_ENABLED` | `true` | Enable E2E workflow tracking |
| `E2E_VERIFICATION_ENABLED` | `false` | Enable E2E verification checks |
| `UNVERIFIED_STANCE_ENABLED` | `true` | Enable unverified stance detection |
| `UNVERIFIED_STANCE_MODE` | `warn` | Detection mode (warn/block) |

**Settings Configuration**:
Add to `P:/.claude/settings.json`:
```json
{
  "env": {
    "E2E_TRACKER_MODE": "advisory",
    "E2E_TRACKING_ENABLED": "true",
    "E2E_VERIFICATION_ENABLED": "true",
    "UNVERIFIED_STANCE_ENABLED": "true",
    "UNVERIFIED_STANCE_MODE": "warn"
  }
}
```

---

## Rollback Procedures

**Immediate Rollback**:
```bash
# Switch to warn mode
export UNVERIFIED_STANCE_MODE=warn

# Disable E2E verification
export E2E_VERIFICATION_ENABLED=false
```

**Emergency Rollback**:
```bash
# Complete bypass
export CONSTITUTIONAL_HOOKS_BYPASS=1

# Or disable specific hooks
export UNVERIFIED_STANCE_ENABLED=false
export E2E_TRACKING_ENABLED=false
```

**Verification**:
```bash
# Check hook status
python P:/.claude/hooks/hook_diagnostics.py

# Review recent logs
python P:/.claude/hooks/shared_utils.py logs --limit 50
```

---

## Documentation Links

- **E2E Tracker**: `PostToolUse_e2e_tracker.py`
- **Unverified Stance Detection**: `StopHook_unverified_stance.py`
- **Observable Effect Verifier**: `posttooluse/observable_effect_verifier.py`
- **Integration Verifier**: `posttooluse/integration_verifier.py`

---

## Contact

For questions or issues with the rollout plan:
- Review hook documentation in `CLAUDE.md`
- Check diagnostics: `python P:/.claude/hooks/hook_diagnostics.py`
- Submit issue via normal channels

---

**Last Updated**: 2026-03-10
**Plan Version**: 1.0
**Status**: Phase 1 Complete, Phase 2 Pending
