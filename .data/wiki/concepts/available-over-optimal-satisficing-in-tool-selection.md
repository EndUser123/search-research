---
title: "Available-over-optimal satisficing in tool selection"
created: 2026-08-10
source: session-20260810
tags: [tool-selection, satisficing, anti-pattern, raw-get-diagnostic, closure-pressure]
categories: [behavioral-pattern, tool-fallbacks]
cognitive_load: 2
host: both
agent: grok
verification: observed
summary: >
  When a tool fails, agents reach for the nearest available alternative that
  works, then stop searching. "Available and works" feels sufficient under
  closure pressure, but it blocks discovering purpose-built tools that are
  architecturally superior. The raw-GET diagnostic (one command before tool
  selection) and the operator question "is that the BEST tool?" are the two
  interventions that prevent the pattern. Distinct from minimal-fix-and-root-
  cause (solution sizing) and writing-discipline-not-enforced (rules not firing).
sources:
  - session 2026-08-10 (ChatPeek vs browser MCP for ChatGPT shared links)
relations:
  - target: wiki/concepts/minimal-fix-and-root-cause.md
    type: related
  - target: wiki/concepts/writing-discipline-not-enforced.md
    type: related
  - target: wiki/concepts/reading-chatgpt-shared-links-js-spa.md
    type: example
  - target: wiki/concepts/tool-fallbacks.md
    type: extends
---

# Available-over-optimal satisficing in tool selection

## Decision context

**Why this was captured:** session 2026-08-10, the operator pasted a ChatGPT shared link and asked for its content. `web_fetch` failed (returns empty shell — strips React Flight payload). The agent reached for `chrome__use_browser` (browser MCP), which worked. The operator pushed: "But is that the best tool? I want the best tool, not the one that we have." Research revealed ChatPeek — a purpose-built parser that does one GET + decodes the React Flight payload, no browser needed. The browser MCP was available, worked, and was suboptimal. The agent stopped at "works" instead of continuing to "optimal."

**The real question behind this pattern:** why does "available and works" feel like a sufficient stopping criterion for tool selection, when one additional search would reveal a better tool?

## The pattern

```
Tool A fails
  → Agent reaches for Tool B (nearest available alternative)
  → Tool B works
  → Agent stops searching → ships Tool B as the answer
  → Operator asks: "Is that the BEST tool?"
  → Research reveals Tool C (purpose-built, architecturally superior)
  → Tool B was never optimal — just first-to-work
```

**Why it happens:** closure pressure. The agent has a working solution; researching alternatives feels like over-engineering. But "works" is not the same as "optimal." The cost of one search is ~10 seconds; the cost of shipping a suboptimal tool is cumulative (every future use pays the overhead).

## Why this is distinct from adjacent patterns

| Pattern | What it covers | How this differs |
|---------|---------------|------------------|
| [[minimal-fix-and-root-cause]] | Solution *sizing* — don't pick the smallest code change | This is about *tool selection* — don't pick the first tool that works |
| [[writing-discipline-not-enforced]] | Rules exist but don't fire under pressure | Here, no rule existed yet — the agent satisficed before any routing was wired |
| [[replacement-before-investigation]] | Recommending replacement without testing workarounds | Here, the agent didn't recommend replacement — it picked the available tool without investigating alternatives at all |

## The raw-GET diagnostic (transferable technique)

Before choosing a fetching tool, run **one raw HTTP GET** and grep the body for the content you need. This single step distinguishes parsing-problems (payload is there, extractor strips it) from rendering-problems (payload requires JS), which determines whether a parser or a browser is the right tool.

```powershell
$r = Invoke-WebRequest -Uri "<url>" -UseBasicParsing -TimeoutSec 20 `
     -Headers @{"User-Agent"="Mozilla/5.0 ... Chrome/120.0 Safari/537.36"}
$r.Content.Length           # body size — <50KB usually means shell
$r.Content -match '<expected-content-keyword>'  # is the text actually there?
```

**Cost:** ~200ms and one command. **Value:** determines the architecturally-correct tool before any tool is chosen. Session 2026-08-10: the raw GET returned HTTP 200, 489KB, with both `reactRouterContext` and the conversation keyword present — proving the browser was unnecessary before ChatPeek was even considered.

This generalizes to any SPA framework that embeds serialized state in `<script>` tags (React Flight, Next.js `__NEXT_DATA__`, SvelteKit `__sveltekit`).

## What this means for our workspace

**For agents:** when a tool fails, do NOT reach for the nearest available alternative without first asking: "Is there a purpose-built tool for this?" One web search (`<task> parser/scraper/CLI tool`) surfaces alternatives that may be architecturally superior.

**For routing:** proactive routing rules (AGENTS.md, skill routing tables) prevent the pattern structurally — if the routing rule says "ChatGPT shared links → ChatPeek," the agent never reaches the decision point where satisficing occurs. This is why the ChatPeek routing was wired across AGENTS.md + /www + /web, not just tool-fallbacks.

**For the operator:** the question "is that the best tool?" is the highest-leverage intervention. It costs one turn and prevents cumulative suboptimality. The agent should anticipate this question by researching alternatives before the operator asks — but until that behavior is reliable, the operator's question is the backstop.

## Receipts

| Claim | Evidence | Source |
|---|---|---|
| Agent picked browser MCP without researching alternatives | Session transcript — first response used `chrome__use_browser` | Session 2026-08-10, turn 1 |
| ChatPeek is architecturally superior (single GET + parse, no browser) | `P:/packages/ChatPeek/ChatPeek.py` — `DEFAULT_HEADERS` with private-window UA, React Flight parser, `ALLOWED_ASSET_HOST_SUFFIXES` SSRF defense | Source inspection, lines 1-80 |
| Raw-GET diagnostic proved browser unnecessary in one command | `Invoke-WebRequest` returned HTTP 200, 489KB, with `reactRouterContext` and conversation keyword present | Session 2026-08-10, raw GET receipt |
| "Available and works" felt sufficient under closure pressure | [INFERENCE] — the agent did not search for alternatives before picking the browser; the search happened only after the operator pushed |

## Falsifier

This concept is wrong if agents consistently research all available tools before picking one, and the "available-over-optimal" gap never appears in practice. Test: in the next 5 tool-failure events, does the agent search for alternatives before reaching for the nearest available tool? If yes, the pattern has been internalized and this concept can be retired. If no, the pattern persists and the concept remains load-bearing.

## Auto-related

- [[model-tool-calling-capability-matrix]]
- [[tool-fallbacks]]
- [[router-proxy-tool-calling-normalization-patterns]]
- [[skill-catalog]]
- [[I'm-going-to-create-a-hook-to-enforce-discovery-be]]

