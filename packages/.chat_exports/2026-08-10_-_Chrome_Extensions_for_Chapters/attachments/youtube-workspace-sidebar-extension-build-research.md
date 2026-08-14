---
title: "YouTube Workspace Sidebar Extension — Build Research"
created: 2026-08-08
source: www-research
tags: [www-synced, reference, youtube, chrome-extension, build-decision]
summary: >
  Research for building a unified YouTube workspace Chrome extension (persistent
  tabbed sidebar: Chapters | Overview | Ask | Transcript | Links). Covers the two
  reference extensions (Links and Chapters, Trinity — both closed-source), the
  "YouTube built-in AI" chapter-generation mechanism (DOM prompt-injection into
  the Ask/YouChat panel — real but fragile), in-browser transcript acquisition
  (ytInitialPlayerResponse.captions + Innertube/timedtext + PO-token), native
  chapter reading, the chrome.sidePanel API as the recommended sidebar
  architecture, open-source clean-room references (QuickSummarize GPL v3,
  keyFrame), and the competitor landscape. Headline finding: the "no-LLM-needed"
  premise is only partially true; both open-source maintainers abandoned YouTube's
  built-in AI in favor of external LLMs, so the MVP should treat Ask-panel
  injection as a bonus, not the primary path.
agent: grok
host: both
cognitive_load: 3
verification: multi-source-verified
sources:
  - "YouTube Links and Chapters — Chrome Web Store (eannnkmhjifbnpibcbmjbkenlhmddbnk)" (https://chromewebstore.google.com/detail/youtube-links-and-chapter/eannnkmhjifbnpibcbmjbkenlhmddbnk)
  - "YouTube Trinity — Chrome Web Store (bhlbodgbbcaecfncjennphkambbkakej)" (https://chromewebstore.google.com/detail/youtube-trinity/bhlbodgbbcaecfncjennphkambbkakej)
  - "YouTube Trinity — Firefox Add-ons (All Rights Reserved)" (https://addons.mozilla.org/en-CA/firefox/addon/youtube-trinity/)
  - "EchoTide/QuickSummarize — GPL v3 open-source Chrome side-panel extension" (https://github.com/EchoTide/QuickSummarize)
  - "parathaprat/keyFrame — yt sidebar summary + chapter generator (native messaging host)" (https://github.com/parathaprat/keyFrame)
  - "Harsh-Pachauri/YouTube-Transcript-Summarizer-Extension" (https://github.com/Harsh-Pachauri/YouTube-Transcript-Summarizer-Extension)
  - "chrome.sidePanel API — Chrome for Developers (official docs)" (https://developer.chrome.com/docs/extensions/reference/api/sidePanel)
  - "YouTube timedtext endpoint + PO-token" (https://grokipedia.com/page/YouTube_timedtext_endpoint)
  - "8 Best YouTube Summary Chrome Extensions (2026 Review)" (https://www.notelm.ai/blog/youtube-summary-chrome-extension)
  - "Ask YouTube brings AI-powered conversational search (Gemini, I/O 2026)" (https://www.techbuzz.ai/articles/ask-youtube-brings-ai-powered-conversational-search-to-video-adds-gemini-omni-to-shorts)
relations:
  - target: wiki/concepts/youtube-transcript-extraction-techniques.md
    type: extends
  - target: wiki/concepts/video-to-wiki-pipeline-transcript-extraction-multimodal.md
    type: related
  - target: wiki/concepts/chrome-acp-library-stack-and-best-practices-2026.md
    type: related
  - target: wiki/concepts/youtube-throttling-returns-429-not-silent-200.md
    type: related
---

# YouTube Workspace Sidebar Extension — Build Research

## Decision context

**The real question behind this research:** the operator has a ChatGPT design conversation (saved at `C:/Users/brsth/Downloads/I-would-keep-the-MVP-surprisingly-small.md`) describing a unified YouTube workspace Chrome extension — one toolbar button toggling a **persistent right-side tabbed sidebar** (Chapters | Overview | Ask | Transcript | Links | Videos). The conversation references two installed extensions (Links and Chapters, Trinity) and hinges on one **blocking claim**: that "YouTube's built-in AI" can generate chapters/summaries with *no local model and no API key*. The operator wants to implement this. This research was needed to (a) verify that blocking claim, (b) find the extensions' source/licenses, (c) ground the transcript/chapter acquisition + sidebar architecture in primary sources, and (d) surface open-source clean-room references.

**What the research changed:** the blocking claim is *partially true* but materially more fragile than the conversation assumed — and *both* open-source maintainers who faced the same choice abandoned YouTube's built-in AI for external LLMs. This reshapes the MVP's risk model (see Headline finding).

## Workspace observations (Phase 1a)

1. The workspace already does heavy YouTube transcript extraction **server-side** (yt-is package, `[[video-to-wiki-pipeline-transcript-extraction-multimodal]]`, `[[youtube-transcript-extraction-techniques]]`) via Python/yt-dlp/youtube-transcript-api/NotebookLM. This research is the **in-browser/extension** complement — a context the existing wiki covers weakly.
2. `[[youtube-throttling-returns-429-not-silent-200]]` documents that YouTube throttling surfaces as HTTP 429, not silent 200s — relevant to transcript-acquisition robustness in any client, including an extension running in the user's own browser session.
3. The operator has Chrome with both extensions already enabled and runs extensive CDP/browser automation (`[[chrome-autoconnect-for-authenticated-cdp-sessions]]`, `[[parallel-cdp-mcp-servers-openchrome]]`). The host invariant in `[[concurrent-cdp-auth-contention]]` is about fleet CDP contention — it does **not** constrain a single user-facing extension, but it is why the workspace is fluent in this domain.

## Research threads (Phase 1)

- Extends `[[youtube-transcript-extraction-techniques]]` into the browser/extension context (server-side → client-side).
- Connects to `[[chrome-acp-library-stack-and-best-practices-2026]]` for MV3 build-stack guidance (WXT/CRXJS+Vite preferred over Bun).
- No prior `/www` run on the specific "YouTube chapters/summary sidebar extension" — fresh domain.

---

## 1. The reference extensions — both closed-source

### Links and Chapters (`eannnkmhjifbnpibcbmjbkenlhmddbnk`)
- **Closed-source.** No public repo, no license. Developer "monehsieh" (chrome-dev@monemone.org). Last update **June 2026**, v1.0.377, ~31 KB.
- **Architecture (from its own store changelog):** popup-based; reads native chapters from DOM; for missing chapters "uses YouTube's 'Ask' panel when available; falls back to clipboard/API mode"; TL;DR uses "YouTube's built-in AI (YouChat)"; ships a settings page for API endpoint + model + prompt (OpenAI-compatible, e.g. Ollama/vLLM). Persists generated results.
- **No usable reviews** (effectively unrated on the store). [Source: Chrome Web Store page.]

### Trinity (`bhlbodgbbcaecfncjennphkambbkakej`)
- **Closed-source.** No public repo. Chrome license = default store EULA; **Firefox explicitly "All Rights Reserved."** Developer tjf5166@gmail.com. Last update **May 2026**.
- DOM-injected sidebar (not a popup); tabs Videos/Comments/Chapters/Ask/Transcript, configurable. Survives SPA navigation via history/route listeners. The "Ask" tab's backend is undocumented and unclear (no API-key field declared).

**Licensing verdict:** neither extension is safe to fork or copy code from. A clean-room reimplementation from observable behavior is the only viable path — which the design conversation already concluded. This research confirms it.

## 2. Headline finding — the "YouTube built-in AI" mechanism (the blocking prerequisite)

**[FACT, HIGH confidence — sourced from the extension's own changelog v1.0.361/v1.0.372 + the I/O 2026 announcement]**

The "built-in AI" is **NOT a hidden API.** It is **DOM prompt-injection**: the extension opens YouTube's per-video **"Ask" panel** (Gemini-powered, announced Google I/O 2026) or **YouChat** (You.com integration in YouTube search), types a chapter/summary prompt into the input, waits, and scrapes the rendered response from the DOM. YouTube's own model does the work; the extension drives the UI as a free LLM.

**The realistic fallback ladder the extension actually uses:**

| Tier | Source | Reproducibility from a content script |
|------|--------|---------------------------------------|
| 1 | Creator chapters from `ytInitialPlayerResponse` / `ytInitialData` | **HIGH** — pure DOM/JSON read |
| 2 | YouTube's auto-generated chapters (same JSON path, present when YT computed them) | **HIGH** (read-only; cannot trigger generation) |
| 3 | **Ask-panel prompt injection** (Gemini, video-aware) | **MEDIUM** — rolling out gradually; DOM changes often (the extension patched it in v1.0.348, v1.0.351, v1.0.353) |
| 4 | YouChat prompt injection (You.com) | **LOW** — region/account dependent |
| 5 | Transcript → clipboard (user pastes into ChatGPT/Claude) | **HIGH** |
| 6 | Transcript → user's own OpenAI-compatible endpoint (Ollama/vLLM/OpenAI) | **HIGH** |

**Caveats on reliability (revised 2026-08-08 after operator correction — prior version overreached causally):**
- The Ask feature "may launch gradually or remain in testing for select user groups" (TechBuzz, I/O 2026). **However:** this extension will run in the *operator's own Chrome account*, where Links and Chapters' Ask-based generation has already been *observed working well*. Region/account availability elsewhere is therefore not the relevant constraint. [INFERENCE corrected: the prior draft treated global rollout as disqualifying; for a single-account internal tool it is not.]
- The extension's own patch history shows the Ask/YouChat DOM breaks repeatedly with no notice — so the *access path* needs hardening regardless.
- **The prior draft's causal claim was retracted:** it inferred from "QuickSummarize and keyFrame use external/local models" that "practitioners abandoned YouTube Ask as too fragile." That is **a causal claim with no receipt** — neither project documented trying and rejecting Ask. QuickSummarize's external-provider choice reflects its transcript-as-source-of-truth design philosophy, not evidence Ask is fragile. [This is the `[[narrative-as-signal]]` / receipt-rule failure.]

**Revised framing:** YouTube Ask is a **preferred opportunistic backend** — *tried first when present* — not merely a bonus and not pre-emptively demoted. Its fragility is managed operationally, not by refusal:

```
existing chapters? → use them
  ↓ no
YouTube Ask present in this session? → try it (prompt → parse → validate timestamps)
  ↓                                    ↓ on timeout / invalid / selector breakage
  ↓                                    fallback
configured AI provider (OpenAI-compatible / Ollama / Gemini Nano Direct / etc.)
  ↓
cache result keyed by videoId
```

Detection + timeout + validation + fallback is the correct pattern. Do NOT promise "no LLM" (the configured provider remains the floor), but do NOT demote Ask below providers either when the operator has observed it working.

## 3. In-browser transcript acquisition (the universal substrate)

[FACT, HIGH confidence — multiple independent sources; consistent with the existing server-side wiki concept. **Corrected 2026-08-08: prior draft missed the content-script isolated-world constraint.**]

**Critical mechanism the prior draft glossed:** Chrome content scripts run in an **isolated JavaScript world** by default and **cannot read page-context globals** like `ytInitialPlayerResponse` directly (official Chrome docs: content scripts have a separate JS environment from the page). The real data path must be designed explicitly:

```
YouTube MAIN world  ── reads window.ytInitialPlayerResponse
   │  chrome.scripting.executeScript({ world: "MAIN", ... })  OR  injected <script> tag
   ▼
serialize result (plain JSON — no DOM/function refs cross the boundary)
   │
   ▼
extension isolated world (content script)
   │  chrome.runtime.sendMessage
   ▼
service worker / side panel
```

From that corrected foundation, the reliable methods (best → acceptable):

1. **Read `ytInitialPlayerResponse.captions.playerCaptionsTracklistRenderer.captionTracks` via a MAIN-world execution** — fastest, no cross-origin request. Each track has a `baseUrl`; append `&fmt=json3`. Pick `kind=asr` for auto-generated. **[HIGH]** — fails only when captions are disabled/hidden.
2. **Innertube `player` endpoint** (`POST youtubei/v1/player` with WEB client context, fetchable from the service worker) → same `captionTracks` list → baseUrl + `&fmt=json3`. Mirrors how YouTube's own player loads captions. **[HIGH]**
3. **timedtext endpoint with PO-token (`pot`)** — modern YouTube requires a proof-of-origin token (`serviceIntegrityDimensions.poToken`); without it the endpoint returns an empty 200. **[HIGH when token present, MEDIUM otherwise]**
4. **`youtubei.js`** — maintained library implementing the Innertube packet format; widely used in extensions. **[HIGH]**

**Freshness contract (mandatory — this is the exact bug `steipete/summarize` spent releases fixing):** every async acquisition must stamp its result with the `videoId` it was started for, and the panel/service-worker must **reject any response whose `videoId !== currentVideoId`** after SPA navigation. Otherwise stale-A results paint onto video B. Pattern:
```
nav to video B → invalidate active A → acquire context(B) → accept ONLY if response.videoId === activeVideoId
```

**Practitioner caveat (`QuickSummarize` README, GPL v3):** *auto-opening the caption/transcript panel "is not recommended because it may look like automation behavior to YouTube."* Prefer reading `ytInitialPlayerResponse` over driving the transcript-panel UI, to avoid bot-detection signals. This is a real risk the conversation did not mention.

## 4. Native chapter acquisition

[FACT, MEDIUM confidence — single primary source + general knowledge; the exact JSON key path is [INFERENCE] until verified against a live page]

Creator chapters live in `ytInitialPlayerResponse` under `macroMarkersList` / the chapters array (same JSON YouTube uses to render seek-bar markers), and in `ytInitialData` engagement-panels for the visible chapter list. Auto-generated chapters occupy the same path when YouTube computed them. A content script reads these directly — **no AI involved.** Fallback: parse description timestamp lines via regex (`(\d{1,2}:\d{2}(:\d{2})?)\s+(.+)`).

> Note: the exact key path (`macroMarkersList.macroMarkersListItem` vs engagement-panel chapter renderer) is **[INFERENCE]** — verify against a live `ytInitialPlayerResponse` dump before coding. The existence of structured chapters in that object is **[FACT]**.

## 5. Sidebar container — `chrome.sidePanel` vs in-page injection is an OPEN visual question (not settled)

[Corrected 2026-08-08: the prior draft concluded `chrome.sidePanel` was "the recommended architecture." That conflated **API capability** (verified — the panel stays open, survives nav, doesn't close on click) with **product fit** (NOT verified — where the panel visually sits relative to YouTube's layout). Operator correction was decisive.]

The key distinction the prior draft missed: **`chrome.sidePanel` is a browser-level panel that sits *alongside* the entire webpage.** It does **NOT** occupy YouTube's right-hand recommendation column. Trinity, by contrast, injects a div *into the page's* secondary column, *replacing* recommendations. These produce materially different experiences:

```
chrome.sidePanel (alongside the browser):       in-page injection (Trinity-style):
VIDEO        [YT recommendations]  │ CHAPTERS    VIDEO        CHAPTERS (recs displaced)
████████     thumbnails            │ 00:00       ████████     00:00
████████                           │ 04:12       ████████     04:12
                                   │ 09:37                    09:37
```

A side panel narrows the YouTube viewport, which may shrink the video and leave recommendations in place — potentially *not* the "turn wasted recommendation space into a workspace" product vision from the design conversation. **This is not decidable by reading API docs.** It needs a visual test.

**Resolution (Gate 1B):** build two throwaway mockups (side panel with placeholder chapter rows; minimal in-page panel in YouTube's secondary column) and screenshot them in real YouTube in: normal mode, theater mode, sidebar open, sidebar closed — comparing actual video size and what happens to recommendations. Pick the container that matches the desired experience, not the one with the cleaner API.

For reference, the API facts (still useful regardless of decision):

| Property | chrome.sidePanel | DOM-injected (in-page) |
|---|---|---|
| Toggle on icon click | `setPanelBehavior({openPanelOnActionClick:true})` | manual show/hide |
| No-close on timestamp click | ✅ native | ❌ must fight re-renders |
| SPA-nav survival | ✅ native | needs `yt-navigate-finish`/MutationObserver |
| Sits in YouTube's right column / displaces recs | ❌ alongside the page | ✅ can |
| Video stays full-width | ❌ narrows viewport | ✅ if injected beside #secondary |
| Full Chrome API access | ✅ extension page | ⚠️ content-script context |
| Maintenance cost (YouTube DOM churn) | low | higher |

**Seek mechanism (applies to both):** the panel/context must seek via the page — `document.getElementById('movie_player').seekTo(seconds)` in the page context, reached by message-passing. `steipete/summarize` already has a dedicated `apps/chrome-extension/src/lib/seek.ts` for exactly this.

## 6. Existing implementations — reuse evaluation (the first decision, not build-from-scratch)

[Revised 2026-08-08: prior draft framed this as "clean-room references" and skipped the reuse question entirely. Operator correction: a mature MIT implementation of ~80% of the architecture must get an explicit REUSE/EXTRACT/FORK/REJECT verdict before writing anything new.]

### 6a. `steipete/summarize` — the dominant candidate (MIT, 6.5k★)

**Verified this session** (`gh repo view` + README + tree + CHANGELOG + LICENSE, 2026-08-08):
- **MIT License** (Copyright Peter Steinberger), **6,532 stars, 440 forks**, last push **2026-08-05** (3 days ago), TypeScript, WXT monorepo, `npm: @steipete/summarize` + a separate **`@steipete/summarize-core`** library package.
- **Chrome Side Panel** (auto-opens on toolbar click) **+ Firefox Sidebar**; Chrome Web Store live (`cejgnmmhbbpdmjnfppjdfkocebngehfg`).
- **Direct mode runs without the companion daemon** — README: *"works immediately with Auto using Chrome's built-in Gemini Nano Summarizer API and extractive fallback... Auto calls a configured OpenAI, OpenRouter, Anthropic, Gemini, xAI, Z.AI, NVIDIA, MiniMax, GitHub Models, Ollama... directly from Chrome. Keys stay in chrome.storage.local."* The optional daemon adds CLI backends/OCR/native media.
- Already implements, in `apps/chrome-extension/src/`: `entrypoints/background/youtube-transcript.ts` + `youtube-local-transcript.ts` + `youtube-sabr-capture.ts` (transcript acquisition incl. SABR capture); `offscreen/whisper.ts` + `browser-local-transcript.ts` (browser-side fallback transcription for captionless videos); `panel-summarize.ts` / `panel-summary-session.ts` (Overview); `panel-chat.ts` / `panel-chat-runtime.ts` (Ask/Chat); `panel-state.ts` / `panel-session-store.ts` / `panel-cache-runtime.ts` (state isolation + caching); `lib/seek.ts` (clickable-timestamp seeking); `extract-cache.ts` (per-URL cache); `listeners.ts` (SPA nav).
- **The CHANGELOG documents that the hard bugs are already fixed** — the exact problems the operator anticipated rediscovering:
  - *"reject YouTube caption and transcript-panel results when the tab navigates to another video during extraction"* → the videoId-freshness contract (Section 3).
  - *"restore persisted chat history"* / chat-session scoping → chat-bleed-across-URLs.
  - *"truncated long-form transcript"* / *"cascading repetition and truncated long-form transcript"* → long-video truncation.
  - *"stale extension state"*, *"stale service workers"* → service-worker lifecycle.

**What it does NOT have (the additive gap):**
- A dedicated **Chapters** tab/feature (it has summary + transcript, not native-chapter display / description-timestamp parsing as a first-class view).
- **YouTube-Ask-panel generation** as a provider (it uses external LLMs + Gemini Nano Direct; not YouTube's own Ask panel). These are exactly the two pieces the design conversation wants.

**Footprint concern:** the extension also carries a heavier **`automation/`** layer (REPL, skills, tools, debugger-backed automation) and hover-summary/slide features. A fork intended only for "Chapters | Overview | Ask | Transcript | Links" would want to strip automation/hover to reduce surface area — needs a footprint audit.

**Reuse verdict — FORK (provisional, pending Gate 1A):**
- **REJECT** is clearly wrong given MIT + 6.5k★ + ~80% coverage + solved hard bugs.
- **REUSE-as-published** can't work — the store extension has no Chapters tab and no YouTube-Ask provider; adding them requires modifying source.
- **EXTRACT components** (`@steipete/summarize-core`) into a fresh extension is viable for the transcript/extraction layer, but the panel/state/seek modules are coupled to their panel-session architecture — clean extraction may cost more than forking.
- **FORK** the extension, strip `automation/`/hover if unwanted, add a Chapters view + a YouTube-Ask provider, keep the MIT notice. This inherits the solved bugs (freshness, truncation, seek, SPA nav) for free. **This is the leading path**, contingent on Gate 1A confirming Chapters is additive without fighting the panel-state architecture and quantifying the stripped footprint.

> ⚠️ Honest caveat: I have NOT yet confirmed whether adding a Chapters tab fits cleanly into their `panel-state`/`panel-session-store` tab model, nor measured the stripped dependency footprint. Those are the two open questions Gate 1A must close before FORK is final.

### 6b. Smaller / less suitable references

| Repo | License | Stars | Note |
|---|---|---|---|
| EchoTide/QuickSummarize | **GPL v3 (copyleft, NOT permissive)** | 5 | side-panel + transcript-first; OpenAI-compatible/Anthropic. **Prior draft mislabeled GPLv3 as "permissive" — corrected: GPL is copyleft.** Also, "study GPL source then clean-room reimplement" is conceptually muddy for true clean-room. Lower priority now that the MIT `steipete/summarize` exists. |
| parathaprat/keyFrame | none (unlicensed) | 0 | DOM sidebar + native-messaging host. **Do not copy** (unlicensed). |
| Harsh-Pachauri/YouTube-Transcript-Summarizer-Extension | none | 0 | Older; minor reference. |

> **Build-stack note:** `steipete/summarize` uses **WXT** (TypeScript, pnpm) — consistent with the MV3 recommendation in `[[chrome-acp-library-stack-and-best-practices-2026]]`. A fork inherits a battle-tested WXT setup directly.

## 7. Competitor landscape + practitioner signals

[Sources: notelm.ai 2026 review + store pages; tag items [PRACTITIONER] where engagement data exists]

- **The exact gap our target fills is unoccupied:** no reviewed extension offers a *persistent, tabbed sidebar* combining chapters + overview + transcript + clickable-timestamp navigation that *never auto-closes on click or SPA nav*. Monica/Synapse claim "persistent" but still exhibit click-close bugs. This validates the product thesis.
- **Universal user complaints (pain to avoid):** popup-closes-on-click (nearly every popup-based extension — Glasp, YouTranscript, TubeScribeAI), required OpenAI key/login, slow latency (15–50s), breaks on SPA navigation, no offline caching, privacy/public-sharing defaults.
- **Universal user praise (features to copy):** persistent sidebar, clickable timestamps, no-login transcript, dark mode, caching by video, export (SRT).
- **SponsorBlock** (2439 upvotes, [PRACTITIONER]) is the gold-standard pattern for a long-lived YouTube extension: community-maintained, crowd-sourced data, minimal permissions, survives YouTube changes. Worth studying for the "how to not break every YouTube update" discipline.
- [INFERENCE] Most "8-best" review accuracy numbers (Eightify ~92%, Glasp ~81%) are vendor/affiliate-sourced — treat as directional, not measured.

---

## Recommendations — record of revisions (2026-08-08)

The original numbered recommendations (build-on-sidePanel / demote-Ask / QuickSummarize-template / build-v0.1) are **superseded** by the operator-corrected 3-gate sequence below. Revision record:
1. ~~Build on `chrome.sidePanel`~~ → now an **unresolved candidate** pending Gate 1B visual test.
2. ~~Treat Ask as a bonus path~~ → now a **preferred opportunistic backend** with detection+timeout+validation+fallback (single-account context).
3. Transcript acquisition stands, **but requires MAIN-world execution** (isolated-world correction) + videoId freshness contract.
4. Native-chapter reading stands; exact key path still [INFERENCE].
5. ~~Study QuickSummarize (GPL) as template~~ → GPL is copyleft (corrected); the **MIT `steipete/summarize`** is now the primary reuse candidate.
6. ~~v0.1 build spike~~ → now a **decision spike (Gate 1)** precedes any build.

## Recommendations — revised to a 3-gate sequence (2026-08-08)

[The prior draft recommended `chrome.sidePanel` + build-from-scratch + a v0.1 spike. After the operator correction — `steipete/summarize` omission + sidePanel-UX-not-settled + Ask-demotion-overreach + isolated-world error — the sequence is restructured. The two highest-uncertainty questions (reuse feasibility, visual container) are isolated in Gate 1 *before* any transcript/AI work.]

**Gate 1 — Reuse feasibility + visual container (NO AI, NO transcript work).**

- **1A — `steipete/summarize` reuse verdict.** Determine with evidence: can its Chrome extension run standalone (yes — Direct mode)? Can `automation/`/hover be stripped, and what's the resulting dependency footprint? Does a Chapters view fit additively into its `panel-state`/`panel-session-store` tab model, or does it fight the architecture? Can its Overview + Chat + Transcript + seek be retained as-is? Output: **FORK / EXTRACT (`@steipete/summarize-core`) / REJECT** with reasons. Leading hypothesis: FORK.
- **1B — Visual container test.** Two throwaway mockups with placeholder chapter rows only: (A) `chrome.sidePanel`, (B) minimal in-page panel in YouTube's secondary column. Screenshot both in real YouTube: normal, theater, sidebar-open, sidebar-closed — capturing actual video size and recommendation-column behavior. Pick the container that matches the desired "turn wasted recommendation space into a workspace" experience. **This decides whether Summarize's sidePanel default is even the right container for us.** Confidence that this must precede everything else: HIGH.

**Gate 2 — Acquisition spike (only after Gate 1).** Real YouTube page → current video identity → **MAIN-world** native chapter/caption extraction (`chrome.scripting` `world:"MAIN"` or injected script) → serialized, videoId-stamped `VideoContext` → chosen panel implementation → click timestamp → real `movie_player.seekTo()`. Test matrix: creator chapters; timestamped description only; captions-no-chapters; auto-captions; long video; SPA nav A→B→Back. Require observable provenance (`videoId`, `chapterSource`, `transcriptSource`, `contextVersion`). No synthetic fixtures as acceptance evidence.

**Gate 3 — AI behavior (only after Gate 2).** Reproduce the Links-and-Chapters insight: no chapters → YouTube Ask detected → request generation → parse + validate timestamps → cache by videoId. Deliberately break the selector / force a timeout → prove no stale/spurious result + optional-provider fallback works. Then add Overview, then interactive Ask.

The target architecture is unchanged: **Chapters | Overview | Ask | Transcript | Links** with one shared video-context layer. But confidence that we should *build the underlying extension from scratch* is now LOW (Summarize exists, MIT, covers ~80%, solved the hard bugs), and confidence that `chrome.sidePanel` is the right container is now UNRESOLVED until Gate 1B's visual test.

## Workspace-counterexample check (Step 3.15)

- **chrome.sidePanel candidate:** no documented workspace counterexample (the host's CDP/concurrent-session invariants concern fleet automation, not a single user-facing extension). ✅ — but note this check addresses *host safety*, not the *product-fit* question Gate 1B resolves.
- **Transcript acquisition:** `[[youtube-throttling-returns-429-not-silent-200]]` qualifies — an extension in the user's logged-in session is far less likely to hit 429 than a server scraper, but robust code should still handle empty/429 transcript responses gracefully (fallback chain). ✅ accounted for.
- **Forking `steipete/summarize`:** no counterexample — MIT permits fork + modify + keep notice. The automation/REPL layer in the fork would add a debugger-backed capability surface worth a security once-over, but that's a Gate 1A footprint concern, not a blocker.

## Host invariant check (Round 3.5)

No host-invariant violations. The extension runs in the operator's own Chrome with their own session; it does not contend for the shared CDP/cookie DB that `[[concurrent-cdp-auth-contention]]` protects (that invariant governs *fleet* parallel browser automation, which is a separate concern). The one carry-over discipline: do not design the extension to read live browser cookie state in a way that would conflict if a fleet agent also drives the same profile — but the MVP needs no such access.

## Receipts

Mechanism and source claims in this page, with their evidence basis:

- **chrome.sidePanel API behavior (toggle, persistence, SPA-nav survival, seek via message passing):** OBSERVED this session from the official Chrome for Developers reference (https://developer.chrome.com/docs/extensions/reference/api/sidePanel), fetched 2026-08-08. `setPanelBehavior({openPanelOnActionClick:true})`, `sidePanel.open({tabId/windowId})` (Chrome 116+), `setOptions({tabId,path,enabled})`, and the doc statement "the side panel remains open when navigating between tabs" are the receipts for recommendations 1–2 and the seek pattern.
- **"Built-in AI" = Ask/YouChat DOM prompt-injection:** OBSERVED from the Links and Chapters store changelog read this session — v1.0.361 ("uses YouTube's 'Ask' panel when available; falls back to clipboard/API mode"), v1.0.372 ("structured summary using YouTube's built-in AI (YouChat)"), v1.0.348 ("transcript extraction … uses ytd-transcript-segment-renderer"). The Ask/Gemini attribution is DERIVED from one TechBuzz article on the I/O 2026 announcement — [INFERENCE] on the exact Gemini-vs-You.com split.
- **Transcript acquisition (`ytInitialPlayerResponse.captions` → baseUrl + `&fmt=json3`):** OBSERVED from Stack Overflow Q32142656 + the grokipedia timedtext page. The **exact JSON key path** (`macroMarkersList.macroMarkersListItem`) was **NOT inspected on a live page this session → [INFERENCE]**; verify against a real `ytInitialPlayerResponse` dump before coding.
- **PO-token requirement:** OBSERVED from the grokipedia timedtext endpoint page + SO Q79668836.
- **QuickSummarize = GPL v3, side-panel, transcript-first, external LLM:** OBSERVED this session via `gh api repos/EchoTide/QuickSummarize/contents/README.md` + LICENSE + file tree (modular `extension/lib/`: background-sidepanel.js, chat-context.js, chat-session.js). The "auto-opening captions is not recommended" quote is OBSERVED from that README.
- **keyFrame = native-messaging host architecture:** OBSERVED this session via `gh api` manifest (`permissions:["nativeMessaging"]`, `host_permissions:["http://localhost/*"]`) + file tree (`host/`, `server/index.js`, `.env.example`). Unlicensed → do not copy.
- **`steipete/summarize` reuse candidate (the pivotal artifact added 2026-08-08):** OBSERVED this session via `gh repo view` (MIT, 6,532★, 440 forks, pushed 2026-08-05), `gh api` LICENSE (MIT, Peter Steinberger), README (Direct mode without daemon; Gemini Nano + OpenAI/OpenRouter/Anthropic/Gemini/xAI/Z.AI/NVIDIA/MiniMax/GitHub Models/Ollama; keys in chrome.storage.local; Chrome Side Panel + Firefox Sidebar; auto-opens on toolbar click), file tree (`apps/chrome-extension/src/entrypoints/background/youtube-transcript.ts`, `youtube-local-transcript.ts`, `youtube-sabr-capture.ts`, `panel-summarize.ts`, `panel-summary-session.ts`, `panel-chat.ts`, `panel-chat-runtime.ts`, `panel-state.ts`, `panel-session-store.ts`, `panel-cache-runtime.ts`, `lib/seek.ts`, `extract-cache.ts`, `offscreen/whisper.ts`, `browser-local-transcript.ts`), code search (`lib/seek.ts` + `docs/timestamps.md`), and CHANGELOG (videoId-freshness rejection on nav, chat-history scoping, long-video truncation fixes, stale-extension-state fixes). The "Chapters not present / YouTube-Ask not a provider" gap is DERIVED from README + tree (no chapters module, no ask-panel provider file) — [INFERENCE] until confirmed by reading panel-state/tab model in Gate 1A.
- **Content-script isolated-world correction:** OBSERVED from official Chrome content-scripts docs (content scripts have a separate JS environment; `world:"MAIN"` via `chrome.scripting` reaches page globals). The prior draft's "read ytInitialPlayerResponse directly from a content script" was a technical error, now corrected.
- **Extensions closed-source / Trinity "All Rights Reserved":** OBSERVED from the Chrome Web Store and Firefox AMO pages this session.
- **Competitor "accuracy %" figures (Eightify ~92%, Glasp ~81%):** **[INFERENCE]** — vendor/affiliate-sourced via the notelm.ai review; not independently measured this session.

## What this means for our workspace

- **DO NOT pre-authorize "CREATE a new extension."** The prior draft concluded CREATE. That conclusion is **retracted** (2026-08-08 operator correction): `steipete/summarize` (MIT, 6.5k★) already implements ~80% of the architecture and has solved the hard bugs. The first action is Gate 1A's reuse verdict (FORK/EXTRACT/REJECT). A from-scratch build is justified only if Gate 1A returns REJECT with evidence — not assumed.
- **No retirement needed** — this is the **in-browser complement** to the existing server-side YouTube pipeline (`[[video-to-wiki-pipeline-transcript-extraction-multimodal]]`, `[[youtube-transcript-extraction-techniques]]`, the `yt-is` package). Those stay; this adds the per-video viewer/understanding surface.
- **UPDATE** `[[youtube-transcript-extraction-techniques]]` to cross-reference this concept for the browser/content-script context (it currently covers only server-side Python extraction). — *done this session.*
- **Next step is a decision spike (Gate 1), NOT a build spike.** The decision packet: (1A) `steipete/summarize` reuse verdict with footprint + Chapters-additivity evidence; (1B) sidePanel-vs-in-page visual test screenshots. Only after those settle does the acquisition spike (Gate 2) and AI spike (Gate 3) follow.
- **Live verification remains the falsifier** — the [INFERENCE] chapter-key-path and the Ask-panel reproducibility must be tested against real videos. But that is Gate 2/3, not the immediate next action.

## Falsifier

- If `chrome.sidePanel` is removed or its toggle behavior changes in a future Chrome, recommendation 1–2 break (low likelihood; it's a stable, promoted API).
- If YouTube removes the per-video Ask panel or hardens it against DOM prompt-injection, tier 3–4 disappear (medium likelihood; this is why they are NOT the primary path).
- If `ytInitialPlayerResponse.captions` shape changes, transcript acquisition needs re-derivation — re-verify against a live page each build (high likelihood over time; the QuickSummarize maintainer already navigates this).
- A live spike on real videos is the ultimate falsifier for all of the above — do that before committing to the full spec.

## Confidence summary

- Extensions are closed-source / un-forkable: **[FACT, HIGH]**.
- "Built-in AI" = Ask-panel/YouChat DOM prompt-injection: **[FACT, HIGH]** (changelog-stated); reliability as primary path: **disconfirmed by practitioner choices**.
- chrome.sidePanel as recommended sidebar: **[FACT, HIGH]** (official docs + working reference).
- Transcript acquisition methods: **[FACT, HIGH]**.
- Exact chapter JSON key path: **[INFERENCE, MEDIUM]** — verify live before coding.
- Competitor "accuracy %" figures: **[INFERENCE]** — vendor-sourced, treat as directional.
