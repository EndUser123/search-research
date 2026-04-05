# Hook Analysis System

Unified analysis across all hook logging systems.

## Quick Start (Recommended)

Use the `/hook-audit` skill for behavioral compliance monitoring:

```bash
# Full compliance dashboard
/hook-audit

# Specific analysis
/hook-audit blocks        # Blocking events
/hook-audit assumptions   # Assumption audit compliance
/hook-audit attribution   # Error attribution compliance
/hook-audit escalation    # Phase 2 recommendations
/hook-audit health        # Hook system health

# Custom time range
/hook-audit --days 14
```

## Script Access

```bash
# Unified dashboard (same as /hook-audit)
python P:/.claude/hooks/hook_audit_dashboard.py

# Legacy unified analysis
python P:/.claude/hooks/analyze_hooks.py

# Specific system with details
python P:/.claude/hooks/analyze_hooks.py --system audit --verbose

# Different time range
python P:/.claude/hooks/analyze_hooks.py --days 30

# All systems detailed
python P:/.claude/hooks/analyze_hooks.py --system all
```

## Registered Log Systems

| System | Log File | Tracks |
|--------|----------|--------|
| `attribution` | `P:/.claude/logs/error_attribution.jsonl` | Error source injections |
| `blocks` | `logs/constructional_blocks.jsonl` | General hook violations with severity |
| `enforcement` | `logs/block_enforcement.jsonl` | Hard blocks (exit 2) |
| `audit` | `logs/test_assumption_audit.jsonl` | Assumption audit triggers + compliance |
| `absence` | `logs/absence_claim_gate.jsonl` | Absence claim detections |
| `subagent` | `logs/subagent_enforcer.jsonl` | Subagent enforcement |

## Severity Levels

Introduced 2026-01-24 in `hook_tracker.py`:

| Level | Constant | User Visibility | Use Case |
|-------|----------|-----------------|----------|
| CRITICAL | `SEVERITY_CRITICAL` | Always shown | Hard blocks, policy violations |
| WARN | `SEVERITY_WARN` | Shown if count ≥ 5 | Soft warnings, policy concerns |
| INFO | `SEVERITY_INFO` | Never shown | Audit trail only |

### Using Severity in Hooks

```python
from hook_tracker import log_block, SEVERITY_INFO, SEVERITY_WARN, SEVERITY_CRITICAL

# Noisy patterns - log silently
log_block("my_hook", "Bash", command, "INFO: Matched pattern", SEVERITY_INFO)

# Policy concerns - show if frequent
log_block("my_hook", "Bash", command, "WARNING: Potential issue", SEVERITY_WARN)

# Hard violations - always show
log_block("my_hook", "Bash", command, "CRITICAL: Policy violation", SEVERITY_CRITICAL)
```

## Compliance Tracking (Assumption Audit)

The assumption audit hook tracks whether LLMs follow soft guidance.

### Flow

1. **Trigger**: LLM responds without observation tools (Read, Bash, Search, etc.)
2. **Pending state**: Hook writes `state/pending_assumption_audit.json`
3. **Next turn**: Hook checks if LLM complied:
   - Used observation tools? → Complied
   - Marked claims as `[UNVERIFIED]`? → Complied
   - Neither? → Ignored
4. **Logged**: `compliance_check` event with `complied: true/false`

### Viewing Compliance Data

```bash
python P:/.claude/hooks/analyze_hooks.py --system audit --verbose
```

Output includes:
```
Compliance Tracking:
  Checks performed: 15
  LLM complied:     12 (80.0%)
  LLM ignored:      3
```

### Interpreting Results

| Compliance Rate | Interpretation | Action |
|-----------------|----------------|--------|
| >80% | Soft guidance effective | Keep current approach |
| 50-80% | Marginal effectiveness | Consider strengthening prompts |
| <50% | Soft guidance ignored | Switch to hard blocks |

## Adding New Log Systems

Edit `LOG_REGISTRY` in `analyze_hooks.py`:

```python
LOG_REGISTRY = {
    # ... existing entries ...
    
    "my_new_system": {
        "file": LOGS_DIR / "my_new_system.jsonl",
        "description": "What this tracks",
        "event_field": "event",  # Field containing event type, or None
        "count_field": "event",  # Field to group counts by
    },
}
```

## Log File Formats

### constructional_blocks.jsonl
```json
{
  "timestamp": "2026-01-24T15:19:41.746619",
  "hook": "unparseable_command_gate",
  "tool": "Bash",
  "command": "python -c '...'",
  "reason": "INFO: python -c executes arbitrary code",
  "severity": "info"
}
```

### test_assumption_audit.jsonl
```json
// Trigger event
{
  "timestamp": "2026-01-24T15:20:50.123456",
  "event": "trigger",
  "tools_used": [],
  "response_snippet": "Based on my knowledge...",
  "duration_ms": 12.5,
  "is_continuation": false
}

// Compliance check event
{
  "timestamp": "2026-01-24T15:21:30.789012",
  "event": "compliance_check",
  "pending_timestamp": "2026-01-24T15:20:50.123456",
  "pending_snippet": "Based on my knowledge...",
  "followup_tools": ["Read", "Bash"],
  "followup_has_observation": true,
  "followup_has_unverified": false,
  "complied": true
}
```

### block_enforcement.jsonl
```json
{
  "timestamp": "2026-01-24T15:10:12.345678",
  "hook": "test_assumption_audit",
  "action": "block",
  "reason": "You responded without using verification tools..."
}
```

## Noise Reduction Architecture

### Problem

Hooks generate many warnings for legitimate patterns:
- `python -c` for one-liners
- Heredocs for multi-line scripts
- Pipe chains for data processing

### Solution

1. **Whitelist legitimate patterns** in gate hooks
2. **Demote to INFO severity** for audit trail without user noise
3. **Raise threshold** for showing summaries (3 → 5)

### Whitelisted Patterns (unparseable_command_gate.py)

```python
SAFE_PATTERNS = [
    r'python[3]?\s+-c.*from beads_helper import',  # Task tracking
    r'python[3]?\s+-c\s+["\']import ast;\s*ast\.parse\(',  # AST checks
    r'python[3]?\s+-c.*json\.load\(open\([^)]+\)\).*print',  # Config reads
    r'grep.*\|\s*python[3]?\s+-c.*sys\.stdin',  # Grep pipes
    r'python[3]?\s+-c.*Path\(.*\)\.exists\(\)',  # Path checks
]
```

## Related Files

| File | Purpose |
|------|---------|
| `analyze_hooks.py` | Unified analysis tool |
| `hook_tracker.py` | Severity levels, session tracking |
| `Stop_router.py` | Aggregates Stop hook outputs |
| `test_assumption_audit.py` | Assumption audit with compliance tracking |
| `unparseable_command_gate.py` | Bash command validation |
| `shell_complexity_gate.py` | Complex shell pattern detection |

## Maintenance

### Clearing Old Logs

```bash
# Archive logs older than 30 days
find P:/.claude/hooks/logs -name "*.jsonl" -mtime +30 -exec gzip {} \;
```

### Checking Log Sizes

```powershell
Get-ChildItem -Path "P:\.claude\hooks\logs" -Filter "*.jsonl" | 
  Select-Object Name, @{N='MB';E={[math]::Round($_.Length/1MB,2)}} |
  Sort-Object MB -Descending
```
