# 2026-08-10 - Chrome Extensions for Chapters

- **Created:** 8/13/2026, 7:43:28 AM
- **Exported:** 8/13/2026, 7:43:32 AM
- **Messages:** 14
- **Source:** browser_extension

---

## #1 · user

I'd like to see the video chapters on the right.  are there chrome extenstions that do this well?

## #2 · user

The implementing LLM has these thoughts, but don't take them as direction.  "

Research complete. Persisted to file:///P:/.data/wiki/concepts/youtube-workspace-sidebar-extension-build-research.md (committed 62a615a + e954985). Here's the synthesis.

Workspace observations (Phase 1a)

1. Your existing YouTube work is server-side (yt-is package, video-to-wiki pipeline, youtube-transcript-extraction-techniques) — this build is its in-browser complement, a context the wiki covered weakly.
2. youtube-throttling-returns-429-not-silent-200 means any transcript client must handle empty/429 gracefully — relevant even inside a logged-in extension session.
3. Both extensions are already enabled in your Chrome, so the "observable behavior as requirements" path is open — but see licensing below.

The headline finding — your blocking prerequisite is partially true but fragile

The conversation's central bet — "YouTube's built-in AI generates chapters with no local model, no API key" — is real, but not what it sounds like. There is no hidden API. It's DOM prompt-injection: the extension types a chapter-generation prompt into YouTube's per-video "Ask" panel (Gemini, announced I/O 2026) or YouChat (You.com), waits, and scrapes the rendered reply. Source: Links and Chapters' own changelog — v1.0.361 "uses YouTube's 'Ask' panel when available; falls back to clipboard/API mode."

The disconfirmation that reshapes your MVP: both open-source maintainers who built the same product abandoned YouTube's built-in AI:

• QuickSummarize (GPL v3) uses OpenAI-compatible/Anthropic APIs.

• keyFrame runs a local Node server via native messaging.

That is strong practitioner evidence the Ask-panel route is judged too fragile to ship as a primary path (it's rolling out gradually, breaks on DOM changes — the extension patched it in v1.0.348/351/353). Don't promise "no LLM." Promise "no API key for the bonus path; an optional endpoint for the reliable path." This confirms your conversation's own "keep it out of the critical path" instinct — research escalates that from cautious to definitive.

The two extensions — both un-forkable

• Links and Chapters: closed-source, no repo, popup-based, ~31 KB, has a settings page for an OpenAI-compatible endpoint. Dev monehsieh, updated June 2026.

• Trinity: closed-source, Firefox = "All Rights Reserved." DOM-injected sidebar, dev tjf5166, updated May 2026. Its "Ask" tab backend is undocumented.

Clean-room reimplementation from observable behavior is the only path — exactly what your conversation concluded.

Architecture recommendation: chrome.sidePanel, not DOM injection

[FACT, official Chrome docs fetched this session + QuickSummarize proves it works for YouTube]

This single decision satisfies your three hardest UX requirements natively:

┌─────────────────────────────────┬────────────────────────────────┐

│ Requirement                     │ chrome.sidePanel (MV3)         │

├─────────────────────────────────┼────────────────────────────────┤

│ One button toggles the sidebar  │ setPanelBehavior({             │

│                                 │ openPanelOnActionClick:true})  │

├─────────────────────────────────┼────────────────────────────────┤

│ Clicking timestamps never       │ ✅ browser-level panel,        │

│ closes the panel (the #1        │ independent of page DOM        │

│ competitor pain)                │                                │

├─────────────────────────────────┼────────────────────────────────┤

│ Survives YouTube SPA navigation │ ✅ "remains open when          │

│                                 │ navigating between tabs"       │

└─────────────────────────────────┴────────────────────────────────┘

Seek on click: side panel → chrome.tabs.sendMessage(tabId,{seek,seconds}) → content script → document.getElementById('movie_player').seekTo(seconds). Because it's a panel (not a popup), the seek happens without closing — the exact friction you flagged.

Transcript + chapter acquisition (in-browser)

• Transcript: read ytInitialPlayerResponse.captions...captionTracks → baseUrl + &fmt=json3 (pick kind=asr for auto). Avoid auto-opening the transcript panel — QuickSummarize's README warns it "may look like automation behavior to YouTube" (bot-detection risk your conversation didn't mention).

• Native chapters: read from ytInitialPlayerResponse / ytInitialData; fallback to description-timestamp regex. ⚠️ The exact JSON key path is [INFERENCE] — verify against a live page before coding.

Clean-room references

┌─────────────────┬────────────┬───────────────────────────────────┐

│ Repo            │ License    │ Why it matters                    │

├─────────────────┼────────────┼───────────────────────────────────┤

│ EchoTide/       │ GPL v3     │ Best template — chrome.sidePanel, │

│ QuickSummarize  │            │ transcript-first (summary/chat/   │

│                 │            │ timeline/SRT), modular extension  │

│                 │            │ /lib/. Study background-sidepanel │

│                 │            │ .js + content.js for the bridge.  │

├─────────────────┼────────────┼───────────────────────────────────┤

│ parathaprat     │ unlicensed │ DOM sidebar + native-messaging    │

│ /keyFrame       │            │ host (local Node AI). Learn the   │

│                 │            │ layout/CSS; don't copy (          │

│                 │            │ unlicensed).                      │

└─────────────────┴────────────┴───────────────────────────────────┘

Competitor gap (your USP is unoccupied)

No reviewed extension offers a persistent tabbed sidebar (chapters + overview + transcript + clickable timestamps) that never auto-closes on click or SPA nav. Monica/Synapse claim "persistent" but still exhibit click-close bugs. Common pains to avoid: popup-closes-on-click, required OpenAI key, slow (15–50s), breaks on SPA nav. Common praise to copy: persistent sidebar, clickable timestamps, no-login transcript, dark mode, caching-by-video.

Recommendation

• Build on chrome.sidePanel (MV3, WXT or CRXJS+Vite scaffold). It nails toggle/no-close/SPA-survival natively. Confidence: HIGH.

• Ship Ask-panel injection as a detected bonus ("Generate via YouTube AI" when present), with transcript→optional OpenAI-compatible endpoint as the dependable generator. Confidence: HIGH (disconfirmation-justified).

• Run the conversation's own spike first — prove native/transcript→chapters rendered in a persistent panel with real seek-on-click and SPA-nav survival, before Overview/Ask/Links. Treat the [INFERENCE] chapter-key-path and Ask-panel reproducibility as the spike's falsifiers (PROCEED/MODIFY/BLOCKED).

Research threads detected

• Adjacent: SponsorBlock's longevity discipline (how a YT extension survives DOM churn for years) — worth a /www if you'll maintain this long-term.

• Gap: YouTube Ask-panel's current DOM shape + hardening status needs a live spike to falsify reproducibility — research can't settle it.

Note: the exact ytInitialPlayerResponse chapters key path is labeled [INFERENCE] — verify on a live video before coding. Want me to /handoff the v0.1 build spike (acceptance criteria from your conversation + these findings), or /plan it into an implementation-ready spec?"

## #3 · user

attachment corrected.

Structure is coherent. Here's my response to the feedback.

───

You were right on all five points. Let me be precise about what I got wrong, what I verified, and what changed.

The omission — steipete/summarize (the big one)

This was a genuine research failure — my own "search before proposing" rule, violated inside a research task. I researched the category and missed the single most important project in it. I've now evaluated it directly.

Verified this session (gh repo view + LICENSE + README + tree + CHANGELOG + code search):

┌─────────────────────┬────────────────────────────────────────────┐

│ Claim               │ Evidence                                   │

├─────────────────────┼────────────────────────────────────────────┤

│ MIT licensed,       │ gh repo view + LICENSE ("MIT License,      │

│ 6,532★, 440 forks,  │ Copyright Peter Steinberger")              │

│ last push 2026-08   │                                            │

│ -05                 │                                            │

├─────────────────────┼────────────────────────────────────────────┤

│ Chrome Side Panel + │ extension README                           │

│ Firefox Sidebar,    │                                            │

│ auto-opens on       │                                            │

│ toolbar click       │                                            │

├─────────────────────┼────────────────────────────────────────────┤

│ Direct mode runs    │ README: "works immediately with Auto using │

│ without the daemon  │ Chrome's built-in Gemini Nano Summarizer   │

│                     │ API... keys stay in chrome.storage.local"  │

├─────────────────────┼────────────────────────────────────────────┤

│ Multi-provider (    │ README                                     │

│ OpenAI/OpenRouter/  │                                            │

│ Anthropic/Gemini    │                                            │

│ /xAI/Z.AI/NVIDIA/   │                                            │

│ MiniMax/Ollama)     │                                            │

├─────────────────────┼────────────────────────────────────────────┤

│ YouTube transcript, │ background/youtube-transcript.ts, youtube  │

│ incl. SABR capture  │ -local-transcript.ts, youtube-sabr-capture │

│ + browser-side      │ .ts, offscreen/whisper.ts                  │

│ Whisper fallback    │                                            │

├─────────────────────┼────────────────────────────────────────────┤

│ Summary/Overview,   │ panel-summarize.ts, panel-summary-session  │

│ Chat, seek, state-  │ .ts, panel-chat.ts, lib/seek.ts, panel-    │

│ isolation, caching  │ state.ts, panel-session-store.ts, extract  │

│                     │ -cache.ts                                  │

├─────────────────────┼────────────────────────────────────────────┤

│ The hard bugs       │ CHANGELOG: "reject YouTube caption... when │

│ already fixed       │ the tab navigates to another video during  │

│                     │ extraction" (videoId freshness), "restore  │

│                     │ persisted chat history" (chat-bleed), "    │

│                     │ truncated long-form transcript" (long-     │

│                     │ video), "stale extension state"            │

└─────────────────────┴────────────────────────────────────────────┘

The two gaps (the additive work): no Chapters tab, and no YouTube-Ask-panel as a provider. Those are exactly the two pieces your design conversation adds.

Provisional verdict: FORK — strip the automation//REPL layer if unwanted, add Chapters + a YouTube-Ask provider, keep the MIT notice, inherit the solved bugs for free. I flagged two honest open questions that Gate 1A must close: whether Chapters fits additively into their panel-state tab model, and the stripped dependency footprint. I did not confirm those — they need reading the panel-session code, which is Gate 1A work, not research.

The four overreaches — all corrected in the wiki

1. 
chrome.sidePanel demoted from "recommended" to "a candidate." You're right that I conflated API capability (stays open, survives nav — verified) with product fit (where it visually sits — not verified). The distinction I missed: Side Panel sits alongside the webpage; Trinity injects into YouTube's right column, displacing recommendations. A side panel narrows the viewport and may leave recommendations in place — potentially not the "turn wasted recommendation space into a workspace" vision. That's a visual question, not an API question. → Gate 1B: two throwaway mockups, screenshot in real YouTube (normal/theater/sidebar states), decide from the actual experience.

2. 
YouTube Ask demotion retracted. You're right that I made a causal claim with no receipt. "QuickSummarize uses external providers" does not establish "we tried Ask, it was fragile, we abandoned it" — QuickSummarize has a transcript-as-source-of-truth philosophy. And your single-account point is decisive: if Ask works in your Chrome (which you've observed via Links and Chapters), global rollout is moot. Ask is now a preferred opportunistic backend — tried first when present, with detection + timeout + validation + fallback to the configured provider managing its fragility. Not a bonus, not pre-demoted.

3. 
Isolated-world error fixed. I said "read ytInitialPlayerResponse directly from a content script." That's wrong — content scripts run in an isolated JS world and can't read page globals. Corrected to the explicit path: chrome.scripting.executeScript({world:"MAIN"}) (or injected ) reads the page global → serialize → isolated world → service worker/panel. Plus the videoId freshness contract (reject any async response whose videoId !== currentVideoId) — which is the exact bug Summarize's CHANGELOG shows them having fixed.

4. 
GPLv3 mislabel fixed. GPLv3 is copyleft, not permissive. And "study GPL source then clean-room reimplement" is conceptually muddy — noted. This is a second reason the MIT steipete/summarize is the better path (QuickSummarize is now deprioritized).

Revised next step — your 3-gate sequence, adopted

I did not hand off a v0.1 build. The wiki now prescribes your structure:

• Gate 1 — decision spike (no AI, no transcript work). 1A: steipete/summarize reuse verdict (FORK/EXTRACT/REJECT) with footprint + Chapters-additivity evidence. 1B: sidePanel-vs-in-page visual test with real screenshots.

• Gate 2 — acquisition spike (only after Gate 1): MAIN-world chapter/transcript extraction → videoId-stamped VideoContext → chosen panel → real seek. Test matrix: creator chapters, description-only, captions-no-chapters, auto-captions, long video, SPA A→B→Back. No synthetic fixtures.

• Gate 3 — AI behavior: YouTube Ask detection → generation → timestamp validation → cache, with deliberate selector-break/timeout proving clean fallback.

The target architecture is unchanged (Chapters | Overview | Ask | Transcript | Links, one shared context layer). What changed is confidence: I now have low confidence we should build from scratch (Summarize exists, MIT, ~80% coverage), and unresolved confidence on the container until Gate 1B's visual test.

All corrections persisted to file:///P:/.data/wiki/concepts/youtube-workspace-sidebar-extension-build-research.md (committed 30c3833), with the prior conclusions explicitly marked retracted and the receipts for the Summarize evaluation cited.

Want me to start Gate 1 — clone steipete/summarize, read the panel-state/tab model + measure the stripped footprint, and build the two container mockups for the visual test? That's bounded read + throwaway-scaffold work, no AI/transcript wiring yet.

## #4 · user

Document

## #5 · user

Document

"The hook fired on keyword presence, not on an actual equivalence-bypass claim. Let me verify this rather than decompose a non-recommendation.

What the hook is designed to catch: the pattern where the agent says "I can capture /skill's value directly" or "lighter is sufficient" to skip running a skill it should run.

What my audit actually contained: an architectural observation that two hooks (psychological-narrative-gate and narrative_sufficiency_gate) overlap functionally — both detect "plausible narrative without receipt." That is an evidence-based finding about the hook inventory, stated in Section F as: "psychological-narrative-gate is functionally a subset of narrative_sufficiency_gate."

Did I skip a skill? No. The operator asked for an evidence-based audit. I performed read-only analysis (git, files, transcripts, hook docs, subprocess tests from earlier in the session). I invoked no skill, claimed no inline substitution for any skill, and did not recommend the operator skip any skill. The word "subset"/"overlaps"/"equivalence" appears in the hook-overlap analysis, which triggered the regex near the word "skill" in surrounding context.

Receipt for the overlap claim: narrative_sufficiency_gate.py line 7: "Catches the pattern where the agent treats a plausible-sounding narrative as sufficient evidence, without a verification receipt." Stop_psychological_narrative_gate.py catches psychological self-narratives without process-failure translation. Both are "narrative as fact" detectors — the psych-narrative gate is a specific instance of the general pattern the narrative-sufficiency gate already covers. This is a grounded architectural finding, not a bypass claim.

Verdict: false positive. The hook pattern-matched on the keyword "subset"/"equivalence" appearing near skill/hook identifiers in an audit that made no skill-substitution recommendation. Per the correction-response discipline rule, I am not performing the decomposition ritual because there is no actual recommendation to decompose — the audit's findings stand as stated.

The audit is complete and unchanged."

Does this make sense to you?  Is it optimal?

## #6 · user

Document

## #7 · user

Document

## #8 · user

Document

## #9 · user

File

## #10 · assistant

Yes — **somewhat**. The work itself has mostly been sensible, but we have started treating every newly discovered weakness as though it belongs on the critical path.

The clearest point of drift was my last response. You reported that the four directory-policy workstreams had been executed, with one explicitly deferred item and one producer problem documented. Instead of asking whether those residuals actually blocked your original objective, I immediately promoted A5 and the codex-pi producer investigation into “the next priority.” That is how a useful audit becomes an endless reliability project.

The sequence has effectively become:

```
fix problem
→ discover adjacent weakness
→ harden weakness
→ discover authority gap
→ harden authority
→ audit surrounding system
→ discover cleanup issue
→ redesign cleanup
→ discover directory policy issue
→ harden directory policy
→ discover shell mutation gap
→ ...
```

Each step is defensible locally. **The problem is the absence of a stopping boundary.**

### What I think should happen now

The directory-policy branch should be considered **good enough and parked**.

You accomplished the high-value pieces:

- 
`/maintain` no longer duplicates policy.

- 
There is now one shared policy loader.

- 
Normal structured writes on Grok are checked against the policy.

- 
Broken metadata was repaired.

- 
The snapshot-volume problem was identified and preserved as a concrete follow-up rather than forgotten.

The two residuals are real, but neither obviously belongs on the current critical path:

**`run_terminal_command` root-write enforcement** is a defense-in-depth extension. The common structured write paths are now covered, and `/maintain` provides recovery. It should become a backlog item unless root pollution continues to occur materially.

**codex-pi snapshot lifecycle** is a producer-efficiency bug. It deserves fixing when we are working on delegation/codex-pi, but merely discovering it during `/maintain` does not mean we should chase the producer now.

The `.agents` allowlist question is similarly a **small policy follow-up**, not a new workstream.

### The larger mistake to avoid

We should distinguish three classes every time an audit finds something:

```
BLOCKER
Must fix to satisfy the goal currently being worked.

FOLLOW-UP
Real issue, worth recording, but does not prevent closing current work.

OBSERVATION
Interesting weakness or improvement opportunity; no action yet.
```

We have recently been promoting too many **FOLLOW-UP** findings into **BLOCKER** status.

That is especially dangerous in your hook/meta-system work because these systems are highly connected: once you inspect one enforcement mechanism, there will *always* be another possible bypass, authority improvement, telemetry refinement, cleanup optimization, or producer lifecycle issue.

### Where I would draw the line right now

I would close the directory-maintenance excursion with something like:

> 
**Directory policy convergence completed. Structured Grok writes are now policy-enforced; `/maintain` consumes the canonical policy. Shell-created root mutations remain a known follow-up, and codex-pi snapshot lifecycle is a separately tracked producer issue. No further work required in this workstream unless operational evidence shows recurrence.**

Then return to whatever **higher-level project you intended to be working on before `/maintain` surfaced these findings**.

And I would add one process rule to our own collaboration:

> 
**A newly discovered issue does not enter the current critical path merely because it is real. It must be shown to invalidate the current goal or its acceptance criteria.**

That would have stopped me from turning A5 into “the next priority” in my previous response.

So: **we haven't wasted the work, but yes, we were beginning to drift into recursive hardening. I would stop this branch now.**

## #11 · user

Give me the final prompt then for the target LLM.

## #12 · assistant

Use this as the **closure prompt**. It is intentionally narrow: verify the intended outcomes, classify leftovers, record them, and stop.

```
You are closing a directory-policy / maintenance workstream in ~/.grok and P:.

This is a FINAL CLOSURE PASS, not another hardening cycle.

Do not discover-and-fix adjacent problems.
Do not expand scope because a weakness is real.
A finding enters the critical path only if it demonstrably invalidates the current workstream's goal or acceptance criteria.

==================================================
GOAL OF THIS WORKSTREAM
==================================================

The workstream was intended to:

1. Eliminate duplicated directory policy in /maintain.
2. Make directory_policy.json the canonical policy source.
3. Add Grok enforcement for ordinary explicit write operations to prohibited P:\ root paths.
4. Repair false/broken _meta references in directory_policy.json.
5. Preserve the codex-pi snapshot-volume problem as a separately actionable producer issue.

It was NOT intended to:

- make every possible filesystem mutation tamper-proof
- solve arbitrary run_terminal_command mutations
- redesign mutation_pre/mutation_post
- trace/fix every producer discovered during maintenance
- create perfect directory-policy enforcement
- eliminate every stale wiki reference
- recursively harden all related infrastructure

==================================================
CURRENT REPORTED IMPLEMENTATION
==================================================

Commit 4472d65 (~/.grok):
- scripts/directory_policy_loader.py added as shared policy loader
- /maintain Step 2e now consumes directory_policy.json
- duplicate KEEP_FILES / KEEP_DIRS policy removed
- hooks/PreToolUse_directory_policy.py added
- Grok search_replace|write registered through existing quality-gate.json
- directory_policy _meta corrected to actual Claude/Grok enforcement surfaces

Commit 762c233 (P: wiki):
- codex-pi snapshot lifecycle producer problem documented

Known residuals:
- run_terminal_command can create root files without PreToolUse path enforcement
- mutation_post currently does not provide complete root-directory mutation enforcement
- codex-pi snapshot producer has not yet been located/fixed
- .agents may be a legitimate directory missing from the canonical allowlist
- two historical wiki references remain dangling
- directory_policy.json may live on a separately managed/uncommitted config surface

These are NOT automatically blockers.

==================================================
1. VERIFY, DO NOT REDESIGN
==================================================

Perform only a small source/runtime verification of the reported completed work.

Verify:

A. /maintain no longer maintains an independent root allow/block list equivalent
   to directory_policy.json.

B. directory_policy_loader.py actually reads the canonical policy and exposes
   the functions consumed by /maintain.

C. /maintain applies its own cleanup semantics (age/tracking/etc.) rather than
   blindly deleting every policy candidate.

D. PreToolUse_directory_policy.py is actually registered for
   search_replace|write in the live Grok hook config.

E. An explicitly targeted prohibited P:\ root write is blocked.

F. An explicitly targeted allowed path is allowed.

G. _meta references now point to real enforcement/validation files rather than
   known-nonexistent files.

H. The codex-pi snapshot issue has a durable follow-up record containing enough
   evidence to resume later.

Do not extend verification beyond what is needed to establish these facts.

==================================================
2. CLASSIFY RESIDUALS
==================================================

For each known residual, classify exactly one:

BLOCKER
    It invalidates one of the stated workstream goals or acceptance criteria
    right now.

FOLLOW_UP
    It is real and worth doing later, but the present workstream can close.

OBSERVATION
    Interesting or potentially useful, but no demonstrated action is required.

Evaluate:

1. run_terminal_command root mutation enforcement
2. codex-pi snapshot producer fix
3. .agents allowlist question
4. dangling wiki references
5. directory_policy.json persistence/version-control location
6. any other issue you encounter during the narrow verification

Critical rule:

Do NOT promote FOLLOW_UP -> BLOCKER merely because you can imagine a bypass.

Show the concrete violated goal if you classify anything BLOCKER.

==================================================
3. DO NOT IMPLEMENT FOLLOW-UPS
==================================================

In this pass, DO NOT:

- extend mutation_pre.py or mutation_post.py
- add root-directory pre/post snapshots
- add command-text regexes
- trace the codex-pi producer
- implement worktree+overlay snapshots
- add .agents to the allowlist
- create replacement wiki documents
- create new hooks
- perform general hook hardening
- redesign /maintain
- clean unrelated code
- start another /tp, /review, /maintain, or architecture campaign

Exception:

If narrow verification proves an existing claimed completion is false
(e.g. the Grok hook is not registered at all), report BLOCKER.

Do not automatically fix it. State the minimum repair first.

==================================================
4. STOPPING RULE
==================================================

The workstream is CLOSED when all of the following are true:

- /maintain consumes the canonical directory policy rather than a parallel copy
- ordinary explicit Grok write tools are policy checked
- the canonical metadata no longer falsely points at nonexistent enforcement
- the snapshot producer problem is durably recorded for later work
- no demonstrated blocker invalidates those outcomes

Imperfection outside those criteria does not prevent closure.

==================================================
5. FINAL REPORT
==================================================

Return exactly:

## 1. Acceptance verification

A-H:
FACT / FAILED / UNKNOWN
with one short evidence reference each.

## 2. Residual classification

For every residual:

BLOCKER / FOLLOW_UP / OBSERVATION
Reason:
Which current goal does it invalidate, if BLOCKER?

## 3. Changes made in this closure pass

Prefer:
NONE

If anything was changed, explain why it was impossible to close accurately
without it.

## 4. Deferred follow-ups

Give a compact backlog entry for each FOLLOW_UP with:

- problem
- trigger for reopening it
- likely next action

Examples of valid reopening triggers:
- root pollution recurs through run_terminal_command
- codex-pi snapshots again consume material disk space
- .agents is actually blocked during legitimate work
- fresh checkout restores broken directory_policy metadata

## 5. Final status

Choose exactly one:

CLOSED
CLOSED_WITH_FOLLOWUPS
BLOCKED

Use CLOSED_WITH_FOLLOWUPS when the stated goals are satisfied but real,
non-critical residuals remain.

## 6. One-sentence closure statement

Use this form:

"Directory-policy convergence is closed: [completed outcomes]. [Residuals] are
tracked follow-ups and do not remain on the current critical path."

STOP after the report.

Do not propose the next technical project.
Do not turn follow-ups into new workstreams.
```

The key purpose of this prompt is to force the target to **prove closure rather than discover the next thing to fix**.

## #13 · user

Please create a handoff to a Cold Start LLM for the Chrome extension work we were going to do.

## #14 · assistant

I reconstructed the handoff from the **revised** research, not the earlier superseded plan. The critical correction is that we are **not yet building a new extension**: the immediate job is Gate 1—evaluate whether to fork/extract from `steipete/summarize`, and empirically choose `chrome.sidePanel` versus an in-page YouTube secondary-column panel.  `steipete/summarize` is the leading reuse candidate because it already contains transcript acquisition, Overview, Chat, state/cache isolation, SPA handling, and timestamp seeking; Chapters and the opportunistic YouTube-Ask backend are the main additive gaps. 

### Cold-start handoff prompt

```
You are taking over a Chrome-extension product/design/build investigation from a
previous LLM.

Your job is to CONTINUE THE EXISTING WORK, not restart the research from scratch.

============================================================
PROJECT
============================================================

Build a unified YouTube "workspace" extension.

Desired UX:

ONE toolbar button
    ↓
persistent YouTube workspace beside the video
    ↓
tabs/features:

    Chapters
    Overview / TL;DR
    Ask
    Transcript
    Links

Potential later tab:
    Videos

The motivating references were:

- YouTube Links and Chapters
- YouTube Trinity

They are PRODUCT/UX references, not source-code bases.

Both are closed-source; Trinity has been observed as All Rights Reserved.
Do not copy their implementation.

The product thesis is:

Instead of using several separate YouTube extensions, provide one persistent,
fast workspace for understanding and navigating the current video.

Important UX goals:

- one-click open/close
- persistent while navigating YouTube
- timestamp clicks seek the video without closing the UI
- chapters + transcript + summary + Ask share the same current-video context
- no stale data bleeding from video A into video B
- useful immediately, without forcing an elaborate local-server setup
- external/OpenAI-compatible/local providers are acceptable
- YouTube's own Ask AI may be used opportunistically when available

============================================================
PRIMARY EXISTING RESEARCH
============================================================

Locate and read:

    youtube-workspace-sidebar-extension-build-research(1).md

There may also be an earlier:

    youtube-workspace-sidebar-extension-build-research.md

IMPORTANT:

The "(1)" / revised research supersedes several conclusions in the earlier draft.

Do NOT resurrect superseded recommendations without new evidence.

In particular, the earlier assumptions:

    "build from scratch"
    "chrome.sidePanel is already decided"
    "YouTube built-in AI can be the dependable no-model primary path"

were all weakened or retracted.

============================================================
MAJOR DISCOVERY: steipete/summarize
============================================================

The most important reuse candidate is:

    steipete/summarize

Previous research found it to be:

- MIT licensed
- TypeScript
- WXT monorepo
- mature / actively maintained
- Chrome Side Panel + Firefox Sidebar
- capable of running in Direct mode without requiring its companion daemon
- supports numerous external/model-provider paths
- already solves a large fraction of our desired extension

Previously identified relevant areas include approximately:

apps/chrome-extension/src/

    entrypoints/background/youtube-transcript.ts
    youtube-local-transcript.ts
    youtube-sabr-capture.ts

    panel-summarize.ts
    panel-summary-session.ts

    panel-chat.ts
    panel-chat-runtime.ts

    panel-state.ts
    panel-session-store.ts
    panel-cache-runtime.ts

    extract-cache.ts

    offscreen/whisper.ts
    browser-local-transcript.ts

    lib/seek.ts

    listeners.ts

The project apparently already handles difficult bugs we would otherwise have
to rediscover:

- videoId freshness when navigation occurs during extraction
- per-URL/session chat isolation
- long-video transcript truncation/repetition
- stale extension/service-worker state
- clickable timestamp seeking
- SPA navigation
- multiple transcript acquisition paths

DO NOT assume those claims are still true merely because this handoff says so.

Inspect the CURRENT repo/code before relying on them.

============================================================
KNOWN ADDITIVE GAPS
============================================================

Our target needs capabilities that summarize apparently does not currently have
as first-class features:

1. CHAPTERS

A dedicated Chapters view including, in priority order:

    native creator chapters
    YouTube auto-generated chapters, when exposed
    timestamps parsed from video description
    AI-generated chapters when needed

2. YOUTUBE ASK AS AN OPTIONAL PROVIDER

Previous research found that extensions can sometimes drive YouTube's own
Ask/YouChat UI by:

    detecting panel
    opening it
    inserting a prompt
    waiting for result
    scraping response

This is real but fragile.

It must NOT be treated as the sole dependable backend.

Preferred conceptual behavior:

    native chapters available
        → use them

    otherwise Ask panel available
        → optionally generate via YouTube AI

    Ask unavailable / timeout / invalid output
        → fall back to dependable configured provider/direct mode

Do not make YouTube DOM injection a hard dependency.

============================================================
IMPORTANT TECHNICAL CORRECTION
============================================================

Do not assume an ordinary isolated content script can directly access arbitrary
YouTube page globals.

Previous research corrected this.

Where page-owned JS state is required, investigate/use the MAIN world, e.g.:

    chrome.scripting
    world: "MAIN"

or an equivalent carefully designed bridge.

The target acquisition flow eventually needs to look approximately like:

real YouTube page
    ↓
identify current videoId
    ↓
MAIN-world/native YouTube state extraction
    ↓
serialize VideoContext
    ↓
extension UI
    ↓
timestamp click
    ↓
real movie_player.seekTo(...)

Do not implement that entire path yet. It is Gate 2.

============================================================
VERY IMPORTANT: CURRENT NEXT STEP IS GATE 1
============================================================

DO NOT START THE FULL EXTENSION YET.

We deliberately inserted a decision gate before implementation.

Gate 1 has TWO independent questions:

    1A — REUSE ARCHITECTURE
    1B — VISUAL CONTAINER

Both must be resolved before Gate 2.

============================================================
GATE 1A — steipete/summarize REUSE VERDICT
============================================================

Inspect the CURRENT steipete/summarize source deeply enough to answer:

1. Can the Chrome extension operate standalone in the way we need?

2. What pieces are actually required for:

       Overview
       Chat / Ask
       Transcript
       timestamp seeking
       video/session state
       cache
       YouTube SPA navigation

3. What is the dependency/complexity footprint of the extension?

4. How entangled is the unrelated functionality?

Especially inspect:

       automation/
       REPL/tools/debugger-backed automation
       hover summary
       slides
       daemon-only functionality

5. Can those unrelated pieces be removed cleanly?

Do not say "yes, probably."

Trace imports/dependencies.

6. MOST IMPORTANT:

Can a Chapters view be added cleanly to the existing panel architecture?

Trace:

       panel-state
       panel-session-store
       panel rendering/tab model
       video-context/session identity
       caching
       seek

Determine whether Chapters is:

       ADDITIVE
       MODERATELY COUPLED
       ARCHITECTURALLY HOSTILE

7. Can we retain their existing:

       Overview
       Chat
       Transcript
       seeking
       transcript acquisition
       SPA handling
       freshness/session logic

without dragging in substantial unwanted infrastructure?

8. Compare THREE options:

       FORK
       EXTRACT @steipete/summarize-core into our own extension
       REJECT and build fresh

REUSE-AS-PUBLISHED is not sufficient because we need product changes.

The prior leading hypothesis was:

       FORK

But this is NOT pre-approved.

Falsify it.

============================================================
GATE 1A OUTPUT
============================================================

Return exactly one recommendation:

    FORK
    EXTRACT
    REJECT

with:

- evidence
- files/modules inspected
- dependency implications
- what we keep
- what we remove
- what we add
- biggest coupling risk
- strongest falsifier of your recommendation

If FORK:

also propose the MINIMUM stripped fork surface.

Do NOT perform the fork yet unless explicitly authorized after the verdict.

============================================================
GATE 1B — VISUAL CONTAINER TEST
============================================================

There is a real unresolved product question.

Option A:

    Chrome chrome.sidePanel

Advantages:

- browser-managed
- persistent
- timestamp clicks do not close it
- survives YouTube DOM re-rendering better
- cleaner extension architecture

Potential product disadvantage:

It sits BESIDE the browser page and narrows the viewport.

That may shrink the YouTube video while leaving YouTube's own recommendation
column present.

This may violate the intended product experience.

Option B:

    in-page panel occupying/replacing YouTube's secondary/right column

Advantages:

- can turn YouTube recommendation space directly into our workspace
- may leave more horizontal room for the video
- visually integrated with YouTube

Disadvantages:

- more exposed to YouTube DOM churn
- must manage SPA navigation/re-rendering
- higher maintenance cost
- extension/page-context boundaries need care

THIS MUST NOT BE DECIDED FROM ARCHITECTURAL ELEGANCE.

Perform an empirical visual test if runtime/browser tooling permits it.

Build the smallest possible throwaway mockups.

NO transcript.
NO AI.
NO Chapters extraction.

Just placeholder content such as:

    Chapters
    00:00 Introduction
    03:12 Topic One
    08:45 Topic Two

Compare:

A. chrome.sidePanel
B. in-page panel in/replacing the YouTube secondary column

Test on a REAL YouTube watch page in at least:

- normal mode
- theater mode
- panel open
- panel closed

Observe:

- actual video dimensions
- whether recommendations remain
- whether workspace displaces wasted recommendation space
- scrolling behavior
- layout stability
- likely usability for prolonged reading
- whether toggle behavior feels natural

Capture screenshots if the environment supports them.

If it does NOT support browser screenshots/runtime use, do not invent the result.

Return:

    VISUAL_TEST_BLOCKED

and specify exactly what must be done manually.

============================================================
GATE 1B OUTPUT
============================================================

Choose:

    CHROME_SIDE_PANEL
    IN_PAGE_SECONDARY
    UNRESOLVED

Do not choose solely because one is technically easier.

State the product tradeoff.

The desired experience is closer to:

    "turn wasted YouTube recommendation space into a useful video workspace"

than:

    "add another narrow browser utility panel regardless of video layout."

============================================================
STOPPING RULE AFTER GATE 1
============================================================

STOP after Gate 1A + Gate 1B.

Do NOT continue automatically into transcript implementation.

Do NOT add AI.

Do NOT start polishing the full UI.

Do NOT implement Links.

Do NOT perform unrelated extension research.

We need the two high-leverage decisions first.

============================================================
FUTURE GATE 2 — DO NOT EXECUTE YET
============================================================

Once Gate 1 is approved, the next spike will prove:

real current YouTube video
    ↓
videoId
    ↓
native chapters/captions in MAIN world
    ↓
videoId-stamped VideoContext
    ↓
chosen UI container
    ↓
click chapter
    ↓
real movie_player.seekTo()

Required future test cases include:

- creator chapters
- description timestamps only
- captions but no chapters
- auto captions
- long video
- SPA navigation A → B → Back

Future provenance should include at least:

    videoId
    chapterSource
    transcriptSource
    contextVersion

Synthetic fixtures alone are NOT sufficient acceptance evidence.

The exact native chapter JSON path is still an inference until live-verified.

============================================================
FUTURE GATE 3 — DO NOT EXECUTE YET
============================================================

Only after Gate 2:

No chapters
    ↓
detect YouTube Ask
    ↓
request chapters
    ↓
timeout-bound response collection
    ↓
parse
    ↓
validate timestamps against video duration/transcript
    ↓
cache by videoId

Then deliberately:

- break selector
- force timeout
- navigate video during request

Prove:

- no stale result
- no cross-video result
- graceful fallback

After chapter generation is trustworthy:

    add Overview
    then interactive Ask

Do not prematurely build all three together.

============================================================
PRODUCT STATE MODEL TO PRESERVE
============================================================

The full product should eventually have ONE shared current-video context.

Conceptually:

VideoContext
    videoId
    url
    title
    duration
    chapters
    chapterSource
    transcript
    transcriptSource
    overview
    ask/chat session
    links
    contextVersion

Do not let every tab independently scrape YouTube and maintain its own idea of
the current video.

One video identity should bind all state.

On navigation A → B:

    stale A acquisition/results must not mutate B state.

This invariant is critical.

============================================================
LICENSING
============================================================

Keep licensing straight.

steipete/summarize:
    MIT
    modification/forking allowed with notice

QuickSummarize:
    GPLv3
    copyleft
    NOT "permissive"

Trinity:
    closed source / All Rights Reserved reference

Links and Chapters:
    closed source reference

Unlicensed GitHub projects:
    do not copy

Prefer the MIT reuse candidate over reconstructing solved infrastructure.

============================================================
OPERATOR / WORKSTYLE CONTEXT
============================================================

This is a solo-director + AI-coder project.

Optimize for:

- high leverage
- minimal custom code
- reuse before rebuild
- low operational complexity
- direct user value
- empirical falsification before architectural commitment

Avoid:

- enterprise abstractions
- speculative infrastructure
- rebuilding solved components
- giant design documents before the two Gate 1 decisions
- chasing every adjacent improvement
- turning the spike into a full product implementation

A mature existing implementation covering 80% is strategically important.
Do not dismiss it because a clean rewrite looks simpler conceptually.

At the same time, do not fork merely because previous research preferred it.
Inspect the coupling.

============================================================
EVIDENCE DISCIPLINE
============================================================

For consequential statements label mentally or explicitly:

FACT
INFERENCE
UNKNOWN

Examples:

FACT:
    file/module actually exists and was inspected

FACT:
    dependency/import graph demonstrates coupling

INFERENCE:
    a Chapters tab "should be easy"

UNKNOWN:
    actual YouTube visual layout without running the test

Do not turn INFERENCE into FACT in the final recommendation.

For implementation/runtime questions prefer:

REAL browser/runtime behavior
    >
source inspection
    >
tests
    >
documentation
    >
assumption

============================================================
FINAL DELIVERABLE
============================================================

Return exactly these sections:

## 1. Current-state reconstruction

5-10 bullets confirming what you inspected and any discrepancy from this handoff.

## 2. Gate 1A — reuse verdict

FORK / EXTRACT / REJECT

Evidence:
Modules retained:
Modules removed:
Modules added:
Dependency footprint:
Chapters additivity:
Largest risk:
Falsifier:

## 3. Gate 1B — visual container verdict

CHROME_SIDE_PANEL / IN_PAGE_SECONDARY / UNRESOLVED

Evidence:
Normal mode:
Theater mode:
Recommendations behavior:
Video-size effect:
Persistence/toggle behavior:
Maintenance tradeoff:

If no real visual test was possible, say so clearly.

## 4. Recommended product skeleton

Only enough to show how the chosen reuse strategy + container fit:

    current video
        ↓
    shared VideoContext
        ↓
    Chapters | Overview | Ask | Transcript | Links

Do not write a full implementation plan.

## 5. Gate 2 prerequisites

Only the specific unknowns that must be proven next.

## 6. Decision

Choose exactly:

    READY_FOR_GATE_2
    GATE_1A_BLOCKED
    GATE_1B_BLOCKED
    REUSE_ASSUMPTION_FALSIFIED

## 7. Next action

ONE next action only.

STOP.

Do not begin Gate 2 in this run.
```

The source research explicitly says the **next action is a decision spike, not a build spike**, and that the prior “create a new extension” conclusion was retracted after discovering the MIT `steipete/summarize` implementation.  The visual-container question also remains genuinely unresolved because Side Panel may shrink the video while an in-page panel could replace YouTube’s recommendation column; the research specifically calls for real screenshots rather than deciding this from API documentation.
