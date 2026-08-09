---
thread_id: 019fe7e9-cd04-7a63-9436-1b446826024a
parent_handoff_path: none
current_session_id: 019fe7e9-cd04-7a63-9436-1b446826024a
current_terminal_id: grok-build-019fe7e9
produced_at: 2026-08-09T21:00:00Z
status: open
handoff_type: investigation
accurate_as_of_head: HEAD
---

# chrome-devtools-mcp: autoConnect configured, security exposure remains

## Objective

Complete the chrome-devtools-mcp configuration work from session 019fe7e9. The `--autoConnect` flag is wired and working (verified: `list_pages` returns 12 real tabs). The remaining work is a security exposure: the MCP attaches to the operator's default Chrome profile, exposing every open tab to any MCP client on the debugging port. Move to the dedicated LLM profile or add a broker with strict target ownership.

## Status

PARTIALLY_DONE — config edit complete and verified working. Security exposure identified but not remediated. Two `/tp` lenses (codex + agy) independently flagged the exposure as the higher-ROI fix.

## Producing context

2026-08-09, session `019fe7e9-cd04-7a63-9436-1b446826024a`, Grok Build. Operator asked to connect `/model-web` to their existing Chrome window. Root cause: installed plugin config was missing `--autoConnect` flag, so the MCP launched its own isolated browser (`about:blank`) instead of attaching. Config edit shipped; `/plugins reload` applied; `list_pages` verified 12 real tabs. During the `/tp` critique of whether Puppeteer is the right foundation, both lenses independently flagged that autoConnect-to-default-profile exposes every open tab.

## Read-first list

1. `C:\Users\brsth\.grok\installed-plugins\chrome-devtools-mcp-2df60288\.claude-plugin\plugin.json` — the config as edited this session. Verify `--autoConnect` is still present (sibling sessions may have reverted it).
2. `P:/.data/wiki/concepts/chrome-autoconnect-for-authenticated-cdp-sessions.md` — the decision of record. Documents why `--autoConnect` over `--browser-url`, the Chrome 136+ restriction, and the enterprise policy.
3. `P:/.data/wiki/concepts/playwright-connectovercdp-not-ruled-out.md` — written this session. The `/tp` critique that surfaced both the Playwright abstraction-level error AND the autoConnect security exposure (§ "A second finding surfaced").
4. `C:\Users\brsth\.grok\skills\model-web\SKILL.md` lines 70-73 — the documented MCP config. Note: includes `--user-data-dir=P:/.data/chrome-llm-profile` which conflicts with the shipped `--autoConnect`. This drift should be resolved based on the operator's Path A/B decision.

## Verified facts

- [FACT] Installed plugin.json had only `["chrome-devtools-mcp@1.6.0"]` before this session — no `--autoConnect`. Receipt: read_file of plugin.json before edit.
- [FACT] `--autoConnect` is the correct fix per wiki decision of record `[[chrome-autoconnect-for-authenticated-cdp-sessions]]`. Chrome 136+ ignores `--remote-debugging-port` for default profiles; `--autoConnect` (Chrome 144+) is purpose-built. Chrome on this host is v151.
- [FACT] Config edit landed: plugin.json args now `["chrome-devtools-mcp@1.6.0", "--autoConnect", "--experimentalPageIdRouting"]`. Receipt: read_file after edit.
- [FACT] After `/plugins reload`, `list_pages` returned 12 real tabs (YouTube extensions, Perplexity, Gemini Notebook) instead of `about:blank`. The connection works.
- [FACT] `RemoteDebuggingAllowed` enterprise policy already set (2026-07-31 per wiki). No permission dialog appeared this session.
- [FACT] `list_pages` exposed tabs beyond LLM sites — Chrome Web Store extensions, a Gemini Notebook. This confirms the security exposure: autoConnect to default profile = every tab visible.
- [INFERENCE] The dedicated LLM profile at `P:/.data/chrome-llm-profile` still has valid LLM-site logins. The wiki says cookies persist, but this was not verified this session.

## Current state

**Done:**
- Root-caused why MCP saw only `about:blank` (missing `--autoConnect` flag)
- Added `--autoConnect` + `--experimentalPageIdRouting` to plugin.json
- Verified connection via `list_pages` (12 real tabs)
- Documented the Playwright abstraction-level error in a new wiki concept
- Identified the security exposure via `/tp` critique

**Not done:**
- Security exposure remediation (Path A: dedicated profile, or Path B: broker)
- SKILL.md drift resolution (lines 70-73 document `--user-data-dir` which conflicts with shipped `--autoConnect`)
- Wiki concept update for the security-exposure finding

## Task packets

### CDP-SEC-01: Operator decides Path A vs Path B
- **goal:** Operator chooses between dedicated LLM profile (Path A) and broker with target ownership (Path B)
- **in scope:** the security/remediation decision
- **out of scope:** implementation (that's CDP-SEC-02)
- **files:** none (decision only)
- **acceptance:** operator states Path A or Path B with rationale
- **falsifier:** operator defers the decision indefinitely (security exposure remains unremediated)
- **verification level:** OPERATOR_DECISION

### CDP-SEC-02: Implement chosen path
- **goal:** Apply the operator's chosen remediation
- **in scope:** if Path A — switch plugin config from `--autoConnect` to `--user-data-dir=P:/.data/chrome-llm-profile`, verify dedicated profile launches cleanly, verify `list_pages` returns only LLM tabs, verify login persistence; if Path B — implement broker restricting MCP access to LLM URL patterns
- **out of scope:** the other path
- **files:** `C:\Users\brsth\.grok\installed-plugins\chrome-devtools-mcp-2df60288\.claude-plugin\plugin.json`; possibly `P:/.agents/scripts/launch_llm_chrome.py` (Path A)
- **acceptance:** `list_pages` returns real tabs AND non-LLM tabs are not accessible to the MCP
- **falsifier:** `list_pages` still returns non-LLM tabs after the chosen path is applied
- **verification level:** RUNTIME

### CDP-SEC-03: Resolve SKILL.md drift
- **goal:** Update model-web SKILL.md lines 70-73 to match the chosen path's config
- **in scope:** the MCP config documentation block
- **out of scope:** other SKILL.md content
- **files:** `C:\Users\brsth\.grok\skills\model-web\SKILL.md`
- **acceptance:** documented config matches shipped config
- **falsifier:** grep for the old config string still returns the drifted version
- **verification level:** STATIC_INSPECTION

### CDP-SEC-04: Update wiki concept with security finding
- **goal:** Add a "Security exposure" section to `chrome-autoconnect-for-authenticated-cdp-sessions.md` documenting the default-profile risk and chosen remediation
- **in scope:** the wiki concept
- **out of scope:** other wiki concepts
- **files:** `P:/.data/wiki/concepts/chrome-autoconnect-for-authenticated-cdp-sessions.md`
- **acceptance:** section added, concept validates, committed
- **falsifier:** wiki validator fails on the updated concept
- **verification level:** STATIC_INSPECTION

## Open decisions

- **Path A (dedicated profile) vs Path B (broker):** Path A is simpler and proven (profile exists); Path B preserves "use my existing window" but adds complexity. Operator's original request ("connect to my existing chrome window") implies Path B, but the security exposure may change their mind. **Status: unresolved — needs operator input.**

## Hard constraints

- Must attach to an authenticated Chrome session (Chrome 136+ blocks `--remote-debugging-port` on default profiles; `--autoConnect` or `--user-data-dir` required)
- Must support `evaluate_script` for framework-controlled inputs (React/ProseMirror)
- Must work across multi-terminal fleet without CDP contention
- Must not expose non-LLM tabs to MCP clients (the security exposure being remediated)

## Cross-reference couplings

- `/model-web` SKILL.md — the config drift (lines 70-73) must be resolved as part of CDP-SEC-03
- Wiki concept `playwright-connectovercdp-not-ruled-out.md` — documents the session that surfaced this exposure; read for context
- The `/tp` dispatch `Invoke-Expression` issue (see Epistemic Labels) affects future `/tp` runs but is not blocking for this handoff

## Explicit non-goals

- Migrating `/model-web` off Puppeteer to Playwright — the `/tp` verdict was REVISE (build a browser-session interface), not "switch libraries." No workload evidence justifies migration.
- Building the browser-session-interface abstraction — that's architectural work separate from this security remediation. May become its own handoff.
- Re-verifying the `--autoConnect` flag survives Grok Build restart — that's `[UNTESTED]` but not blocking

## Resumption protocol

1. Read this handoff + the 4 read-first files
2. Confirm `--autoConnect` is still in plugin.json (sibling sessions may have reverted it)
3. Ask operator for Path A vs Path B decision (CDP-SEC-01)
4. Implement the chosen path (CDP-SEC-02)
5. Resolve SKILL.md drift (CDP-SEC-03)
6. Update wiki concept (CDP-SEC-04)

## Suggested next invocation

`/handoff claim P:/docs/handoffs/chrome-devtools-mcp-autoconnect-security-20260809` then ask operator for the Path A/B decision.

## Last user message (verbatim)

> /handoff

## Epistemic labels

- The config edit and `list_pages` verification are `[FACT]` with tool-call receipts
- The security exposure is `[FACT]` — confirmed by `list_pages` returning non-LLM tabs
- Dedicated profile login state is `[INFERENCE]` — wiki says cookies persist but not verified this session
- The `/plugins reload` persistence across Grok Build restarts is `[UNTESTED]`
- The `/tp` dispatch `Invoke-Expression` issue: the `/tp` SKILL.md says "run the command printed by tp_dispatch.py verbatim" — I compressed the packer + execution into one call via `Invoke-Expression`, which is policy-blocked. Fix: run as two separate `run_terminal_command` calls. Affects future `/tp` runs, not this handoff.
