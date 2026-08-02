---
title: "Grok Build session transcript format: tool call data lives in updates.jsonl, not chat_history.jsonl"
created: 2026-08-01
source: session-019fbf02
tags: ['grok-build', 'transcript-format', 'session-parsing', 'tool-calls', 'debugging']
summary: >
  When parsing Grok Build session transcripts for tool call details (tool
  name, arguments, file paths), target updates.jsonl not chat_history.jsonl.
  chat_history.jsonl stores assistant content as plain strings, not
  structured tool_use blocks. The structured tool call data lives in
  updates.jsonl under params.update.sessionUpdate with type 'tool_call'.
agent: grok
cognitive_load: 3
verification: observed
host: grok
relations:
  - target: wiki/concepts/grok-build-stop-hook-agent-text.md
    type: refines
  - target: wiki/concepts/quality-gate-hook-system-implementation.md
    type: complements
  - target: wiki/concepts/conversation-distillation-review-packet-export.md
    type: related
---

# Grok Build session transcript format: tool call data lives in updates.jsonl

## Decision context

**Why this knowledge was needed:** session 019fbf02 needed to extract tool
call data (which tools were called, which files were written, which commands
run) from the session transcript for `/recap-grok`. The natural assumption
was that `chat_history.jsonl` — the file named "chat history" — would contain
structured tool call blocks (like Anthropic's format where assistant messages
contain a list of content blocks including `tool_use` types). This assumption
was wrong and cost 10 Python errors (8 Tracebacks + 2 SyntaxErrors) before
the correct data source was found.

## Key findings

### chat_history.jsonl structure

Each line is a JSON object with `type` and `content` keys:

| type | content shape | What it contains |
|------|---------------|------------------|
| `system` | string | System prompt |
| `user` | list of text blocks | User messages (with `<user_query>` tags inside) |
| `reasoning` | string | Thinking/reasoning traces |
| `assistant` | **string** (not a list of blocks) | Agent response text — plain string, no structured tool_use |
| `tool_result` | string | Tool output |

**The critical discovery:** assistant entries store `content` as a **plain
string**, not as a list of structured content blocks. There is no `tool_use`
block type inside assistant content. A parser that iterates assistant
`content` looking for tool calls will find nothing.

The `quality-gate-hook-system-implementation.md` concept mentions a top-level
`tool_calls` array on some entries — this may exist on certain entry types
but was not present on the assistant entries in session 019fbf02. The reliable
source for tool call data is updates.jsonl.

### updates.jsonl structure (the correct source)

Each line has `{timestamp, method, params}` where `params.update` contains
a `sessionUpdate` field identifying the update type:

| sessionUpdate type | What it contains |
|--------------------|------------------|
| `tool_call` | **Structured tool call data** — `title` (tool name), `rawInput` (arguments dict), `toolCallId` |
| `tool_call_update` | Status update for an in-progress tool call |
| `user_message_chunk` | User message text (streamed) |
| `agent_thought_chunk` | Agent reasoning text (streamed) |
| `agent_message_chunk` | Agent response text (streamed) |
| `hook_execution` | Hook firing record |
| `plugins_changed` | Plugin state change |

To extract tool calls:
```python
# CORRECT: read updates.jsonl for structured tool call data
for line in updates_path:
    entry = json.loads(line)
    update = entry.get("params", {}).get("update", {})
    if update.get("sessionUpdate") == "tool_call":
        tool_name = update.get("title", "")
        raw_input = update.get("rawInput", {})
        file_path = raw_input.get("file_path", raw_input.get("target_file", ""))
```

### When to use which file

| Task | File to read |
|------|-------------|
| Extract tool calls (name, args, file paths) | `updates.jsonl` |
| Read assistant response text | `chat_history.jsonl` (type=assistant) |
| Read user messages | `chat_history.jsonl` (type=user, extract from `<user_query>` tags) |
| Scan for friction patterns (exit codes, errors) | `chat_history.jsonl` (text search via Select-String) |
| Build the AAR evidence packet | Use the AAR preprocessor (`full_preprocessor.py`) — it handles both files |

## What this means for our workspace

**Stop writing `python -c` scripts that try to parse chat_history.jsonl for
tool call data.** They will fail because the data isn't there. Either:

1. Write a parser script to `P:/tmp/` that targets `updates.jsonl`, OR
2. Use the AAR preprocessor (which already handles both files correctly), OR
3. Use `Select-String` for text-pattern scanning (works on chat_history.jsonl for string matching, just not for structured extraction)

The AAR preprocessor (`full_preprocessor.py`) already parses both files
correctly and produces a canonical events stream. For anything more complex
than text scanning, prefer the preprocessor over hand-rolled parsing.

## Falsifier

If a future Grok Build update adds structured `tool_use` blocks to
`chat_history.jsonl` assistant entries (aligning with the Anthropic format),
this finding becomes obsolete. Check the entry structure before assuming
updates.jsonl is still required.

## Receipts

- Session 019fbf02 `chat_history.jsonl`: type distribution = {system:1, user:8, reasoning:46, assistant:72, tool_result:88} — assistant content is string type, verified by `json.loads` + `isinstance(content, str)` check
- Session 019fbf02 `updates.jsonl`: `params.update.sessionUpdate` distribution verified — `tool_call` entries contain `title` and `rawInput` fields with structured arguments
- [[grok-build-stop-hook-agent-text]] documents the chat_history.jsonl structure for Stop hooks (reading assistant text) but does not cover tool call extraction
- [[conversation-distillation-review-packet-export]] ships a parser for chat_history.jsonl but targets conversation distillation, not tool call extraction
- [[session-arc-scan-transcript-as-external-memory]] documents the transcript-as-ground-truth principle that motivated the parsing attempt
- [[multi-agent-transcript-race-condition-check-preprocessor]] documents the session directory structure and encoded paths used to locate transcripts

## Auto-related

- [[skill-catalog]]
- [[skill-graph]]
- [[claude-code-external-tool-integration-via-mcp]]
- [[claude-code-cli-agent-configuration-and-workflow-patterns]]
- [[router-proxy-tool-calling-normalization-patterns]]

