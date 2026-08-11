---
thread_id: 8c182e5b-ed61-48c4-8a95-d78d4c97ad35
parent_handoff_path: P:/docs/handoffs/youtube-workspace-extension-gate2-20260810/HANDOFF.md
current_session_id: 019fea30-500e-7b83-abac-d737446e86fb
parent_session: 019fea30-500e-7b83-abac-d737446e86fb
current_terminal_id: 019fea30-500e-7b83-abac-d737446e86fb
produced_at: 2026-08-10T08:05:00Z
last_updated_by: 019fee39-abb7-7490-a66a-e2cd7df5600a
last_updated_at: 2026-08-11T00:45:00Z
status: open
handoff_type: implementation-spike
accurate_as_of_head: 2f003f6
assigned_to: grok
assigned_at: 2026-08-11T00:32:46
assigned_by: 019fee39-abb7-7490-a66a-e2cd7df5600a
---




# Handoff — yt-workspace: Chapters Vertical Slice

## Objective

Build a **real, installable, usable** Chrome extension that delivers the Chapters experience end-to-end through the actual MV3/WXT execution environment. **This is not a scaffold** — plumbing that "passes" while leaving important integration risks unresolved is the failure mode this handoff explicitly guards against.

**Done means:** I could install this extension unpacked in `chrome://extensions/`, navigate to a real YouTube watch page, click the toolbar button, see a tabbed workspace appear in YouTube's right column, watch the Chapters tab render the video's chapters, click a chapter row and watch the actual movie player seek, navigate from video A to video B and watch the workspace re-mount with B's chapters, and — crucially — the freshness invariant rejects a late A-result with the structured `rejected_stale` diagnostic the operator specified. At that point I have a **good Chapters extension**, not a passing test suite.

**Scope bounds:** This is the first product-valuable deliverable. Gate 3 (YouTube Ask as opportunistic backend) is a **separate spike** that runs *after* this vertical slice ships and is evaluated as a product, not a dependency. Whisper fallback, polished UI, Chrome Web Store packaging, and the receipt-identity investigation are explicitly out of scope.

## Status

OPEN — ready for `/go`. Inherits the EXTRACT + IN_PAGE_SECONDARY decisions from Gate 1 and the runtime contract from Gate 2; does NOT re-decide them. The verification-receipt identity-provenance smell is recorded in a separate deferred-reliability handoff (do not address here).

## Producing context

- Date: 2026-08-10
- Session: 019fea30... (this session — prep only)
- Operator directive (verbatim, summarized): "Build a vertical-slice extension, not a scaffold. The next artifact should already be useful. Toolbar click → real YouTube page → workspace replaces `#secondary` → Chapters appear → timestamp click seeks → navigation A→B works → stale A result is observably rejected. That's essentially the proven Gate 2 mechanism transplanted into the actual MV3/WXT execution environment. Done means: I could install this extension and already use it as a good Chapters extension."

## Read-first list (ordered)

1. **This handoff** — full scope, task packets, hard constraints, permission discipline.
2. **Gate 1 handoff** — `P:/docs/handoffs/youtube-workspace-extension-gate1-20260810/HANDOFF.md` — EXTRACT + IN_PAGE_SECONDARY decisions and the **module retain/remove/add lists**. The 13 files to extract are listed in D1's "Modules retained" subsection.
3. **Gate 2 handoff** — `P:/docs/handoffs/youtube-workspace-extension-gate2-20260810/HANDOFF.md` — runtime contract proven via the 6 task packets. **Especially:** `## Execution Status` block at the end of the file (lists evidence files, key findings, structured diagnostic shape).
4. **Research concept** — `P:/.data/wiki/concepts/youtube-workspace-sidebar-extension-build-research.md` — 3-gate sequence (this is implementation phase, NOT Gate 3), MAIN-world bridge correction, transcript/chapter acquisition notes.
5. **Receipt-identity-provenance handoff** — `P:/docs/handoffs/receipt-identity-provenance-unverified-20260810/HANDOFF.md` — separate reliability investigation, NOT this workstream's concern.

## Inherited decisions (DO NOT RE-DECIDE)

- **Reuse strategy:** EXTRACT from `steipete/summarize`'s `apps/chrome-extension/src/lib/` + `entrypoints/background/` (the 13-file solve-bug layer). Build fresh UI on top. **Do not copy Summarize's UI architecture** — the sidepanel/summary+slides+chat shape is the wrong product shape.
- **Visual container:** IN_PAGE_SECONDARY (Trinity-style DOM injection into YouTube's `#secondary`). `chrome.sidePanel` is REJECTED as a product container (Gate 1B empirical proof: it narrows the video viewport and leaves recommendations intact).
- **Runtime contract (Gate 2):** The `VideoContext` shape (videoId + url + title + duration + chapters + chapterSource + transcriptSource + contextVersion); the freshness invariant (`result.videoId === state.currentAuthoritativeVideoId`); the structured diagnostic emission (`{resultVideoId, activeVideoId, disposition, timestamp, sourceUrl, activeUrl, context}`).
- **No Gate 3 work** in this handoff. Gate 3 (YouTube Ask as opportunistic backend) is a separate spike after this vertical slice is evaluated as a product.
- **No receipt-identity-provenance investigation** in this handoff (deferred per operator directive 2026-08-10).

## Done criterion (operational definition)

The vertical slice is **DONE** when ALL of the following hold simultaneously, observed against the real loaded extension in the operator's Chrome:

- [ ] The extension loads unpacked in `chrome://extensions/` without errors.
- [ ] Navigating to a real YouTube watch page does NOT show the workspace until the toolbar button is clicked.
- [ ] Clicking the toolbar button mounts a workspace element inside YouTube's `#secondary`. No other layout shift occurs (video width unchanged).
- [ ] The Chapters tab renders rows from the VideoContext's `chapters[]`, with timestamp (clickable) + title.
- [ ] Clicking a chapter row causes the actual movie player to seek. Verified by reading `video.currentTime` before/after via MAIN-world eval.
- [ ] Navigating from video A to video B (real YouTube SPA navigation) triggers `yt-navigate-finish`. The workspace detaches/reattaches cleanly. No duplicate workspace elements. No leftover A content.
- [ ] Clicking the Back button (or history.back()) restores the prior video and re-acquires its chapters without duplicate mounts.
- [ ] On a video ≥60 min long (e.g., Stanford CS229, 104 min), the acquisition runs without truncation or timeout-induced failure.
- [ ] On a video with description-timestamp chapters but no `macroMarkersList` (e.g., Fareed Zakaria, 24:48), the regex fallback extracts the chapters and the Chapters tab renders them.
- [ ] On a video with creator-uploaded chapters (if found), `chapterSource: 'native'` and the chapters render.
- [ ] **Structured `rejected_stale` diagnostic fires** under a forced-timing scenario: start an A-acquisition, navigate to B before it completes, observe the late A-result rejected with the diagnostic record containing `resultVideoId: A, activeVideoId: B, disposition: "rejected_stale"`.
- [ ] **Negative control:** when no stale result is in flight, valid acquisitions produce `disposition: "accepted"`.
- [ ] Overview / Ask / Transcript / Links tabs appear as disabled placeholders (visible structure, non-functional).
- [ ] No permissions appear in the manifest that don't have a documented consumer (the `permission → calling module → runtime capability → acceptance test` chain holds for every permission).

**Critically:** the vertical slice is NOT done if any of the above is achieved only via `chrome.devtools` eval stand-in rather than through the actual extension boundary (content-script → background → MAIN-world-bridge). Gate 2's evidence is the ceiling for the runtime contract; this handoff proves the contract survives the extension boundary.

## Minimum permissions (with chain)

**Every permission must have a documented `permission → calling module → runtime capability → acceptance test` chain. Anything without a consumer is stripped.**

| Permission | Consumer (calling module) | Runtime capability | Acceptance test |
|---|---|---|---|
| `scripting` | `src/background/acquire.ts` (MAIN-world bridge), `src/content/workspace-injector.ts` (workspace mount) | `chrome.scripting.executeScript({ world: "MAIN", ... })` to read `ytInitialPlayerResponse` and inject the workspace | Forced-timing A→B diagnostic fires through the extension (not just devtools) |
| `activeTab` | `src/background/service-worker.ts` (`chrome.action.onClicked`) | Query the active tab to know whether to mount/refresh the workspace | Toolbar click on a YouTube tab mounts the workspace |
| `storage` | `src/background/service-worker.ts` | Persist workspace open/closed state across page reloads | Reload the YouTube page; workspace state survives |
| `host_permissions: ["*://*.youtube.com/*"]` | All of the above | Scoped to YouTube watch pages | Toolbar action is a no-op on non-YouTube tabs |

**Explicitly NOT requested** (Gate 1 rejected these as containers; this slice does not need them):

- `sidePanel` — REJECTED by Gate 1 (verdict IN_PAGE_SECONDARY). Do not include.
- `nativeMessaging` — no daemon in this slice.
- `userScripts` — no userscript need.
- `webRequest`, `webNavigation` — no intercept/observe need.
- `offscreen` — no offscreen document in this slice (Whisper fallback is deferred).
- `debugger` — no debugger use.
- `<all_urls>` — replaced with the narrower `*://*.youtube.com/*`. YouTube is the only surface.

If a permission's calling module is not implemented in this slice, that permission is stripped. If a future capability requires a new permission, it is added at that time with the same chain documented.

## Modules to extract (from `P:/tmp/summarize-audit`)

Per Gate 1's "Modules retained" subsection, extract only these (the solve-bug layer):

- `apps/chrome-extension/src/lib/youtube-page-transcript.ts` — MAIN-world bridge pattern. Extend (do not rewrite) to expose the chapter JSON path. **GATE 2 CORRECTION (2026-08-11):** chapters are NOT in `ytInitialPlayerResponse.macroMarkersListRenderer` — they are in `ytInitialData.engagementPanels[].engagementPanelSectionListRenderer.content.macroMarkersListRenderer.contents[].macroMarkersListItemRenderer`. The adapter must read from `ytInitialData`, not the player response. Description regex fallback remains as-is. See `P:/tmp/yt-workspace-gate2-evidence/G2-02-chapter-json-path.json` for the corrected path and verified chapter item shape.
- `apps/chrome-extension/src/lib/seek.ts` — dual-path seek helper.
- `apps/chrome-extension/src/entrypoints/background/panel-session-store.ts` — per-tab/per-URL cache invalidation pattern. Adapt to per-`videoId`.
- `apps/chrome-extension/src/entrypoints/background/extract-cache.ts` — cached extract.
- `apps/chrome-extension/src/entrypoints/background/panel-cache-runtime.ts` — panel cache.
- `apps/chrome-extension/src/entrypoints/background/panel-state.ts` — background UI-state resolver. Strip automation/hover/slides fields.
- `apps/chrome-extension/src/entrypoints/background/panel-message-router.ts` — message routing.
- `apps/chrome-extension/src/entrypoints/background/panel-runtime.ts` — background panel runtime. Strip slides/automation paths.
- `apps/chrome-extension/src/entrypoints/background/content-script-bridge.ts` — `seekInTab`, `extractFromTab`, MAIN-world bridge.
- `apps/chrome-extension/src/entrypoints/background/youtube-transcript.ts` — orchestrator wrapping the MAIN-world lib.
- `apps/chrome-extension/src/entrypoints/background/listeners.ts` — SPA navigation + tab events.
- `apps/chrome-extension/src/lib/settings.ts`, `apps/chrome-extension/src/lib/panel-contracts.ts` — settings + contract patterns (strip automation fields).
- `apps/chrome-extension/wxt.config.ts` — **REFERENCE ONLY**. Do not wholesale-inherit. Reconstruct the manifest with the minimum permissions above.

**MIT attribution** must appear in `LICENSE-THIRD-PARTY` or equivalent, citing:
- `steipete/summarize` — MIT — Copyright (c) 2026 Peter Steinberger

## Real test videos (for end-to-end acceptance)

From Gate 2's evidence, the two videos that worked in the operator's Chrome:

| videoId | Title | Duration | Chapters source | Captions | Use for |
|---|---|---|---|---|---|
| `Sx5-xt8tH_M` | Trump, China, Europe, AI & tariffs — Fareed Zakaria | 24:48 (1489s) | description-derived (4 rows via regex) | none | G2-03 description-regex test; G2-06 forced-timing test |
| `9vM4p9NN0Ts` | Stanford CS229 — Building Large Language Models | 104 min (6271s) | description-derived (22 rows via regex) | timedtext (en manual + en ASR) | Long-video test (≥60 min); caption acquisition test |

Several other popular videos (Apple WWDC 2024/2025, Tesla Battery Day, Vox) returned stub `ytInitialPlayerResponse` in the operator's Chrome (likely region/access restrictions). Do not depend on them. If a creator-chapter test is needed, search for a video with non-empty `macroMarkersList` during the spike and add it to the evidence directory.

## Task packets

### VS-01 — minimal WXT extension (manifest + skeleton)

- **goal:** Set up the new package at `P:/packages/yt-workspace/` with WXT, extract the 13 files from `P:/tmp/summarize-audit`, and emit a manifest with ONLY the minimum permissions (the chain table above). No Summarize UI copied.
- **in scope:** `package.json`, `wxt.config.ts` (reconstructed, NOT wholesale-inherited), `LICENSE-THIRD-PARTY` with MIT attribution, `tsconfig.json`, the 13 extracted files placed under `src/` (lib/ + entrypoints/background/), a placeholder `src/content/workspace-injector.ts` that mounts an empty `<div id="__yt_workspace">` in `#secondary` only when the toolbar action fires.
- **out of scope:** Real VideoContext logic, real chapter rendering, real seeking. Those are VS-02..04.
- **acceptance:** `pnpm install` succeeds; `pnpm -C packages/yt-workspace build` produces a valid MV3 manifest with ONLY `scripting`, `activeTab`, `storage`, `host_permissions: ["*://*.youtube.com/*"]`. Loading unpacked shows the toolbar action icon and clicking it on a non-YouTube tab is a no-op.
- **falsifier:** If `pnpm build` fails for WXT-version or type-incompatibility reasons, fall back to a hand-rolled MV3 manifest (still scoped to YouTube) and document why WXT was abandoned.
- **verification level required:** BUILD (manifest validates) + LOAD_UNPACKED (loads without errors).

### VS-02 — production VideoContext boundary

- **goal:** Implement the Gate 2 runtime contract as actual extension code, with the structured diagnostic firing through the real extension boundary (not just chrome-devtools eval).
- **in scope:**
  - `src/lib/video-context-store.ts` — state machine: `currentAuthoritativeVideoId`, `lastAccepted`, `applyResult(result)` → emit `{resultVideoId, activeVideoId, disposition, timestamp, sourceUrl, activeUrl, context}` diagnostic, dispatch to background.
  - `src/lib/structured-diagnostic.ts` — types + structured-log writer (durable: append to a `chrome.storage.local` key `diagnostics[]`, capped at N entries).
  - `src/background/acquire.ts` — orchestrates MAIN-world `ytInitialPlayerResponse` read + chapter extraction (macroMarkersList → shortDescription regex fallback) + VideoContext construction with all 4 provenance fields (`videoId`, `chapterSource: 'native'|'auto'|'desc'|'none'`, `transcriptSource: 'timedtext'|'innertube'|'whisper'|'none'`, `contextVersion`).
  - `src/background/service-worker.ts` — wires acquire to navigation events (`chrome.webNavigation.onHistoryStateUpdated` + `chrome.tabs.onUpdated`) and to the toolbar action.
- **out of scope:** UI (that's VS-03), seek (VS-04), Provider abstraction (deferred).
- **acceptance:** With the extension loaded unpacked and navigated to a real YouTube page:
  - The VideoContext is constructed and stored; reading `chrome.storage.local` shows `videoId`, `chapterSource`, `transcriptSource`, `contextVersion` populated.
  - Forcing a stale-acquisition scenario (programmatically trigger A-acquisition, then simulate nav to B) emits the structured `rejected_stale` diagnostic into `chrome.storage.local.diagnostics[]`.
  - Diagnostic shape matches Gate 2's spec: `{resultVideoId, activeVideoId, disposition: "rejected_stale" | "accepted", timestamp, sourceUrl, activeUrl, context}`.
- **falsifier:** If the extension-boundary path cannot reproduce Gate 2's G2-06 evidence, the vertical slice is incomplete. Diagnose whether the failure is in the bridge (MAIN-world eval), the message router, or the store, and fix the specific layer.
- **verification level required:** LOAD_UNPACKED + real YouTube + structured-diagnostic evidence in `chrome.storage.local`.

### VS-03 — real `#secondary` workspace with toolbar toggle

- **goal:** Build the user-visible workspace: toolbar click toggles it; Chapters tab renders; SPA navigation re-mounts cleanly; Overview/Ask/Transcript/Links appear as disabled placeholders.
- **in scope:**
  - `src/background/service-worker.ts` (extend) — `chrome.action.onClicked` toggles workspace state in `chrome.storage.session` and sends a message to the active YouTube tab's content script.
  - `src/content/workspace-injector.ts` (extend) — on toggle-on, inject the workspace into `#secondary`; on toggle-off, detach; on `yt-navigate-finish`, re-mount with the new videoId's VideoContext.
  - `src/content/workspace-ui.ts` — tabbed layout (Chapters | Overview | Ask | Transcript | Links). Chapters tab renders rows from the active VideoContext. Other tabs are disabled placeholders showing the tab name + "Coming soon" copy.
  - `src/content/workspace.css` — workspace styling. Dark theme matching YouTube's dark mode.
- **out of scope:** Real Overview/Ask/Transcript/Links logic (deferred). Real provider integration (Gate 3, deferred).
- **acceptance:**
  - Click toolbar on a YouTube watch page → workspace appears in `#secondary` (no other layout shift; video width unchanged per Gate 1B empirical proof).
  - Click toolbar again → workspace detaches cleanly.
  - Navigate A → B → workspace re-mounts with B's chapters and B's VideoContext.
  - Click Back → workspace re-mounts with A's chapters without duplicate mounts.
  - Workspace element count is exactly 1 across these transitions (verified via `document.querySelectorAll('#__yt_workspace').length`).
  - Overview/Ask/Transcript/Links tabs render as disabled placeholders.
- **falsifier:** If YouTube replaces `#secondary` in a way that strands the workspace (detaches without firing `yt-navigate-finish` AND no MutationObserver catches the replacement), the workspace must re-attach on a follow-up render or the spike fails.
- **verification level required:** LOAD_UNPACKED + real YouTube navigation flows + DOM count invariant.

### VS-04 — real chapter seeking through the extension boundary

- **goal:** Timestamp click in workspace → MAIN-world seek via the extension's actual bridge path. Verify the extension-boundary seek path works the same as Gate 2's chrome-devtools MAIN-world eval.
- **in scope:**
  - `src/content/seek-handler.ts` — on chapter-row click, compute seconds from the row's timestamp, send a message to background, background invokes `chrome.scripting.executeScript({ world: "MAIN", func: (s) => document.getElementById('movie_player')?.seekTo(s, true) ?? document.querySelector('video').currentTime = s })` in the active tab.
  - The seek-relay MUST go through the extension's bridge, not chrome.devtools eval. Verify by reading the background's `chrome.scripting.executeScript` invocations in the extension's log.
- **out of scope:** Chapter-row visual hover effects (deferred polish).
- **acceptance:** On a real YouTube video, clicking a chapter row in the workspace:
  - `video.currentTime` jumps to the row's seconds (before: 0, after: row.seconds). Read via MAIN-world eval as the verification mechanism.
  - The seek happens within 1 second of the click.
  - Both paths work: `movie_player.seekTo(s, true)` (YouTube's API) and `video.currentTime = s` (raw HTML5 video fallback).
- **falsifier:** If the extension's bridge cannot reproduce Gate 2's G2-04 evidence (60s and 300s seeks), diagnose whether the failure is in messaging (content-script → background), scripting API invocation, or the world:"MAIN" bridge itself.
- **verification level required:** LOAD_UNPACKED + real YouTube + before/after `video.currentTime` measurement.

### VS-05 — end-to-end acceptance test through the real extension

- **goal:** Run the full Done-criterion checklist (above) against the real loaded extension in the operator's Chrome, capturing evidence to `P:/tmp/yt-workspace-vertical-slice-evidence/`.
- **in scope:** One acceptance test per Done-criterion item. Each test produces a structured evidence file:
  - `load-unpacked.txt` — extension loads without errors
  - `toolbar-toggle-on.txt` — workspace mounts in `#secondary`
  - `chapters-rendered.txt` — Chapters tab content for both Fareed Zakaria + Stanford CS229
  - `seek-click-{ts}.txt` — before/after currentTime on chapter click
  - `spa-nav-a-to-b.txt` — workspace re-mount count, B's chapters rendered
  - `spa-back-a.txt` — workspace re-mount count, A's chapters restored
  - `long-video-stanford.txt` — Stanford CS229 acquisition (no truncation)
  - `description-regex-fareed.txt` — Fareed Zakaria chapter extraction (4 rows)
  - `forced-timing-rejected-stale.json` — the structured diagnostic from a forced A→B scenario
  - `negative-control-accepted.json` — the diagnostic from a no-stale valid acquisition
  - `permission-chain.md` — the documented `permission → calling module → runtime capability → acceptance test` for each permission
- **out of scope:** Performance benchmarks (latency, memory). Defer.
- **acceptance:** Every Done-criterion item is checked off with evidence file path. The permission-chain document confirms no permission lacks a consumer.
- **falsifier:** If any Done-criterion item fails, the vertical slice is NOT done regardless of how the other items pass. Fail-fast; do not paper over.
- **verification level required:** LOAD_UNPACKED + real YouTube + all Done-criterion items checked.

## Hard constraints

1. **Vertical slice, not scaffold.** Every implementation must be useful. Plumbing that doesn't deliver user value is a fail.
2. **Real YouTube evidence only.** No synthetic fixtures. No mocked `ytInitialPlayerResponse`. Every acceptance criterion runs against a real YouTube video in the operator's Chrome.
3. **The extension-boundary path is the verification surface.** Anything achieved only via `chrome.devtools` eval is NOT acceptable as a Done-criterion item. The runtime contract was proven via devtools in Gate 2; this slice proves it survives the real extension boundary.
4. **Minimum permissions, with chain.** Every permission has a `permission → calling module → runtime capability → acceptance test` chain. No permission without a consumer. Wholesale-inheriting `wxt.config.ts` from Summarize is FORBIDDEN.
5. **Gate 3 is OUT OF SCOPE.** Do not start YouTube Ask, Overview, Ask, Transcript, Links logic, or Whisper fallback in this slice.
6. **Receipt-identity-provenance investigation is OUT OF SCOPE.** Do not modify `verification_receipt.py` or any consuming hook.
7. **The five Gate 1 doc nits remain deferred.** Do not address them here.

## Cross-reference couplings

- **Gate 1 handoff** — EXTRACT + IN_PAGE_SECONDARY decisions and the 13-file extraction list.
- **Gate 2 handoff** — runtime contract (VideoContext shape, freshness invariant, structured diagnostic), real test videos, evidence directory pattern.
- **Research concept** — 3-gate sequence; this slice is the implementation phase between Gate 2 and Gate 3 (Gate 3 is still a separate spike after this).
- **Clone** — `P:/tmp/summarize-audit` (depth 1, last pushed 2026-08-05). Read-only source for extraction. Do not modify.
- **Receipt-identity-provenance handoff** — deferred reliability work, NOT this slice's concern.
- **Five Gate 1 doc nits** — `P:\.artifacts\noterm\grok-review\youtube-workspace-gate1\20260810-071405\findings.json` (DOC-001..DOC-005) — explicitly deferred, do not address here.

## Explicit non-goals

- Do NOT build Overview, Ask, Transcript, or Links tab logic (placeholders only).
- Do NOT implement Gate 3 (YouTube Ask as opportunistic backend) — separate spike.
- Do NOT implement Whisper captionless fallback — Gate 3+ work.
- Do NOT ship to Chrome Web Store — packaging is post-Gate-3.
- Do NOT wholesale-inherit Summarize's permissions. Reconstruct minimum permissions.
- Do NOT wholesale-inherit Summarize's UI architecture. Build a fresh tabbed workspace.
- Do NOT address the five Gate 1 doc nits.
- Do NOT investigate receipt-identity provenance.

## Resumption protocol

1. Read this handoff, the Gate 1 handoff, and the Gate 2 handoff (in that order). Confirm EXTRACT + IN_PAGE_SECONDARY are inherited; confirm the Gate 2 runtime contract is the target shape.
2. Set up the new package at `P:/packages/yt-workspace/` with WXT. Initialize git if not already initialized.
3. Extract the 13 files from `P:/tmp/summarize-audit` (see list above). Add the LICENSE-THIRD-PARTY attribution.
4. Reconstruct `wxt.config.ts` from first principles with ONLY the minimum permissions (chain table). Do not copy Summarize's.
5. Implement VS-01 → VS-02 → VS-03 → VS-04 → VS-05 in dependency order.
6. After VS-05 produces all evidence files, write the final Execution Status block (see `## Execution Status` template below).
7. Commit + push.
8. Do NOT proceed to Gate 3 without operator authorization.

## Suggested next invocation

- Run `/go` against this handoff in a **fresh session**. The fresh session will execute the 5 task packets as an implementation spike (NOT a runtime-evidence spike — this is real code, real MV3, real build).
- After VS-05 passes, evaluate the vertical slice as a product: install unpacked, use it for a day, decide whether YouTube Ask (Gate 3) is worth the fragility.
- Then Gate 3 spike (separate handoff, separate workstream).

## Last user message (verbatim, paraphrased)

> "Don't you have to update the handoff then with everything we need?"

Preceded by a detailed directive: build a vertical-slice extension (not a scaffold), with 5 specific deliverables (minimal WXT extension, production VideoContext boundary, real #secondary workspace, real chapter seeking, end-to-end acceptance test), strict permission discipline, "I could install this extension and already use it as a good Chapters extension" as the Done criterion, Gate 3 demoted to a separate spike after the vertical slice ships and is evaluated as a product.

## Epistemic labels per claim

- [FACT] The Gate 2 runtime contract (VideoContext shape, freshness invariant, structured diagnostic shape) was proven via chrome-devtools MAIN-world eval on real YouTube videos. Receipts: `P:/tmp/yt-gate2-evidence/videocontext-fareed-zakaria.json`, `P:/tmp/yt-gate2-evidence/videocontext-stanford-cs229.json`, `P:/tmp/yt-gate2-evidence/g2-06-freshness-diagnostic.json`.
- [FACT] Fareed Zakaria (`v=Sx5-xt8tH_M`, 24:48) and Stanford CS229 (`v=9vM4p9NN0Ts`, 104 min) are real accessible YouTube videos in the operator's Chrome. Receipts: same JSONs.
- [FACT] The 13-file extraction list is from Gate 1's "Modules retained" subsection. Receipt: `P:/docs/handoffs/youtube-workspace-extension-gate1-20260810/HANDOFF.md`.
- [FACT] `steipete/summarize` is MIT licensed. Receipt: `P:/tmp/summarize-audit/LICENSE`.
- [INFERENCE] The extension-boundary path (content-script → background → MAIN-world bridge via `chrome.scripting.executeScript`) will reproduce Gate 2's runtime contract. To be confirmed by VS-05.
- [INFERENCE] WXT (the source's build harness) is the appropriate harness for this slice. To be confirmed by VS-01.
- [UNKNOWN] Whether `chrome.devtools` eval evidence transfers 1:1 to the extension-boundary path. This is exactly what VS-02..VS-05 prove.

## Suggested skills for next session

- `/go` — execute the 5 task packets as an implementation spike.
- `/wiki` — after VS-05 passes, update the research concept with the vertical-slice outcome.
- `/handoff` — if Gate 3 (YouTube Ask) is authorized after evaluation, create a new handoff for it.

## Changelog

| Date | Session | Action |
|------|---------|--------|
| 2026-08-11T00:32:46 | 019fee39... | claimed by grok |
| 2026-08-10T08:05 | 019fea30... | created. Vertical-slice handoff (NOT Gate 3). Inherits Gate 1 EXTRACT + IN_PAGE_SECONDARY and Gate 2 runtime contract. 5 task packets (VS-01..VS-05). Operator-directed: vertical slice not scaffold; install-and-use as done criterion; permission discipline with chain; Gate 3 demoted to separate spike after evaluation. Ready for `/go` in a fresh session. |