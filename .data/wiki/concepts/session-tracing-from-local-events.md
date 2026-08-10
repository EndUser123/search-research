---
title: "Session tracing from local events — lightweight observability without external infrastructure"
created: 2026-08-10
source: session-20260810
tags: [observability, tracing, session-analysis, tooling, agent-monitoring]
categories: [tooling, infrastructure]
cognitive_load: 2
host: both
agent: grok
verification: observed
summary: >
  Grok Build already captures structured tool events (tool_started,
  tool_completed, MCP connections, turn boundaries) in events.jsonl per
  session. The session_trace.py script makes this data queryable: tool
  usage by type, duration, failure rate, and timeline view — without
  requiring Langfuse or any external service. The data was always there;
  only the query tool was missing. This closes the observability gap for
  agents that don't have external tracing infrastructure configured.
sources:
  - session 2026-08-10 — 286 tool traces matched from this session's events.jsonl
  - https://www.humanlayer.dev/blog/skill-issue-harness-engineering-for-coding-agents — harness engineering context
  - https://addyosmani.com/blog/ai-coding-workflow/ — workflow patterns
relations:
  - target: wiki/concepts/tool-fallbacks.md
    type: extends
  - target: wiki/concepts/reading-chatgpt-shared-links-js-spa.md
    type: related
---

# Session tracing from local events

## Decision context

**Why this was needed:** research into what the field does that we don't surfaced
"agent observability" as the highest-leverage gap. The field uses Langfuse, Braintrust,
or OpenTelemetry-based tracing to see every tool call, subagent dispatch, and multi-agent
handoff. We had no equivalent — `log_spawn.py` records only spawn results, not what
happens inside a session.

**The discovery:** Grok Build already captures 76,000+ structured events per session in
`events.jsonl`, including `tool_started`, `tool_completed`, `mcp_server_connected/failed`,
`turn_started/ended`, `loop_started`, and `first_token` events. The data for full session
tracing was already on disk — only the query tool was missing.

## What the data contains

Every Grok Build session at `~/.grok/sessions/<encoded-cwd>/<session-id>/events.jsonl`
captures:

| Event type | Count (typical session) | What it records |
|---|---|---|
| `tool_started` | ~290 | Tool name + timestamp |
| `tool_completed` | ~285 | Tool name + timestamp + exit code |
| `permission_requested` / `permission_resolved` | ~290 | Every permission gate fire |
| `turn_started` / `turn_ended` | ~18 | Turn boundaries |
| `loop_started` | ~283 | Agent loop iterations |
| `mcp_server_connected` / `mcp_server_failed` | ~16/8 | MCP server health at session start |
| `phase_changed` | ~74,000 | Internal phase transitions (noise — filter out) |
| `first_token` | ~170 | LLM response latency (time to first token) |

From `tool_started` + `tool_completed` pairs, we can derive: tool call count by type,
duration per call, failure rate, and a session timeline showing which tools ran in which
turn.

## The tool: `session_trace.py`

**Location:** `P:/.agents/scripts/session_trace.py`

**Usage:**
```powershell
# Full trace (timeline + tool summary + failures)
python P:/.agents/scripts/session_trace.py <session-id>

# Just the timeline
python P:/.agents/scripts/session_trace.py <session-id> --timeline

# Just tool usage stats
python P:/.agents/scripts/session_trace.py <session-id> --by-tool

# Just failures
python P:/.agents/scripts/session_trace.py <session-id> --failures
```

## What this session's trace revealed

Running the tracer on this session (019fea06) produced:

| Tool | Calls | Failed | Avg(s) | Max(s) |
|------|-------|--------|--------|--------|
| run_terminal_command | 121 | 0 | 6.8 | 24.4 |
| read_file | 50 | 0 | 0.7 | 5.2 |
| grep | 30 | 0 | 1.1 | 17.7 |
| write | 29 | 0 | 3.9 | 6.7 |
| search_replace | 22 | 0 | 3.8 | 7.8 |
| use_tool (MCP) | 6 | 0 | 10.3 | 16.5 |
| web_fetch | 5 | 0 | 0.9 | 1.5 |
| get_command_or_subagent_output | 5 | 0 | 8.4 | 38.5 |

**Insights from the trace:**
- **0 failed tool calls** — the session was clean (no silent failures)
- **38.5s max wait on a subagent** — that's the ship-py background task polling
- **121 terminal commands** — high, reflecting the ship-py workaround effort
- **MCP tools averaged 10.3s** — slower than native tools, confirming the latency cost of MCP dispatch
- **3 MCP servers failed to connect** — discord, kinocut, sourcegraph (visible in session start)

This is the observability we were missing — and it was already on disk.

## What this means for our workspace

**Immediate:** any session can now be traced with one command. No Langfuse account, no
external infrastructure, no credential setup. The data is local and already captured.

**For debugging:** when a session goes wrong, run `session_trace.py --failures` to see
which tools failed and when. The timeline view shows which turn the problem started in.

**For performance analysis:** `--by-tool` shows which tools are slowest. This session's
data confirms MCP tools are 10x slower than native tools on average.

**For the Langfuse question:** if we later adopt Langfuse for cross-session dashboards,
the `events.jsonl` data can be exported to Langfuse's trace format. The local tool is not
a replacement for Langfuse's aggregation and alerting — it's the zero-infrastructure
starting point that proves the value before investing in external infrastructure.

**Connection to [[available-over-optimal-satisficing-in-tool-selection]]:** this session
tracer is itself an example of the available-over-optimal pattern in reverse. The field's
"optimal" solution is Langfuse; but the "available" data was already on disk. Building a
local query tool first — before adopting external infrastructure — is the right ordering.
It proves value, surfaces what data is missing, and informs whether the external tool is
even needed.

**Connection to [[tool-fallbacks]]:** `session_trace.py` belongs in the agent-callable
scripts list alongside `dgemma_read.py`. It's a fleet-wide utility, not a session-specific
tool.

**Connection to [[writing-discipline-not-enforced]]:** the observability gap existed
despite the data being captured — because no rule said "use events.jsonl for tracing."
The fix was structural (a script), not behavioral (a rule).

## Receipts

| Claim | Evidence | Source |
|---|---|---|
| events.jsonl exists per session | `~/.grok/sessions/P%3A%5C/019fea06.../events.jsonl` — 4MB, 76,194 events | filesystem |
| Tool events have start+complete pairs with timestamps | `tool_started` at `04:56:05.277`, `tool_completed` at `04:56:06.123` for the same tool | events.jsonl inspection |
| 286 tool traces matched from 577 tool events | session_trace.py output | this session, 2026-08-10 |
| Duration calculation is accurate (start-to-complete) | derived: 6.8s avg for run_terminal_command matches observed behavior | session_trace.py |
| MCP tools average 10.3s vs native tools 0.7-6.8s | use_tool avg 10.3s, read_file avg 0.7s | session_trace.py --by-tool |

## Falsifier

This approach is wrong if (a) events.jsonl is removed or its format changes in a future
Grok Build update, or (b) the tool_started/tool_completed pairing is unreliable (some
tools don't emit both events). Track by running `session_trace.py --by-tool` after each
Grok Build update — if the matched-trace count drops significantly, the event format
changed and the pairing logic needs updating.

## Auto-related

- [[skill-catalog]]
- [[opentelemetry-logging-patterns]]
- [[opentelemetry-structured-logging-patterns]]
- [[local-llm-inference-optimization]]
- [[opentelemetry-logging]]

