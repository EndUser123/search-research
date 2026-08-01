---
current_session_id: 019fb933-040b-7720-a257-e364f5df726f
last_updated_by: 019fb933-040b-7720-a257-e364f5df726f
last_updated_at: 2026-08-01T13:10:46.831448
parent_session: none
produced_at: 2026-08-01T13:10:46.831448
status: open
handoff_type: investigation
---
# Workflow Friction: Session-Close Pipeline + Perplexity→Grok Handoff

## Goal
Eliminate two chronic workflow friction patterns: (1) manual session-close skill chaining, (2) manual Perplexity→Grok paste-buffer handoff.

## Session
019fb933-040b-7720-a257-e364f5df726f (2026-07-31)

## Status
OPEN — identified via `/friction`, tracked in `/harvest`, not yet implemented.

## Tasks

### 1. Extend `/close` to chain session-close skills
**Friction:** The operator manually ran `/harvest`, `/capture`, `/friction`, `/slc`, `/recap-grok`, `/wiki`, and `/handoff` in sequence at session close (7 invocations). `/close` chains some of these but misses `/harvest`, `/friction`, `/slc`, and `/recap-grok`.

**Fix:** Add `/harvest`, `/friction`, and `/slc` to `/close`'s mandatory gate template between the AAR step and the summary step. The `/capture` SKILL.md already documents `/close` integration — the gap is that `/close` doesn't actually invoke `/capture`, `/harvest`, or `/friction`.

**File:** `~/.grok/skills/close/SKILL.md` — gate template section

**Harvest item:** `01KYXN38EC96TRQZYRKTJ0P2KG`

**Verification:** run `/close` after the change and confirm all skills fire in the summary.

### 2. Automate Perplexity→Grok handoff (chronic, cross-session)
**Friction:** The operator manually pastes Perplexity (or other web-LLM) responses into the Grok chat for evaluation. This happened 5+ times this session, and the session literally started with a pasted Perplexity transcript (`## User.txt`). This pattern recurs across many sessions.

**Why it matters:** The manual paste buffer is the operator acting as a router between two LLMs. The `web-model` skill exists for browser-LLM interaction via Chrome DevTools MCP, but it wasn't used. The Perplexity web-mcp skill (`perplexity-web-mcp`) also exists but does API queries, not browser-session handoff.

**Possible fixes (in order of effort):**
- **Low effort:** Add an AGENTS.md rule: "when the operator pastes a web-LLM response, suggest using `/web-model` or the `perplexity-web-mcp` skill for the next query instead of manual paste." Behavioral, not structural.
- **Medium effort:** Extend `/web-model` or create a `/cross-model-debate` command that sends a prompt to a web-LLM, extracts the response, and feeds it back automatically — no manual paste needed.
- **High effort:** Build a Perplexity session bridge that maintains context across turns (the operator currently re-pastes context each time because Perplexity loses it).

**What to decide next session:** which effort tier is appropriate, and whether `web-model` already covers this (it may just need discoverability — the operator didn't know to use it).

## Key decisions
- Both items identified via `/friction` scan and confirmed as chronic (5+ occurrences each, cross-session for #2)
- `/harvest` tracks the obligations but doesn't produce next-session work instructions — that's why these need handoffs

## Next session checklist
- [ ] Read `/close/SKILL.md` gate template and add `/harvest` + `/friction` + `/slc` as mandatory steps
- [ ] Evaluate whether `web-model` skill covers the Perplexity handoff; if so, add discoverability; if not, decide on automation tier

## Changelog

| Date | Session | Action |
|------|---------|--------|
| 2026-08-01T13:10 | 019fb933-040... | backfilled session_id from transcript scan |
