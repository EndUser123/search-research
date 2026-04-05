# Error Attribution Tracker

## Overview

Tracks error sources from tool output and injects prominent attribution to prevent LLM confabulation.

**Problem Solved**: LLM reads error message containing source (e.g., `skill_enforcement_gate.py`), then explains error by inventing different source (e.g., "TDD hook").

## Current Status: Phase 1 (Advisory + Logging)

### Behavior
- PostToolUse hook extracts error source via regex patterns
- Injects prominent visual attribution box
- Logs all attributions to `P:/.claude/logs/error_attribution.jsonl`
- Writes state for potential Stop gate validation

### Patterns Detected
```
[python .claude/hooks/skill_enforcement_gate.py]  → hook_file
PreToolUse:Bash hook error                         → hook_event  
File "foo.py", line 42                             → python_exception
```

### Injection Format
```
┌─────────────────────────────────────────────────────────┐
│ ⚠️  ERROR SOURCE: skill_enforcement_gate.py             │
│ Reference this source when explaining what went wrong.  │
└─────────────────────────────────────────────────────────┘
```

## Escalation Plan

### Phase 2 Trigger Criteria
Implement Stop gate (`error_attribution_gate.py`) if logs show:
- >30% of error explanations ignore injected source
- Pattern: `error_attribution.jsonl` entries without matching source mention in subsequent response

### Phase 2 Implementation
```python
# Stop_router.py addition
def check_error_attribution(response: str) -> dict | None:
    state = read_last_error_state()
    if not state or time.time() > state["expires_at"]:
        return None
    
    source = state["source"].lower()
    source_stem = Path(source).stem  # "skill_enforcement_gate"
    
    if source_stem not in response.lower():
        return {
            "block": True,
            "reason": f"Error explanation must reference: {source}"
        }
    return None
```

### Audit Query
```bash
# Check compliance rate
python -c "
import json
from pathlib import Path
logs = [json.loads(l) for l in Path('P:/.claude/logs/error_attribution.jsonl').read_text().splitlines()]
print(f'Total errors tracked: {len(logs)}')
# Manual review: compare timestamps with transcript to check if source was mentioned
"
```

## Configuration

| Env Var | Default | Description |
|---------|---------|-------------|
| `ERROR_ATTRIBUTION_ENABLED` | `true` | Enable/disable tracker |
| `ERROR_ATTRIBUTION_DEBUG` | `0` | Debug logging to stderr |

## Files

- `posttooluse/error_attribution_tracker.py` - Main hook implementation
- `P:/.claude/logs/error_attribution.jsonl` - Audit log
- `P:/.claude/hooks/state/last_error_source.json` - State for Stop gate

## History

- **v1.0.0** (2026-01-24): Initial implementation, Phase 1 advisory + logging
