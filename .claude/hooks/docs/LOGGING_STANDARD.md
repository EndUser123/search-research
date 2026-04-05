# Hook Logging Standard

## Log File Locations

| File | Purpose | Retention |
|------|---------|-----------|
| `logs/enforcement.jsonl` | Blocks, warnings, forced actions | 7 days |
| `logs/diagnostics/hook_invocations.jsonl` | All hook calls (debug) | 1 day |
| `logs/diagnostics/decisions.jsonl` | Decision audit trail | 3 days |

## Storage Policy

- SQLite (`logs/diagnostics/diagnostics.db`) is the authoritative store for
  structured, query-worthy events.
- JSONL remains valid for high-volume traces, bootstrap/failsafe logging, and
  append-only RCA streams where file tailing is useful.
- `logs/diagnostics/pretooluse_blocks.jsonl` is the canonical flat-file stream
  for `PreToolUse` block diagnostics.
- Avoid duplicate sinks for the same event unless one is explicitly a fallback.

## Entry Schema (JSONL)

### Hook Decision Entry (enforcement.jsonl)
```json
{
  "ts": "2026-01-30T15:30:00.123Z",
  "hook": "PreToolUse_hook_edit_gate",
  "type": "PreToolUse",
  "decision": "block",
  "tool": "Edit",
  "reason": "Hook not tested before edit",
  "latency_ms": 12.5,
  "session_id": "abc123",
  "terminal_id": "term_1"
}
```

### Router Orchestration Entry (hook_invocations.jsonl)
```json
{
  "ts": "2026-01-30T15:30:00.100Z",
  "router": "PostToolUse_router",
  "type": "PostToolUse",
  "tool": "Edit",
  "hooks_executed": ["fix_validator", "change_verification"],
  "total_latency_ms": 45.2,
  "any_blocked": false,
  "session_id": "abc123"
}
```

## Required Fields

- `ts`, `hook`/`router`, `type`, `decision` (hooks only)

## Optional Fields

- `tool`, `reason`, `latency_ms`, `session_id`, `terminal_id`, `ctx`

## Decision Values

- `allow`: Hook passed, no intervention
- `block`: Hook blocked action (exit code 2)
- `warn`: Hook injected warning but allowed
- `skip`: Hook not applicable to this input
- `error`: Hook failed internally
