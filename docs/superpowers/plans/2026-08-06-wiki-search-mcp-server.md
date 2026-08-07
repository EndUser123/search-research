# Plan: Wiki Search MCP Server

Created: 2026-08-06
Session: 019fd8dc
Plan type: soft plan (single MCP server, additive, reversible)
Status: ready

## Goal

Build a minimal stdio MCP server that exposes the wiki FTS5 index as a
`wiki_search` tool the model can call at any time. This replaces the failed
UserPromptSubmit context-injection approach with a pull-based model: the
model queries when it needs to, instead of relying on push-based injection
that Grok Build doesn't support.

## Why this plan exists

The UserPromptSubmit hook approach failed — Grok Build ignores stdout on
passive events (verified 3 times, documented in
`[[userpromptsubmit-hooks-cannot-auto-invoke-skills-grok-build]]`).
The MCP approach works with the platform instead of against it:

- MCP tools are always available to the model (no injection needed)
- The tool description drives usage ("search BEFORE external research")
- Every skill (/www, /tp, /check) can call the same tool
- No dependency on passive-event stdout processing

## Design decisions (resolved)

| Question | Decision | Source |
|---|---|---|
| Backend | FTS5 index (already built — 990 concepts) | wiki_index_builder.py |
| Interface | stdio MCP server, one tool | Grok Build config.toml format |
| MCP SDK | Python `mcp` package v1.26.0 (already installed) | Verified on host |
| Query module | Extract from wiki_context_injector.py into standalone module | DRY — shared by MCP + hook + CLI |
| Gate? | No — tool description drives usage, no enforcement needed | Operator preference, /tp agreement |
| Registration | `~/.grok/config.toml` under `[mcp_servers.wiki_search]` | Grok Build docs §05 |

## Architecture

```
Model calls wiki_search("model routing hook")
    │
    ▼
MCP stdio server (wiki_search_server.py)
    │
    ├── imports wiki_search.py (shared query module)
    │     ├── extract_keywords() — camelCase/underscore normalization
    │     ├── build_fts_query() — quoted phrase queries (FTS5-safe)
    │     └── query_index() — SQLite FTS5, returns title/summary/path
    │
    └── returns structured results to model
         [{title, summary, path, url}]

Other consumers:
    /www Phase 1 → calls wiki_search.py directly (import)
    /tp Step 0.5 → calls wiki_search.py directly (import)
    CLI → python wiki_search.py "model routing"
```

## Files to create

| # | File | Purpose |
|---|------|---------|
| 1 | `~/.grok/hooks/scripts/wiki_search.py` | Shared query module (extracted from wiki_context_injector.py) |
| 2 | `~/.grok/hooks/scripts/wiki_search_server.py` | MCP stdio server wrapping wiki_search.py |
| 3 | `~/.grok/hooks/tests/test_wiki_search.py` | Tests for wiki_search.py query module |
| 4 | Config edit: `~/.grok/config.toml` | Register MCP server |

## Files to modify

None. This is additive.

## Tasks

### Task 1: Extract wiki_search.py as shared query module

Create `~/.grok/hooks/scripts/wiki_search.py` by extracting the query logic
from `wiki_context_injector.py` into a standalone, importable module.

**What it provides:**
- `extract_keywords(prompt: str) -> list[str]` — same logic as injector
- `build_fts_query(keywords: list[str]) -> str` — same FTS5-safe builder
- `query_index(keywords: list[str], max_results: int = 5) -> list[dict]`
  Returns `[{title, summary, path, url}]` where url is the file:/// link
- `search(query: str, max_results: int = 5) -> list[dict]` — convenience
  function that chains extract → build → query
- CLI interface: `python wiki_search.py "model routing"` prints results

**Test:** `test_wiki_search.py`
- `test_search_returns_results()` — "model routing hook" returns concepts
- `test_search_empty_keywords()` — "asdf qwerty" returns empty list
- `test_search_camelcase()` — "PreToolUse modify" returns relevant concepts
- `test_search_returns_clickable_urls()` — results contain file:/// links
- `test_cli_interface()` — subprocess call returns formatted output

**Run:**
```bash
python ~/.grok/hooks/scripts/wiki_search.py "model routing hook"
```

- [x] Task 1 complete

### Task 2: Build MCP stdio server

Create `~/.grok/hooks/scripts/wiki_search_server.py`.

**What it does:**
- Uses `mcp` Python SDK (v1.26.0) to create a stdio server
- Exposes one tool: `wiki_search`
- Tool schema:
  ```json
  {
    "name": "wiki_search",
    "description": "Search the workspace knowledge base of 990+ concepts. Use this BEFORE external research to check if this workspace already documented your topic. Returns title, summary, and clickable path for each match.",
    "inputSchema": {
      "type": "object",
      "properties": {
        "query": {
          "type": "string",
          "description": "Search terms (natural language OK — keywords are extracted automatically)"
        },
        "max_results": {
          "type": "integer",
          "description": "Maximum results to return (default: 5)",
          "default": 5
        }
      },
      "required": ["query"]
    }
  }
  ```
- Handler calls `wiki_search.search(query, max_results)` from Task 1
- Returns results as structured text (title + summary + URL per line)

**Implementation notes:**
- Use `mcp.server.Server` with `@server.call_tool()` and `@server.list_tools()`
- Stdio transport: `mcp.server.stdio.stdio_server`
- No external dependencies beyond `mcp` (already installed) and stdlib
- Fail-open: if index missing, return helpful error message

**Run (test):**
```bash
echo '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}' | python wiki_search_server.py
```

- [x] Task 2 complete

### Task 3: Register MCP server in config.toml

Add to `~/.grok/config.toml`:

```toml
[mcp_servers.wiki_search]
command = "python"
args = ["C:/Users/brsth/.grok/hooks/scripts/wiki_search_server.py"]
enabled = true
startup_timeout_sec = 10
```

**Verify:** after editing config, check `/mcp` in the TUI or verify the
tool appears in the model's tool list.

- [x] Task 3 complete

### Task 4: Integration test

After registering the MCP server:
1. Start a new session
2. Ask a question that should trigger wiki hits: "how does model routing work on this host?"
3. Verify: the model can call `wiki_search` and get results
4. Verify: results include clickable file:/// links
5. Verify: the tool appears in the session tool list

- [x] Task 4 complete (requires restart)

## Acceptance criteria

1. `wiki_search.py` module is importable and callable from any Python script
2. `wiki_search_server.py` starts and responds to MCP tool calls
3. MCP server is registered in config.toml and appears in tool list
4. `wiki_search("model routing")` returns relevant wiki concepts
5. CLI interface works: `python wiki_search.py "query"` prints results
6. Tests pass: `pytest ~/.grok/hooks/tests/test_wiki_search.py`

## Falsifier

The MCP approach is wrong if: after deployment, the model never calls
`wiki_search` (ignores it like it ignored the behavioral "check the wiki"
rule). That would mean the tool description isn't sufficient to drive usage,
and we'd need the PreToolUse gate after all. Monitor for 3-5 sessions.

## Anti-scope

- No PreToolUse gate (tool description drives usage)
- No UserPromptSubmit hook (passive events can't deliver on Grok Build)
- No semantic/embedding search (FTS5 keyword search is sufficient)
- No modification to /www, /tp, or other skills (they can adopt the module later)
