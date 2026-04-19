## Summary
- **Root cause**: `recursive_failure_detector.py` and `PreToolUse_investigation_gate.py` call `json.loads(sys.stdin.read())` without checking if stdin is empty
- **Symptom**: `JSONDecodeError: Expecting value: line 1 column 1` surfacing as PreToolUse:Edit hook errors in UI
- **Fix**: Read stdin first, check if whitespace-only, exit 0 (allow) if empty

## Files
- `.claude/hooks/recursive_failure_detector.py` (+5 lines)
- `.claude/hooks/PreToolUse_investigation_gate.py` (+4 lines)
- `.claude/hooks/tests/test_pretooluse_empty_stdin_fix.py` (new, 6 tests)

## Verification
```
# Empty stdin - both exit 0, no error
echo "" | python recursive_failure_detector.py → exit 0, {"continue": true}
echo "" | python PreToolUse_investigation_gate.py → exit 0

# Valid JSON - both work correctly
echo '{"tool_name":"Edit","tool_input":{}}' | python recursive_failure_detector.py → {} (exit 0)
echo '{"tool_name":"Edit","tool_input":{}}' | python PreToolUse_investigation_gate.py → {"decision": "approve"} (exit 0)

# Regression tests: 6/6 pass
pytest tests/test_pretooluse_empty_stdin_fix.py -v → 6 passed
```

## Review
Depth: quick
Required passes: correctness PASS, scope PASS, pr-ready PASS

🤖 Generated with [Claude Code](https://claude.ai/claude-code)
