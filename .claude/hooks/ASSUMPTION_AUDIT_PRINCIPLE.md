# Assumption Audit: Principle Over Patterns

## The Problem
Pattern-based fabrication detection = endless whack-a-mole:
- "Found 13 tasks" → add pattern
- "These 8 items" → add pattern  
- "System rotates logs every 7 days" → add pattern
- ∞ maintenance burden

## The Principle
**No observation tools used? → Self-audit required**

Simple enforcement: If CC responds without Read/Bash/Grep/Search, it must self-evaluate whether it made unverified claims.

## Implementation

### Core Hook: test_assumption_audit.py
**Flow:**
1. CC generates response
2. Hook checks: Were observation tools used?
3. If NO tools → Block with audit prompt
4. CC self-evaluates: "Did I make empirical claims?"
5. If YES → Verify now or mark [UNVERIFIED]
6. If NO → Proceed

**Exemptions added (to prevent false positives):**
- General knowledge: "A mutex is...", "Git uses SHA-1..."
- Questions/clarifications
- Acknowledgments
- Responses < 100 chars
- Already marked [UNVERIFIED]

### Backup: Pattern-based gates
**Still active:**
- empirical_claims_gate.py (enumeration patterns added)
- Stop_absence_claim_gate.py  
- concern_detection.py (verification challenge patterns added)

**Why keep both?**
- Patterns: Fast, deterministic (catches obvious cases)
- Principle: General, scalable (catches novel cases)

## Protections Added

### 1. False Positive Management ✓
**Problem:** Would block "What's a mutex?" (general knowledge)

**Solution:** SAFE_RESPONSE_PATTERNS exempt:
- Definitions, general knowledge
- Short acknowledgments
- Self-awareness ("Let me check...")

**Measure:** `python analyze_assumption_audit.py` shows safe vs blocked

### 2. Observability ✓
**Logging added:**
- Event type (safe_response, trigger, check)
- Response snippet
- Tools used
- Duration (ms)

**Analysis:** `python analyze_assumption_audit.py` shows:
- Block rate %
- Which tools prevent blocks
- Sample blocked responses
- Performance impact

### 3. Performance Measurement ✓
**Instrumentation:**
- Timing at each decision point
- Logged in `duration_ms` field
- Analyze: Does audit add significant latency?

**Early exit optimizations:**
- Tools present? Allow immediately
- Safe patterns? Allow immediately  
- Only blocks when needed

## What We Didn't Address (Yet)

**Waiting for real data:**
- Tool selection quality (did CC use RIGHT tool?)
- Multi-turn staleness (when does observation expire?)
- Hedging calibration (avoid unhelpful "PROBABLY [UNVERIFIED]")
- Composability (interactions with other principle-based gates)

**Measure first, optimize later:**
- False positive rate in practice
- Real latency impact
- User friction tolerance

## Usage

### Terminal Isolation (v2.1)

All audit events are tagged with terminal ID to prevent cross-instance contamination.
See `docs/TERMINAL_ISOLATION.md` for details.

```bash
# Current terminal only
python analyze_assumption_audit.py --terminal

# All terminals separately  
python analyze_assumption_audit.py --all
```

### When to Check Logs

**Automatic alerts (no action needed):**
1. **During session:** Stop_router shows alert if block rate > 15%
2. **End of session:** SessionEnd hook reports if issues detected

**Manual triggers:**
- User complains: "Claude keeps asking me to verify obvious things"
- Session feels slow/blocky
- Curious about verification patterns

### Enable/Disable
```bash
export TEST_ASSUMPTION_AUDIT_ENABLED=true   # Default: enabled
export TEST_ASSUMPTION_AUDIT_ENABLED=false  # Disable if problematic
```

### Monitor
```bash
# View last 24 hours
python P:/.claude/hooks/analyze_assumption_audit.py

# View last 1 hour
python P:/.claude/hooks/analyze_assumption_audit.py 1
```

### Test
```bash
# Verify principle catches novel claim types
python P:/.claude/hooks/test_principle_vs_patterns.py
```

## Expected Outcomes

**Short term:**
- Block rate: 5-15% (most responses use tools or are general knowledge)
- False positives: < 5% (caught by exemptions)
- Latency: < 50ms added (fast pattern checks)

**Long term:**
- Pattern gates become unnecessary (principle catches everything)
- Audit prompt tuned based on what self-evaluations miss
- Exemption patterns expanded based on false positive patterns

## Key Insight

**Whack-a-mole (patterns):** Reactive, never complete, high maintenance
**Self-evaluation (principle):** Proactive, general, self-correcting

Trading debuggability for generality. Worth it when failure modes are unbounded.
