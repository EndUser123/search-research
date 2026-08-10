---
thread_id: 5e74c374-0369-4dc1-ba7d-ac9e646d4fcb
parent_handoff_path: P:/docs/handoffs/youtube-workspace-extension-gate1-20260810/HANDOFF.md
current_session_id: 019fea30-500e-7b83-abac-d737446e86fb
parent_session: 019fea30-500e-7b83-abac-d737446e86fb
current_terminal_id: 019fea30-500e-7b83-abac-d737446e86fb
produced_at: 2026-08-10T07:20:00Z
last_updated_by: 019fea30-500e-7b83-abac-d737446e86fb
last_updated_at: 2026-08-10T07:20:00Z
status: open
handoff_type: investigation
accurate_as_of_head: d1a89915c01f59d9d51170dd0bbfce0cb5fde7a7
---

# Handoff — YouTube Workspace Sidebar Extension: Gate 2 Acquisition Spike

## Objective

Prove the real runtime chain that the Gate 1 reuse verdict depends on:

**real YouTube video → authoritative `videoId` → MAIN-world acquisition → real chapters/transcript → videoId-stamped `VideoContext` → rendered in `#secondary` workspace → click real timestamp → real `movie_player.seekTo()`**

Then deliberately stress the dangerous boundary:

**A acquisition starts → navigate to B → A completes late → A result demonstrably rejected by the freshness invariant (not merely "didn't overwrite") → B remains authoritative → Back → correct A state restored or reacquired without duplicate mounts.**

**Scope bounds:** Gate 2 only — a falsification spike, not implementation. Gate 3 (YouTube Ask as opportunistic chapter/summary provider) and any packaging/polish are explicitly out of scope until Gate 2 settles.

## Status

OPEN — ready for a fresh session to execute. Gate 1 settled (EXTRACT + IN_PAGE_SECONDARY, recorded in the parent handoff). This handoff **inherits** those decisions; it does NOT re-decide them. Created in the prep session (2026-08-10, 019fea30...).

## Producing context

- Date: 2026-08-10
- Session: 019fea30... (this session — **prep only**, no execution)
- Operator directive (verbatim, paraphrased): "Gate 2 is a falsification spike, not permission to start building the product. Require evidence that the specific rejection mechanism fired — e.g., a structured diagnostic showing `{resultVideoId: A, activeVideoId: B, disposition: rejected_stale}`. Don't merely demonstrate that stale A *happened not to overwrite* B."
- Chrome MCP + chrome-devtools MCP connected in this session; can drive the operator's real Chrome AND a separate clean Chrome browser for visual/runtime tests.

## Read-first list (ordered)

1. **Parent handoff:** `P:/docs/handoffs/youtube-workspace-extension-gate1-20260810/HANDOFF.md` — Gate 1 resolutions (EXTRACT + IN_PAGE_SECONDARY), module lists, evidence trail. **Do NOT re-decide Gate 1.**
2. Research concept: `P:/.data/wiki/concepts/youtube-workspace-sidebar-extension-build-research.md` — full context (3-gate sequence, claim ledger, transcript/chapter acquisition, MAIN-world + isolated-world correction).
3. Clone of `steipete/summarize` at `P:/tmp/summarize-audit` (already exists this session, depth 1, last pushed 2026-08-05). Reuse the MAIN-world reader (`lib/youtube-page-transcript.ts`) and the seek helper (`lib/seek.ts`). Extend the reader to expose the chapter JSON path.
4. Source files to read before testing:
   - `P:/tmp/summarize-audit/apps/chrome-extension/src/lib/youtube-page-transcript.ts` — MAIN-world bridge (already implements `chrome.scripting.executeScript({ world: "MAIN" })`)
   - `P:/tmp/summarize-audit/apps/chrome-extension/src/lib/seek.ts` — dual-path seek
   - `P:/tmp/summarize-audit/apps/chrome-extension/src/entrypoints/background/panel-session-store.ts` — freshness contract pattern (per-tab/per-URL cache invalidation, inflight URL tracking, AbortController plumbing). Adapt to per-`videoId` for our `VideoContext`.

## Inherited decisions from Gate 1 (DO NOT RE-DECIDE)

- **Reuse strategy:** EXTRACT from `apps/chrome-extension/src/{lib,entrypoints/background}/`. Build fresh UI on top. The Summarize sidepanel UI is REJECTED (wrong product shape — summary-centric, no tab model).
- **Visual container:** IN_PAGE_SECONDARY (Trinity-style DOM injection into YouTube's `#secondary`).
- **YouTube Ask panel:** opportunistic backend with detection + timeout + validation + fallback — **Gate 3, not Gate 2**. Do not start this in Gate 2.
- **Module lists** (retained / removed / added): see the parent handoff's D1 section.

## Gate 2 success criterion

**The single end-to-end runtime proof:**

> real video A → authoritative `videoId` → real chapters/transcript → stamped `VideoContext` → rendered in `#secondary` workspace → click real timestamp → real `movie_player.seekTo()` → navigate A → B → Back during acquisition → stale A result demonstrably rejected by the freshness invariant (not merely "didn't overwrite")

### Critical acceptance bar (operator directive 2026-08-10)

> Don't merely demonstrate that stale A *happened not to overwrite* B. Require evidence that the **specific rejection mechanism fired** — for example, a structured diagnostic showing `{resultVideoId: A, activeVideoId: B, disposition: rejected_stale}`. That distinction matters. Otherwise a successful-looking A→B test could be accidental because timing prevented the mutation rather than because the freshness invariant actually protected it.

This means: G2-06 must produce **structured diagnostic records** at every rejection point (and ideally at every accept point too, for negative-control evidence). A "passing" A→B test without the rejection mechanism firing is a **FAILED** test, not a passed test — re-test with forced timing until the diagnostic fires.

## Verified facts inherited from Gate 1 (with receipts)

- [FACT] `steipete/summarize` is MIT licensed, mature, last push 2026-08-05. (Receipt: LICENSE + git log of clone.)
- [FACT] `lib/youtube-page-transcript.ts` already implements `chrome.scripting.executeScript({ world: "MAIN" })` for caption source read + timedtext fetch. (Receipt: source inspection at `P:/tmp/summarize-audit/apps/chrome-extension/src/lib/youtube-page-transcript.ts`.)
- [FACT] `lib/seek.ts` implements dual-path seek (`<video>.currentTime` first, then `document.getElementById('movie_player').seekTo()`). (Receipt: source inspection.)
- [FACT] `entrypoints/background/panel-session-store.ts` implements per-tab/per-URL cache invalidation (`cached.url !== url → invalidate`), inflight URL tracking, AbortController plumbing. (Receipt: source inspection.)
- [FACT] Visual test confirmed (Gate 1B): in-page injection in `#secondary` preserves video width and replaces recommendations; chrome.sidePanel shrinks video and leaves recommendations. (Receipt: empirical measurements + screenshots from the Gate 1 session.)
- [FACT] `grep 'chapter|macroMarkers|chapters'` across `apps/chrome-extension/src/` returns NONE — Chapters is not a first-class concept anywhere. (Receipt: grep output from Gate 1.)
- [INFERENCE → Gate 2 will resolve to FACT] The exact native chapter JSON key path (`macroMarkersList` vs engagement-panel chapter renderer). G2-02 will discover this against a live `ytInitialPlayerResponse` dump.

## Current state

- Gate 1 committed and pushed. HEAD = `d1a89915c01f59d9d51170dd0bbfce0cb5fde7a7`, on `origin/main`. Research commits: `62a615a`, `e954985`, `30c3833`, `12e03ec`. Gate 1 resolution commit: `d1a8991`.
- Clone of `steipete/summarize` exists at `P:/tmp/summarize-audit` (depth 1).
- Chrome-devtools MCP (29 tools) + chrome MCP (1 tool) connected in this session — can drive a real YouTube watch page in the operator's Chrome (pageId-typed) or in a separate clean Chrome browser at any viewport size.
- No extension code written. No extension scaffolded. Gate 2 produces runtime evidence, not a packaged extension.
- Five Gate 1 doc nits (DOC-001..DOC-005 in `P:\.artifacts\noterm\grok-review\youtube-workspace-gate1\20260810-071405\findings.json`) are explicitly **deferred** by operator directive 2026-08-10. Not blocking Gate 2.

## Task packets

### G2-01 — live MAIN-world acquisition on a real YouTube watch page

- **goal:** Confirm `chrome.scripting.executeScript({ world: "MAIN" })` returns YouTube's caption source AND chapter JSON from `ytInitialPlayerResponse` on a live watch page.
- **in scope:** Load a throw-away extension skeleton in the operator's Chrome (or use the chrome-devtools MCP to inject MAIN-world eval as a stand-in for the extension's `chrome.scripting.executeScript`). Run against at least two real YouTube watch pages (e.g., `v=Sx5-xt8tH_M` which has native chapters; another with no chapters). Capture the full MAIN-world response from `window.ytInitialPlayerResponse`.
- **out of scope:** Building the actual extension UI. Caching. Chapter display. AI generation.
- **files / anchors:** `P:/tmp/summarize-audit/apps/chrome-extension/src/lib/youtube-page-transcript.ts` (reuse the reader pattern; extend to expose chapter path).
- **acceptance:** A live dump of `ytInitialPlayerResponse` from the MAIN world, captured as a structured artifact (JSON file or console record). The response includes the caption source structure (`captions.playerCaptionsTracklistRenderer.captionTracks`) and a discoverable chapter path.
- **falsifier:** If the MAIN-world reader fails to access `ytInitialPlayerResponse` (CSP or other restriction), Gate 2 is `BLOCKED: acquisition path not reachable from MAIN world`. Mitigation: a content-script-injected `<script>` tag as an alternative MAIN-world bridge.
- **verification level required:** LIVE_BEHAVIOR (real Chrome, real YouTube, no synthetic fixtures)

### G2-02 — native chapter JSON key path live-verified

- **goal:** Discover the exact JSON key path for native chapters and document it.
- **in scope:** From G2-01's dump, locate the chapter list. Test at least three videos: one with creator chapters, one with auto-generated chapters, one with neither. Try the candidate paths `macroMarkersList` and the engagement-panel chapter renderer.
- **out of scope:** Generating chapters via AI (Gate 3).
- **acceptance:** A documented path that works for both creator and auto-generated chapters when present. A small table of (videoId → chapter path → number of chapters) from the live test.
- **falsifier:** If creator chapters and auto-generated chapters use structurally different paths, both paths must be handled in the eventual adapter.
- **verification level required:** LIVE_BEHAVIOR

### G2-03 — description-timestamp regex fallback

- **goal:** For videos with no native chapters, parse timestamps from the description text.
- **in scope:** Apply the regex `(\d{1,2}:\d{2}(:\d{2})?)\s+(.+)` to the visible description text (from MAIN world or DOM walk). Live-verify against a real video whose description has timestamps but no chapter markers.
- **acceptance:** The regex extracts ≥1 chapter row from a real video whose description has timestamps; the rows render correctly in the placeholder workspace.
- **falsifier:** If YouTube's description HTML structure breaks the regex (embedded links, soft line breaks, RTL text), document the limitation and try a DOM-walk alternative (walking `yt-formatted-string` nodes).
- **verification level required:** LIVE_BEHAVIOR

### G2-04 — real `movie_player.seekTo` reachable

- **goal:** Confirm the seek path works in practice from the workspace context.
- **in scope:** From the content-script-injected workspace in `#secondary`, dispatch a seek request. Two paths to live-verify: (a) `<video>.currentTime = N` (works from isolated content-script world against the same-origin DOM); (b) `document.getElementById('movie_player').seekTo(N)` from page context (likely requires MAIN-world relay). Capture before/after `video.currentTime` and the seek-bar visual state.
- **acceptance:** A timestamp click in the workspace causes the actual movie player to seek. The seek is verifiable via console log of `video.currentTime` immediately after the click.
- **falsifier:** If `movie_player.seekTo` is not callable from isolated content-script context (likely), the seek must be relayed via MAIN-world execution (`chrome.scripting.executeScript({ world: "MAIN", func: (s) => document.getElementById('movie_player').seekTo(s) })`). Capture the relay's evidence.
- **verification level required:** LIVE_BEHAVIOR

### G2-05 — `#secondary` workspace SPA remount robustness

- **goal:** Confirm the workspace survives YouTube's SPA navigation A → B → Back without losing state or duplicating mounts.
- **in scope:** Subscribe to the `yt-navigate-finish` event (or fall back to a MutationObserver on `#secondary`). Re-mount the workspace when `#secondary` re-renders. Live-verify: navigate A → B (workspace re-renders with B's VideoContext) → Back → A (workspace re-renders with A's VideoContext). Count mounts; there must be exactly one workspace element per active videoId at any time.
- **acceptance:** Workspace renders exactly once per active videoId across navigation. No orphan elements. No duplicate panels. A DOM-count log (`document.querySelectorAll('#__yt_workspace').length === 1` invariant) at each transition.
- **falsifier:** If YouTube's `#secondary` is replaced in a way that strands the workspace (detaches without firing `yt-navigate-finish` AND no relevant MutationObserver fires), the workspace must re-attach on a follow-up render or the test fails.
- **verification level required:** LIVE_BEHAVIOR

### G2-06 — stale-result rejection with structured diagnostic evidence (CRITICAL)

- **goal:** Demonstrate that the freshness invariant **REJECTS** stale cross-video results with **observable evidence** — NOT merely that the timing prevented the mutation.
- **in scope:** Instrument the freshness check to emit a **structured diagnostic record** at every accept AND every rejection. Shape: `{ resultVideoId, activeVideoId, disposition: 'accepted' | 'rejected_stale', timestamp, sourceUrl, activeUrl, context }`. Then:
  - **Test A→B:** start A's acquisition, navigate to B before A completes, force a delay so A's result arrives AFTER B becomes authoritative, observe A's late completion with disposition=`rejected_stale` and the diagnostic record showing `resultVideoId: A, activeVideoId: B`.
  - **Test B→A (inverse):** same pattern, swapped.
  - **Test Back→A:** after A→B, navigate Back, observe correct A state restored or reacquired without duplicate mounts.
  - **Negative control:** with no stale result in flight, the acceptance path produces `disposition: 'accepted'` for valid matches.
- **acceptance:** A diagnostic log is produced showing the specific rejection mechanism fired (not just "the result didn't take"). The diagnostic includes both `resultVideoId` (the rejected result's videoId) and `activeVideoId` (the authoritative one at the rejection moment), and a disposition field like `rejected_stale`. The log is durable (file on disk or console capture).
- **falsifier:** If the timing happens to prevent mutation without the freshness check firing, the test is **INSUFFICIENT**. Repeat with a forced delay (artificial 1-3s pause in the result delivery) to ensure A's result actually arrives after B becomes authoritative. The rejection mechanism MUST fire (with the structured diagnostic). A "passing" test without the diagnostic is a FAILED test.
- **verification level required:** LIVE_BEHAVIOR + EVIDENCE OF REJECTION MECHANISM FIRING

## Hard constraints

1. **NO implementation beyond the spike.** Gate 2 produces runtime evidence for the 6 items above; packaging comes after Gate 3. No UI polish, no provider abstraction, no Overview/Ask/Links tab building, no Whisper fallback, no daemon.
2. **Real YouTube videos, not synthetic fixtures.** Every acceptance criterion runs against a live watch page in the operator's actual Chrome session, or the separate clean chrome MCP browser for layout-isolated tests.
3. **No transcript/AI work beyond the substrate.** Transcript acquisition IS the substrate (allowed). AI-backed chapter generation is Gate 3 — do not start.
4. **The structured-diagnostic evidence requirement for G2-06 is non-negotiable.** A passing-looking A→B test that doesn't show the rejection mechanism firing is a **FAILED** test. Re-test until the diagnostic fires under forced timing.
5. **YouTube Ask as a provider is Gate 3.** Do not start this in Gate 2.
6. **Do NOT re-decide Gate 1.** EXTRACT + IN_PAGE_SECONDARY are fixed.

## Cross-reference couplings

- **Parent handoff:** `P:/docs/handoffs/youtube-workspace-extension-gate1-20260810/HANDOFF.md` — inherits Gate 1 decisions; do not re-decide.
- **Research concept:** `P:/.data/wiki/concepts/youtube-workspace-sidebar-extension-build-research.md` — Gate 2/3 sequences, transcript acquisition, claim ledger.
- **Clone:** `P:/tmp/summarize-audit` — reuse the MAIN-world reader and seek helper; extend the reader to expose the chapter JSON path.
- **Chrome MCP + chrome-devtools MCP:** connected in this session; can drive a real YouTube watch page (operator's existing tab or a new chrome MCP browser tab at any viewport).
- **Five Gate 1 doc nits** at `P:\.artifacts\noterm\grok-review\youtube-workspace-gate1\20260810-071405\findings.json` (DOC-001..DOC-005) — explicitly deferred; not blocking Gate 2.

## Other outstanding streams (not handed off)

- **Research-artifact-revision-invalidation** wiki concept — needs AGENTS.md promotion decision + 2 minor review fixes (broken wikilink, pre-correction line numbers). Open but not blocking Gate 2.
- **ship-py pi CLI dispatch failure** — separate handoff. Open but not blocking Gate 2.
- **Five Gate 1 doc nits** (DOC-001..DOC-005) — deferred by operator directive 2026-08-10. Not blocking Gate 2; do not address them in Gate 2's session.

## Explicit non-goals (Gate 2)

- Do NOT build the full extension. Gate 2 produces runtime evidence; packaging comes after Gate 3.
- Do NOT implement chapter generation via AI. That's Gate 3.
- Do NOT implement Overview, Ask, Links, or Whisper fallback. Those are after Gate 3.
- Do NOT add a polished UI. Placeholder chapter rows are acceptable for the spike.
- Do NOT broaden Gate 2 beyond the 6 task packets above. The success criterion is the single end-to-end proof.
- Do NOT fix the five Gate 1 doc nits.

## Resumption protocol

1. Read this handoff and the parent Gate 1 handoff. Confirm EXTRACT + IN_PAGE_SECONDARY are inherited (do not re-decide).
2. Set up a throw-away extension skeleton in the operator's Chrome. The skeleton can be minimal: a `manifest.json` (MV3, `sidePanel` + `scripting` + `<all_urls>` permissions), a background service worker that runs the MAIN-world reader, a content script that mounts a placeholder workspace in `#secondary`. No packaged extension required. Alternatively, use the chrome-devtools MCP to inject MAIN-world eval as a stand-in for `chrome.scripting.executeScript({ world: "MAIN" })`.
3. For each task packet, run against a real YouTube watch page (the operator's existing tab or a new chrome MCP browser tab). Capture evidence as console logs, structured diagnostic records (especially for G2-06), JSON dumps (for G2-01 / G2-02), or screenshots (for G2-05).
4. For **G2-06 specifically**: instrument the freshness check to emit structured diagnostic records on every accept and every rejection. Live-verify the rejection mechanism fires under forced timing (artificial 1-3s pause). A passing-looking test without the diagnostic firing is a FAILED test — re-test.
5. After all 6 task packets produce real evidence, write a Gate 2 verdict (PASS / FAIL per task packet + overall verdict). Update this handoff's `## Status` to `resolved` with the verdict and the diagnostic-evidence path.
6. Do NOT proceed to Gate 3 unless the operator authorizes after seeing the Gate 2 evidence.

## Suggested next invocation

- Run `/go` against this handoff in a **fresh session**. The fresh session will execute the 6 task packets as a runtime falsification spike.
- After Gate 2 evidence is captured: `/check` to session-verify the captures match the claims; then return to the operator for authorization to proceed.
- After Gate 3 (post-Gate 2): `/wiki` to update `youtube-workspace-sidebar-extension-build-research.md` with the Gate 2 + Gate 3 revision blocks. The revision must propagate to frontmatter, decision-context, recommendations, falsifier, and confidence per the research concept's claim ledger.
- Gate 3 handoff: created after Gate 2 settles and the operator authorizes.

## Last user message (verbatim)

> "/go This is a clean stopping point for Gate 1.
>
> I would not spend another cycle on the five documentation nits now. ... Proceed to Gate 2 ... preserve one important discipline: Gate 2 is a falsification spike, not permission to start building the product. Its job is to prove the real runtime chain: real YouTube video → authoritative videoId → MAIN-world acquisition → real chapters/transcript → videoId-stamped VideoContext → #secondary workspace → timestamp click → actual seek. Then deliberately stress the dangerous boundary: A acquisition starts → navigate to B → A completes late → A result rejected → B remains authoritative → Back → correct A state restored/reacquired without duplicate mounts.
>
> One thing I would add to the Gate 2 acceptance bar: Don't merely demonstrate that stale A *happened not to overwrite* B. Require evidence that the **specific rejection mechanism fired** — for example, a structured diagnostic showing `{resultVideoId: A, activeVideoId: B, disposition: rejected_stale}`.
>
> Next action: open `P:/docs/handoffs/youtube-workspace-extension-gate2-20260810/HANDOFF.md` in a fresh session and run `/go` against it."

## Epistemic labels per claim

- [FACT] All [FACT] claims cite tool-call receipts from the Gate 1 session (file inspection at `P:/tmp/summarize-audit/`, eval output, screenshots, git log).
- [INFERENCE → Gate 2 will resolve to FACT] The exact native chapter JSON key path (`macroMarkersList` vs engagement-panel chapter renderer). G2-02 promotes it to FACT via a live `ytInitialPlayerResponse` dump.
- [UNKNOWN] Real-world behavior of the freshness mechanism under forced timing — the structured-diagnostic requirement for G2-06 is the operator's prescribed mechanism for reducing this unknown.

## Suggested skills for next session

- `/go` — execute the 6 task packets as a runtime falsification spike. Each task is a bounded evidence-collection step with a real-video acceptance criterion and a structured diagnostic where applicable.
- `/check` — after Gate 2 evidence is captured, session-verify the evidence matches the claims before claiming Gate 2 resolved.
- `/wiki` — after Gate 2 + Gate 3 outcomes, update the research concept with revision blocks (frontmatter, decision-context, recommendations, falsifier, confidence per the claim ledger).
- `/handoff` — create the Gate 3 handoff after Gate 2 settles and the operator authorizes.

## Changelog

| Date | Session | Action |
|------|---------|--------|
| 2026-08-10T07:20 | 019fea30... | created. Gate 2 prep. Inherits Gate 1 EXTRACT + IN_PAGE_SECONDARY decisions. 6 task packets defined. Operator-directed acceptance bar (structured diagnostic for stale rejection) added to G2-06. Ready for fresh session `/go`. |