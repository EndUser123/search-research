---
current_session_id: 019fb933-040b-7720-a257-e364f5df726f
last_updated_by: 019fb933-040b-7720-a257-e364f5df726f
last_updated_at: 2026-08-01T13:10:46.831448
parent_session: none
produced_at: 2026-08-01T13:10:46.831448
status: open
handoff_type: investigation
---
# HANDOFF: Chrome DevTools MCP Multi-Session Support (PR #991)

## Status: RESOLVED — shipped differently than planned (no action needed)

**Finding (2026-08-01):** Issue #926 was closed as COMPLETED (2026-02-23). Two PRs
(#899, #1241) proposed `create_session`/`list_sessions`/`close_session` tools with
`BrowserContext` isolation — both were **closed without merging**. The team shipped
a simpler approach: `--experimentalPageIdRouting` flag (route by pageId without
`select_page`) and `--isolated` flag (separate temporary profiles per server instance).

**Impact on `/model-web`:** No action needed. Our sequential blast/collect protocol
via `select_page` + `--autoConnect` remains correct:
- `--isolated` breaks our authentication requirement (launches new Chrome, not real session)
- `--experimentalPageIdRouting` helps multiple agents sharing one server — we have one orchestrator
- The `create_session`/`close_session` API the handoff planned around does not exist

**Recommendation:** mark this handoff as resolved-no-action. Update the wiki concept
`[[multi-llm-aggregator-landscape]]` to note the shipped approach.

## Objective
When Chrome DevTools MCP merges multi-session support (create_session / list_sessions / close_session), upgrade `/model-web`'s ensemble protocol from sequential blast/collect to true parallel multi-session dispatch.

## What to watch

**Issue/PR:** https://github.com/ChromeDevTools/chrome-devtools-mcp/issues/926
**Proposed API:** `create_session`, `list_sessions`, `close_session` tools. Each session has isolated cookies/auth state. All existing tools gain a `sessionId` parameter.

**Current status (2026-08-01):** PR was closed (not yet merged). The need is acknowledged by the team. Check for a new PR or a reopened issue.

## Implementation plan (when PR merges)

### Step 1: Update chrome-devtools-mcp
```powershell
cd ~/.grok/installed-plugins/chrome-devtools-mcp-2df60288
# Check new version
npm info chrome-devtools-mcp version
# Update plugin.json args if API changed
```

### Step 2: Upgrade /model-web ensemble protocol
Current protocol (sequential):
```
for each site:
    navigate_page(url)
    fill/click/type_text prompt
    wait for response
    collect response
```

New protocol (parallel):
```
for each site:
    session = create_session()
    navigate_page(url, sessionId=session)
    fill/click/type_text prompt (sessionId=session)

for each site:
    wait for response (sessionId=session)
    collect response (sessionId=session)
```

### Step 3: Update SKILL.md
- Replace "blast/collect" section with "parallel multi-session" section
- Document `create_session` / `close_session` lifecycle
- Keep sequential as fallback for single-session MCP versions

### Step 4: Test
- Run ensemble test with 4+ models in parallel
- Verify response collection works across sessions
- Verify session isolation (cookies don't bleed)

## Files to modify
- `~/.grok/skills/model-web/SKILL.md` — ensemble protocol section
- `~/.grok/installed-plugins/chrome-devtools-mcp-2df60288/.claude-plugin/plugin.json` — version bump if needed
- `P:/.data/wiki/concepts/multi-llm-aggregator-landscape.md` — update Pattern 4 to note parallel is now native
- `P:/.data/wiki/concepts/parallel-cdp-mcp-servers-openchrome.md` — update with native multi-session as alternative to OpenChrome

## Dependencies
- chrome-devtools-mcp version that includes multi-session support
- `/model-web` skill (current version)

## Acceptance criteria
- [ ] chrome-devtools-mcp updated to version with multi-session
- [ ] `/model-web` ensemble protocol updated to parallel
- [ ] Ensemble test with 4+ models runs in parallel (wall-clock < sequential / N)
- [ ] Sequential fallback documented for backward compatibility

## Changelog

| Date | Session | Action |
|------|---------|--------|
| 2026-08-01T13:10 | 019fb933-040... | backfilled session_id from transcript scan |
