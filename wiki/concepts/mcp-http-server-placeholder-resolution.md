---
title: MCP HTTP Server Placeholder Resolution
description: "${VAR} placeholders don't resolve in HTTP headers, only in env blocks. Keys must be hardcoded directly in headers."
relations:
  - target: wiki/concepts/mcp-http-server-placeholder-resolution
    type: self
category: configuration
tags:
  - mcp
  - serpapi
  - http
  - environment-variables
created: 2026-04-15
source: serpapi-mcp setup investigation (2026-04-14/15)
severity: important
score: 7
ckks_id: pat_019b3721ef4e43f7
---

# MCP HTTP Server Placeholder Resolution

## The Problem

When configuring MCP servers over HTTP, the `${VAR}` placeholder syntax was used in `headers.Authorization` for the API key:

```json
"serpapi-mcp": {
  "type": "http",
  "url": "https://mcp.serpapi.com/mcp",
  "headers": {
    "Authorization": "Bearer ${SERPAPI_API_KEY}"
  }
}
```

This produced a doctor warning: `Missing environment variables: SERPAPI_API_KEY`

## Root Cause

Claude Code's MCP doctor checker only inspects the `env:` block for missing environment variables — it does not check `headers:` for HTTP servers. Placeholder resolution (`${VAR}`) works in `env:{}` but **NOT** in `headers:{}` for HTTP MCP servers.

## The Fix

Hardcode the API key directly in the `headers` object, matching the pattern used by other HTTP MCP servers (zread, web-search-prime, web-reader):

```json
"serpapi-mcp": {
  "type": "http",
  "url": "https://mcp.serpapi.com/mcp",
  "headers": {
    "Authorization": "Bearer ee4c1e88035595cab506ad207f58a0d813f136e55fcb9ef608718c23e1fffa41"
  }
}
```

## Key Files

| File | Purpose |
|------|---------|
| `~/.claude.json` | User-level MCP config (NOT `~/.claude/.mcp.json`) |
| `P:/.env` | Contains `SERPAPI_API_KEY` |
| `P:/__mcp/serpapi-mcp/` | Local serpapi-mcp installation |

## Related Configuration Schema Differences

| Transport | Schema Keys |
|-----------|-------------|
| `stdio` | `type`, `command`, `args`, `env` |
| `http` | `type`, `url`, `headers` |

## Tags

#mcp #configuration # serpapi #http-server
