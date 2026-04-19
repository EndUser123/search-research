# Task Contract

## Objective
Fix PreToolUse:Edit hook errors caused by empty stdin in recursive_failure_detector and PreToolUse_investigation_gate

## Scope
**In scope:**
- `recursive_failure_detector.py`: Add empty stdin guard before json.loads()
- `PreToolUse_investigation_gate.py`: Add empty stdin guard before json.loads()

**Out of scope:**
- Other hook files
- Other PreToolUse hooks
- Test files

## Forbidden Files
- None

## Acceptance Criteria
- [ ] Hooks exit 0 (allow) when stdin is empty or whitespace-only
- [ ] Hooks still work correctly with valid JSON input
- [ ] No regression in normal hook operation

## Verification Commands
```bash
echo "" | python .claude/hooks/recursive_failure_detector.py 2>&1; echo "exit: $?"
echo "" | python .claude/hooks/PreToolUse_investigation_gate.py 2>&1; echo "exit: $?"
echo '{"tool_name":"Edit","tool_input":{}}' | python .claude/hooks/recursive_failure_detector.py 2>&1 | head -1
echo '{"tool_name":"Edit","tool_input":{}}' | python .claude/hooks/PreToolUse_investigation_gate.py 2>&1 | head -1
```

## State
- Created: 2026-04-19
- Status: IN_PROGRESS
- Iteration: 0
- Review Depth: quick
