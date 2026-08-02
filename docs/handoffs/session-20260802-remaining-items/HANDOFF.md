# Handoff: Session 2026-08-02 Remaining Items

## Status
OPEN — 3 items, all low-to-medium urgency

## Created
2026-08-02

## Assignee
grok (fresh session)

## Item 1: Passive telemetry at session start

**Problem:** pre-mortem killed active session-start probing (anti-pattern: thundering herd, false positives). Replaced with passive approach: read `cc_errors.jsonl` and `hooks/.evidence/` at session start to surface recent tool failures.

**Design decision needed:** SessionStart hook (mechanical) vs AGENTS.md per-turn step (behavioral) vs `/check` sub-command (on-demand)?

**Key constraint:** must not add latency to session start (the reason we killed active probing).

## Item 2: Reddit MCP follow-up

**Done:** `reddit-rss` MCP installed in config.toml + .claude.json. Existing `reddit` (browse) and `dialog-mcp` (semantic search) confirmed working.

**Not done:** 
- Test `reddit-rss` MCP with actual tool calls (only tested server starts)
- old.reddit.com still works (HTTP 200) but login required "soon" per Ars Technica
- When old.reddit.com dies, update all tool-fallbacks references to point at reddit-rss exclusively

**Not urgent** — old.reddit.com hasn't died yet. But when it does, the /www and /web SKILL.md references to old.reddit.com need updating.

## Item 3: AGENTS.md bloat assessment

**Research finding (session 2026-08-02):** Anthropic best-practices recommends CLAUDE.md/AGENTS.md under 200 lines. Our AGENTS.md is far beyond that. Cited research: linear compliance decay, <30% perfect compliance with prose rules (AgentIF, anthropics/claude-code#32163).

**Design question:** should we restructure AGENTS.md to move topic-specific rules to separate files (like `~/.claude/rules/`) and keep the main file as a thin pointer? Or split into multiple AGENTS.md files by domain?

**Not urgent** — but worth assessing whether the bloat is causing rule-firing degradation.

## Key files

- `C:/Users/brsth/.grok/AGENTS.md` — the file in question (item 3)
- `C:/Users/brsth/.grok/config.toml` — reddit-rss MCP config (item 2)
- `P:/.data/wiki/concepts/tool-fallbacks.md` — Reddit entries (item 2)
- `P:/docs/handoffs/tool-failure-lifecycle-and-verification-20260802/HANDOFF.md` — item 1 context

## Context

Session 2026-08-02 was a long session spanning TTS research → Perplexity quota debugging → meta-analysis of agent behavior → tool-failure lifecycle design → epistemic knowledge system design. All high-urgency work shipped. These 3 items are follow-up tasks.
