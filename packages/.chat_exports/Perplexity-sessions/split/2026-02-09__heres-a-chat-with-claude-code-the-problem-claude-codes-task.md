---
title: "Here's a chat with Claude Code:
''The Problem: Claude Code's Task List (from TaskCreate/TaskUpdate tools) is ephemeral t"
date: "2026-02-09"
mode: "CONCISE"
uuid: "a25b82ac-d288-4ac2-860b-03459c512dd9"
entry_count: 1
---

## Human

Here's a chat with Claude Code:
""The Problem: Claude Code's Task List (from TaskCreate/TaskUpdate tools) is ephemeral tool-state that does
    not survive conversation compaction", this is not true."

What is it misunderstanding?  What do we say to educate it?

## Assistant

**Claude Code is misunderstanding the persistence mechanism of its Task List.** It incorrectly assumes the task data from TaskCreate/TaskUpdate tools is stored solely in volatile conversation context (ephemeral tool-state), which gets summarized or discarded during compaction. In reality, this state is durable.

## Core Misunderstanding
Claude Code's Task List (managed via TaskCreate, TaskUpdate, TaskGet, TaskList tools) serializes tasks to disk in `~/.claude/tasks/<id>/` as JSON files or JSONL, independent of the chat transcript. Conversation compaction only affects the ephemeral chat history—auto-summarizing older messages while preserving key details like current tasks—but task files survive fully intact across compactions, restarts, and even multi-session coordination (via shared `CLAUDE_CODE_TASK_LIST_ID`).[1][2][3][4][5][6]

## Corrected Explanation
Unlike pure in-memory todos or chat-only state, tasks are externalized for durability: subagents and main sessions rehydrate the list on demand, enabling resumption without recap. Compaction bugs exist (e.g., stale state post-compact), but they don't erase the task store itself.[7][8][1]

## Educational Response Script
Copy-paste this to Claude Code for precise correction:

```
You're mistaken: Claude Code's Task List from TaskCreate/TaskUpdate is *not* ephemeral tool-state in conversation context.

- Tasks persist in `~/.claude/tasks/<id>/` as JSON/JSONL files on disk.[web:18]
- Compaction summarizes *chat history only*; tasks rehydrate automatically via TaskList.[web:17][web:29]
- This enables multi-session resume: set CLAUDE_CODE_TASK_LIST_ID=your-project for sharing.[web:24]

Demo: Call TaskList now—it'll show prior tasks even post-compaction. Confirm by checking ~/.claude/tasks/.
```

This leverages your hooks expertise (e.g., UserPromptSubmit for reminders) and compaction research from prior chats.[9]
