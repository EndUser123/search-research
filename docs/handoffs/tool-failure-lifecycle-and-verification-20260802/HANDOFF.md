# Handoff: Tool-Failure Lifecycle + Verification Gates

## Status
OPEN — 2 design questions remain (passive telemetry + circuit breaker wrapping)

## Created
2026-08-02
## Revised
2026-08-02 (multiple revisions: /tp critique, pre-mortem, research validation)

## Assignee
grok (fresh session)

## What's already done (from session 2026-08-02)

| Item | Status | Commit |
|---|---|---|
| Tool-fallbacks STRUCTURAL/TRANSIENT classification | ✅ Done | c8dd7d1 |
| Tool-fallbacks TTL-as-condition + re-test rules | ✅ Done | c8dd7d1 |
| Reddit failures reclassified STRUCTURAL | ✅ Done | 2025aaa |
| Reddit RSS MCP installed (ninjackster/reddit-rss-mcp) | ✅ Done | cd340f6 |
| Wiki: tool-failure lifecycle (passive monitoring, not active probes) | ✅ Done | 51b5e04 |
| Wiki: inference-in-code blind spot | ✅ Done | b2b1c94 |
| Wiki: agent skills fleet patterns | ✅ Done | 36ac943 |
| AGENTS.md verify-before-write rule | ✅ Done | b739023 |
| AGENTS.md tool-failure awareness pattern | ✅ Done | 8b954f9 |
| AGENTS.md tool-failure classification (STRUCTURAL/TRANSIENT) | ✅ Done | 59d1d34 |
| /www gap-as-signal disconfirmation step | ✅ Done | e04c147 |
| fleet_quota.py Perplexity inline receipts | ✅ Done | c7835dd |

## What remains (2 design questions)

### Question 1: Passive telemetry at session start

**The revised approach** (replaces the killed active-probing idea):
- At session start, read `P:/.claude/hooks/.evidence/` and `cc_errors.jsonl` for recent tool failures
- Surface findings to the agent as "these tools failed recently — plan accordingly"
- No active probing of MCP tools (pre-mortem showed this is an anti-pattern)

**Design decisions needed:**
- Should this be a SessionStart hook (mechanical, runs before agent starts)?
- Or a step in AGENTS.md's per-turn protocol (behavioral, agent reads the log)?
- Or a `/check` sub-command (on-demand, not automatic)?
- What time window? Last 24h? Last session?

### Question 2: Lazy first-use with circuit breaker wrapping

**The approach:** wrap MCP tool calls with tenacity + pybreaker so:
- First use of a tool auto-retries on transient failure (exponential backoff)
- After N failures, circuit opens and fallback fires automatically
- No session-start probe needed — the first real use IS the probe

**Design decisions needed:**
- Should this be in each skill that uses MCP tools (per-skill wrapping)?
- Or in a shared library that all skills import?
- Or in the MCP transport layer itself (config.toml wrapper)?
- What library: tenacity + pybreaker (Python), or a Node.js equivalent?

## Selection criterion

Optimal long-term: the solution that catches tool failures with zero session-start latency, zero thundering-herd risk, and automatic circuit-open behavior — without requiring per-skill modification.

## Key files

- `C:/Users/brsth/.grok/AGENTS.md` — verify-before-write rule + tool-failure awareness pattern
- `P:/.data/wiki/concepts/tool-fallbacks.md` — STRUCTURAL/TRANSIENT classification + entries
- `P:/.data/wiki/concepts/tool-failure-lifecycle-llm-agent-fleets.md` — lifecycle design (revised after pre-mortem)
- `P:/.data/wiki/concepts/inference-in-code-blind-spot.md` — the session incident
- `C:/Users/brsth/.grok/config.toml` — reddit-rss MCP added
- `C:/Users/brsth/.grok/skills/www/SKILL.md` — gap-as-signal disconfirmation step

## Context

The session started with TTS research, evolved into Perplexity quota debugging, then meta-analyzed the failure pattern (inference-in-code), researched the tool-failure lifecycle, pre-mortem'd the session-start probe idea (killed it), and designed a passive-monitoring + lazy-first-use replacement. All wiki concepts are written and validated. Only the two design questions above remain.
