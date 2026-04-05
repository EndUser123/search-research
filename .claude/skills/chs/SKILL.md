---
name: chs
description: Dedicated chat history search with summarization, workspace aliases, tool filtering, context preview, session stats, and branch filtering
category: chat-history
version: 1.0.0
status: stable
enforcement: advisory
aliases:
  - /chat-history
  - /history-search

suggest:
  - /search
  - /all
  - /cks
  - /top-problems

do_not:
  - duplicate /search functionality - use this for chat-specific workflows
  - load full conversations into context unnecessarily
  - skip the two-stage search architecture
---

# Chat History Search (/chs)

## Purpose

Dedicated search for Claude Code chat history with advanced features: summarization modes, workspace aliases, tool filtering, context preview, session statistics, and branch filtering.

**Why /chs instead of /search?**
- `/search` = Unified search across all sources (chat + knowledge + code + docs)
- `/chs` = Chat-specific workflows with dedicated features for conversation analysis

## Project Context

### Technical Architecture
- **Primary CLI**: `P:/packages/search-research/skills/chs/scripts/chs_cli.py`
- **CHS Backend**: Reuses existing CHS infrastructure from `/search`
- **Two-Stage Search**: Lightweight index → Deep content scan (on-demand)
- **Storage**: SQLite metrics database at `P:/packages/search-research/data/chs_metrics.db`

### Consolidation History
- Previously part of `/search` (consolidated old `/chs`, `/recent`, `/search-more`)
- Now re-extracted as dedicated chat history skill with advanced features
- `/search` handles unified queries; `/chs` handles chat-specific workflows

## Your Workflow

1. **Parse query** - Extract filters (workspace, tool, branch, date, mode)
2. **Stage 1 search** - Lightweight index-only search (firstPrompt, summary fields)
3. **Check results** - If insufficient, trigger Stage 2
4. **Stage 2 search** - Deep JSONL content scan (only when needed)
5. **Apply filters** - Tool, branch, workspace, date filters
6. **Generate output** - Summary, context preview, or full details
7. **Optional summarization** - Apply selected summarization mode

## Seven Key Features

### 1. Summarization Modes

Transform raw chat history into structured documentation.

| Mode | Description | Use Case |
|------|-------------|----------|
| `documentation` | Full technical doc: problem, changes, patterns, lessons | Deep dive into complex sessions |
| `short-memory` | MEMORY.md-ready bullets (500-2000 chars) | Quick knowledge capture |
| `changelog` | Added/Changed/Fixed/Removed with file paths | Track what changed over time |
| `debug-postmortem` | Symptoms, investigation, dead ends, root cause, fix | Learn from debugging sessions |
| `onboarding` | "How this works" for new devs | Team knowledge transfer |

Usage: `/chs "query" --mode <mode>` -- See `references/examples.md` for mode-specific examples.

### 2. Two-Stage Search Architecture

**Stage 1 (Fast):** Index-only search (~10ms) -- `firstPrompt`, `summary`, `terminalId`, `branch`, `timestamp`.
**Stage 2 (Deep):** Full JSONL content scan (~500ms) -- all message content, tool results, thinking blocks.

Default is `--stage auto` (Stage 1 first, Stage 2 on-demand). Key principle: never load full conversations unnecessarily.

### 3. Workspace Aliases

Group related workspaces for unified search. Define in `~/.claude/chs_config.json`.

Usage: `/chs "query" --workspace-alias <alias>` -- See `references/configuration.md` for setup.

### 4. Tool-Based Filtering

Find conversations by tool usage (Edit, Write, Bash, Read, Grep, Glob, Task, Agent, LSP, etc.).

Usage: `/chs --tool <Tool> --file "<pattern>"` -- See `references/examples.md` for tool filter examples.

### 5. Context Window Preview

Show surrounding messages without loading full conversation.

Usage: `/chs show <session-id> --context <N>` -- See `references/examples.md` for preview examples.

### 6. Session Statistics Dashboard

Metrics: sessions per workspace, average length, most-used tools, terminal mapping, branch distribution, time patterns.

Usage: `/chs stats [--workspace <ws>] [--since <date>]`

### 7. Branch-Based Filtering

Search conversations by git branch: `/chs "query" --branch "<branch-name>"`

## Command Reference

See `references/command-reference.md` for full command syntax covering basic search, filter options, output options, session management, and advanced options.

## Configuration

See `references/configuration.md` for config file format (`~/.claude/chs_config.json`), workspace aliases setup, and `/search` integration guidance.

## Examples

See `references/examples.md` for practical examples covering all seven features including summarization modes, two-stage search, tool filtering, branch filtering, and session statistics.

## Implementation Notes

- **Reuses existing CHS backend** from `/search` for consistency
- **Two-stage architecture** ensures fast initial results
- **Summarization modes** use LLM templates for structured output
- **Tool filtering** parses JSONL content for tool usage patterns
