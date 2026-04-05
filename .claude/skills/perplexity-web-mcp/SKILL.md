---
name: querying-perplexity
description: >-
  Search the web and query AI models via Perplexity AI using perplexity-web-mcp-cli.
  Supports CLI commands (pwm ask, pwm research), MCP tools (pplx_*), and
  Anthropic/OpenAI-compatible API server. Use when the user mentions "perplexity",
  "pplx", "pwm", "web search with AI", "deep research", "search the internet",
  or wants to query premium models like GPT-5.4, Claude, Gemini, Nemotron through
  Perplexity's web interface.
version: 0.9.5
status: beta
category: web
metadata:
  version: "0.9.5"
  author: "Jacob BD"
---

# Perplexity Web MCP

Search the web and query premium AI models through Perplexity AI.

## Quick Reference

Run `pwm --ai` for comprehensive AI-optimized documentation covering all
commands, models, MCP tools, auth flows, and error recovery.

```bash
pwm --ai                # Full AI reference (RECOMMENDED first step)
pwm --help              # CLI help
pwm login --check       # Check auth status
```

## Critical Rules

1. **Authenticate first**: Run `pwm login` before any queries
2. **Tokens last ~30 days**: Re-run `pwm login` on 403 errors
3. **Check quota before your first query every session** (see protocol below)
4. **Default to quick/Sonar** — only escalate when the query genuinely needs Pro
5. **Never use Deep Research autonomously** — only when the user explicitly asks

## Quota-Aware Usage Protocol (MANDATORY)

Perplexity has hard quota limits. Wasting Pro queries on simple lookups exhausts
the weekly pool fast, leaving nothing for questions that actually need it.

### Cost Model

| Tier | Cost | Resets | Pool |
|------|------|--------|------|
| Sonar / quick | **FREE** | -- | Unlimited |
| Pro Search (standard/detailed) | 1 Pro query | Weekly | ~300/week |
| Deep Research | 1 Research query | Monthly | ~5-10/month |

### Before Every Session

1. Check quota: `pplx_usage()` (MCP) or `pwm usage` (CLI)
2. If Pro < 20% remaining, restrict to quick/Sonar except user-requested Pro queries

### Smart Routing (USE BY DEFAULT)

```
MCP:  pplx_smart_query(query, intent="quick")       # FREE for most lookups
MCP:  pplx_smart_query(query, intent="standard")    # 1 Pro when quick isn't enough
CLI:  pwm ask "query"                                # auto routes via smart logic
```

The router automatically protects quota: downgrades when low, falls back to Sonar when exhausted.

For detailed intent selection criteria and decision flowchart, see [references/quota-decision-guide.md](references/quota-decision-guide.md).

### When to Use Explicit Models

Only use model-specific tools (pplx_gpt54, pplx_claude_sonnet, etc.) when:
- The user explicitly requests a specific model
- You're comparing outputs across models
- The smart router's choice isn't working for the specific use case

## Tool Detection

```
has_mcp = check for tools starting with "pplx_"
has_cli = can run "pwm" commands via shell

if has_mcp and has_cli:
    Use MCP for programmatic access (preferred)
elif has_mcp:
    Use pplx_* MCP tools directly
else:
    Use pwm CLI via shell
```

## Workflow Decision Tree

```
User wants to...
|
+-- Search the web / ask a question → pplx_smart_query(query, intent) or pwm ask "query"
+-- Deep research on a topic → pplx_deep_research(query) or pwm research "query"
+-- Use a specific model → pplx_<model>(query) or pwm ask "query" -m <model>
+-- Check remaining quotas → pplx_usage() or pwm usage
+-- Authenticate → pwm login (interactive) or pplx_auth_request_code + pplx_auth_complete
+-- Start MCP server → pwm-mcp
+-- Start API server → pwm api [--port PORT]
```

## CLI Quick Commands

For full CLI reference: See [references/cli-usage.md](references/cli-usage.md)

```bash
pwm ask "query"                           # Smart routing (default)
pwm ask "query" -m gpt54                  # Specific model
pwm ask "query" -m claude_sonnet -t       # Model with thinking
pwm ask "query" -s academic               # Source focus
pwm ask "query" --json                    # JSON output
pwm research "query"                      # Deep research
pwm login --check                         # Check auth
pwm usage                                 # Check quotas
```

## MCP Tools Summary

| Tool | Cost | Purpose |
|------|------|---------|
| `pplx_smart_query` | **Varies by intent** | **DEFAULT** — quota-aware auto routing |
| `pplx_sonar` | **FREE** | Perplexity Sonar (no Pro quota) |
| `pplx_query` | 1 Pro | Explicit model selection with thinking toggle |
| `pplx_ask` | 1 Pro | Quick Q&A (auto model) |
| `pplx_gpt54` / `_thinking` | 1 Pro | OpenAI GPT-5.4 |
| `pplx_claude_sonnet` / `_think` | 1 Pro | Anthropic Claude 4.6 Sonnet |
| `pplx_claude_opus` / `_think` | 1 Pro | Anthropic Claude 4.6 Opus |
| `pplx_gemini_pro_think` | 1 Pro | Google Gemini 3.1 Pro |
| `pplx_nemotron_thinking` | 1 Pro | NVIDIA Nemotron 3 Super |
| `pplx_deep_research` | 1 Research | In-depth reports (scarce monthly quota) |
| `pplx_usage` | FREE | Check remaining quotas |
| `pplx_auth_*` | FREE | Auth status, request code, complete |

All query tools accept `source_focus`: `"none"`, `"web"`, `"academic"`, `"social"`, `"finance"`, `"all"`.

For full MCP tool parameters: See [references/mcp-tools.md](references/mcp-tools.md)

## Models

| CLI Name | Provider | Thinking | Notes |
|----------|----------|----------|-------|
| auto | Perplexity | No | Auto-selects best |
| sonar | Perplexity | No | Latest, FREE via quick intent |
| deep_research | Perplexity | No | Monthly quota |
| gpt54 | OpenAI | Toggle | GPT-5.4 |
| claude_sonnet | Anthropic | Toggle | Claude 4.6 Sonnet |
| claude_opus | Anthropic | Toggle | Claude 4.6 Opus (Max tier) |
| gemini_pro | Google | Always | Gemini 3.1 Pro |
| nemotron | NVIDIA | Always | Nemotron 3 Super 120B |

For full model details: See [references/models.md](references/models.md)

## Source Focus Options

| Option | Description | Example Use Case |
|--------|-------------|------------------|
| `none` | Model training data only | Code review, analysis without web |
| `web` | General web search (default) | News, general questions |
| `academic` | Academic papers, journals | Research, scientific topics |
| `social` | Reddit, Twitter, forums | Opinions, recommendations |
| `finance` | SEC EDGAR filings | Company financials |
| `all` | Web + Academic + Social | Broad coverage |

## Error Recovery

| Error | Cause | Solution |
|-------|-------|----------|
| 403 Forbidden | Token expired | `pwm login` |
| 429 Rate limit | Quota exhausted | Wait, check `pwm usage` |
| "No token found" | Not authenticated | `pwm login` |
| "LIMIT REACHED" | Quota at zero | Wait for reset or upgrade |

## Reference Files

| File | Contents |
|------|----------|
| [quota-decision-guide.md](references/quota-decision-guide.md) | Intent selection criteria, decision flowchart, automatic quota protection |
| [cli-usage.md](references/cli-usage.md) | Full CLI commands, flags, common patterns |
| [mcp-tools.md](references/mcp-tools.md) | Complete MCP tool parameters and signatures |
| [models.md](references/models.md) | Model identifiers, subscription tiers |
| [api-endpoints.md](references/api-endpoints.md) | API server setup, model name mapping, SDK integration |
