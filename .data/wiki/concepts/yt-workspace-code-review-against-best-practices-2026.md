---
title: "yt-workspace code review against Chrome extension best practices (2026)"
date_created: 2026-08-12
tags: [www-synced, reference, chrome-extension, youtube, mv3, best-practices, code-review]
confidence: HIGH
verification_tier: 1
sources:
  - "Chrome official: Service Worker Lifecycle (developer.chrome.com)"
  - "LectureLoop dev.to: YouTube SPA Navigation in Chrome Extensions"
  - "javaspring.net: Detect YouTube Video Changes with Injected JavaScript"
  - "Groovyweb: Chrome Extension Development Guide 2026"
  - "Reddit r/chrome_extensions: MV3 service worker patterns"
  - "SponsorBlock source (github.com/ajayyy/SponsorBlock)"
---

# yt-workspace code review against Chrome extension best practices

## Workspace observations (Phase 1a)

1. **MV3 service worker state loss is a known unfixed issue.** Our `tabStates` Map in `video-context-store.ts` is wiped on SW dormancy (~30s idle). The /tp review flagged this as HIGH severity.
2. **SPA navigation uses `yt-navigate-finish` custom event.** The bug we fixed (content not updating on video switch) was caused by using `sender.tab.url` (stale) instead of `message.url` (current).
3. **Trusted Types compliance is achieved by avoiding `innerHTML` and `DOMParser`.** All DOM construction uses `createElement` + `textContent`.

## Findings: our code vs best practices

### 1. Service worker state persistence — GAP (HIGH)

**Our code:** module-level `Map<number, TabState>` in `video-context-store.ts`. State is wiped when Chrome terminates the service worker after 30s of inactivity.

**Best practice (official Chrome docs):** "Any global variables you set will be lost if the service worker shuts down. Instead of using global variables, save values to storage." Options: `chrome.storage.session` (1MB, cleared on browser close), `chrome.storage.local` (10MB, persistent), `IndexedDB` (structured data).

**Practitioner consensus (Reddit r/chrome_extensions):** "Stop trying to make MV3 behave like MV2. Treat the worker like a lambda — stateless, short-lived, event-triggered."

**Recommendation:** Persist `currentAuthoritativeVideoId` and `currentUrl` to `chrome.storage.session` keyed by tabId. Read from storage in `getTabState()` when the in-memory entry is absent. This eliminates spurious re-fetches after SW restart.

### 2. SPA navigation detection — CORRECT (with minor improvement needed)

**Our code:** Content script listens for YouTube's `yt-navigate-finish` custom event, relays `location.href` to background via `chrome.runtime.sendMessage`.

**Best practice:** Three approaches exist:
- `yt-navigate-finish` event (YouTube-specific, SponsorBlock-compatible) ← **what we use**
- MutationObserver on `document.body` comparing `location.href` (LectureLoop pattern)
- `chrome.webNavigation.onHistoryStateUpdated` (requires `webNavigation` permission)

**Assessment:** Our approach is correct and standard for YouTube-specific extensions. SponsorBlock and ResizeYoutubePlayer use the same `yt-navigate-finish` event. The recent fix (using `message.url` instead of `sender.tab.url`) was right — Chrome's tab model URL is stale during pushState.

**Minor gap:** LectureLoop recommends a cancellation token for async init: "Start each `init()` with an incrementing ID, and bail out of async steps if a newer ID has been issued." Our `acquireVideoContext` is not reentrancy-guarded — rapid navigation could cause concurrent MAIN-world injections to race.

### 3. Message passing error handling — GAP (CRITICAL, already flagged by /tp)

**Our code:** `background.ts` seek/query handlers use `void handleSeekRequest(...).then(sendResponse)` with no `.catch`.

**Best practice (every tutorial + official docs):** Always add `.catch` that sends an error response when returning `true` to keep the channel open. If the promise rejects, `sendResponse` is never called and Chrome logs "message port closed" + the sender hangs.

**Recommendation:** Add `.catch((err) => { console.error(err); sendResponse({ ok: false, error: String(err) }); })` on both promise chains.

### 4. MAIN-world script injection — CORRECT

**Our code:** `chrome.scripting.executeScript({ world: "MAIN", func: readYouTubeData })`.

**Best practice:** This is the documented Chrome API for reading page-context globals from an extension. The freshness invariant (videoId check before applying results) matches the pattern documented in our wiki build research.

**Trade-off noted:** LectureLoop author points out that `scripting` permission triggers a CWS review warning about "reading browsing history." However, since we use `activeTab` (not broad host permissions for scripting), this is minimal. Our permission set (scripting, activeTab, storage, youtube.com host) is clean and justified.

### 5. DOM selector resilience — PARTIAL

**Our code:** `#secondary` with fallback to `#related` (added in playlist fix). `#movie_player` for player access. `video` element for seek.

**Best practice (SponsorBlock pattern + javaspring article):** Use multiple fallback selectors. SponsorBlock maintains arrays of selectors and patches them frequently when YouTube changes its DOM. The javaspring article recommends: `['#player', '.html5-video-container', 'ytd-player', '[data-video-id]']`.

**Assessment:** Our selectors are minimal. `#secondary` → `#related` fallback is good (playlist fix). But `#movie_player` is a single point of failure — if YouTube renames it, acquisition breaks entirely. Consider adding `ytd-player` or `#player-api` as fallbacks.

### 6. Permissions — CORRECT

**Our manifest:** `scripting`, `activeTab`, `storage`, `host_permissions: ["*://*.youtube.com/*"]`.

**Best practice:** Minimal permissions, no `tabs`, no `webNavigation`, no `history`. The groovyweb article confirms this is the right set for a YouTube content-modification extension. Clean for CWS review.

### 7. Build stack — CORRECT

**WXT + TypeScript + Vite.** Already confirmed as best practice in `[[chrome-acp-library-stack-and-best-practices-2026]]`. WXT handles MV3 manifest generation, content script auto-injection, and cross-browser compatibility.

### 8. Trusted Types compliance — CORRECT (conservative but safe)

**Our code:** No `innerHTML`, no `DOMParser`, no `eval`. All DOM construction via `createElement` + `textContent`.

**Assessment:** This is more conservative than necessary — YouTube's CSP allows a Trusted Types policy that would permit `innerHTML` with a declared policy. But the conservative approach is safe and avoids the overhead of managing a TT policy. No change needed.

## Priority-ranked recommendations

| Priority | Finding | Fix shape | Effort |
|----------|---------|-----------|--------|
| CRITICAL | Message handler `.catch` missing | Add `.catch` to 2 promise chains in background.ts | 5 min |
| HIGH | SW state persistence | Persist videoId to `chrome.storage.session` | 30 min |
| MEDIUM | Acquire reentrancy guard | Track in-flight per-tab acquire Promise | 20 min |
| MEDIUM | Player selector fallback | Add `ytd-player` / `#player-api` as fallbacks | 10 min |
| LOW | Debounce navigation handler | Add cancellation token to mountIfNeeded | 15 min |

## Cross-references

- [[youtube-workspace-sidebar-extension-build-research]] — original build research
- [[youtube-chapter-json-path-ytinitialdata-not-player-response]] — data acquisition path
- [[chrome-acp-library-stack-and-best-practices-2026]] — WXT/CRXJS build stack
- [[youtube-transcript-extraction-techniques]] — transcript acquisition methods
