---
title: "Anthropic’s tool search tool"
date: "2026-01-13"
mode: "COPILOT"
uuid: "ad0a8401-fccf-4cec-97b3-e9f0ca9939c7"
entry_count: 2
---

## Human

Anthropic’s tool search tool

## Assistant

Anthropic’s **Tool Search Tool** is a new “meta‑tool” that lets Claude dynamically discover and load tools on demand instead of preloading every MCP/tool definition into the context window.[1][2]

## What the Tool Search Tool Is

- It is itself a single tool that searches across your entire catalog of tools (including MCP tools) and returns only a small set of relevant matches for the current request.[2][1]
- Anthropic positions it as a way for Claude to work with “hundreds or thousands of tools” without blowing out context or manual routing logic.[3][4][2]

## How It Works (Conceptually)

- You register all your tools with Anthropic, but mark most of them with `defer_loading: true`, which makes them discoverable but not initially loaded into Claude’s context.[5][1]
- At runtime, Claude only sees:
  - The Tool Search Tool definition.
  - Any “always-on” tools with `defer_loading: false`.[1]
- When Claude needs some capability (“create a GitHub PR”, “send Slack message”), it calls the Tool Search Tool with a query (e.g., “github pull request”), which runs BM25 or regex search over your tool catalog and returns a small list of matching tools whose full schemas are then injected into context.[6][5][1]

## Why It Exists (Scaling Problem)

- Without this, a serious MCP setup (many servers, hundreds of tools) can consume tens of thousands of tokens just in tool schemas before any user content or reasoning, which kills context for actual work.[7][8][1]
- Anthropic reports up to ~85% reduction in token usage on large MCP stacks, plus a big jump in MCP benchmark accuracy when Tool Search is enabled, because Claude can still reach all tools but sees far fewer at once.[9][5][1]

## Capabilities and Limits

- Supports catalogs up to around 10,000 tools, returning only the top 3–5 most relevant tools per search call.[3]
- Currently tied to newer Claude models (e.g., Sonnet 4.5 / Opus 4.5 variants) and exposed via the “advanced tool use” beta flags in the API.[4][2][3]
- Retrieval is BM25- or regex-based; external evaluations on very large catalogs have found retrieval accuracy in the ~50–65% range (correct tool retrieved somewhere in the result set), which is good but not yet perfect for extremely dense, overlapping tool libraries.[10][5][6]

## How You’d Use It as a Dev

- In your tool registration layer (or MCP client), mark most tools with `defer_loading: true` and only keep your core, frequently used tools always loaded.[1][3]
- Enable the “Tool Search Tool” beta and include its tool definition; your agent then:
  - Tries built-in tools first.
  - When they are insufficient, queries Tool Search to discover additional tools.
  - Calls the discovered tools just like any other tool once their definitions are loaded.[8][2][1]

If you want, the next step can be walking through how to wire this into your current Claude Code + MCP setup and how it interacts with your progressive disclosure pattern.

## Human

tell me how to wire it

## Assistant

Here’s the minimal wiring you need, broken down into concrete steps and example configs.

## 1. Add the Tool Search Tool

In your API client (or agent router), add one of Anthropic’s tool-search tools to the `tools` array. For plain API usage it will look like:

```json
{
  "tools": [
    {
      "name": "tool_search_tool_bm25_20251119",
      "description": "Search over deferred tools and return relevant tool references",
      "input_schema": {
        "type": "object",
        "properties": {
          "query": { "type": "string" }
        },
        "required": ["query"]
      }
    }
    // other (non-deferred) tools here
  ]
}
``` 

BM25 is the natural-language search variant; regex is `tool_search_tool_regex_20251119`.[1][2]

## 2. Mark Most Tools `defer_loading: true`

For every tool you want discoverable via search, add `defer_loading: true` to its definition. Example from the docs:[2][1]

```json
{
  "name": "get_weather",
  "description": "Get current weather for a location",
  "input_schema": {
    "type": "object",
    "properties": {
      "location": { "type": "string" },
      "unit": { "type": "string", "enum": ["celsius", "fahrenheit"] }
    },
    "required": ["location"]
  },
  "defer_loading": true
}
```

Any tools without `defer_loading` (or with `defer_loading: false`) remain always-loaded and visible to Claude from the start.[3][2]

## 3. Defer Whole MCP Servers (Claude Code style)

For MCP, wrap servers with an `mcp_toolset` and use `default_config.defer_loading: true`, then override a few hot-path tools as always-on.[4][2]

```json
{
  "type": "mcp_toolset",
  "mcp_server_name": "google-drive",
  "default_config": { "defer_loading": true },
  "configs": {
    "search_files": {
      "defer_loading": false
    }
  }
}
```

In JS/TS (e.g., LangChain’s Anthropic integration) this pattern looks like:[5]

```ts
tools: [
  tools.toolSearchRegex_20251119(),
  tools.mcpToolset_20251120({
    serverName: "example-mcp",
    defaultConfig: { deferLoading: true },
  }),
],
```

## 4. Let Claude Drive Discovery

Once wired:

- Your request includes:
  - All tools (and MCP toolsets) with `defer_loading` flags.
  - Exactly one tool-search tool.[1][2][4]
- At runtime:
  - Claude sees only non-deferred tools + the search tool.
  - When it needs something else, it calls the search tool internally with a query.
  - The API responds with `tool_reference` entries (e.g. `{"type": "tool_reference","tool_name": "get_weather"}`) that the runtime expands into full tool definitions.[6][4][1]

You do not manually call tool search yourself; you just expose it and mark things deferred.

## 5. Custom Search (Optional, Advanced)

If you prefer your own retrieval (e.g., embeddings over your MCP catalog), you can implement a custom search tool that returns `tool_reference` blocks in its `tool_result` content:[1]

```json
{
  "type": "tool_result",
  "tool_use_id": "toolu_your_tool_id",
  "content": [
    { "type": "tool_reference", "tool_name": "get_weather" },
    { "type": "tool_reference", "tool_name": "search_files" }
  ]
}
```

Each `tool_name` must correspond to a tool definition present in the top-level `tools` list with `defer_loading: true`.[6][1]

***

If you share how you’re currently registering MCP servers for Claude Code (CLI-only vs custom gateway / router), a concrete snippet can be tailored to your exact wiring (e.g., your TS/Python layer that fronts Claude).
