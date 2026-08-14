---
title: "does the github repos from disler have a hook system to record all user messages and tool use to a jsonl file?"
date: "2026-03-31"
mode: "COPILOT"
uuid: "18b1b52e-1b8e-4a37-b5fd-9a2b0d9bf77f"
entry_count: 9
---

## Human

does the github repos from disler have a hook system to record all user messages and tool use to a jsonl file?

## Assistant

No, Disler's GitHub repos (primarily claude-code-hooks-mastery and claude-code-hooks-multi-agent-observability) implement a hook system for Claude Code that captures user messages (via UserPromptSubmit hook) and tool use (via PreToolUse/PostToolUse hooks), but they send events via HTTP POST to a Bun/Socket server storing in SQLite—not directly to a jsonl file.[1][2]

## Hook Coverage
- **User Messages**: user_prompt_submit.py logs prompts; send_event.py transmits as JSON payload with prompt text.[2][1]
- **Tool Use**: pre_tool_use.py/post_tool_use.py capture tool name, inputs, outputs, results; transmitted similarly.[1][2]
- **Storage**: Events → HTTP → SQLite db (events.db); no local jsonl append observed in hooks or config.[1]

## Data Flow
Hooks like send_event.py POST JSON (e.g., {"source_app": "...", "session_id": "...", "hook_event_type": "UserPromptSubmit", "payload": {...}}) to localhost:4000/events; server inserts to DB, broadcasts via WebSocket.[1]

## Customization
To adapt for jsonl: Modify send_event.py or add a post-hook command like `echo '$JSON' >> events.jsonl` in .claude/settings.json. Requires uv/Python; test via repo's start-system.sh.[1]

Next step: Clone https://github.com/disler/claude-code-hooks-multi-agent-observability, inspect .claude/hooks/*.py for payloads.[2]

## Human

what advantage does disler offer over what claude does natively?

## Assistant

Disler's repos (claude-code-hooks-mastery, claude-code-hooks-multi-agent-observability) extend Claude Code's native hooks with pre-built, production-ready implementations for deterministic control, multi-agent observability, and workflow enforcement—beyond basic shell script triggers.[1][2][3]

## Key Advantages
- **Ready-Made Hooks**: 13 lifecycle hooks (e.g., PreToolUse blocks rm -rf; PostToolUse logs JSON) with Python/uv scripts for security, validation, notifications—native requires manual .claude/settings.json scripting.[4][3][1]
- **Multi-Agent Observability**: Real-time Bun TS server + SQLite + WebSocket dashboard tracks concurrent agents (events, sessions, transcripts); native lacks visualization/storage.[2][5]
- **Deterministic Enforcement**: 100% compliance via interceptors (e.g., linting, .env blocking) vs. native's probabilistic prompts/instructions.[6]

## Native vs. Disler Comparison

| Aspect              | Native Claude Code Hooks [3] | Disler Extensions [2][1] |
|---------------------|-----------------------------------|----------------------------------|
| Setup              | Manual shell cmds in settings.json | Clone repo, run start-system.sh; auto-migrates DB |
| Observability      | Stdout/JSON stdin only            | HTTP→SQLite→live dashboard/WebSocket |
| Multi-Agent        | Single-instance support           | Session IDs, parallel tracking, pulse charts |
| Examples           | Basic (e.g., say "done")          | Security filters, MCP logging, voice alerts |
| Reliability        | User-script dependent             | Battle-tested Python hooks + server |

Next step: `git clone https://github.com/disler/claude-code-hooks-multi-agent-observability && cd $_ && ./start-system.sh` to deploy locally.[2]

## Human

I mean for session transcripts.  claude saves them all, so does disler offer something more otehr than in sqlite?

## Assistant

Disler offers session transcript observability beyond Claude's native JSONL storage (~/.claude/projects/*/*.jsonl, deletable via cleanupPeriodDays=0) via real-time capture, multi-agent tracking, and interactive visualization—SQLite stores granular events (prompts, tools, outputs), not raw transcripts.[1][2]

## Native Claude Transcripts
Claude auto-saves full session JSONL (user/assistant turns, timestamps, tools); accessible via API or tools like claude-code-transcripts for HTML export. No built-in dashboard or multi-session filtering; inactive sessions auto-delete after 30 days (configurable).[3][4][2]

## Disler Enhancements
- **Real-Time Events**: Hooks (UserPromptSubmit, Pre/PostToolUse) send JSON payloads (prompts, tool inputs/outputs, session_id) to Bun server → SQLite (events.db, WAL for concurrency).[5]
- **Transcript Storage**: ChatTranscriptModal.vue views history; `--add-chat` flag includes context; Stop/SubagentStop hooks capture summaries/transcripts.[5]
- **Beyond SQLite**: Live Vue dashboard (localhost:5173) with WebSocket streaming, filters (app/session/type), pulse charts, event timeline—no native equivalent.[1][5]

## Feature Comparison

| Capability          | Native Claude [2][1] | Disler [5][1]          |
|---------------------|--------------------------------|---------------------------------|
| Storage Format     | JSONL files per session        | SQLite events + chat payloads   |
| Access             | Filesystem/API, post-hoc tools | Real-time WS dashboard          |
| Multi-Agent        | Single-session files           | Session_id tracking, subagents  |
| Filtering/Search   | Manual grep/CLI tools          | UI multi-select (type/app/time) |
| Export             | JSONL/HTML via 3rd-party       | Query SQLite; no built-in jsonl |

**No direct jsonl append**; query `events.db` (e.g., `sqlite3 events.db "SELECT * FROM events WHERE hook_event_type='UserPromptSubmit'"`) for transcripts. Next step: After `./start-system.sh`, inspect `apps/server/events.db` schema via sqlite CLI.[5]

## Human

are there other repos that do a better job or have more useful features for session capture and analysis?

## Assistant

Several repos outperform Disler in session capture/analysis with richer features like production tracing (Langfuse), interactive HTML exports (claude-code-transcripts), typed parsing/JSONL logging (claude-log), or live SSE dashboards (ObservAgent)—focusing on usability, schemas, and integrations beyond SQLite events.[1][2][3][4]

## Top Alternatives
| Repo | Key Features | Stars/Edge over Disler [ et al.] |
|------|--------------|---------------------------------------|
| [doneyli/claude-code-langfuse-template](https://github.com/doneyli/claude-code-langfuse-template) | Hooks → Langfuse (self-hosted/cloud); traces, metrics, LLM eval, sessions UI/search/export [1] | Prod-ready observability stack; analytics/queries > basic DB |
| [simonw/claude-code-transcripts](https://github.com/simonw/claude-code-transcripts) | CLI converts native JSONL to multi-page HTML transcripts; web/local/gist export, agent incl. [2][5] | Shareable browsable views; no hooks/server needed |
| [lw100/claude-log](https://github.com/lw100/claude-log) (via Reddit) | Hook script → ~/claude-log.jsonl; parse.py with Pydantic models for transcripts/tools/hooks [4] | Typed schemas, direct JSONL; simple audit |
| ObservAgent (HN-linked) | Hooks → Fastify/SQLite/SSE React dashboard; live visibility, no code mods [3] | Real-time streaming like Disler but lighter relay |

## Capture/Analysis Strengths
- **Langfuse**: Full lifecycle traces (hooks + native JSONL ingest); eval frameworks, cost tracking; scales to teams.[1]
- **claude-code-transcripts**: Post-capture analysis; interactive timelines, thinking traces; GitHub Gist sharing.[2]
- Disler remains strong for multi-agent real-time (Vue dashboard, subagent tracking) but lacks schemas/export depth.[6]

Next step: `uv tool install claude-code-transcripts; claude-code-transcripts all --open` for instant transcript archive from native files.[2]

## Human

I don't really need live viewing of hooks and agents.  It's ok for me to find out what happened after.  I do use them for troubleshooting hooks and workflows a lot.

## Assistant

For post-hoc troubleshooting of hooks/workflows via session transcripts (aligning with your heavy use of failure_recorder_hook.py, review_investigation_loops.py, and transcript analysis on thousands of sessions), prioritize simple JSONL append/parsing tools over live dashboards—these enhance native ~/.claude/projects/*/*.jsonl with grep-able logs and schemas without runtime overhead.[1][2]

## Recommended Repos
- **lw100/claude-log**: Hook → ~/claude-log.jsonl (user/prompt/tool/output); parse.py with Pydantic for queries (e.g., filter failures/hooks). Ideal for your debugging patterns—grep "failure_recorder" across logs.[2]
- **simonw/claude-code-transcripts**: CLI aggregates native JSONL to searchable HTML (per-session/multi); timelines for hook/tool flows. No hooks needed; run post-session: `claude-code-transcripts all`.[1][3]
- **doneyli/claude-code-langfuse-template**: Optional hooks → Langfuse DB/JSON export; SQL queries on traces (e.g., hook failures). Skip UI; use traces API for batch analysis.[4]

## Setup for Troubleshooting
1. Add to .claude/settings.json: `"postToolUseCommand": "echo '{\"type\":\"tool\",\"name\":\"$CLAUDE_TOOL_NAME\",\"args\":$CLAUDE_TOOL_ARGS,\"output\":$CLAUDE_TOOL_RESULT}' >> hooks.jsonl"` (native, no repo).[5]
2. `git clone https://github.com/lw100/claude-log; cd claude-log; ./install-hook.sh`—auto-logs hooks to JSONL.
3. Query: `jq 'select(.hook=="failure_recorder") | .error' hooks.jsonl | sort | uniq -c` for patterns.

These beat Disler for your offline needs (no server/SQLite); claude-log adds schemas matching your verification guardrails. Next step: Test claude-log hook on a failure workflow, grep for investigation_loops.[2]

## Human

do they nullify the problem of claude code purging jsonl files older than 30 days?

## Assistant

No, repos like claude-log, claude-code-transcripts, and Langfuse templates do **not** prevent native JSONL purging (after cleanupPeriodDays=30 inactivity, based on lastActiveAt)—they either process **existing** files or use hooks for **parallel** external logs, leaving originals vulnerable.[1][2][3]

## Purge Mechanics
Native ~/.claude/projects/<hash>/*.jsonl auto-deletes post-30 days inactivity (cron-like); set `"cleanupPeriodDays": 99999` in ~/.claude/settings.json for ~274-year retention (can't fully disable; 0 breaks writes).[4][2][1]

## Repo Mitigation
| Repo/Tool | Handles Purge? | How [ et al.] |
|-----------|----------------|--------------------|
| claude-log | Partial (hooks → external JSONL) | PostToolUse/etc. appends to ~/claude-log.jsonl; survives purge |
| claude-code-transcripts | No (reads natives) | CLI exports to HTML **before** purge: `claude-code-transcripts all --output ~/archive` |
| Langfuse template | Yes (external) | Hooks → Langfuse DB/JSON; optional cron export |
| Native config | Partial | High cleanupPeriodDays delays purge |

**Best for you**: Combine `cleanupPeriodDays: 99999` + claude-log hooks for permanent troubleshooting archive (grep failures_investigation_loops). Next step: `echo '{"cleanupPeriodDays":99999}' > ~/.claude/settings.json; claude restart` then add claude-log.[5][1]

## Human

what does claude-log use as a permanent data store for the log info?

## Assistant

**claude-log** (ljw1004/claude-log from Reddit author) uses a single **permanent JSONL file at `~/claude-log.jsonl`** as its datastore—hooks append full transcripts + hook activities in real-time, bypassing native purge entirely.[1][2]

## Storage Details
- **Format**: NDJSON lines with typed Pydantic schemas (prompts, tools, hooks, tokens: e.g., `{"type": "user", "content": "...", "tokens": {"read-input": 22239}}`).[1]
- **Hooks**: Install `log-hook.sh` as PostToolUse/UserPromptSubmit/etc. in .claude/settings.json; captures `$CLAUDE_FULL_TRANSCRIPT` + metadata.[1]
- **Persistence**: Home-dir file survives ~/.claude cleanup; no DB/server. Parse via `parse.py` for queries (e.g., `python parse.py --filter hook=failure_recorder`).[1]
- **Size/Perf**: Append-only; grep/jq friendly for your workflows (e.g., `grep -i investigation ~/claude-log.jsonl`).

Confirms Reddit: "logs all interactions into ~/claude-log.jsonl". Next step: `git clone https://github.com/ljw1004/claude-log; cd claude-log; ./install.sh` (adapt shell for Calgary MDT locale if needed).[1]

## Human

how is it functionally different than claude-history?

## Assistant

**claude-log** (ljw1004's hook-based logger → `~/claude-log.jsonl`) is **proactive** (real-time hook capture to purge-proof external file with Pydantic schemas for tool/hook parsing), while **claude-history** (raine/claude-history CLI) is **reactive** (fuzzy-searches native `~/.claude/projects/*/*.jsonl` files, vulnerable to 30-day purge).[1][2][3]

## Functional Differences

| Aspect | claude-log [3][4] | claude-history [1][2] |
|--------|-----------------------------|---------------------------------|
| Capture | Hooks append to external JSONL (PostToolUse etc.) | Scans native JSONL post-hoc |
| Purge Immunity | Full (external store) | None (reads purgeable natives) |
| Output | Structured NDJSON + parse.py queries | Fuzzy CLI search (ripgrep + fzf) |
| Hooks/Tools | Typed schemas (tool args/outputs) | Basic text search |
| Install | Hook scripts to settings.json | `cargo install claude-history` |
| Troubleshooting | Grep schemas for failures (your loops/hooks) | Keyword search sessions |

claude-log fits your post-hoc debugging (e.g., `jq '.[] | select(.hook=="failure_recorder")' ~/claude-log.jsonl`); claude-history for quick native lookups pre-purge. Next step: Prioritize claude-log hooks for permanent archive; test `claude-history search "investigation_loop"` on currents.[3][2]

## Human

best alternatives to claude-history and claude-log

## Assistant

Top alternatives to claude-history (native-search CLI) and claude-log (hook JSONL) emphasize richer post-hoc analysis, purge-proof exports, and visuals for troubleshooting—e.g., HTML archives (claude-code-transcripts), desktop apps (claude-devtools), web UIs (kamahmed/claude-run).[1][2][3]

## Best for Troubleshooting
| Repo | Strengths | Purge Handling | Setup |
|------|-----------|----------------|-------|
| [simonw/claude-code-transcripts](https://github.com/simonw/claude-code-transcripts) | Multi-page HTML timelines; tool views; Gist-shareable; `all` → archive [3][4] | Export pre-purge | `uv tool install claude-code-transcripts` |
| [jhlee0409/claude-code-history-viewer](https://github.com/jhlee0409/claude-code-history-viewer) | Unified search/visuals (tools/git/term); handles large histories; auto-refresh [5] | Reads natives (export option) | Desktop app (Electron?) |
| [kamahmed/claude-run](https://github.com/kamahmed/claude-run) (npx) | Browser UI by project; live-stream + history; keyword/date filter [2] | Scans natives | `npx claude-run` |
| [matt1398/claude-devtools](via awesome) | Desktop observability; session analysis/logs [1] | Likely export | Download app |
| [AshleyT3/llm-prompts-and-tools](JSONL→MD) | Offline VSCode/grep search; stdlib Python [6] | Converts to MD files | Clone + run script |

claude-code-transcripts edges for shareable, detailed hook/tool flows matching your workflows. Next step: `uv tool install claude-code-transcripts; claude-code-transcripts all --output ~/transcripts` for instant archive.[3]
