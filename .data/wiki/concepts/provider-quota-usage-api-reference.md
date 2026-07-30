---
title: "Provider quota and usage API reference (updated with opencode-quota)"
created: 2026-07-30
updated: 2026-07-30
source: session-2026-07-29/30 (provider quota API probing + opencode-quota discovery)
tags: [quota, usage, billing, providers, openrouter, glm, minimax, nvidia, opencode, opencode-quota, api-reference]
summary: >
  How to check quota/usage for each fleet provider. Two tools work:
  (1) opencode-quota (@slkiser/opencode-quota) checks most providers
  programmatically — MiniMax, Z.ai, OpenCode Go/Zen, OpenRouter, Copilot,
  Google AGY/Antigravity, xAI. (2) GLM usage-query plugin provides detailed
  token breakdowns. OpenRouter has a direct API. The earlier claim that
  "most providers have no API" was wrong — opencode-quota found them.
agent: grok
host: grok
cognitive_load: 2
verification: empirically-tested
status: updated — supersedes original "provider-quota-usage-api-reference"
superseded_by: (this is the updated version)
sources:
  - "Direct API probing 2026-07-30"
  - "github.com/slkiser/opencode-quota (590 commits, npm package)"
  - "opencode-quota status output 2026-07-30 (live verified)"
relations:
  - target: wiki/concepts/opencode-go-zen-quota-and-pricing.md
    type: related
  - target: wiki/concepts/model-fleet-provider-pools.md
    type: related
  - target: capabilities/reasoning-model-pool.md
    type: related
---

# Provider quota and usage API reference

## Decision context

The operator needs to check quota across all providers for routing
decisions. Initial probing found only OpenRouter and GLM had working APIs.
The operator pointed out this was wrong — MiniMax, OpenCode, and others
have repos/skills that check quota. Research found `@slkiser/opencode-quota`
(npm), a purpose-built tool that checks quota for all fleet providers.

## The tool: opencode-quota

**npm:** `@slkiser/opencode-quota`
**Repo:** github.com/slkiser/opencode-quota (590 commits, MIT license)
**Install:** `npm install -g @slkiser/opencode-quota`

### What it checks

| Provider | Method | Data source | Verified |
|----------|--------|------------|----------|
| **Z.ai (GLM)** | Remote API via ZAI_API_KEY | 5h tokens + monthly MCP | ✅ 2026-07-30 |
| **MiniMax** | Remote API via MINIMAX_API_KEY | 5h interval + weekly | ✅ 2026-07-30 |
| **OpenCode Go** | Dashboard scraping | Rolling + weekly + monthly | ✅ 2026-07-30 |
| **OpenCode Zen** | Dashboard scraping | Budget + balance | ✅ (needs config) |
| **OpenRouter** | Remote API via key | Credits + usage | ✅ 2026-07-30 |
| **GitHub Copilot** | Remote API via OAuth | Monthly | ✅ 2026-07-30 |
| **OpenAI (Codex)** | Remote API via auth | Weekly quota | ✅ (needs setup) |
| **Google AGY** | Remote API | Quota | ✅ (needs companion) |
| **Google Antigravity** | Remote API | Quota | ✅ (needs companion) |
| **xAI SuperGrok** | Remote API (automatic) | Quota | ✅ |
| **Kimi Code** | Remote API | Quota | ✅ (needs config) |

### Commands

```bash
# Quick quota check (all providers)
opencode-quota show

# JSON output for scripts
opencode-quota show --json

# Diagnostics (shows auth state per provider)
opencode-quota status

# Single provider
opencode-quota show --provider minimax-coding-plan
```

### Companion packages needed

```bash
# Google AGY quota (reads agy's stored auth)
npm install -g @anthonyhaussman/opencode-agy-auth

# Google Antigravity quota
npm install -g opencode-antigravity-auth
```

### Verified live data (2026-07-30 20:18)

From `opencode-quota status`:

| Provider | Quota | Remaining | Reset |
|----------|-------|-----------|-------|
| Z.ai | 5h tokens | 63% | Thu 17:35 |
| Z.ai | Monthly MCP | 96% (195/4000) | Aug 21 |
| MiniMax | 5h interval | 92% | Thu 15:00 |
| MiniMax | Weekly | 100% | Aug 3 |
| OpenCode Go | Rolling 5h | 89% | Thu 17:47 |
| OpenCode Go | Weekly | 89% | Aug 3 |
| OpenCode Go | Monthly | 9% | Aug 6 |
| Copilot | Monthly | 100% | Aug 1 |

## Additional quota tools

### GLM detailed usage (token-level breakdown)

```powershell
node "P:/packages/.claude-marketplace/plugins/glm-plan-usage/skills/usage-query-skill/scripts/query-usage.mjs"
```

Returns: hourly token usage, model call counts, 5h quota percentage,
monthly MCP usage, plan level.

### OpenRouter direct API

```bash
curl -s https://openrouter.ai/api/v1/credits -H "Authorization: Bearer $OPENROUTER_API_KEY"
curl -s https://openrouter.ai/api/v1/key -H "Authorization: Bearer $OPENROUTER_API_KEY"
```

Credits: $65 total, $41.43 used, $23.57 remaining (2026-07-30).

### agy /usage (interactive only)

`/usage` inside an agy TUI session shows Google AI Pro subscription
quota. Not available as a headless/CLI flag — agy quota requires either
the interactive command or the opencode-quota companion package.

## /model-quota skill

The `/model-quota` skill at `~/.grok/skills/model-quota/SKILL.md` uses
`opencode-quota show --json` as its primary data source, supplemented by
the GLM usage-query plugin and OpenRouter direct API.

## Falsifier

This reference is wrong if:
- opencode-quota package is abandoned or stops working
- A provider changes their auth flow or API format
- New providers are added to the fleet not covered by opencode-quota
