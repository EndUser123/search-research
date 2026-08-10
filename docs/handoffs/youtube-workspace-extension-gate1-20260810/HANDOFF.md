---
thread_id: 5dd97700-52ec-4da2-95a8-075bf504d082
parent_handoff_path: none
current_session_id: 019fe36e-7cb5-7003-b7dd-f94396165026
parent_session: none
current_terminal_id: 019fe36e-7cb5-7003-b7dd-f94396165026
produced_at: 2026-08-10T05:45:00Z
last_updated_by: 019fe36e-7cb5-7003-b7dd-f94396165026
last_updated_at: 2026-08-10T05:45:00Z
status: open
handoff_type: investigation
accurate_as_of_head: 30be829fbb81fc415759b9b91636ab4a1173289f
---

# Handoff — YouTube Workspace Sidebar Extension: Gate 1 Decision Spike

## Objective

Determine whether to FORK, EXTRACT, or REJECT `steipete/summarize` as the foundation for a unified YouTube workspace Chrome extension (Chapters | Overview | Ask | Transcript | Links), and decide the visual container (chrome.sidePanel vs in-page injection) — before any transcript/AI implementation work.

**Scope bounds:** Gate 1 only (reuse verdict + visual container test). Gate 2 (acquisition spike) and Gate 3 (AI behavior) are explicitly out of scope until Gate 1 settles.

## Status

OPEN — ready to implement Gate 1. All research complete; no code written yet.

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

### G1A-01 — `steipete/summarize` reuse audit

- goal: Determine FORK / EXTRACT / REJECT with evidence.
- in scope: Clone the repo, read `apps/chrome-extension/src/entrypoints/background/panel-state.ts` and `panel-session-store.ts` to determine whether a Chapters view fits additively into the tab model. Measure the stripped dependency footprint (what's the bundle size if `automation/` and hover features are removed?).
- out of scope: Building the Chapters feature. Writing any extension code. Gate 2/3 work.
- files / anchors: `apps/chrome-extension/src/entrypoints/background/panel-state.ts`, `panel-session-store.ts`, `lib/seek.ts`, `manifest.json` (in the repo, not local yet).
- acceptance: A written verdict (FORK / EXTRACT / REJECT) with: (a) evidence that Chapters fits or fights the tab model, (b) measured stripped footprint, (c) what's inherited for free vs what must be built.
- falsifier: If Chapters cannot be added without modifying the panel-session architecture (not just adding a tab), FORK degrades toward EXTRACT or REJECT.
- verification level required: STATIC_INSPECTION

### G1B-01 — Visual container test

- goal: Decide `chrome.sidePanel` vs in-page injection based on real visual evidence.
- in scope: Build two throwaway mockups with placeholder chapter rows only: (A) `chrome.sidePanel` with minimal HTML, (B) minimal in-page div injected into YouTube's `#secondary` column. Screenshot both in real YouTube in: normal mode, theater mode, sidebar open, sidebar closed. Compare actual video size and recommendation-column behavior.
- out of scope: Transcript acquisition. AI. Chapters generation. Clickable timestamps. Any functionality beyond placeholder rows.
- files / anchors: Two throwaway `manifest.json` + minimal content scripts. Not committed to the workspace — throwaway spikes.
- acceptance: Screenshots showing both containers in all 4 YouTube modes, with a written verdict: which container matches the "turn wasted recommendation space into a workspace" experience from the design conversation.
- falsifier: If `chrome.sidePanel` narrows the video and leaves recommendations in place (not the desired UX), in-page injection wins despite higher maintenance cost.
- verification level required: LIVE_BEHAVIOR

## Open decisions

### D1: FORK vs EXTRACT vs REJECT

- **Question:** Do we fork `steipete/summarize`, extract its core library, or build clean-room?
- **Options:** (1) FORK — strip automation/hover, add Chapters + YouTube-Ask, keep MIT notice. (2) EXTRACT — use `@steipete/summarize-core` npm package for transcript/extraction, build fresh panel. (3) REJECT — clean-room build.
- **Selection criterion:** lowest total cost (inherited solved bugs + additive work) without architectural fighting.
- **Currently leading:** FORK (provisional — subject to G1A-01 evidence).
- **What would change the lead:** If Chapters fights the panel-session tab model, or the stripped footprint is too heavy, EXTRACT becomes viable.

### D2: chrome.sidePanel vs in-page injection

- **Question:** Which visual container?
- **Options:** (A) `chrome.sidePanel` (browser-level, alongside page, clean API, no DOM-fighting). (B) In-page injection (DOM div in YouTube's `#secondary`, displaces recommendations, fights SPA re-renders).
- **Selection criterion:** matches the product vision ("turn wasted recommendation space into workspace") with acceptable maintenance cost.
- **Currently leading:** UNRESOLVED — requires visual test (G1B-01). Cannot be decided from API docs.
- **What would change the lead:** Screenshots showing whether sidePanel leaves recommendations in place (bad) or narrows the video unacceptably (bad).

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

## Suggested next invocation

- `/refine` if G1A or G1B findings need tightening into implementation-ready task packets before Gate 2.
- `/design` if the container decision triggers a design-doc need (unlikely — the visual test settles it).
- `/go` after Gate 1 settles and Gate 2 task packets are defined.
- `/wiki` to update the research concept with Gate 1 outcomes (revision block).

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
