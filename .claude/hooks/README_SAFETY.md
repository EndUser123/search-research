# Safety System Hook Documentation

**Hook**: `UserPromptSubmit_safety_router.py`
**Layer**: -999 (executes FIRST)
**Version**: 2.1.0

---

## Purpose

Intercepts all user prompts before execution to detect design smells and logic errors that commonly lead to incorrect implementations or wasted effort.

---

## How It Works

```
User submits prompt
        |
        v
Safety Hook (layer -999)
        |
        +--> Analyze prompt for design smells
        +--> Check for empirical claims without Read
        +--> Validate location specificity
        |
        v
Decision: ALLOW | WARN | CONFIRM | BLOCK
        |
        v
If ALLOW/WARN/CONFIRM: Continue to other hooks
If BLOCK: Stop execution, show message
```

---

## Current Behavior

| Mode | Setting | Behavior |
|------|---------|----------|
| **Shadow** | `enabled: true` | Log decisions, never block |
| **Canary** | `enabled: false` | Gradual rollout (not yet active) |
| **Full** | `enabled: false` | Full enforcement (not yet active) |

**Currently**: Shadow mode only - all prompts pass through normally.

---

## Patterns Detected

### 1. Logic Inversion (Severity 5)
```
"Remove --force flag"
"Delete the --required option"
"Make database the default instead of --from-db"
```
**Why block**: These defaults were added to prevent dangerous operations.

### 2. Location Ambiguity (Severity 3)
```
"Put statusline where?"
"Add the function"
"Create the config here"
```
**Why block**: Without a location, the implementation will be wrong.

### 3. Empirical Claim (Severity 4)
```
"The code has a bug in auth"
"This file imports the wrong module"
"The function returns None"
```
**Why block**: Claims about code must be verified by reading first.

### 4. Premature Abstraction (Severity 3)
```
"Extract this into a base class"
"Create an interface for this"
"Abstract the error handling"
```
**Why block**: Abstraction without concrete implementations is YAGNI.

---

## Configuration

**Config File**: `P:\__csf\config\safety_system\config.yaml`

```yaml
safety_system:
  enabled: true
  phases:
    shadow_mode:
      enabled: true
  gates:
    design_smell_detection:
      severity_threshold: 3  # Block at severity >= 3
```

**Environment Override**:
```bash
export SAFETY_ROUTER_ENABLED=false  # Disable temporarily
```

---

## Hook Output

### Shadow Mode (current)
```json
{
  "passed": true,
  "shadow_mode": true,
  "would_have_blocked": false,
  "decision_type": "allow",
  "risk_score": 0.0
}
```

### Block (when enabled)
```json
{
  "passed": false,
  "block": true,
  "user_message": "Please specify where this should go.",
  "reason": "location_ambiguity",
  "gate_source": "design_smell_detection",
  "risk_score": 75.0
}
```

---

## Monitoring

### Check Decision Log
```bash
sqlite3 P:\.claude\data\safety_decisions.db \
  "SELECT action, COUNT(*) FROM decisions GROUP BY action"
```

### Shadow Mode Report
```python
from safety_system import PersistentDecisionLogger

logger = PersistentDecisionLogger()
report = logger.get_shadow_report(hours=24)

print(f"Total: {report['total_decisions']}")
print(f"Would block: {report['would_have_blocked']}")
print(f"Block rate: {report['block_percentage']:.1f}%")
```

---

## File Locations

| File | Path |
|------|------|
| Hook | `.claude/hooks/UserPromptSubmit_safety_router.py` |
| Config | `__csf/config/safety_system/config.yaml` |
| Source | `__csf/src/safety_system/` |
| Decision Log | `.claude/data/safety_decisions.db` |

---

## Disabling

To temporarily disable the safety hook:

```bash
# Environment variable (recommended)
export SAFETY_ROUTER_ENABLED=false

# Or rename the hook
mv .claude/hooks/UserPromptSubmit_safety_router.py \
   .claude/hooks/UserPromptSubmit_safety_router.py.disabled
```

---

## Next Steps

1. **Shadow mode**: Currently running - collecting data for 72 hours
2. **Review**: Check false positive/negative rate
3. **Canary**: Enable at 1% when confident
4. **Full rollout**: Expand gradually based on metrics

---

## Documentation

- **Full README**: `__csf/src/safety_system/README.md`
- **Implementation**: `__csf/.speckit/memory/TSK-SAFETY-20260104/synthesis.md`
