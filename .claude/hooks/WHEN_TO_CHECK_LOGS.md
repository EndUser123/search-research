# How to Know When to Check Logs

## The Problem
You added instrumentation but no trigger to act on it:
```
Logs fill → Nobody checks → Problems accumulate → System degrades
```

## The Solution: Automatic Alerting

### 1. Real-Time Alerts (Stop Hook)

**When:** During active session, at response time
**Trigger:** Block rate > 15% AND 5+ responses
**Display:** Injected into Stop hook output (user sees immediately)

```
⚠️ Assumption Audit Alert: 8/20 responses blocked (40%)

This may indicate:
  • False positives (blocking general knowledge)
  • Missing tool usage (CC not verifying claims)
  
Run: python P:/.claude/hooks/analyze_assumption_audit.py
```

**Implementation:** `Stop_router.py` calls `assumption_audit_summary.py`

### 2. Session-End Report (SessionEnd Hook)

**When:** End of session
**Trigger:** Block rate > 15% for the session
**Display:** Printed to stderr in session cleanup

**Implementation:** `SessionEnd_assumption_audit_report.py`

### 3. Manual Investigation

**When to manually check:**
- User feedback: "Claude keeps blocking my responses"
- Curiosity: "What's getting blocked?"
- After hook changes: "Did my exemption patterns work?"
- Compliance analysis: "Is the LLM following soft guidance?"

**Commands:**
```bash
# PRIMARY: Unified hook behavioral compliance dashboard
python P:/.claude/hooks/hook_audit_dashboard.py
# Or use skill: /hook-audit

# Specific subcommands
/hook-audit blocks        # Blocking events
/hook-audit assumptions   # Assumption audit compliance
/hook-audit attribution   # Error attribution compliance
/hook-audit escalation    # Phase 2 escalation recommendations
/hook-audit health        # Hook system health

# Legacy: Unified analysis of all hook systems
python P:/.claude/hooks/analyze_hooks.py

# Terminal-filtered analysis (v2.1)
python P:/.claude/hooks/analyze_assumption_audit.py --terminal  # Current terminal only
python P:/.claude/hooks/analyze_assumption_audit.py --all       # Per-terminal breakdown

# Detailed view of specific system
python P:/.claude/hooks/analyze_hooks.py --system audit --verbose
python P:/.claude/hooks/analyze_hooks.py --system blocks --verbose

# Different time range
python P:/.claude/hooks/analyze_hooks.py --days 30

# All systems detailed
python P:/.claude/hooks/analyze_hooks.py --system all

# Legacy: Single-system analysis
python P:/.claude/hooks/assumption_audit_summary.py
python P:/.claude/hooks/analyze_assumption_audit.py
python P:/.claude/hooks/analyze_error_attribution.py
```

See `docs/HOOK_ANALYSIS.md` for full documentation.
See `docs/TERMINAL_ISOLATION.md` for terminal filtering details.

## Alert Thresholds

**Current settings:**
- **15% block rate** = Investigation recommended
- **5+ responses** = Minimum sample size for statistical relevance
- **5+ warnings** = Show session summary (raised from 3 on 2026-01-24)

**Rationale:**
- < 15% = Expected (some claims need verification)
- 15-30% = Concerning (possible false positives)
- > 30% = Critical (likely broken exemption patterns)

**Tuning:**
Edit `assumption_audit_summary.py`:
```python
ALERT_THRESHOLD = 0.15  # Adjust this
```

## Compliance Tracking (New 2026-01-24)

The assumption audit now tracks whether LLMs follow soft guidance.

**What it measures:**
- After a soft warning, did the LLM:
  - Use observation tools (Read, Bash, Search)? → Complied
  - Mark claims as `[UNVERIFIED]`? → Complied
  - Neither? → Ignored the guidance

**How to check:**
```bash
python P:/.claude/hooks/analyze_hooks.py --system audit --verbose
```

**Interpreting results:**
| Compliance Rate | Meaning | Action |
|-----------------|---------|--------|
| >80% | Soft guidance works | Keep approach |
| 50-80% | Marginal | Consider stronger prompts |
| <50% | Being ignored | Switch to hard blocks |

## What the Alerts Tell You

### High Block Rate Causes

**1. False Positives (most common)**
- Blocking general knowledge: "What's a mutex?"
- Blocking definitions: "Git uses SHA-1"
- Need better exemption patterns

**Action:** Review blocked responses, add patterns to `SAFE_RESPONSE_PATTERNS`

**2. Missing Tool Usage**
- CC actually making unverified claims
- Hook working correctly, CC behavior needs improvement
- May need stronger enforcement in prompts

**Action:** Review if CC *should* have used tools

**3. Tool Selection Issues**
- CC using wrong tools (ls instead of cat)
- Requires semantic validation, not just presence check

**Action:** This is a limitation - log for future enhancement

### Low Block Rate Causes

**Good news:**
- Exemptions working
- CC using tools appropriately
- System healthy

**No action needed.**

## Observability Workflow

```
1. Session runs
   ↓
2. Automatic threshold check
   ↓
3. Alert shows if > 15%
   ↓
4. You run analysis script
   ↓
5. Identify false positive patterns
   ↓
6. Add to SAFE_RESPONSE_PATTERNS
   ↓
7. Block rate drops
```

## Files Involved

**Alerting:**
- `Stop_router.py` - Real-time alerts, severity filtering
- `SessionEnd_assumption_audit_report.py` - End-of-session report
- `assumption_audit_summary.py` - Alert logic and formatting
- `hook_tracker.py` - Severity levels (CRITICAL/WARN/INFO)

**Analysis:**
- `analyze_hooks.py` - **PRIMARY** unified analysis tool (2026-01-24)
- `analyze_assumption_audit.py` - Legacy single-system analysis
- `test_assumption_audit.py` - The hook itself (logs events + compliance)

**Logs:**
- `P:/.claude/logs/error_attribution.jsonl` - Error source injections (2026-01-25)
- `logs/constructional_blocks.jsonl` - General hook violations
- `logs/block_enforcement.jsonl` - Hard blocks (exit 2)
- `logs/test_assumption_audit.jsonl` - Audit triggers + compliance
- `logs/absence_claim_gate.jsonl` - Absence claim detections
- `logs/subagent_enforcer.jsonl` - Subagent enforcement

**State:**
- `state/pending_assumption_audit_*.json` - Compliance tracking state (terminal-scoped via hash)
- `state/last_error_source.json` - Error attribution state (2026-01-25)

**Documentation:**
- `docs/HOOK_ANALYSIS.md` - Full analysis system documentation
- `docs/TERMINAL_ISOLATION.md` - Multi-instance isolation (v2.1)

## Expected Behavior

**Healthy system:**
- Block rate: 5-15%
- No alerts (below threshold)
- Occasional manual checks confirm patterns

**Problem detected:**
- Block rate: > 15%
- Alert shown during session
- Investigation reveals false positives
- Exemption patterns updated
- Block rate returns to normal

**Critical issues:**
- Block rate: > 30%
- Multiple alerts per session
- System feels unusable
- Emergency disable: `export TEST_ASSUMPTION_AUDIT_ENABLED=false`

## Feedback Loop

This creates a continuous improvement cycle:

```
Alert → Investigate → Find pattern → Add exemption → Lower block rate → Repeat
```

Eventually, exemption patterns converge and alerts stop.

## Key Insight

**Don't wait for problems.** Automatic alerts surface issues proactively:
- No "I wonder if this is working?"
- No stale logs nobody checks
- No silent degradation

The system tells you when to look.
