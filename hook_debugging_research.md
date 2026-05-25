# Claude Code Hook Debugging: Root Cause Analysis Guide

## Research Date
2026-05-24

## Sources
- Claude Code official docs: https://code.claude.com/docs/en/hooks
- Claude Lab debugging guide: https://claudelab.net/en/articles/claude-code/claude-code-hooks-production-debugging-methodology
- DEV Community hooks pitfalls: https://dev.to/yurukusa/5-claude-code-hook-mistakes-that-silently-break-your-safety-net-58l3
- Everything Claude Code troubleshooting: https://lzw.me/docs/opencodedocs/affaan-m/everything-claude-code/faq/troubleshooting-hooks
- GitHub issues: #10875, #34713, #20034, #58558, #10401

## 1. How to Find Which Hook is Causing "Hook JSON Output Validation Failed"

The error means: Claude Code parsed hook stdout but the JSON did not match the expected schema for that event type.

Step 1: Enable Debug Mode - claude --debug hooks
Step 2: Check the Transcript - [DEBUG] Successfully parsed confirms success
Step 3: Plugin vs Inline Hook Behavior (GitHub #10875)

Inline hooks capture stdout. Plugin hooks may skip stdout parsing.

Step 4: Check Event-Specific Allowed Fields

PreToolUse JSON fails on Stop because Stop only accepts {decision, reason, systemMessage}.

Event fields:
- PreToolUse: hookSpecificOutput.permissionDecision, additionalContext.systemMessage
- Stop: decision, reason, systemMessage
- PostToolUse: warning (advisory only, exit must be 0)

## 2. Log File Locations

- Structured errors: ~/.claude/hooks/logs/diagnostics/cc_errors.jsonl
- Hook stderr captures: ~/.claude/hooks/logs/diagnostics/hook_runner_stderr.jsonl
- Startup probe: ~/.claude/hooks/logs/diagnostics/startup_probe.log
- Failsafe fallback: ~/.claude/hooks/logs/diagnostics/failsafe_errors.log

cc_errors.jsonl fields: timestamp, session_id, event, error_type, error_message, stack_trace, error_class, failure_code, is_startup_actionable, root_cause_key.

hook_runner_stderr.jsonl fields: ts, hook, hook_path, session_id, terminal_id, tool_name, cwd, event_kind, stderr_len, stderr (truncated 2000 chars), exit_code.

## 3. Identifying the Failing Hook

Error type format: {hook_name}_{error_category} - e.g. PostToolUse_syntax_error, Stop_runtime_error, Stop_timeout_imminent.

Run hooks in isolation:
echo JSON stdin | python /path/to/hook.py
echo $?  # 0=success, 1=error, 2=block

Minimal reproduction: Create /tmp/hooks-repro with test settings.json

## 4. Best Practices

Shell Profile Interference: Shell profiles contaminate stdout/stderr. Fix: invoke interpreter directly, not through bash wrapper.

Exit Codes:
  0 = Success
  2 = Blocking (PreToolUse blocks tool, Stop forces continuation)
  non-zero not 2 = Non-blocking warning

stdout Rules:
- Emit raw JSON only
- No banners or debug prints
- Human messages to stderr
- Never print() for JSON outside actual response

Stderr (Critical): Claude Code treats ANY stderr as hook error. Hook runner suppresses stderr re-emit and logs to hook_runner_stderr.jsonl instead.

## 5. Common Validation Failure Causes

1. Markdown fencing around JSON
2. Event schema mismatch
3. Shell profile contamination on Git Bash
4. Missing dependencies
5. Exit 2 on PostToolUse (should be 0)
6. sys.exit() in imported modules
7. Import errors (ModuleNotFoundError)

## 6. hook_runner.py Diagnostics System

Custom hook_runner.py provides:
- Structured error classification (timeout, load_failure, runtime_error, known_fixed)
- Multilayer logging (cc_errors.jsonl + hook_runner_stderr.jsonl)
- Startup probe before any imports
- Stop protocol normalization
- Timeout monitoring without stderr

Key: Stderr suppressed and logged to file, not re-emitted to Claude Code process.

## 7. Diagnostic Checklist

- claude --debug hooks for [DEBUG] Hooks output
- Check cc_errors.jsonl for structured errors
- Check hook_runner_stderr.jsonl for raw stderr
- Run hook in isolation with echo JSON | python /path/to/hook.py
- Verify raw JSON (no markdown fences)
- Check settings.json event key spelling
- matcher uses capitalized: Bash, Edit, Write
- Hook paths absolute or ~ (not $HOME)
- Exit code: 0=success, 2=blocking

## 8. Known False-Positive Bug

GitHub #34713: Hook executions incorrectly labeled hook error even with exit 0, no stderr, valid JSON. This is a Claude Code UI bug, not a hook failure.

If hook_runner_stderr.jsonl shows exit_code: 0 and stderr_len: 0 but transcript shows hook error, the hook actually ran successfully.

## Evidence from Local Logs

PostToolUse_router hits TypeError: __bases__ assignment in hook base class.
Stop hooks hit AttributeError: UNKNOWN - TurnMode enum refactoring artifact.
Stop hooks hit NameError: name anomalies/user_prompt - removed variables with remaining references.
