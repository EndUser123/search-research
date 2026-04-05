# Dependency Verification Gate - Implementation Plan

## Overview

Create `PreToolUse_dependency_verification_gate.py` to prevent "lazy configuration errors" where AI makes package-related changes without verifying external dependencies exist first.

## Architecture

**Module:** `P:\.claude/hooks/PreToolUse_dependency_verification_gate.py`

**Components:**
1. **Pattern Detection** - Regex for npm/pip/cargo install commands
2. **Verification Command Detection** - Allow npm view, npm search, pip search
3. **Blocking Logic** - Exit code 2 for unverified installs
4. **Error Messages** - Guide AI to verify first
5. **Configuration** - ENV var toggle (DEPENDENCY_VERIFICATION_ENABLED)

**Interfaces:**
- Input: JSON via stdin (tool_name, tool_input)
- Output: JSON decision or sys.exit(2) to block
- Registration: settings.json PreToolUse hooks

## Data Flow

```
Bash tool called
    ↓
HookImporter loads dependency_verification_gate
    ↓
Parse stdin JSON
    ↓
Check if tool_name == "Bash"
    ↓
Extract command from tool_input
    ↓
Match package manager patterns (npm/pip/cargo)
    ↓
Is this a verification command?
    ├─ YES → Allow (exit 0)
    └─ NO  → Block with error message (exit 2)
```

## Error Handling

**Patterns detected:**
- `npm install @scope/package`
- `npm install package-name`
- `pip install package-name`
- `cargo add crate-name`

**Verification commands allowed:**
- `npm view package`
- `npm search package`
- `pip search package`
- `cargo search package`

**Error message format:**
```
**Unverified Package Reference Detected**

The command references npm package '@scope/package' without prior verification.

Before installing, verify the package exists:
  npm: npm view @scope/package
  pip: pip search package-name
  cargo: cargo search crate-name

Command: npm install @scope/package
```

## Test Strategy

### Unit Tests

**Positive cases (should block):**
1. `npm install @scope/package` - Block with message
2. `npm install package-name` - Block with message
3. `pip install package-name` - Block with message
4. `cargo add crate-name` - Block with message

**Negative cases (should allow):**
1. `npm view @scope/package` - Allow (verification)
2. `npm search package` - Allow (verification)
3. `pip search package` - Allow (verification)
4. `cargo search package` - Allow (verification)
5. `git commit -m "message"` - Allow (not package-related)
6. Non-Bash tools - Allow (not Bash command)

**Edge cases:**
1. Empty command - Allow
2. Malformed JSON - Allow
3. Command with multiple flags - Still detect pattern
4. Local package installs (`./path`) - Allow (not a registry package)

## Standards Compliance

**Python standards** (`/code-python`):
- Type hints for all functions
- f-strings for formatting
- Pathlib for file paths
- logging for errors (not print)
- pytest for tests

**Universal standards** (`/code-standards`):
- DRY - Single pattern matcher function
- Single responsibility - Only verifies dependencies
- Clear error messages - Guides user to verification
- Testable - Pure functions where possible

## Ramifications

**Impact on existing code:**
- New hook file created
- settings.json updated with PreToolUse hook registration
- No breaking changes to existing hooks

**Backwards compatibility:**
- Disabled by default (DEPENDENCY_VERIFICATION_ENABLED=false)
- Users can enable via env var
- Can bypass with --allow flag if needed

**Performance:**
- Pattern matching: <5ms per Bash command
- No subprocess overhead (HookImporter in-process)
- Only runs for Bash tool calls

## Pre-Mortem Analysis

**Failure Mode 1: False positives blocking legitimate work**
- Root cause: Overly broad regex patterns
- Prevention:
  - Test with adversarial inputs
  - Add exclusion patterns for local installs
  - User can disable with env var

**Failure Mode 2: Verification commands blocked**
- Root cause: Incomplete whitelist of verification commands
- Prevention:
  - Test all common verification commands (view, search, show)
  - Add tests for each package manager

**Failure Mode 3: Hook slows down all Bash commands**
- Root cause: Expensive regex or slow pattern matching
- Prevention:
  - Pre-compile all regex patterns
  - Early exit for non-Bash tools
  - Performance test with 100+ iterations

## Observability Planning

**Metrics to track:**
- How often does the hook block? (Counter in logs)
- Which package managers are most problematic? (Pattern distribution)
- False positive rate? (User overrides)

**Alerting:**
- High block rate (>10% of Bash commands) → Review patterns
- New package manager detected → Add support

**Where to look during diagnosis:**
- Logs: `P:/.claude/hooks/state/logs/dependency_verification.log`
- State files: `P:/.claude/hooks/state/dependency_verification_*.json`

## Implementation Tasks

1. **RED:** Write failing tests for all positive/negative cases
2. **GREEN:** Implement hook to pass all tests
3. **REFACTOR:** Clean up code, add type hints, improve error messages
4. **VERIFY:** Independent verification of correctness

## Success Criteria

- [ ] All tests pass (unit + integration)
- [ ] Blocks unverified package installs
- [ ] Allows verification commands
- [ ] Error messages are clear and actionable
- [ ] Performance <10ms per check
- [ ] Registered in settings.json
- [ ] Documented in CLAUDE.md
