---
title: "Multi-LLM aggregator landscape: browser extensions, desktop apps, and MCP orchestration"
slug: multi-llm-aggregator-landscape
date: 2026-08-01
tags: [multi-llm, aggregator, browser-automation, model-web, ensemble, architecture, transferable-technique]
host: grok
---

# Multi-LLM aggregator landscape

## Summary

Three architectural patterns exist for sending one prompt to multiple LLMs simultaneously: (1) Chrome extension DOM injection (AI-Multichat, ChatHub), (2) Electron desktop apps with embedded browser views (ChatALL, ParallelChat), and (3) API-level routing (big-AGI Beam, LibreChat). No existing tool combines browser automation (using authenticated web sessions, not API keys) with agent-driven orchestration (ranking, synthesis, follow-up). `/model-web` occupies this niche uniquely.

## Decision context

### The problem

During ensemble testing (session 019fba58, 2026-08-01), the operator asked whether purpose-built tools exist that "show a web page with a chat entry, but then automatically distribute to multiple LLMs automatically out of sight." The question: should we replace or supplement `/model-web`'s sequential MCP blast/collect protocol with an existing tool?

### What the research changed

The research confirmed that `/model-web`'s unique value is agent-driven orchestration — no existing tool combines browser automation with programmatic collection, ranking, and synthesis. The right architecture is hybrid: a Chrome extension for quick parallel blasts + `/model-web` for agent-driven ensemble work.

## Architectural patterns

### Pattern 1: Chrome extension DOM injection

Content scripts injected into each open LLM tab find the input field and send button via site-specific CSS selectors, type the prompt, click send, then scrape responses from the DOM.

| Tool | License | Stars | LLMs | Key feature |
|---|---|---|---|---|
| **AI-Multichat-Extension** (AndrewJu246) | MIT | new | ChatGPT, Claude, Gemini, DeepSeek | Swap & Debate round-robin mode |
| **Multi-LLM** (jaidev7823) | Open | new | 10 sites including Poe, Mistral, Cohere, Perplexity, You.com, HuggingFace |
| **ChatHub** (chathub-dev) | GPL-3.0 | 10,638 | ChatGPT, Claude, Gemini, Llama, 20+ | Most polished consumer product |
| **Multi-AI-Prompt** | Closed | N/A | Up to 30 tabs |

**Strengths:** true parallel dispatch (all tabs fire simultaneously), uses authenticated sessions, zero API cost.
**Weaknesses:** no response ranking or synthesis; breaks when providers update their UI; no agent orchestration.

### Pattern 2: Electron desktop apps (embedded browser views)

Standalone app spawns its own browser windows for each LLM, loads each site with the user's session, injects prompts.

| Tool | License | Stars | Key feature |
|---|---|---|---|
| **ChatALL** (ai-shifu) | MIT | 17,000+ | Most mature; web + API modes; warns web mode breaks frequently |
| **ParallelChat** (woniu9524) | GPL | 193 | Closest architectural twin to `/model-web` — automates official LLM websites directly |
| **LLM-God** (czhou578) | Open | new | Simple JS injection into BrowserWindow views |

**Strengths:** standalone (doesn't need an agent framework); true parallel; web-access mode uses authenticated sessions.
**Weaknesses:** manages own browser instances (can't connect to existing Chrome); UI updates break automation; no agent integration.

### Pattern 3: API-level routing (not web-session-based)

Sends one prompt to multiple model APIs in parallel using user-provided API keys.

| Tool | License | Stars | Key feature |
|---|---|---|---|
| **big-AGI** (enricoros) | MIT | 7,071 | Beam: 1 prompt → 24 models → best-of-N merge |
| **LibreChat** (danny-avila) | MIT | 41,516 | Self-hosted platform, MCP support, side-by-side |
| **ChatPlayground** | Commercial | N/A | $20/mo, parallel comparison |
| **MultipleChat** | Commercial | N/A | Web workspace for ChatGPT/Claude/Gemini/Grok |

**Strengths:** most reliable (API contracts are stable, unlike DOM selectors); best merge logic (big-AGI Beam).
**Weaknesses:** uses API quota (not web subscription quota); requires API keys; doesn't leverage operator's existing web subscriptions.

### Pattern 4: MCP orchestration (our approach)

`/model-web` uses Chrome DevTools MCP with `--autoConnect` to a real authenticated Chrome session. Agent sends prompts to each tab via `evaluate_script`/`click`/`type_text`, collects responses, ranks them, and synthesizes.

**Strengths:** uses web subscription quota; full agent orchestration (ranking, synthesis, follow-up questions); MCP-native (integrates with agent fleet); documents per-site input methods and failure modes.
**Weaknesses:** sequential (not true parallel); depends on MCP single-session limitation until PR #991 merges.

## How /model-web compares

| Dimension | `/model-web` | Chrome extensions | Electron apps | API routers |
|---|---|---|---|---|
| Uses web sessions (not API) | ✅ | ✅ | ✅ | ❌ |
| Agent-driven ranking | ✅ | ❌ | ❌ | big-AGI only |
| Follow-up questions | ✅ | ❌ | ❌ | ❌ |
| True parallel | ❌ (sequential) | ✅ | ✅ | ✅ |
| Integrates with agent fleet | ✅ (MCP) | ❌ | ❌ | ❌ |
| Stable across UI updates | Documented fixes | Breaks | Breaks | ✅ |

## Recommended hybrid architecture

- **Quick parallel blast** (eyeball N responses): install a Chrome extension (AI-Multichat-Extension, MIT). Operator types once, all tabs fire simultaneously.
- **Agent-driven ensemble** (collect → rank → synthesize): use `/model-web`. The agent controls the full pipeline.
- **Borrow from all repos:** site selectors from AI-Multichat and ParallelChat; merge/rank logic from big-AGI Beam.

## Cloned repos for reference

| Repo | Path | What to extract |
|---|---|---|
| AI-Multichat-Extension | `P:/packages/.github_repos/AI-Multichat-Extension/` | Site DOM selectors, React input methods, Swap & Debate architecture |
| ParallelChat | `P:/packages/.github_repos/ParallelChat/` | Chinese LLM selectors (Kimi, Qwen, Doubao, Yuanbao, GLM), parallel dispatch pattern |
| big-AGI | `P:/packages/.github_repos/big-AGI/` | Beam merge/rank logic, provider adapter pattern |

## Future upgrade path

Chrome DevTools MCP shipped two flags for concurrent sessions (issue #926, resolved
2026-02-23). Two PRs proposing `create_session`/`close_session` tools (#899, #1241)
were **closed without merging**. Instead, the team shipped:

- `--experimentalPageIdRouting`: exposes `pageId` on page-scoped tools for concurrent
  agents sharing one server
- `--isolated`: separate temporary Chrome profiles per server instance

**Neither helps `/model-web`:** `--isolated` breaks `--autoConnect` authentication
(launches new Chrome), and `--experimentalPageIdRouting` targets a multi-agent-per-server
architecture we don't use. Our sequential `select_page` blast/collect protocol remains
correct.

## Cross-references

- [[browser-automation-failure-modes-llm-chat]] — per-site input methods and failure modes
- [[chrome-autoconnect-for-authenticated-cdp-sessions]] — why we use autoConnect
- [[captcha-solving-for-non-vision-llm-agents]] — CAPTCHA handling for browser automation
- [[parallel-cdp-mcp-servers-openchrome]] — parallel CDP upgrade path
- [[research-quality-principle-efficiency-not-censorship]] — research methodology

## Falsifier

This landscape analysis becomes stale if:
- Chrome DevTools MCP merges PR #991 (collapses Pattern 4 into Pattern 1)
- LLM providers offer official multi-model APIs (eliminates need for browser automation)
- ChatALL or ChatHub add agent orchestration features (eliminates `/model-web`'s unique value)
- Providers block all browser automation regardless of CAPTCHA solving
