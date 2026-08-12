# Handoff: yt-workspace CRITICAL fixes (2 silent-failure bugs)

**Created:** 2026-08-12
**Session:** 019fe3ff-afbc-71c1-b2a3-3cfbccfd2bc7
**Status:** OPEN
**Priority:** HIGH
**Assignee:** unassigned

## Objective

Fix the 2 CRITICAL findings from the yt-workspace code review (`P:/.artifacts/noterm/grok-review/yt-workspace-tp-fixes/FINDINGS.md`). Both produce silent-failure UX — the user clicks something and nothing visible happens.

## Findings

### CRITICAL 1: Workspace stuck in "Loading..." on shorts pages

**File:** `src/background/service-worker.ts:50-69` + `src/background/acquire.ts:165-194`
**Problem:** `acquireVideoContext` returns `null` when `result.videoId` is missing (shorts pages where `getPlayerResponse` doesn't expose `videoDetails.videoId` early). The content script mounts the workspace with `null` context, provenance shows "Loading..." forever.
**Fix:** Retry the acquire (shorts videoIds land in `ytInitialPlayerResponse` slightly later), or surface the failure in provenance ("acquire failed - reload page"), or send a delayed retry from `handleToolbarClick`.

### CRITICAL 2: Service worker unhandled rejections hang message channels

**File:** `src/entrypoints/background.ts:31-47`
**Problem:** `seek` and `query-workspace-state` handlers return `true` (keep channel open for async `sendResponse`) but `void handleSeekRequest(...).then(sendResponse)` has no `.catch`. If the promise rejects, `sendResponse` is never called, Chrome logs "message port closed", sender hangs.
**Fix:** Add `.catch((err) => { console.error("yt-workspace handler failed", err); sendResponse({ ok: false, error: String(err), beforeTime: -1, afterTime: -1 }); })` on both promise chains. Ensure `appendDiagnostic` never rejects (wrap `chrome.storage.local.set` in try/catch).

## Additional findings (HIGH priority, same file)

- **Toolbar-toggle race:** rapid open/close/open can leave workspace permanently open (needs per-tab AbortController)
- **SW state loss:** `setAuthoritativeVideoId` is in-memory only, wiped on MV3 SW restart (persist to `chrome.storage.session`)
- **Settings panel listener leak:** `createSettingsButton` registers a new click listener on every remount (use AbortController)
- **Storage quota:** `appendDiagnostic` has no try/catch on `chrome.storage.local.set` — quota rejection cascades to silent toolbar failure

## Scope

- Package: `P:/packages/yt-workspace/`
- Read the package CLAUDE.md/AGENTS.md before starting
- Build verification: `pnpm build` + `tsc --noEmit` must exit 0
- No tests exist — add vitest tests for `applyResult` and `parseTimestampToSeconds` while fixing

## Acceptance criteria

1. Shorts pages show video context (not "Loading...") within 2 seconds
2. No "message port closed" errors in console during seek/query operations
3. `pnpm build` + `tsc --noEmit` pass clean
4. At least 1 test for `applyResult` state machine

## Files

- Review findings: `P:/.artifacts/noterm/grok-review/yt-workspace-tp-fixes/FINDINGS.md`
- Package: `P:/packages/yt-workspace/src/`
