# Lazy Workaround Detection Gate

## Status: ✅ ACTIVE

**File**: `P:/.claude/hooks/Stop_lazy_workaround_gate.py`
**Tests**: `P:/.claude/hooks/tests/test_lazy_workaround_gate.py`
**Memory**: `P:\.claude\memory\lazy_patterns.md`

## What It Does

**Blocks** LLM responses that suggest accepting bugs as features instead of fixing root causes.

## Example: What Would Have Been Blocked

**The lazy suggestion from your other terminal:**
```
"Keep current changes and accept the duplicate bars as 'visible logging'"
```

**Result**: ✅ BLOCKED with message:
```
LAZY WORKAROUND DETECTED: accepting bug as feature

⚠️  This suggests accepting a problem instead of fixing the root cause.

Required approach:
1. TRACE: Find where the problem originates
2. IDENTIFY: What's causing it
3. FIX: Address the actual root cause
4. VERIFY: Confirm the fix works
```

## Patterns Blocked

| Pattern | Example | Blocked As |
|---------|---------|------------|
| `accept.*as.*visible logging` | "Accept duplicate bars as visible logging" | Accepting bug as feature |
| `live with.*(bug|issue)` | "Live with the race condition" | Accepting technical debt |
| `(duplicate|redundant).*(is fine|acceptable)` | "Duplicates are fine" | Ignoring duplication |
| `(cosmetic|minor).*(bug|issue)` | "This is a cosmetic issue" | Dismissing functional bug |
| `not worth fixing` | "Not worth investigating" | Avoiding necessary work |
| `workaround.*(is fine|sufficient)` | "The workaround is fine" | Accepting workaround over fix |

## Patterns Allowed

✅ Root cause investigation:
- "Let me trace where the duplicate tasks are created"
- "I'll investigate why this happens"
- "Let's identify the root cause"
- "Need to debug the source of this issue"

## Integration

**Integrated into Stop.py** (2026-03-06) via `_run_lazy_workaround_gate` function, appended to `IN_PROCESS_GATES`.

## Testing

```bash
# Test the gate directly
python P:/.claude/hooks/Stop_lazy_workaround_gate.py "accept duplicate bars as visible logging"

# Run tests
cd P:/.claude/hooks/tests
python test_lazy_workaround_gate.py -v
```

## Why This Matters

**Without this gate:**
- LLMs suggest "accept the bug as feature"
- Technical debt accumulates
- Users suffer from confusing/buggy behavior
- Problems never get fixed

**With this gate:**
- LLMs are forced to investigate root causes
- Problems get fixed at the source
- Technical debt is prevented
- Quality is maintained

## Memory Storage

Pattern documented in: `P:\.claude\memory\lazy_patterns.md`

This ensures future sessions recognize and reject lazy workaround suggestions.
