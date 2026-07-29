# Stop Hook `lastAssistantMessage` Payload Field (Systemic Pattern)

**Host provenance:** grok
**Date:** 2026-07-29
**Status:** OBSERVED — 3 hooks fixed this session

## Finding

Grok Build Stop hooks receive the agent's response in `payload["lastAssistantMessage"]` (camelCase), per `user-guide/10-hooks.md:262`. Three separate hook implementations on this host were reading the wrong field names, causing them to silently produce zero detections on every real session.

## Affected hooks

| Hook | Wrong field | Fixed | Date |
|------|------------|-------|------|
| `behavioral_check.py` | `response`, `messages`, `transcript_path` | ✓ Added `lastAssistantMessage` first | 2026-07-28 |
| `wiki_persistence_check.py` | `response`, `messages`, `transcript_path` | ✓ Added `lastAssistantMessage` first | 2026-07-28 |
| `proposal-grounding-monitor/stop_detect.py` | `response`, `last_assistant_message` (snake_case) | ✓ Added `lastAssistantMessage` first | 2026-07-29 |

## Canonical 4-tier extraction pattern

```python
def extract_response_text(payload: dict) -> str:
    # 1. lastAssistantMessage (canonical Grok Build field, camelCase)
    lam = payload.get("lastAssistantMessage")
    if isinstance(lam, str) and lam.strip():
        return lam
    if isinstance(lam, dict):
        t = lam.get("text")
        if isinstance(t, str) and t.strip():
            return t
    # 2. response (legacy field name)
    v = payload.get("response")
    if isinstance(v, str) and v.strip():
        return v
    # 3. messages[-1].content (SDK / Claude-compat shape)
    messages = payload.get("messages")
    if isinstance(messages, list) and messages:
        last = messages[-1]
        if isinstance(last, dict):
            content = last.get("content")
            if isinstance(content, str):
                return content
            if isinstance(content, list):
                texts = [b.get("text", "") for b in content
                         if isinstance(b, dict) and b.get("type") == "text"]
                if texts:
                    return "\n".join(texts)
    # 4. message.content (older single-message shape)
    msg = payload.get("message")
    if isinstance(msg, dict):
        content = msg.get("content")
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            parts = [i.get("text", "") for i in content
                     if isinstance(i, dict) and isinstance(i.get("text"), str)]
            if parts:
                return "\n".join(parts)
    return ""
```

## Why this happened

Grok Build uses camelCase throughout its hook payload (documented at `user-guide/10-hooks.md:281`). Earlier hook code was written for Claude Code's snake_case payload format. When the hooks were ported or written, the field name mismatch wasn't caught because the fail-open behavior (return `""`) produced no error — just silent non-detection.

## Detection

Any Stop hook that reads `payload.get("response")` or `payload.get("last_assistant_message")` without first checking `payload.get("lastAssistantMessage")` is likely broken. Grep for these patterns when auditing hook health.

## Falsifier

Run `grok inspect` to confirm the hook is dispatched, then check `telemetry/stop.jsonl` — if `dispatch_received` events exist but `gate_decision` events are absent or always `FAIL_OPEN`, the hook is hitting the empty-text guard.
