---
title: "Chrome ACP library stack, updated ecosystem, and front/back-end best practices (2026)"
created: 2026-07-31
source: session-2026-07-31
tags: [chrome-acp, hono, react, wxt, crxjs, shadcn, radix-ui, tailwind, acp, acp-components, browser-extension, front-end, back-end, security, cve, host-invariants]
summary: >
  The chrome-acp extension uses React + Bun + Radix/shadcn + Tailwind + KaTeX on the
  front-end and Hono + @hono/node-server + @hono/node-ws on the back-end. Research found:
  (1) Bun is not the standard for MV3 extension builds — WXT or CRXJS+Vite dominate;
  (2) Hono has had 6 CVEs in 2026 (auth bypass via serveStatic, XSS, cache deception) —
  installed 4.12.32 is patched but the ^4.7.0 range is a latent risk;
  (3) the ACP ecosystem exploded — ACP Components offers a ready-made React component
  library for agent UIs, and Casper is a direct chrome-acp alternative;
  (4) shadcn/Radix remains dominant but the "your component, your problem" maintenance
  burden is the main criticism. Installable skills available for Chrome extension dev.
agent: grok
host: grok
cognitive_load: 3
verification: multi-source-verified
relations:
  - target: wiki/concepts/chrome-acp-grok-build-browser-driven-agentic-clis.md
    type: refines
    reciprocal: related
  - target: wiki/concepts/chrome-acp-grok-build-setup-implementation.md
    type: refines
    reciprocal: related
  - target: wiki/concepts/concurrent-cdp-auth-contention.md
    type: supports
  - target: wiki/concepts/invariants-beat-environment-comfort.md
    type: related
---

## Summary

This concept answers: **what libraries does chrome-acp use, are they current, and what
best practices / skills / ecosystem updates should we know for both front-end and back-end?**

The chrome-acp project is a patched fork of [Areo-Joe/chrome-acp](https://github.com/Areo-Joe/chrome-acp)
(v1.0.40) that bridges browser tabs to `grok agent stdio` via a WebSocket proxy. We maintain
~8 custom IIFE/patch injections because upstream is stale (177 stars, last push 2026-04-09,
issue #11 Windows crash still open). This research focuses on the library stack itself. See
[[chrome-acp-grok-build-setup-implementation]] for the patch inventory and
[[chrome-acp-grok-build-browser-driven-agentic-clis]] for the original architecture research.

## Decision context

**The problem:** the operator wanted to know what libraries the chrome-acp project uses, whether
they're current, and what updated best practices / skills / ecosystem developments would help
with both the front-end (Chrome extension side panel) and back-end (proxy server).

**What alternatives were explored:**
- Checked upstream repo health (still stale, no new releases since v1.0.40)
- Searched for extension build frameworks (WXT vs Plasmo vs CRXJS vs Bun)
- Searched for back-end framework comparisons (Hono vs Fastify vs Express)
- Searched for installable community skills (skills.sh)
- Fetched the ACP clients registry (ecosystem exploded since 2026-07-29)

**What the research changed:** confirmed the current stack is mostly sound but identified:
(1) Bun is non-standard for extensions — WXT/CRXJS are the 2026 standard;
(2) Hono has a real security surface (6 CVEs) — the installed version is patched but the
dependency range is risky; (3) new ACP-specific resources (ACP Components, Casper) now exist
that weren't available when we first researched this; (4) installable skills are available
for Chrome extension development that could accelerate future work.

---

## Current library stack (observed from dist/ bundles + patched source)

### Front-end (Chrome Extension side panel)

| Library | Role | Evidence |
|---------|------|----------|
| **React** | UI framework | `index.html` title "Bun + React", `<div id="root">`, controlled-input patterns in IIFE patches |
| **Bun** | Build tool / bundler | Hashed filenames (`sidepanel-t6n74ra3.js`), `index.html` title |
| **Radix UI + shadcn-style** | Component primitives | `data-radix-popper-content-wrapper`, `data-slot="dropdown-menu-trigger"`, `data-state` attrs in IIFE |
| **Tailwind CSS** | Styling | Inferred from shadcn pattern + `data-slot` convention |
| **KaTeX** | Math rendering | `@font-face KaTeX_AMS` in CSS |

### Back-end (Proxy server)

| Library | Role | Evidence |
|---------|------|----------|
| **Hono** | Web framework | `import { Hono } from "hono"` in `server.patched.js` |
| **@hono/node-server** | Node.js adapter | `import { serve }` |
| **@hono/node-server/serve-static** | Static file serving | `import { serveStatic }` |
| **@hono/node-ws** | WebSocket support | `import { createNodeWebSocket }` |

### Chrome Extension APIs (Manifest V3)
`sidePanel`, `activeTab`, `scripting`, `tabs`, `declarativeNetRequest` (CSP stripping),
`<all_urls>` host permissions.

---

## Front-end best practices (2026 state of the art) [HIGH confidence — ≥3 sources]

### Build tools: WXT and CRXJS+Vite dominate; Bun is non-standard

**WXT** ([wxt.dev](https://wxt.dev)) is the leading 2026 extension framework — Nuxt-inspired,
framework-agnostic (React/Vue/Svelte), handles MV2/MV3, cross-browser (Chrome/Firefox/Edge/Safari),
file-based routing, HMR, auto-manifest. 216 contributors, regular releases. Multiple independent
comparisons (extensionbooster, trybuildpilot, extenshi.io, StarterPick) rank it #1 for new production
extensions. [HIGH — ≥4 comparison articles agree]

**CRXJS** (`@crxjs/vite-plugin` v2.7.1) plugs into Vite for MV3 HMR + manifest orchestration.
Lighter-weight than WXT — good if you already have a Vite setup. [HIGH]

**Plasmo** is the third major option — React-first, similar to Next.js conventions. [MEDIUM]

**Bun** (what chrome-acp uses) is NOT recommended for MV3 extension development. No 2025-2026
source recommends it; it lacks the CSP helpers, HMR, and manifest orchestration that WXT/CRXJS
provide. The extension's build appears to use Bun's bundler directly, which works but misses
extension-specific tooling. [MEDIUM — absence of positive evidence + explicit comparisons favor alternatives]

**Implication for chrome-acp:** since we patch a minified upstream bundle (not build from source),
switching build tools only matters if we fork/rebuild the extension from source. The IIFE-injection
patching strategy works regardless of build tool.

### UI components: shadcn/ui + Radix remains dominant

shadcn/ui remains the most-cited React component collection for MV3 side panels in 2025-2026.
Built on Radix UI primitives + Tailwind. No successor has displaced it. [HIGH]

**Main criticism** [PRACTITIONER]: "When you take a component from shadcn/ui, it becomes YOUR
component. If there's a problem, it's YOUR problem" — no auto-updates, you maintain the copied
code. A popular YouTube video (211K views, Jun 2025) asks "Has Radix become a liability?"
flagging the Radix dependency as a maintenance risk. [MEDIUM — practitioner criticism, not docs]

**Implication for chrome-acp:** the current Radix/shadcn stack is fine. The maintenance burden
is real but manageable since the extension UI changes rarely.

### Markdown rendering: react-markdown + remark + KaTeX is the standard

`react-markdown` (v8.0.0, Apr 2026) + `remark-gfm` + `remark-math` + `rehype-katex` is the
standard React chat-UI markdown stack. Alternatives: `marked` (v4.1.0) + `dompurify` for
lighter-weight, or `markdown-it` (v13.0.0) with plugin system. chrome-acp already uses KaTeX
for math — the rendering path is standard. [HIGH]

### Tailwind in extensions: CSP requires hash/nonce

Tailwind's runtime style injection requires either a CSP hash or nonce in the extension's
`content_security_policy.extension_pages`. chrome-acp's manifest already declares a permissive
CSP (`script-src 'self' 'wasm-unsafe-eval' http://localhost:*`) and uses `declarativeNetRequest`
to strip CSP from target pages — so this is handled for the target-page side. [HIGH]

### MV3 side-panel lifecycle + API changes

**API change:** in 2026, the `openPanelOnActionClick` manifest field was removed. Side panels
must now be opened programmatically from the **service worker** via `chrome.action.onClicked` →
`chrome.sidePanel.open()`. chrome-acp's manifest uses `side_panel.default_path` (which still
works), but any panel-open-trigger logic needs the service-worker pattern. [MEDIUM]

### Content-script injection safety patterns

The 2026 security best practice for `chrome.scripting.executeScript` (which chrome-acp's
`browser_read`/`browser_execute` uses):
- **Verify target domain** before injecting — don't inject into arbitrary URLs
- **Use `run_at: document_start`** to avoid race conditions
- **Limit injected code** to a single, narrowly-scoped function
- **Minimize `matches` permissions** — broad `<all_urls>` host permissions (which chrome-acp
  uses) create a large attack surface

[FACT — developer.chrome.com security docs + bestchromeextensions.com injection patterns guide]

### ⚠️ CSP stripping is a known malicious-extension pattern [PRACTITIONER signal]

chrome-acp uses `declarativeNetRequest` with `rules/strip_csp.json` to strip CSP headers from
target pages so the agent can read/interact with them. A 2025 cybersecurity analysis
("16 Malicious Chrome Extensions") documents that **CSP stripping via declarative rules is a
common malicious-extension technique** — attackers disable CSP to enable injection attacks.

**Implication for chrome-acp:** the CSP stripping is intentional (the agent needs to read DOM
content without CSP blocking), but it's the same pattern malware uses. Mitigations:
- Use `setHeaders` with targeted `Content-Security-Policy` modification rather than full removal
  (the declarativeNetRequest best-practice doc recommends `remove` on specific directives, not
  blanket stripping)
- Consider **dynamic declarativeNetRequest rules** (`updateDynamicRules`) that strip CSP only
  for the specific tab the agent is actively reading, rather than all tabs globally
- This connects to the browser-agent security risk in [[chrome-acp-grok-build-browser-driven-agentic-clis]]
  § "The six attack vectors" — CSP stripping amplifies the prompt-injection risk

[MEDIUM — security best-practice docs + practitioner analysis]

---

## Back-end best practices (2026 state of the art) [HIGH confidence — ≥3 sources]

### Hono: thriving but has a real CVE surface

Hono is thriving — 29.7K stars (+92/week), zero dependencies, Web Standards-based, runs on
every JS runtime. It wins on portability; Fastify wins on Node.js-specific raw performance
benchmarks. For a localhost proxy (chrome-acp's use case), Hono is the right choice —
portability and simplicity matter more than raw throughput. [HIGH]

**⚠️ Security: Hono has had 6 CVEs in 2026** [FACT — CVEReports, SentinelOne, Vulert]:

| CVE | Issue | Fixed in | Relevant to chrome-acp? |
|-----|-------|----------|------------------------|
| CVE-2026-29045 | Auth bypass: inconsistent URL decoding between router and `serveStatic` | 4.12.4 | **YES** — proxy uses `serveStatic` |
| CVE-2026-24472 | Web Cache Deception in cache middleware | 4.11.7 | No (proxy doesn't use cache middleware) |
| CVE-2026-29085 | XSS in `streamSSE()` | patched | No (proxy uses WS, not SSE) |
| CVE-2026-24771 | ErrorBoundary XSS bypass in JSX middleware | patched | No (proxy doesn't use JSX middleware) |
| CVE-2026-22817 | JWT Algorithm Confusion | patched | No (proxy doesn't use JWT) |
| CVE-2026-47676 | Inconsistent Path Parsing in sub-app mounting | patched | Unlikely (no sub-app mounting) |

**Installed version check** [FACT — `node -e require('hono/package.json').version`]:
- Installed: **4.12.32** (≥4.12.4 → CVE-2026-29045 patched ✓)
- Declared range in `@chrome-acp/proxy-server` package.json: `^4.7.0` → **a fresh `npm install`
  could install 4.7.0–4.12.3, which IS vulnerable to CVE-2026-29045**

**Recommendation:** pin Hono to `>=4.12.4` in the proxy's dependencies (or `^4.12.32`) to
prevent a vulnerable install on rebuild. Since the proxy runs on localhost only (not
internet-exposed), the auth-bypass risk is low — but defense in depth applies.

### Framework alternatives: Fastify, Express, Elysia

2026 comparisons consistently rank the Node.js framework landscape as: **Hono** best for
multi-runtime/edge, **Fastify** best for raw Node.js throughput (2-3× Express), **Express**
legacy-only, and **Elysia** the emerging speed demon (~6KB, claims 15% faster than Fastify on
Bun, type-safe API). Express is explicitly called "legacy" in 2026 posts — not recommended for
new production work. [HIGH — ≥3 comparison articles agree]

**Elysia** is worth watching — ultra-light (~6KB), claims 15% faster raw throughput than Fastify
on Bun, compiles to native V8 bytecode. However, its WebSocket extension ecosystem is less mature
than Hono's, making it a weaker fit for chrome-acp's WS-heavy proxy today. [MEDIUM]

**Implication for chrome-acp:** Hono remains the right choice. The localhost proxy doesn't need
Fastify's raw throughput edge, and Hono's multi-runtime support + `@hono/node-ws` integration is
well-suited. No change needed.

### WebSocket + stdio bridging patterns

The chrome-acp proxy pattern (WS ↔ stdio JSON-RPC) is clean and standard. `@hono/node-ws`
provides the WebSocket layer; the agent communicates over stdin/stdout. No better alternative
exists for this use case — the pattern is validated by the broader ACP ecosystem:

- **ACP Remote, stdio Bus, Aptove Bridge** — all use similar WS-to-stdio bridges
- **MCP HTTP-Stdio Bridge** (Lobehub) — documents the same transparent-proxy pattern for MCP
  servers, confirming the architecture generalizes beyond ACP
- **ACP SDKs provide ready-made stdio plumbing:** the Python SDK (`agent-client-protocol`) has
  async base classes for stdio JSON-RPC, and the Rust crate (`agent-client-protocol-schema`)
  has type-safe models for every ACP release. If the proxy were ever rewritten in Python or Rust,
  these SDKs eliminate the JSON-RPC boilerplate. [HIGH]

---

## ACP ecosystem explosion (major update since 2026-07-29) [HIGH — official registry]

The ACP clients registry ([agentclientprotocol.com/get-started/clients](https://agentclientprotocol.com/get-started/clients))
now lists 80+ projects across categories that barely existed 2 months ago:

### Directly relevant new resources

**ACP Components** ([github.com/zvzuola/acp-components](https://github.com/zvzuola/acp-components))
— "A universal frontend component library for building AI Agent interfaces based on the ACP."
This is a ready-made React component library purpose-built for ACP agent UIs (tool-call rendering,
session management, streaming responses). Could replace the manual Radix/shadcn setup in chrome-acp
if we rebuild from source. [MEDIUM — new, adoption unknown]

**Casper** ([github.com/joeyshi12/casper](https://github.com/joeyshi12/casper)) — "A web client
for kiro-cli that talks to it over ACP, giving you a browser-based chat UI with live streaming,
session history, and rich per-tool-call rendering." This is a direct alternative to chrome-acp's
purpose, built as a standalone web client (no browser extension needed). Worth evaluating if
chrome-acp's extension-based approach proves too brittle. [MEDIUM]

**ACP Inspector** ([github.com/newioapp/acp-inspector](https://github.com/newioapp/acp-inspector))
— desktop debugger/inspector for the ACP protocol. Useful for debugging proxy↔agent communication.
[MEDIUM]

**Codeg** — collaborative multi-agent coding workbench with session aggregation. **Braide** —
parallel sessions, worktrees, personas. **Jockey** — multi-agent orchestrator (Tauri + Rust + SolidJS).

### Framework integrations now available
LangChain/Deep Agents ACP, Mastra (`@mastra/acp`), LlamaIndex, Pydantic AI, fast-agent — all
now have ACP adapters. This means you can wrap any of these framework-based agents as ACP agents
and drive them from chrome-acp or any ACP client.

### HN practitioner signal
- **Zero HN results for "chrome acp"** — no community discussion exists. Chrome ACP is invisible
  in the broader developer community. [FACT — HN Algolia API query returned 0 hits]
- **ACP itself has strong signal**: 281pts main post, JetBrains adoption blog, Rowboat (219+131pts),
  VT Code (18pts), Webctl (134pts)
- **Browser automation is hot**: Workflow Use (69pts), Browser4, Browsernode — the category is
  validated but chrome-acp specifically has no mindshare

---

## Installable skills [FACT — `npx skills find` results]

### Chrome extension development

| Skill | Installs | Notes |
|-------|----------|-------|
| `clerk/skills@clerk-chrome-extension-patterns` | 8.5K | Highest-install extension skill |
| `googlechrome/modern-web-guidance@chrome-extensions` | 2.4K | **Official Google** — most authoritative |
| `mindrally/skills@chrome-extension-development` | 2.3K | General extension dev |
| `samber/cc-skills@chrome-extension` | 2K | Claude Code-focused |
| `pproenca/dot-skills@chrome-extension-ui` | 622 | Extension UI specifically |

### ACP / agent protocol

| Skill | Installs | Notes |
|-------|----------|-------|
| `borghei/claude-skills@agent-protocol` | 97 | General agent protocol |
| `diegosouzapw/awesome-omni-skill@agent-client-protocol` | 1 | ACP-specific (very low adoption) |
| `sickn33/antigravity-awesome-skills@hono` | — | Hono framework best practices |

**Recommendation:** `googlechrome/modern-web-guidance@chrome-extensions` is the highest-value
install — official Google guidance for extension development. Install via
`npx skills add googlechrome/modern-web-guidance@chrome-extensions`.

---

## Upstream health (updated 2026-07-31) [FACT — `gh repo view`]

| Metric | Value | Trend vs 2026-07-29 |
|--------|-------|---------------------|
| Stars | 177 | +3 (from 174) |
| Last push | 2026-04-09 | Unchanged (still ~3.5 months stale) |
| Last release | v1.0.40 (2026-03-09) | Unchanged |
| Issue #11 (Windows crash) | OPEN | Unchanged — still blocks |
| Docs site | areo-joe.github.io/chrome-acp | **NEW** — docs now exist |

The new docs site is the only change. Upstream remains effectively unmaintained for our purposes.
Our patch-based fork strategy is still the right call.

---

## Research applicability gate (Round 3.25)

| Finding | Applies? | Promote? |
|---------|----------|----------|
| Switch Bun→WXT for extension builds | Partially — only matters if we rebuild from source, not for IIFE patching | **Conditional** — note for future rebuild decision |
| Pin Hono `>=4.12.4` in proxy deps | Yes — installed is safe but range is risky | **Yes** — actionable security hardening |
| Adopt ACP Components | Uncertain — need to evaluate the library quality | **Conditional** — investigate before adopting |
| Evaluate Casper as chrome-acp alternative | Yes — if extension brittleness becomes untenable | **Informational** — keep on radar |
| Install googlechrome extension skill | Yes — accelerates future extension work | **Yes** — low-cost, high-value |
| react-markdown + KaTeX stack | Informational — we don't control the upstream bundle | **No** — upstream's choice |

## Host invariant check (Round 3.5)

| Invariant | Violation risk | Status |
|-----------|---------------|--------|
| Multi-terminal CDP isolation ([[concurrent-cdp-auth-contention]]) | None — all recommendations are build-tool/library level, not runtime browser access | PASSED |
| Singleton proxy (localhost:9315) | None — Hono upgrade doesn't change proxy architecture | PASSED |
| No cookies-from-browser in parallel | None — no recommendation touches browser session access | PASSED |

Host invariant check: **PASSED — no violations.**

---

## Recommendations

1. **Pin Hono to `>=4.12.4`** in the proxy's package.json. The installed 4.12.32 is safe, but
   `^4.7.0` allows a vulnerable fresh install. Defense in depth for a localhost proxy. [HIGH confidence]
2. **Install `googlechrome/modern-web-guidance@chrome-extensions`** skill — official Google
   extension dev guidance, highest authority available. [HIGH]
3. **Evaluate ACP Components** (github.com/zvzuola/acp-components) if rebuilding the extension
   from source — purpose-built ACP UI components could replace manual Radix/shadcn setup. [MEDIUM]
4. **Keep Casper on the radar** as a chrome-acp alternative — if the extension-patching strategy
   becomes unmaintainable, a web-client approach may be simpler. [LOW]
5. **If rebuilding from source:** use WXT (not Bun) as the build framework — it's the 2026 standard
   for MV3 extensions with HMR, manifest orchestration, and cross-browser support. [MEDIUM]
6. **Tighten CSP-stripping scope:** replace the blanket `strip_csp.json` rule with dynamic
   `declarativeNetRequest` rules that strip CSP only for the specific tab being actively read,
   not all tabs globally. CSP stripping is a documented malicious-extension pattern — narrowing
   the blast radius reduces the prompt-injection amplification risk. [MEDIUM]

## What this means for our workspace

This workspace runs chrome-acp as the primary browser-driven agent interface (see
[[chrome-acp-grok-build-setup-implementation]]). The concrete actions:

- **Immediate:** pin Hono `>=4.12.4` in `@chrome-acp/proxy-server/package.json` to prevent a
  vulnerable reinstall. The installed 4.12.32 is safe — this is a defense-in-depth fix.
- **Immediate:** install `googlechrome/modern-web-guidance@chrome-extensions` skill for future
  extension development work.
- **When rebuilding from source (future):** migrate from Bun to WXT as the build tool — Bun lacks
  MV3-specific tooling (HMR, CSP helpers, manifest orchestration) that WXT provides natively.
  Evaluate [[mcp-servers-for-polishing-code-words-images-video]] for media tool integration.
- **Monitor:** ACP Components and Casper as potential replacements for the current patch-based
  fork strategy. If upstream chrome-acp remains stale, forking with WXT + ACP Components may be
  more maintainable than continuing to inject IIFEs into minified bundles.
- **Security posture:** the proxy runs on localhost only, so the Hono CVEs are low-risk in
  practice. But the [[concurrent-cdp-auth-contention]] invariant still applies — one terminal
  drives chrome-acp at a time, and the browser_read/execute surface remains the dominant risk
  per [[chrome-acp-grok-build-browser-driven-agentic-clis]] § security.

## Receipts

| Claim | Evidence |
|-------|----------|
| Front-end uses React + Bun + Radix/shadcn + Tailwind + KaTeX | `dist/index.html` title "Bun + React"; `dist/sidepanel-6b07g991.css` line 1 `@font-face KaTeX_AMS`; `patches/sidepanel-iife.js` refs `data-radix-popper-content-wrapper`, `data-slot="dropdown-menu-trigger"` |
| Back-end uses Hono + @hono/node-server + serveStatic + @hono/node-ws | `server.patched.js` lines 7-10: `import { Hono }`, `import { serve }`, `import { serveStatic }`, `import { createNodeWebSocket }` |
| Installed Hono version 4.12.32 | `node -e require('hono/package.json').version` → 4.12.32 (run 2026-07-31) |
| Proxy declares `^4.7.0` for Hono | `node -e require('@chrome-acp/proxy-server/package.json').dependencies.hono` → `^4.7.0` (run 2026-07-31) |
| Hono CVE-2026-29045 affects serveStatic | CVEReports + DailyCVE: "inconsistent URL decoding between router and serveStatic middleware" |
| Upstream still stale (177 stars, last push 2026-04-09, #11 open) | `gh repo view Areo-Joe/chrome-acp --json pushedAt,stargazerCount` + `gh issue list` (run 2026-07-31) |
| Zero HN results for chrome-acp | HN Algolia API: `search?query=chrome+acp+agent&tags=story` → 0 hits (run 2026-07-31) |
| ACP ecosystem has 80+ clients | Fetched https://agentclientprotocol.com/get-started/clients (2026-07-31) |
| Installable skills exist | `npx skills find chrome-extension` + `npx skills find "agent client protocol"` (run 2026-07-31) |

---

## Falsifier

This concept is wrong if:
- Hono's CVE count continues to grow, making it a liability for even localhost proxies (watch: 2026
  CVE cadence — 6 in 7 months is already high)
- ACP Components proves low-quality or unmaintained (watch: commit cadence, star count)
- WXT loses momentum to Plasmo or a new entrant (watch: GitHub stars, contributor count)
- Chrome ACP upstream revives and adopts these best practices natively (watch: issue #11 resolution,
  new releases after v1.0.40)
- The ACP ecosystem consolidates around a single dominant client, making chrome-acp irrelevant

---

## Sources

- ACP clients registry: https://agentclientprotocol.com/get-started/clients (fetched 2026-07-31)
- Chrome ACP docs: https://areo-joe.github.io/chrome-acp/getting-started/introduction.html (fetched 2026-07-31)
- Chrome ACP repo health: `gh repo view Areo-Joe/chrome-acp` (run 2026-07-31)
- WXT: https://wxt.dev/ + https://github.com/wxt-dev/wxt
- Extension framework comparisons: extensionbooster.net, trybuildpilot.com, extenshi.io/blog, StarterPick (2026)
- Hono: https://hono.dev/docs + opensourcedrop.com (29.7K stars, +92/week)
- Hono CVEs: CVEReports (CVE-2026-29045, 47676), SentinelOne (CVE-2026-29085), Vulert (CVE-2026-24472), DailyCVE
- shadcn/ui criticism: dev.to/playfulprogramming, YouTube "Watch this if you use shadcn/ui" (211K views, Jun 2025)
- react-markdown: https://github.com/remarkjs/react-markdown (v8.0.0, Apr 2026)
- HN Algolia: queries for "chrome acp" (0 results), "agent client protocol" (281pts main), "browser automation agent"
- Installable skills: `npx skills find chrome-extension` + `npx skills find "agent client protocol"` (run 2026-07-31)
- Installed Hono version: `node -e require('hono/package.json').version` → 4.12.32 (run 2026-07-31)
