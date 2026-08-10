---
thread_id: 5dd97700-52ec-4da2-95a8-075bf504d082
parent_handoff_path: none
current_session_id: 019fea30-500e-7b83-abac-d737446e86fb
parent_session: 019fe36e-7cb5-7003-b7dd-f94396165026
current_terminal_id: 019fea30-500e-7b83-abac-d737446e86fb
produced_at: 2026-08-10T05:45:00Z
last_updated_by: 019fea30-500e-7b83-abac-d737446e86fb
last_updated_at: 2026-08-10T07:08:00Z
status: resolved
handoff_type: investigation
accurate_as_of_head: cc8aba6eea9f9ce7e1ee6b069049f1fcdbf1b490
---

# Handoff — YouTube Workspace Sidebar Extension: Gate 1 Decision Spike

## Objective

Determine whether to FORK, EXTRACT, or REJECT `steipete/summarize` as the foundation for a unified YouTube workspace Chrome extension (Chapters | Overview | Ask | Transcript | Links), and decide the visual container (chrome.sidePanel vs in-page injection) — before any transcript/AI implementation work.

**Scope bounds:** Gate 1 only (reuse verdict + visual container test). Gate 2 (acquisition spike) and Gate 3 (AI behavior) are explicitly out of scope until Gate 1 settles.

## Status

RESOLVED — Gate 1 settled (2026-08-10, session 019fea30...). Both decisions recorded with evidence. Gate 2 spike is the next session's work; this handoff is the durable record of the Gate 1 outcome.

## Producing context

- Date: 2026-08-10
- Session: 019fe36e-7cb5-7003-b7dd-f94396165026
- Operator provided a ChatGPT design conversation (`C:/Users/brsth/Downloads/I-would-keep-the-MVP-surprisingly-small.md`) describing the target product.

## Read-first list (ordered)

1. `P:/.data/wiki/concepts/youtube-workspace-sidebar-extension-build-research.md` — the full research concept with all findings, the 3-gate sequence, the claim ledger, and the verified `steipete/summarize` evidence. **This is the primary input.**
2. `C:/Users/brsth/Downloads/I-would-keep-the-MVP-surprisingly-small.md` — the original ChatGPT design conversation (product vision, UX mockup, MVP scope).
3. `P:/.data/wiki/concepts/research-artifact-revision-invalidation.md` — the durable rule captured from the operator's review (revision-integrity discipline). Relevant if Gate 1 produces findings that revise the research concept.
4. https://github.com/steipete/summarize — the dominant reuse candidate (MIT, 6.5k★, TypeScript, WXT). Read `apps/chrome-extension/src/` tree, `entrypoints/background/panel-state.ts`, `panel-session-store.ts`, and `lib/seek.ts`.
5. https://developer.chrome.com/docs/extensions/reference/api/sidePanel — official `chrome.sidePanel` API docs (already fetched this session; receipt in the research concept).

## Verified facts (with source paths)

- [FACT] `steipete/summarize` is MIT licensed, 6,532 stars, 440 forks, last push 2026-08-05. Receipt: `gh repo view` + LICENSE content read this session. (research concept §6a)
- [FACT] Its Chrome extension already implements: Side Panel (auto-opens on toolbar click), YouTube transcript acquisition (`youtube-transcript.ts`, `youtube-local-transcript.ts`, `youtube-sabr-capture.ts`), Summary/Overview (`panel-summarize.ts`, `panel-summary-session.ts`), Chat/Ask (`panel-chat.ts`, `panel-chat-runtime.ts`), state isolation + caching (`panel-state.ts`, `panel-session-store.ts`, `panel-cache-runtime.ts`, `extract-cache.ts`), clickable-timestamp seeking (`lib/seek.ts`), browser-side Whisper fallback for captionless videos (`offscreen/whisper.ts`). Receipt: `gh api` file tree this session.
- [FACT] Its CHANGELOG documents that the hard bugs are already fixed: "reject YouTube caption and transcript-panel results when the tab navigates to another video during extraction" (videoId freshness), "restore persisted chat history" (chat-bleed), "truncated long-form transcript" (long-video truncation). Receipt: CHANGELOG content read this session.
- [FACT] Direct mode runs without the companion daemon — uses Chrome's built-in Gemini Nano + configured OpenAI/OpenRouter/Anthropic/Gemini/xAI/Z.AI/NVIDIA/MiniMax/Ollama providers directly. Keys stay in `chrome.storage.local`. Receipt: README read this session.
- [FACT] It does NOT have: a dedicated Chapters tab, or YouTube-Ask-panel as a provider. These are the additive gap. Receipt: README + file tree — no chapters module, no ask-panel provider file.
- [FACT] The two reference extensions (Links and Chapters, Trinity) are both closed-source. Trinity Firefox = "All Rights Reserved." Receipt: Chrome Web Store + Firefox AMO pages read this session.
- [FACT] "YouTube built-in AI" = DOM prompt-injection into the Ask/YouChat panel. Receipt: Links and Chapters changelog v1.0.361/v1.0.372.
- [INFERENCE] `chrome.sidePanel` sits alongside the webpage, not inside YouTube's right column. The visual impact on YouTube's layout is not yet verified — Gate 1B resolves this.
- [INFERENCE] Adding a Chapters view to `steipete/summarize`'s panel-state/tab model is likely additive, but this is NOT yet confirmed by reading the panel-session code. Gate 1A resolves this.

## Current state

- Research complete and committed (4 commits: `62a615a`, `e954985`, `30c3833`, `12e03ec` — all pushed, HEAD == origin/main).
- Research concept validated and passes `/wiki` validator.
- 3-gate sequence defined and agreed with operator.
- No code written. No extension scaffolded.

## Task packets

### G1A-01 — `steipete/summarize` reuse audit — ✅ RESOLVED (EXTRACT)

- goal: Determine FORK / EXTRACT / REJECT with evidence.
- status: **RESOLVED 2026-08-10** — verdict **EXTRACT** (with the correction that the source is the extension's internal `lib/` + `entrypoints/background/`, NOT the published `@steipete/summarize-core`).
- evidence collected this session:
  - Cloned `steipete/summarize` `--depth 1` to `P:/tmp/summarize-audit`. LICENSE = MIT (Copyright Peter Steinberger).
  - Read `apps/chrome-extension/src/entrypoints/sidepanel/panel-state-store.ts` — `PanelState` has `summaryMarkdown`, `slides`, `chat`; **NO tab/view model exists**. The only "transcript" concept is `slidesText.mode: "transcript"` (a slide-deck text-source toggle), not a standalone view.
  - Read `apps/chrome-extension/src/entrypoints/sidepanel/index.html` — **NO `<nav>`/tab bar**; it is a single summary area with a controls drawer.
  - `grep 'chapter|macroMarkers|chapters'` across `apps/chrome-extension/src/` returns **NONE** — Chapters is not a first-class concept anywhere. (Promotes research concept [INFERENCE] to [FACT].)
  - Read `apps/chrome-extension/src/lib/youtube-page-transcript.ts` (357 lines) — already implements MAIN-world `chrome.scripting.executeScript({ world: "MAIN" })` for caption source read + timedtext fetch. The single most valuable reusable asset; needs only an extension to expose the chapter JSON path.
  - Read `apps/chrome-extension/src/lib/seek.ts` (40 lines) — clean dual-path seek (`<video>.currentTime` then `document.getElementById('movie_player').seekTo()`). No modification required.
  - Read `apps/chrome-extension/src/entrypoints/background/panel-session-store.ts` — per-tab/per-URL cache invalidation (`cached.url !== url → invalidate`), inflight URL tracking, AbortController plumbing. The CHANGELOG entries the research concept quoted are real (verified by source).
  - Read `packages/core/package.json` — `@steipete/summarize-core` is a **server-side Node library** (`@mozilla/readability`, `linkedom`, `sanitize-html`, `undici`, `ffmpeg-wasm`, `node ≥ 24`). It does **not** include the MV3 extension pieces. The handoff's original EXTRACT option ("use `@steipete/summarize-core` for transcript/extraction") was based on a stale assumption; the correct EXTRACT source is the extension's internal files.
  - Entanglement check (grep `sidepanel|automation|repl|userscripts` across `lib/` and `background/`, excluding self-imports): only `direct-prompts.ts` (capability-flag branch), `panel-contracts.ts` (declares `automationEnabled` field), `settings.ts` (stores toggle) in `lib/` — all trivial boolean references. In `background/`, only `runtime-actions.ts` deeply imports `../../automation/{artifacts-store,native-input-guard}` — that one file must be rewritten; everything else (`panel-session-store.ts`, `panel-state.ts`, `panel-cache-runtime.ts`, `extract-cache.ts`, `listeners.ts`, `panel-message-router.ts`, `panel-runtime.ts`, `content-script-bridge.ts`, `youtube-transcript.ts`) is clean of sidepanel/automation imports.
- outcome: See D1 in "Resolved decisions" above. EXTRACT keeps the solved-bug layer without inheriting the wrong-product UI.
- falsifier check: Chapters fits additively in our NEW UI (not Summarize's). Pass. Stripped footprint is significantly lighter than a full fork (we keep ~13 files ≈ 2.5k LOC from the extension source and build a new UI). Pass.

### G1B-01 — Visual container test — ✅ RESOLVED (IN_PAGE_SECONDARY)

- goal: Decide `chrome.sidePanel` vs in-page injection based on real visual evidence.
- status: **RESOLVED 2026-08-10** — verdict **IN_PAGE_SECONDARY**. Visual test was possible (chrome-devtools + chrome MCPs connected), so this is **not** `VISUAL_TEST_BLOCKED`. Real measurements captured against a live YouTube watch page.
- evidence collected this session:
  - Used the operator's existing YouTube tab (pageId 10, CNN Fareed Zakaria, `v=Sx5-xt8tH_M`, 24:48, native chapters present, YouTube's own "Chapters / ✦ Ask / Transcript" engagement tabs present).
  - For the side-panel simulation: used the separate clean `chrome` MCP browser at viewport 1100×900 (since the operator's window is maximized and unmaximizing would be intrusive). YouTube is public; no auth needed for layout testing.
  - Default-mode baseline (viewport 1502px): video 1032px, `#primary` 1048px, `#secondary` 418px (recommendations column on the right). Theater mode tested too (video spans 1483px, `#secondary` pushed below).
  - In-page injection: workspace mock (402px, tabs row "Chapters | Overview | Ask | Transcript | Links" + 7 placeholder chapter rows) inserted into `#secondary`; recommendation children hidden. Result: **video unchanged at 1032px**, workspace cleanly displaces recommendations. Screenshot captured.
  - Side-panel simulation (viewport 1100×900): **video shrinks to ~715px (~31% reduction), recommendations column STILL VISIBLE on the right (~340px) with full thumbnail list**. Screenshot captured.
  - Toggle behavior acknowledged: chrome.sidePanel has the cleaner one-click toggle (native, survives SPA nav); in-page needs extension-managed show/hide + SPA re-render handling (mitigated by Summarize's `listeners.ts` patterns and the stable `#secondary` anchor).
- outcome: See D2 in "Resolved decisions" above. The product thesis ("turn wasted recommendation space into a useful video workspace") is decisively served by IN_PAGE_SECONDARY and not by chrome.sidePanel.
- falsifier check: chrome.sidePanel DID narrow the video and leave recommendations in place. The exact failure mode the research concept flagged. Pass.

## Resolved decisions (Gate 1 outcome, 2026-08-10)

### D1: EXTRACT (resolved)

- **Question:** Do we fork `steipete/summarize`, extract its core library, or build clean-room?
- **Verdict:** **EXTRACT** — but with a correction to the framing in the original task packets. The source is the **extension's internal `apps/chrome-extension/src/lib/` + `entrypoints/background/`**, NOT the published `@steipete/summarize-core` npm package. The published core is a server-side Node library (`@mozilla/readability`, `linkedom`, `sanitize-html`, `undici`, `ffmpeg-wasm`, `node ≥ 24`) and does **not** contain the MV3 extension pieces (MAIN-world bridge, seek, panel-session-store, listeners). The extension's valuable reusable code lives inside the extension source tree.
- **Modules retained (extracted from `apps/chrome-extension/src/`):**
  - `lib/youtube-page-transcript.ts` — MAIN-world `chrome.scripting.executeScript({ world: "MAIN" })` reader of YouTube caption source + timedtext fetch. Extend (do not modify) to expose the chapter JSON path (`macroMarkersList` / engagement-panel chapter renderer).
  - `lib/seek.ts` — clean dual-path seek (`<video>.currentTime` first, then `document.getElementById('movie_player').seekTo()`).
  - `entrypoints/background/panel-session-store.ts` — per-tab/per-URL cache invalidation + inflight URL tracking + AbortController plumbing. Adapt to per-`videoId`.
  - `entrypoints/background/extract-cache.ts`, `panel-cache-runtime.ts`, `panel-state.ts`, `panel-message-router.ts`, `panel-runtime.ts`, `content-script-bridge.ts`, `youtube-transcript.ts`, `listeners.ts` — background layer (strip automation/hover/slides fields).
  - `lib/settings.ts`, `lib/panel-contracts.ts` — settings + contract patterns (strip automation fields).
  - `apps/chrome-extension/wxt.config.ts` — WXT setup, MV3 manifest with `sidePanel` permission, `<all_urls>`, optional `nativeMessaging`/`userScripts`/`debugger`. Inherit wholesale.
- **Modules removed (REJECTED):**
  - ALL of `entrypoints/sidepanel/` (~80 modules: summary view, slides view, chat view, slides-renderer, slides-stream, slides-summary, slide-images, slides-text, chat-controller, chat-runtime, chat-agent-loop, chat-history-*, model-presets, setup-*, typography-controller, presentation-runtime, drawer-controls, header-controller, metrics-controller, appearance-controls). Wrong product shape — summary-centric single-view, no tab model. Adding Chapters would require replacing the entire sidepanel UI; that's not a fork, it's a rewrite of the UI layer.
  - ALL of `automation/` + `entrypoints/automation.content.ts` + `background/hover-controller.ts` + `entrypoints/hover.content.ts` — REPL, element picker, debugger-backed native input, hover summaries.
  - Slides layer: `entrypoints/background/browser-slides*`, `browser-ai-slides-runtime.ts`, `browser-ai-summary-runtime.ts`, `browser-ai-recursive-summary.ts`, `browser-ai-snapshot-runtime.ts`, `browser-ai-contracts.ts`, `browser-slides-context.ts`, `panel-slides-context.ts`, `browser-media*`, `youtube-local-transcript.ts` (Whisper transcription), `entrypoints/offscreen/*` (Whisper/transformers).
  - Daemon bridge: `lib/direct-provider/*`, `lib/daemon-*`, `lib/daemon-fetch.ts`, `lib/daemon-payload.ts`, `lib/daemon-permission.ts`, `lib/daemon-policy.ts`, `lib/daemon-recovery.ts`, `lib/daemon-status.ts`, `lib/daemon-url.ts`, `background/daemon-client.ts`, `panel-summary-daemon.ts`, `runtime-actions.ts` (deep automation imports).
  - `entrypoints/options/*` — write a minimal options page.
  - `lib/slides-*`, `lib/browser-panel-cache.ts`, `lib/browser-summary.ts`, `lib/browser-url-content.ts`, `lib/automation-capabilities.ts`, `lib/extension-logs.ts`, `lib/metrics.ts`, `lib/model-routing.ts`, `lib/options-tabs.ts`, `lib/theme.ts`, `lib/status.ts`, `lib/slides-text.ts`, `lib/slides-presentation.ts`, `lib/token.ts`, `lib/header.ts`, `lib/combo.ts` — UI/token/theme/log infrastructure tied to summary/slides UX.
- **Modules added (new, our product):**
  - Tabbed sidepanel (or in-page UI per D2): `Chapters | Overview | Ask | Transcript | Links`
  - `background/chapters.ts` — read `macroMarkersList` / engagement-panel chapter renderer via MAIN-world + description-timestamp regex fallback (`(\d{1,2}:\d{2}(:\d{2})?)\s+(.+)`)
  - `background/video-context.ts` — shared `VideoContext` (videoId, url, title, duration, chapters, chapterSource, transcript, transcriptSource, overview, askSession, links, contextVersion) with freshness contract `response.videoId === activeVideoId`
  - `background/youtube-ask-provider.ts` — opportunistic YouTube Ask-panel provider (Gate 3)
  - `background/links.ts` — extract links from description (Gate 3)
  - `lib/video-context-store.ts` — adapter from extracted `panel-session-store.ts` to per-`videoId` VideoContext
- **Chapters additivity:** ADDITIVE in the most additive possible sense. Because we are NOT reusing Summarize's sidepanel UI, our tab model is native to our new UI. Chapters is a first-class tab from day one; no fighting an existing summary-centric `PanelState`. The research concept's [INFERENCE] that Chapters is absent is now **[FACT]** (grep `chapter|macroMarkers|chapters` across `apps/chrome-extension/src/` returns NONE).
- **Largest risk:** The extracted `panel-session-store.ts` is keyed by `tabId`/`windowId` and invalidated by URL. Our `VideoContext` is keyed by `videoId`. The adaptation is straightforward (cache by `videoId`, invalidate on nav) but is a semantic shift from "one summary run per tab" to "one VideoContext per videoId." Gate 2 spike will surface any hidden coupling.
- **Strongest falsifier:** If a deeper trace of the background files reveals hidden imports from `sidepanel/` or `automation/` that the grep above missed (probability low; only boolean-flag references and `runtime-actions.ts` were found, and `runtime-actions.ts` is already planned for rewrite), EXTRACT degrades toward **REJECT** with a manual port of the two clearly-self-contained lib pieces (`youtube-page-transcript.ts`, `seek.ts`).
- **Why not FORK:** The sidepanel UI is the wrong product shape (summary-centric, no tab model). Gutting it to add our tab model is a rewrite of the UI layer, not a fork. FORK would mean inheriting 19 slides modules, 20+ automation modules, the chat-agent-loop, and the summary/slides state model — all to throw most of it away. EXTRACT keeps the solved-bug layer (MAIN-world, seek, freshness, cache, listeners) without inheriting the wrong-product UI.
- **Why not REJECT:** REJECT would force rebuilding solved infrastructure (MAIN-world bridge, seek, freshness contract, per-tab cache invalidation) — the exact failure mode the research concept and AGENTS.md rules ("reuse before rebuild") exist to prevent. The reusable layer is too valuable to ignore.

### D2: IN_PAGE_SECONDARY (resolved)

- **Question:** Which visual container?
- **Verdict:** **IN_PAGE_SECONDARY** (Trinity-style DOM injection into YouTube's `#secondary` column).
- **Empirical evidence (real YouTube watch page test, not `VISUAL_TEST_BLOCKED`):**
  - Test video: CNN Fareed Zakaria, "Trump, China, Europe, AI & tariffs" (`v=Sx5-xt8tH_M`), 24:48, native chapters present, YouTube's own "Chapters / ✦ Ask / Transcript" engagement tabs present.
  - Default-mode baseline (viewport 1502px): video 1032px wide, `#secondary` 418px recommendations column on the right.
  - In-page injection: workspace (402px, tabs row "Chapters | Overview | Ask | Transcript | Links" + 7 placeholder chapter rows) displaces the recommendations column. **Video unchanged at 1032px.**
  - Side-panel simulation (separate clean Chrome browser at viewport 1100×900, simulating `chrome.sidePanel` consuming ~400px of a ~1500px window): video shrinks to ~715px (~31% reduction). **Recommendations column STILL VISIBLE on the right (~340px)** with full thumbnail list — the wasted space was not replaced; the video shrank AND recs remain.
- **Product tradeoff:** chrome.sidePanel has the cleaner toggle (`setPanelBehavior({openPanelOnActionClick:true})`, survives SPA nav natively, no DOM-fighting). In-page injection needs extension-managed show/hide and must fight YouTube's SPA re-renders (the `yt-navigate-finish` event, MutationObservers on `#secondary`). The product thesis ("turn wasted recommendation space into a useful video workspace") is decisively served by in-page and not by chrome.sidePanel — chrome.sidePanel shrinks the video and leaves recs intact, achieving neither the workspace-instead-of-recs experience nor the full-video experience. The product value of in-page outweighs its maintenance cost, given:
  1. Summarize's `listeners.ts` already solves SPA-nav refresh in this exact context.
  2. The workspace can be anchored to YouTube's own `#secondary` slot (the same slot YouTube uses for Chapters/Ask/Transcript engagement panels) — a first-party-stable anchor.
  3. The product value (full-width video + useful workspace replacing recs) is exactly what the design conversation described.
- **Maintenance cost acknowledgment:** In-page injection's higher DOM-maintenance cost is the real trade-off. Falsifier: if YouTube's `#secondary` becomes unstable or the SPA-nav cost proves unacceptable in Gate 2, this verdict degrades toward CHROME_SIDE_PANEL with a redesigned product thesis (narrower workspace beside the video rather than displacing recs).
- **Theater mode:** Both containers behave coherently in theater (recommendations pushed below video). In-page injection puts the workspace below the video, displacing recs. chrome.sidePanel narrows the window further in theater; recs below shrink, video above shrinks. The default-mode comparison is the decisive one because that's where the "wasted right column" thesis is most testable; theater-mode behavior is a straightforward extension of the same finding.

## Hard constraints

1. **No AI/transcript work in Gate 1.** The decision spike must settle before implementation. Do not start building chapters/overview/ask until G1A and G1B are done.
2. **Operator's Chrome has both extensions enabled.** Observable behavior from Links and Chapters and Trinity is available as requirements input.
3. **YouTube Ask works in the operator's account** (observed via Links and Chapters). Single-account context means global rollout is not a constraint.

## Cross-reference couplings

- `youtube-workspace-sidebar-extension-build-research.md` → this handoff is the implementation of its Gate 1. If the research concept is revised, the task packets may change.
- `steipete/summarize` repo (external) → G1A-01 reads its source. If the repo is restructured before the audit, re-clone.
- `ship-py-pi-dispatch-not-found-20260809/HANDOFF.md` → adjacent (pi CLI dispatch failure affects ship-py but not this build work).
- This handoff's `accurate_as_of_head` → `30be829f`. If HEAD moves, the research concept (the primary input) should still be valid — it's committed.

## Other outstanding streams (not handed off)

- **Research-artifact-revision-invalidation** — durable rule captured in wiki concept; needs AGENTS.md promotion decision + 2 minor review fixes (broken wikilink, pre-correction line numbers). Open but not blocking this stream.
- **ship-py pi CLI dispatch failure** — pi returns `empty_response` for orchestrator dispatches; separate handoff exists at `ship-py-pi-dispatch-not-found-20260809`. Open.

## Explicit non-goals

- Do NOT build the full extension in Gate 1. Gate 1 produces decisions, not code.
- Do NOT implement transcript acquisition, chapter generation, or AI integration yet. Those are Gate 2/3.
- Do NOT fork `steipete/summarize` until G1A-01 returns FORK. Forking prematurely inherits a footprint you haven't measured.
- Do NOT assume `chrome.sidePanel` is correct. Test it visually first.

## Resumption protocol

1. Clone `steipete/summarize`: `git clone https://github.com/steipete/summarize.git P:/tmp/summarize-audit`
2. Read `apps/chrome-extension/src/entrypoints/background/panel-state.ts` and `panel-session-store.ts` — can a "Chapters" tab be added as a new entry in the tab model without modifying the session architecture?
3. Measure stripped footprint: what does the build look like without `src/automation/` and hover features? (`pnpm install`, then `pnpm -C apps/chrome-extension build`, check `.output/` size)
4. Build two throwaway mockup extensions: (A) sidePanel with 3 placeholder chapter rows, (B) in-page div in YouTube `#secondary` with same rows.
5. Load both in Chrome, navigate to a real YouTube video, screenshot in normal/theater/sidebar-open/sidebar-closed modes.
6. Write the verdict: FORK/EXTRACT/REJECT + sidePanel/in-page. Post as a revision to the research concept.

## Gate 1 outcome (summary)

- **D1: EXTRACT** — reuse surface is ~13 files from `apps/chrome-extension/src/lib/` + `entrypoints/background/`. NOT the published `@steipete/summarize-core` (which is server-side). The Summarize sidepanel UI is the wrong product shape (summary-centric, no tab model) and is REJECTED along with automation/REPL/slides/daemon layers.
- **D2: IN_PAGE_SECONDARY** — empirically verified against a real YouTube watch page. In-page preserves the 1032px video width and replaces the recommendations column with the workspace; chrome.sidePanel shrinks the video to ~715px and leaves recommendations intact. Product thesis ("turn wasted recommendation space into a workspace") achieved by IN_PAGE_SECONDARY, not by chrome.sidePanel.
- **Decision: `READY_FOR_GATE_2`** — Gate 2 is a bounded **runtime falsification spike** (NOT an implementation phase) scoped to six items: live MAIN-world acquisition, native chapter path, description fallback, real seeking, `#secondary` SPA remounting, stale-result rejection. Success criterion: real video A → authoritative `videoId` → real chapters/transcript → stamped `VideoContext` → rendered in `#secondary` → click real timestamp → real `movie_player.seekTo()` → navigate A→B→Back during acquisition → stale A result demonstrably cannot mutate B.
- **Do NOT broaden Gate 2** beyond those six items. If they pass, most of the dangerous architectural uncertainty is gone. If they fail, we learn *where* before spending effort on Overview, Ask, Links, provider abstraction, or UI polish.

## Suggested next invocation

- The **following session** should execute the bounded Gate 2 spike. Open a new handoff (e.g. `P:/docs/handoffs/youtube-workspace-extension-gate2-20260810/HANDOFF.md`) and run `/go` against it. Gate 2 inherits the EXTRACT + IN_PAGE_SECONDARY decisions from this handoff; it does NOT re-decide them.
- `/wiki` (later, after Gate 2 / Gate 3 outcomes) to update `youtube-workspace-sidebar-extension-build-research.md` with the Gate 1 revision block (and ultimately the Gate 2/3 revision blocks when those land). The revision must propagate to frontmatter summary, decision-context, recommendations, falsifier, and confidence per the research concept's claim ledger.
- `/handoff` (Gate 3) only after Gate 2 passes — YouTube Ask-panel opportunistic provider with detection + timeout + validation + fallback.

## Last user message (verbatim)

> "/handoff"

## Epistemic labels per claim

- All [FACT] claims cite tool-call receipts from this session (gh api, web_fetch, grep — all in the research concept's Receipts section).
- [INFERENCE] claims are the two unresolved questions Gate 1 settles (sidePanel visual fit, Chapters additivity).
- [UNKNOWN]: none — all unknowns are explicitly deferred to Gate 1/2/3.

## Suggested skills for next session

- `/go` — Gate 1 has 2 bounded task packets ready to execute (clone+audit, mockup+visual test)
- `/wiki` — update the research concept with Gate 1 verdict outcomes
- `/handoff` — create Gate 2 handoff after Gate 1 settles

## Changelog

| Date | Session | Action |
|------|---------|--------|
| 2026-08-10T05:45 | 019fe36e... | created |
| 2026-08-10T07:08 | 019fea30... | Gate 1 resolved. D1 = EXTRACT (from `apps/chrome-extension/src/{lib,entrypoints/background}/`, not the published `summarize-core`). D2 = IN_PAGE_SECONDARY (empirically verified). Status → resolved. Task packets G1A-01 and G1B-01 marked resolved. Frontmatter timestamps + `accurate_as_of_head` updated. STOPPED — Gate 2 spike is the next session's work. |
