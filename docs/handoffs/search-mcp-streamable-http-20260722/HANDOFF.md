---
thread_id: 727c0da9-a4cf-4b8e-8036-873e07d7aef3
parent_handoff_path: none
current_session_id: 019f819a-7619-7cb3-a6a4-480ff1c916ce
current_terminal_id: console
produced_at: 2026-07-22T15:00:00Z
status: open
handoff_type: implementation
accurate_as_of_head: 126891056635ff42155ee68027aeda11fc6cf2d2
assigned_to: unassigned
---

# Handoff: Convert Search MCP to Streamable HTTP

## 1. Objective

Convert the Search MCP server (`~/.grok/search-mcp/server.py`) from stdio (one process per terminal) to Streamable HTTP (one shared daemon) to address observed memory pressure from multiple concurrent terminals each spawning their own MCP process.

## 2. Status

**Not started. Trigger condition met (memory pressure observed).**

Previously deferred pending memory pressure signal. Operator confirmed pressure observed 2026-07-22.

## 3. What exists

| File | Purpose |
|------|---------|
| `~/.grok/search-mcp/server.py` | FastMCP server, 2 tools (query, fuse), stdio transport |
| `~/.grok/search-mcp/backends.py` | Brave, Exa, DDG async adapters |
| `~/.grok/search-mcp/rrf.py` | Reciprocal Rank Fusion |
| `~/.grok/search-mcp/config.toml` | Backend config |
| `~/.grok/config.toml` | Wired as `[mcp_servers.search]` with stdio command |

## 4. What to build

1. Change `server.py` line: `mcp.run()` → `mcp.run(transport="streamable-http", host="127.0.0.1", port=8321)`
2. Change `config.toml`: `[mcp_servers.search]` from `command/args` to `url = "http://127.0.0.1:8321/mcp"`
3. Set up daemon (Task Scheduler at logon or NSSM Windows Service)
4. Test: restart Grok, verify `search__query` and `search__fuse` connect to the daemon
5. Verify shared health tracking across multiple terminals

## 5. Trade-offs (documented in wiki)

| Factor | stdio (current) | Streamable HTTP (target) |
|--------|-----------------|--------------------------|
| Memory (5 terminals) | ~500MB (5 × ~100MB) | ~100MB (1 daemon) |
| Shared health tracking | No | Yes |
| Shared cache | No | Yes (if added) |
| Fault isolation | Perfect (1 crash = 1 terminal) | Shared (daemon crash = all terminals) |
| Startup ordering | No issue (Grok spawns) | Daemon must run before Grok connects |

## 6. References

- `P:/.data/wiki/concepts/mcp-server-sharing-multi-terminal.md` — full stdio vs HTTP analysis
- `P:/.data/wiki/concepts/grok-build-stop-hook-agent-text.md` — chat_history.jsonl workaround for Stop hooks (relevant if we add daemon health monitoring)
