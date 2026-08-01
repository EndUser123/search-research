---
current_session_id: 019fb0c3-2ca7-7f22-9a2e-203130cb6e99
last_updated_by: 019fb0c3-2ca7-7f22-9a2e-203130cb6e99
last_updated_at: 2026-07-30T19:31:28.014550
parent_session: none
produced_at: 2026-07-30T19:31:28.014550
status: open
handoff_type: investigation
---
# Handoff: Chrome ACP Proxy — P11 + Remaining Live Testing

## Objective
Implement P11 (persistent agent process) properly, and complete live testing of UI features that are present in code but need operator confirmation.

## Context
Chrome ACP proxy bridges browser tabs to Grok Build via WebSocket + ACP stdio. Session shipped with all review findings fixed. Every reconnect cold-starts a fresh `grok agent stdio` (~2-3s). P11 would eliminate this.

## P11 proper implementation (mutable client proxy pattern)
The SDK's `ClientSideConnection` captures the client callback in constructor closures (`acp.js:364-365`). You can't replace the client after construction. Use an indirection layer:

```javascript
const clientRef = { ws: null, state: null };
function createClient(clientRef) {
  return {
    async requestPermission(params) {
      const { ws, state } = clientRef;
      // ... use ws and state from ref
    },
    // ... same for sessionUpdate, extMethod, extNotification
  };
}
// In handleConnect: clientRef.ws = ws; clientRef.state = state;
// Process lifecycle: agentProcess.on('exit', () => { persistentProcess = null; ... })
// Liveness: persistentProcess.exitCode === null
```

## Acceptance criteria
- [ ] Reconnect uses warm process (no respawn)
- [ ] Agent crash detected within 1 tick
- [ ] Second client gets a NEW process
- [ ] All 19 tests still pass

## Live testing checklist (present in code, needs operator confirmation)
- [ ] Resize handle drag works
- [ ] File search filters correctly
- [ ] Thinking toggle hides/shows reasoning text
- [ ] Tool-call toggle hides/shows tool entries
- [ ] Permission auto-open works
- [ ] Error toast appears on proxy error
- [ ] Reload button reloads extension
- [ ] browser_read on Perplexity after Comet policy patch

## Files
- Proxy: `...\proxy-server\dist\server.js`
- Files: `...\proxy-server\dist\files.js`
- Handler: `...\proxy-server\dist\mcp\handler.js`
- Command: `...\proxy-server\dist\cli\command.js`
- Extension: `...\chrome-acp\dist\sidepanel-t6n74ra3.js`
- Tests: `P:/tmp/acp-verify/test_patched_files.py`
- Wiki: `P:/.data/wiki/concepts/chrome-acp-grok-build-setup-implementation.md`

## Changelog

| Date | Session | Action |
|------|---------|--------|
| 2026-07-30T19:31 | 019fb0c3-2ca... | backfilled session_id from transcript scan |
