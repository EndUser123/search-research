<img src="https://r2cdn.perplexity.ai/pplx-full-logo-primary-dark%402x.png" style="height:64px;margin-right:32px"/>

# In Claude Code, is there a repo that allows me to record all message turns, tool use calls, internal dialogue to a JSON-L file for every terminal session?

Yes. **Claude Code already records every message turn, tool‑use call, and internal thinking into JSONL files on disk by default**; there is no separate “plugin” you must install in the agent to enable this.[^1_1][^1_2][^1_3][^1_4]

### What Claude Code already logs

- Every terminal session is stored as a JSONL file under `~/.claude/projects/...` (project‑path encoded as directory name), with one JSON object per line.[^1_2][^1_3][^1_4]
- Each line captures:
    - Role (`user` / `assistant` / `system` / tool‑related roles),
    - Message content and structure,
    - Tool calls and results (e.g., `bash`, `read`, `edit`, `write`, etc.),
    - Token‑usage and timestamps,
    - Internal thinking blocks (across “thinking” tokens / blocks).[^1_5][^1_6][^1_1][^1_2]

So **you already have a per‑session JSONL log for every terminal session**; the “repo” is effectively the local `~/.claude/projects/` tree plus the global `~/.claude/history.jsonl` index.[^1_3][^1_4][^1_2]

### Existing repos that replay / inspect those JSONL logs

If you want a **dedicated repo that post‑processes** these logs (e.g., for replay, analysis, or export), useful projects include:

- [`daaain/claude-code-log`](https://github.com/daaain/claude-code-log):
    - Converts Claude Code transcript JSONL files into HTML (with filtering by message type, tool use, thinking blocks, etc.).[^1_7][^1_4]
    - Can process all projects under `~/.claude/projects/` and generates per‑session and per‑project HTML pages, but it **reads** the existing JSONL; it doesn’t change how Claude Code writes them.[^1_7]
- Various community tools (e.g., HTML replayers, CLI tools for “history” or “conversation search”) that consume the same JSONL files under `~/.claude/projects/` or `~/.claude/history.jsonl`.[^1_8][^1_1][^1_2][^1_3]


### How to exploit this for your use case

If you want every terminal session to **also** be written to a custom JSONL sink (e.g., a separate repo‑side log, or a hook‑based pipeline), you can:

- Treat `~/.claude/projects/.../*.jsonl` as your canonical source of truth.[^1_4][^1_2][^1_3]
- Use Claude Code’s **hooks** (e.g., `SessionStart`, `SessionClose`, custom command hooks) to:
    - Copy or stream the JSONL into another repo‑local JSONL under version control, or
    - Append a minimal, transformed event stream (e.g., anonymized tool‑use events) into your own structured log.[^1_9]

***

Given your architecture background: **do you want this recording to be “write‑through” (i.e., your own hooks mirror the built‑in JSONL into a repo‑local JSONL file) or “read‑only” (post‑process the existing `~/.claude/projects/` JSONL after‑the‑fact)?**

If you confirm which pattern you prefer, I can sketch:

- a concrete hook + `jq` / Python script that tails and copies enriched events into a repo‑local JSONL, or
- a background daemon that watches `~/.claude/projects/` and mirrors sessions into your git‑tracked log.
<span style="display:none">[^1_10][^1_11][^1_12][^1_13][^1_14][^1_15]</span>

<div align="center">⁂</div>

[^1_1]: https://news.ycombinator.com/item?id=47276604

[^1_2]: https://alexop.dev/posts/building-conversation-search-skill-claude-code/

[^1_3]: https://kentgigger.com/posts/claude-code-conversation-history

[^1_4]: https://simonwillison.net/2025/Oct/22/claude-code-logs/

[^1_5]: https://github.com/anthropics/claude-code/issues/31143

[^1_6]: https://introl.com/blog/claude-code-cli-comprehensive-guide-2025

[^1_7]: https://github.com/daaain/claude-code-log

[^1_8]: https://dev.to/kuroko1t/i-built-a-tool-to-stop-losing-my-claude-code-conversation-history-5500

[^1_9]: https://www.linkedin.com/posts/christopher-k-lee-marks-3693512b_running-multiple-claude-code-sessions-at-activity-7425056870039494656-6ArE

[^1_10]: https://github.com/anthropics/claude-code/issues/24148

[^1_11]: https://www.reddit.com/r/ClaudeAI/comments/1rmk93n/i_built_a_tool_to_turn_claude_code_sessions_into/

[^1_12]: https://platform.claude.com/docs/en/agents-and-tools/tool-use/implement-tool-use

[^1_13]: https://blog.sshh.io/p/how-i-use-every-claude-code-feature

[^1_14]: https://www.youtube.com/watch?v=imw8MkwW9xw

[^1_15]: https://www.reddit.com/r/ClaudeAI/comments/1lix9q0/using_client_tool_calls_in_claude_api_requires/


---

# The hard part is finding the chat history log files.  When I ask Claude to find a previous conversation, it takes a bit of time in searching.  Any idea on how to address that pain point?

The slowness you see is Claude’s **in‑UI “search past conversations” feature** traversing a large, unindexed pile of JSONL over the network; it doesn’t use a local inverted index, so it scales poorly with history size.[^2_1][^2_2][^2_3][^2_4]

Here are the main ways to de‑couple *finding* history from Claude’s UI search and make it effectively instant:

***

### 1. Use a local index (MCP‑based skill)

There are several MCP servers / skills that:

- Index all `~/.claude/projects/**/*.jsonl` into a fast local search engine (e.g., SQLite, DuckDB, or a vector‑based index).[^2_4][^2_5][^2_6]
- Let you ask things like
`“where did we fix auth?”` or
`“search sessions for ‘refactor webpack’ in this project”`
and they return a short list of session IDs and project paths in <100–300 ms.[^2_5][^2_4]

Examples you can drop into your workflow:

- [`ticpu/claude-conversation-search-mcp`](https://github.com/ticpu/claude-conversation-search-mcp):
    - Scans `~/.claude/projects/`, skips full‑file dumps, and keeps reasoning/tool‑use messages in a searchable index.[^2_4]
- [`akatz‑ai/cc‑conversation‑search`](https://github.com/akatz-ai/cc-conversation-search):
    - Hybrid extraction + JIT indexing; returns session IDs + project paths so you can jump directly into the right session.[^2_6]

You can then bind a slash command (e.g., `/search-history`) that routes queries to this MCP, and keep Claude’s built‑in search off or disabled.

***

### 2. Use a thin CLI + `ripgrep` / `pt` / `grep`

If you want something minimal and infra‑light:

- `cd ~/.claude/projects && rg "auth refactor"` (or `grep`, `ag`, `pt`) over all JSONL files.[^2_7][^2_8]
- Wrap it in a small skill or script that:
    - Accepts a query string,
    - Gathers matches with filename, timestamp, and snippet,
    - Returns a compact list for Claude to render.[^2_9][^2_7]

This often beats the in‑UI search on latency because it runs on your own machine and doesn’t need to re‑transfer gigabytes of history each time.[^2_8][^2_4]

***

### 3. Reduce what you’re asking Claude to search

- Turn off “search past chats” for everything except current project, so Claude only scans one `~/.claude/projects/...` directory at a time.[^2_1][^2_9]
- Favor project‑scoped prompts like
`“in this project, search for sessions where we discussed X”`
instead of global “search all history” queries.[^2_9][^2_1]

***

### 4. Keep a separate repo‑side log index (hook‑based)

If you already have a repo‑local JSONL log per session (as in your earlier question), you can:

- Add a hook that, on `SessionClose`, writes a short metadata row (topic tags, project path, session ID, timestamp) into a repo‑local SQLite / DuckDB table.[^2_5][^2_6][^2_4]
- Then expose a slash command (or MCP) that queries that table first, falling back to full JSONL scan only when needed.

This is the “write‑through index” pattern you alluded to and typically lets you answer “which sessions contain X?” in tens of milliseconds.[^2_4][^2_5]

***

### Concrete next‑step suggestion

Given your stack, a low‑friction path is:

1. Install an MCP‑backed search such as `ticpu/claude‑conversation‑search‑mcp` and wire it into your Claude Code CLI.[^2_4]
2. Disable or strongly scope Claude’s built‑in “search past chats” so it doesn’t fight your local index.[^2_2][^2_1]

If you tell me whether you prefer **SQLite‑style text‑only** or **vector‑based semantic search**, I can sketch a minimal schema + slash‑command handler tailored to your existing JSONL‑logging setup.
<span style="display:none">[^2_10][^2_11][^2_12][^2_13][^2_14][^2_15]</span>

<div align="center">⁂</div>

[^2_1]: https://support.claude.com/en/articles/11817273-use-claude-s-chat-search-and-memory-to-build-on-previous-context

[^2_2]: https://github.com/anthropics/claude-code/issues/16528

[^2_3]: https://alexop.dev/posts/building-conversation-search-skill-claude-code/

[^2_4]: https://github.com/ticpu/claude-conversation-search-mcp

[^2_5]: https://news.ycombinator.com/item?id=47128630

[^2_6]: https://github.com/akatz-ai/cc-conversation-search

[^2_7]: https://kentgigger.com/posts/claude-code-conversation-history

[^2_8]: https://www.reddit.com/r/ClaudeCode/comments/1pa0s0h/is_there_a_way_to_have_claude_code_search_the/

[^2_9]: https://www.codeagentswarm.com/en/guides/claude-code-history

[^2_10]: https://www.reddit.com/r/ClaudeAI/comments/1pzsu17/what_do_you_do_when_your_claude_chat_history_gets/

[^2_11]: https://github.com/anthropics/claude-code/issues/10881

[^2_12]: https://thirdbear.substack.com/p/searching-and-browsing-claude-conversations

[^2_13]: https://dev.to/kuroko1t/i-built-a-tool-to-stop-losing-my-claude-code-conversation-history-5500

[^2_14]: https://www.facebook.com/groups/vibecodinglife/posts/1947490542506140/

[^2_15]: https://towardsai.net/p/machine-learning/time-travel-debugging-with-claude-codes-conversation-history


---

# What is currently the most feature-rich, popular, fastest, best Claude chat search repo?

Right now, the **most feature‑rich, popular, and fastest Claude chat search solution is `claude-history` (Rust CLI)**, with strong runners‑up being MCP‑based indexers like `cc‑conversation‑search` and `claude‑code‑conversation‑search‑mcp`.[^3_1][^3_2][^3_3][^3_4][^3_5]

### 1. `claude-history` (Rust CLI) – best overall

- **What it is**: A terminal‑native TUI that scans `~/.claude/projects/` and exposes fuzzy search, session‑resume, and inline content preview.[^3_4][^3_5]
- **Why it’s strong**:
    - Very fast text search (Rust, lightweight, runs locally).[^3_4]
    - Understands Claude’s JSONL structure: supports multi‑word AND queries, UUID lookup, and tool‑result text (e.g., `bash` output, `grep`, file contents).[^3_5]
    - Popular enough that it’s explicitly called out in recent “best tools for Claude Code history” comparisons.[^3_4]

Use case: when you want **blazing‑fast, terminal‑first search** across all projects without extra MCP overhead.[^3_5][^3_4]

***

### 2. MCP‑based indexers – richer, more “agent‑friendly”

These are better if you want rich tooling around context, tagging, and multi‑project search:

- [`akatz‑ai/cc‑conversation‑search`](https://github.com/akatz-ai/cc-conversation-search):
    - Hybrid extraction + JIT indexing; exposes session IDs / project paths so you can jump directly into Claude Code.[^3_3][^3_1]
    - Good for “find that session where we discussed X” type queries and integrating with other skills.
- `TonySimonovsky/claude‑code‑conversation‑search‑mcp` (MCP server):
    - MCP‑wrapped search skill that integrates cleanly with Claude Code; good for building slash‑command style UX.[^3_6][^3_2]

These are often slower than a raw `ripgrep` or `claude‑history`, but far more structured and composable inside your agent graph.[^3_2][^3_3][^3_4]

***

### 3. Other notable options

- **`Mantra` / `CCHV` / `Claude Code History Viewer`**:
    - Offer deeper analytics, code‑diff views, and GUIs, but are more focused on replay and introspection than pure speed‑of‑search.[^3_7][^3_4]
- **`traul`‑style aggregators**:
    - Index Claude Code sessions alongside other comms (Slack, Telegram, etc.) into SQLite + Ollama‑backed vector search; great if you want “search everything” but heavier infra.[^3_8]

***

### Recommendation for your workflow

Given your setup (multi‑terminal, repo‑indexed JSONL logging, performance‑sensitive), a solid combo is:

- Use **`claude‑history` as your primary search UI** for speed and ergonomics.[^3_5][^3_4]
- Optionally wire in **`cc‑conversation‑search` or a similar MCP** as a secondary, structured “agent‑facing” history layer (for slash‑command‑style search and heavy‑weight queries).[^3_1][^3_2]

If you say whether you prefer **Rust CLI** (`claude‑history`) vs **MCP‑only** (e.g., `cc‑conversation‑search`), I can draft a concrete config + aliases tailored to your hook‑based architecture.
<span style="display:none">[^3_10][^3_11][^3_12][^3_13][^3_14][^3_15][^3_9]</span>

<div align="center">⁂</div>

[^3_1]: https://github.com/akatz-ai/cc-conversation-search

[^3_2]: https://mcpmarket.com/tools/skills/claude-history-search

[^3_3]: https://mcpmarket.com/server/claude-code-conversation-search

[^3_4]: https://dev.to/gonewx/i-tested-4-tools-for-browsing-claude-code-session-history-17ie

[^3_5]: https://docs.rs/crate/claude-history/latest

[^3_6]: https://github.com/TonySimonovsky/claude-code-conversation-search-mcp

[^3_7]: https://www.producthunt.com/products/claude-code-history-viewer

[^3_8]: https://www.reddit.com/r/ClaudeCode/comments/1rvort4/i_gave_my_claude_code_agent_a_search_engine/

[^3_9]: https://www.instagram.com/p/DU36DMyEnzR/

[^3_10]: https://thirdbear.substack.com/p/searching-and-browsing-claude-conversations

[^3_11]: https://www.paigeniedringhaus.com/blog/getting-the-most-out-of-claude-code/

[^3_12]: https://intuitionlabs.ai/articles/mcp-servers-claude-code-internet-search

[^3_13]: https://www.linkedin.com/posts/charlywargnier_just-stumbled-upon-the-absolute-best-repo-activity-7434656834516434948-w3kn

[^3_14]: https://mcpmarket.com/tools/skills/claude-conversation-search-resume

[^3_15]: https://www.youtube.com/watch?v=SUysp3sJHbA


---

# I'm willing to use rust + whatever else is needed to fill in any gaps

For you, the **sweet spot is Rust + a small layer of SQLite / vector search + hooks** to fill the remaining gaps. Here’s the current “best‑in‑class” stack you can assemble:

***

### 1. Core: `claude-history` (Rust TUI)

- What it does:
    - Searches `~/.claude/projects/**/*.jsonl` with a TUI; lets you jump directly into any session via `claude --resume <uuid>`.[^4_1][^4_2][^4_3]
- Why it fits you:
    - Zero‑runtime, single‑binary, fast keyword‑style search.[^4_2][^4_3]
    - You can trivially wrap it inside your own hooks or shell functions.[^4_3]

Install:

```bash
cargo install claude-history
```


***

### 2. Gap‑filler: `claude-vault` (Rust + SQLite FTS5)

If you want **durable, searchable history that survives compaction / deletion**:

- `claude-vault` pulls JSONL into a SQLite DB with FTS5 full‑text search, noise‑filtering (tool results, system tags), and UUID dedup.[^4_4]
- It supports hooks like `PreCompact` and `SessionEnd` so archived sessions are always queryable even if the original JSONL is gone.[^4_4]

Use it when you need:

- Long‑term, cross‑machine history with consistent IDs.[^4_5][^4_4]
- A single source of truth for “all sessions ever” instead of relying on file‑system paths.[^4_4]

***

### 3. “Agent‑facing” search: `cc‑conversation‑search` (MCP) or `claude‑conversation‑search‑mcp`

If you want to expose search **to Claude Code itself** (slash‑command style):

- [`akatz‑ai/cc‑conversation‑search`](https://github.com/akatz-ai/cc-conversation-search):
    - Hybrid extraction + JIT indexing; returns session IDs and project paths so you can resume.[^4_6][^4_7]
- [`ticpu/claude‑conversation‑search‑mcp`](https://github.com/ticpu/claude-conversation-search-mcp):
    - Single Rust binary that works both as CLI and as an MCP server.[^4_8][^4_6]

You can wire:

- `claude-history` for **you** (terminal UX)
- an MCP like `cc‑conversation‑search` or `ticpu/...` for **Claude** (slash‑command driven search).[^4_7][^4_6]

***

### 4. Optional: `claude‑run` / `claude‑code‑sync` for ergonomics

- `claude‑run` (Node‑based) lets you browse sessions per‑project in a browser UI; good if you ever want a visual index.[^4_9]
- `claude‑code‑sync` (Rust) syncs your history across machines via Git; useful if you work on multiple laptops.[^4_5]

***

### Recommended architecture for you

Given your taste for Rust + hooks:

1. **Primary UX**:
    - Install `claude-history`; bind it to an alias like `ch` or `claude-search`.[^4_1][^4_3]
2. **Durable index**:
    - Add `claude-vault` as a background service that listens to Claude Code hooks and keeps an SQLite FTS5 index of everything.[^4_4]
3. **Agent‑facing search**:
    - Add `cc‑conversation‑search` or `ticpu/claude‑conversation‑search‑mcp` as an MCP server so Claude can answer `/search-history ...` using the same index.[^4_6][^4_7]
4. **Optional**:
    - Use `claude‑code‑sync` if you want history mirrored into a repo‑local Git‑tracked structure for backup + `git grep` / `rg` as a fallback.[^4_5]

***

If you tell me whether you want:

- **pure‑Rust, no‑MCP** (just CLI + SQLite), or
- **Rust + MCP** (hooks + skills + slash‑commands),

I can draft a concrete `ClaudeCode.toml` snippet + a tiny Rust hook that wires `claude-vault` + `claude-history` into your repo‑local JSONL log.
<span style="display:none">[^4_10][^4_11][^4_12][^4_13][^4_14][^4_15][^4_16]</span>

<div align="center">⁂</div>

[^4_1]: https://crates.io/crates/claude-history

[^4_2]: https://news.ycombinator.com/item?id=47104602

[^4_3]: https://docs.rs/crate/claude-history/latest

[^4_4]: https://lib.rs/crates/claude-vault

[^4_5]: https://github.com/perfectra1n/claude-code-sync

[^4_6]: https://github.com/ticpu/claude-conversation-search-mcp

[^4_7]: https://github.com/akatz-ai/cc-conversation-search

[^4_8]: https://news.ycombinator.com/item?id=47128630

[^4_9]: https://www.reddit.com/r/ClaudeAI/comments/1q0zm9d/i_built_a_tool_to_browse_claude_code_history_by/

[^4_10]: https://www.reddit.com/r/ClaudeAI/comments/1rvd4wx/made_a_cli_tool_for_exploring_rust_crate_apis/

[^4_11]: https://www.reddit.com/r/ClaudeAI/comments/1mp09yp/search_chat_functionality_awesome_but_with/

[^4_12]: https://www.reddit.com/r/rust/comments/1papifb/anyone_here_using_claude_code_ai_assistants_for/

[^4_13]: https://www.jetbrains.com/help/ai-assistant/ai-chat.html

[^4_14]: https://support.claude.com/en/articles/11817273-use-claude-s-chat-search-and-memory-to-build-on-previous-context

[^4_15]: https://community.openai.com/t/best-practices-for-cost-efficient-high-quality-context-management-in-long-ai-chats/1373996

[^4_16]: https://github.com/TonySimonovsky/claude-code-conversation-search-mcp


---

# Integrate Rust history search as Claude Code skill

You can integrate a Rust history search tool as a Claude Code **skill** by wrapping its CLI in a small skill directory that Claude can invoke via `/search-history`.[^5_1][^5_2]

Below is a minimal, concrete pattern you can adapt to `claude-history`, `claude-vault`, or any Rust binary that searches your JSONL/SQLite index.

***

## 1. High‑level pattern

- Use a **Claude Code skill** as the UX + orchestration layer.[^5_3][^5_2]
- Inside the skill folder, provide:
    - `SKILL.md` with frontmatter + instructions.[^5_2]
    - A small script (Rust, bash, or Python) that shells out to your Rust search binary and prints JSON for Claude.[^5_2]

Claude will then:

- Call the script when you run `/search-history ...`.[^5_2]
- Parse the JSON output and show a list of sessions/snippets you can click or copy.[^5_1]

***

## 2. Skill directory layout

Create a directory (personal skill):

```bash
mkdir -p ~/.claude/skills/rust-history-search
cd ~/.claude/skills/rust-history-search
```

Files:

- `SKILL.md` – definition + instructions for Claude.[^5_2]
- `search-history.sh` (or a tiny Rust wrapper binary you build) – runs your Rust search tool.

Example `SKILL.md`:

```markdown
---
name: search-history
description: Fast local search over Claude Code history using a Rust indexer.
user-invocable: true
disable-model-invocation: false
allowed-tools:
  - Bash
---

## Usage

When the user runs `/search-history <query>`, call the bundled script:

1. Run the script with the query as argument:

   ```bash
   bash search-history.sh "<query>"
```

2. The script prints newline-delimited JSON objects with at least:
    - `project`: string (project path or name)
    - `session_id`: string (UUID or filename)
    - `score`: number (relevance score, higher is better)
    - `snippet`: string (short excerpt with the match)
    - `timestamp`: string (ISO timestamp if available)
3. Parse the JSON lines and present a concise list, for example:
    - One bullet per result: project, timestamp, snippet.
    - Include the `session_id` in backticks so the user can copy it to resume.
    - Prefer the top 10–20 results unless the user asks for more.

If the query is empty, ask the user what to search for instead of running the tool.
If the tool fails or returns no results, say so and suggest narrowing or changing the query.

```

This follows the docs pattern for skills with a script helper.[^5_4][^5_2]

***

## 3. Wrapper script that calls your Rust binary

Assume you have a Rust binary `claude-history-search` that supports:

```bash
claude-history-search --query "auth refactor" --format jsonl
```

You can keep the wrapper almost trivial:

```bash
#!/usr/bin/env bash
set -euo pipefail

QUERY="${1-}"

if [ -z "$QUERY" ]; then
  echo '{"error":"missing query"}'
  exit 1
fi

# Example: call your Rust tool. It should output JSONL with fields that match SKILL.md.
claude-history-search --query "$QUERY" --format jsonl
```

Make it executable:

```bash
chmod +x search-history.sh
```

You can implement `claude-history-search` by:

- Building a small Rust binary that:
    - Scans `~/.claude/projects/**/*.jsonl` or your SQLite/FTS index.[^5_5][^5_6]
    - Emits JSONL with the fields described above.

If you prefer, you can skip bash and put the wrapped logic directly in a Rust CLI that reads `argv[^5_1]` and writes JSONL to stdout; the skill still calls it via `Bash`.[^5_2]

***

## 4. Wiring an MCP‑based Rust search server (optional)

If you want deeper capabilities (semantic search, paging, filters):

- Use an MCP server like `claude-conversation-search-mcp` or `claude-historian-mcp` that already exposes tools such as `search_sessions` and `get_session`.[^5_7][^5_8][^5_1]
- Configure Claude Code to connect to that MCP server, then write a skill that **calls the MCP tools** instead of a local script.[^5_3][^5_4]

The high‑level change in `SKILL.md` is:

- Replace the Bash call with a call to the MCP toolset (using the Skill tool syntax documented in the skills docs).[^5_9][^5_2]

This gives you:

- Same `/search-history` UX.
- Under the hood, Rust MCP server doing TF‑IDF or SQLite FTS search over all history.[^5_8][^5_10][^5_7]

***

## 5. Next small step

Given your comfort with Rust:

- Start with the **simple skill + bash wrapper + Rust CLI** pattern above (no MCP), targeting your existing JSONL or `claude-vault` SQLite index.[^5_6][^5_5][^5_2]
- Once that’s working, you can refactor the Rust CLI into an MCP server to unlock richer multi‑tool workflows, but your SKILL UX (`/search-history`) stays the same.[^5_7][^5_8][^5_3]

If you paste your current Rust search CLI’s interface (flags + output format), a tailored `search-history` wrapper and a more precise `SKILL.md` can be sketched to match it exactly.
<span style="display:none">[^5_11][^5_12][^5_13][^5_14]</span>

<div align="center">⁂</div>

[^5_1]: https://mcpmarket.com/tools/skills/claude-history-search

[^5_2]: https://code.claude.com/docs/en/skills

[^5_3]: https://www.whytryai.com/p/claude-code-ide-skills-mcp

[^5_4]: https://brightdata.com/blog/ai/claude-skills-with-web-mcp

[^5_5]: https://docs.rs/crate/claude-history/latest

[^5_6]: https://lib.rs/crates/claude-vault

[^5_7]: https://github.com/Vvkmnn/claude-historian-mcp

[^5_8]: https://github.com/ticpu/claude-conversation-search-mcp

[^5_9]: https://platform.claude.com/docs/en/agents-and-tools/tool-use/tool-search-tool

[^5_10]: https://news.ycombinator.com/item?id=47128630

[^5_11]: https://www.reddit.com/r/ClaudeCode/comments/1q6j6e0/claude_skills_vs_claude_mcp/

[^5_12]: https://www.youtube.com/watch?v=vuuhOM9731w

[^5_13]: https://www.reddit.com/r/ClaudeAI/comments/1rjxdvk/i_used_claude_to_build_an_mcp_server_that_lets_it/

[^5_14]: https://www.youtube.com/watch?v=wQ0duoTeAAU


---

# How to build custom Rust MCP server for Claude history

A custom Rust MCP server for Claude history is just a stdio JSON‑RPC server that exposes a few tools over your local JSONL / SQLite index and speaks the Model Context Protocol.[^6_1][^6_2][^6_3]

Below is a minimal but realistic blueprint tailored to Claude Code history.

***

## 1. Overall design

- Transport: **stdio** (Claude Code connects via MCP over stdin/stdout).[^6_2][^6_3][^6_1]
- Protocol: use the `model_context_protocol` Rust crate (or similar) so you don’t hand‑roll JSON‑RPC.[^6_4][^6_3]
- Storage:
    - Start simple: walk `~/.claude/projects/**/*.jsonl` on demand.
    - Upgrade: preload / maintain a **SQLite FTS5** index for fast search.[^6_5][^6_2]
- Tools to expose:
    - `list_projects` – enumerate projects with history.[^6_6]
    - `search_sessions` – keyword (and later semantic) search over messages.[^6_6]
    - `get_session` – fetch messages/snippets for a specific session.[^6_6]

These three tools basically reproduce what existing history MCP servers do, but in your own Rust implementation.[^6_7][^6_6]

***

## 2. Rust project setup

`Cargo.toml` (trimmed to essentials):

```toml
[package]
name = "claude-history-mcp"
version = "0.1.0"
edition = "2021"

[dependencies]
tokio = { version = "1", features = ["full", "io-std"] }
serde = { version = "1", features = ["derive"] }
serde_json = "1"
anyhow = "1"
thiserror = "1"
tracing = "0.1"
tracing-subscriber = { version = "0.3", features = ["env-filter"] }

# MCP implementation
model_context_protocol = { version = "0.1", features = ["stdio-server"] } # adjust to latest [web:67]

# Optional but recommended: SQLite FTS index
rusqlite = { version = "0.31", features = ["bundled"] }
```

This mirrors standard Rust MCP server patterns.[^6_8][^6_2][^6_4]

***

## 3. Defining tools

Use the `model_context_protocol` macros / types to define tools.[^6_3]

Conceptual types:

```rust
use serde::{Deserialize, Serialize};

#[derive(Serialize, Deserialize)]
pub struct ListProjectsArgs {}

#[derive(Serialize, Deserialize)]
pub struct ProjectInfo {
    pub project: String,
    pub session_count: u32,
    pub last_activity: Option<String>,
}

#[derive(Serialize, Deserialize)]
pub struct SearchSessionsArgs {
    pub query: String,
    pub project: Option<String>,
    pub limit: Option<u32>,
}

#[derive(Serialize, Deserialize)]
pub struct SessionSummary {
    pub project: String,
    pub session_id: String,
    pub score: f32,
    pub snippet: String,
    pub timestamp: Option<String>,
}

#[derive(Serialize, Deserialize)]
pub struct GetSessionArgs {
    pub project: String,
    pub session_id: String,
    pub max_messages: Option<u32>,
}
```

Tool handlers (conceptual):

```rust
use model_context_protocol::prelude::*; // pseudo-import, see crate docs [web:67]

#[mcp_tool(name = "list_projects", desc = "List Claude Code projects with history")]
async fn list_projects_tool(_args: ListProjectsArgs) -> McpResult<Vec<ProjectInfo>> {
    // Walk ~/.claude/projects, count *.jsonl, track last modified time.
    // Return Vec<ProjectInfo>.
}

#[mcp_tool(name = "search_sessions", desc = "Search sessions in Claude Code history")]
async fn search_sessions_tool(args: SearchSessionsArgs) -> McpResult<Vec<SessionSummary>> {
    // If you have SQLite FTS, run SELECT with MATCH.
    // Otherwise, simple scan / ranking over JSONL files.
}

#[mcp_tool(name = "get_session", desc = "Get messages from a single session")]
async fn get_session_tool(args: GetSessionArgs) -> McpResult<serde_json::Value> {
    // Open the specific JSONL file and filter by session_id,
    // or read from SQLite by foreign key.
}
```

The `#[mcp_tool]` macro creates the MCP tool descriptors and routes tool calls to your functions.[^6_4][^6_3]

***

## 4. Server main with stdio transport

Following typical Rust MCP server scaffolding:[^6_1][^6_2][^6_3]

```rust
use model_context_protocol::server::stdio::McpStdioServer;
use model_context_protocol::{McpServerHub, InitializeCapabilities};
use tracing_subscriber::{layer::SubscriberExt, util::SubscriberInitExt};

mod tools; // where you put the functions & types above

#[tokio::main]
async fn main() -> anyhow::Result<()> {
    // log to stderr; stdout reserved for MCP JSON-RPC
    tracing_subscriber::registry()
        .with(tracing_subscriber::EnvFilter::new(
            std::env::var("RUST_LOG").unwrap_or_else(|_| "info".into()),
        ))
        .with(tracing_subscriber::fmt::layer().with_writer(std::io::stderr))
        .init();

    let mut hub = McpServerHub::new("claude-history-mcp", "0.1.0");

    // Register tools
    hub.register_tool(tools::list_projects_tool());
    hub.register_tool(tools::search_sessions_tool());
    hub.register_tool(tools::get_session_tool());

    // Optional: declare capabilities (streaming, resources, prompts, etc.) [web:67][web:60]
    hub.set_capabilities(InitializeCapabilities::default());

    // Run server on stdio
    McpStdioServer::run(hub.to_config()).await?;

    Ok(())
}
```

Claude Code will talk JSON‑RPC over stdin/stdout to this process.[^6_2][^6_1]

***

## 5. History parsing / indexing

### a) Direct JSONL scan (simplest)

- Walk `~/.claude/projects/**/sessions/*.jsonl` (paths depend on your installation).[^6_9][^6_10]
- For each JSONL line, parse the message, extract:
    - project path (from dir),
    - session UUID,
    - timestamp,
    - text content (user + assistant + tool output).

Quick \& dirty search for `search_sessions`:

- Filter sessions whose concatenated text contains all query terms.
- Score by term frequency or last activity time.

This is enough to prove out the MCP plumbing before optimizing.

### b) SQLite FTS index (fast + durable)

Use a schema like:

```sql
CREATE TABLE sessions (
    id TEXT PRIMARY KEY,
    project TEXT NOT NULL,
    started_at TEXT,
    last_activity TEXT
);

CREATE VIRTUAL TABLE session_content USING fts5(
    session_id UNINDEXED,
    content,
    tokenize = "unicode61"
);
```

Index builder (one‑time + incremental):

- For each JSONL file:
    - Upsert into `sessions`.
    - Insert into `session_content` a row per message chunk: `session_id`, `content`.

Then `search_sessions` becomes:

```sql
SELECT s.project, s.id, s.last_activity,
       bm25(session_content) as score,
       snippet(session_content, 0, '[', ']', '...', 64) as snippet
FROM session_content sc
JOIN sessions s ON s.id = sc.session_id
WHERE session_content MATCH :query
ORDER BY score
LIMIT :limit;
```

This mirrors what existing “Claude Code history MCP servers” do under the hood.[^6_7][^6_5][^6_6]

***

## 6. Wiring into Claude Code

Once your Rust binary is built (say it’s `claude-history-mcp`):

1. **Register MCP server** in Claude Code (UI or config):
    - Command: `claude-history-mcp`
    - Transport: `stdio`
    - Name: `claude-history`
2. Exposed tools will show up as:
    - `claude-history:list_projects`
    - `claude-history:search_sessions`
    - `claude-history:get_session`
3. Optionally add a **skill** that wraps them into a nice UX, e.g. a `/history` command that:
    - Calls `list_projects` when no arguments.
    - Calls `search_sessions` with the query otherwise.[^6_11][^6_12][^6_6]

***

## 7. Recommended next step

Given your background, the fastest route:

1. Start from the official “Build an MCP server” Rust example and drop in `model_context_protocol`.[^6_3][^6_1][^6_2]
2. Implement **only** `list_projects` + a naive `search_sessions` that scans JSONL.
3. Once that’s working with Claude Code, add the SQLite FTS5 layer under the same tool signatures so you don’t have to change the Claude‑side wiring.

If you want, you can paste the on‑disk layout of your `~/.claude/projects` tree and preferred index location, and a more concrete `search_sessions` implementation (walk + filter or FTS SQL) can be sketched exactly against that structure.
<span style="display:none">[^6_13][^6_14][^6_15]</span>

<div align="center">⁂</div>

[^6_1]: https://modelcontextprotocol.io/docs/develop/build-server

[^6_2]: https://oneuptime.com/blog/post/2026-01-07-rust-mcp-server/view

[^6_3]: https://docs.rs/model-context-protocol

[^6_4]: https://rup12.net/posts/write-your-mcps-in-rust/

[^6_5]: https://lib.rs/crates/claude-vault

[^6_6]: https://mcpservers.org/zh-TW/servers/yudppp/claude-code-history-mcp

[^6_7]: https://www.reddit.com/r/ClaudeAI/comments/1lzeihw/vvkmnnclaudehistorian_an_mcp_server_for_claude/

[^6_8]: https://dev.to/ejb503/from-println-disasters-to-production-building-mcp-servers-in-rust-imf

[^6_9]: https://kentgigger.com/posts/claude-code-conversation-history

[^6_10]: https://thirdbear.substack.com/p/searching-and-browsing-claude-conversations

[^6_11]: https://code.claude.com/docs/en/skills

[^6_12]: https://mcpmarket.com/tools/skills/claude-history-search

[^6_13]: https://hackmd.io/@Hamze/SytKkZP01l

[^6_14]: https://www.reddit.com/r/rust/comments/1ja1vjg/i_built_a_rust_implementation_of_anthropics_model/

[^6_15]: https://market-mcp.com/mcp/claude-historian

