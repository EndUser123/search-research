# Stop Negative Existence Guard

## Purpose

Blocks responses that claim files, documentation, or resources don't exist WITHOUT verification tools used THIS TURN.

## Problem Solved

AI agents frequently claim "no X file", "X doesn't exist", "missing X" without checking with Read, Glob, Grep, or other verification tools. This creates hallucinated gap analysis that blocks legitimate work.

## Implementation

**File**: `P:/.claude/hooks/Stop_negative_existence_guard.py`

**Event**: Stop (response validation)

**Performance**: 142.49ms average (target: <200ms) ✓

## Detection Patterns

### Core Negative Existence Patterns
- `missing`
- `doesn't exist` / `does not exist`
- `no such`
- `wasn't created`
- `not documented`
- `no documentation`
- `no X file` (e.g., "no config file")

### File-Specific Patterns
- `no (\w+\.?\w*) file` - "no config file", "no .env file"
- `(\w+\.?\w*) file (doesn't|does not) exist`
- `(\w+\.?\w*) (is|was) missing`
- `there's no (\w+\.?\w*)`
- `no (\w+) documentation`

## Allowlist (Obvious Claims - No Verification Needed)

- **Capability statements**: "no internet access", "no network", "offline"
- **Domain knowledge**: "no configuration needed", "no config required", "no setup needed"

These are legitimate claims about system capabilities or domain knowledge that don't require file system verification.

## Verification Tools (Evidence Requirements)

To claim a file/resource doesn't exist, you must use AT LEAST ONE of these tools THIS TURN:

- **Read** - Direct file access
- **Glob** - Pattern-based file discovery
- **Grep** - Content search
- **Bash** - With verification commands: `ls`, `find`, `git ls-files`, `test -f`
- **WebSearch** - For external resources
- **WebFetch** - For URL verification

## Turn Scoping (Stale-Data-Immune)

Uses `_read_turn_marker()` from `Stop_unverified_existence_gate.py` to check ONLY tool events from THIS TURN (`id > turn_start_event_id`).

**Prevents**: "I verified 3 hours ago" stale evidence bypass.

## PreToolUse Coordination

Checks for `file_existence_decision_{session_id}.json` state file written by PreToolUse hooks to coordinate overwrite justification.

**If PreToolUse allowed**: Stop guard doesn't double-block.

## Decision Logic

1. **No negative patterns**: Allow (no block)
2. **In obvious allowlist**: Allow (domain knowledge)
3. **Verification found THIS TURN**: Allow (already verified)
4. **PreToolUse justified overwrite**: Allow (coordinated)
5. **No verification**: Block with guidance

## Output Format

```json
{
    "decision": "block",  // or "warn", "allow" (implicit)
    "reason": "Explanation for agent",
    "blocking_hook": "Stop_negative_existence_guard"
}
```

**Warning mode** (evidence unavailable): Non-blocking advisory injected into response

**Block mode** (evidence available, no verification): Exits with code 2 to prevent response

## Example Blocks

### ❌ Blocked (No Verification)
```
"There's no documentation for feature X"
-> No Read/Glob/Grep for docs THIS TURN
-> Block: "Before claiming something doesn't exist, verify it"
```

### ❌ Blocked (Missing File Claim)
```
"The config file is missing"
-> No Bash `ls` or Read attempted THIS TURN
-> Block: "use Read, Glob, Grep, or Bash (ls/find) first"
```

### ✅ Allowed (Obvious Allowlist)
```
"There's no internet access available"
-> Capability statement (domain knowledge)
-> Allow: No verification needed
```

### ✅ Allowed (Verified This Turn)
```
[Uses Glob to check for *.md files]
"There's no README.md file"
-> Glob tool used THIS TURN
-> Allow: Already verified
```

## Test Results

```
Comprehensive Test Suite for Stop_negative_existence_guard.py
======================================================================
✓ No negative patterns
✓ Obvious allowlist - no internet
✓ Obvious allowlist - no config needed
✓ Negative existence - missing file
✓ Negative existence - doesn't exist
✓ Negative existence - no such file
✓ File-specific pattern - no X file
======================================================================
Results: 7 passed, 0 failed
```

## Environment Variables

None required (standalone operation)

## Logging

- **Location**: `P:/.claude/hooks/state/logs/negative_existence_guard.log`
- **Format**: JSON lines with timestamp, level, message
- **Retention**: Indefinite (manual cleanup as needed)

## Integration

1. **Register in settings.json** (not yet done - see task #1428)
2. **Coordinate with PreToolUse_file_existence_guard.py** (state sharing)
3. **Follows hook protocol** from `PROTOCOL.md`

## Related Hooks

- `Stop_unverified_existence_gate.py` - External resources (URLs, repos)
- `StopHook_spec_compliance.py` - Specification deviation detection
- `PreToolUse_file_existence_guard.py` - File overwrite protection (complementary)

## Implementation Date

2026-03-07

## Author

Claude Code (Sonnet 4.6)

## License

Part of Cognitive Steering Framework (CSF) - Constitutional Hooks
