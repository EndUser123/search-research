# HANDOFF: Chrome DevTools MCP Multi-Session Support (PR #991)

## Status: WAITING — upstream PR not yet merged

**Tracking:** Checked via `/maintain` Step 2h (scheduled checks). Registry entry at `P:/.data/scheduled-checks.json` → `mcp-multi-session-pr-991`. No scheduled task needed — `/maintain` surfaces resolution inline when it runs.

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
