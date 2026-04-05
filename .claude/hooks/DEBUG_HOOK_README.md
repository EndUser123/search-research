# Debug Payload Hook - Quick Reference

**Status**: ✅ **ACTIVE** - Currently logging payloads

**Purpose**: Capture actual Stop and PreToolUse payload structures to understand what fields are available in your Claude Code environment.

---

## 📍 Log Location

```
P:/.claude/state/logs/debug_payloads/
├── Stop_payloads.jsonl          # Summaries (keys present)
├── Stop_full.jsonl               # Complete payloads
├── PreToolUse_payloads.jsonl     # Summaries
├── PreToolUse_full.jsonl         # Complete payloads
└── errors.jsonl                  # Any errors
```

---

## 🚀 How to Use

### 1. **Generate Test Data**

Just use Claude Code normally for 5-10 responses. The hooks will automatically log:
- Every Stop event (after assistant responses)
- Every PreToolUse event (before tool execution)

### 2. **Check What Was Captured**

```bash
# View Stop summaries (keys available)
cat P:/.claude/state/logs/debug_payloads/Stop_payloads.jsonl

# View PreToolUse summaries
cat P:/.claude/state/logs/debug_payloads/PreToolUse_payloads.jsonl

# View full payloads (for detailed inspection)
cat P:/.claude/state/logs/debug_payloads/Stop_full.jsonl | jq -s '.[0]'
cat P:/.claude/state/logs/debug_payloads/PreToolUse_full.jsonl | jq -s '.[0]'
```

### 3. **Look For Key Fields**

**Stop hook should have**:
- `response` (string) - The assistant's response text
- OR raw transcript text
- `session_id` - Session identifier

**PreToolUse hook should have**:
- `tool_name` (string) - Name of tool being called
- `tool_input` (dict) - Parameters for the tool
- Possibly: `recent_messages`, `messages`, `conversation` (if available)

---

## 🛠 How to Remove (When Done)

### Option 1: Manual Removal (Recommended)

Edit `P:\.claude\settings.json` and remove these lines:

**From Stop hooks**:
```json
{
  "type": "command",
  "command": "python P:/.claude/hooks/debug_payload_hook.py Stop",
  "timeout": 2
}
```

**From PreToolUse hooks**:
```json
{
  "type": "command",
  "command": "python P:/.claude/hooks/debug_payload_hook.py PreToolUse",
  "timeout": 2
}
```

### Option 2: Quick Disable (Temporary)

```bash
# Rename the hook file
mv P:/.claude/hooks/debug_payload_hook.py P:/.claude/hooks/debug_payload_hook.py.disabled
```

To re-enable later:
```bash
mv P:/.claude/hooks/debug_payload_hook.py.disabled P:/.claude/hooks/debug_payload_hook.py
```

---

## 📊 What to Look For

### Critical Questions

1. **Stop hook**:
   - ✅ Does it have `response` field?
   - ✅ Does it have `assistant_message` field?
   - ✅ What's the actual structure of the transcript?

2. **PreToolUse hook**:
   - ❌ Does it have `last_assistant_message`? (Perplexity assumes yes, but probably no)
   - ✅ What fields contain the assistant's previous message?
   - ✅ Is there any message history available?

3. **Session tracking**:
   - ✅ What's the `session_id` format?
   - ✅ Can we correlate Stop and PreToolUse events?

---

## 🎯 Next Steps After Discovery

Once you have 5-10 captures:

1. **Review the logs** to see actual field names
2. **Compare with Perplexity assumptions**:
   - Perplexity: `data.get("assistant_message")`
   - Reality: ???
3. **Identify gaps**:
   - Can PreToolUse access previous assistant messages?
   - Is there a message history?
   - What's the correlation mechanism?

4. **Decide on implementation**:
   - If PreToolUse has assistant message: Can implement Perplexity design
   - If not: Need sidecar file or Stop-only enforcement

---

## 🔧 Troubleshooting

### No logs appearing?

```bash
# Check if hook file exists
ls -la P:/.claude/hooks/debug_payload_hook.py

# Check if log directory was created
ls -la P:/.claude/state/logs/debug_payloads/

# Check for errors
cat P:/.claude/state/logs/debug_payloads/errors.jsonl
```

### Hooks causing delays?

The debug hooks have a 2-second timeout. If you notice delays:
1. Remove from settings.json immediately (see removal steps above)
2. Check logs for errors
3. Verify hook isn't stuck in a loop

---

## 📝 Implementation Notes

**Hook behavior**:
- ✅ **Never blocks** - Always returns `{}` (allow)
- ✅ **Read-only** - Only logs, never modifies
- ✅ **Fail-safe** - Catches all exceptions, logs errors
- ✅ **Non-intrusive** - Runs AFTER other hooks

**Log format**:
```json
{
  "timestamp": "2026-03-07T...",
  "event_type": "Stop",
  "top_level_keys": ["response", "session_id", ...],
  "session_id": "...",
  "response_fields": {
    "response": "<string, 1234 chars>"
  }
}
```

---

**Created**: 2026-03-07
**Purpose**: Architecture investigation for behavior guardrails
**Status**: Temporary - remove after data collection
