---
title: "Playwright connectOverCDP was not ruled out — only Playwright wrappers were"
slug: playwright-connectovercdp-not-ruled-out
created: 2026-08-09
source: session-20260809
tags: [playwright, puppeteer, chrome-devtools-mcp, connectovercdp, browser-automation, model-web, abstraction-level, alternatives-evaluation, decision-integrity]
summary: >
  The wiki concept [[cdp-network-interception-and-sse-capture-for-llm-chat]]
  rejected "Playwright" as architecturally mismatched for the authenticated
  browser-LLM bridge use case. That rejection was at the wrong abstraction
  level: it tested wrappers built on Playwright (agent-browser, BrowserPilot)
  that launch their own browsers, not Playwright's own connectOverCDP() method,
  which attaches to an existing authenticated Chrome session the same way
  --autoConnect does. Playwright remains a viable alternative adapter for
  /model-web. The deeper finding: the decision "Puppeteer vs Playwright" is
  itself the wrong frame — the correct solution unit is "owned authenticated
  browser sessions with pluggable adapters," not "pick one automation library."
agent: grok
host: grok
cognitive_load: 3
verification: multi-source-verified
sources:
  - "https://playwright.dev/docs/api/class-browsertype#browser-type-connect-over-cdp (Playwright connectOverCDP docs, verified 2026-08-09 via codex lens)"
  - "P:/tmp/tp-dispatch-019fe7e9-cd0/tp-codex-puppeteer-context.md (codex GPT-5.6 critique, session 019fe7e9)"
  - "P:/tmp/tp-dispatch-019fe7e9-cd0/console_5cf32bda-tp-agy-puppeteer-result.md (agy Gemini critique, session 019fe7e9)"
  - "P:/.data/wiki/concepts/cdp-network-interception-and-sse-capture-for-llm-chat.md (existing concept being refined)"
relations:
  - target: wiki/concepts/cdp-network-interception-and-sse-capture-for-llm-chat.md
    type: refines
  - target: wiki/concepts/chrome-autoconnect-for-authenticated-cdp-sessions.md
    type: related
  - target: wiki/concepts/browser-automation-failure-modes-llm-chat.md
    type: related
  - target: wiki/concepts/replacement-before-investigation-pattern.md
    type: instance-of
  - target: wiki/concepts/solution-unit-validation-before-build.md
    type: instance-of
---

# Playwright connectOverCDP was not ruled out — only Playwright wrappers were

## Decision context

**The problem:** during a `/tp` critique of whether Puppeteer (via
chrome-devtools-mcp) is the right browser-automation foundation for
`/model-web`, the codex lens (GPT-5.6) caught that the existing wiki
concept [[cdp-network-interception-and-sse-capture-for-llm-chat]] had
rejected "Playwright" as architecturally mismatched — but the rejection
was based on testing **wrappers built on Playwright** (agent-browser,
BrowserPilot), not Playwright itself. Those wrappers launch their own
browser and cannot attach to an authenticated Chrome session. Playwright's
own `connectOverCDP()` method does exactly that attachment.

This is the same failure class as [[replacement-before-investigation-pattern]]:
a tool was rejected based on a misunderstanding of what was tested, and
the rejection propagated into a wiki concept that future sessions treat
as authoritative. The operator's question "is Puppeteer a good choice?"
was partly pre-answered by a wiki concept that hadn't actually evaluated
the leading alternative.

## Key findings

### What the existing concept actually rejected

[[cdp-network-interception-and-sse-capture-for-llm-chat]] §5 assessed
three tools and found all three architecturally mismatched:

| Tool | Why rejected | Abstraction level |
|---|---|---|
| **agent-browser** (vercel-labs) | "Launches own browser. Can't connect to authenticated Chrome." | Rust CLI *built on* Playwright — not Playwright itself |
| **BrowserPilot** | "Complete alternative product. Launches own browser." | Scraper *using a Playwright fork* (Patchright) |
| **OpenClaw** | "Relay designed for OpenClaw's own agent." | AI assistant runtime, not an automation library |

The section then concludes "Playwright-based tools can't connect to our
authenticated Chrome." But none of these ARE Playwright — they are
products that happen to use Playwright as an engine. Playwright the
library has `connectOverCDP()` for exactly this purpose.

### What Playwright's connectOverCDP actually does

Per Playwright's official docs (verified via codex lens 2026-08-09):

- `browserType.connectOverCDP(endpointURL)` attaches to an existing
  Chromium browser running with remote debugging enabled
- It supports a `noDefaults` option explicitly intended for attaching
  to a user's daily-driver browser without injecting Playwright's
  default automation flags
- This is the Playwright equivalent of chrome-devtools-mcp's
  `--autoConnect` — same mechanism, same CDP transport

**The wiki's own falsifier** (line 210 of the existing concept) says the
verdict changes if "agent-browser or OpenClaw add `connectOverCDP()`
support." That falsifier missed that **Playwright itself already has it** —
the falsifier condition was already met by a tool the concept didn't
test.

### Both /tp lenses converged on the deeper framing error

The `/tp` critique (3-lens panel: spawn + codex + agy; 2/3 returned
substantive, spawn lost to result-capture) produced independent convergence:

- **codex (GPT-5.6, REVISE):** "The question is too library-centric. The
  real architecture has at least four decisions: authenticated-browser
  attachment, page interaction/evaluation, streamed-response capture,
  and model-specific orchestration. Replacing one library does not
  automatically solve target routing, SSE correlation, or concurrent-tab
  safety." Also: "The unexamined premise is that the wrapper's
  architecture and the underlying automation library are interchangeable.
  They are not."
- **agy (Gemini 3.5, REVISE):** "The proposal operates at too low an
  abstraction level... A higher-level abstraction should encapsulate
  these low-level interactions." Recommended a general-purpose
  browser-driver framework rather than hardcoding /model-web to one
  library.

2/2 lens convergence on REVISE with the same reframe is high-confidence.
The verdict is not "switch to Playwright" — it is "build a browser-session
interface with pluggable adapters, where Puppeteer is today's adapter
and Playwright-over-CDP is a testable alternative behind the same seam."

### A second finding surfaced: autoConnect to default profile is a security exposure

Both lenses independently flagged that connecting chrome-devtools-mcp to
the operator's everyday default Chrome profile exposes **all** open tabs
(not just LLM tabs) to any MCP client on the debugging port. Codex cited
the official chrome-devtools-mcp docs' own warning. The safer architecture
is a **dedicated authenticated profile** (which already exists at
`P:/.data/chrome-llm-profile`) or a broker with strict target ownership.

This is separable from the Playwright finding but was surfaced by the same
critique. The current session configured `--autoConnect` to the default
profile — that should be revised toward the dedicated profile.

## What this means for our workspace

1. **The existing wiki concept needs a correction.** §5's conclusion
   overreached: it rejected wrappers, not the library. The concept's
   falsifier condition (line 210) is already satisfied by Playwright's
   own `connectOverCDP`. Future sessions reading that concept as
   authoritative will inherit the wrong-level rejection. Section §5
   should be updated to distinguish "Playwright wrappers that launch
   their own browser" from "Playwright's connectOverCDP, which attaches
   to existing sessions."

2. **Do NOT migrate /model-web to Playwright based on this finding alone.**
   Both lenses agreed: no workload evidence justifies migration. The
   existing Puppeteer adapter works for the current use case. Playwright
   is a *testable alternative*, not a proven replacement. Any migration
   claim requires a workload benchmark across the supported-site matrix.

3. **The correct architectural move is a browser-session interface, not
   a library swap.** Build a narrow seam (`BrowserSession` /
   `WebLLMDriver`) that makes Puppeteer, Playwright-over-CDP, and native
   CDP interchangeable behind it. Then `/model-web` depends on the
   interface, not on a specific library. This is
   [[solution-unit-validation-before-build]] applied: the proposed unit
   ("pick one library") was wrong; the correct unit is "pluggable
   adapters behind a session interface."

4. **Move off autoConnect to the default profile.** The dedicated LLM
   profile at `P:/.data/chrome-llm-profile` already exists. Connecting
   there instead of the everyday profile limits exposure to LLM tabs
   only. This is the higher-ROI security fix from this session.

5. **The pattern generalizes: abstraction-level checking at write time.**
   This is the second instance (after the "overnight controller" case in
   [[solution-unit-validation-before-build]]) where a wiki concept
   rejected something at the wrong level and a later `/tp` caught it.
   The structural fix: when writing a wiki concept that rejects an
   alternative, explicitly state the abstraction level ("we reject X
   itself" vs "we reject a product built on X"). The
   [[decision-integrity-in-research-blocking-unknowns-and-decision-red-teaming]]
   contract's `best_reuse_candidate` field should distinguish this too.

## Falsifier

This concept (and the correction) is wrong if:
- **Playwright's connectOverCDP does not actually work on Chrome 151+**
  with authenticated sessions in the same reliable way `--autoConnect`
  does. This is `[UNTESTED]` — codex verified the docs, not the runtime.
  A spike test on this host would resolve it. If connectOverCDP fails
  where autoConnect succeeds, the original rejection stands (but for a
  different reason than the one documented).
- **A workload benchmark shows Puppeteer materially outperforms
  Playwright-over-CDP** on the /model-web site matrix (attach reliability,
  evaluate_script success, SSE capture, concurrency). Then Playwright
  stays ruled out — but on measured evidence, not on the wrong-level
  rejection.
- **The browser-session-interface abstraction adds complexity without
  enabling actual adapter swaps.** If Puppeteer and Playwright-over-CDP
  diverge in ways the interface cannot paper over (e.g., different
  target-ownership semantics, different concurrency models), the seam
  is premature and the direct-library approach is correct.

## Receipts

- **codex critique (15 tool calls, 6 tool-grounded findings):**
  `P:/tmp/tp-dispatch-019fe7e9-cd0/tp-codex-puppeteer-context.md` —
  caught the abstraction-level error, verified Playwright connectOverCDP
  against official docs, flagged the autoConnect security exposure.
  Verdict: REVISE.
- **agy critique (Gemini 3.5 Flash, 3 tool calls):**
  `P:/tmp/tp-dispatch-019fe7e9-cd0/console_5cf32bda-tp-agy-puppeteer-result.md` —
  independently converged on REVISE with the same abstraction-level
  reframe. Added the dedicated-profile recommendation.
- **Playwright connectOverCDP docs:** verified by codex lens via
  `site:playwright.dev/docs/api/class-browsertype connectOverCDP` search.
  The `noDefaults` option is explicitly documented for daily-driver
  browser attachment.
- **Existing wiki concept being refined:**
  `P:/.data/wiki/concepts/cdp-network-interception-and-sse-capture-for-llm-chat.md`
  §5 and falsifier line 210 — the overreach and the self-contradicting
  falsifier condition.
- **Session evidence (autoConnect exposure):** `list_pages` returned 12
  tabs including YouTube extensions, Chrome Web Store, and a Gemini
  Notebook — confirming that autoConnect to the default profile exposes
  every open tab, not just LLM tabs. Verified directly this session.

## Sources

- [Playwright API: browserType.connectOverCDP](https://playwright.dev/docs/api/class-browsertype#browser-type-connect-over-cdp) (Playwright docs, verified 2026-08-09 via codex lens) — confirms connectOverCDP attaches to existing Chromium with remote debugging, including a `noDefaults` option for daily-driver browsers
- [cdp-network-interception-and-sse-capture-for-llm-chat](file:///P:/.data/wiki/concepts/cdp-network-interception-and-sse-capture-for-llm-chat.md) (this workspace, 2026-08-02) — the concept being refined; §5 and falsifier line 210 contain the overreach
- [[solution-unit-validation-before-build]] (this workspace) — the pattern this finding instantiates: engaging with a proposal's framing without questioning the framing itself
- [[replacement-before-investigation-pattern]] (this workspace) — the broader failure class: rejecting a tool based on misunderstanding of what was tested

## Auto-related

- [[skill-graph]]
- [[wiki-improvement-opportunities-practitioner-evidence]]
- [[sdlc-workflow-improvements-from-session-019fdf3d]]
- [[dynamic-wiki-driven-skill-configuration]]
- [[skill-catalog]]

